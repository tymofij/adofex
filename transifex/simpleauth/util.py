from urllib import unquote
from django.conf import settings
from django.http import HttpResponseRedirect, str_to_unicode

DEFAULT_NEXT = getattr(settings, 'DEFAULT_REDIRECT_NEXT', '/')
def clean_next(next):
    """
    Do necessary init and clean to the 'next' variable.

    (Credits to django_authopenid.util)
    """
    if next is None:
        return DEFAULT_NEXT
    next = str_to_unicode(unquote(next), 'utf-8')
    next = next.strip()
    if next.startswith('/'):
        return next
    return DEFAULT_NEXT
