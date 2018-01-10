"""
Simple URLConf for Django user authentication (no registration).
"""

from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.contrib.auth import views as auth_views
from django.utils.translation import ugettext as _
from transifex.simpleauth.views import login, logout, account_settings, profile_public

urlpatterns = patterns('',
    url(r'^login/$', login, name='login'),
    url(r'^logout/$', logout, name='logout'),
    url(r'^$', account_settings, name='profile_overview'),
    url(r'^profile/(?P<username>.+)/$', profile_public, name='profile_public'),
)
