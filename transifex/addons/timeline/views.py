# -*- coding: utf-8 -*-
from django.views.generic import list_detail
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from transifex.txcommon.decorators import one_perm_required_or_403
from transifex.projects.models import Project
from transifex.projects.permissions import pr_project_add_change,\
        pr_project_private_perm
from actionlog.models import LogEntry
from filters import LogEntryFilter


@login_required
def user_timeline(request, *args, **kwargs):
    """
    Present a log of the latest actions of a user.

    The view limits the results and uses filters to allow the user to even
    further refine the set.
    """
    log_entries = LogEntry.objects.by_user(request.user)
    f = LogEntryFilter(request.GET, queryset=log_entries)

    return render_to_response("timeline/timeline_user.html",
        {'f': f,
         'actionlog': f.qs},
        context_instance = RequestContext(request))


@login_required
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=False)
def project_timeline(request, project_slug, *args, **kwargs):
    """
    Present a log of the latest actions on the project.

    The view limits the results and uses filters to allow the user to even
    further refine the set.
    """
    project = get_object_or_404(Project, slug=project_slug)
    log_entries = LogEntry.objects.by_object(project)
    f = LogEntryFilter(request.POST, queryset=log_entries)
    # The template needs both these variables. The first is used in filtering,
    # the second is used for pagination and sorting.
    kwargs.setdefault('extra_context', {}).update(
        {'f': f,
         'actionlog': f.qs.select_related('action_type', 'user')})
    return list_detail.object_detail(request, slug=project_slug, *args, **kwargs)
