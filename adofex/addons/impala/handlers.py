# -*- coding: utf-8 -*-

import re
from django.db.models import get_model
from django.conf import settings
from transifex.projects.signals import project_created, project_deleted
from transifex.projects.models import Project
from transifex.resources.formats.mozillaproperties import MozillaPropertiesHandler


def outsource_to_mozilla(sender, **kwargs):
    """
    Outsources translation of the newborn project to general Mozilla project
    """
    try:
        mozilla = Project.objects.get(slug='mozilla')
        sender.outsource = mozilla
        sender.save()
    except Project.DoesNotExist:
        pass

def properties_escape(self, s):
    """
    Escape special characters in Mozilla properties files.

    We escape \\, \n, \t.
    """
    return (s.replace('\\', r'\\')
             .replace('\n', r'\n')
             .replace('\r', r'\r')
             .replace('\t', r'\t'))

def properties_unescape(self, s):
    """
    Reverse the escape of special characters.
    """
    return (s.replace(r'\n', '\n')
             .replace(r'\r', '\r')
             .replace(r'\t', '\t')
             .replace(r'\\', '\\'))

def properties_replace_unicode_escapes(self, s):
    """
    Replaces \\u1234 escapes by the corresponding unicode characters.
    """
    return re.sub(r'\\[uU]([0-9A-Fa-f]+)', lambda m: unichr(int(m.group(1), 16)), s)

def connect():
    project_created.connect(outsource_to_mozilla)
    MozillaPropertiesHandler._escape = properties_escape
    MozillaPropertiesHandler._unescape = properties_unescape
    MozillaPropertiesHandler._visit_value = properties_replace_unicode_escapes
