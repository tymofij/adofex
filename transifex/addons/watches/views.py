# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from notification import models as notification

from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.projects.permissions import pr_project_private_perm
from transifex.projects.permissions.project import ProjectPermission
from transifex.resources.models import Resource
from transifex.teams.models import Team
from transifex.txcommon.decorators import one_perm_required_or_403
from transifex.txcommon.views import (json_result, json_error, permission_denied)

from models import TranslationWatch, WatchException


@login_required
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'))
def resource_translation_toggle_watch(request, project_slug, resource_slug, language_code):
    """Add/Remove a TranslationWatch for a specific user."""

    if request.method != 'POST':
        return json_error(_('Must use POST to activate'))

    if not settings.ENABLE_NOTICES:
        return json_error(_('Notification is not enabled'))

    resource = get_object_or_404(Resource, slug=resource_slug,
                                project__slug=project_slug)
    project = resource.project
    language = get_object_or_404(Language, code=language_code)
    team = Team.objects.get_or_none(project, language_code)

    check = ProjectPermission(request.user)
    if not check.submit_translations(team or project) and not \
        check.maintain(project) and not \
        request.user.has_perm('watches.add_translationwatch') and not \
        request.user.has_perm('watches.delete_translationwatch'):
        return permission_denied(request)

    url = reverse('resource_translation_toggle_watch', args=(project_slug,
        resource_slug, language_code))

    try:
        twatch = TranslationWatch.objects.get(resource=resource,
            language=language)

        result = {
            'style': 'watch_add',
            'title': _('Watch it'),
            'id': twatch.id,
            'url': url,
            'error': None,
        }

        notification.stop_observing(twatch, request.user,
            signal='project_resource_translation_changed')

    except (TranslationWatch.DoesNotExist,
        notification.ObservedItem.DoesNotExist):

        try:
            twatch = TranslationWatch.objects.get_or_create(resource=resource,
                language=language)[0]

            result = {
                'style': 'watch_remove',
                'title': _('Stop watching'),
                'id': twatch.id,
                'url': url,
                'error': None,
            }

            notification.observe(twatch, request.user,
                'project_resource_translation_changed',
                signal='project_resource_translation_changed')

        except WatchException, e:
            return json_error(e.message, result)
    return json_result(result)


@login_required
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=False)
def project_toggle_watch(request, project_slug):
    """Add/Remove watches on a project for a specific user."""
    if request.method != 'POST':
        return json_error(_('Must use POST to activate'))

    if not settings.ENABLE_NOTICES:
        return json_error(_('Notification is not enabled'))

    project = get_object_or_404(Project, slug=project_slug)
    url = reverse('project_toggle_watch', args=(project_slug,))

    project_signals = ['project_changed',
                       'project_deleted',
                       'project_release_added',
                       'project_release_deleted',
                       'project_resource_added',
                       'project_resource_deleted']
    release_signals = ['project_release_changed',]

    resource_signals = ['project_resource_changed']
    try:
        result = {
            'style': 'watch_add',
            'title': _('Watch this project'),
            'project': True,
            'url': url,
            'error': None,
        }

        for signal in project_signals:
            try:
                notification.stop_observing(project, request.user, signal)
            except notification.ObservedItem.MultipleObjectsReturned, e:
                notification.ObservedItem.objects.filter(user=request.user,
                        signal=signal, content_type__model='project',
                        object_id = project.id).delete()
        for release in project.releases.all():
            for signal in release_signals:
                try:
                    notification.stop_observing(release, request.user, signal)
                except notification.ObservedItem.MultipleObjectsReturned, e:
                    notification.ObservedItem.objects.filter(user=request.user,
                        signal=signal, content_type__model='release',
                        object_id = release.id).delete()
        for resource in project.resources.all():
            for signal in resource_signals:
                try:
                    notification.stop_observing(resource, request.user, signal)
                except notification.ObservedItem.MultipleObjectsReturned, e:
                    notification.ObservedItem.objects.filter(user=request.user,
                        signal=signal, content_type__model='resource',
                        object_id=resource.id).delete()

    except notification.ObservedItem.DoesNotExist:
        try:
            result = {
                'style': 'watch_remove',
                'title': _('Stop watching this project'),
                'project': True,
                'url': url,
                'error': None,
            }

            for signal in project_signals:
                notification.observe(project, request.user, signal, signal)
            for release in project.releases.all():
                for signal in release_signals:
                    notification.observe(release, request.user, signal, signal)
            for resource in project.resources.all():
                for signal in resource_signals:
                    notification.observe(resource, request.user, signal, signal)

        except WatchException, e:
            return json_error(e.message, result)
    return json_result(result)
