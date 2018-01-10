# -*- coding: utf-8 -*-

"""
Wikitext format handler.
"""

from __future__ import absolute_import
import os, re
from itertools import groupby
from transifex.txcommon.log import logger
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.formats.core import Handler, ParseError, CompileError
from transifex.resources.formats.resource_collections import StringSet, \
        GenericTranslation
from .compilation import FillEmptyCompilerFactory


class WikiParseError(ParseError):
    pass


class WikiCompileError(CompileError):
    pass


class WikiHandler(FillEmptyCompilerFactory, Handler):
    """Class for mediawiki markup."""

    name = "Wiki handler"
    format = "Files extracted from Wikipedia (.wiki)"
    method_name = 'WIKI'

    HandlerParseError = WikiParseError
    HandlerCompileError = WikiCompileError

    def _parse(self, is_source, lang_rules):
        self._find_linesep(self.content)
        par_splitter = self.linesep + self.linesep
        template_open = "{{"
        template_ends = "}}"

        template = self.content
        context = ''

        prev_split_pos = 0
        prev_text_pos = 0
        while 1:
            par_pos = self.content.find(par_splitter, prev_split_pos)
            t_open_pos = self.content.find(template_open, prev_split_pos)
            if prev_text_pos == -1:
                break
            elif par_pos == -1 and t_open_pos == -1:
                # end of document
                source = trans = self.content[prev_text_pos:].strip()
                prev_text_pos = -1
            elif par_pos < t_open_pos or t_open_pos == -1:
                source = trans = self.content[prev_text_pos:par_pos].strip()
                if par_pos == -1:
                    prev_split_pos = prev_text_pos = -1
                else:
                    prev_split_pos = prev_text_pos = par_pos + 2
            else:
                t_end_pos = self.content.find(template_ends, prev_split_pos + 1)
                prev_split_pos = t_end_pos
                continue

            if not source.strip('\n'):
                continue
            source_len = len(source)
            template = re.sub(
                re.escape(trans),
                "%(hash)s_tr" % {'hash': hash_tag(source, context)},
                template
            )
            self.stringset.add(GenericTranslation(
                    source, trans, context=context
            ))
        return template
