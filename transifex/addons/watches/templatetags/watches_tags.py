# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import get_model
from django import template
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_noop as _

Project = get_model('projects', 'Project')
Resource = get_model('resources', 'Resource')
TranslationWatch = get_model('watches', 'TranslationWatch')

register = template.Library()

@register.inclusion_tag('watch_toggle.html', takes_context=True)
def watch_toggle(context, obj, language=None):
    """
    Handle watch links for objects by the logged in user
    """
    if isinstance(obj, Project):
        obj.toggle_watch_url = reverse('project_toggle_watch',
            args=(obj.slug,))
        obj.is_project = True

    elif isinstance(obj, Resource) and language:
        obj = TranslationWatch.objects.get_or_create(resource=obj,
            language=language)[0]
        obj.toggle_watch_url = reverse('resource_translation_toggle_watch',
            args=(obj.resource.project.slug, obj.resource.slug, language.code,))
        obj.is_resource = True

    user = context['request'].user
    obj.is_watched = obj.is_watched(user)
    context['obj'] = obj
    context['ENABLE_NOTICES'] = settings.ENABLE_NOTICES
    return context
