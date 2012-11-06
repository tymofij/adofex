# -*- coding: UTF-8 -*-

import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, IntegrityError

from transifex.languages.models import Language
from transifex.projects.models import Project

class Command(BaseCommand):
    help = "Removes strings identical to English"

    def handle(self, **options):
        from transifex.resources.models import Resource, SourceEntity, Translation
        from transifex.resources.handlers import invalidate_stats_cache

        en = Language.objects.get(code='en-US')
        p = Project.objects.get(slug="bzmenu")
        for r in Resource.objects.filter(project=p):
            for orig in Translation.objects.filter(resource=r, language=en):
                Translation.objects.exclude(language=en
                    ).filter(resource=r, string=orig.string).delete()

        # reset Stats
        for r in Resource.objects.filter(project=p):
            for l in Language.objects.filter(pk__in=Translation.objects.filter(resource=r
                    ).order_by('language').values_list('language', flat=True).distinct()):
                        invalidate_stats_cache(r, l)
