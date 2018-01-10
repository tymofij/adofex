import re
from django import forms

class UnicodeRegexField(forms.RegexField):
    """
    Return a regex field that allows unicode chars.

    The ``regex`` parameter needs to be a basestring for that to happen.
    """
    def __init__(self, regex, max_length=None, min_length=None,
        error_message=None, *args, **kwargs):

        if isinstance(regex, basestring):
            regex = re.compile(regex, re.UNICODE)

        super(UnicodeRegexField, self).__init__(regex, max_length,
            min_length, *args, **kwargs)

