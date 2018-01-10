# -*- coding: utf-8 -*-

import os
from transifex.txcommon.tests.base import Languages
from transifex.languages.models import Language
from transifex.resources.formats.desktop import DesktopHandler
from transifex.resources.tests.lib.base import FormatsBaseTestCase


class TestDesktopHandler(FormatsBaseTestCase):
    """Tests for .desktop files."""

    def setUp(self):
        super(TestDesktopHandler, self).setUp()
        self.handler = DesktopHandler()

    def test_comment_line(self):
        line = "#Name=Name"
        self.assertTrue(self.handler._is_comment_line(line))
        line = "Name=Name"
        self.assertFalse(self.handler._is_comment_line(line))

    def test_empty_line(self):
        for line in ["", " ", "  ", "\t", ]:
            self.assertTrue(self.handler._is_empty_line(line))
        line = "  a  \n"
        self.assertFalse(self.handler._is_empty_line(line))

    def test_group_header_line(self):
        line = "[Group]"
        self.assertTrue(self.handler._is_group_header_line(line))
        line = "Name[en_GB]=Name"
        self.assertFalse(self.handler._is_group_header_line(line))

    def test_get_elements(self):
        line = "Name=Name = Name"
        elems = self.handler._get_elements(line)
        self.assertEqual(elems[0], "Name")
        self.assertEqual(elems[1], "Name = Name")
        line = "Name"
        elems = self.handler._get_elements(line)
        self.assertEqual(elems[0], "Name")
        self.assertEqual(len(elems), 1)

    def test_locale_support(self):
        langs = {
            "Name[en]": 'en',
            "Name[en_US]": 'en_US',
            "Name[en_US.UTF-8]": 'en_US',
            "Name[ca@valencia]": 'ca@valencia',
            "Name[ca.UTF-8@valencia]": 'ca@valencia',
        }
        for key, lang in langs.iteritems():
            locale = self.handler._get_locale(key)
            lang_code = self.handler._get_lang_code(locale)
            self.assertEqual(
                Language.objects.by_code_or_alias(lang_code).code,
                lang
            )

    def test_parse_file(self):
        lang = Language.objects.by_code_or_alias('en_US')
        self.handler.set_language(lang)
        filename = os.path.join(
            os.path.dirname(__file__),
            'data/okular.desktop'
        )
        self.handler.bind_file(filename)
        self.handler.parse_file(is_source=True)
        self.assertEquals(len(self.handler.stringset), 2)

