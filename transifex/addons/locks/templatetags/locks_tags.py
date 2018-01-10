# -*- coding: utf-8 -*-
from django.conf import settings
from django.db.models import get_model
from django.template import Library
from django.contrib.auth.models import AnonymousUser

Lock = get_model('locks', 'Lock')

register = Library()

@register.inclusion_tag('lock_resource_action.html', takes_context=True)
def lock_resource_action(context, resource, language):
    """Display a lock with the status of the object lock."""
    request = context['request']
    user = request.user
    lock = Lock.objects.get_or_none(resource, language)
    if request.user in (None, AnonymousUser()):
        context['can_lock'] = False
    else:
        context['can_lock'] = Lock.can_lock(resource, language, user)
    if lock:
        if not lock.valid():
            lock.delete()
            context['is_locked'] = False
        else:
            context['lock'] = lock
            context['is_unlockable'] = lock.can_unlock(user)
            context['is_locked'] = True
            context['is_owner'] = (lock.owner == user)
    else:
        context['is_locked'] = False
    context['resource'] = resource
    context['language'] = language
    context['locks_lifetime'] = settings.LOCKS_LIFETIME / 3600
    context['lock_html_id'] = '%s_%s' % (resource.id, language.id)
    context['next'] = request.META.get('HTTP_REFERER', None) or '/'
    return context

