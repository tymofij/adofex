# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext

from django.utils.translation import ugettext as _

from transifex.txcommon.decorators import one_perm_required_or_403
from transifex.projects.models import Project
from transifex.projects.permissions import pr_resource_priority
from transifex.resources.models import Resource

# Allow only maintainers to cycle priority
@one_perm_required_or_403(pr_resource_priority,
                          (Project, "slug__exact", "project_slug"))
def cycle_resource_priority(request, project_slug, resource_slug,*args, **kwargs):
    """Return a template snippet with the new priority image."""

    resource = get_object_or_404(Resource, project__slug=project_slug,
                                 slug=resource_slug)

    resource.priority.cycle()

    return render_to_response("resource_priority_snippet.html",
        { 'priority': resource.priority },
        context_instance = RequestContext(request))
