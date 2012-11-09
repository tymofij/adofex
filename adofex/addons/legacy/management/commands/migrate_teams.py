# -*- coding: utf-8 -*-

from transifex.projects.models import Project
from transifex.languages.models import Language
from transifex.teams.models import Team

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.utils.encoding import smart_unicode
from django.contrib.auth.models import User

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
    help = "Copies Project and Teams from legacy Babelzilla DB to Transifex"

    def handle(self, *args, **options):
        """ parameter: extension ID
        """
        from transifex.resources.models import Resource, SourceEntity, Translation
        from transifex.resources.handlers import invalidate_stats_cache
        en = Language.objects.get(code='en-US')

        e = legacy.Extension.objects.get(id=args[0])
        admin = User.objects.get(username='admin')

        owner = migrate_user(e.owner.username)
        slug = NEW_SLUGS.get(e.slug, e.slug)
        p, created = Project.objects.get_or_create(slug=slug,
            defaults={
                'name': smart_unicode(e.name),
                'description': smart_unicode(e.description),
                'homepage': e.homepage,
                'source_language':en,
                'owner': owner,
                'trans_instructions': 'http://www.babelzilla.org/forum/index.php?showtopic=%s' % e.topic if e.topic else None
            })
        p.maintainers.add(owner)

        # import Teams
        for g in legacy.Group.objects.filter(extension=e):
            team_owner = admin

            try:
                lang = LangLookup.get(g.language.name)
            except Language.DoesNotExist:
                continue
            # no need to create team for English
            if lang == en:
                continue

            coordinators = []
            translators = []
            for m in legacy.Membership.objects.filter(group=g):
                try:
                    user = migrate_user(m.user.username)
                except legacy.User.DoesNotExist:
                    print "Invalid membership for {:<5}, id={}, user_id={}".format(lang.code, m.id, m.user_id)
                    continue
                if m.permissions == 'm':
                    coordinators.append(user)
                else:
                    translators.append(user)

            # somebody is found
            if coordinators:
                team, created = Team.objects.get_or_create(language=lang, project=p,
                    defaults = {'creator': admin} )
                team.coordinators.add(*coordinators)
                team.members.add(*translators)