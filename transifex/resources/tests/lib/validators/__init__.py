# -*- coding: utf-8 -*-

from __future__ import with_statement
from django.test import TestCase
from transifex.languages.models import Language
from transifex.resources.formats.validators import *


class TestValidators(TestCase):

    def test_empty_translation(self):
        old = 'old'
        new = ''
        v = BaseValidator()
        v(old, new)

    def test_spaces(self):
        v = SpaceValidator()
        old = "as"
        new = "  "
        self.assertRaises(ValidationError, v, old, new)
        new = "  \t"
        self.assertRaises(ValidationError, v, old, new)

    def test_brackets(self):
        v = MatchingBracketsValidator()
        for c in MatchingBracketsValidator.bracket_chars:
            old = c + "string"
            new = c + "trans"
            v(old, new)
            new = "trans" + c
            v(old, new)
            new = "tr" + c + "ans"
            v(old, new)
            new = "trans"
            self.assertRaises(ValidationError, v, old, new)
        for c1 in MatchingBracketsValidator.bracket_chars:
            for c2 in MatchingBracketsValidator.bracket_chars:
                old = 'a' + c1 + 'b' + c2 + 'c'
                new = c1 + 'abc' + c2
                v(old, new)
                new = c2 + 'abc' + c1
                v
                new = c1 + 'abc'
                self.assertRaises(ValidationError, v, old, new)
                new = c2 + 'abc'
                self.assertRaises(ValidationError, v, old, new)

    def test_urls(self):
        v = UrlsValidator()
        old = "blah http://www.transifex.net blah"
        new = "blah http://www.transifex.net blah"
        v(old, new)
        new = "blah www.transifex.net blah"
        self.assertRaises(ValidationError, v, old, new)
        # Check typos
        new = "blah http://www.trasnifex.net blah"
        self.assertRaises(ValidationError, v, old, new)
        new = "blah-blah"
        self.assertRaises(ValidationError, v, old, new)

        old = "blah http://www.transifex.net blah https://indifex.com"
        new = "blah http://www.transifex.net blah https://indifex.com"
        v(old, new)
        new = "blah https://indifex.com"
        self.assertRaises(ValidationError, v, old, new)

    def test_emails(self):
        v = EmailAddressesValidator()
        old = "blah me@indifex.com"
        new = "blah me@indifex.com blah"
        v(old, new)
        new = "blah you@indifex.com blah"
        self.assertRaises(ValidationError, v, old, new)
        old = "blah me@indifex.com and me@gmail.com blah"
        new = "blah me@indifex.com and me@gmail.com blah"
        v(old, new)
        new = "blah you@indifex.com blah"
        self.assertRaises(ValidationError, v, old, new)

    def test_start_newlines(self):
        v = NewLineAtBeginningValidator()
        old = "asdaf"
        new = "asdasa"
        v(old, new)
        old = "\n asdasa"
        self.assertRaises(ValidationError, v, old, new)
        new = "\nasdasdsaafsaf"
        v(old, new)
        old = "asadaaf"
        self.assertRaises(ValidationError, v, old, new)

    def test_start_newlines(self):
        v = NewLineAtEndValidator()
        old = "asdaf"
        new = "asdasa"
        v(old, new)
        old = "asdasa\n"
        self.assertRaises(ValidationError, v, old, new)
        new = "asdasdsaafsaf\n"
        v(old, new)
        old = "asadaaf"
        self.assertRaises(ValidationError, v, old, new)

    def test_numbers(self):
        v = NumbersValidator()
        old = "asa0asda1as+2afd-3asdas0.12asda"
        new = "asa0asda1as+2afd-3asdas0.12asda"
        v(old, new)
        new = "asa0asda1as+2afd-3asdas0,12asda"
        v(old, new)
        new = "asa0asda1as+2afd-3asdas012asda"
        self.assertRaises(ValidationError, v, old, new)
        new = "asaasda1as+2afd-3asdas012asda"
        self.assertRaises(ValidationError, v, old, new)
        new = "asa0asda1as-2afd-3asdas0.12asda"
        self.assertRaises(ValidationError, v, old, new)
        old = "as as das dsa "
        new = "agre dsg fs sa d"
        v(old, new)

    def test_printf_formats(self):

        class Language(object):
            pass

        sl = Language()
        sl.nplurals = 2
        tl = Language()
        tl.nplurals = 2
        v = PrintfFormatNumberValidator(sl, tl)
        old = "%s %d"
        new = "%s %d"
        v(old, new)
        new = "%f"
        self.assertRaises(ValidationError, v, old, new)
        tl.nplurals = 3
        new = "%f %s %x"
        v(old, new)

    def test_source_printf_format(self):
        v = PrintfFormatSourceValidator()
        old = "%s %d asda"
        new = "%d %s asagsfdsf %f"
        v(old, new)
        new = "%d"
        self.assertRaises(ValidationError, v, old, new)
        new = "%s"
        self.assertRaises(ValidationError, v, old, new)
        old = "%s %d"
        new = "%2$d %1$s"
        v(old, new)

        old = "%(foo)s %(bar)s"
        new = "%(fo0)s %(bar)s"
        with self.assertRaises(ValidationError) as cm:
            v(old, new)
        self.assertIn('foo', unicode(cm.exception))
        new = "%(foo)s"
        with self.assertRaises(ValidationError) as cm:
            v(old, new)
        self.assertIn('bar', unicode(cm.exception))
        new = "%(bar)s"
        with self.assertRaises(ValidationError) as cm:
            v(old, new)
        self.assertIn('foo', unicode(cm.exception))
        new = "%(bar)s %(foo)s"
        v(old, new)

    def test_translation_printf_format(self):
        v = PrintfFormatTranslationValidator()
        old = "%s %d asda %f"
        new = "%d %s asagsfdsf %f"
        v(old, new)
        old = "%d %s"
        self.assertRaises(ValidationError, v, old, new)
        old = "%s %d asda %k"
        self.assertRaises(ValidationError, v, old, new)

        old = "%s %d"
        new = "%2$d %1$s"
        v(old, new)

        old = "%(foo)s %(bar)s"
        new = "%(fo0)s %(bar)s"
        with self.assertRaises(ValidationError) as cm:
            v(old, new)
        self.assertIn('fo0', unicode(cm.exception))
        new = "%(baz)s"
        with self.assertRaises(ValidationError) as cm:
            v(old, new)
        self.assertIn('baz', unicode(cm.exception))
        new = "%(bar)s %(foo)s"
        v(old, new)

    def test_singular_printf_number(self):

        class Language(object):
            pass

        sl = Language()
        sl.nplurals = 2
        tl = Language()
        tl.nplurals = 2
        v = PrintfFormatPluralizedNumberValidator(sl, tl, rule=5)
        old = "%s apples"
        new = "apples"
        self.assertRaises(ValidationError, v, old, new)
        v.rule = 1
        new = "apple"
        v(old, new)
        v.rule = 5
        tl.nplurals = 5
        v(old, new)

    def test_singular_printf_source(self):
        v = PrintfFormatPluralizedSourceValidator(rule=5)
        old = "%s apples"
        new = "apples"
        self.assertRaises(ValidationError, v, old, new)
        v.rule = 1
        new = "apple"
        v(old, new)
