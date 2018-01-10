# -*- coding: utf-8 -*-

"""
Mozilla properties file handler/compiler
"""

from __future__ import absolute_import
import os, re
from django.utils.hashcompat import md5_constructor
from transifex.txcommon.log import logger
from transifex.resources.models import SourceEntity
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.formats.core import Handler, ParseError, CompileError
from transifex.resources.formats.resource_collections import StringSet, \
        GenericTranslation
from transifex.resources.formats.properties import PropertiesHandler, \
        PropertiesParseError, PropertiesCompileError, PropertiesCompiler
from .compilation import FillEmptyCompilerFactory


class MozillaPropertiesParseError(PropertiesParseError):
    pass


class MozillaPropertiesCompileError(PropertiesCompileError):
    pass


class MozillaPropertiesHandler(FillEmptyCompilerFactory, PropertiesHandler):
    name = "Mozilla *.PROPERTIES file handler"
    format = "Mozilla PROPERTIES (*.properties)"
    method_name = 'MOZILLAPROPERTIES'
    format_encoding = 'UTF-8'

    HandlerParseError = MozillaPropertiesParseError
    HandlerCompileError = MozillaPropertiesCompileError
    CompilerClass = PropertiesCompiler

    escaped_unicode_pattern = re.compile(
            r'\\[uU]([0-9A-Fa-f]{4})')

    def _escape(self, s):
        """ preparing the string to be written to file
        """
        s = (s.replace('\n', r'\n')
              .replace('\r', r'\r')
              .replace('\t', r'\t')
        )
        # double the slashes, except when they start unicode sequence
        # or other control character
        s = re.sub(r'\\([^uUnrt])', r'\\\\\1', s)
        # double slashes at the end of the line too
        return re.sub(r'\\$', r'\\\\', s)

    def _unescape(self, s):
        """ Outputting the strings to the screen
        """
        return (s.replace(r'\n', '\n')
                 .replace(r'\r', '\r')
                 .replace(r'\t', '\t')
                 .replace(r'\\', '\\')
        )


    def _visit_value(self, value):

        def unpattern(m):
            """ Convert \uXXXX into its unicode equivalent.
                Except for spaces. \u0020 are there probably for a reason,
                and that reason usually is that Moz parser strips trailing spaces,
                so the only mean to use them is to put \u0020 into string.
            """
            charcode = m.group(1)
            if charcode == '0020':
                return r'\u'+charcode
            return unichr(int(charcode, 16))

        if value:
            return self.escaped_unicode_pattern.sub(unpattern, value)
