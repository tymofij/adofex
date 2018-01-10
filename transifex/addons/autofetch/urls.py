# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from views import fetch_url

urlpatterns = patterns('',
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/fetch_url/$',
        view = fetch_url,
        name = 'fetch_url',),
)
