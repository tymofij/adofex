# -*- coding: utf-8 -*-

"""
Modes for compiling a translation.
"""


class _Mode(object):
    """Class to suggest, what a translation is downloaded for.

    This class **should not** be used directly by the user. He should
    use the *constants* defined afterwards.

    The class has a ``_value`` variable, which is an integer that
    *remembers* which *features* were chosen.

    Each type of *feature* should define a value that is the next
    available power of two.
    """

    # use slots to save memory
    __slots__ = ('_value', 'label')

    def __init__(self, value=0, label=None):
        """Set the initial mode of the object."""
        self._value = value
        self.label = label

    def __or__(self, other):
        """Combine modes."""
        return _Mode(self._value + other._value)

    def __contains__(self, item):
        """Return whether the mode contains the specified state."""
        return (self._value >> (item._value - 1)) % 2

    def __unicode__(self):
        return u'<Mode %s>' % self._value


class Mode(object):
    """Act as a namespace for the pre-defined modes."""

    DEFAULT = _Mode(0, 'for_use')
    TRANSLATED = _Mode(1, 'for_translation')
    REVIEWED = _Mode(2, 'for_use_reviewed')
