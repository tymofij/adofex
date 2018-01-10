# -*- coding: utf-8 -*-

from django.test import TestCase
from transifex.resources.formats.resource_collections import StringSet
from transifex.resources.formats.wiki import WikiHandler


class TestWikiHandler(TestCase):

    def test_parse_wiki_text(self):
        handler = WikiHandler()
        handler.stringset = StringSet()
        # Test content with '\n' as line separator
        content = "Text {{italics|is}}\n\nnew {{italics|par\n\npar}}.\n\nTers"
        handler.content = content
        handler._parse(None, None)
        self.assertEquals(len(handler.stringset), 3)
        # Test content with '\r\n' as line separator
        handler.stringset = StringSet()
        content = "Text {{italics|is}}\r\n\r\nnew "\
                "{{italics|par\r\n\r\npar}}.\r\n\r\nTers"
        handler.content = content
        handler._parse(None, None)
        self.assertEquals(len(handler.stringset), 3)

        # Test content with '\n' as line separator
        handler.stringset = StringSet()
        content = "Text {{italics|is}}\n\n\n\nnew {{italics|par\n\npar}}.\n\nTers"
        handler.content = content
        handler._parse(None, None)
        self.assertEquals(len(handler.stringset), 3)
        # Test content with '\r\n' as line separator
        handler.stringset = StringSet()
        content = "Text {{italics|is}}\r\n\r\n\r\n\r\nnew "\
                "{{italics|par\r\n\r\npar}}.\r\n\r\nTers"
        handler.content = content
        handler._parse(None, None)
        self.assertEquals(len(handler.stringset), 3)

        # Test content with '\n' as line separator
        handler.stringset = StringSet()
        content = ("text {{italics|is}} {{bold|bold}}\n\n\n\nnew "
                   "{{italics|par\n\npar}}.\n\nters")
        handler.content = content
        handler._parse(None, None)
        self.assertEquals(len(handler.stringset), 3)
        # Test content with '\r\n' as line separator
        handler.stringset = StringSet()
        content = ("text {{italics|is}} {{bold|bold}}\r\n\r\n\r\n\r\nnew "
                   "{{italics|par\r\n\r\npar}}.\r\n\r\nters")
        handler.content = content
        handler._parse(None, None)
        self.assertEquals(len(handler.stringset), 3)
