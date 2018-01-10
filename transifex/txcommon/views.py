from __future__ import absolute_import
import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect
from django.views.generic import list_detail
from django.core.urlresolvers import reverse
from django.contrib.syndication.views import feed

from haystack.query import SearchQuerySet
from notification import models as notification
from userena.views import password_change
from userena.views import profile_edit as userena_profile_edit

from transifex.actionlog.models import LogEntry, action_logging
from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.simpleauth.forms import RememberMeAuthForm
from transifex.txcommon.feeds import TxNoticeUserFeed
from transifex.txcommon.filters import LogEntryFilter
from transifex.txcommon.forms import TxAuthenticationForm
from transifex.txcommon.haystack.utils import (support_fulltext_search,
        prepare_solr_query_string, fulltext_fuzzy_match_filter,
        fulltext_project_search_filter)
from transifex.txcommon.log import logger

from notification.decorators import basic_auth_required, simple_basic_auth_callback

FULLTEXT = support_fulltext_search()

@basic_auth_required(realm='Notices Feed', callback_func=simple_basic_auth_callback)
def feed_for_user(request):
    url = "feed/%s" % request.user.username
    return feed(request, url, {
        "feed": TxNoticeUserFeed,
    })


def permission_denied(request, template_name=None, extra_context={}, *args,
    **kwargs):
    """Wrapper to allow undeclared key arguments."""
    from authority.views import permission_denied
    return permission_denied(request, template_name, extra_context)

def search(request):
    query_string = prepare_solr_query_string(request.GET.get('q', ""))
    search_terms = query_string.split()
    index_query = SearchQuerySet().models(Project)
    spelling_suggestion = None

    if not FULLTEXT:
        try:
            results = index_query.auto_query(query_string)
            count = results.count()
        except TypeError:
            count = 0
    else:
        try:
            qfilter = fulltext_project_search_filter(query_string)
            results = index_query.filter(qfilter)
            spelling_suggestion = results.spelling_suggestion(query_string)
            count = results.count()
        except TypeError:
            results = []
            count = 0

    logger.debug("Searched for %s. Found %s results." % (query_string, count))
    return render_to_response("search.html",
        {'query': query_string,
         'terms': search_terms,
         'results': results,
         'spelling_suggestion': spelling_suggestion},
          context_instance = RequestContext(request))

@csrf_protect
def index(request):
    if settings.ENABLE_SIMPLEAUTH:
        form = RememberMeAuthForm()
    else:
        form = TxAuthenticationForm()
    return render_to_response("index.html",
        {'form': form,
         'next': request.path,
         'num_projects': Project.objects.count(),
         'num_languages': Language.objects.count(),
         'num_users': User.objects.count(),
        },
        context_instance = RequestContext(request))


@login_required
def user_timeline(request, *args, **kwargs):
    """
    Present a log of the latest actions of a user.

    The view limits the results and uses filters to allow the user to even
    further refine the set.
    """
    log_entries = LogEntry.objects.by_user(request.user)
    f = LogEntryFilter(request.GET, queryset=log_entries)

    return render_to_response("txcommon/user_timeline.html", {
        'f': f,
        'actionlog': f.qs
    }, context_instance = RequestContext(request))


def profile_public(request, username, template_name='userena/public.html'):
    """User public profile page."""
    user = get_object_or_404(
        User.objects.select_related('profile'), username=username
    )
    teams_coordinating = user.team_coordinators.public()
    projects_maintaining = Project.objects.maintained_by(user).public()

    entries = []
    for n, project in enumerate(projects_maintaining):
        entries.append({
            'action': 'maintaining',
            'project': project,
            'index': n
        })

    for n, team in enumerate(teams_coordinating):
        entries.append({
            'action': 'coordinating',
            'project': team.project,
            'team': team,
            'index': n
        })

    return render_to_response(template_name, {
        'profile': user.get_profile(),
        'entries': entries,
    }, context_instance=RequestContext(request))


@login_required
def profile_social_settings(request, username,
    template_name='userena/profile_social_settings.html'):
    """Social login settings page under user profile."""
    user = get_object_or_404(User, username=username)
    return render_to_response(template_name, {
        'profile': user.get_profile()
    }, context_instance=RequestContext(request))


@login_required
def profile_social_settings_redirect(request):
    """
    Redirect a logged in user to his social settings page. This is necessary
    because the URL is used in a settings variable by django-social-auth that
    doesn't support dynamics URL (i.e. with a username in it).
    """
    return HttpResponseRedirect(reverse('profile_social_settings',
        args=[request.user,]))


@login_required
def password_change_custom(request, username):
    """
    This was added because users created through django-social-auth don't
    have a usable password but we should allow them to set a new one.
    """
    if request.user.has_usable_password():
        pass_form = PasswordChangeForm
    else:
        pass_form = SetPasswordForm

    return password_change(request, username=username, pass_form=pass_form)

def profile_edit(request, username, edit_profile_form=None):
    if request.user.is_authenticated() and request.user.username == username:
        return userena_profile_edit(request, username=username,
                                    edit_profile_form=edit_profile_form)
    else:
        return HttpResponseRedirect(reverse("profile_public",
                                            kwargs={'username': username}))


# Ajax response

def json_result(result):
    return HttpResponse(simplejson.dumps(result))

def json_error(message, result=None):
    if result is None:
        result = {}
    result.update({
        'style': 'error',
        'error': message,
    })
    return json_result(result)
