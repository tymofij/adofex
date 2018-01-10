# -*- coding: utf-8 -*-

"""
Handlers for the addon.
"""

import requests
from django.db.models import get_model
from django import forms
from django.utils.translation import ugettext_lazy as _
from transifex.txcommon.log import logger
from transifex.txcommon.validators import validate_http_url
from transifex.resources.signals import post_update_rlstats
from transifex.projects.signals import project_form_init, post_proj_save_m2m
from webhooks.models import WebHook


def visit_url(sender, **kwargs):
    """Visit the URL for the project.

    Send the slug of the project, the slug of the resource and the language
    of the translation as identifiers. Send the translation percentage
    as information.

    Args:
        sender: The rlstats object itself.
    Returns:
        True of False for success (or not).
    """
    # TODO make it a celery task
    # TODO increase the timeout in celery

    stats = sender
    resource = stats.resource
    project = resource.project
    language = stats.language

    if 'post_function' in kwargs:
        post_function = kwargs['post_function']
    else:
        post_function = requests.post

    hooks = WebHook.objects.filter(project=project)
    if not hooks:
        logger.debug("Project %s has no web hooks" % project.slug)
        return

    event_info = {
        'project': project.slug,
        'resource': resource.slug,
        'language': language.code,
        'percent': stats.translated_perc,
    }
    logger.debug(
        "POST data for %s: %s" % (stats.resource.project.slug, event_info)
    )

    for hook in hooks:
        res = post_function(hook.url,
          data=event_info, allow_redirects=False, timeout=2.0)

        if res.ok:
            logger.debug("POST for project %s successful." % project)
        else:
            msg = "Error visiting webhook %s: HTTP code is %s" % (
              hook, res.status_code)
            logger.error(msg)


def add_web_hook_field(sender, **kwargs):
    """Add the field for a web hook to the project edit form."""
    form = kwargs['form']
    project =form.instance

    try:
        url = WebHook.objects.get(project=project, kind='p').url
    except WebHook.DoesNotExist:
        url = ''

    form.fields['webhook'] = forms.URLField(
        verify_exists=False, required=False, initial=url,
        label=_("Web hook URL"), validators=[validate_http_url, ],
        help_text=_("You can specify a URL which Transifex will visit whenever "
                    "a translation of a resource of the project is changed.")
    )


def save_web_hook(sender, **kwargs):
    """Save a web hook, after saving a project (if defined)."""
    project = kwargs['instance']
    form = kwargs['form']
    url = form.cleaned_data['webhook']
    if url:
        try:
            hook, created = WebHook.objects.get_or_create(
                project=project, kind='p', defaults={'url': url}
            )
            if not created:
                hook.url = url
                hook.save()
        except Exception, e:
            logger.error("Error saving hook for project %s: %s" % (project, e))


def connect():
    # TODO catch other cases, too (eg project.pre_delete
    post_update_rlstats.connect(visit_url)
    project_form_init.connect(add_web_hook_field)
    post_proj_save_m2m.connect(save_web_hook)
