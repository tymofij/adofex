# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import get_model
from django import template
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_noop as _

Project = get_model('projects', 'Project')

register = template.Library()

@register.inclusion_tag('projects/project_hub_projects_toogler.html', takes_context=True)
def hub_associate_project_toogler(context, hub_project, outsourced_project):
    """Handle watch links for objects by the logged in user."""
    context['ENABLE_NOTICES'] = settings.ENABLE_NOTICES
    outsourced_project.url = reverse('project_hub_projects_toggler',
        args=(hub_project.slug,))
    context['outsourced_project'] = outsourced_project

    return context
