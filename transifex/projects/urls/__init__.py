# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.conf import settings
from tagging.views import tagged_object_list

from transifex.projects.feeds import LatestProjects, ProjectFeed, ProjectTimelineFeed
from transifex.projects.models import Project
from transifex.projects.views import *
from transifex.projects.views.project import *
from transifex.projects.views.hub import *
from transifex.projects.views.permission import *
from transifex.txcommon.decorators import one_perm_required_or_403
from transifex.urls import PROJECTS_URL

project_list = {
    'queryset': Project.objects.all(),
    'template_object_name': 'project',
}

public_project_list = {
    'queryset': Project.public.all(),
    'template_object_name': 'project',
    'extra_context' : {'type_of_qset' : 'projects.all',},
}

feeds = {
    'latest': LatestProjects,
    'project': ProjectFeed,
    'timeline': ProjectTimelineFeed,
}

# Used only in urls already under projects/, such as this one and
# resources/urls.py. For addons, use PROJECT_URL instead.
PROJECT_URL_PARTIAL = '^p/(?P<project_slug>[-\w]+)/'

# Full URL (including /projects/ prefix). The ^ on ^p/ must be escaped.
PROJECT_URL = PROJECTS_URL + PROJECT_URL_PARTIAL[1:]

#TODO: Temporary until we import view from a common place
urlpatterns = patterns('',
    url(
        regex = r'^feed/$',
        view = 'projects.views.slug_feed',
        name = 'project_latest_feed',
        kwargs = {'feed_dict': feeds,
                  'slug': 'latest'}),
    url(
        regex = '^p/(?P<param>[-\w]+)/resources/feed/$',
        view = 'projects.views.project_feed',
        name = 'project_feed',
        kwargs = {'feed_dict': feeds,
                  'slug': 'project'}),
    url(
	regex = '^p/(?P<param>[-\w]+)/feed/$',
	view = 'projects.views.timeline_feed',
	name = 'timeline_feed',
	kwargs = {'feed_dict':feeds,
		  'slug': 'timeline'}),
)


# Project
urlpatterns += patterns('',
    url(
        regex = '^add/$',
        view = project_create,
        name = 'project_create'),
    url(
        regex = PROJECT_URL_PARTIAL+r'edit/$',
        view = project_update,
        name = 'project_edit',),
    url(
        regex = PROJECT_URL_PARTIAL+r'edit/access/$',
        view = project_access_control_edit,
        name = 'project_access_control_edit',),
    url(
        regex = PROJECT_URL_PARTIAL+r'delete/$',
        view = project_delete,
        name = 'project_delete',),
    url(
        regex = PROJECT_URL_PARTIAL+r'access/pm/add/$',
        view = project_add_permission,
        name = 'project_add_permission'),
    url(
        regex = PROJECT_URL_PARTIAL+r'access/outsource/$',
        view = project_hub_projects,
        name = 'project_hub_projects'),
    url(
        regex = PROJECT_URL_PARTIAL+r'access/pm/(?P<permission_pk>\d+)/delete/$',
        view = project_delete_permission,
        name = 'project_delete_permission'),
    
    # Outsource / Hub
    url(
        regex = PROJECT_URL_PARTIAL+r'access/outsource/$',
        view = project_hub_projects,
        name = 'project_hub_projects'),
    url(
        regex = PROJECT_URL_PARTIAL+r'access/outsource/withdraw/$',
        view = project_hub_join_withdraw,
        name = 'project_hub_join_withdraw'),
    url(
        regex = PROJECT_URL_PARTIAL+r'access/outsource/(?P<outsourced_project_slug>[-\w]+)/approve/$',
        view = project_hub_join_approve,
        name = "project_hub_join_approve"),
    url(
        regex = PROJECT_URL_PARTIAL+r'access/outsource/(?P<outsourced_project_slug>[-\w]+)/deny/$',
        view = project_hub_join_deny,
        name = "project_hub_join_deny"),

    #url(
        #regex = PROJECT_URL_PARTIAL+r'access/rq/add/$',
        #view = project_add_permission_request,
        #name = 'project_add_permission_request'),
    url(
        regex = PROJECT_URL_PARTIAL+r'access/rq/(?P<permission_pk>\d+)/delete/$',
        view = project_delete_permission_request,
        name = 'project_delete_permission_request'),

    url(regex = PROJECT_URL_PARTIAL+r'access/rq/(?P<permission_pk>\d+)/approve/$',
        view = project_approve_permission_request,
        name = "project_approve_permission_request"),

    url(regex = PROJECT_URL_PARTIAL+r'$',
        view = project_detail,
        name = 'project_detail'),

    url(regex = PROJECT_URL_PARTIAL+r'resources/$',
        view = project_resources,
        name = 'project_resources'),
)


urlpatterns += patterns('django.views.generic',
    url(
        r'^tag/(?P<tag>[^/]+)/$',
        tagged_object_list,
        dict(queryset_or_model=Project.public.all(), allow_empty=True,
             template_object_name='project'),
        name='project_tag_list'),
)

urlpatterns += patterns('',
    url('', include('resources.urls')),
    url(PROJECT_URL_PARTIAL, include('teams.urls')),
    url(PROJECT_URL_PARTIAL, include('releases.urls')),
)
