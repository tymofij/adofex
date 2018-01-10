# -*- coding: utf-8 -*-

from datetime import date
from django.db.models import get_model
from django.conf import settings
from transifex.resources.signals import post_save_translation
from transifex.addons.lotte.signals import lotte_save_translation


def save_copyrights(sender, **kwargs):
    """
    Save copyright info for po files.
    """
    resource = kwargs['resource']
    language = kwargs['language']
    if resource.i18n_method != 'PO' or kwargs.get(
        'copyright-disabled', False):
        return
    copyrights = kwargs['copyrights']
    CModel = get_model('copyright', 'Copyright')
    for c in copyrights:
        owner = c[0]
        years = c[1]
        for year in years:
            CModel.objects.assign(
                resource=resource, language=language,
                owner=owner, year=year
            )


def lotte_copyrights(sender, **kwargs):
    """Save copyrights from lotte for PO files."""
    resource = kwargs['resource']
    if resource.i18n_method != 'PO':
        return
    language = kwargs['language']
    user = kwargs['user']

    firstname = user.first_name
    lastname = user.last_name
    email = user.email
    copyrights = [
        (
            ''.join([firstname, ' ', lastname, ' <', user.email, '>']),
            [str(date.today().year)]
        ),
    ]
    CModel = get_model('copyright', 'Copyright')
    for c in copyrights:
        owner = c[0]
        years = c[1]
        for year in years:
            CModel.objects.assign(
                resource=resource, language=language,
                owner=owner, year=year, user=user
            )


def connect():
    post_save_translation.connect(save_copyrights)
    lotte_save_translation.connect(lotte_copyrights)
