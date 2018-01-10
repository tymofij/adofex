import os
import re
import unittest
from transifex.resources.tests.lib.base import FormatsBaseTestCase
from transifex.languages.models import Language
from transifex.resources.models import *
from transifex.resources.formats.compilation import Mode
from transifex.resources.formats.strings import AppleStringsHandler, \
        StringsParseError

from transifex.addons.suggestions.models import Suggestion


class TestAppleStrings(FormatsBaseTestCase):
    """Suite of tests for the strings file lib."""

    def setUp(self):
        super(TestAppleStrings, self).setUp()
        self.resource.i18n_method = 'STRINGS'
        self.resource.save()

    def test_regex(self):
        """Test regex used in the parser"""
        p = re.compile(r'(?P<line>(("(?P<key>[^"\\]*(?:\\.[^"\\]*)*)")|'\
                r'(?P<property>\w+))\s*=\s*"(?P<value>[^"\\]*(?:\\.[^"\\]'\
                r'*)*)"\s*;)', re.U)
        c = re.compile(r'\s*/\*(.|\s)*?\*/\s*', re.U)
        ws = re.compile(r'\s+', re.U)

        good_lines = [
                      '"key" = "value";',
                      'key = "value";',
                      '"key"\t=\n\t"value"  \n ;',
                      '"key with \\" double quote"\n=\t"value with \\" double quote";',
                      '''"key with ' single quote"\t=\n"Value with ' single quote";''',
                      ]
        bad_lines = [
                     '"key = "value";',
                     '"key" = "value"',
                     '"key" foo" = "value \"foo";',
                     '"key" = "value " foo";',
                     '"key\' = "value";',
                     'key foo = "value";',
                     'key = value',
                     ]
        good_comment = '/* foo\n\tfoo\'"@ $***/'
        bad_comments = ['//foo\n',
                        '/*foo*',
                        '*foo*',
                        ]
        whitespaces = ['\t','\n','\r', ' ']

        for i in good_lines:
            self.assertTrue(p.match(i))

        for i in bad_lines:
            self.assertFalse(p.match(i))

        self.assertTrue(c.match(good_comment))

        for i in bad_comments:
            self.assertFalse(c.match(i))

        for i in whitespaces:
            self.assertTrue(ws.match(i))

    def test_strings_parser(self):
        """STRINGS parsing tests."""
        # Parsing STRINGS content
        files = ['test_utf_16.strings', 'test_utf_8.strings',
                'test_utf_8_with_BOM.strings',]
        for i in range(1, 9):
            files.append('bad%d.strings'%i)
        for file_ in files:
            handler = AppleStringsHandler()
            handler.bind_file(os.path.join(os.path.dirname(__file__), file_))
            handler.set_language(self.resource.source_language)
            if file_ in ['test_utf_16.strings', 'test_utf_8.strings',
                    'test_utf_8_with_BOM.strings']:
                handler.parse_file(is_source=True)
                self.stringset = handler.stringset
                entities = 0
                translations = 0
                for s in self.stringset:
                    entities += 1
                    if s.translation.strip() != '':
                        translations += 1
                if file_ == 'test_utf_8_with_BOM.strings':
                    count = 1
                else:
                    count = 4
                self.assertEqual(entities, count)
                self.assertEqual(translations, count)
            else:
                self.assertRaises(StringsParseError, handler.parse_file, is_source=True)

    def _test_save2db(self):
        """Test saving Apple Strings files"""
        source_file = os.path.join(
                os.path.dirname(__file__), 'test_utf_16.strings'
        )
        trans_file = os.path.join(
                os.path.dirname(__file__), 'test_translation.strings'
        )
        handler = self._save_source(AppleStringsHandler(), self.resource,
                source_file, 4, 4)
        handler = self._save_translation(handler, self.resource,
                self.language_ar, trans_file, 2)

        self._mark_translation_as_reviewed(self.resource, ['key2'],
                self.language_ar, 1)

        return handler

    def _test_compile(self, handler):
        source_compiled_file = os.path.join(
            os.path.dirname(__file__), 'test_utf_16_compiled.strings'
        )
        trans_compiled_file_for_use = os.path.join(
            os.path.dirname(__file__),
            'test_translation_compiled_for_use.strings'
        )
        trans_compiled_file_for_review = os.path.join(
            os.path.dirname(__file__),
            'test_translation_compiled_for_review.strings'
        )
        trans_compiled_file_for_translation = os.path.join(
            os.path.dirname(__file__),
            'test_translation_compiled_for_translation.strings'
        )
        self._check_compilation(handler, self.resource,
                self.resource.source_language, source_compiled_file
        )
        self._check_compilation(handler, self.resource, self.language_ar,
                trans_compiled_file_for_use
        )
        self._check_compilation(handler, self.resource, self.language_ar,
                trans_compiled_file_for_review, Mode.REVIEWED
        )
        self._check_compilation(handler, self.resource, self.language_ar,
                trans_compiled_file_for_translation, Mode.TRANSLATED
        )

    def test_save_and_compile(self):
        handler = self._test_save2db()
        self._test_compile(handler)
