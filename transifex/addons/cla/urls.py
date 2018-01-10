from django.conf.urls.defaults import patterns, url
from transifex.projects.urls import PROJECT_URL
from cla.views import view, users, cla_project_sign

urlpatterns = patterns('',
    url(PROJECT_URL+r'cla/$', cla_project_sign, name="cla_project_sign"),
    url(PROJECT_URL+r'cla/snippet/$', view, name="cla_view"),
    url(PROJECT_URL+r'cla/snippet/users/$', users, name="cla_users"),
)
