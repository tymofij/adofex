# -*- coding: utf-8 -*-
"""
Handler for .desktop files.
"""

from __future__ import absolute_import
import re
import codecs
from django.utils.translation import ugettext as _
from collections import defaultdict
from transifex.txcommon.log import logger
from transifex.languages.models import Language
from transifex.resources.models import Translation, Template, SourceEntity
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.formats.core import Handler, ParseError, CompileError
from .compilation import Compiler, SimpleCompilerFactory
from transifex.resources.formats.resource_collections import StringSet, \
        GenericTranslation


class DesktopParseError(ParseError):
    pass


class DesktopCompileError(CompileError):
    pass


class DesktopBaseCompiler(Compiler):
    """Base compiler for .desktop files."""

    def _get_source_strings(self):
        return SourceEntity.objects.filter(resource=self.resource).values_list(
            'id', 'string_hash', 'string'
        )

    def _compile_content(self, content, language):
        stringset = self._get_source_strings()
        self._tset.language = language
        translations = self._tset()
        for string in stringset:
            trans = translations.get(string[0], u"")
            if trans:
                content = self._apply_translation(string[2], trans, content, language)
        return content

    def _apply_translation(self, source, trans, content, language):
        if isinstance(content, str):
            content = content.decode(self.default_encoding)
        if isinstance(source, str):
            source = source.decode(self.default_encoding)
        if isinstance(trans, str):
            trans = trans.decode(self.default_encoding)
        return ''.join([
                content, source, '[', language.code, ']=',
                self._tdecorator(trans), '\n',
        ])


class DesktopSourceCompiler(DesktopBaseCompiler):
    """Compiler for source .desktop files.

    Show all translations.
    """

    def _compile(self, content):
        """Compile all translations."""
        all_languages = set(self.resource.available_languages_without_teams)
        source_language = set([self.resource.source_language, ])
        translated_to = all_languages - source_language
        for language in translated_to:
            content = self._compile_content(content, language)
        self.compiled_template = content


class DesktopTranslationCompiler(DesktopBaseCompiler):
    """Compiler for translation .desktop files.

    Show a single language, the one of the translation.
    """
    def _compile(self, content):
        self.compiled_template = self._compile_content(content, self.language)


class DesktopHandler(SimpleCompilerFactory, Handler):
    """Class for .desktop files.

    See http://standards.freedesktop.org/desktop-entry-spec/latest/.
    """

    name = ".desktop file handler"
    format = ".desktop (*.desktop)"
    method_name = 'DESKTOP'

    HandlerParseError = DesktopParseError
    handlerCompileError = DesktopCompileError

    comment_chars = ('#', )
    delimiter = '='
    # We are only intrested in localestrings, see
    # http://standards.freedesktop.org/desktop-entry-spec/latest/ar01s05.html
    localized_keys = ['Name', 'GenericName', 'Comment', 'Icon', ]

    def _is_comment_line(self, line):
        """Return True, if the line is a comment."""
        return line[0] in self.comment_chars

    def _is_empty_line(self, line):
        """Return True, if the line is empty."""
        return re.match('\s*$', line) is not None

    def _is_group_header_line(self, line):
        """Return True, if this is a group header."""
        return line[0] == '[' and line[-1] == ']'

    def _get_compiler(self, mode=None):
        """Choose between source and single translation compilers."""
        if self.language == self.resource.source_language:
            return DesktopSourceCompiler(self.resource)
        else:
            return DesktopTranslationCompiler(self.resource)

    def _get_elements(self, line):
        """Get the key and the value of a line."""
        return line.split(self.delimiter, 1)

    def _get_lang_code(self, locale):
        """Return the lang_code part from a locale string.

        locale is of the form lang_COUNTRY.ENCODING@MODIFIER
        (in general)
        We care for lang_COUNTRY part.
        """
        modifier = ''
        at_pos = locale.find('@')
        if at_pos != -1:
            modifier = locale[at_pos:]
            locale = locale[:at_pos]
        dot_pos = locale.find('.')
        if dot_pos != -1:
            locale = locale[:dot_pos]
        return ''.join([locale, modifier])

    def _get_locale(self, key):
        """Get the locale part of a key."""
        return key[key.find('[') + 1:-1]

    def _should_skip(self, line):
        """Return True, if we should skip the line.

        This is the case if the line is an empty line, a comment or
        a group header line.

        """
        return self._is_empty_line(line) or\
                self._is_comment_line(line) or\
                self._is_group_header_line(line) or\
                self.delimiter not in line

    def _parse(self, is_source=False, lang_rules=None):
        """
        Parse a .desktop file.

        If it is a source file, the file will have every translation in it.
        Otherwise, it will have just the translation for the specific language.
        """
        # entries is a dictionary with the entry keys in the file
        entries = defaultdict(list)

        template = u''
        for line in self._iter_by_line(self.content):
            if self._should_skip(line) :
                template += line + "\n"
                continue
            key, value = self._get_elements(line)
            if '[' in key:
                # this is a translation
                # find the language of it
                # Skip the template
                actual_key = key[:key.find('[')]
                locale = self._get_locale(key)
                lang_code = self._get_lang_code(locale)
                if lang_code == "x-test":
                    template += line + "\n"
                    continue
                try:
                    lang = Language.objects.by_code_or_alias(lang_code)
                except Language.DoesNotExist, e:
                    msg = _("Unknown language specified: %s" % lang_code)
                    logger.warning(msg)
                    raise DesktopParseError(msg)
            else:
                lang = False    # Use False to mark source string
                actual_key = key
                template += line + "\n"

            if actual_key not in self.localized_keys:
                # Translate only standard localestring keys
                continue
            entries[actual_key].append((value, lang))

        context = ""
        template += '\n# Translations\n'

        for key, value in entries.iteritems():
            for translation, language in value:
                if is_source and language:
                    # Skip other languages when parsing a source file
                    continue
                elif not is_source and language != self.language:
                    # Skip other languages than the one the parsing is for
                    continue
                self._add_translation_string(key, translation, context=context)

        return template
