import os
import polib
from django.utils import unittest
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.client import Client
from transifex.txcommon.tests import utils
from transifex.languages.models import Language
from transifex.resources.models import *
from transifex.resources.backends import ResourceBackend, FormatsBackend
from transifex.resources.formats.pofile import POHandler, POTHandler, \
        PoParseError
from transifex.resources.formats.compilation import Mode
from transifex.resources.tests.lib.base import FormatsBaseTestCase
from transifex.addons.copyright.models import Copyright

from transifex.addons.suggestions.models import Suggestion


TEST_FILES_PATH = os.path.join(
    settings.TX_ROOT, 'resources/tests/lib/pofile/general'
)

class TestPoFile(FormatsBaseTestCase):
    """Suite of tests for the pofile lib."""

    def test_pot_parser(self):
        """POT file tests."""
        # Parsing POT file
        handler = POHandler('%s/tests.pot' %
            os.path.split(__file__)[0])

        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        self.stringset = handler.stringset
        entities = 0

        # POT has no associated language
        self.assertEqual(self.stringset.target_language, None)

        for s in self.stringset:
            # Testing if source entity and translation are the same
            if not s.pluralized:
                self.assertEqual(s.source_entity, s.translation)

            # Testing plural number
            if s.source_entity == '{0} results':
                self.assertEqual(s.rule, 5)

            # Counting number of entities
            if s.rule == 5:
                entities += 1

        # Asserting number of entities - POT file has 3 entries.
        self.assertEqual(entities, 6)

    def test_po_parser_pt_BR(self):
        """Tests for pt_BR PO file."""
        handler = POHandler('%s/pt_BR.po' %
            os.path.split(__file__)[0])


        handler.set_language(self.language)
        handler.parse_file()
        self.stringset = handler.stringset

        nplurals = 0

        for s in self.stringset:

            # Testing plural number
            if s.source_entity == '{0} results':
                self.assertEqual(s.rule, 5)

            if s.source_entity == '{0} result' and s.pluralized:
                nplurals += 1

        # Asserting nplurals based on the number of plurals of the
        # '{0 results}' entity - pt_BR has nplurals=2
        self.assertEqual(nplurals, 2)

    def test_po_parser_pt_BR_with_warning_messages(self):
        """
        Tests if nplural warning is raised for 'pt_BR' PO file loaded as an
        'ar' language.
        """
        handler = POHandler('%s/pt_BR.po' % os.path.split(__file__)[0])
        handler.set_language(self.language_ar)
        handler.parse_file()
        self.assertTrue('nplural' in handler.warning_messages.keys())

    def test_po_parser_ar(self):
        """Tests for ar PO file."""
        handler = POHandler('%s/ar.po' %
            os.path.split(__file__)[0])

        handler.set_language(self.language_ar)
        handler.parse_file()
        self.stringset = handler.stringset
        nplurals = 0

        for s in self.stringset:

            # Testing if source entity and translation are NOT the same
            self.assertNotEqual(s.source_entity, s.translation)

            # Testing plural number
            if s.source_entity == '{0} results':
                self.assertEqual(s.rule, 5)

            if s.source_entity == '{0} result' and s.pluralized:
                nplurals += 1

        # Asserting nplurals based on the number of plurals of the
        # '{0 results}' entity - ar has nplurals=6.
        self.assertEqual(nplurals, 6)

    def _test_po_save2db(self):
        """Test creating source strings from a PO/POT file works"""
        handler = POHandler('%s/tests.pot' %
            os.path.split(__file__)[0])

        l = Language.objects.get(code='en_US')

        handler.set_language(l)
        handler.parse_file(is_source=True)

        r = self.resource

        handler.bind_resource(r)

        handler.save2db(is_source=True)

        self.assertEqual( SourceEntity.objects.filter(resource=r).count(), 6)

        self.assertEqual( len(Translation.objects.filter(source_entity__resource=r,
            language=l)), 7)

        handler.bind_file('%s/ar.po' % os.path.split(__file__)[0])
        l = Language.objects.by_code_or_alias('ar')
        handler.set_language(l)
        handler.parse_file()

        handler.save2db()

        self.assertEqual( SourceEntity.objects.filter(resource=r).count(), 6)

        self.assertEqual( len(Translation.objects.filter(source_entity__resource=r,
            language=l)), 11)

        self._mark_translation_as_reviewed(self.resource,
                [
                    '{0} result',
                    'Location',
                ],
                self.language_ar, 7
        )

        #update resource with the same source file and
        #check that the resource.last_update does not
        #change from its previous value
        last_update = self.resource.last_update
        handler.bind_file('%s/tests.pot' %
            os.path.split(__file__)[0])
        l = Language.objects.get(code='en_US')
        handler.set_language(l)
        handler.parse_file(True)
        handler.save2db(is_source=True)
        self.assertEqual(self.resource.last_update, last_update)

        self.assertEqual( SourceEntity.objects.filter(resource=r).count(), 6)

        self.assertEqual( len(Translation.objects.filter(source_entity__resource=r,
            language=l)), 7)

        return handler

    def _test_po_compile(self, handler):
        """Test compiling po translations"""
        source_compiled_file = os.path.join(os.path.dirname(__file__),
                'en_compiled.po')
        trans_compiled_file = os.path.join(os.path.dirname(__file__),
                'ar_compiled.po')
        trans_compiled_file_reviewed = os.path.join(os.path.dirname(__file__),
                'ar_compiled_for_review.po')
        handler.bind_resource(self.resource)
        handler.set_language(Language.objects.get(code='en_US'))
        compiled_template = handler.compile()
        f = open(source_compiled_file, 'r')
        expected_compiled_template = f.read()
        f.close()
        po = polib.pofile(compiled_template)
        epo = polib.pofile(expected_compiled_template)
        po.metadata['PO-Revision-Date'] = epo.metadata['PO-Revision-Date']
        po.metadata['Last-Translator'] = epo.metadata['Last-Translator']
        compiled_template = str(po)
        self.assertEqual(compiled_template,
                expected_compiled_template)

        handler.set_language(self.language_ar)
        compiled_template = handler.compile()
        f = open(trans_compiled_file, 'r')
        expected_compiled_template = f.read()
        f.close()
        po = polib.pofile(compiled_template)
        epo = polib.pofile(expected_compiled_template)
        po.metadata['PO-Revision-Date'] = epo.metadata['PO-Revision-Date']
        po.metadata['Last-Translator'] = epo.metadata['Last-Translator']
        compiled_template = str(po)
        self.assertEqual(compiled_template,
                expected_compiled_template)

        handler.set_language(self.language_ar)
        compiled_template = handler.compile(mode=Mode.REVIEWED)
        f = open(trans_compiled_file_reviewed, 'r')
        expected_compiled_template = f.read()
        f.close()
        po = polib.pofile(compiled_template)
        epo = polib.pofile(expected_compiled_template)
        po.metadata['PO-Revision-Date'] = epo.metadata['PO-Revision-Date']
        po.metadata['Last-Translator'] = epo.metadata['Last-Translator']
        compiled_template = str(po)
        self.assertEqual(compiled_template,
                expected_compiled_template)

    def test_po_save_and_compile(self):
        handler = self._test_po_save2db()
        self._test_po_compile(handler)

    def test_logical_ids(self):
        """Test po files with logical ids instead of normal strings"""


        # Empty our resource
        SourceEntity.objects.filter(resource=self.resource).delete()

        # Make sure that we have no suggestions to begin with
        self.assertEqual(Suggestion.objects.filter(source_entity__in=
            SourceEntity.objects.filter(resource=self.resource).values('id')).count(), 0)

        # Import file with two senteces
        handler = POHandler('%s/logical_ids/tests.pot' %
            os.path.split(__file__)[0])
        handler.bind_resource(self.resource)
        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        handler.save2db(is_source=True)

        # import pt_BR translation
        handler = POHandler('%s/logical_ids/pt_BR.po' %
            os.path.split(__file__)[0])
        handler.bind_resource(self.resource)
        handler.set_language(self.language)
        handler.parse_file()
        handler.save2db()

        # Make sure that we have all translations in the db
        self.assertEqual(Translation.objects.filter(source_entity__in=
            SourceEntity.objects.filter(resource=self.resource).values('id')).count(), 2)

        source = SourceEntity.objects.get(resource=self.resource)
        en_trans = Translation.objects.get(source_entity__resource=self.resource,
            language = self.resource.source_language)
        pt_trans = Translation.objects.get(source_entity__resource=self.resource,
            language = self.language)

        # Check to see that the correct strings appear as the translations and
        # not the logical id
        self.assertEqual(en_trans.string, "Hello, World!")
        self.assertEqual(pt_trans.string, "Holas, Amigos!")
        self.assertEqual(source.string, "source_1")

    @unittest.skipIf(settings.MAX_STRING_ITERATIONS == 0,
            "Skipping because MAX_STRING_ITERATIONS = 0")
    def test_convert_to_suggestions(self):
        """Test convert to suggestions when importing new source files"""

        # Empty our resource
        SourceEntity.objects.filter(resource=self.resource).delete()

        # Make sure that we have no suggestions to begin with
        self.assertEqual(Suggestion.objects.filter(source_entity__in=
            SourceEntity.objects.filter(resource=self.resource).values('id')).count(), 0)

        # Import file with two senteces
        handler = POHandler('%s/suggestions/tests.pot' %
            os.path.split(__file__)[0])
        handler.bind_resource(self.resource)
        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        handler.save2db(is_source=True)

        # import pt_BR translation
        handler = POHandler('%s/suggestions/pt_BR.po' %
            os.path.split(__file__)[0])
        handler.bind_resource(self.resource)
        handler.set_language(self.language)
        handler.parse_file()
        handler.save2db()

        # Make sure that we have all translations in the db
        self.assertEqual(Translation.objects.filter(source_entity__in=
            SourceEntity.objects.filter(resource=self.resource).values('id')).count(), 5)

        # import source with small modifications
        handler = POHandler('%s/suggestions/tests-diff.pot' %
            os.path.split(__file__)[0])
        handler.bind_resource(self.resource)
        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        handler.save2db(is_source=True)

        # Make sure that all suggestions were added
        self.assertEqual(Suggestion.objects.filter(source_entity__in=
            SourceEntity.objects.filter(resource=self.resource).values('id')).count(), 2)

        # Make both strings are now untranslated
        self.assertEqual(Translation.objects.filter(source_entity__in=
            SourceEntity.objects.filter(resource=self.resource).values('id')).count(), 3)

        # import pt_BR translation again
        handler = POHandler('%s/suggestions/pt_BR.po' %
            os.path.split(__file__)[0])
        handler.bind_resource(self.resource)
        handler.set_language(self.language)
        handler.parse_file()
        handler.save2db()

        # Make sure that we have all translations in the db
        self.assertEqual(Translation.objects.filter(source_entity__in=
            SourceEntity.objects.filter(resource=self.resource).values('id')).count(), 3)

    def test_general_po(self):
        """
        Test with a PO file containing multiple different 'breakable'
        cases.
        """

        # Empty our resource
        SourceEntity.objects.filter(resource=self.resource).delete()

        # Import file with two senteces
        handler = POHandler('%s/general/test.pot' %
            os.path.split(__file__)[0])
        handler.bind_resource(self.resource)
        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        handler.save2db(is_source=True)
        exported_file = polib.pofile(handler.compile())
        for entry in exported_file:
            se = SourceEntity.objects.get(
               string = entry.msgid,
               context = entry.msgctxt or 'None',
               resource = self.resource
            )

            if se.pluralized:
                plurals = Translation.objects.filter(
                    source_entity__resource = self.resource,
                    language = self.resource.source_language,
                    source_entity__string = entry.msgid
                ).order_by('rule')

                plural_keys = {}
                # last rule excluding other(5)
                lang_rules = self.resource.source_language.get_pluralrules_numbers()
                # Initialize all plural rules up to the last
                for p,n in enumerate(lang_rules):
                    plural_keys[str(p)] = ""
                for n,p in enumerate(plurals):
                    plural_keys[str(n)] = p.string

                self.assertEqual(entry.msgstr_plural, plural_keys)

            else:
                trans = se.get_translation(
                    self.resource.source_language.code, rule=5
                )

                self.assertEqual(entry.msgstr, trans.string.encode('utf-8'), "Source '%s'"\
                    " differs from translation %s" % (entry.msgstr,
                    trans.string.encode('utf-8')))

    def test_wrong_po(self):
        handler = POHandler(os.path.join(
                os.path.dirname(__file__), 'wrong.pot')
        )
        handler.bind_resource(self.resource)
        handler.set_language(self.resource.source_language)
        self.assertRaises(PoParseError, handler.parse_file, is_source=True)


class TestPoFileHeaders(FormatsBaseTestCase):
    """Test PO File library support for PO file headers."""

    def _load_pot(self):
        test_file = os.path.join(TEST_FILES_PATH, 'test.pot')
        # First empty our resource
        self.resource.entities.all().delete()
        # Load file
        handler = POHandler(test_file)
        handler.bind_resource(self.resource)
        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        handler.save2db(is_source=True)
        return handler

    def test_poheader_team_url(self):
        """Test team header when no main list is defined (URL)."""
        self.assertFalse(self.team.mainlist)
        handler = self._load_pot()
        handler.set_language(self.language)
        pofile = handler.compile()
        self.assertTrue("Portuguese (Brazil)" in pofile)
        self.assertTrue(self.urls['team'] in pofile)

    def test_poheader_team_email(self):
        """Test team header when main list is defined."""
        self.team.mainlist = "test@test.com"
        self.team.save()
        handler = self._load_pot()
        handler.set_language(self.language)
        pofile = handler.compile()
        self.assertTrue("Portuguese (Brazil)" in pofile)
        self.assertFalse(self.urls['team'] in pofile)
        self.assertTrue(self.team.mainlist in pofile)


class TestPoFileCopyright(FormatsBaseTestCase):
    """Test copyright lines for translators in po files."""

    def setUp(self):
        self.handler = POHandler()
        self.matched_lines = [
            '# John Doe, 2011.',
            '# John Doe <john@doe>, 2011.',
            '# John Doe <john@doe>, 2011, 2012.',
            '# Jogn Doe, 2011',
        ]
        self.unmatched_lines = [
            '#John Doe, 2011',
            '# John <john>, 20123',
            '# Copyright, 2011, John Doe.',
            'asdas, 2011',
        ]
        super(TestPoFileCopyright, self).setUp()

    def test_match_lines(self):
        for line in self.matched_lines:
            m = self.handler._get_copyright_from_line(line)
            self.assertTrue(m is not None)
        for line in self.unmatched_lines:
            m = self.handler._get_copyright_from_line(line)
            self.assertTrue(m is None)

    def test_copyright_on_save(self):
        handler = POHandler(os.path.join(
                os.path.dirname(__file__), 'copyright.po')
        )
        handler.bind_resource(self.resource)
        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        handler.save2db(is_source=True)
        self.assertIn("AB", handler.compile())

    def test_headers_on_pot(self):
        handler = POHandler(os.path.join(
                os.path.dirname(__file__), 'tests.pot')
        )
        handler.bind_resource(self.resource)
        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        handler.save2db(is_source=True)
        self.assertNotIn("FIRST AUTHOR", handler.compile())
        handler = POTHandler(os.path.join(
                os.path.dirname(__file__), 'tests.pot')
        )
        handler.bind_resource(self.resource)
        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        handler.save2db(is_source=True)
        self.assertIn("FIRST AUTHOR", handler.compile())

    def test_order(self):
        handler = POHandler(os.path.join(
                os.path.dirname(__file__), 'copyright.po')
        )
        handler.bind_resource(self.resource)
        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        handler.save2db(is_source=True)
        cr = Copyright.objects.assign(
            language=self.language_en, resource=self.resource,
            owner='CC', year='2014')
        cr = Copyright.objects.assign(
            language=self.language_en, resource=self.resource,
            owner='ZZ', year='2014')
        cr = Copyright.objects.assign(
            language=self.language_en, resource=self.resource,
            owner='BA', year='2015')
        compiled_template = handler.compile()
        lines_iterator = compiled_template.split("\n")
        for n, line in enumerate(lines_iterator):
            if line == "# Translators:":
                break
        line = lines_iterator[n + 1]
        self.assertTrue('AB' in line)
        line = lines_iterator[n + 3]
        self.assertTrue('BA' in line)
        line = lines_iterator[n + 4]
        self.assertTrue('CC' in line)
        line = lines_iterator[n + 6]
        self.assertTrue('ZZ' in line)


class TestPolibEmptyComments(unittest.TestCase):
    """Check that no error is raised for empty comment lines from polib.

    Polib v0.7 raised IOError for po files that had empty comments.
    """

    def test_empty_comment_file(self):
        filename = os.path.join(
            settings.TX_ROOT, 'resources/tests/lib/pofile/empty_comment.po'
        )
        polib.pofile(filename)
