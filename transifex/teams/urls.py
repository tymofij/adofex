from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import redirect_to
from transifex.teams.views import *

TEAM_PARTIAL_URL =  r'language/(?P<language_code>[\-_@\w\.]+)/'

urlpatterns = patterns('',
    url(
        regex = r'languages/add/$',
        view = team_create,
        name = 'team_create',),
    url(
        regex = TEAM_PARTIAL_URL + r'edit/$',
        view = team_update,
        name = 'team_update',),
    url(
        regex = TEAM_PARTIAL_URL + r'$',
        view = team_detail,
        name = 'team_detail',),
    url(
        regex = TEAM_PARTIAL_URL + r'members/$',
        view = team_members,
        name = 'team_members',),
    url(
        regex = TEAM_PARTIAL_URL + r'delete/$',
        view = team_delete,
        name = 'team_delete',),
    url(
        regex = TEAM_PARTIAL_URL + r'request/$',
        view = team_join_request,
        name = 'team_join_request',),
    url(
        regex = TEAM_PARTIAL_URL + r'approve/(?P<username>[\.\w-]+)/$',
        view = team_join_approve,
        name = 'team_join_approve',),
    url(
        regex = TEAM_PARTIAL_URL + r'deny/(?P<username>[\.\w-]+)/$',
        view = team_join_deny,
        name = 'team_join_deny',),
    url(
        regex = TEAM_PARTIAL_URL + r'withdraw/$',
        view = team_join_withdraw,
        name = 'team_join_withdraw',),
    url(
        regex = TEAM_PARTIAL_URL + r'leave/$',
        view = team_leave,
        name = 'team_leave',),
    url(
        regex = r'languages/request/$',
        view = team_request,
        name = 'team_request',),
    url(
        regex = TEAM_PARTIAL_URL + r'approve/$',
        view = team_request_approve,
        name = 'team_request_approve',),
    url(
        regex = TEAM_PARTIAL_URL + r'deny/$',
        view = team_request_deny,
        name = 'team_request_deny',),
    # Legacy redirect
    url(r'teams/$', redirect_to, {'url': '/projects/p/%(project_slug)s/'}),
)
