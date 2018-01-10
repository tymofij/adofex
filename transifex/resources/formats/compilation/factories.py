# -*- coding: utf-8 -*-

"""
Factories for compilers.
"""

from __future__ import absolute_import
from .decorators import NormalDecoratorBuilder, PseudoDecoratorBuilder, \
        EmptyDecoratorBuilder
from .builders import AllTranslationsBuilder, EmptyTranslationsBuilder, \
        ReviewedTranslationsBuilder, SourceTranslationsBuilder, \
        ReviewedSourceTranslationsBuilder, MarkedSourceTranslationsBuilder, \
        ReviewedMarkedSourceTranslationsBuilder
from .mode import Mode


class CompilerFactory(object):
    """Factory to create compilers.

    This should be used as a mixin.
    """

    def construct_compiler(self, language, pseudo_type, mode):
        """Construct a compiler.

        Args:
            language: The language to use.
            pseudo_type: The pseudo_type to use.
            mode: The mode of the compilation.
        Returns:
            A suitable compiler.
        """
        tdec = self._get_translation_decorator(pseudo_type)
        tset = self._get_translation_setter(language, mode)
        compiler = self._get_compiler(mode)
        compiler.translation_decorator = tdec
        compiler.translation_set = tset
        return compiler

    def _get_compiler(self, mode=None):
        """Construct the compiler to use.

        We use by default ``cls.CompilerClass``. If a format does not have
        any special needs, we only need to set the ``CompilerClass``
        variable to the appropriate compiler subclass.

        Otherwise, a subclass should override this, so that it can
        choose the appropriate compiler.
        """
        return self.CompilerClass(resource=self.resource)

    def _get_translation_decorator(self, pseudo_type):
        """Choose the decorator to use.

        Override in subclasses, if you need to use a custom one for a
        specific format.

        Args:
            pseudo_type: The pseudo type chosen.
        Returns:
            An instance of the applier.
        """
        if pseudo_type is None:
            return NormalDecoratorBuilder(escape_func=self._escape)
        else:
            return PseudoDecoratorBuilder(
                escape_func=self._escape,
                pseudo_func=pseudo_type.compile
            )

    def _get_translation_setter(self, language, mode):
        """Get the translations builder.

        This is used to fetch the set of translations to be used in
        the compilation process.

        Subclasses should override this.

        Args:
            language: The language for the translations.
            mode: The mode for the compilation.
        Returns:
            An instance of the apporpriate translations builder.
        """
        raise NotImplementedError


class EmptyCompilerFactory(CompilerFactory):
    """Return an empty translation set."""

    def _get_translation_setter(self, language, mode):
        return EmptyTranslationsBuilder(self.resource, language)


class SimpleCompilerFactory(CompilerFactory):
    """Use translation string set as is.

    The features this compiler offers are the default ones:
    - Uses only the translation strings, whenever a translation is
      asked.
    - Supports fetching only reviewed strings.

    This compiler should be used by formats such as PO.
    """

    def _get_translation_setter(self, language, mode):
        """Get the translations builder.

        We either use all translations or only reviewed ones.
        """
        if Mode.REVIEWED in mode:
            return ReviewedTranslationsBuilder(self.resource, language)
        else:
            return AllTranslationsBuilder(self.resource, language)


class FillEmptyCompilerFactory(CompilerFactory):
    """Fill empty translations with source strings, if asked.

    The features this compiler offers are:
    - If the user does not want to translate the file, he will receive a
      full translation, filled with source strings, where needed.
    - Supports reviewed translations only.
    """

    def _get_translation_setter(self, language, mode):
        """Get the translations builder."""
        if Mode.REVIEWED in mode and Mode.TRANSLATED in mode:
            return ReviewedSourceTranslationsBuilder(self.resource, language)
        elif Mode.REVIEWED in mode:
            return ReviewedTranslationsBuilder(self.resource, language)
        elif Mode.TRANSLATED in mode:
            return AllTranslationsBuilder(self.resource, language)
        else:
            return SourceTranslationsBuilder(self.resource, language)


class AlwaysFillEmptyCompilerFactory(CompilerFactory):
    """Always fill empty translations with source strings.

    The features this compiler offers are:
    - Source strings are always used for empty translations.
    - Supports reviewed translations only.
    """

    def _get_translation_setter(self, language, mode):
        """Get the translations builder."""
        if Mode.REVIEWED in mode:
            return ReviewedSourceTranslationsBuilder(self.resource, language)
        else:
            return SourceTranslationsBuilder(self.resource, language)


class MarkedSourceCompilerFactory(CompilerFactory):
    """Use source strings, but mark them."""

    def _get_translation_setter(self, language, mode):
        if Mode.REVIEWED in mode:
            return ReviewedMarkedSourceTranslationsBuilder(
                self.resource, language
            )
        else:
            return MarkedSourceTranslationsBuilder(self.resource, language)
