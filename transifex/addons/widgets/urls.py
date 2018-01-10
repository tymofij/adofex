# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from views import view_project_widgets

urlpatterns = patterns('',
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/widgets/$',
        view = view_project_widgets,
        name = 'project_widgets',
    )
)
