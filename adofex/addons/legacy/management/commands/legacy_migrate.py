# -*- coding: utf-8 -*-

from transifex.projects.models import Project
from transifex.languages.models import Language
from transifex.teams.models import Team

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.utils.encoding import smart_unicode

from legacy import models as legacy
from legacy.actions import LangLookup, migrate_user

# sometimes new projects opt to have new slugs.
# old_slug -> new_slug
NEW_SLUGS = {
    'babelzillamenu-13': 'bzmenu',
    'adblock-plus-616': 'adblock-plus'
}
SKIPPED_SLUGS = ( # do not migrate those projects
	'adblock-plus-616',
)

@transaction.commit_on_success
class Command(BaseCommand):
    help = "Copies all string from legacy Babelzilla DB to Transifex"

    def handle(self, **options):
        from transifex.resources.models import Resource, SourceEntity, Translation
        from transifex.resources.handlers import invalidate_stats_cache

        en = Language.objects.get(code='en-US')

        for e in legacy.Extension.objects.filter(slug='smarttemplate4'):
            owner = migrate_user(e.owner.username)
            slug = NEW_SLUGS.get(e.slug, e.slug)
            p, created = Project.objects.get_or_create(slug=slug,
                defaults={
                    'name': smart_unicode(e.name),
                    'description': smart_unicode(e.description),
                    'homepage': e.homepage,
                    'source_language':en,
                    'owner': owner,
                })
            p.maintainers.add(owner)

            # import Strings and Translations
            for f in legacy.File.objects.filter(extension=e):
                r, created = Resource.objects.get_or_create(name=f.name, project=p, slug=slugify(f.name))
                if f.name.endswith('.dtd'):
                    r.i18n_type = 'DTD'
                elif f.name.endswith('.properties'):
                    r.i18n_type = 'MOZILLAPROPERTIES'
                else:
                    raise Exception("Unknown file type")
                r.save()
                for s in legacy.String.objects.filter(file=f, extension=e).select_related('language'):
                    entity, created = SourceEntity.objects.get_or_create(resource=r, string=s.name)
                    try:
                        lang = LangLookup.get(s.language.name)
                    except Language.DoesNotExist:
                        # FIXME: might overwrite "pl" strings with "pl_PL" ones
                        # when both are present
                        print "Language lookup failed for %s" % s.language.name
                        continue
                    try:
                        t, created = Translation.objects.get_or_create(
                            resource=r, source_entity=entity, language=lang
                            )
                        t.string = smart_unicode(s.string)
                        t.save()
                    except:
                        print "Error saving String {0}".format(s.id)

            # reset Stats
            for r in Resource.objects.filter(project=p):
                for l in Language.objects.filter(pk__in=Translation.objects.filter(resource=r
                        ).order_by('language').values_list('language', flat=True).distinct()):
                            invalidate_stats_cache(r, l)

            # import Teams
            for g in legacy.Group.objects.filter(extension=e):
                l_members = legacy.Membership.objects.filter(group=g).order_by('permissions')
                team_owner = migrate_user(e.owner.username)
                try:
                    if l_members and l_members[0].permissions == 'm':
                        # members exist and first one is a maintainer
                        team_owner = migrate_user(l_members[0].user.username)
                except legacy.User.DoesNotExist:
                    print "Invalid membership: %s" % l_members[0].id

                lang = LangLookup.get(g.language.name)
                team, created = Team.objects.get_or_create(language=lang, project=p,
                    defaults = {'creator': team_owner} )
                for m in l_members:
                    try:
                        user = migrate_user(m.user.username)
                    except legacy.User.DoesNotExist:
                        print "Invalid membership: %s" % l_members[0].id
                        continue
                    if m.permissions == 'm':
                        team.coordinators.add(user)
                    else:
                        team.members.add(user)