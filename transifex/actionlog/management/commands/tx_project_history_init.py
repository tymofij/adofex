# -*- coding: utf-8 -*-

from __future__ import absolute_import
from django.core.management.base import BaseCommand, CommandError
from django.contrib.contenttypes.models import ContentType
from transifex.actionlog.models import LogEntry
from transifex.actionlog.queues import redis_key_for_project
from datastores.txredis import TxRedisMapper
from transifex.projects.models import Project


class Command(BaseCommand):

    help = "Populate the latest history of a project."

    def handle(self, *args, **options):
        if not args:
            projects = Project.objects.all().iterator()
        else:
            projects = Projects.objects.filter(slug__in=args).iterator()
        for idx, p in enumerate(projects):
            if int(options.get('verbosity')) > 1:
                self.stdout.write("Project %d: %s\n" % (idx, p.slug))
            self._populate_history(p)

    def _populate_history(self, project):
        """Store the latest action log items for the specified project."""
        ids = [project.id]
        if project.is_hub:
            ids += project.outsourcing.all().values_list('id', flat=True)
        entries = LogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(Project),
            object_id__in=ids
        )[:5]
        r = TxRedisMapper()
        key = redis_key_for_project(project)
        for entry in entries:
            data = {
                'action_time': entry.action_time,
                'message': entry.message,
                'action_type': entry.action_type
            }
            r.rpush(key, data=data)
        r.ltrim(key, 0, 4)

