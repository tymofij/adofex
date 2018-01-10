# -*- coding: utf-8 -*-

from django.utils import unittest
from transifex.resources.formats.compilation import *


class TestFactories(unittest.TestCase):
    """Test the compiler factories."""

    def test_review_mode(self):
        """Test that if the REVIEWED mode has been enabled, the factories
        always return a reviewed-related factory.
        """
        Factories = [
            SimpleCompilerFactory, FillEmptyCompilerFactory,
            AlwaysFillEmptyCompilerFactory
        ]
        for Factory in Factories:
            factory = Factory()
            factory.resource = None
            tsetter = factory._get_translation_setter(None, Mode.REVIEWED)
            name = tsetter.__class__.__name__
            self.assertIn('Reviewed', name)
