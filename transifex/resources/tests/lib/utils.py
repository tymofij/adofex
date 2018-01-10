# -*- coding: utf-8 -*-

"""
Tests for the utils module.
"""

from django.utils import unittest
from transifex.resources.formats.utils.string_utils import split_by_newline


class TestSplitNewlines(unittest.TestCase):
    """Test the split_by_newlines function."""

    def test_empty_text(self):
        """Test with empty text."""
        it = split_by_newline('')
        _, s = it.next()
        self.assertEqual(s, '')
        self.assertRaises(StopIteration, it.next)

    def test_ends_newline(self):
        """Test the behavior in case the text ends with a new line character."""
        text = 'A line\nAnother line\nAnd a final one.\n'
        expected_res = text.split('\n')
        for res, expected in zip(split_by_newline(text), expected_res):
            self.assertEqual(res[1], expected)

    def test_ends_character(self):
        """Test the behavior in case the text does not end
        with a new line character.
        """
        text = 'A line\nAnother line\nAnd a final one.'
        expected_res = text.split('\n')
        for res, expected in zip(split_by_newline(text), expected_res):
            self.assertEqual(res[1], expected)

    def test_index(self):
        """Test the index part of the function."""
        text = 'a\nb\nc'
        expected_pos = [2, 4, -1]
        for res, expected in zip(split_by_newline(text), expected_pos):
            self.assertEqual(res[0], expected)

        text = 'a\nb\nc\n'
        expected_pos = [2, 4, 6, -1]
        for res, expected in zip(split_by_newline(text), expected_pos):
            self.assertEqual(res[0], expected)
