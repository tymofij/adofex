# -*- coding: utf-8 -*-

import os
from transifex.languages.models import Language
from transifex.resources.models import Resource
from transifex.resources.formats.joomla import JoomlaINIHandler
from transifex.resources.formats.compilation import Mode
from transifex.resources.tests.lib.base import FormatsBaseTestCase
from transifex.resources.models import Translation

class TestJoomlaIni(FormatsBaseTestCase):
    """Tests for Joomla init files."""

    def setUp(self):
        super(TestJoomlaIni, self).setUp()
        self.file = os.path.join(os.path.dirname(__file__), 'example1.6.ini')
        self.trans_file = os.path.join(os.path.dirname(__file__),
                'example_ar_1.6.ini')
        self.parser = JoomlaINIHandler(self.file)
        self.parser.set_language(Language.objects.by_code_or_alias("en_US"))
        self.resource.i18n_type = 'INI'
        self.resource.save()

    def test_accept(self):
        self.assertTrue(self.parser.accepts('INI'))

    def test_quote_removal(self):
        self.parser.parse_file(is_source=True)
        for s in self.parser.stringset:
            self.assertFalse(s.translation.startswith('"'))
        self.compare_to_actual_file(self.parser, self.file)

    def test_string_count(self):
        self.parser.parse_file(is_source=True)
        entities = 0
        translations = 0
        for s in self.parser.stringset:
            entities += 1
            if s.translation.strip() != '':
                translations += 1
        self.assertEqual(entities, 3)
        self.assertEqual(translations, 3)

    def test_quotes_on_previous_version(self):
        file_ = os.path.join(os.path.dirname(__file__), 'example1.5.ini')
        self.parser.bind_file(file_)
        self.parser.parse_file(is_source=True)
        self.compare_to_actual_file(self.parser, file_)

    def test_newlines(self):
        file_ = os.path.join(os.path.dirname(__file__), 'newline.ini')
        r = Resource.objects.create(
            slug="joomla", name="Joomla", i18n_type="INI",
            source_language=Language.objects.by_code_or_alias('en'),
            project=self.project
        )
        self.parser.bind_file(file_)
        self.parser.bind_resource(r)
        self.parser.parse_file(is_source=True)
        self.parser.save2db(is_source=True)
        compiled_template = self.parser.compile()
        self.assertIn(r'\n', compiled_template)

    def test_key_translation(self):
        content = ';test\nKEY_OFFLINE="OFFLINE"'
        self.parser.bind_content(content)
        self.parser.parse_file(is_source=True)
        self.assertEquals(self.parser.template.count('tr'), 1)
        self.assertTrue('=' in self.parser.template)
        self.assertTrue('tr' in self.parser.template)

    def test_translation_escaping(self):
        """Test for a Joomla 1.6 INI file"""
        content = ';test\nKEY1="Translation with "_QQ_"quotes"_QQ_""'\
                  '\nKEY2="Translation with a quote &quot;"'
        self.parser.bind_content(content)
        self.parser.parse_file(is_source=True)
        translation_strings = []
        for s in self.parser.stringset:
            translation_strings.append(s.translation)
        self.assertEqual(translation_strings, ['Translation with "quotes"',
                'Translation with a quote "'])

        """Test for a Joomla 1.5 INI file"""
        content = 'KEY1=Translation with &quot;quotes&quot;'\
                  '\nKEY2=Translation with a quote &quot;'
        self.parser.bind_content(content)
        self.parser.parse_file(is_source=True)
        translation_strings = []
        for s in self.parser.stringset:
            translation_strings.append(s.translation)
        self.assertEqual(translation_strings, ['Translation with "quotes"',
                'Translation with a quote "'])

        """Test unescaping of new lines during parsing"""
        content = 'KEY1=Translation\\nwith new line \\r\\n'
        self.parser.bind_content(content)
        self.parser.parse_file(is_source=True)
        self.assertEqual(len(self.parser.stringset), 1)
        for s in self.parser.stringset:
            translation_string = s.translation
        self.assertEqual(translation_string, 'Translation\nwith new line \r\n')

    def apply_translation(self, t, compiler):
        t = super(TestJoomlaIni, self).get_translation(t, compiler)
        return compiler.jformat.get_compilation(t)

    def _test_save2db(self):
        """Test saving Joomla INI files"""
        handler = self._save_source(JoomlaINIHandler(), self.resource,
                self.file, 3, 3)
        handler = self._save_translation(handler, self.resource,
                self.language_ar, self.trans_file, 2)

        self._mark_translation_as_reviewed(self.resource, ['KEY1'],
                self.language_ar, 1)

        return handler

    def _test_compile(self, handler):
        source_compiled_file = os.path.join(
            os.path.dirname(__file__), 'example1.6.ini'
        )
        trans_compiled_file_for_use = os.path.join(
            os.path.dirname(__file__), 'example1.6_ar_compiled_for_use.ini'
        )
        trans_compiled_file_for_review = os.path.join(
            os.path.dirname(__file__), 'example1.6_ar_compiled_for_review.ini'
        )
        trans_compiled_file_for_translation = os.path.join(
            os.path.dirname(__file__), 'example1.6_ar_compiled_for_translation.ini'
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
