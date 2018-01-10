# -*- coding: utf-8 -*-
""" DTD file handler/compiler """

from __future__ import absolute_import
import os, re
from transifex.txcommon.log import logger
from transifex.resources.formats import FormatError
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.formats.core import Handler, ParseError, CompileError
from transifex.resources.formats.resource_collections import StringSet, \
        GenericTranslation
from .compilation import FillEmptyCompilerFactory


class DTDParseError(ParseError):
    pass


class DTDCompileError(CompileError):
    pass


class DTDHandler(FillEmptyCompilerFactory, Handler):
    """ Handler for DTD translation files. """
    default_encoding = 'UTF-8'
    format_encoding = 'UTF-8'
    name = "DTD file handler"
    format = "DTD (*.dtd)"
    method_name = "DTD"

    HandlerParseError = DTDParseError
    HandlerCompileError = DTDCompileError

    def _escape(self, s):
        """Escape format content.
        HTML escape double quotes. Other things are permitted.
        """
        return s.replace('"', '&quot;')

    def _unescape(self, s):
        """ Unescape entities for easy editing """
        return s.replace('&quot;', '"')

    def _should_skip_translation(self, se, trans):
        """ Never skip empty translations, they are valid in DTD
        """
        return False

    def _get_content_from_file(self, filename, encoding):
        fh = open(filename, "r")
        try:
            text = fh.read().decode(encoding)
            fh.close()
        except UnicodeDecodeError as e:
            logger.warning("Unicode decode error in DTDHandler.parse_file(): %s"
                    % unicode(e), exc_info=True)
            raise self.HandlerParseError(unicode(e))
        except IOError, e:
            logger.warning(
                "Error opening file %s with encoding %s: %s" %\
                    (filename, encoding, e.message),
                exc_info=True
            )
            raise FormatError(e.message)
        except Exception, e:
            logger.error("Unhandled exception in DTDHandler.parse_file(): %s"
                    % unicode(e), exc_info=True)
            raise self.HandlerParseError(unicode(e))
        finally:
            fh.close()
        return text

    def _parse(self, is_source, lang_rules):
        resource = self.resource

        context = ""
        text = self.content

        name_start_char = u':A-Z_a-z\xC0-\xD6\xD8-\xF6\xF8-\u02FF' + \
            u'\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF'+\
            u'\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD'
        name_char = name_start_char + ur'\-\.0-9' + u'\xB7\u0300-\u036F\u203F-\u2040'
        name = u'[' + name_start_char + u'][' + name_char + u']*'

        re_entity = u'<!ENTITY\s+(' + name + u')\s+((?:\"[^\"]*\")|(?:\'[^\']*\'))\s*>'
        re_comment = u'\<!\s*--(.*?)(?:--\s*\>)'
        re_tag = re.compile("(%s|%s)" % (re_entity, re_comment), re.M|re.S|re.U)

        latest_comment = ""
        for (orig, key, value, comment) in re.findall(re_tag, text):
            if key:
                self.stringset.add(GenericTranslation(
                        key, self._unescape(value[1:-1]),
                        rule=5, # no plural forms
                        context=context, comment=latest_comment,
                        pluralized=False, fuzzy=False,
                        obsolete=False
                ))
                if is_source:
                    hashed_entity = orig.replace(value,
                        '"%(hash)s_tr"' % {'hash': hash_tag(key, context)} )
                    text = text.replace(orig, hashed_entity)
                latest_comment = ""

            if comment:
                latest_comment = comment
        return text
