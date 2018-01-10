# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.views.decorators.cache import never_cache
from piston.resource import Resource
#from piston.authentication import OAuthAuthentication
from transifex.api.authentication import CustomHttpBasicAuthentication

#TODO: Implement full support for OAUTH and refactor URLs!
#auth = OAuthAuthentication(realm='Transifex API')

from transifex.languages.api import LanguageHandler
from transifex.projects.api import ProjectHandler
from transifex.resources.api import ResourceHandler, StatsHandler, \
        TranslationHandler, FormatsHandler, TranslationObjectsHandler,\
        SingleTranslationHandler
from transifex.releases.api import ReleaseHandler
from transifex.actionlog.api import ActionlogHandler
from transifex.api.views import reject_legacy_api

auth = CustomHttpBasicAuthentication(realm='Transifex API')

resource_handler = Resource(ResourceHandler, authentication=auth)
release_handler = Resource(ReleaseHandler, authentication=auth)
project_handler = Resource(ProjectHandler, authentication=auth)
stats_handler = Resource(StatsHandler, authentication=auth)
translation_handler = Resource(TranslationHandler, authentication=auth)
actionlog_handler = Resource(ActionlogHandler, authentication=auth)
formats_handler = Resource(FormatsHandler, authentication=auth)
translation_objects_handler = Resource(TranslationObjectsHandler,
        authentication=auth)
single_translation_handler = Resource(SingleTranslationHandler,
        authentication=auth)

urlpatterns = patterns('',
    url(
        r'^languages/$',
        reject_legacy_api,
        {'api_version': 1},
        name='api.languages',
    ), url(
        r'^projects/$',
        reject_legacy_api,
        {'api_version': 1},
        name='api_projects',
    ), url(
        r'^project/',
        reject_legacy_api,
        {'api_version': 1},
        name='api_project',
     ), url(
        r'^storage/',
        reject_legacy_api,
        {'api_version': 1},
        name='api.storage',
    ), url(
        r'^1/',
        reject_legacy_api,
        {'api_version': 1},
        name='api.languages',
    ), url(
        r'^2/projects/$',
        never_cache(project_handler),
        {'api_version': 2},
        name='apiv2_projects',
    ), url(
        r'^2/project/(?P<project_slug>[-\w]+)/$',
        never_cache(project_handler),
        {'api_version': 2},
        name='apiv2_project',
    ), url(
        r'^2/project/(?P<project_slug>[-\w]+)/resources/$',
        never_cache(resource_handler),
        {'api_version': 2},
        name='apiv2_resources',
    ), url(
        r'^2/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/$',
        never_cache(resource_handler),
        {'api_version': 2},
        name='apiv2_resource',
    ), url(
        r'^2/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/content/$',
        never_cache(translation_handler),
        {'api_version': 2, 'lang_code': 'source'},
        name='apiv2_source_content',
    ), url(
        r'^2/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/pseudo/$',
        never_cache(translation_handler),
        {'api_version': 2, 'lang_code': 'source', 'is_pseudo':True},
        name='apiv2_pseudo_content',
    ), url(
        r'^2/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/translation/(?P<lang_code>[\-_@\w\.]+)/$',
        never_cache(translation_handler),
        {'api_version': 2},
        name='apiv2_translation',
    ), url(
        r'^2/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/stats/$',
        never_cache(stats_handler),
        {'api_version': 2, 'lang_code': None},
        name='apiv2_stats',
    ), url(
        r'^2/project/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/stats/(?P<lang_code>[\-_@\w\.]+)/$',
        never_cache(stats_handler),
        {'api_version': 2},
        name='apiv2_stats',
    ), url(
        r'^2/project/(?P<project_slug>[-\w]+)/release/(?P<release_slug>[-\w]+)/$',
        never_cache(release_handler),
        {'api_version': 2},
        name='apiv2_release',
    ), url(
        r'^2/actionlog/$',
        actionlog_handler,
        {'api_version': 2},
        name='global_actionlogs',
    ), url(
        r'^2/accounts/profile/(?P<username>[\.\w-]+)/actionlog/$',
        actionlog_handler,
        {'api_version': 2},
        name='user_actionlogs',
    ), url(
        r'^2/project/(?P<project_slug>[\w-]+)/actionlog/$',
        actionlog_handler,
        {'api_version': 2},
        name='project_actionlogs',
    ), url(
        r'^2/projects/actionlog/$',
        actionlog_handler,
        {'api_version': 2},
        name='projects_actionlogs',
    ), url(
        r'^2/project/(?P<project_slug>[\w-]+)/teams/actionlog/$',
        actionlog_handler,
        {'api_version': 2},
        name='project_teams_actionlogs',
    ), url(
        r'^2/project/(?P<project_slug>[\w-]+)/team/(?P<language_code>[\-_@\w\.]+)/actionlog/$',
        actionlog_handler,
        {'api_version': 2},
        name='project_team_actionlogs',
    ), url(
        r'^2/project/(?P<project_slug>[\w-]+)/releases/actionlog/$',
        actionlog_handler,
        {'api_version': 2},
        name='project_releases_actionlogs',
    ), url(
        r'^2/project/(?P<project_slug>[\w-]+)/r/(?P<release_slug>[\w-]+)/actionlog/$',
        actionlog_handler,
        {'api_version': 2},
        name='project_release_actionlogs',
    ), url(
        r'^2/project/(?P<project_slug>[\w-]+)/resources/actionlog/$',
        actionlog_handler,
        {'api_version': 2},
        name='project_resources_actionlogs',
    ), url(
        r'^2/project/(?P<project_slug>[\w-]+)/resource/(?P<resource_slug>[\w-]+)/actionlog/$',
        actionlog_handler,
        {'api_version': 2},
        name='project_resource_actionlogs',
    ), url(
       r'^2/formats/$',
       formats_handler,
       {'api_version': 2},
       name='supported_formats',
    ), url(
       r'^2/project/(?P<project_slug>[\w-]+)/resource/(?P<resource_slug>[\w-]+)/translation/(?P<language_code>[\-_@\w\.]+)/strings/$',
       translation_objects_handler,
       {'api_version': 2},
       name='translation_strings'
    ), url(
       r'^2/project/(?P<project_slug>[\w-]+)/resource/(?P<resource_slug>[\w-]+)/translation/(?P<language_code>[\-_@\w\.]+)/string/(?P<source_hash>[0-9a-f]{32})/$',
       single_translation_handler,
       {'api_version': 2},
       name='translation_string'
    )
)
