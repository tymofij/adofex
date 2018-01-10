# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from priorities.views import *
from transifex.resources.urls import RESOURCE_URL

urlpatterns = patterns('',
    # Resource-specific Lotte
    url(RESOURCE_URL+'cycle_priority/$', cycle_resource_priority,
        name='cycle_resource_priority'),
)
