# -*- coding: utf-8 -*-
from django.conf import settings
from django.db.models import get_model
from django.db.models.signals import pre_save
from transifex.actionlog.models import action_logging
from transifex.projects.signals import post_resource_save, post_resource_delete
from transifex.txcommon import notifications as txnotification
from transifex.resources.utils import invalidate_template_cache
from transifex.teams.models import Team

RLStats = get_model('resources', 'RLStats')
Translation = get_model('resources', 'Translation')

def get_project_teams(project):
    if project.outsource:
        return project.outsource.team_set.all()
    else:
        return project.team_set.all()

def invalidate_stats_cache(resource, language, **kwargs):
    """
    Invalidate template caches and handle the updating of the persistent
    stats.
    """

    is_source = False
    if not language or language == resource.source_language:
        is_source = True
        language = resource.source_language

    team_languages = get_project_teams(resource.project).values_list(
            'language', flat=True)

    if not is_source:
        # Get or create new RLStat object
        rl, created = RLStats.objects.get_or_create(resource=resource,
            language=language)
        rl.update( kwargs['user'] if kwargs.has_key('user') else None)
        # Check to see if the lang has zero translations and is not a team
        # lang. If yes, delete RLStats object
        if rl.translated == 0 and rl.language.id not in\
          team_languages:
            rl.delete()
    else:
        rl, created = RLStats.objects.get_or_create(resource=resource,
            language=language)
        # Source file was updated. Update all language statistics
        stats = RLStats.objects.filter(resource=resource)
        for s in stats:
            s.update(kwargs['user'] if kwargs.has_key('user') else None)
            if s.translated == 0 and s.language.id not in\
              team_languages:
                s.delete()

        # Update resource wordcount and total entities
        resource.update_total_entities(save=False)
        resource.update_wordcount(save=True)

    invalidate_object_templates(resource, language, **kwargs)

def invalidate_object_templates(resource, language, **kwargs):
    """
    Invalidate all template level caches related to a specific object
    """

    if language == resource.source_language:
        langs = resource.available_languages
    else:
        langs = [language]

    # Template lvl cache for resource details
    invalidate_template_cache("resource_details",
        resource.project.slug, resource.slug)

    invalidate_template_cache("project_resource_details",
        resource.project.slug, resource.slug)

    # Number of source strings in resource
    for lang in langs:
        invalidate_template_cache("team_details",
            resource.project.slug, lang.code, resource.id)

        for rel in resource.project.releases.all():
            # Template lvl cache for release details
            invalidate_template_cache("release_details",
                rel.id, lang.id)

        # Template lvl cache for resource details
        invalidate_template_cache("resource_details_lang",
            resource.project.slug, resource.slug,
             lang.code)

def on_resource_save(sender, instance, created, user, **kwargs):
    """
    Called on resource post save and passes a user object in addition to the
    saved instance. Used for logging the create/update of a resource.
    """
    # ActionLog
    context = {'resource': instance,
               'sender': user}
    object_list = [instance.project, instance]
    if created:
        nt = 'project_resource_added'
        action_logging(user, object_list, nt, context=context)
    else:
        nt = 'project_resource_changed'
        action_logging(user, object_list, nt, context=context)

def on_resource_delete(sender, instance, user, **kwargs):
    """
    Called on resource post delete to file an action log for this action.
    Passes a user object along with the deleted instance for use in the logging
    mechanism.
    """
    # ActionLog
    context = {'resource': instance,
               'sender': user}
    object_list = [instance.project, instance]
    nt = 'project_resource_deleted'
    action_logging(user, object_list, nt, context=context)
    if settings.ENABLE_NOTICES:
        txnotification.send_observation_notices_for(instance.project,
                signal=nt, extra_context=context)

# Resource signal handlers for logging
post_resource_save.connect(on_resource_save)
post_resource_delete.connect(on_resource_delete)
