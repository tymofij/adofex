# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from django.conf import settings
from transifex.projects.urls import PROJECT_URL

from impala.views import moz_import

urlpatterns = patterns('',
   url(PROJECT_URL+r'import/$',  moz_import, name='moz_import'),
)


