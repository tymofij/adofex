# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings
from lotte.views import *
from transifex.projects.urls import PROJECT_URL
from transifex.resources.urls import RESOURCE_URL
from transifex.resources.views import clone_language


# Project-language URLs
# Prefix example: /projects/p/<project_slug>/l/<lang_code>/
PROJECT_LANG_URL = PROJECT_URL + r'l/(?P<lang_code>[\-_@\w\.]+)/'

urlpatterns = patterns('',
    # Project-wide Lotte
    url(PROJECT_LANG_URL+'$', translate, name='translate_project'),
    url(PROJECT_LANG_URL+'stringset/$', stringset_handling, name='stringset_handling'),
    url(PROJECT_LANG_URL+'push_translations/$', push_translation, name='push_translation'),
    url(PROJECT_URL+'developer_comment/$', add_edit_developer_comment_extra, name='developer_comment_extra'),
    url(PROJECT_LANG_URL+'delete/$', delete_translation, name='delete_translation'),
    url(PROJECT_LANG_URL+'exit/$', exit, name='exit_lotte'),
    url(PROJECT_LANG_URL+'proofread/$', proofread, name='proofread'),
)

# Resource-language URLs
# Prefix example: /projects/p/<project_slug>/resource/<resource_slug>/l/<lang_code>/
RESOURCE_LANG_URL = RESOURCE_URL + r'l/(?P<lang_code>[\-_@\w\.]+)/'

urlpatterns += patterns('',
    # Resource-specific Lotte
    url(RESOURCE_LANG_URL+'spellcheck/$', spellcheck, name='spellcheckurl'),
    url(RESOURCE_LANG_URL+'$', translate, name='translate_resource'),
    url(RESOURCE_LANG_URL+'view/$', view_strings, name='view_strings'),
    url(RESOURCE_URL+r'l/(?P<source_lang_code>[\-_@\w\.]+)/clone/(?P<target_lang_code>[\-_@\w\.]+)/$', clone_language, name='clone_translate'),
    url(RESOURCE_LANG_URL+'stringset/$', stringset_handling, name='stringset_handling'),
    url(RESOURCE_LANG_URL+'delete/$', delete_translation, name='delete_translation'),
    url(RESOURCE_LANG_URL+'proofread/$', proofread, name='proofread'),
    url(RESOURCE_LANG_URL+'exit/$', exit, name='exit_lotte'),
)

# General URLs

urlpatterns += patterns('',
    url('^entities/(?P<entity_id>\d+)/l/(?P<lang_code>[\-_@\w\.]+)/tab_details_snippet/$',
        tab_details_snippet, name='tab_details_snippet'),
    url('^entities/(?P<entity_id>\d+)/l/(?P<lang_code>[\-_@\w\.]+)/tab_suggestions_snippet/$',
        tab_suggestions_snippet, name='tab_suggestions_snippet'),
)
