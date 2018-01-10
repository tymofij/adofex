# -*- coding: utf-8 -*-
from __future__ import with_statement
from mock import patch
import os
import logging
from django.conf import settings
from django.utils.hashcompat import md5_constructor
from transifex.txcommon.tests import base
from transifex.resources.formats.compilation import \
        NormalDecoratorBuilder as Decorator
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.models import SourceEntity, Translation
from transifex.resources.formats.compilation import Mode


class FormatsBaseTestCase(base.BaseTestCase):
    """Base class for tests on supported formats."""

    def setUp(self):
        super(FormatsBaseTestCase, self).setUp()

    def compare_to_actual_file(self, handler, actual_file):
        template = handler.template
        compiler = handler.CompilerClass(handler.resource)
        compiler._tdecorator = Decorator(escape_func=handler._escape)
        compiler._examine_content(handler.template)
        compiler.language = handler.language
        sources = [
            (idx, "%s" % hash_tag(s.source_entity, ""))
            for idx, s in enumerate(handler.stringset)
        ]
        translations = dict([
            (idx, s.translation)
            for idx, s in enumerate(handler.stringset)
        ])
        with patch.object(compiler, '_get_source_strings') as smock:
            with patch.object(compiler, '_tset', create=True) as tmock:
                smock.return_value = sources
                tmock.return_value = translations
                compiler._compile(handler.template)
                template = compiler.compiled_template
        with open(actual_file, 'r') as f:
            actual_content = f.read()
        self.assertEquals(template, actual_content)

    def get_translation(self, t, compiler):
        if not t:
            return ""
        return t

    def get_content_from_file(self, filename, encoding=False):
        """Get content from a file as required by handler's
        bind_content() method"""
        f = open(filename, 'r')
        content = f.read()
        f.close()
        if encoding:
            content = content.decode(encoding)
        return content

    def _save_source(self, handler, resource, source_file,
            source_entity_count, source_translation_count):
        """Save source translations
            handler: Handler instance for i18n_type
            resource: a Resource instance
            source_file: path to source file
            source_entity_count: expected count for source entities saved
            source_translation_count: expected count for translations in
                    resource.source_language
            Returns a handler
        """
        l = resource.source_language
        handler.set_language(l)
        handler.bind_resource(resource)
        handler.bind_content(self.get_content_from_file(source_file))
        handler.parse_file(is_source=True)
        handler.save2db(is_source=True)

        self.assertEqual(SourceEntity.objects.filter(resource=resource
            ).count(), source_entity_count)
        self.assertEqual(len(Translation.objects.filter(
            source_entity__resource=resource, language=l)),
            source_translation_count)
        return handler

    def _save_translation(self, handler, resource, target_lang,
            translation_file, translation_count):
        """
        Save translations from a translation file for a resource
        handler: Handler instance for i18n_type
        resource: a Resource instance
        target_lang: target language instance
        translation_file: path to translation file
        translation_count: expected count for translations saved in
            target_lang for resource

        Returns a handler
        """
        handler.bind_resource(resource)
        handler.bind_content(self.get_content_from_file(translation_file))
        handler.set_language(target_lang)
        handler.parse_file()
        handler.save2db()
        self.assertEqual(len(Translation.objects.filter(
            source_entity__resource=resource,
            language=target_lang)), translation_count)
        return handler

    def _mark_translation_as_reviewed(self, resource, source_strings, language,
            expected_reviewed_count):
        """
        Mark translation strings as reviewed
        resource: A Resource instance
        source_strings: A list containing source strings
        language: Language for translations to be reveiewed
        expected_reviewed_count: Expected number of translations marked as
            reviewed
        """
        Translation.objects.filter(source_entity__in=resource.source_entities.filter(
            string__in=source_strings), language=language).update(reviewed=True)
        self.assertEqual(Translation.objects.filter(
            source_entity__resource=resource, reviewed=True
            ).count(), expected_reviewed_count)

    def _check_compilation(self, handler, resource, language, compiled_file,
            mode=Mode.DEFAULT):
        """
        Verify compilation with a compiled_file's content
        handler: A Handler instance
        resource: A Resource instance
        language: Language in which the resource will be compiled
        compiled_file: path to a compiled file
        mode: Compilation Mode instance
        """
        if isinstance(mode, str):
            if mode == 'REVIEWED':
                mode = Mode.REVIEWED
            elif mode == 'TRANSLATED':
                mode = Mode.TRANSLATED
            else:
                mode = Mode.DEFAULT

        handler.bind_resource(resource)
        handler.set_language(language)
        compiled_template = handler.compile(mode=mode)
        f = open(compiled_file, 'r')
        expected_compiled_template = f.read()
        f.close()
        self.assertEqual(compiled_template, expected_compiled_template)

