# -*- coding: utf-8 -*-
import re
from transifex.resources.formats.validators import \
    PrintfFormatNumberValidator as PrintfValidator


def next_splitter_or_func(string, splitters, func, pseudo_type):
    """
    Helper for doing the next splitter check.
    
    If the list is not empty, call the next splitter decorator appropriately,
    otherwise call the decorated function.
    """
    if splitters:
        return splitters[0](string, splitters[1:])(func)(pseudo_type, 
            string)
    else:
        return func(pseudo_type, string)  


class SplitterDecorators(object):
    """
    A class decorator that receives a list of splitter decorator classes and
    calls the first splitter from the list passing the decorated function as
    an argument as well as the list of splitters without the called splitter.
    
    In case the list of splitters is empty, it calls the decorated function
    right away. 
    
    This decorator must be only used with method of classes inheriting from
    ``transifex.resources.formats.pseudo.PseudoTypeMixin``.
    """
    def __init__(self, splitters):
        self.splitters = splitters  
    
    def __call__(self, func):  
        def _wrapper(pseudo_type, string):  
            return next_splitter_or_func(string, self.splitters, func, 
                pseudo_type)
        return _wrapper  


class BaseSplitter(object):
    """
    Base class decorator for splitting a given string based on a regex and 
    call the subsequent splitter class available in the ``splitters`` var or 
    the decorated method.
    """
    REGEX = r''

    def __init__(self, string, splitters):
        self.string = string
        self.splitters = splitters  

    def __call__(self, func):
        def _wrapped(pseudo_type, string, **kwargs):
            text=[]
            keys = [l.group() for l in self._regex_matches(string)]
            nkeys = len(keys)
            i=0
            for key in keys:
                t = string.split(key,1)
                string = t[0]
                string = next_splitter_or_func(string, self.splitters, 
                    func, pseudo_type) 
                text.extend([string, key])
                i += 1
                string = t[1]
            string = next_splitter_or_func(string, self.splitters, 
                func, pseudo_type)
            text.append(string)
            return "".join(text)
        return _wrapped

    @classmethod
    def _regex_matches(cls, string):
        return re.finditer(cls.REGEX, string)


class PrintfSplitter(BaseSplitter):
    """
    Split the string on printf placeholders, such as %s, %d, %i, %(foo)s, etc.
    """
    # Lets reuse the printf regex from the validators
    REGEX = PrintfValidator.printf_re


class TagSplitter(BaseSplitter):
    """
    Split the string on XML/HTML tags, such as <b>, </b>, <a href="">, etc.
    """
    REGEX = r'(<|&lt;)(.|\n)*?(>|&gt;)'


class EscapedCharsSplitter(BaseSplitter):
    """
    Split the string on escaped chars, such as \\\\n, \\\\t, etc.
    """
    REGEX = r'(\\\\[\w]{1})'


class HTMLSpecialEntitiesSplitter(BaseSplitter):
    """
    Splits the string on HTML special entities, such as &lt;, &amp;, etc.
    """
    REGEX = r'&[a-zA-Z]+;'