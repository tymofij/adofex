# -*- coding: UTF-8 -*-
from django.core.management.base import NoArgsCommand, CommandError
from django.db import transaction, IntegrityError

import os
from transifex.languages.models import Language

class Command(NoArgsCommand):
    help = "Remove languages not used by Mozilla, tweak codes, add missing"

    missing_langs = {
        'lg': 'Luganda',
        'dsb': 'Lower Sorbian',
    }

    def handle_noargs(self, **options):
        codes = open(os.path.join(os.path.dirname(__file__), 'all-locales')
            ).read().split()
        codes.extend([
            "en-US", # US English, not included because it is default
            "hsb", # Upper Sorbian
            "ms", # Malay - see bug 286080
            ])

        for l in Language.objects.all():
            # already there
            if l.code in codes:
                print "Found %s" % l
                continue
            # Mozilla uses dashes, not underscores
            if l.code.replace("_", "-") in codes:
                print "Tweaking code for %s" % l
                l.code = l.code.replace("_", "-")
                l.save()
                continue
            # probably some unneeded double, like af_ZA - af is enough
            print "Deleting %s" % l
            l.delete()
        # Transifex at the moment does not have Luganda language in fixture
        for (code, name) in self.missing_langs.items():
            if not Language.objects.filter(code=code).exists():
                print "Adding {} ({})".format(name, code)
                Language(name=name, code=code).save()
