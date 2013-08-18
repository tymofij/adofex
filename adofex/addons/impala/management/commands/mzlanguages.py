# -*- coding: UTF-8 -*-
from django.conf import settings
from django.core.management.base import NoArgsCommand, CommandError
from django.db import transaction, IntegrityError
from django.utils import simplejson

import os
from transifex.languages.models import Language
from transifex.languages.management.commands.txlanguages import _DEFAULT_FIXTURE, fill_language_data

mz_codes = open(os.path.join(os.path.dirname(__file__), 'all-locales')).read().split()
# languages not present even in the fixture
missing_langs = {
    'dv': 'Maldivian',
    'dsb': 'Lower Sorbian',
    'ach': 'Acholi',
    'ff': 'Pulaar-Fulfulde',
    'lij': 'Ligurian',
    'sah': 'Sakha',
}
tx_data = simplejson.load(file(os.path.abspath(os.path.join(settings.TX_ROOT, _DEFAULT_FIXTURE))))

class Command(NoArgsCommand):
    help = "Remove languages not used by Mozilla, tweak codes, add missing"

    @transaction.commit_on_success
    def handle_noargs(self, **options):
        # this is to be run after txlanguages, doing cleanup
        for l in Language.objects.all():
            # already there
            if l.code in mz_codes or l.code in missing_langs.keys():
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

        # fill in missing languages from fixture
        fill_the_database_verbose(tx_data)

        # fill in missing languages from list
        for (code, name) in missing_langs.items():
            if not Language.objects.filter(code=code).exists():
                print "Adding {} ({})".format(name, code)
                Language(name=name, code=code).save()

        # check that all moz ones are present
        for code in mz_codes:
            try:
                Language.objects.get(code=code)
            except Language.DoesNotExist:
                print "{} is still missing".format(code)


@transaction.commit_on_success
def fill_the_database_verbose(data):
    """
    Update the language object and be verbose about it.
    """
    for obj in data:
        if obj['fields']['code'] not in mz_codes:
            continue
        fields = obj['fields']
        lang, created = Language.objects.get_or_create(code=fields['code'])
        if created:
            print (u'Creating %s language (%s)' % (fields['name'], fields['code'])).encode('UTF-8')
        else:
            print (u'Updating %s language (%s)' % (fields['name'], fields['code'])).encode('UTF-8')
        fill_language_data(lang, fields)