# -*- coding: utf-8 -*-
from django.conf import settings

from notification import models as notification

from lotte.signals import lotte_done
from transifex.projects.signals import post_submit_translation
from transifex.projects.signals import post_resource_save, \
        post_release_save
from transifex.txcommon import notifications as txnotification
from transifex.txcommon.log import logger

from models import TranslationWatch

release_signals = ['project_release_changed',]

resource_signals = ['project_resource_changed',]

def _notify_translationwatchers(resource, language):
    """
    Notify the watchers for a specific TranslationWatch
    """
    context = {
        'project': resource.project,
        'resource': resource,
        'language': language,
    }

    twatch = TranslationWatch.objects.get_or_create(resource=resource,
        language=language)[0]

    logger.debug("addon-watches: Sending notification for '%s'" % twatch)
    txnotification.send_observation_notices_for(twatch,
        signal='project_resource_translation_changed', extra_context=context)

def _notify_releasewatchers(project, release, signal):
    """
    Notify watchers of a release add/change
    """
    context = {'project': project,
               'release': release,
    }
    logger.debug("addon-watches: Sending notification for '%s'" % release)
    if signal == "project_release_added":
        observed_instance = project
    else:
        observed_instance = release
    txnotification.send_observation_notices_for(observed_instance,
            signal=signal, extra_context=context)

def _notify_resourcewatchers(project, resource, signal):
    """
    Notify watchers of a resource add/change
    """
    context = {'project': project,
               'resource': resource,
    }
    logger.debug("addon-watches: Sending notification for '%s'" % resource)
    if signal == 'project_resource_added':
        observed_instance = project
    else:
        observed_instance = resource
    txnotification.send_observation_notices_for(observed_instance,
            signal=signal, extra_context=context)

def post_release_save_handler(sender, instance, created, user, **kwargs):
    if settings.ENABLE_NOTICES:
        release = instance
        project = release.project
        users = [watch.user for watch in notification.ObservedItem.objects.filter(content_type__model='project', object_id = project.id, signal="project_changed").select_related('user')]
        for user in users:
            try:
                notification.ObservedItem.objects.get_for(release.project, user, "project_changed")
                if created:
                    for signal in release_signals:
                        try:
                            notification.ObservedItem.objects.get_for(release, user, signal)
                        except notification.ObservedItem.DoesNotExist:
                            notification.observe(release, user, signal, signal)
                    nt = "project_release_added"
                else:
                    nt = "project_release_changed"
                project = release.project
                _notify_releasewatchers(project, release, nt)
            except notification.ObservedItem.DoesNotExist, e:
                logger.debug("Watches: %s" % unicode(e))

def post_resource_save_handler(sender, instance, created, user, **kwargs):
    if settings.ENABLE_NOTICES:
        resource = instance
        project = resource.project
        users = [watch.user for watch in notification.ObservedItem.objects.filter(content_type__model='project', object_id = project.id, signal="project_changed").select_related('user')]
        for user in users:
            try:
                notification.ObservedItem.objects.get_for(resource.project, user, "project_changed")
                if created:
                    for signal in resource_signals:
                        try:
                            notification.ObservedItem.objects.get_for(resource, user, signal)
                        except notification.ObservedItem.DoesNotExist:
                            notification.observe(resource, user, signal, signal)
                    nt = "project_resource_added"
                else:
                    nt = "project_resource_changed"
                project = resource.project
                _notify_resourcewatchers(project, resource, nt)
            except notification.ObservedItem.DoesNotExist, e:
                logger.debug("Watches: %s" % unicode(e))

def lotte_done_handler(sender, request, resources, language, modified,
    **kwargs):
    if modified and settings.ENABLE_NOTICES:
        for resource in resources:
            _notify_translationwatchers(resource, language)


def post_submit_translation_handler(sender, request, resource, language,
    modified, **kwargs):
    if modified and settings.ENABLE_NOTICES:
        _notify_translationwatchers(resource, language)

def connect():
    lotte_done.connect(lotte_done_handler)
    post_submit_translation.connect(post_submit_translation_handler)
    post_release_save.connect(post_release_save_handler)
    post_resource_save.connect(post_resource_save_handler)
