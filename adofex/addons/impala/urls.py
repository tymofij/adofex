# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from django.conf import settings
from transifex.projects.urls import PROJECT_URL
from transifex.releases.urls import RELEASE_URL_PARTIAL
from transifex.urls import PROJECTS_URL
from impala.forms import EditProfileForm

from django.contrib.auth.decorators import login_required
from txcommon.views import profile_edit as txcommon_profile_edit

RELEASE_URL = RELEASE_URL_PARTIAL[1:]

from impala.views import moz_import, message_watchers,\
    release_download, release_language_download, release_language_install

LANG_URL = PROJECTS_URL + RELEASE_URL[1:] + r'l/(?P<lang_code>[\-_@\w]+)/'

urlpatterns = patterns('',
    url(regex = PROJECT_URL + r'import/$',
        view = moz_import,
        name = 'moz_import'),
    url(
        regex = LANG_URL + 'install/$',
        view =  release_language_install,
        name = 'release_language_install',
    ),
    url(
        regex = LANG_URL + 'download/$',
        view =  release_language_download,
        name = 'release_language_download',
    ),
    url(
        regex = LANG_URL + 'download/skipped/$',
        view =  release_language_download,
        name = 'release_language_download_skipped',
        kwargs = {'skip': True},
    ),
   url(
        regex = PROJECTS_URL+RELEASE_URL[1:] + r'download/$',
        view =  release_download,
        name = 'release_download',
    ),
   url(
        regex = PROJECTS_URL+RELEASE_URL[1:] + r'download/skipped/$',
        view =  release_download,
        name = 'release_download_skipped',
        kwargs = {'skip': True},
    ),
    url(regex = PROJECT_URL + r'message/$',
        view = message_watchers,
        name = 'message_watchers'),

    url(regex   =   r'^accounts/(?P<username>(?!signout|signup|signin)[\.\w]+)/$',
        view    =   login_required(txcommon_profile_edit),
        kwargs  =   {'edit_profile_form': EditProfileForm},
        name    =   'userena_profile_edit'),
)
