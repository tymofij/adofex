# -*- coding: utf-8 -*-

from mock import Mock
from django.utils import unittest
from django.conf import settings
from transifex.resources.formats.registry import registry, _FormatsRegistry
from transifex.resources.formats.pofile import POHandler, POTHandler
from transifex.txcommon.tests.base import BaseTestCase


class TestRegistry(BaseTestCase):

    def setUp(self):
        super(TestRegistry, self).setUp()
        methods = {
            'PO': {
                'description': 'PO file handler',
                'file-extensions': '.po, .pot',
                'mimetype': 'text/x-po, application/x-gettext, application/x-po',
            }, 'QT': {
                    'description': 'Qt Files',
                    'mimetype': 'application/xml',
                    'file-extensions': '.ts'
            },
        }
        handlers = {
            'PO': 'resources.formats.pofile.POHandler',
            'QT': 'resources.formats.qt.LinguistHandler',
        }
        self.registry = _FormatsRegistry(methods=methods, handlers=handlers)

    def test_register(self):
        from transifex.resources.formats.joomla import JoomlaINIHandler
        self.registry.add_handler('INI', JoomlaINIHandler)
        self.assertEquals(len(self.registry.handlers.keys()), 3)
        self.assertIn('INI', self.registry.handlers.keys())
        j = self.registry.handler_for('INI')
        self.assertIsInstance(j, JoomlaINIHandler)

    def test_extensions(self):
        extensions = self.registry.extensions_for('PO')
        self.assertEquals(len(extensions), 2)
        self.assertEquals(extensions[0], '.po')
        self.assertEquals(extensions[1], '.pot')

    def test_mimetypes(self):
        mimetypes = self.registry.mimetypes_for('PO')
        self.assertEquals(len(mimetypes), 3)
        self.assertEquals(mimetypes[0], 'text/x-po')
        self.assertEquals(mimetypes[1], 'application/x-gettext')
        self.assertEquals(mimetypes[2], 'application/x-po')


class TestAppropriateHandler(unittest.TestCase):
    """Test the process of finding the appropriate handler in
    various situations.
    """

    @classmethod
    def setUpClass(cls):
        cls.appropriate_handler = registry.appropriate_handler

    def test_normal_types(self):
        for method in settings.I18N_METHODS:
            if method not in ('PO', 'POT', ):
                resource = Mock()
                resource.__dict__['i18n_type'] = method
                handler = self.appropriate_handler(resource, None)
                self.assertIsInstance(
                    handler, type(registry.handler_for(method))
                )

    def test_get(self):
        resource = Mock()
        resource.__dict__['i18n_type'] = 'PO'
        resource.source_language = 'en'

        handler = self.appropriate_handler(resource, None)
        self.assertIsInstance(handler, POTHandler)
        handler = self.appropriate_handler(resource, 'en')
        self.assertIsInstance(handler, POHandler)
        handler = self.appropriate_handler(resource, 'el')
        self.assertIsInstance(handler, POHandler)

    def test_save(self):
        resource = Mock()
        resource.__dict__['i18n_type'] = 'PO'
        resource.source_language = 'en'

        filename = 'f.po'
        handler = self.appropriate_handler(resource, None, filename=filename)
        self.assertIsInstance(handler, POHandler)
        handler = self.appropriate_handler(resource, 'en', filename=filename)
        self.assertIsInstance(handler, POHandler)
        handler = self.appropriate_handler(resource, 'el', filename=filename)
        self.assertIsInstance(handler, POHandler)
        filename = 'f.pot'
        handler = self.appropriate_handler(resource, None, filename=filename)
        self.assertIsInstance(handler, POTHandler)
        handler = self.appropriate_handler(resource, 'en', filename=filename)
        self.assertIsInstance(handler, POTHandler)
        handler = self.appropriate_handler(resource, 'el', filename=filename)
        self.assertIsInstance(handler, POTHandler)


class TestFileExtensions(unittest.TestCase):
    """Test the file extensions used."""

    def setUp(self):
        self.resource = Mock()
        self.resource.source_language = 'en'

    def test_extensions(self):
        for method in registry.available_methods:
            if method == 'POT':
                continue
            self.resource.i18n_method = method
            correct_extensions = registry.extensions_for(method)
            for lang in ('en', 'el'):
                extension_returned = registry.file_extension_for(
                    self.resource, lang
                )
                self.assertIn(extension_returned, correct_extensions)

    def test_po_extensions(self):
        """Test PO/POT extensions.

        If language is None: extension == 'pot'.
        """
        self.resource.i18n_method = 'PO'
        for lang in ('en', 'el', None):
            extension = registry.file_extension_for(self.resource, lang)
            if lang is None:
                self.assertEqual(extension, registry.extensions_for('POT')[0])
            else:
                self.assertEqual(extension, registry.extensions_for('PO')[0])

