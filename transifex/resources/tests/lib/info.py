# -*- coding: utf-8 -*-

import unittest
from transifex.resources.formats.formats_info import XmlFormatInfo


class TestXmlFormatInfo(unittest.TestCase):

    def setUp(self):
        self.format = XmlFormatInfo()

    def test_escape(self):
        for c in "<", ">", "'", '&', '"':
            s = c.join(['blah', 'blah', 'and blah'])
            s = self.format._escape(s)
            if c != '&':
                self.assertFalse(c in s)
            self.assertTrue(s.count('&'), 2)
            self.assertTrue(s.count(';'), 2)

    def test_unescape(self):
        for c in "&lt;", "&gt;", "&apos;", "&amp;", "&quot;":
            s = c.join(['blah', 'blah', 'and blah'])
            s = self.format._unescape(s)
            self.assertFalse(c in s)
