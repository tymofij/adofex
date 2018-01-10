# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from piston.handler import BaseHandler, AnonymousBaseHandler
from piston.utils import rc, throttle, require_mime

from transifex.txcommon.decorators import one_perm_required_or_403
from transifex.txcommon.log import logger
from transifex.projects.permissions import *
from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.projects.permissions.project import ProjectPermission

from transifex.resources.decorators import method_decorator
from transifex.resources.models import Resource
from transifex.teams.models import Team
from transifex.releases.models import Release

from transifex.api.utils import BAD_REQUEST
from django.contrib.contenttypes.models import ContentType

from transifex.actionlog.models import LogEntry



class BadRequest(Exception):
    pass

class NoContentError(Exception):
    pass

class ActionlogHandler(BaseHandler):
    """
    Actionlog Handler for Read operation.
    """
    allowed_methods = ('GET')
    exclude = ()

    def _has_perm(self, user, project):
        """
        Check that the user has access to this resource.
        """
        perm = ProjectPermission(user)
        if not perm.private(project):
            return False
        return True

    def read(self, request, project_slug=None, resource_slug=None, release_slug=None,
            username=None, language_code=None, api_version=2,):
        try:
            if request.GET.has_key('limit'):
                limit = request.GET['limit']
            else:
                limit = None

            if username:
                user = User.objects.get(username=username)
                if request.user == user:
                    feeds = LogEntry.objects.filter(user=user,
                            content_type=ContentType.objects.get(model='project'))
                else:
                    feeds = LogEntry.objects.filter(user=user,
                            content_type=ContentType.objects.get(model='project'),
                            project__private=False)

            elif not project_slug:
                private_slugs = list(
                    Project.objects.filter(private=True).values_list('slug', flat=True)
                )
                feeds = LogEntry.objects.filter(
                    content_type=ContentType.objects.get(model='project')
                ).exclude(
                    project__slug__in=private_slugs
                )
                for slug in private_slugs:
                    feeds = feeds.exclude(message__contains='/projects/p/%s/'%slug)

            else:
                project = Project.objects.get(slug=project_slug)
                if not self._has_perm(request.user, project):
                    return rc.FORBIDDEN
                if resource_slug:
                    resource = Resource.objects.get(slug=resource_slug,
                            project=project)
                    feeds = LogEntry.objects.by_object(resource)
                elif language_code:
                    team = Team.objects.get(language__code=language_code,
                            project=project)
                    feeds = LogEntry.objects.by_object(team)
                elif release_slug:
                    release = Release.objects.get(slug=release_slug,
                            project=project)
                    feeds = LogEntry.objects.by_object(release)
                elif project_slug and request.path == reverse('project_actionlogs', args=[project_slug]):
                    feeds = LogEntry.objects.by_object(project)
                else:
                    if request.path.find('resources/actionlog/') > 0:
                        feeds = LogEntry.objects.by_object(project).filter(
                                action_type__label__startswith='project_resource')
                    elif request.path.find('teams/actionlog/') > 0:
                        feeds = LogEntry.objects.by_object(project).filter(
                                action_type__label__startswith='project_team')
                    elif request.path.find('releases/actionlog/') > 0:
                        feeds = LogEntry.objects.by_object(project).filter(
                                action_type__label__startswith='project_release')
            feeds = feeds.values('action_time', 'message', 'user__username')
            if limit:
                feeds = feeds[:limit]
            return feeds

        except Project.DoesNotExist, e:
            logger.warning(unicode(e))
            return rc.NOT_FOUND
        except Resource.DoesNotExist, e:
            logger.warning(unicode(e))
            return rc.NOT_FOUND
        except Team.DoesNotExist, e:
            logger.warning(unicode(e))
            return rc.NOT_FOUND
        except Release.DoesNotExist, e:
            logger.warning(unicode(e))
            return rc.NOT_FOUND
        except User.DoesNotExist, e:
            logger.warning(unicode(e))
            return rc.NOT_FOUND
