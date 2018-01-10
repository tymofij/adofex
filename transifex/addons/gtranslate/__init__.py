# -*- coding: utf-8 -*-

from django.db.models import get_model
from django.conf import settings


class Meta:
    title = "Control integration with google translate."
    author = "Apostolos Bessas"
    description = "Enables/disables translate.google.com integration for projects."


def is_gtranslate_allowed(project):
    """
    Check whether the use of the google translate service is allowed.

    It is not allowed if this project or the one this project
    outsources to has a value of False.
    """

    # Check the outsource first
    GtModel = get_model('gtranslate', 'Gtranslate')
    try:
        if project.outsource is not None:
            gt = GtModel.objects.get(project=project.outsource)
            if not gt.use_gtranslate:
                return False
    except GtModel.DoesNotExist, e:
        pass

    # Then the project
    try:
        gt = GtModel.objects.get(project=project)
        if not gt.use_gtranslate:
            return False
    except GtModel.DoesNotExist, e:
        pass

    # Assume True, if there is no entry in gtranslate for
    # project or outsource
    return True
