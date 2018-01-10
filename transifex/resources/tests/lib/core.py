# -*- coding: utf-8 -*-

from mock import patch, Mock
from django.test import TestCase, TransactionTestCase
from django.utils import unittest
from django.conf import settings
from transifex.txcommon.tests.base import TransactionUsers,\
        TransactionLanguages
from transifex.projects.models import Project
from transifex.resources.models import Resource, SourceEntity
from transifex.languages.models import Language
from transifex.resources.formats.joomla import JoomlaINIHandler
from transifex.resources.formats.core import Handler
from transifex.resources.formats.compilation import mode


class TestCoreFunctions(TransactionUsers, TransactionLanguages,
        TransactionTestCase):

    def test_delete_old(self):
        """Test that old source entities get deleted, even when the iterations
        block doesn't get executed.
        """
        old_max_iters = settings.MAX_STRING_ITERATIONS
        settings.MAX_STRING_ITERATIONS = 1
        content = ';1.6\nKEY1="value1"\nKEY2="value2"\nKEY3="value3"\n'
        parser = JoomlaINIHandler()
        parser.bind_content(content)
        # FIXME get project/resource from parents
        p = Project.objects.create(slug="pr", name="Pr", source_language=self.language_en)
        l = self.language_en
        r = Resource.objects.create(
            slug="core", name="Core", project=p, source_language=l
        )
        parser.bind_resource(r)
        parser.set_language(l)
        parser.parse_file(is_source=True)
        parser.save2db(is_source=True)
        self.assertEquals(SourceEntity.objects.filter(resource=r).count(), 3)
        content = ';1.6\nKEY1="value1"\nKEY4="value4"\n'
        parser.bind_content(content)
        parser.parse_file(is_source=True)
        parser.save2db(is_source=True)
        self.assertEquals(SourceEntity.objects.filter(resource=r).count(), 2)
        settings.MAX_STRING_ITERATIONS = old_max_iters


class TestMode(TestCase):
    """Test the mode variable used in compilation."""

    @unittest.skip('Do it later')
    @patch.object(Handler, '_compile_viewing')
    @patch.object(Handler, '_compile_translating')
    @patch.object(Handler, '_content_from_template')
    def test_mode(self, tempalte_mock, tmock, vmock):
        """Test that the correct function is called for compilation."""
        h = Handler()
        h.resource = Mock()
        h.compile(mode=mode.DEFAULT)
        self.assertTrue(vmock.called)
        self.assertFalse(tmock.called)
        vmock.reset_mock()
        h.compile(mode=mode.TRANSLATE)
        self.assertFalse(vmock.called)
        self.assertTrue(tmock.called)
        vmock.reset_mock()
        h.compile(mode=mode.REVIEWED)
        self.assertFalse(vmock.called)
        self.assertTrue(tmock.called)
