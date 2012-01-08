# -*- coding: utf-8 -*-

import os

from django.conf import settings
from django.template import Library
from django.template.loader_tags import BlockNode, BLOCK_CONTEXT_KEY
from django.utils.safestring import mark_safe

from impala.models import XpiFile

register = Library()

@register.inclusion_tag('download_project_xpi.html', takes_context=True)
def download_project_xpi(context, project):
    """Display a download link when project has xpi."""
    context.update({
        'has_xpi': XpiFile.objects.filter(project=project).count(),
        })
    return context

@register.filter
def supersuper(block):
    """Include the block value from the template parent two levels up."""
    if not isinstance(block, BlockNode):
        return ''
    render_context = block.context.render_context
    if not BLOCK_CONTEXT_KEY in render_context:
        return ''

    block_context = render_context[BLOCK_CONTEXT_KEY]
    saved = block_context.pop(block.name)
    if saved is None:
        return ''
    result = mark_safe(block.render(block.context))
    block_context.push(block.name, saved)
    return result
