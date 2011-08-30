# -*- coding: utf-8 -*-

import os

from django.conf import settings
from django.template import Library

from impala.models import XpiFile

register = Library()

@register.inclusion_tag('download_project_xpi.html')
def download_project_xpi(project):
    """Display a download link when project has xpi."""
    return {
        'has_xpi': XpiFile.objects.filter(project=project).count(),
        }
