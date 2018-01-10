# -*- coding: utf-8 -*-

import os, chardet
import unittest
from transifex.resources.tests.lib.base import FormatsBaseTestCase
from transifex.languages.models import Language
from transifex.resources.models import *
from transifex.resources.formats.compilation import Mode
from transifex.resources.formats.javaproperties import  JavaPropertiesHandler, \
        JavaParseError, convert_to_ascii, convert_to_unicode

from transifex.addons.suggestions.models import Suggestion

class TestJavaProperties(FormatsBaseTestCase):
    """Suite of tests for the propertiesfile lib."""

    def setUp(self):
        super(TestJavaProperties, self).setUp()
        self.resource.i18n_method = 'PROPERTIES'
        self.resource.save()

    def test_escaped(self):
        j = JavaPropertiesHandler()
        self.assertFalse(j._is_escaped(r"es blah", 2))
        self.assertTrue(j._is_escaped(r"e\ blah", 2))
        self.assertFalse(j._is_escaped(r"\\ blah", 2))
        self.assertTrue(j._is_escaped(r"e\\\ blah", 4))

    def test_accept(self):
        parser = JavaPropertiesHandler()
        self.assertTrue(parser.accepts('PROPERTIES'))

    def test_split(self):
        j = JavaPropertiesHandler()
        res = j._split("asd sadsf")
        self.assertEqual(res[0], "asd")
        self.assertEqual(res[1], "sadsf")
        res = j._split("asd=sadsf")
        self.assertEqual(res[0], "asd")
        self.assertEqual(res[1], "sadsf")
        res = j._split("asd:sadsf")
        self.assertEqual(res[0], "asd")
        self.assertEqual(res[1], "sadsf")
        res = j._split("asd\tsadsf")
        self.assertEqual(res[0], "asd")
        self.assertEqual(res[1], "sadsf")
        res = j._split(r"asd\ =sadsf")
        self.assertEqual(res[0], "asd\ ")
        self.assertEqual(res[1], "sadsf")
        res = j._split(r"asd = sadsf")
        self.assertEqual(res[0], "asd")
        self.assertEqual(res[1], "sadsf")
        res = j._split(r"asd\\=sadsf")
        self.assertEqual(res[0], r"asd\\")
        self.assertEqual(res[1], "sadsf")
        res = j._split(r"asd\\\=sadsf")
        self.assertEqual(res[0], r"asd\\\=sadsf")
        self.assertEqual(res[1], None)
        res = j._split(r"asd\\\\=sadsf")
        self.assertEqual(res[0], r"asd\\\\")
        self.assertEqual(res[1], "sadsf")
        res = j._split(r"Key21\:WithColon : Value21")
        self.assertEqual(res[0], r"Key21\:WithColon")
        self.assertEqual(res[1], "Value21")

    def test_properties_parser(self):
        """PROPERTIES file tests."""
        # Parsing PROPERTIES file
        handler = JavaPropertiesHandler(
            os.path.join(os.path.dirname(__file__), 'complex.properties')
        )

        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        self.stringset = handler.stringset
        entities = 0
        translations = 0
        for s in self.stringset:
            entities += 1
            if s.translation.strip() != '':
                translations += 1

        # Asserting number of entities - PROPERTIES file has 25 entries.
        # we ignore keys without a value
        self.assertEqual(entities, 25)
        self.assertEqual(translations, 25)

    def _test_properties_save2db(self):
        """Test creating source strings from a PROPERTIES file works"""
        handler = JavaPropertiesHandler(
            os.path.join(os.path.dirname(__file__), 'complex.properties')
        )

        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)

        r = self.resource
        l = self.resource.source_language

        handler.bind_resource(r)

        handler.save2db(is_source=True)

        # Check that all 25 entities are created in the db
        self.assertEqual( SourceEntity.objects.filter(resource=r).count(), 25)

        # Check that all source translations are there
        self.assertEqual(
            len(Translation.objects.filter(source_entity__resource=r, language=l)), 25
        )

        # Import and save the finish translation
        handler.bind_file(os.path.join(os.path.dirname(__file__),'complex_hi_IN-ascii.properties'))
        l = Language.objects.get(code='hi_IN')
        handler.set_language(l)
        handler.parse_file()

        entities = 0
        translations = 0
        for s in handler.stringset:
            entities += 1
            if s.translation.strip() != '':
                translations += 1

        self.assertEqual(entities, 23)
        self.assertEqual(translations, 23)

        handler.save2db()
        # Check if all Source strings are untouched
        self.assertEqual(SourceEntity.objects.filter(resource=r).count(), 25)
        # Check that all translations are there
        self.assertEqual(
            len(Translation.objects.filter(resource=r, language=l)), 23
        )
        self._mark_translation_as_reviewed(self.resource,
                ['Key00', 'Key02'], l, 2)
        return handler

    def _test_properties_compile(self, handler):
        source_compiled_file = os.path.join(
            os.path.dirname(__file__), 'complex_compiled.properties'
        )
        trans_compiled_file_for_use = os.path.join(
            os.path.dirname(__file__), 'complex_hi_IN-ascii_compiled.properties'
        )
        trans_compiled_file_for_review = os.path.join(
            os.path.dirname(__file__),
            'complex_hi_IN-ascii_compiled_for_review.properties'
        )
        trans_compiled_file_for_translation = os.path.join(
            os.path.dirname(__file__),
            'complex_hi_IN-ascii_compiled_for_translation.properties'
        )
        self._check_compilation(handler, self.resource,
                self.resource.source_language, source_compiled_file
        )
        l = Language.objects.get(code='hi_IN')
        self._check_compilation(handler, self.resource, l,
                trans_compiled_file_for_use
        )
        self._check_compilation(handler, self.resource, l,
                trans_compiled_file_for_review, Mode.REVIEWED
        )
        self._check_compilation(handler, self.resource, l,
                trans_compiled_file_for_translation, Mode.TRANSLATED
        )

    def test_properties_save_and_compile(self):
        handler = self._test_properties_save2db()
        self._test_properties_compile(handler)

    def test_convert_unicode(self):
        """Test the conversion of a series of bytes that represent a unicode
        character to the character itself.
        """
        parser = JavaPropertiesHandler()
        for a in u'ΑΒΓΔΕΖΗΘ':
            s = convert_to_ascii(a)
            c = convert_to_unicode(s)
            self.assertEquals(a, c)

    def test_unicode_conversion(self):
        """Test that the unicode codepoints are converted to unicode strings."""
        parser = JavaPropertiesHandler()
        line = r'key = \u03b1'
        key, value, old_value = parser._key_value_from_line(line)
        self.assertEquals(value, u'α')

