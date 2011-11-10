# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from django.conf import settings
from transifex.projects.urls import PROJECT_URL, RELEASE_URL
from transifex.urls import PROJECTS_URL

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


)
