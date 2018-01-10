# -*- coding: utf-8 -*-
from django.utils import simplejson
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils.timesince import timeuntil
from django.utils.translation import ugettext as _

from transifex.languages.models import Language
from models import Lock, LockError
from transifex.projects.models import Project
from transifex.resources.models import Resource
from transifex.resources.utils import invalidate_template_cache
from transifex.teams.models import Team
from transifex.txcommon.decorators import one_perm_required_or_403

from permissions import pr_resource_language_lock

#try:
    #TFC_CACHING_PREFIX = settings.TFC_CACHING_PREFIX
#except:
    #TFC_CACHING_PREFIX = ""

@login_required
@one_perm_required_or_403(pr_resource_language_lock,
    (Project, 'slug__exact', 'project_slug'))
def resource_language_lock(request, project_slug, resource_slug, language_code):
    """
    View to lock a resource language.

    It uses a json response to be used with Ajax requests.
    """
    response={}
    if request.method == 'POST':
        resource = get_object_or_404(Resource.objects.select_related('project'),
            slug=resource_slug, project__slug=project_slug)
        language = get_object_or_404(Language, code=language_code)
        team = Team.objects.get_or_none(resource.project, language_code)

        try:
            lock = Lock.objects.create_update(resource, language, request.user)
            response['status'] = "OK"
            response['message'] = _("Lock created.")
            response['timeuntil'] = timeuntil(lock.expires)
        except LockError, e:
            response['status'] = "FAILED"
            response['message'] = e.message
    else:
        response['status'] = "FAILED"
        response['message'] = _("Sorry, but you need to send a POST request.")

    return HttpResponse(simplejson.dumps(response),
        mimetype='application/json')


@login_required
@one_perm_required_or_403(pr_resource_language_lock,
    (Project, 'slug__exact', 'project_slug'))
def resource_language_unlock(request, project_slug, resource_slug,
    language_code):
    """
    View to unlock a resource language.

    It uses a json response to be used with Ajax requests.
    """
    response={}
    if request.method == 'POST':
        resource = get_object_or_404(Resource.objects.select_related('project'),
            slug=resource_slug, project__slug=project_slug)
        language = get_object_or_404(Language, code=language_code)
        team = Team.objects.get_or_none(resource.project, language_code)

        lock = Lock.objects.get_valid(resource, language)
        if lock:
            try:
                lock.delete_by_user(request.user)
                response['status'] = "OK"
                response['message'] = _("Lock removed.")
            except LockError, e:
                return HttpResponseForbidden(_("You don't have permission to "
                    "unlock this file."))
        else:
            response['status'] = "FAILED"
            response['message'] = _("Unlock failed. Lock doesn't exist.")
    else:
        response['status'] = "FAILED"
        response['message'] = _("Sorry, but you need to send a POST request.")

    return HttpResponse(simplejson.dumps(response),
        mimetype='application/json')


