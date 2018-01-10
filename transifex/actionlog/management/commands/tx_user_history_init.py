# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.db.models import get_model
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from transifex.actionlog.models import LogEntry
from transifex.actionlog.queues import redis_key_for_user
from datastores.txredis import TxRedisMapper


class Command(BaseCommand):

    help = "Populate the latest history of a user."

    def handle(self, *args, **options):
        users = User.objects.all().iterator()
        for idx, u in enumerate(users):
            if int(options.get('verbosity')) > 1:
                self.stdout.write("User %d: %s\n" % (idx, u.username))
            self._populate_history(u)

    def _populate_history(self, user):
        """Store the latest action log items for the specified team."""
        entries = LogEntry.objects.by_user(user)[:12]
        r = TxRedisMapper()
        key = redis_key_for_user(user)
        for entry in entries:
            data = {
                'action_time': entry.action_time,
                'message': entry.message,
                'action_type': entry.action_type,
                'user': entry.user.username
            }
            r.rpush(key, data=data)
        r.ltrim(key, 0, 11)
