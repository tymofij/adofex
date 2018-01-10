# -*- coding: utf-8 -*-

"""
Tests for the builders module.
"""

from __future__ import absolute_import
from transifex.txcommon.tests.base import BaseTestCase
from transifex.resources.models import Resource, Translation, SourceEntity
from transifex.resources.formats.compilation import *


class TestTranslationsBuilders(BaseTestCase):
    """Test the various translation builders."""

    def test_all_builder(self):
        """Test that the AllTransaltionsBuilder correctly returns
        all translations.
        """
        builder = AllTranslationsBuilder(self.resource, self.language_en)
        translations = builder()
        self.assertEquals(len(translations), 1)
        self.translation_en.delete()
        translations = builder()
        self.assertEquals(translations, {})
        self._has_correct_normal_format(translations)

    def test_all_builder_pluralized(self):
        """Test the AllTranslationsBiuilder in the pluralized case."""
        builder = AllTranslationsBuilder(self.resource, self.language_en)
        builder.pluralized = True
        translations = builder()
        self.assertEquals(len(translations), 1)
        self._has_correct_plural_format(translations)
        self.translation_en.delete()
        translations = builder()
        self.assertEquals(translations, {})

    def test_empty_builder(self):
        """Test that the EmptyTranslationsBuilder always returns an empty
        dictionary.
        """
        builder = EmptyTranslationsBuilder(self.resource, self.language_en)
        translations = builder()
        self.assertEquals(translations, {})
        self.translation_en.delete()
        translations = builder()
        self.assertEquals(translations, {})
        self._has_correct_normal_format(translations)

    def test_empty_builder_pluralized(self):
        """Test the EmptyTranslationsBuilder in the pluralized case."""
        builder = EmptyTranslationsBuilder(self.resource, self.language_en)
        translations = builder()
        self.assertEquals(translations, {})
        self._has_correct_plural_format(translations)
        self.translation_en.delete()
        translations = builder()
        self.assertEquals(translations, {})

    def test_source_builder(self):
        """Test that the SourceTranslationsBuilder uses source strings
        instead of empty translations.
        """
        builder = SourceTranslationsBuilder(self.resource, self.language_ar)
        translations = builder()
        self.assertEquals(len(translations), 1)
        self.translation_ar.delete()
        translations = builder()
        self.assertEquals(len(translations), 1)
        self._has_correct_normal_format(translations)

    def test_source_builder_pluralized(self):
        """Test that the SourceTranslationsBuilder uses source strings
        instead of empty translations in the pluralized case.
        """
        builder = SourceTranslationsBuilder(self.resource, self.language_ar)
        builder.pluralized = True
        translations = builder()
        self.assertEquals(len(translations), 1)
        self.translation_ar.delete()
        translations = builder()
        self.assertEquals(len(translations), 1)
        self._has_correct_plural_format(translations)

    def test_reviewed_builder(self):
        """Test the ReviewedTranslationsBuilder builder returns only
        reviewed strings.
        """
        builder = ReviewedTranslationsBuilder(self.resource, self.language_ar)
        translations = builder()
        self.assertEquals(len(translations), 0)
        self.translation_ar.reviewed = True
        self.translation_ar.save()
        translations = builder()
        self._has_correct_normal_format(translations)
        self.assertEquals(len(translations), 1)
        self.assertEquals(
            translations.keys()[0], self.translation_ar.source_entity_id
        )

    def test_reviewed_builder_pluralized(self):
        """Test the ReviewedTranslationsBuilder builder, when pluralized."""
        builder = ReviewedTranslationsBuilder(self.resource, self.language_ar)
        builder.pluralized = True
        translations = builder()
        self.assertEquals(len(translations), 0)
        self.translation_ar.reviewed = True
        self.translation_ar.save()
        translations = builder()
        self.assertEquals(len(translations), 1)
        self.assertEquals(
            translations.keys()[0], self.translation_ar.source_entity_id
        )
        self.assertEquals(len(translations.values()), 1)
        self._has_correct_plural_format(translations)
        t = translations.values()[0]
        self.assertIsInstance(t, dict)
        self.assertEquals(len(t), 1)
        self.assertIn(5, t)

    def test_marked_source_strings_builder(self):
        """Test that source strings are marked by the
        MarkedSourceTranslationsBuilder.
        """
        builder = MarkedSourceTranslationsBuilder(
            self.resource, self.language_ar
        )
        translations = builder()
        self.assertEquals(len(translations), 1)
        self.translation_ar.delete()
        translations = builder()
        self.assertEquals(len(translations), 1)
        self._has_correct_normal_format(translations)
        t_string = translations.values()[0]
        self.assertTrue(t_string.endswith('txss'))

    def test_marked_source_builder_pluralized(self):
        """Test that the SourceTranslationsBuilder uses source strings
        instead of empty translations in the pluralized case.
        """
        builder = MarkedSourceTranslationsBuilder(
            self.resource, self.language_ar
        )
        builder.pluralized = True
        translations = builder()
        self.assertEquals(len(translations), 1)
        self.translation_ar.delete()
        translations = builder()
        self.assertEquals(len(translations), 1)
        self._has_correct_plural_format(translations)
        t_string = translations.values()[0][5]
        self.assertTrue(t_string.endswith('txss'))

    def test_reviewed_marked_builder(self):
        """Test the ReviewedMarkedTranslationsBuilder builder returns only
        reviewed strings.
        """
        builder = ReviewedMarkedSourceTranslationsBuilder(
            self.resource, self.language_ar
        )
        translations = builder()
        self.assertEquals(len(translations), 1)
        t_string = translations.values()[0]
        self.assertTrue(t_string.endswith('txss'))
        self.translation_ar.reviewed = True
        self.translation_ar.save()
        translations = builder()
        self._has_correct_normal_format(translations)
        self.assertEquals(len(translations), 1)
        self.assertEquals(
            translations.keys()[0], self.translation_ar.source_entity_id
        )
        t_string = translations.values()[0]
        self.assertFalse(t_string.endswith('txss'))

    def test_reviewed_marked_builder_pluralized(self):
        """Test the ReviewedTranslationsBuilder builder, when pluralized."""
        builder = ReviewedMarkedSourceTranslationsBuilder(
            self.resource, self.language_ar
        )
        builder.pluralized = True
        translations = builder()
        self.assertEquals(len(translations), 1)
        t_string = translations.values()[0][5]
        self.assertTrue(t_string.endswith('txss'))
        self.translation_ar.reviewed = True
        self.translation_ar.save()
        translations = builder()
        self.assertEquals(len(translations), 1)
        self.assertEquals(
            translations.keys()[0], self.translation_ar.source_entity_id
        )
        self.assertEquals(len(translations.values()), 1)
        self._has_correct_plural_format(translations)
        t = translations.values()[0]
        self.assertIsInstance(t, dict)
        self.assertEquals(len(t), 1)
        self.assertIn(5, t)
        t_string = translations.values()[0][5]
        self.assertFalse(t_string.endswith('txss'))

    def _has_correct_normal_format(self, t):
        """Test t has the correct normal format."""
        self.assertIsInstance(t, dict)
        for rule in t.keys():
            self.assertIsInstance(rule, int)

    def _has_correct_plural_format(self, t):
        """Test t has the correct plural format."""
        self.assertIsInstance(t, dict)
        for rule in t.values():
            self.assertIsInstance(rule, dict)
            self.assertIsInstance(rule.keys()[0], int)
