# -*- coding: utf-8 -*-
from datetime import datetime
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _
from django.conf import settings
from django.db.models.signals import post_save, pre_delete
from django.contrib.sites.models import Site
from django.contrib import messages
from notification  import models as notification
from transifex.resources.models import Resource
from transifex.resources.utils import invalidate_template_cache
from transifex.teams.models import Team
from transifex.txcommon.log import logger
from txcron.signals import cron_daily, cron_hourly
from transifex.projects.signals import pre_submit_translation, post_submit_translation
from lotte.signals import lotte_init, lotte_done
from models import Lock, LockError


# Resource presubmit signal handler
# Allow only owner of the lock to submit translations, otherwise throw Exception
def pre_handler(sender, resource=None, language=None, user=None,
    instance=None, **kwargs):

    if not resource or not language or not user:
        # Invalid situation
        return

    lock = Lock.objects.get_valid(resource, language)
    if not lock:
        # Lock doesn't exist
        return

    if lock.owner != user:
        # Lock exists and person who wants to upload is not owner of the lock
        raise PermissionDenied


# Resource postsubmit signal handler
# Update the lock if user checked the checkbox
def post_handler(sender, request=None, resource=None, language=None,
    user=None, instance=None, **kwargs):
    if 'lock_extend' in request.POST and request.POST['lock_extend']:
        if user:
            Lock.objects.create_update(resource, language, user).expires


def lotte_init_handler(sender, request, resources=None, language=None,
    **kwargs):
    user = request.user
    logger.debug("lock-addon: Started editing in Lotte")
    for resource in resources:
        try:
            lock = Lock.objects.create_update(resource, language, user)
            logger.debug("lock-addon: Lock acquired/extended: '%s'" % lock)
        except LockError, e:
            logger.debug("lock-addon: %s" % e.message)
            messages.error(request,
                           _("This translation is "
                           "locked by someone else."))


def lotte_done_handler(sender, request, resources=None, language=None,
    **kwargs):
    user = request.user
    logger.debug("lock-addon: Finished editing in Lotte")
    for resource in resources:
        lock = Lock.objects.get_valid(resource, language)
        if lock:
            try:
                lock.delete_by_user(user)
                logger.debug("lock-addon: Lock deleted: '%s'" % lock)
            except LockError, e:
                logger.debug("lock-addon: User '%s' sent translations to a "
                    "resource/language locked by someone else: %s" %
                    (user, e.message))


def expiration_notification(sender, **kwargs):
    """
    FIXME: Migrate it (txcron) to work with the String Level.
    """
    logger.debug("lock-addon: Sending expiration notifications...")
    if not settings.ENABLE_NOTICES:
        logger.debug("lock-addon: ENABLE_NOTICES is not enabled")
        return
    current_site = Site.objects.get_current()
    locks = Lock.objects.expiring()
    nt = 'project_resource_language_lock_expiring'
    for lock in locks:
        context = { 'resource': lock.rlstats.resource,
                    'language': lock.rlstats.language,
                    'project' : lock.rlstats.resource.project,
                    'user': lock.owner,
                    'expires': lock.expires,
                    'current_site' : current_site }
        logger.debug("lock-addon: Sending notification about lock: %s" % lock)
        notification.send_now([lock.owner,], nt, context)
        lock.notified = True
        lock.save()


def db_cleanup(sender, **kwargs):
    logger.debug("lock-addon: Looking for expired locks")
    locks = Lock.objects.expired()
    for lock in locks:
        logger.debug("lock-addon: Deleting lock: %s" % lock)
        lock.delete()


def invalidate_cache(sender, instance, created=True, **kwargs):
    """
    Invalidate caching on places related to the lock icon in the stats table
    row.
    """
    if created:
        logger.debug("lock-addon: Invalidating cache: %s" % instance)

        invalidate_template_cache('resource_details_lang',
            instance.rlstats.resource.project.slug,
            instance.rlstats.resource.slug,
            instance.rlstats.language.code)

        invalidate_template_cache('resource_details',
            instance.rlstats.resource.project.slug,
            instance.rlstats.resource.slug)

        invalidate_template_cache("team_details",
            instance.rlstats.resource.project.slug,
            instance.rlstats.language.code,
            instance.rlstats.resource.id
        )

def connect():
    pre_submit_translation.connect(pre_handler, sender=Resource)
    post_submit_translation.connect(post_handler, sender=Resource)
    lotte_init.connect(lotte_init_handler)
    lotte_done.connect(lotte_done_handler)
    cron_hourly.connect(db_cleanup)
    cron_hourly.connect(expiration_notification)
    post_save.connect(invalidate_cache, sender=Lock)
    pre_delete.connect(invalidate_cache, sender=Lock)
