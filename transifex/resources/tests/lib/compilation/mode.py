# -*- coding: utf-8 -*-

from django.utils import unittest
from transifex.resources.formats.compilation.mode import Mode


class TestCompilationModes(unittest.TestCase):
    """Test the modes of compilation."""

    def test_combine(self):
        """Test that modes can be combined."""
        m1 = Mode.REVIEWED
        m2 = Mode.TRANSLATED
        m = m1 | m2
        self.assertEquals(m._value, m1._value | m2._value)

    def test_containment(self):
        """Test that the ``in`` operator works for modes."""
        m1 = Mode.REVIEWED
        m2 = Mode.TRANSLATED
        m = m1 | m2
        self.assertIn(Mode.TRANSLATED, m)
        self.assertIn(Mode.REVIEWED, m)

        m1 = Mode.DEFAULT
        m2 = Mode.REVIEWED
        m = m1 | m2
        self.assertIn(Mode.REVIEWED, m)
        self.assertNotIn(Mode.TRANSLATED, m)

        m = Mode.DEFAULT
        self.assertNotIn(Mode.TRANSLATED, m)
        self.assertNotIn(Mode.REVIEWED, m)
