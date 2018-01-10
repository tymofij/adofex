from celery.decorators import task
from notification import models as notification

from django.conf import settings
from django.db.models import get_model
from transifex.txcommon.log import logger
from transifex.txcommon import notifications as txnotification
from transifex.projects.signals import post_resource_save


#@task(name='tx_project_resource_full_reviewed', ignore_result=True, max_retries=3)
def check_and_notify_resource_full_reviewed(**kwargs):
    """
    Handler to notify maintainers about 100% reviewed translations.
    """
    rlstats = kwargs.pop('sender')
    if (settings.ENABLE_NOTICES and
        rlstats.resource.source_language != rlstats.language):

        logger.debug("resource: Checking if resource translation is fully "
            "reviewed: %s (%s)" % (rlstats.resource, rlstats.language.code))

        if rlstats.reviewed_perc == 100:
            logger.debug("resource: Resource translation is fully reviewed.")

            # Notification
            context = {
                'project': rlstats.resource.project,
                'resource': rlstats.resource,
                'language': rlstats.language,}
            nt = "project_resource_full_reviewed"

            notification.send(rlstats.resource.project.maintainers.all(),
                nt, context)


def _notify_all_on_source_change(resource, context):
    """
    Send notifications to everyone involved with a resource.

    Args:
        resource: The updated resource.
    """
    signal_name = 'project_resource_translation_changed'
    msg = "addon-watches: Sending notification for '%s'"
    TWatch = get_model('watches', 'TranslationWatch')

    for l in resource.available_languages:
        twatch = TWatch.objects.get_or_create(resource=resource, language=l)[0]
        logger.debug(msg % twatch)
        txnotification.send_observation_notices_for(
            twatch, signal=signal_name, extra_context=context
        )


@task(name='send_notices_on_importing_files', max_retries=3)
def send_notices_for_formats(signal, context):
    """
    Send notifications to watching users that a resource has been changed.

    Args:
        signal: The signal to send.
        context: The context of the signal.
    """
    resource = context['resource']
    project = context['project']
    language = context['language']

    txnotification.send_observation_notices_for(project, signal, context)
    if language == resource.source_language:
        _notify_all_on_source_change(resource, context)


@task(name='send_notices_on_resource_changed', max_retries=2)
def send_notices_for_resource_edited(resource, user):
    """
    Send notifications, when a resource has been edited.

    Args:
        resource: The resource that has been edited.
        user: The user that did the update.
    """
    post_resource_save.send(
        sender=None, instance=resource, created=False, user=user
    )
