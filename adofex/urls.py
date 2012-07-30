# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'impala.common.index', name="home"),
    url(r'^', include('transifex.urls.main')),
)
