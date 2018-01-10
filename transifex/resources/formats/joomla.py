# -*- coding: utf-8 -*-

"""
Joomla INI file handler/compiler
"""

from __future__ import absolute_import
import os, re
import codecs
from transifex.txcommon.log import logger
from transifex.resources.models import SourceEntity
from .core import Handler, ParseError, CompileError
from .compilation import Compiler, MarkedSourceCompilerFactory
from .resource_collections import StringSet, GenericTranslation
from .utils.hash_tag import hash_tag
from .utils.decorators import *


class JoomlaParseError(ParseError):
    pass


class JoomlaCompileError(CompileError):
    pass


class JoomlaCompiler(Compiler):
    """Compiler for Joomla .ini files."""

    def _iter_by_line(self, content):
        """Iterate the content by line."""
        for line in content.split(self.linesep):
            yield line

    def _examine_content(self, content):
        """Determine the version of the file."""
        if "\r\n" in content:         # windows line ending
            self.linesep = "\r\n"
        else:
            self.linesep = "\n"
        for line in self._iter_by_line(content):
            if not line or line.startswith(('#', ';',)):
                continue
            try:
                source, trans = line.split('=', 1)
                if trans.strip().startswith('"') and\
                        trans.strip().endswith('"'):
                    self.jformat = JoomlaIniNew()
                else:
                    self.jformat = JoomlaIniOld()
                break
            except ValueError:
                continue
        return content

    def _post_compile(self):
        """Comment out source strings."""
        pattern = r'(?P<actual>.*)_txss'
        suffix = ""
        if isinstance(self.jformat, JoomlaIniNew):
            pattern += r'"'
            suffix = '"'
        regex = re.compile(pattern)
        self.compiled_template = regex.sub(
            lambda m: '%s '% self.jformat.comment_char +\
                    m.group('actual') + suffix, self.compiled_template
        )

    def _visit_translation(self, s):
        """Modify the translation depending on the version of the file."""
        return self.jformat.get_compilation(s)


class JoomlaINIHandler(MarkedSourceCompilerFactory, Handler):
    """
    Handler for Joomla's INI translation files.

    See http://docs.joomla.org/Specification_of_language_files
    and http://docs.joomla.org/Creating_a_language_definition_file.
    """

    name = "Joomla *.INI file handler"
    format = "Joomla INI (*.ini)"
    method_name = 'INI'
    comment_chars = ('#', ';', ) # '#' is for 1.5 and ';' for >1.6

    HandlerParseError = JoomlaParseError
    HandlerCompileError = JoomlaCompileError
    CompilerClass = JoomlaCompiler

    def _escape(self, s):
        return  s.replace('\n', r'\n').replace('\r', r'\r')

    def _unescape(self, s):
        return s.replace('\\n', '\n').replace('\\r', '\r')

    def _parse(self, is_source, lang_rules):
        """
        Parse an INI file and create a stringset with all entries in the file.
        """
        content = self.content
        self._find_linesep(content)
        comment = ""

        buf = ''
        initialized = False
        for line in self._iter_by_line(content):
            # Skip empty lines and comments
            if not line or line.startswith(self.comment_chars):
                if is_source:
                    buf += line + self.linesep
                    if line.startswith(self.comment_chars):
                        comment = line[1:] + self.linesep
                    else:
                        comment = ""
                continue

            try:
                source, trans = line.split('=', 1)
                if not initialized:
                    if trans.strip().startswith('"') and\
                            trans.strip().endswith('"'):
                        self.jformat = JoomlaIniNew()
                    else:
                        self.jformat = JoomlaIniOld()
                    initialized = True
            except ValueError:
                # Maybe abort instead of skipping?
                logger.warning('Could not parse line "%s". Skipping...' % line)
                continue

            escaped_trans = self.jformat.get_translation(trans)
            source = source.strip()
            trans = trans.strip()
            if isinstance(self.jformat, JoomlaIniNew):
                trans = trans[1:-1]
            context = ""        # We use empty context

            if is_source:
                if not trans.strip():
                    buf += line + self.linesep
                    continue
                source_len = len(source)
                new_line = line[:source_len] + re.sub(
                    re.escape(trans),
                    "%(hash)s_tr" % {'hash': hash_tag(source, context)},
                    line[source_len:]
                )
                buf += new_line + self.linesep
            elif not SourceEntity.objects.filter(resource=self.resource, string=source).exists()\
                    or not escaped_trans.strip():
                #ignore keys with no translation
                context=""
                continue
            self.stringset.add(GenericTranslation(
                    source, self._unescape(escaped_trans),
                    context=context, comment=comment
            ))
            comment = ""
        return buf[:buf.rfind(self.linesep)]


class JoomlaIniVersion(object):
    """Base class for the various formats of Joomla ini files."""

    @classmethod
    def create(cls, content):
        """Factory method to return the correct instance for the format.

        In versions >=1.6 translations are surrounded by double quotes.
        """
        if content[0] == ';':
            return JoomlaIniNew()
        else:
            return JoomlaIniOld()

    def get_translation(self, value):
        """
        Return the trasnlation value extracted from the specified string.
        """
        raise NotImplementedError


class JoomlaIniOld(JoomlaIniVersion):
    """Format for Joomla 1.5."""
    comment_char = '#'

    def _escape(self, value):
        return value.replace('"', "&quot;")

    def _unescape(self, value):
        return value.replace("&quot;", '"')

    def get_translation(self, value):
        return self._unescape(value)

    def get_compilation(self, value):
        return self._escape(value)


class JoomlaIniNew(JoomlaIniVersion):
    """Format for Joomla 1.6."""
    comment_char = ';'

    def _escape(self, value):
        return value.replace('"', '"_QQ_"')

    def _unescape(self, value):
        return value.replace("&quot;", '"').replace('"_QQ_"', '"')

    def get_translation(self, value):
        # Get rid of double-quote at the start and end of value
        return self._unescape(value.strip()[1:-1])

    def get_compilation(self, value):
        return self._escape(value)
