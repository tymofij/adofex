# -*- coding: utf-8 -*-
import copy
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q, get_model, Sum, Max, Count
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.dispatch import Signal
from django.utils.translation import ugettext as _
from django.conf import settings
from django.views.generic import list_detail
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from actionlog.models import action_logging, LogEntry
from actionlog.filters import LogEntryFilter
from notification import models as notification
from transifex.projects.models import Project, HubRequest
from transifex.projects.forms import ProjectAccessControlForm, \
    ProjectForm, ProjectDeleteForm
from transifex.projects.permissions import *
from transifex.projects import signals

from transifex.languages.models import Language
from transifex.projects.permissions.project import ProjectPermission
from transifex.projects.signals import project_outsourced_changed
from transifex.releases.handlers import update_all_release
from transifex.resources.models import Resource, RLStats
from transifex.resources.utils import invalidate_template_cache
from transifex.teams.forms import TeamRequestSimpleForm
from transifex.projects.models import Permission

# Temporary
from transifex.txcommon import notifications as txnotification

from transifex.txcommon.decorators import one_perm_required_or_403
from transifex.txcommon.log import logger
from transifex.txcommon.views import json_result, json_error
# To calculate user_teams
from transifex.teams.models import Team

from priorities.models import level_display

Lock = get_model('locks', 'Lock')
TranslationWatch = get_model('watches', 'TranslationWatch')


def _project_create_update(request, project_slug=None,
    template_name='projects/project_form.html'):
    """
    Handler for creating and updating a project.

    This function helps to eliminate duplication of code between those two
    actions, and also allows to apply different permission checks in the
    respective views.
    """

    if project_slug:
        project = get_object_or_404(Project, slug=project_slug)
    else:
        project = None

    if request.method == 'POST':
        owner = project and project.owner or request.user
        project_form = ProjectForm(
            request.POST, request.FILES, instance=project, prefix='project',
            owner=owner
        )
        if project_form.is_valid():
            project = project_form.save(commit=False)
            project_id = project.id
            # Only here the owner is written to the project model
            if not project_id:
                project.owner = request.user

            # provide the form data to any signal handlers before project_save
            Signal.send(signals.pre_proj_save, sender=Project, instance=project,
                        form=project_form)
            project.save()
            project_form.save_m2m()

            # TODO: Not sure if here is the best place to put it
            Signal.send(signals.post_proj_save_m2m, sender=Project,
                        instance=project, form=project_form)

            # ActionLog & Notification
            context = {'project': project,
                       'sender': request.user}
            if not project_id:
                nt = 'project_added'
                action_logging(request.user, [project], nt, context=context)
            else:
                nt = 'project_changed'
                action_logging(request.user, [project], nt, context=context)
                if settings.ENABLE_NOTICES:
                    txnotification.send_observation_notices_for(project,
                                        signal=nt, extra_context=context)

            return HttpResponseRedirect(reverse('project_detail',
                                        args=[project.slug]),)
    else:
        # Make the current user the maintainer when adding a project
        if project:
            initial_data = {}
        else:
            initial_data = {"maintainers": [request.user.pk]}

        project_form = ProjectForm(instance=project, prefix='project',
                                   initial=initial_data)

    return render_to_response(template_name, {
        'project_form': project_form,
        'project': project,
    }, context_instance=RequestContext(request))


# Projects
@login_required
@one_perm_required_or_403(pr_project_add)
def project_create(request):
    return _project_create_update(request)

@login_required
@one_perm_required_or_403(pr_project_add_change,
    (Project, 'slug__exact', 'project_slug'))
def project_update(request, project_slug):
        return _project_create_update(request, project_slug)


@login_required
@one_perm_required_or_403(pr_project_add_change,
    (Project, 'slug__exact', 'project_slug'))
def project_access_control_edit(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    outsourced = project.outsource
    if request.method == 'POST':
        form = ProjectAccessControlForm(request.POST, instance=project,
            user=request.user)
        if form.is_valid():
            access_control = form.cleaned_data['access_control']
            project_type = form.cleaned_data['project_type']
            project = form.save(commit=False)
            project_hub = project.outsource
            hub_request = None

            # TODO call signal project_outsourced_changed
            if 'outsourced' != project_type:
                project.outsource = None
            else:
                check = ProjectPermission(request.user)
                if not (check.maintain(project) and check.maintain(project_hub)):
                    # If the user is not maintainer of both projects it does
                    # not associate the outsource project directly.
                    # It does a request instead.
                    try:
                        hub_request = HubRequest.objects.get(project=project)
                    except ObjectDoesNotExist:
                        hub_request = HubRequest(project=project)
                    hub_request.project_hub = project_hub
                    hub_request.user = request.user
                    hub_request.save()

                    messages.success(request,
                        _("Requested to join the '%s' project hub.") % project_hub)
                    # ActionLog & Notification
                    # TODO: Use signals
                    nt = 'project_hub_join_requested'
                    context = {'hub_request': hub_request,
                               'sender': request.user}

                    # Logging action
                    action_logging(request.user, [project, project_hub], nt, context=context)

                    if settings.ENABLE_NOTICES:
                        # Send notification for project hub maintainers
                        notification.send(project_hub.maintainers.all(), nt, context)

                    return HttpResponseRedirect(reverse('project_detail',args=[project.slug]),)


            if 'hub' == project_type:
                project.is_hub = True
            else:
                project.is_hub = False

            if ('free_for_all' == access_control and
                project_type != "outsourced"):
                project.anyone_submit = True
            else:
                project.anyone_submit = False

            # Check if cla form exists before sending the signal
            if 'limited_access' == access_control and \
            form.cleaned_data.has_key('cla_license_text'):
                # send signal to save CLA
                signals.cla_create.send(
                    sender='project_access_control_edit_view',
                    project=project,
                    license_text=form.cleaned_data['cla_license_text'],
                    request=request
                )

            project.save()
            form.save_m2m()
            handle_stats_on_access_control_edit(project)
            project_outsourced_changed.send(sender=project_hub)

            if outsourced and not project.outsource:
                # Drop resources from all-resources release of the hub project
                update_all_release(outsourced)

                # Logging action
                nt = 'project_hub_left'
                context = {'project': project, 'project_hub': outsourced,
                           'sender': request.user}
                action_logging(request.user, [project, outsourced], nt, context=context)

            return HttpResponseRedirect(reverse('project_detail',args=[project.slug]),)

    else:
        form = ProjectAccessControlForm(instance=project, user=request.user)

    return render_to_response('projects/project_form_access_control.html', {
        'project_permission': True,
        'project': project,
        'form': form,
    }, context_instance=RequestContext(request))


def handle_stats_on_access_control_edit(project):
    """
    This function is called in the access_control_edit of a project and deals
    with add/remove of RLStats for existing teams based on whether the project
    is outsourced or not.
    """
    if project.outsource:
        # The project got outsourced. Create RLStats for all teams of the
        # master project
        teams = project.outsource.team_set.all()
        for resource in project.resources.all():
            new_stats = teams.exclude(language__in=RLStats.objects.filter(resource=resource).values(
                'language'))
            for stat in new_stats:
                RLStats.objects.get_or_create(resource=resource,
                    language=stat.language)
            invalidate_template_cache("project_resource_details",
                project.slug, resource.slug)
            invalidate_template_cache("resource_details",
                project.slug, resource.slug)
    else:
        teams = project.team_set.all()
        for resource in project.resources.all():
            old_stats = RLStats.objects.filter(Q(resource=resource) &
                Q(translated=0) & ~Q(language__in=teams.values('language')))
            for stat in old_stats:
                stat.delete()
            invalidate_template_cache("project_resource_details",
                project.slug, resource.slug)
            invalidate_template_cache("resource_details",
                project.slug, resource.slug)


def _delete_project(request, project):
    project_ = copy.copy(project)
    project.delete()
    Permission.objects.filter(content_type__model="project",object_id=project_.id).delete()

    messages.success(request, _("The project '%s' was deleted." % project.name))

    # ActionLog & Notification
    nt = 'project_deleted'
    context = {'project': project_,
               'sender': request.user}
    action_logging(request.user, [project_], nt, context=context)
    if settings.ENABLE_NOTICES:
        txnotification.send_observation_notices_for(project_,
            signal=nt, extra_context=context)


@login_required
@one_perm_required_or_403(pr_project_delete,
    (Project, 'slug__exact', 'project_slug'))
def project_delete(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    if request.method == 'POST':
        delete_form = ProjectDeleteForm(data=request.POST, request=request)
        if delete_form.is_valid():
            _delete_project(request, project)
            return HttpResponseRedirect(reverse(getattr(settings,
                    "REDIRECT_AFTER_PROJECT_DELETE", "project_list")))
        else:
            return render_to_response('projects/project_delete.html', {
                'project': project,
                'delete_form': delete_form,
            }, context_instance=RequestContext(request))
    else:
        delete_form = ProjectDeleteForm(request=request)
        return render_to_response('projects/project_delete.html', {
            'project': project,
            'delete_form': delete_form,
        }, context_instance=RequestContext(request))


@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def project_detail(request, project_slug):
    project = get_object_or_404(Project.objects.select_related(), slug=project_slug)
    team_request_form = TeamRequestSimpleForm(project)

    source_language_codes = Language.objects.filter(
        Q(id=project.source_language.id) |
        Q(id__in=project.outsourcing.all().values('source_language').distinct())
    ).distinct().values_list('code', flat=True)

    language_stats = RLStats.objects.for_user(request.user
        ).by_project_language_aggregated(project)

    teams = project.available_teams.values('id').annotate(
        request_count=Count('join_requests', distinct=True),
        member_count=Count('members', distinct=True),
        reviewer_count=Count('reviewers', distinct=True),
        coordinator_count=Count('coordinators', distinct=True)
    ).values(
        'language__code', 'request_count', 'member_count',
        'reviewer_count', 'coordinator_count'
    )

    available_teams_codes = project.available_teams.values_list('language__code',
        flat=True)

    team_requests = project.teamrequest_set.select_related('language',
        'project', 'user').all().order_by('language__name')

    team_dict = {}
    for t in teams:
        lang_code = t['language__code']
        request_count = t['request_count']
        total_members = t['member_count'] + t['coordinator_count'] + t['reviewer_count']
        team_dict[lang_code] = (request_count, total_members)

    return render_to_response('projects/project_detail.html', {
        'project_overview': True,
        'project': project,
        'teams': team_dict,
        'languages': Language.objects.all(),
        'language_stats': language_stats,
        'source_language_codes': source_language_codes,
        'team_request_form': team_request_form,
        'available_teams_codes': available_teams_codes,
        'team_requests': team_requests,
        'maintainers': project.maintainers.select_related('profile').all()[:6],
        'releases': project.releases.select_related('project').all(),
    }, context_instance=RequestContext(request))


@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def project_resources(request, project_slug):
    project = get_object_or_404(Project.objects.select_related(), slug=project_slug)

    statslist = Resource.objects.filter(
        project=project
    ).values(
        'slug', 'name', 'category', 'priority__level',
        'total_entities', 'wordcount'
    ).annotate(
        last_update=Max('rlstats__last_update')
    )
    for stat in statslist:
        stat['priority__display'] = level_display(stat['priority__level'])

    return render_to_response('projects/project_resources.html', {
        'project_resources': True,
        'project': project,
        'statslist': statslist,
    }, context_instance=RequestContext(request))


@login_required
def myprojects(request):
    user = request.user

    maintain = Project.objects.maintained_by(user)
    submit_projects = Project.objects.translated_by(user)
    watched_projects = Project.get_watched(user)
    watched_resource_translations = TranslationWatch.get_watched(user)
    locks = Lock.objects.valid().filter(owner=user)

    context_var = {
        'maintain_projects': maintain,
        'submit_project_permissions': submit_projects,
        'watched_projects': watched_projects,
        'watched_resource_translations': watched_resource_translations,
        'locks': locks,
        'coordinator_teams': user.team_coordinators.all(),
        'member_teams': user.team_members.all(),
    }

    return render_to_response("projects/project_myprojects.html",
            context_var,
            context_instance = RequestContext(request))



