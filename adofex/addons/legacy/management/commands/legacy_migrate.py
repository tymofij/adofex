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

@transaction.commit_on_success
class Command(BaseCommand):
    help = "Copies all string from legacy Babelzilla DB to Transifex"

    def handle(self, **options):
        from transifex.resources.models import Resource, SourceEntity, Translation
        from transifex.resources.handlers import invalidate_stats_cache

        en = Language.objects.get(code='en-US')

        for e in legacy.Extension.objects.filter(slug='smarttemplate4'):
            p = Project(slug=e.slug, name=smart_unicode(e.name),
                description=smart_unicode(e.description), homepage=e.homepage, source_language=en)
            p.save()
            for f in legacy.File.objects.filter(extension=e):
                r = Resource(name=f.name, project=p, slug=slugify(f.name)+str(f.id))
                if f.name.endswith('.dtd'):
                    r.i18n_type = 'DTD'
                elif f.name.endswith('.properties'):
                    r.i18n_type = 'MOZILLAPROPERTIES'
                else:
                    raise Exception("Unknown file type")
                r.save()
                for s in legacy.String.objects.filter(file=f, extension=e).select_related('language'):
                    entity, created = SourceEntity.objects.get_or_create(resource=r, string=s.name)
                    lang = LangLookup.get(s.language.name)
                    if not lang:
                        continue
                    try:
                        Translation(string=smart_unicode(s.string), resource=r,
                            source_entity=entity, language=lang).save()
                    except:
                        print "Error reading String {0}".format(s.id)

            for r in Resource.objects.filter(project=p):
                for l in Language.objects.filter(pk__in=Translation.objects.filter(resource=r
                        ).order_by('language').values_list('language', flat=True).distinct()):
                            invalidate_stats_cache(r, l)

            # p = Project.objects.get(slug=e.slug)

            for g in legacy.Group.objects.filter(extension=e):
                l_members = legacy.Membership.objects.filter(group=g).order_by('permissions')
                # members exist and first one is maintainer
                if l_members and l_members[0].permissions == 'm':
                    owner = migrate_user(l_members[0].user.username)
                else:
                    owner = migrate_user(e.owner.username)
                lang = LangLookup.get(g.language.name)
                team = Team(language=lang, project=p, creator=owner)
                team.save()
                for m in l_members:
                    user = migrate_user(m.user.username)
                    if m.permissions == 'm':
                        team.coordinators.add(user)
                    else:
                        team.members.add(user)
