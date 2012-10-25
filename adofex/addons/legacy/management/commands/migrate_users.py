# -*- coding: utf-8 -*-

import sys
from datetime import datetime
from transifex.projects.models import Project
from transifex.languages.models import Language

from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django.utils.encoding import smart_unicode
from legacy import models as legacy
from django.db import transaction, IntegrityError

from userena.models import UserenaSignup
from userena import signals as userena_signals
from userena import settings as userena_settings

from legacy.actions import migrate_user

class Command(BaseCommand):
    help = "Copies all users from legacy Babelzilla DB into Transifex"

    @transaction.commit_manually
    def handle(self, **options):
        i = 0
        for u in legacy.User.objects.exclude(username__in=('june', 'seaousak')).filter(username='tymofiy'):
            migrate_user(u.username)

            i += 1
            if i % 10 == 0:
                sys.stdout.write('.')
                sys.stdout.flush()

            if i % 1000 == 0:
                transaction.commit()

        # final commit
        transaction.commit()