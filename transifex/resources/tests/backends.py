# -*- coding: utf-8 -*-

from __future__ import with_statement
import os
from mock import patch, Mock
from django.conf import settings
from django.test import TransactionTestCase
from transifex.projects.models import Project
from transifex.txcommon.tests.base import TransactionLanguages, \
        TransactionUsers, TransactionNoticeTypes
from transifex.languages.models import Language
from transifex.resources.models import Resource, SourceEntity, Translation
from transifex.resources.backends import *


class TestBackend(TransactionUsers, TransactionLanguages,
        TransactionNoticeTypes, TransactionTestCase):

    def setUp(self):
        super(TestBackend, self).setUp()
        file_ = os.path.join(
            settings.TX_ROOT, "resources/tests/lib/pofile/pt_BR.po"
        )
        f = open(file_, 'r')
        try:
            self.content = f.read()
        finally:
            f.close()
        self.source_lang = self.language_en
        self.target_lang = self.language
        self.maintainer = self.user['maintainer']
        self.project = Project.objects.create(slug='testp', name='Test Project',
                source_language=self.source_lang)
        self.resource = Resource.objects.create(
            slug='test', name='Test', source_language=self.source_lang,
            project=self.project, i18n_type='PO'
        )
        self.method = 'PO'


class TestResourceBackend(TestBackend):

    def test_create(self):
        rb = ResourceBackend()
        res = rb.create(
            self.project, slug='test1', name='Test', method=self.method,
            source_language=self.source_lang, content=self.content,
            user=self.maintainer, extra_data={'accept_translations': True}
        )
        self.assertEquals(res[0], 6)
        self.assertEquals(res[1], 0)


class TestFormatsBackend(TestBackend):

    def test_import(self):
        fb = FormatsBackend(self.resource, self.source_lang, self.maintainer)
        res = fb.import_source(self.content, self.method)
        ses = SourceEntity.objects.filter(resource=self.resource)
        trs = Translation.objects.filter(source_entity__in=ses)
        self.assertEquals(res[0], 6)
        self.assertEquals(res[1], 0)
        self.assertEquals(len(ses), 6)
        self.assertEquals(len(trs), 7)

    def test_handlers_used_for_source_import(self):
        """Test the handlers used for various combinations of resources and
        languages, when pushing the source file.
        """
        resource = Mock()
        resource.source_language = 'en'

        with patch.object(FormatsBackend, '_import_content') as mock:
            ## No filenames
            for method in registry.available_methods:
                if method == 'PO':
                    continue
                resource.i18n_type = method
                lang = 'en'
                fb = FormatsBackend(resource, lang, None)
                fb.import_source('')
                used_handler = mock.call_args[0][0]
                self.assertIsInstance(
                    used_handler, type(registry.handler_for(method))
                )

                lang = None
                fb = FormatsBackend(resource, lang, None)
                self.assertRaises(FormatsBackendError, fb.import_source, '')

            method = 'PO'
            resource.i18n_type = method
            lang = 'en'         # source language
            fb = FormatsBackend(resource, lang, None)
            fb.import_source('')
            used_handler = mock.call_args[0][0]
            self.assertIsInstance(
                used_handler, type(registry.handler_for(method))
            )
            lang = None         # lang is None
            fb = FormatsBackend(resource, lang, None)
            self.assertRaises(FormatsBackendError, fb.import_source, '')

            ## With filenames
            filename = 'does-not-matter'
            for method in registry.available_methods:
                if method == 'PO':
                    continue
                resource.i18n_type = method
                lang = 'en'
                fb = FormatsBackend(resource, lang, None)
                fb.import_source('', filename=filename)
                used_handler = mock.call_args[0][0]
                self.assertIsInstance(
                    used_handler, type(registry.handler_for(method))
                )

                lang = None
                fb = FormatsBackend(resource, lang, None)
                self.assertRaises(FormatsBackendError, fb.import_source, '')

            # .po filename
            filename = 'file.po'
            method = 'PO'
            resource.i18n_type = method
            lang = 'en'         # source language
            fb = FormatsBackend(resource, lang, None)
            fb.import_source('', filename=filename)
            used_handler = mock.call_args[0][0]
            self.assertIsInstance(
                used_handler, type(registry.handler_for(method))
            )
            lang = None         # lang is None
            fb = FormatsBackend(resource, lang, None)
            self.assertRaises(FormatsBackendError, fb.import_source, '')

            # .pot filename
            filename = 'file.pot'
            method = 'PO'
            resource.i18n_type = method
            lang = 'en'         # source language
            fb = FormatsBackend(resource, lang, None)
            fb.import_source('', filename=filename)
            used_handler = mock.call_args[0][0]
            self.assertIsInstance(
                used_handler, type(registry.handler_for('POT'))
            )
            lang = None         # lang is None
            fb = FormatsBackend(resource, lang, None)
            self.assertRaises(FormatsBackendError, fb.import_source, '')

    def test_handlers_used_for_translations(self):
        """Test the handlers used for various combinations of resources and
        languages, when pushing a translation.
        """
        resource = Mock()
        resource.source_language = 'en'

        with patch.object(FormatsBackend, '_import_content') as mock:
            ## No filenames
            for method in registry.available_methods:
                resource.i18n_type = method
                lang = 'en'
                fb = FormatsBackend(resource, lang, None)
                fb.import_translation('')
                used_handler = mock.call_args[0][0]
                self.assertIsInstance(
                    used_handler, type(registry.handler_for(method))
                )

                lang = None
                fb = FormatsBackend(resource, lang, None)
                self.assertRaises(FormatsBackendError, fb.import_source, '')

