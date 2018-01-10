from django import template
from django.conf import settings
from django.db.models import get_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from actionlog.models import LogEntry
from actionlog.queues import redis_key_for_resource, redis_key_for_project, \
        redis_key_for_team, redis_key_for_user
from datastores.txredis import TxRedisMapper, redis_exception_handler


register = template.Library()

class LogNode(template.Node):
    def __init__(self, limit, varname, user=None, object=None, log_type='get_log'):
        self.limit, self.varname, self.object , self.user = (limit, varname,
                                                             object, user)
        self.log_type = log_type

    def __repr__(self):
        return "<GetLog Node>"

    def render(self, context):
        # XXX Should be fixed when ActionLog starts using Redis.
        # XXX __init_ is executed only once (before template compilation).
        # XXX NEEDS FIXING: get_public_log <limit>: limit is now useless.
        self.limit = 5

        if self.user is not None:
            user = template.Variable(self.user).resolve(context)
            if self.log_type and self.log_type == 'get_public_log':
                query = LogEntry.objects.by_user_and_public_projects(
                  user, self.limit)
            else:
                query = LogEntry.objects.by_user(user, self.limit)
        elif self.object is not None:
            obj = template.Variable(self.object).resolve(context)
            query = LogEntry.objects.by_object(obj)

        context[self.varname] = query
        return ''

class DoGetLog:
    """
    Populates a template variable with the log for the given criteria.

    Usage::

        {% get_log <limit> as <varname> [for object <context_var_containing_user_obj>] %}

    Examples::

        {% get_log 10 as action_log for_object foo %}
        {% get_log 10 as action_log for_user current_user %}
    """

    def __init__(self, tag_name):
        self.tag_name = tag_name

    def __call__(self, parser, token):
        tokens = token.contents.split()
        if len(tokens) < 4:
            raise template.TemplateSyntaxError, (
                "'%s' statements requires two arguments" % self.tag_name)
        if not tokens[1].isdigit():
            raise template.TemplateSyntaxError, (
                "First argument in '%s' must be an integer" % self.tag_name)
        if tokens[2] != 'as':
            raise template.TemplateSyntaxError, (
                "Second argument in '%s' must be 'as'" % self.tag_name)
        if len(tokens) > 4:
            if tokens[4] == 'for_user':
                return LogNode(limit=tokens[1], varname=tokens[3],
                               user=(len(tokens) > 5 and tokens[5] or None),
                               log_type=self.tag_name)
            elif tokens[4] == 'for_object':
                return LogNode(limit=tokens[1], varname=tokens[3],
                               object=(len(tokens) > 5 and tokens[5] or None),
                               log_type=self.tag_name)
            else:
                raise template.TemplateSyntaxError, (
                    "Fourth argument in '%s' must be either 'user' or "
                    "'object'" % self.tag_name)


class RecentLogNode(template.Node):
    """Node to get the most recent action logs for an item."""

    def __init__(self, model, obj, key_func, context_var):
        self.model = model
        self.obj = obj
        self.key_func = key_func
        self.context_var = context_var

    def render(self, context):
        obj = template.Variable(self.obj).resolve(context)
        redis_key = self.key_func(obj)
        events = self._action_logs_from_redis(redis_key)
        if events is None:
            Project = get_model('projects', 'Project')
            if isinstance(obj, Project) and obj.is_hub:
                ids = [obj.id, ]
                ids += obj.outsourcing.all().values_list('id', flat=True)
                events = LogEntry.objects.filter(
                    content_type=ContentType.objects.get_for_model(Project),
                    object_id__in=ids
                )[:5]
            else:
                events = LogEntry.objects.filter(
                    content_type=ContentType.objects.get_for_model(self.model),
                    object_id=obj.id
                )[:5]
        context[self.context_var] = events
        return ""

    @redis_exception_handler
    def _action_logs_from_redis(self, key):
        """Get the action logs for the key from redis."""
        if not settings.USE_REDIS:
            return None
        r = TxRedisMapper()
        return r.lrange(key, 0, -1)


def _parse_recent_log_args(token):
    """Parse the token of a recent log tags and return the useful values."""
    tokens = token.split_contents()
    if len(tokens) != 4:
        msg = "Wrong number of arguments for %s."
        raise template.TemplateSyntaxError(msg % tokens[0])
    elif tokens[2] != 'as':
        msg = "Wrong syntax for %s: third argument must be the keyword 'as'"
        raise template.TemplateSyntaxError(msg % tokens[0])
    return (tokens[1], tokens[3])


def recent_resource_log(parser, token):
    """Return the most recent logs of the specified resource."""
    (resource, context_var) = _parse_recent_log_args(token)
    Resource = get_model('resources', 'Resource')
    return RecentLogNode(Resource, resource, redis_key_for_resource, context_var)


def recent_project_log(parser, token):
    """Return the most recent logs of the specified resource."""
    (project, context_var) = _parse_recent_log_args(token)
    Project = get_model('projects', 'Project')
    return RecentLogNode(Project, project, redis_key_for_project, context_var)


def recent_team_log(parser, token):
    """Return the most recent logs of the specified team."""
    (team, context_var) = _parse_recent_log_args(token)
    Team = get_model('teams', 'Team')
    return RecentLogNode(Team, team, redis_key_for_team, context_var)


def recent_user_log(parser, token):
    """Return the most recent logs of the specified user."""
    (user, context_var) = _parse_recent_log_args(token)
    return RecentLogNode(User, user, redis_key_for_user, context_var)


register.tag('get_log', DoGetLog('get_log'))
register.tag('get_public_log', DoGetLog('get_public_log'))
register.tag('recent_resource_log', recent_resource_log)
register.tag('recent_project_log', recent_project_log)
register.tag('recent_team_log', recent_team_log)
register.tag('recent_user_log', recent_user_log)
