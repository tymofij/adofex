from django.conf.urls.defaults import *

from common import PROJECTS_URL

urlpatterns = patterns('',
    url(PROJECTS_URL, include('projects.urls.extra')),
)