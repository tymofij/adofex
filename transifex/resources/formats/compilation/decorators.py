# -*- coding: utf-8 -*-

"""
Functors to decorate translations.

These functors are called whenever a translation is requested, when
compiling a template of a resource. An instance of a decorator is
passed to the compiler instance and the compiler will call it, whenever
it needs to use a translation string.

This allows us to escape the translations or create pseudo-translations.
"""


class DecoratorBuilder(object):
    """Builder for decorating the translation.

    By default, we allow the user to provide a ``escape`` function,
    which will be used to escape the translation string, if needed.
    """

    def __init__(self, *args, **kwargs):
        """Set the escape function to use."""
        self._escape = kwargs.get('escape_func', self._default_escape)

    def __call__(self, translation):
        """Decorate a translation.
        Args:
            translation: The translation string.
        Returns:
            The decorated translation.
        """
        raise NotImplementedError

    def _default_escape(self, s):
        """Default escape function."""
        return s


class NormalDecoratorBuilder(DecoratorBuilder):
    """Just escape the translation."""

    def __call__(self, translation):
        """Escape the string first."""
        if not translation:
            return ''
        return self._escape(translation)


class PseudoDecoratorBuilder(DecoratorBuilder):
    """Pseudo-ize the translation.

    It takes as an argument an extra function, which will produce the
    pseudo-ized translation.
    """

    def __init__(self, pseudo_func, *args, **kwargs):
        """Set the pseudo function to use."""
        self._pseudo_decorate = pseudo_func
        super(PseudoDecoratorBuilder, self).__init__(*args, **kwargs)

    def __call__(self, translation):
        """Use the pseudo function."""
        return self._pseudo_decorate(self._escape(translation))


class EmptyDecoratorBuilder(DecoratorBuilder):
    """Use an empty translation."""

    def __call__(self, translation):
        """Return an empty string."""
        return ""
