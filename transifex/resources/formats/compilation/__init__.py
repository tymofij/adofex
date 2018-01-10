# -*- coding: utf-8 -*-

"""
The compilation package for Transifex.

This package hosts the code to compile a template of a resource to
a translation file.
"""

from __future__ import absolute_import
from .compilers import Compiler, PluralCompiler
from .decorators import NormalDecoratorBuilder, PseudoDecoratorBuilder, \
        EmptyDecoratorBuilder
from .builders import AllTranslationsBuilder, EmptyTranslationsBuilder, \
        ReviewedTranslationsBuilder, SourceTranslationsBuilder, \
        MarkedSourceTranslationsBuilder
from .factories import SimpleCompilerFactory, FillEmptyCompilerFactory, \
        AlwaysFillEmptyCompilerFactory, EmptyCompilerFactory, \
        MarkedSourceCompilerFactory, ReviewedMarkedSourceTranslationsBuilder
from .mode import Mode
