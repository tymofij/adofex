# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from transifex.resources.urls import RESOURCE_URL_PARTIAL, RESOURCE_LANG_URL_PARTIAL
from transifex.resources.views import resource_actions, update_translation, \
    lock_and_get_translation_file, resource_pseudo_translation_actions

urlpatterns = patterns('',
    url(RESOURCE_URL_PARTIAL + r'l/(?P<target_lang_code>[\-_@\w\.]+)/actions/$',
        resource_actions, name='resource_actions'),
    url(RESOURCE_LANG_URL_PARTIAL + r'update/$',
        update_translation, name='update_translation'),
    url(RESOURCE_URL_PARTIAL + r'add_translation/$',
        update_translation, name='add_translation'),
    url(RESOURCE_LANG_URL_PARTIAL+'download/lock/$',
        lock_and_get_translation_file, name='lock_and_download_for_translation'),
    url(RESOURCE_URL_PARTIAL + r'pseudo_translation_actions/$',
        resource_pseudo_translation_actions, name='pseudo_translation_actions'),
)
