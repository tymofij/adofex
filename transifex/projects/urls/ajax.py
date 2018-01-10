# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

from transifex.projects.views.hub import (project_hub_projects,
    project_hub_projects_toggler)
from transifex.projects.urls import PROJECT_URL_PARTIAL

# Project
urlpatterns = patterns('',
    url(
        regex = PROJECT_URL_PARTIAL+r'access/outsource/projects/association/$',
        view = project_hub_projects_toggler,
        name = 'project_hub_projects_toggler'),
)



