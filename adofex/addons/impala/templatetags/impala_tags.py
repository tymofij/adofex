# -*- coding: utf-8 -*-

import os

from django.conf import settings
from django.template import Library

from impala.models import XpiFile

register = Library()

@register.inclusion_tag('download_project_xpi.html', takes_context=True)
def download_project_xpi(context, project):
    """Display a download link when project has xpi."""
    context.update({
        'has_xpi': XpiFile.objects.filter(project=project).count(),
        })
    return context
