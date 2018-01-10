# -*- coding: utf-8 -*-

from django.utils import unittest
from transifex.resources.formats.compilation.compilers import Compiler, \
        PluralCompiler


class TestCompiler(unittest.TestCase):
    """Test the compiler class."""

    def test_apply_translations(self):
        """Test translations are substituted correctly."""
        string_hash = '1' * 32 + '_tr'
        text = string_hash + ' '
        translations = {string_hash: 'yes'}
        compiler = Compiler(resource=None)
        res = compiler._apply_translations(translations, text)
        self.assertEquals(res, 'yes ')


class TestPluralCompiler(unittest.TestCase):
    """Test the compiler class for pluralized formats."""

    def test_apply_translations(self):
        """Test that both plurals and normal translations are
        substituted correctly.
        """
        hash_normal = '1' * 32 + '_tr'
        hash_plural = '2' * 32 + '_pl_0'
        text = '%s %s' % (hash_normal, hash_plural)
        translations = {
            hash_normal: 'normal',
            hash_plural: 'plural',
        }
        compiler = PluralCompiler(resource=None)
        res = compiler._apply_translations(translations, text)
        self.assertEquals(res, 'normal plural')

