# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.db.models import get_model
from django.contrib.contenttypes.models import ContentType
from transifex.actionlog.models import LogEntry
from transifex.actionlog.queues import redis_key_for_team
from datastores.txredis import TxRedisMapper


class Command(BaseCommand):

    help = (
        "Populate the latest history of a team.\n"
        "You can specify the slug(s) of a project to initialize "
        "only the teams of those projects."
    )

    def handle(self, *args, **options):
        Team = get_model('teams', 'Team')
        if not args:
            teams = Team.objects.all().iterator()
        else:
            teams = Team.objects.filter(project__slug__in=args).iterator()
        for idx, t in enumerate(teams):
            if int(options.get('verbosity')) > 1:
                self.stdout.write("Team %d: %s\n" % (idx, t.id))
            self._populate_history(t)

    def _populate_history(self, team):
        """Store the latest action log items for the specified team."""
        Team = get_model('teams', 'Team')
        entries = LogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(Team),
            object_id=team.id
        )[:5]
        r = TxRedisMapper()
        key = redis_key_for_team(team)
        for entry in entries:
            data = {
                'action_time': entry.action_time,
                'message': entry.message,
                'action_type': entry.action_type,
            }
            r.rpush(key, data=data)
        r.ltrim(key, 0, 4)

