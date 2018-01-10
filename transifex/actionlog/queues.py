# -*- coding: utf-8 -*-

"""
Redis related stuff for action logs.
"""

from django.db.models import get_model
from django.utils.encoding import force_unicode
from django.contrib.auth.models import User
from transifex.txcommon.log import logger
from datastores.txredis import TxRedisMapper, redis_exception_handler


def redis_key_for_resource(resource):
    return 'resource:history:%s:%s' % (resource.project_id, resource.slug)


def redis_key_for_project(project):
    return 'project:history:%s' % project.slug


def redis_key_for_team(team):
    return 'team:history:%s:%s' % (team.project_id, team.language_id)


def redis_key_for_user(user):
    return 'user:history:%s' % user.id


@redis_exception_handler
def log_to_queues(o, user, action_time, action_type, message):
    """Log actions to redis' queues."""
    Project = get_model('projects', 'Project')
    Resource = get_model('resources', 'Resource')
    Team = get_model('teams', 'Team')
    _log_to_user_history(user, action_time, action_type, message)
    if isinstance(o, Project):
        _log_to_recent_project_actions(o, user.id, action_time, message)
        _log_to_project_history(o, action_time, action_type, message)
    elif isinstance(o, Resource):
        _log_to_resource_history(o, action_time, action_type, message)
    elif isinstance(o, Team):
        _log_to_team_history(o, action_time, action_type, message)

def _log_to_recent_project_actions(p, user_id, action_time, message):
    """Log actions that refer to projects to a queue of most recent actions.

    We use redis' list for that. We skip actions that refer to private projects.
    """
    Project = get_model('projects', 'Project')
    if p.private:
        return
    private_slugs = Project.objects.filter(
        private=True
    ).values_list('slug', flat=True)
    for slug in private_slugs:
        if ('/projects/p/%s/' % slug) in message:
            return

    key = 'event_feed'
    data = {
        'name': force_unicode(p)[:200],
        'user_id': user_id,
        'action_time': action_time,
        'message': message
    }
    r = TxRedisMapper()
    r.lpush(key, data=data)
    r.ltrim(key, 0, 11)


@redis_exception_handler
def _log_to_project_history(project, action_time, action_type, message):
    """Log a message to a project's history queue."""
    Project = get_model('projects', 'Project')
    key = redis_key_for_project(project)
    data = {
        'action_time': action_time,
        'message': message,
        'action_type': action_type,
    }
    r = TxRedisMapper()
    r.lpush(key, data=data)
    r.ltrim(key, 0, 4)

    # Store logs in hubs, too
    if project.outsource:
        _log_to_project_history(
            project.outsource, action_time, action_type, message
        )


@redis_exception_handler
def _log_to_resource_history(resource, action_time, action_type, message):
    """Log a message to a resource's history queue."""
    Resource = get_model('resources', 'Resource')
    key = redis_key_for_resource(resource)
    data = {
        'action_time': action_time,
        'message': message,
        'action_type': action_type,
    }
    r = TxRedisMapper()
    r.lpush(key, data=data)
    r.ltrim(key, 0, 4)


@redis_exception_handler
def _log_to_team_history(team, action_time, action_type, message):
    """Log a message to a team's history queue."""
    Resource = get_model('teams', 'Team')
    key = redis_key_for_team(team)
    data = {
        'action_time': action_time,
        'message': message,
        'action_type': action_type,
    }
    r = TxRedisMapper()
    r.lpush(key, data=data)
    r.ltrim(key, 0, 4)


@redis_exception_handler
def _log_to_user_history(user, action_time, action_type, message):
    """Log a message to a user's history queue."""
    key = redis_key_for_user(user)
    data = {
        'action_time': action_time,
        'message': message,
        'action_type': action_type,
        'user': user.username
    }
    r = TxRedisMapper()
    r.lpush(key, data=data)
    r.ltrim(key, 0, 11)
