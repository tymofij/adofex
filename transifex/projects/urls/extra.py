# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

from transifex.projects.models import Project
from transifex.projects.views.project import myprojects
from transifex.projects.urls import PROJECT_URL_PARTIAL, public_project_list

# Project
urlpatterns = patterns('',
    url(
        regex = '^myprojects/$',
        view = myprojects,
        name = 'myprojects'),
)

urlpatterns += patterns('django.views.generic',
    url(
        regex = '^$',
        view = 'list_detail.object_list',
        kwargs = public_project_list,
        name = 'project_list'),
    url(
        '^recent/$', 'list_detail.object_list',
        kwargs = {
            'queryset': Project.public.recent(),
            'template_object_name': 'project',
            'extra_context' : {'type_of_qset' : 'projects.recent',},
        },
        name = 'project_list_recent'),
    url (
        regex = '^open_translations/$',
        view = 'list_detail.object_list',
        kwargs = {
            'queryset': Project.public.open_translations(),
            'template_object_name': 'project',
            'extra_context' : {'type_of_qset' : 'projects.open_translations',},
        },
        name = 'project_list_open_translations'),
)