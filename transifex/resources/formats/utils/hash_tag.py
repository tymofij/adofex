# -*- coding: utf-8 -*-
import re
from django.utils.hashcompat import md5_constructor


def hash_tag(source_entity, context):
    """Calculate the md5 hash of the (source_entity, context)."""
    if type(context) == list:
        if context:
            keys = [source_entity] + context
        else:
            keys = [source_entity, '']
    else:
        if context == 'None':
            keys = [source_entity, '']
        else:
            keys = [source_entity, context]
    return md5_constructor(':'.join(keys).encode('utf-8')).hexdigest()


def escape_context(value):
    """
    Escape context to be able to calculate hash of a (source_entity, context).
    """
    if type(value) == list:
        return [_escape_colon(v) for v in value]
    else:
        return _escape_colon(value)


def _escape_colon(value):
    """Escape colon in the string."""
    return re.sub(r'(?<!\\)\:', '\:', unicode(value))


class _HashRegex(object):
    """Functor to get a regular expression for a hash.

    We use MD5 to hash strings and store the hexdigest of it. So, the hash
    consists of 32 hexadecimal digits plus the (default) '_tr' suffix.

    We use a functor, so that the default regular expression will
    always be compiled and ready to be used.
    """

    md5_pattern = r'[0-9a-f]{32}'
    default_pattern = md5_pattern + '_tr'
    plural_pattern = md5_pattern + '_(tr|pl_\d)'
    default_regex = re.compile(default_pattern, re.IGNORECASE)
    plural_regex = re.compile(plural_pattern, re.IGNORECASE)

    def __init__(self, plurals=False):
        """Choose the default behavior: support plurals or not."""
        self.regex = self.plural_regex if plurals else self.default_regex

    def __call__(self, suffix=None):
        """Allow to use object as function.

        Users can sutomize just the suffix of the hash. In such case, the
        regular expression is compiled on demand.

        Args:
            suffix: The suffix to use.
        Returns:
            A compiled regular expression.
        """
        if suffix is None:
            return self.regex
        return re.compile(self.md5_pattern + suffix, re.IGNORECASE)

hash_regex = _HashRegex()
pluralized_hash_regex = _HashRegex(plurals=True)
