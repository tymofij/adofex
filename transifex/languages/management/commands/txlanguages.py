# -*- coding: utf-8 -*-
"""
File containing the necessary mechanics for the txlanguages management command.
"""
from optparse import make_option, OptionParser
import os.path
import sys
from django.db import transaction
from django.utils import simplejson
from django.core import serializers
from django.core.management.base import (BaseCommand, LabelCommand, CommandError)
from django.conf import settings
from transifex.languages.models import Language

_DEFAULT_FIXTURE = 'languages/fixtures/all_languages.json'

_help_text = ('Create, Update, or Export the default languages.\n'
        '\t--export [filename] for export to stdout or to the filename '
        '(filename is optional)\n'
        '\t--import [filename] to import from a file. If not given will try '
        'to load data from the default fixture file (%s)\n' %
        _DEFAULT_FIXTURE)


class Command(LabelCommand):
    """
    Management Command Class about language updates
    """
    help = _help_text
    option_list = LabelCommand.option_list + (
        make_option('--import', action='store_true',
                    dest='doimport', default=False,
            help='Import data from a file or from the default '),
        make_option('--export', action='store_true',
                    dest='doexport', default=False,
            help='Be more verbose in reporting progress.'),
    )

    requires_model_validation = False
    can_import_settings = True

    def handle(self, *args, **options):
        verbose = int(options.get('verbosity'))
        doimport = options.get('doimport')
        doexport = options.get('doexport')

        if doimport and doexport:
            raise CommandError("The arguments '--import' and '--export' can "
                "not be used simultaneously.")

        if doimport:
            import_lang(filename=get_filename(args), verbose=verbose)
            return
        if doexport:
            export_lang(filename=get_filename(args), verbose=verbose)
            return

        #default functionality of previous version.
        import_lang(verbose=verbose)

def export_lang(filename=None, verbose=False):
    """
    Export the already existing languages

    Just like the dumpdata does but just for a specific model it serializes the
    models contents and depending on the filename it either writes to it or to
    stdout.
    """
    print 'Exporting languages...'
    data = serializers.serialize("json", Language.objects.all().order_by('id'),
        indent=2)
    if filename:
        storefile = None
        try:
            storefile = open(filename, 'w')
            storefile.write(data)
        except:
            pass
        if storefile:
            storefile.close()
    else:
        sys.stdout.write(data)

def import_lang(filename=None, verbose=False):
    """
    Import languages

    Input (optional) : filepath(relative or full) to the json file
    If not given load the default fixture.

    Its logic is simple:
        1) Open the fixture file
        2) Read the json data
        3) For each model's object at the json data update references in the db
    """
    if verbose:
        sys.stdout.write('Importing initial set of languages...\n')

    if not filename:
        filename = os.path.abspath(os.path.join(settings.TX_ROOT,
                                                _DEFAULT_FIXTURE))
        if not os.path.exists(filename):
            raise CommandError("Could not find fixture %s." % filename)

    if verbose:
        print (u'Importing languages from %s' % filename).encode('UTF-8')

    try:
        datafile = open(filename, 'r')
    except IOError:
        print (u'Cannot open %s' % filename).encode('UTF-8')
        return
    except:
        print "Unexpected error: %s" % sys.exc_info()[0]
        return

    data = simplejson.load(datafile)
    if verbose:
        fill_the_database_verbose(data)
    else:
        fill_the_database_silently(data)

@transaction.commit_on_success
def fill_the_database_verbose(data):
    """
    Update the language object and be verbose about it.
    """
    for obj in data:
        fields = obj['fields']
        lang, created = Language.objects.get_or_create(code=fields['code'])
        if created:
            print (u'Creating %s language (%s)' % (fields['name'], fields['code'])).encode('UTF-8')
        else:
            print (u'Updating %s language (%s)' % (fields['name'], fields['code'])).encode('UTF-8')
        fill_language_data(lang, fields)

@transaction.commit_on_success
def fill_the_database_silently(data):
    """
    Update the language object without producing any more noise.
    """
    for obj in data:
        fields = obj['fields']
        lang, created = Language.objects.get_or_create(code=fields['code'])
        fill_language_data(lang, fields)

def fill_language_data(lang, fields):
    """
    Based on the fields update the lang object.
    """
    lang.code_aliases = fields['code_aliases']
    lang.name = fields['name']
    lang.description = fields['description']
    lang.specialchars = fields['specialchars']
    lang.nplurals = fields['nplurals']
    lang.pluralequation = fields['pluralequation']
    lang.rule_zero = fields['rule_zero']
    lang.rule_one = fields['rule_one']
    lang.rule_two = fields['rule_two']
    lang.rule_few = fields['rule_few']
    lang.rule_many = fields['rule_many']
    lang.rule_other = fields['rule_other']
    lang.save()

def get_filename(args):
    ret=None
    try:
        ret=args[0]
    except:
        pass
    return ret
