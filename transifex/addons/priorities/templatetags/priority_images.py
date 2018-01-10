# -*- coding: utf-8 -*-

from django import template
from django.utils.safestring import mark_safe
from priorities.models import PRIORITY_LEVELS


register = template.Library()

@register.filter
def priority_image_path(level):
    """Return the path to the appropriate image for the specified level."""
    if level not in map(lambda e: e[0], PRIORITY_LEVELS):
        level = 0
    return mark_safe("priorities/images/%s.png" % level)
