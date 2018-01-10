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
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.formats.properties import PropertiesHandler, \
        PropertiesParseError, PropertiesCompileError
from transifex.resources.formats.resource_collections import StringSet, \
        GenericTranslation


class UnicodeParseError(PropertiesParseError):
    pass


class UnicodeCompileError(PropertiesCompileError):
    pass


class UnicodePropertiesHandler(PropertiesHandler):
    """Handler for Unicode PROPERTIES translation files."""

    name = "Unicode *.PROPERTIES file handler"
    format = "Unicode PROPERTIES (*.properties)"
    method_name = 'UNICODEPROPERTIES'

    HandlerParseError = UnicodeParseError
    HandlerCompileError = UnicodeCompileError
