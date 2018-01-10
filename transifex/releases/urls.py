# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib.auth.decorators import login_required

from transifex.releases.feeds import ReleaseFeed, ReleaseLanguageFeed
from transifex.releases.views import *

RELEASE_URL_PARTIAL = r'^r/(?P<release_slug>[\-\w_]+)/'

feeds = {
    'release': ReleaseFeed,
    'release_language': ReleaseLanguageFeed,
}

urlpatterns = patterns('',
    url(
        regex = RELEASE_URL_PARTIAL + r'feed/$',
        view = release_feed,
        name = 'release_feed',
        kwargs = {'feed_dict': feeds,
                  'slug': 'release'}),
    url(
        regex = RELEASE_URL_PARTIAL + r'l/(?P<language_code>[\-_@\w\.]+)/feed/$',
        view = release_language_feed,
        name = 'release_language_feed',
        kwargs = {'feed_dict': feeds, 'slug': 'release_language'}),
)

urlpatterns += patterns('',
    url(
        regex = r'add-release/$',
        view = release_create_update,
        name = 'release_create',),
    url(
        regex = RELEASE_URL_PARTIAL + r'$',
        view = release_detail,
        name = 'release_detail'),
    url(
        regex = RELEASE_URL_PARTIAL + r'edit/$',
        view = release_create_update,
        name = 'release_edit',),
    url(
        regex = RELEASE_URL_PARTIAL + r'delete/$',
        view = release_delete,
        name = 'release_delete',),
    url(
        regex = RELEASE_URL_PARTIAL + r'l/(?P<language_code>[\-_@\w\.]+)/$',
        view = release_language_detail,
        name = 'release_language_detail',
    ),
)
