import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django import forms
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
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
from transifex.projects.models import Project
from transifex.simpleauth.forms import RememberMeAuthForm
from transifex.txcommon.filters import LogEntryFilter
from transifex.txcommon.log import logger
from transifex.txcommon.haystack_utils import prepare_solr_query_string, \
    fulltext_fuzzy_match_filter

@csrf_protect
def index(request):
    """ Adds Watched and Maintained projects lists for logged in user
    """
    if request.user.is_authenticated():
        maintained_projects = Project.objects.maintained_by(request.user)
        watched_projects = Project.objects.watched_by(request.user)
    else:
        maintained_projects = None
        watched_projects = None

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
