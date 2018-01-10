from __future__ import absolute_import
import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import get_model, signals, Q
from django.utils.translation import ugettext_lazy as _

from notification import models as notification
from txcron import signals as txcron_signals

from transifex.resources.signals import post_save_translation
from transifex.resources.models import Resource, RLStats
from transifex.releases import RELEASE_ALL_DATA
from transifex.txcommon.log import logger
from .models import Release


def update_all_release(project):
    """
    Update all-resources release for the given project and also for the
    related project hub in case the project is outsourcing its access.
    """
    projects = [project,]
    if project.outsource:
        projects.append(project.outsource)

    for p in projects:
        resources = p.resources.all()
        if p.is_hub:
            resources |= Resource.objects.filter(project__outsource=p)

        if resources.count():
            rel, rel_created = p.releases.get_or_create(
                slug=RELEASE_ALL_DATA['slug'],
                defaults={'name': RELEASE_ALL_DATA['name'],
                        'description': RELEASE_ALL_DATA['description'],})
            rel.resources = resources

def release_all_push(sender, instance, **kwargs):
    """
    Append newly created resource to the 'all' release.

    Add newly created resources to the special release called 'All Resources',
    which contains all the resources for a project at all times. If it is the
    first create the release when the first resource is added to the project.

    Called every time a resource is created.
    """

    resource = instance
    created = kwargs['created']
    if created:
        update_all_release(resource.project)


def release_all_pop(sender, instance, **kwargs):
    """
    Remove newly deleted resource to the 'all' release.

    Remove newly deleted resources from the special release called
    'All Resources'. Delete the release when the last resource is added to it.

    Called every time a resource is deleted.
    """

    resource = instance
    if resource.project is None:
        # The whole project is being deleted, so postgresql will handle the
        # removal of relevant objects.
        return
    try:
        rel = resource.project.releases.get(slug=RELEASE_ALL_DATA['slug'])
    except Release.DoesNotExist:
        rel = None
    if rel and not rel.resources.count():
        rel.delete()


def notify_string_freeze(sender=None, instance=None, **kwargs):
    """
    Handler to notify people about string freeze of releases.
    """
    now = datetime.datetime.now()
    # 48hs before
    logger.debug("release: Sending notifications 48hs before entering the "
        "String Freeze period.")
    timestamp =  now + datetime.timedelta(hours=48)
    releases = Release.objects.filter(stringfreeze_date__lte=timestamp,
        notifications__before_stringfreeze=False)
    for release in releases:
        logger.debug("release: Sending notifications for '%s'." % release)
        project = release.project.outsource or release.project

        # List with project maintainers of the given release PLUS maintainers
        # of projects that outsource theirs team to the project of the release
        resource_ids = release.resources.all().values('id').query
        users = User.objects.filter(
            (Q(projects_maintaining__resources__in=resource_ids) &
                Q(projects_maintaining__outsource=project)) |
            Q(projects_maintaining=project)).distinct()

        # Notification
        context = {'project': release.project, 'release': release}
        if release.project != project:
            context.update({'parent_project': project})

        nt = "project_release_before_stringfreeze"
        #TODO: Add support for actionlog without a user author.
        #action_logging(None, [project, release], nt, context=context)
        if settings.ENABLE_NOTICES:
            notification.send(users, nt, context)

        release.notifications.before_stringfreeze=True
        release.notifications.save()

    # Exactly on time
    logger.debug("release: Sending notifications about being in String "
        "Freeze period.")
    releases = Release.objects.filter(stringfreeze_date__lte=now,
        notifications__in_stringfreeze=False)
    for release in releases:
        logger.debug("release: Sending notifications for '%s'." % release)
        project = release.project.outsource or release.project

        # List with project maintainers of the given release PLUS maintainers
        # of projects that outsource theirs team to the project of the release
        # PLUS team coordinators and team members
        resource_ids = release.resources.all().values('id').query
        users = User.objects.filter(
            (Q(projects_maintaining__resources__in=resource_ids) &
                Q(projects_maintaining__outsource=project)) |
            Q(projects_maintaining=project) |
            Q(team_coordinators__project=project) |
            Q(team_members__project=project)).distinct()

        # Notification
        context = {'project': release.project, 'release': release}
        if release.project != project:
            context.update({'parent_project': project})

        nt = "project_release_in_stringfreeze"
        #TODO: Add support for actionlog without a user author.
        #action_logging(None, [project, release], nt, context=context)
        if settings.ENABLE_NOTICES:
            notification.send(users, nt, context)

        release.notifications.in_stringfreeze=True
        release.notifications.save()


def notify_translation_deadline(sender=None, instance=None, **kwargs):
    """
    Handler to notify people about translation deadline of releases.
    """
    now = datetime.datetime.now()
    # 48hs before
    logger.debug("release: Sending notifications 48hs before hitting the "
        "Translation deadline date.")
    timestamp =  now + datetime.timedelta(hours=48)
    releases = Release.objects.filter(develfreeze_date__lte=timestamp,
        notifications__before_trans_deadline=False)
    for release in releases:
        logger.debug("release: Sending notifications for '%s'." % release)
        project = release.project.outsource or release.project

        # List with team coordinators and team members for the given project
        # release
        users = User.objects.filter(
            Q(team_coordinators__project=project) |
            Q(team_members__project=project)).distinct()

        # Notification
        context = {'project': release.project, 'release': release}
        if release.project != project:
            context.update({'parent_project': project})

        nt = "project_release_before_trans_deadline"
        #TODO: Add support for actionlog without a user author.
        #action_logging(None, [project, release], nt, context=context)
        if settings.ENABLE_NOTICES:
            notification.send(users, nt, context)

        release.notifications.before_trans_deadline=True
        release.notifications.save()

    # Exactly on time
    logger.debug("release: Sending notifications for Translation period being "
        "over.")
    releases = Release.objects.filter(develfreeze_date__lte=now,
        notifications__trans_deadline=False)
    for release in releases:
        logger.debug("release: Sending notifications for '%s'." % release)
        project = release.project.outsource or release.project

        # List with project maintainers of the given release PLUS maintainers
        # of projects that outsource theirs team to the project of the release
        # PLUS team coordinators and team members
        resource_ids = release.resources.all().values('id').query
        users = User.objects.filter(
            (Q(projects_maintaining__resources__in=resource_ids) &
                Q(projects_maintaining__outsource=project)) |
            Q(projects_maintaining=project) |
            Q(team_coordinators__project=project) |
            Q(team_members__project=project)).distinct()

        # Notification
        context = {'project': release.project, 'release': release}
        if release.project != project:
            context.update({'parent_project': project})

        nt = "project_release_hit_trans_deadline"
        #TODO: Add support for actionlog without a user author.
        #action_logging(None, [project, release], nt, context=context)
        if settings.ENABLE_NOTICES:
            notification.send(users, nt, context)

        release.notifications.trans_deadline=True
        release.notifications.save()


# TODO: Candidate for a celery task
def check_and_notify_string_freeze_breakage(sender, **kwargs):
    """
    Handler to notify people about string freeze breakage of releases.

    This happens whenever a resource source file changes in the string freeze
    period.
    """
    resource = kwargs.pop('resource')
    language = kwargs.pop('language')

    # Check it only for source languages
    if kwargs.pop('is_source'):
        logger.debug("release: Checking string freeze breakage.")
        # FIXME: Get timestamp from RLStats last_update field, but it depends
        # on some changes on formats/core.py. At this point the RLStats object
        # wasn't created yet.
        timestamp = datetime.datetime.now()
        project = resource.project.outsource or resource.project
        releases = Release.objects.filter(resources=resource, project=project,
            stringfreeze_date__lte=timestamp, develfreeze_date__gte=timestamp)
        for release in releases:
            logger.debug("release: Sending notifications about string "
                "freeze breakage for '%s'" % release)
            project = release.project.outsource or release.project

            # User list with project maintainers and team coordinators of the
            # given release PLUS maintainers of the project that the RLStats
            # object belongs to PLUS
            users = User.objects.filter(
                Q(projects_maintaining=resource.project) |
                Q(projects_maintaining=project) |
                Q(team_coordinators__project=project)).distinct()

            # Notification
            context = {'project': release.project, 'release': release,
                'resource': resource}
            if release.project != project:
                context.update({'parent_project': project})

            nt = "project_release_stringfreeze_breakage"
            #TODO: Add support for actionlog without a user author.
            #action_logging(None, [project, release], nt, context=context)
            if settings.ENABLE_NOTICES:
                notification.send(users, nt, context)


# Connect handlers to populate 'all' release (more info in handler docstrings):
signals.post_save.connect(release_all_push, sender=Resource)
signals.post_delete.connect(release_all_pop, sender=Resource)

# Connect handlers to notify people whenever the specific signals from txcron
# are raise.
label = settings.RELEASE_NOTIFICATION_CRON['notify_string_freeze']
getattr(txcron_signals, label).connect(notify_string_freeze)

label = settings.RELEASE_NOTIFICATION_CRON['notify_translation_deadline']
getattr(txcron_signals, label).connect(notify_translation_deadline)

# Connect handler for string freeze breakage to the RLStats post_save signal
post_save_translation.connect(check_and_notify_string_freeze_breakage)
