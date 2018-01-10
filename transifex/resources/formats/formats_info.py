# -*- coding: utf-8 -*-
"""
Various info classes for the suported formats.

"""

from xml.sax.saxutils import escape as xml_escape
from xml.sax.saxutils import unescape as xml_unescape


class FormatInfo(object):
    """Represent individual formats.

    The class keeps extra info for the format and minor operations
    for that.
    """

    def prepare_for_viewing(self, value):
        """Prepare a value for viewing.

        This method prepares translations so that they can be viewed
        by translators.

        Args:
            value: The value to prepare for viewing.
        Returns:
            A ready-for-viewing value.
        """
        return value

    def prepare_for_saving(self, value):
        """Prepare a value for saving to the database.

        This method prepares translations entered by translators so that
        they can be saved to the database.

        Args:
            value: The value to prepare for saving.
        Returns:
            The prepared value.
        """
        return value


class XmlFormatInfo(FormatInfo):
    """Specialization for XML formats.

    XML based formats need to convert certain characters
    to xml entities and vice-versa.
    """

    def prepare_for_viewing(self, value):
        """Prepare a value for viewing.

        Support both basestring objects and iterables of basestring
        objects.
        """
        if isinstance(value, basestring):
            return self._unescape(value)
        else:
            return (self._unescape(v) for v in value)

    def prepare_for_saving(self, value):
        """Prepare a value for saving.

        Support both basestring objects and iterables of basestring
        objects.
        """
        if isinstance(value, basestring):
            return self._escape(value)
        else:
            return (self._escape(v) for v in value)

    def _escape(self, s):
        return xml_escape(s, {"'": "&apos;", '"': '&quot;'})

    def _unescape(self, s):
        return xml_unescape(s, {"&apos;": "'", '&quot;': '"'})
