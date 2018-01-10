# -*- coding: utf-8 -*-

# from django.utils import unittest FIXME
import unittest
from transifex.resources.models import SourceEntity, Translation
from transifex.resources.formats.core import SourceEntityCollection, \
        TranslationCollection, GenericTranslation, StringSet


class TestResourceCollections(unittest.TestCase):

    def setUp(self):
        self.se1 = SourceEntity(string="A string", context="None")
        self.se2 = SourceEntity(string="A second string", context="None")
        self.se3 = SourceEntity(string="A third string")

    def test_source_entities(self):
        col = SourceEntityCollection()
        self.assertFalse(self.se1 in col)
        col.add(self.se1)
        self.assertTrue(self.se1 in col)
        self.assertFalse(self.se2 in col)
        col.add(self.se2)
        self.assertTrue(self.se2 in col)
        self.assertEquals(len(col._items), 2)
        self.assertFalse(self.se3 in col)
        col.add(self.se3)
        self.assertTrue(self.se3 in col)
        self.assertEquals(col.get(self.se1), self.se1)
        self.assertEquals(col.get(self.se2), self.se2)
        self.assertEquals(col.get(self.se3), self.se3)
        se = col.get(self.se3)
        self.assertEquals(se.string, self.se3.string)

        gt1 = GenericTranslation(
            source_entity=self.se1.string, context=self.se1.context,
            translation="Blah"
        )
        col.add(gt1)
        self.assertEquals(len(col._items), 3)
        gt2 = GenericTranslation(
            source_entity=self.se2.string + "1", context=self.se2.context,
            translation="Blah"
        )
        col.add(gt2)
        self.assertEquals(len(col._items), 4)
        gt3 = GenericTranslation(
            source_entity=self.se3.string, context="a",
            translation="Blah"
        )
        col.add(gt3)
        self.assertEquals(len(col._items), 5)

    def test_translations(self):
        t1 = Translation(string="A translation", source_entity=self.se1, rule=1)
        t1.source_entity_id = 1
        t2 = Translation(
            string="Two translations", source_entity=self.se1, rule=5
        )
        t2.source_entity_id = 1
        t3 = Translation(string="A translation", source_entity=self.se2, rule=5)
        t3.source_entity_id = 2
        col = TranslationCollection()
        self.assertFalse(t1 in col)
        col.add(t1)
        self.assertTrue(t1 in col)
        self.assertFalse(t2 in col)
        col.add(t2)
        self.assertTrue(t2 in col)
        self.assertFalse(t3 in col)
        col.add(t3)
        self.assertTrue(t3 in col)
        self.assertTrue(len(col._items), 3)


class TestStringSet(unittest.TestCase):
    """Test stringset class."""

    def setUp(self):
        self.stringset = StringSet()

    def test_correct_addition(self):
        """Test that entries are correctly added to a StringSet."""
        t1 = GenericTranslation('se1', 'trans1', context='')
        t2 = GenericTranslation('se2', 'trans2', context='')
        t3 = GenericTranslation('se2', 'trans1', context='c3')
        translations = [t1, t2, t3, ]
        for idx, t in enumerate(translations, start=1):
            self.stringset.add(t)
            self.assertEquals(len(self.stringset), idx)
            for old_t in translations[:idx]:
                self.assertIn(old_t, self.stringset)

    def test_adding_duplicates(self):
        """Test that adding a duplicate element only keeps one."""
        t1 = GenericTranslation('se', 'trans1', context='')
        self.stringset.add(t1)
        self.assertEquals(len(self.stringset), 1)
        self.assertIn(t1, self.stringset)
        t2 = GenericTranslation('se', 'trans2', context='')
        self.stringset.add(t2)
        self.assertEquals(len(self.stringset), 1)
        self.assertIn(t2, self.stringset)
        for t in self.stringset:
            self.assertEqual(t1.translation, t.translation)

