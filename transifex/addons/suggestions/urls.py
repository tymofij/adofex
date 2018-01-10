# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from views import *

from transifex.resources.urls import RESOURCE_LANG_URL

#FIXME: Move this to resource if we agree.
ENTITY_URL = '^entities/(?P<entity_id>\d+)/'
SUGGESTIONS_URL = ENTITY_URL + 'lang/(?P<lang_code>[\-_@\w\.]+)/suggestions/'

urlpatterns = patterns('',
    url(SUGGESTIONS_URL+'create/$',
        suggestion_create, name='suggestion_create'),
    url(SUGGESTIONS_URL+'(?P<suggestion_id>\d+)/vote/1/$',
        suggestion_vote, {'direction': 'up'},
        name='suggestion_vote_up',),
    url(SUGGESTIONS_URL+'(?P<suggestion_id>\d+)/vote/-1/$',
        suggestion_vote, {'direction': 'down'},
        name='suggestion_vote_down',),
)

