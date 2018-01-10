# -*- coding: utf-8 -*-

"""
Java properties file handler/compiler
"""
from __future__ import absolute_import
import os, re
from django.utils.hashcompat import md5_constructor
from transifex.txcommon.log import logger
from transifex.resources.models import SourceEntity
from transifex.resources.formats.utils.decorators import *
from .utils.hash_tag import hash_tag
from .properties import PropertiesCompiler, PropertiesHandler, \
        PropertiesParseError, PropertiesCompileError
from .resource_collections import StringSet, GenericTranslation


class JavaParseError(PropertiesParseError):
    pass


class JavaCompileError(PropertiesCompileError):
    pass


def convert_to_unicode(s):
    """Convert the string s to a proper unicode string.

    Java .properties files go through native2ascii first, which
    converts unicode characters to \uxxxx representations, ie to a series
    of bytes that represent the original unicode codepoint.

    We convert each \uxxxx representation back to the unicode character
    by finding the decimal representation of it and then
    calling ord on the result.

    Args:
        s: A string of the form '\\uxxxx'.
    Returns:
        The unicode character that corresponds to that.
    """
    assert len(s) == 6
    char = 0
    base = 16
    for rank, c in enumerate(reversed(s[2:])):
        char += int(c, base) * base ** rank
    return unichr(char)


def convert_to_ascii(c):
    """Convert the character c to a \uxxxx representation.

    THe method converts a unicode character c to a series of bytes
    that represent its codepoint.

    Args:
        c: The unicode character to convert.
    Returns:
        A string that represents its codepoint.
    """
    assert len(c) == 1
    s = ''
    base = 16
    n = ord(c)
    for i in xrange(4):
        (n, mod) = divmod(n, base)
        s = ''.join([hex(mod)[2], s])
    return ''.join(['\\u', s])


class JavaCompiler(PropertiesCompiler):
    """Compiler for java .properties files.

    We need to convert translations to unicode sequences.
    """

    def _visit_translation(self, translation):
        """Use unicode escape sequences to represent unicode characters."""
        for char in translation:
            if ord(char) in range(127, 160) or ord(char) > 255:
                translation = translation.replace(char, convert_to_ascii(char))
        return translation


class JavaPropertiesHandler(PropertiesHandler):
    """Handler for Java PROPERTIES translation files.

    Java properties files *must* be encoded in cls.default_encoding encoding.

    See
    http://download.oracle.com/javase/1.4.2/docs/api/java/util/PropertyResourceBundle.html,
    http://download.oracle.com/javase/1.4.2/docs/api/java/util/Properties.html#encoding and
    http://download.oracle.com/javase/1.4.2/docs/api/java/util/Properties.html#load(java.io.InputStream)
    """

    name = "Java *.PROPERTIES file handler"
    format = "Java PROPERTIES (*.properties)"
    method_name = 'PROPERTIES'
    format_encoding = 'ISO-8859-1'

    HandlerParseError = JavaParseError
    HandlerCompileError = JavaCompileError
    CompilerClass = JavaCompiler

    def _visit_value(self, value):
        """Convert the value to unicode-escaped string."""
        if value is not None:
            uni_chars = re.findall(r'(\\u[0-9A-Fa-f]{4})', value)
            for uni_char in uni_chars:
                value = value.replace(
                    uni_char, convert_to_unicode(uni_char)
                )
        return value
