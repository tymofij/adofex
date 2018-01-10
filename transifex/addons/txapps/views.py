# -*- coding: utf-8 -*-

import requests
from django.utils import simplejson as json
from django.http import HttpResponse, HttpResponseRedirect, \
        HttpResponseForbidden
from django.views.generic.list_detail import object_list
from django.shortcuts import get_object_or_404, render_to_response
from django.template import Template, RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils.translation import ugettext as _
from transifex.txcommon.decorators import one_perm_required_or_403
from transifex.txcommon.log import logger
from transifex.projects.models import Project
from transifex.projects.permissions import pr_project_add_change
from txapps.models import TxApp
from txapps.exceptions import RemoteTxAppError
from webhooks.models import WebHook


@one_perm_required_or_403(
    pr_project_add_change,
    (Project, 'slug__exact', 'project_slug')
)
def apps_list(request, project_slug, **kwargs):
    """List the tx apps."""
    kwargs['extra_context'] = {
        'project_slug': project_slug,
        'apps_for_p': Project.objects.get(
            slug=project_slug).apps.values_list('slug', flat=True)
    }

    return object_list(request, **kwargs)


@one_perm_required_or_403(
    pr_project_add_change,
    (Project, 'slug__exact', 'project_slug')
)
def enable_app(request, project_slug, txapp_slug, **kwargs):
    """Enable an app for the specified project.

    Handle this as an AJAX view.
    """
    # TODO don't hardcode source language for projects
    # TODO Handle content=None, status=None (no response)
    txapp = get_object_or_404(TxApp, slug=txapp_slug)
    project = get_object_or_404(Project, slug=project_slug)
    url = '/'.join([txapp.url, 'tx/register',  project_slug])
    method = 'POST'
    try:
        res = _forward_to_app(url, method, post_data={'source_language': 'en'})
    except RemoteTxAppError, e:
        return HttpResponse(unicode(e))
    except Exception, e:
        msg = "Uncaught exception while enabling app %(app)s for %(project)s"
        logger.error(
            msg % {'app': txapp_slug, 'project': project_slug}, exc_info=True
        )
        return HttpResponse(unicode(e))
    url = '/'.join([txapp.url, 'tx/translated'])
    WebHook.objects.get_or_create(project=project, url=url, kind='a')
    txapp.projects.add(project)
    return HttpResponse('')


@one_perm_required_or_403(
    pr_project_add_change,
    (Project, 'slug__exact', 'project_slug')
)
def disable_app(request, project_slug, txapp_slug, **kwargs):
    """Disable an ap for the specified project.

    Handle this as an AJAX view.
    """
    txapp = get_object_or_404(TxApp, slug=txapp_slug)
    project = get_object_or_404(Project, slug=project_slug)
    url = '/'.join([txapp.url, 'tx/unregister',  project_slug])
    method = 'POST'
    try:
        res = _forward_to_app(url, method)
    except RemoteTxAppError, e:
        return HttpResponse(unicode(e))
    except Exception, e:
        msg = "Uncaught exception while enabling app %(app)s for %(project)s"
        logger.error(
            msg % {'app': txapp_slug, 'project': project_slug}, exc_info=True
        )
        return HttpResponse(unicode(e))
    url = '/'.join([txapp.url, 'tx/translated'])
    WebHook.objects.filter(project=project, url=url).delete()
    txapp.projects.remove(project)
    return HttpResponse('')


@csrf_exempt
@one_perm_required_or_403(
    pr_project_add_change,
    (Project, 'slug__exact', 'project_slug')
)
def get_from_app(request, project_slug, txapp_slug):
    """Get a template string from a tx app."""
    txapp = get_object_or_404(TxApp, slug=txapp_slug)
    project = get_object_or_404(Project, slug=project_slug)

    root_path = _root_namespace(request.path, txapp)
    requested_path = _remove_namespace_from_path(root_path, request.path)
    if not txapp.access_is_allowed(request.user, project, requested_path):
        return HttpResponseForbidden()
    logger.debug(
        "Path requested from tx app %s is %s" % (txapp_slug, requested_path)
    )

    url = '/'.join([txapp.url, project_slug, requested_path])
    try:
        res = _forward_to_app(url, request.method, dict(request.POST.items()))
    except RemoteTxAppError, e:
        return error_contacting_app(request, url, txapp, e)
    if 'next_url' in res:
        path = _add_namespace_to_path(root_path, res['next_url'])
        return HttpResponseRedirect(path)
    template = '\n'.join([
            '{% extends "txapp_base.html" %}',
            '{% block txapp %}',
            res['content'],
            '{% endblock %}',
    ]).replace("\{", "{").replace("\}", "}").replace("\%", "%")
    t = Template(template)
    context = RequestContext(
        request,
        {'txapp_root_url': root_path, 'is_owner': request.user == project.owner}
    )
    return HttpResponse(
        t.render(context)
    )


def _forward_to_app(url, method, post_data=None):
    """Forward the request to the tx app."""
    if method == "GET":
        res = requests.get(url)
    else:
        res = requests.post(url, data=post_data)
    if not res.ok:
        content = res.content if hasattr(res, 'content') else ''
        status_code = res.status_code if hasattr(res, 'status_code') else ''
        raise RemoteTxAppError(status_code, content)
    return json.loads(res.content)


def error_contacting_app(request, url, app, exception):
    """Handle the case, where an app did not respond.

    This view is called, if there was a HTTP error, when contacting the remote
    tx app.
    """
    if all([exception.status_code, exception.content]):
        log_msg = (
            "Error visiting URL %s for app %s: status code "
            "was %s and error_message %s" % (
                url, app.name, exception.status_code, exception.content
            )
        )
        view_msg = _("TxApp responded with an error: %s" % exception.content)
    else:
        log_msg = "Error contacting remote server: url is %s" % url
        view_msg = _("Error contacting app.")
    logger.error(log_msg)
    return render_to_response(
        'txapp_error.html',
        {
            'app_name': app.name,
            'error_message': view_msg
        },
        context_instance=RequestContext(request)
    )


def _add_namespace_to_path(root_path, path):
    """Add the necessary namespace to the specified path.

    The ``path`` should not start with '/'.
    """
    if path.startswith('/'):
        path = path[1:]
    return '/'.join([root_path, path])


def _remove_namespace_from_path(root_path, path):
    """Remove the namespace from the specified ``path``.

    The value returned does not begin with a '/'.
    """
    return path[len(root_path) + 1:]


def _root_namespace(request_path, txapp):
    """Find the root path for this ``txapp``."""
    pos = request_path.find(txapp.slug)
    return request_path[:pos + len(txapp.slug)]
