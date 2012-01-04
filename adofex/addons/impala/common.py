import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_protect
from django.views.generic import list_detail

from notification import models as notification
from haystack.query import SearchQuerySet

from actionlog.models import LogEntry, action_logging
from transifex.languages.models import Language
from transifex.teams.models import Team
from transifex.projects.models import Project
from transifex.simpleauth.forms import RememberMeAuthForm
from transifex.txcommon.filters import LogEntryFilter
from transifex.txcommon.log import logger
from transifex.txcommon.haystack_utils import prepare_solr_query_string, \
    fulltext_fuzzy_match_filter

from transifex.releases import RELEASE_ALL_DATA
from transifex.releases.models import Release
from transifex.resources.models import Resource, RLStats, _aggregate_rlstats

@csrf_protect
def index(request):
    """ Adds Watched and Maintained projects lists for logged in user
    """
    if request.user.is_authenticated():
        maintained_projects = Project.objects.maintained_by(request.user)
        watched_projects = Project.objects.watched_by(request.user)
        user_language_ids = Team.objects.filter(
            Q(members=request.user)|Q(coordinators=request.user)
            ).values_list('language', flat=True)
    else:
        maintained_projects = []
        watched_projects = []


    for project in watched_projects:
        try:
            release = Release.objects.get(slug=RELEASE_ALL_DATA['slug'],
                    project=project)
            total = Resource.objects.filter(releases=release).aggregate(
                total=Sum('total_entities'))['total']

            statlist = _aggregate_rlstats(
                RLStats.objects.filter(language__in=user_language_ids
                ).by_release(release).order_by('language__code'),
                'language', total)
            setattr(project, 'statlist', statlist)
        except:
            raise

    return render_to_response("index.html",
        {'form': RememberMeAuthForm(),
         'next': request.path,
         'num_projects': Project.objects.count(),
         'num_languages': Language.objects.count(),
         'num_users': User.objects.count(),
         'maintained_projects': maintained_projects,
         'watched_projects': watched_projects,
        },
        context_instance = RequestContext(request))
