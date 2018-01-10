# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from transifex.projects.urls import PROJECT_URL
from txapps.models import TxApp
from txapps.views import apps_list, get_from_app, enable_app, disable_app


urlpatterns = patterns('',
    url(
        PROJECT_URL + r'apps/$',
        apps_list,
        name='txapps_list',
        kwargs={
            'queryset': TxApp.objects.select_related('projects.Project').all(),
            'template_object_name': 'txapps',
            'template_name': 'txapps_list.html',
        },
    ), url(
        '^ajax/projects/p/(?P<project_slug>[-\w]+)' + r'/apps/(?P<txapp_slug>[\w-]+)/enable',
        enable_app,
        name='enable_app_for_project',
    ), url(
        '^ajax/projects/p/(?P<project_slug>[-\w]+)' + r'/apps/(?P<txapp_slug>[\w-]+)/disable',
        disable_app,
        name='disable_app_for_project',
    ), url(
        PROJECT_URL + r'apps/(?P<txapp_slug>[\w-]+)/',
        get_from_app,
        name='get_from_app',
    )
)
