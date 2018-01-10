# -*- coding: utf-8 -*-
import copy
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _

from actionlog.models import action_logging
from notification import models as notification
from transifex.projects.models import Project, HubRequest
from transifex.projects.permissions import *
from transifex.projects.signals import project_outsourced_changed

# Temporary
from transifex.txcommon import notifications as txnotification

from transifex.txcommon.decorators import one_perm_required_or_403
from transifex.txcommon.log import logger
from transifex.txcommon.views import json_result, json_error


@one_perm_required_or_403(pr_project_add_change,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=False)
def project_hub_projects(request, project_slug):
    project = get_object_or_404(
        Project.objects.select_related(), slug=project_slug
    )

    return render_to_response('projects/project_hub_projects.html', {
        'project': project,
        'hub_projects_page': True,
    }, context_instance=RequestContext(request))


@login_required
@one_perm_required_or_403(pr_project_add_change,
    (Project, "slug__exact", "project_slug"))
@transaction.commit_on_success
def project_hub_join_approve(request, project_slug, outsourced_project_slug):

    hub_request = get_object_or_404(HubRequest,
        project__slug=outsourced_project_slug,
        project_hub__slug=project_slug)

    outsourced_project = hub_request.project

    if request.POST:
        try:
            outsourced_project.outsource = hub_request.project_hub
            outsourced_project.anyone_submit = False
            outsourced_project.save()

            _hub_request = copy.copy(hub_request)
            hub_request.delete()

            messages.success(request, _("You added '%(project)s' to the "
                "'%(project_hub)s' project hub")% {
                    'project':outsourced_project,
                    'project_hub':hub_request.project_hub})

            # ActionLog & Notification
            nt = 'project_hub_join_approved'
            context = {'hub_request': hub_request,
                       'sender': request.user}

            # Logging action
            action_logging(request.user, [outsourced_project,
                hub_request.project_hub], nt, context=context)

            if settings.ENABLE_NOTICES:
                # Send notification for maintainers, coordinators and the user
                notification.send(outsourced_project.maintainers.all(), nt, context)

        except IntegrityError, e:
            transaction.rollback()
            logger.error("Something weird happened: %s" % str(e))

        project_outsourced_changed.send(sender=hub_request.project_hub)
    return HttpResponseRedirect(reverse("project_detail", args=(project_slug,)))


@login_required
@one_perm_required_or_403(pr_project_add_change,
    (Project, "slug__exact", "project_slug"))
@transaction.commit_on_success
def project_hub_join_deny(request, project_slug, outsourced_project_slug):

    hub_request = get_object_or_404(HubRequest,
        project__slug=outsourced_project_slug,
        project_hub__slug=project_slug)

    outsourced_project = hub_request.project

    if request.POST:
        try:
            _hub_request = copy.copy(hub_request)
            hub_request.delete()

            messages.info(request, _("You rejected the request of "
                "'%(project)s' to join the '%(project_hub)s' project hub")% {
                    'project': outsourced_project,
                    'project_hub':_hub_request.project_hub})

            # ActionLog & Notification
            # TODO: Use signals
            nt = 'project_hub_join_denied'
            context = {'hub_request': hub_request,
                       'sender': request.user}

            # Logging action
            action_logging(request.user, [outsourced_project,
                _hub_request.project_hub], nt, context=context)

            if settings.ENABLE_NOTICES:
                # Send notification for maintainers, coordinators and the user
                notification.send(outsourced_project.maintainers.all(), nt, context)

        except IntegrityError, e:
            transaction.rollback()
            logger.error("Something weird happened: %s" % e.message)

        project_outsourced_changed.send(sender=hub_request.project_hub)
    return HttpResponseRedirect(reverse("project_detail", args=(project_slug,)))


@login_required
@one_perm_required_or_403(pr_project_add_change,
    (Project, 'slug__exact', 'project_slug'))
@transaction.commit_on_success
def project_hub_join_withdraw(request, project_slug):

    # project_slug here refers to outsourced_project_slug. It was kept like
    # it to keep consistency across url regexes.
    hub_request = get_object_or_404(HubRequest, project__slug=project_slug)

    if request.POST:
        try:
            _hub_request = copy.copy(hub_request)
            hub_request.delete()
            messages.success(request, _("Request to join '%s' project hub "
                "was withdrawn") % _hub_request.project_hub)

            # ActionLog & Notification
            # TODO: Use signals
            nt = 'project_hub_join_withdrawn'
            context = {'hub_request': _hub_request,
                       'performer': request.user,
                       'sender': request.user}

            # Logging action
            action_logging(request.user, [_hub_request.project,
                hub_request.project_hub], nt, context=context)

            if settings.ENABLE_NOTICES:
                # Send notification for maintainers, coordinators and the user
                notification.send(_hub_request.project_hub.maintainers.all(),
                    nt, context)
        except IntegrityError, e:
            transaction.rollback()
            logger.error("Something weird happened: %s" % e.message)

    return HttpResponseRedirect(reverse("project_access_control_edit",
        args=(project_slug,)))


@login_required
@one_perm_required_or_403(pr_project_add_change,
    (Project, "slug__exact", "project_slug"),)
def project_hub_projects_toggler(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    url = reverse('project_hub_projects_toggler', args=(project_slug,))

    if request.method != 'POST':
        return json_error(_('Must use POST to activate'))

    # POST request must have a 'outsourced_project_slug' parameter
    outsourced_project_slug = request.POST.get('outsourced_project_slug', None)
    if not outsourced_project_slug:
        return json_error(_('Bad request.'))

    try:
        outsourced_project = project.outsourcing.get(slug=outsourced_project_slug)
        outsourced_project.outsource = None
        outsourced_project.save()

        ## ActionLog & Notification
        #nt = 'project_hub_added'
        #context = {'team': team,
                   #'sender': request.user}

        ## Logging action
        #action_logging(request.user, [project, team], nt, context=context)

        #if settings.ENABLE_NOTICES:
            ## Send notification for those that are observing this project
            #txnotification.send_observation_notices_for(project,
                    #signal=nt, extra_context=context)
            ## Send notification for maintainers and coordinators
            #notification.send(set(itertools.chain(project.maintainers.all(),
                #team.coordinators.all())), nt, context)

        result = {
            'style': 'undo',
            'title': _('Undo'),
            'outsourced_project_slug': outsourced_project_slug,
            'url': url,
            'error': None,
            }

    except Project.DoesNotExist:

        outsourced_project = get_object_or_404(Project,
            slug=outsourced_project_slug)
        outsourced_project.outsource = project
        outsourced_project.save()

        result = {
            'style': 'connect',
            'title': _('Disassociate'),
            'outsourced_project_slug': outsourced_project_slug,
            'url': url,
            'error': None,
            }

    except Exception, e:
        return json_error(e.message, result)

    project_outsourced_changed.send(sender=project)
    return json_result(result)
