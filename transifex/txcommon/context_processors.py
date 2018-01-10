# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils import translation

def site_section(request):
    """
    Return a ContextProcessor with the tokens from the URL as a list.

    Eg. Templates accessed at a URL '/projects/foo/' will have a
    RequestContext processor with ``site_section`` available and equal to
    ['projects', 'foo'].
    
    To access in templates, use something like:
    
    {% if site_section.0 == "projects" %}...
    """

    try:
        ret = request.path.split('/')
    except IndexError:
        ret = ''
    # Avoid empty last token if URL ends with /
    if ret[-1] == '':
        ret.pop()
    return { 'site_section': ret[1:] }

def site_url_prefix_processor(request):
    """
    Inserts context variable SITE_URL_PREFIX for absolute URLs
    """
    return {"SITE_URL_PREFIX" : request.build_absolute_uri("/")[:-1] }


def bidi(request):
    """Adds to the context BiDi related variables

    LANGUAGE_DIRECTION -- Direction of current language ('ltr' or 'rtl')
    """
    if translation.get_language_bidi():
        extra_context = { 'LANGUAGE_DIRECTION':'rtl', }
    else:
        extra_context = { 'LANGUAGE_DIRECTION':'ltr', }
    return extra_context
