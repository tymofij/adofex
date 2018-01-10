# -*- coding: utf-8 -*-
import copy
import itertools
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.db import transaction
from django.db.models import Q, Sum
from django.dispatch import Signal
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import Http404
from django.utils.translation import ugettext as _

from actionlog.models import action_logging
from transifex.languages.models import Language
from notification import models as notification
from transifex.projects.models import Project
from transifex.projects.permissions import *
from transifex.projects.signals import pre_team_request, pre_team_join, ClaNotSignedError
from transifex.resources.models import RLStats, Resource
from transifex.teams.forms import TeamSimpleForm, TeamRequestSimpleForm, ProjectsFilterForm
from transifex.teams.models import Team, TeamAccessRequest, TeamRequest
# Temporary
from transifex.txcommon import notifications as txnotification

from transifex.txcommon.decorators import one_perm_required_or_403, access_off
from transifex.txcommon.log import logger


def team_off(request, project, *args, **kwargs):
    """
    This view is used by the decorator 'access_off' to redirect a user when
    a project outsources its teams or allow anyone to submit files.

    Usage: '@access_off(team_off)' in front on any team view.
    """
    language_code = kwargs.get('language_code', None)
    if language_code:
        language = Language.objects.by_code_or_alias_or_404(language_code)
        extra_context = {
            'parent_template': 'teams/team_menu.html',
            'language': language,
            'project_team_members': True,
        }
    else:
        extra_context = {
            'parent_template': 'projects/project_menu.html',
            'project_overview': True,
        }

    context = {
        'project': project,
    }

    context.update(extra_context)

    return render_to_response('teams/team_off.html', context,
        context_instance=RequestContext(request)
    )

def update_team_request(team):
    project = team.project
    language = team.language
    try:
        team_request = project.teamrequest_set.get(
                language=language)
        user = team_request.user
        if not (user in team.members.all() or user in team.coordinators.all()\
                or user in team.reviewers.all()):
            team_access_request = TeamAccessRequest.objects.create(
                    user=user, team=team, created=team_request.created)
        team_request.delete()
    except TeamRequest.DoesNotExist, e:
        pass

def _team_create_update(request, project_slug, language_code=None, extra_context=None):
    """
    Handler for creating and updating a team of a project.

    This function helps to eliminate duplication of code between those two
    actions, and also allows to apply different permission checks in the
    respective views.
    """
    project = get_object_or_404(Project, slug=project_slug)
    team, language = None, None

    if language_code:
        language = get_object_or_404(Language, code=language_code)
        try:
            team = Team.objects.get(project__pk=project.pk,
                language=language)
        except Team.DoesNotExist:
            pass

    if request.POST:
        form = TeamSimpleForm(project, language, request.POST, instance=team)
        form.data["creator"] = request.user.pk
        if form.is_valid():
            team=form.save(commit=False)
            team_id = team.id
            team.save()
            form.save_m2m()

            # Delete access requests for users that were added
            for member in itertools.chain(team.members.all(),
                team.coordinators.all()):
                tr = TeamAccessRequest.objects.get_or_none(team, member)
                if tr:
                    tr.delete()

            # ActionLog & Notification
            # TODO: Use signals
            if not team_id:
                nt = 'project_team_added'
            else:
                nt = 'project_team_changed'

            context = {'team': team,
                       'sender': request.user}

            # Logging action
            action_logging(request.user, [project, team], nt, context=context)
            update_team_request(team)

            if settings.ENABLE_NOTICES:
                # Send notification for those that are observing this project
                txnotification.send_observation_notices_for(project,
                        signal=nt, extra_context=context)
                # Send notification for maintainers and coordinators
                from notification.models import NoticeType
                try:
                    notification.send(set(itertools.chain(project.maintainers.all(),
                        team.coordinators.all())), nt, context)
                except NoticeType.DoesNotExist:
                    pass

            return HttpResponseRedirect(reverse("team_members",
                                        args=[project.slug, team.language.code]))
    else:
        form = TeamSimpleForm(project, language, instance=team)

    context = {
        "project": project,
        "team": team,
        "project_team_form": form,
    }

    if extra_context:
        context.update(extra_context)

    return render_to_response("teams/team_form.html", context,
        context_instance=RequestContext(request))


pr_team_add=(("granular", "project_perm.maintain"),)
@access_off(team_off)
@login_required
@one_perm_required_or_403(pr_team_add,
    (Project, "slug__exact", "project_slug"))
def team_create(request, project_slug):
    extra_context = {
        'parent_template': 'projects/base.html',
        'team_create': True
    }
    return _team_create_update(request, project_slug,
        extra_context=extra_context)


pr_team_update=(("granular", "project_perm.coordinate_team"),)
@access_off(team_off)
@login_required
@one_perm_required_or_403(pr_team_update,
    (Project, 'slug__exact', 'project_slug'),
    (Language, "code__exact", "language_code"))
def team_update(request, project_slug, language_code):
    language = Language.objects.by_code_or_alias_or_404(language_code)
    extra_context = {
        'language': language,
        'parent_template': 'teams/team_menu.html',
        'team_update': True
    }
    return _team_create_update(request, project_slug, language_code,
        extra_context=extra_context)


@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def team_detail(request, project_slug, language_code):
    project = get_object_or_404(Project.objects.select_related(), slug=project_slug)
    language = Language.objects.by_code_or_alias_or_404(language_code)
    team = Team.objects.get_or_none(project, language.code)

    filter_form = ProjectsFilterForm(project, request.GET)

    projects_filter = []
    if filter_form.is_valid():
        projects_filter = filter_form.cleaned_data['project']

    if team and request.user.is_authenticated():
        user_access_request = request.user.teamaccessrequest_set.filter(
            team__pk=team.pk)
    else:
        user_access_request = None

    statslist = RLStats.objects.select_related('resource', 'resource__project',
        'lock', 'last_committer', 'resource__priority')

    if projects_filter:
        statslist = statslist.filter(resource__project__in=[projects_filter,])

    statslist = statslist.by_project_and_language(project, language)

    if not statslist and not team:
        raise Http404

    empty_rlstats = Resource.objects.select_related('project', 'priority'
        ).by_project(project).exclude(id__in=statslist.values('resource')
        ).order_by('project__name')

    if projects_filter:
        empty_rlstats = empty_rlstats.filter(project__in=[projects_filter,])

    total_entries = Resource.objects.by_project(project).aggregate(
        total_entities=Sum('total_entities'))['total_entities']

    if team:
        coordinators = team.coordinators.select_related('profile').all()[:6]
    else:
        coordinators = None

    # HACK: For every resource without an RLStats object, we need to fool
    # the template that there is one. So, we create the object without
    # saving it to the DB and append it to the list. I know this is not very
    # nice but I can't think of a nicer way to do it.
    statslist = list(statslist)
    for resource in empty_rlstats:
        rl = RLStats(resource=resource, language=language,
            untranslated=resource.total_entities,
        )
        statslist.append(rl)

    return render_to_response("teams/team_detail.html", {
        "project": project,
        "language": language,
        "team": team,
        "user_access_request": user_access_request,
        "project_team_page": True,
        "statslist": statslist,
        "filter_form": filter_form,
        "total_entries": total_entries,
        "coordinators": coordinators,
    }, context_instance=RequestContext(request))

@access_off(team_off)
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def team_members(request, project_slug, language_code):

    project = get_object_or_404(Project.objects.select_related(), slug=project_slug)
    language = get_object_or_404(Language.objects.select_related(), code=language_code)

    team = Team.objects.get_or_none(project, language.code)

    if team:
        team_access_requests = TeamAccessRequest.objects.filter(team__pk=team.pk)
    else:
        team_access_requests = None

    if team and request.user.is_authenticated():
        user_access_request = request.user.teamaccessrequest_set.filter(
            team__pk=team.pk)
    else:
        user_access_request = None

    return render_to_response("teams/team_members.html", {
        "project": project,
        "language": language,
        "team": team,
        "team_access_requests": team_access_requests,
        "user_access_request": user_access_request,
        "project_team_members": True,
    }, context_instance=RequestContext(request))

pr_team_delete=(("granular", "project_perm.maintain"),
                ("general",  "teams.delete_team"),)
@access_off(team_off)
@login_required
@one_perm_required_or_403(pr_team_delete,
    (Project, "slug__exact", "project_slug"))
def team_delete(request, project_slug, language_code):

    project = get_object_or_404(Project, slug=project_slug)
    team = get_object_or_404(Team, project__pk=project.pk,
        language__code=language_code)

    if request.method == "POST":
        _team = copy.copy(team)
        team.delete()
        messages.success(request, _("The team '%s' was deleted.") % _team.language.name)

        # ActionLog & Notification
        # TODO: Use signals
        nt = 'project_team_deleted'
        context = {'team': _team,
                   'sender': request.user}

        #Delete rlstats for this team in outsourced projects
        for p in project.outsourcing.all():
            RLStats.objects.select_related('resource').by_project_and_language(
                    p, _team.language).filter(translated=0).delete()

        # Logging action
        action_logging(request.user, [project, _team], nt, context=context)

        if settings.ENABLE_NOTICES:
            # Send notification for those that are observing this project
            txnotification.send_observation_notices_for(project,
                    signal=nt, extra_context=context)
            # Send notification for maintainers
            notification.send(project.maintainers.all(), nt, context)

        return HttpResponseRedirect(reverse("project_detail",
                                     args=(project_slug,)))
    else:
        return render_to_response(
            "teams/team_confirm_delete.html",
            {"team": team, "project": team.project},
            context_instance=RequestContext(request)
        )


@access_off(team_off)
@login_required
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'))
@transaction.commit_on_success
def team_join_request(request, project_slug, language_code):

    team = get_object_or_404(Team, project__slug=project_slug,
        language__code=language_code)
    project = team.project

    if request.POST:
        if request.user in team.members.all() or \
            request.user in team.coordinators.all():
            messages.warning(request,
                          _("You are already on the '%s' team.") % team.language.name)
        try:
            # send pre_team_join signal
            cla_sign = 'cla_sign' in request.POST and request.POST['cla_sign']
            cla_sign = cla_sign and True
            pre_team_join.send(sender='join_team_view', project=project,
                               user=request.user, cla_sign=cla_sign)

            access_request = TeamAccessRequest(team=team, user=request.user)
            access_request.save()
            messages.success(request,
                _("You requested to join the '%s' team.") % team.language.name)
            # ActionLog & Notification
            # TODO: Use signals
            nt = 'project_team_join_requested'
            context = {'access_request': access_request,
                       'sender': request.user}

            # Logging action
            action_logging(request.user, [project, team], nt, context=context)

            if settings.ENABLE_NOTICES:
                # Send notification for those that are observing this project
                txnotification.send_observation_notices_for(project,
                        signal=nt, extra_context=context)
                # Send notification for maintainers and coordinators
                notification.send(set(itertools.chain(project.maintainers.all(),
                    team.coordinators.all())), nt, context)


        except IntegrityError:
            transaction.rollback()
            messages.error(request,
                            _("You already requested to join the '%s' team.")
                             % team.language.name)
        except ClaNotSignedError, e:
            messages.error(request,
                             _("You need to sign the Contribution License Agreement for this "\
                "project before you join a translation team"))


    return HttpResponseRedirect(reverse("team_detail",
                                        args=[project_slug, language_code]))



pr_team_add_member_perm=(("granular", "project_perm.coordinate_team"),)
@access_off(team_off)
@login_required
@one_perm_required_or_403(pr_team_add_member_perm,
    (Project, "slug__exact", "project_slug"),
    (Language, "code__exact", "language_code"))
@transaction.commit_on_success
def team_join_approve(request, project_slug, language_code, username):

    team = get_object_or_404(Team, project__slug=project_slug,
        language__code=language_code)
    project = team.project
    user = get_object_or_404(User, username=username)
    access_request = get_object_or_404(TeamAccessRequest, team__pk=team.pk,
        user__pk=user.pk)

    if request.POST:
        if user in team.members.all() or \
            user in team.coordinators.all():
            messages.warning(request,
                            _("User '%(user)s' is already on the '%(team)s' team.")
                            % {'user':user, 'team':team.language.name})
            access_request.delete()
        try:
            team.members.add(user)
            team.save()
            messages.success(request,
                            _("You added '%(user)s' to the '%(team)s' team.")
                            % {'user':user, 'team':team.language.name})
            access_request.delete()

            # ActionLog & Notification
            # TODO: Use signals
            nt = 'project_team_join_approved'
            context = {'access_request': access_request,
                       'sender': request.user}

            # Logging action
            action_logging(request.user, [project, team], nt, context=context)

            if settings.ENABLE_NOTICES:
                # Send notification for those that are observing this project
                txnotification.send_observation_notices_for(project,
                        signal=nt, extra_context=context)
                # Send notification for maintainers, coordinators and the user
                notification.send(set(itertools.chain(project.maintainers.all(),
                    team.coordinators.all(), [access_request.user])), nt, context)

        except IntegrityError, e:
            transaction.rollback()
            logger.error("Something weird happened: %s" % str(e))

    return HttpResponseRedirect(reverse("team_detail",
                                        args=[project_slug, language_code]))


pr_team_deny_member_perm=(("granular", "project_perm.coordinate_team"),)
@access_off(team_off)
@login_required
@one_perm_required_or_403(pr_team_deny_member_perm,
    (Project, "slug__exact", "project_slug"),
    (Language, "code__exact", "language_code"))
@transaction.commit_on_success
def team_join_deny(request, project_slug, language_code, username):

    team = get_object_or_404(Team, project__slug=project_slug,
        language__code=language_code)
    project = team.project
    user = get_object_or_404(User, username=username)
    access_request = get_object_or_404(TeamAccessRequest, team__pk=team.pk,
        user__pk=user.pk)

    if request.POST:
        try:
            access_request.delete()
            messages.info(request,_(
                "You rejected the request by user '%(user)s' to join the "
                "'%(team)s' team."
                ) % {'user':user, 'team':team.language.name})

            # ActionLog & Notification
            # TODO: Use signals
            nt = 'project_team_join_denied'
            context = {'access_request': access_request,
                       'performer': request.user,
                       'sender': request.user}

            # Logging action
            action_logging(request.user, [project, team], nt, context=context)

            if settings.ENABLE_NOTICES:
                # Send notification for those that are observing this project
                txnotification.send_observation_notices_for(project,
                        signal=nt, extra_context=context)
                # Send notification for maintainers, coordinators and the user
                notification.send(set(itertools.chain(project.maintainers.all(),
                    team.coordinators.all(), [access_request.user])), nt, context)

        except IntegrityError, e:
            transaction.rollback()
            logger.error("Something weird happened: %s" % str(e))

    return HttpResponseRedirect(reverse("team_detail",
                                        args=[project_slug, language_code]))

@access_off(team_off)
@login_required
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'))
@transaction.commit_on_success
def team_join_withdraw(request, project_slug, language_code):

    team = get_object_or_404(Team, project__slug=project_slug,
        language__code=language_code)
    project = team.project
    access_request = get_object_or_404(TeamAccessRequest, team__pk=team.pk,
        user__pk=request.user.pk)

    if request.POST:
        try:
            access_request.delete()
            messages.success(request,_(
                "You withdrew your request to join the '%s' team."
                ) % team.language.name)

            # ActionLog & Notification
            # TODO: Use signals
            nt = 'project_team_join_withdrawn'
            context = {'access_request': access_request,
                       'performer': request.user,
                       'sender': request.user}

            # Logging action
            action_logging(request.user, [project, team], nt, context=context)

            if settings.ENABLE_NOTICES:
                # Send notification for those that are observing this project
                txnotification.send_observation_notices_for(project,
                        signal=nt, extra_context=context)
                # Send notification for maintainers, coordinators
                notification.send(set(itertools.chain(project.maintainers.all(),
                    team.coordinators.all())), nt, context)

        except IntegrityError, e:
            transaction.rollback()
            logger.error("Something weird happened: %s" % str(e))

    return HttpResponseRedirect(reverse("team_detail",
                                        args=[project_slug, language_code]))

@access_off(team_off)
@login_required
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'))
@transaction.commit_on_success
def team_leave(request, project_slug, language_code):

    team = get_object_or_404(Team, project__slug=project_slug,
        language__code=language_code)
    project = team.project

    if request.POST:
        try:
            if (team.members.filter(username=request.user.username).exists() or
                team.reviewers.filter(username=request.user.username).exists()):
                team.members.remove(request.user)
                team.reviewers.remove(request.user)
                messages.info(request, _(
                    "You left the '%s' team."
                    ) % team.language.name)

                # ActionLog & Notification
                # TODO: Use signals
                nt = 'project_team_left'
                context = {'team': team,
                           'performer': request.user,
                           'sender': request.user}

                # Logging action
                action_logging(request.user, [project, team], nt, context=context)

                if settings.ENABLE_NOTICES:
                    # Send notification for those that are observing this project
                    txnotification.send_observation_notices_for(project,
                            signal=nt, extra_context=context)
                    # Send notification for maintainers, coordinators
                    notification.send(set(itertools.chain(project.maintainers.all(),
                        team.coordinators.all())), nt, context)
            else:
                messages.info(request, _(
                    "You are not in the '%s' team."
                    ) % team.language.name)

        except IntegrityError, e:
            transaction.rollback()
            logger.error("Something weird happened: %s" % str(e))

    return HttpResponseRedirect(reverse("team_detail",
                                        args=[project_slug, language_code]))


# Team Creation
@access_off(team_off)
@login_required
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'))
@transaction.commit_on_success
def team_request(request, project_slug):

    if request.POST:
        language_pk = request.POST.get('language', None)
        if not language_pk:
            messages.error(request, _(
                "Please select a language before submitting the form."))
            return HttpResponseRedirect(reverse("project_detail",
                                        args=[project_slug,]))


        project = get_object_or_404(Project, slug=project_slug)

        language = get_object_or_404(Language, pk=int(language_pk))

        try:
            team = Team.objects.get(project__pk=project.pk,
                language__pk=language.pk)
            messages.warning(request,_(
                "'%s' team already exists.") % team.language.name)
        except Team.DoesNotExist:
            try:
                team_request = TeamRequest.objects.get(project__pk=project.pk,
                    language__pk=language.pk)
                messages.warning(request, _(
                    "A request to create the '%s' team already exists.")
                    % team_request.language.name)
            except TeamRequest.DoesNotExist:
                try:
                    # send pre_team_request signal
                    cla_sign = 'cla_sign' in request.POST and \
                            request.POST['cla_sign']
                    cla_sign = cla_sign and True
                    pre_team_request.send(sender='request_team_view',
                                          project=project,
                                          user=request.user,
                                          cla_sign=cla_sign)

                    team_request = TeamRequest(project=project,
                        language=language, user=request.user)
                    team_request.save()
                    messages.info(request, _(
                        "You requested creation of the '%s' team.")
                        % team_request.language.name)

                    # ActionLog & Notification
                    # TODO: Use signals
                    nt = 'project_team_requested'
                    context = {'team_request': team_request,
                               'sender': request.user}

                    # Logging action
                    action_logging(request.user, [project], nt, context=context)

                    if settings.ENABLE_NOTICES:
                        # Send notification for those that are observing this project
                        txnotification.send_observation_notices_for(project,
                                signal=nt, extra_context=context)
                        # Send notification for maintainers
                        notification.send(project.maintainers.all(), nt, context)

                except IntegrityError, e:
                    transaction.rollback()
                    logger.error("Something weird happened: %s" % str(e))
                except ClaNotSignedError, e:
                    messages.error(request, _(
                        "You need to sign the Contribution License Agreement "\
                        "for this project before you submit a team creation "\
                        "request."
                    ))

    return HttpResponseRedirect(reverse("project_detail", args=[project_slug,]))


pr_team_request_approve=(("granular", "project_perm.maintain"),)
@access_off(team_off)
@login_required
@one_perm_required_or_403(pr_team_request_approve,
    (Project, "slug__exact", "project_slug"),)
@transaction.commit_on_success
def team_request_approve(request, project_slug, language_code):

    team_request = get_object_or_404(TeamRequest, project__slug=project_slug,
        language__code=language_code)
    project = team_request.project

    if request.POST:
        try:
            team = Team(project=team_request.project,
                language=team_request.language, creator=request.user)
            team.save()
            team.coordinators.add(team_request.user)
            team.save()
            team_request.delete()
            messages.success(request, _(
                "You approved the '%(team)s' team requested by '%(user)s'."
                ) % {'team':team.language.name, 'user':team_request.user})

            # ActionLog & Notification
            # TODO: Use signals
            nt = 'project_team_added'
            context = {'team': team,
                       'sender': request.user}

            # Logging action
            action_logging(request.user, [project, team], nt, context=context)

            if settings.ENABLE_NOTICES:
                # Send notification for those that are observing this project
                txnotification.send_observation_notices_for(project,
                        signal=nt, extra_context=context)
                # Send notification for maintainers and coordinators
                notification.send(set(itertools.chain(project.maintainers.all(),
                    team.coordinators.all())), nt, context)

        except IntegrityError, e:
            transaction.rollback()
            logger.error("Something weird happened: %s" % str(e))

    return HttpResponseRedirect(reverse("project_detail",
                                        args=[project_slug,]))


pr_team_request_deny=(("granular", "project_perm.maintain"),)
@access_off(team_off)
@login_required
@one_perm_required_or_403(pr_team_request_deny,
    (Project, "slug__exact", "project_slug"),)
@transaction.commit_on_success
def team_request_deny(request, project_slug, language_code):

    team_request = get_object_or_404(TeamRequest, project__slug=project_slug,
        language__code=language_code)
    project = team_request.project

    if request.POST:
        try:
            team_request.delete()
            messages.success(request, _(
                "You rejected the request by '%(user)s' for a '%(team)s' team."
                ) % {'team':team_request.language.name,
                     'user':team_request.user})

            # ActionLog & Notification
            # TODO: Use signals
            nt = 'project_team_request_denied'
            context = {'team_request': team_request,
                       'performer': request.user,
                       'sender': request.user}

            # Logging action
            action_logging(request.user, [project], nt, context=context)

            if settings.ENABLE_NOTICES:
                # Send notification for those that are observing this project
                txnotification.send_observation_notices_for(project,
                        signal=nt, extra_context=context)
                # Send notification for maintainers and the user
                notification.send(set(itertools.chain(project.maintainers.all(),
                    [team_request.user])), nt, context)

        except IntegrityError, e:
            transaction.rollback()
            logger.error("Something weird happened: %s" % str(e))

    return HttpResponseRedirect(reverse("project_detail",
                                        args=[project_slug,]))

