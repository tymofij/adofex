# -*- coding: utf-8 -*-
import os
import codecs
import logging
from django.utils.translation import ugettext as _

# See https://docs.djangoproject.com/en/dev/ref/settings/#languages
gettext = lambda s: s


def available_languages(localedir):
    """Return available languages in the LINGUAS file."""
    available_languages = []
    linguas_file = os.path.join(localedir, 'LINGUAS')
    if not os.path.exists(linguas_file):
        raise EnvironmentError("The file 'locale/LINGUAS' cannot be read.")
    try:
        linguas = codecs.open(linguas_file, 'r')
        for lang in linguas.readlines():
            lang = lang.strip()
            if lang and not lang.startswith('#'):
                code, name = lang.split(None, 1)
                available_languages.append((code, gettext(name)))
    except IOError, e:
        logging.error(
            'The LINGUAS file (%(file)s) could not be opened: %(exc)s' %
            {'file': linguas_file, 'exc': e}
        )
    return available_languages
