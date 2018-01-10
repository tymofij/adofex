# -*- coding: utf-8 -*-

"""
Apple strings file handler/compiler
"""

from __future__ import absolute_import
import codecs, os, re, chardet
from transifex.txcommon.log import logger
from transifex.resources.models import SourceEntity, Template
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.formats.core import Handler, ParseError, CompileError
from transifex.resources.formats.resource_collections import StringSet, \
        GenericTranslation
from .compilation.compilers import Compiler
from .compilation.factories import CompilerFactory
from .compilation.mode import Mode
from .compilation.builders import MarkedSourceTranslationsBuilder,\
        AllTranslationsBuilder, ReviewedTranslationsBuilder


class StringsParseError(ParseError):
    pass


class StringsCompileError(ParseError):
    pass


class AppleMarkedSourceCompilerFactory(CompilerFactory):
    """Use source strings, but mark them."""

    def _get_translation_setter(self, language, mode):
        if Mode.TRANSLATED in mode:
            return MarkedSourceTranslationsBuilder(self.resource, language)
        elif Mode.REVIEWED in mode:
            return ReviewedTranslationsBuilder(self.resource, language)
        else:
            return AllTranslationsBuilder(self.resource, language)


class AppleStringsCompiler(Compiler):
    def _post_compile(self):
        line = r'(?P<prefix>(("(?P<key>[^"\\]*(?:\\.[^"\\]*)*)")|'\
               r'(?P<property>\w+))\s*=\s*"(?P<value>[^"\\]*(?:\\.'\
               r'[^"\\]*)*))_txss(?P<suffix>"\s*;)'
        regex = re.compile(line, re.U|re.DOTALL)
        self.compiled_template = regex.sub(
            lambda m: '/* ' + m.group('prefix') + m.group('suffix') + ' */',
            self.compiled_template
        )

class AppleStringsHandler(AppleMarkedSourceCompilerFactory, Handler):
    """
    Handler for Apple STRINGS translation files.

    Apple strings files *must* be encoded in cls.ENCODING encoding.
    """

    name = "Apple *.STRINGS file handler"
    format = "Apple STRINGS (*.strings)"
    method_name = 'STRINGS'
    format_encoding = 'UTF-16'

    HandlerParseError = StringsParseError
    HandlerCompileError = StringsCompileError

    CompilerClass = AppleStringsCompiler

    def _escape(self, s):
        return s.replace('"', '\\"').replace('\n', r'\n').replace('\r', r'\r')

    def _unescape_key(self, s):
        return s.replace('\\\n', '')

    def _unescape(self, s):
        s = s.replace('\\\n', '')
        return s.replace('\\"', '"').replace(r'\n', '\n').replace(r'\r', '\r')

    def _get_content(self, filename=None, content=None):
        if content is not None:
            if chardet.detect(content)['encoding'].startswith(self.format_encoding):
                encoding = self.format_encoding
            else:
                encoding = 'UTF-8'
            if isinstance(content, str):
                try:
                    return content.decode(encoding)
                except UnicodeDecodeError, e:
                    raise FormatError(unicode(e))
            else:
                return content
        if filename is None:
            return None
        return self._get_content_from_file(filename, self.format_encoding)

    def _get_content_from_file(self, filename, encoding):
        f = open(filename, 'r')
        try:
            content = f.read()
            if chardet.detect(content)['encoding'].startswith(self.format_encoding):
                #f = f.decode(self.format_encoding)
                encoding = self.format_encoding
            else:
                #f = f.decode(self.default_encoding)
                encoding = 'utf-8'
            f.close()
            f = codecs.open(filename, 'r', encoding=encoding)
            return f.read()
        except IOError, e:
            logger.warning(
                "Error opening file %s with encoding %s: %s" %\
                    (filename, self.format_encoding, e.message),
                exc_info=True
            )
            raise FormatError(e.message)
        except Exception, e:
            logger.error("Unhandled exception: %s" % e.message, exc_info=True)
            raise
        finally:
            f.close()

    def _parse(self, is_source, lang_rules):
        """Parse an apple .strings file and create a stringset with
        all entries in the file.

        See
        http://developer.apple.com/library/mac/#documentation/MacOSX/Conceptual/BPInternational/Articles/StringsFiles.html
        for details.
        """
        resource = self.resource
        context = ""
        f = self.content
        prefix = ""
        if f.startswith(u'\ufeff'):
            prefix = u'\ufeff'
            f = f.lstrip(u'\ufeff')
        #regex for finding all comments in a file
        cp = r'(?:/\*(?P<comment>(?:[^*]|(?:\*+[^*/]))*\**)\*/)'
        p = re.compile(r'(?:%s[ \t]*[\n]|[\r\n]|[\r]){0,1}(?P<line>(("(?P<key>[^"\\]*(?:\\.[^"\\]*)*)")|(?P<property>\w+))\s*=\s*"(?P<value>[^"\\]*(?:\\.[^"\\]*)*)"\s*;)'%cp, re.DOTALL|re.U)
        #c = re.compile(r'\s*/\*(.|\s)*?\*/\s*', re.U)
        c = re.compile(r'//[^\n]*\n|/\*(?:.|[\r\n])*?\*/', re.U)
        ws = re.compile(r'\s+', re.U)
        buf = u""
        end=0
        start = 0
        for i in p.finditer(f):
            start = i.start('line')
            end_ = i.end()
            line = i.group('line')
            key = i.group('key')
            comment = i.group('comment') or ''
            if not key:
                key = i.group('property')
            value = i.group('value')
            while end < start:
                m = c.match(f, end, start) or ws.match(f, end, start)
                if not m or m.start() != end:
                    raise StringsParseError("Invalid syntax: %s" %\
                            f[end:start])
                if is_source:
                    buf += f[end:m.end()]
                end = m.end()
            end = end_
            key = self._unescape_key(key)
            if is_source:
                if not value.strip():
                    buf += line
                    continue
                else:
                    line = f[start:end]
                    buf += line[0:i.start('value')-start]
                    buf += re.sub(
                        re.escape(value),
                        "%(hash)s_tr" % {'hash': hash_tag(key, context)},
                        line[i.start('value')-start:i.end('value')-start]
                    )
                    buf += line[i.end('value')-start:]
            elif not SourceEntity.objects.filter(resource=resource, string=key).exists() or not value.strip():
                # ignore keys with no translation
                continue
            self.stringset.add(GenericTranslation(
                    key, self._unescape(value), rule=5, context=context,
                    pluralized=False, fuzzy=False, comment=comment,
                    obsolete=False
            ))
        while len(f[end:]):
            m = c.match(f, end) or ws.match(f, end)
            if not m or m.start() != end:
                raise StringsParseError("Invalid syntax: %s" %  f[end:])
            if is_source:
                buf += f[end:m.end()]
            end = m.end()
            if end == 0:
                break
        if is_source:
            buf = prefix + buf
        return buf
