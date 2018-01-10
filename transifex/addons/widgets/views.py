# -*- coding: utf-8 -*-
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from transifex.projects.models import Project
from transifex.projects.permissions import pr_project_private_perm
from transifex.resources.models import Resource
from transifex.txcommon.context_processors import site_url_prefix_processor
from transifex.txcommon.decorators import one_perm_required_or_403

def view_project_widgets(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    if project.private:
        raise PermissionDenied
    resources = Resource.objects.filter(project=project)
    if len(resources) > 0:
        default_resource = resources[0]
    else:
        default_resource = None
    return render_to_response("project_widgets.html",
        {
            'project' : project,
            'project_widgets' : True,
            'default_resource' : default_resource,
            'resources' : resources,
        },
        RequestContext(request, {}, [site_url_prefix_processor]))