# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand, CommandError
from django.db.models import get_model
from django.contrib.contenttypes.models import ContentType
from transifex.actionlog.models import LogEntry
from transifex.actionlog.queues import redis_key_for_resource
from datastores.txredis import TxRedisMapper


class Command(BaseCommand):

    help = (
        "Populate the latest history of a resource.\n"
        "You can specify the slug(s) of a project to initialize "
        "only the resources of those projects."
    )

    def handle(self, *args, **options):
        Resource = get_model('resources', 'Resource')
        if not args:
            resources = Resource.objects.all().iterator()
        else:
            resources = Resource.objects.filter(
                project__slug__in=args
            ).iterator()
        for idx, r in enumerate(resources):
            if int(options.get('verbosity')) > 1:
                self.stdout.write("Resource %d: %s\n" % (idx, r.slug))
            self._populate_history(r)

    def _populate_history(self, resource):
        """Store the latest action log items for the specified resources."""
        Resource = get_model('resources', 'Resource')
        entries = LogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(Resource),
            object_id=resource.id
        )[:5]
        r = TxRedisMapper()
        key = redis_key_for_resource(resource)
        for entry in entries:
            data = {
                'action_time': entry.action_time,
                'message': entry.message,
                'action_type': entry.action_type,
            }
            r.rpush(key, data=data)
        r.ltrim(key, 0, 4)

