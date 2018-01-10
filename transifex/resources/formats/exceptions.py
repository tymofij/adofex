# -*- coding: utf-8 -*-

"""
Hold all (base) exceptions used in the formats code.
"""

class FormatError(Exception):
    """Base class for all formats related errors."""


class ParseError(FormatError):
    """Base class for parsing errors."""


class CompileError(FormatError):
    """Base class for all compiling errors."""


class UninitializedCompilerError(FormatError):
    """Error raised by the compilers to indicate partial initilazation."""
