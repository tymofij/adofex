from __future__ import absolute_import
import datetime
from django.db import models
from django.db.models import get_model
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_unicode, force_unicode
from django.template import loader, Context, TemplateDoesNotExist
from django.utils.translation import get_language, activate
from notification.models import NoticeType
from transifex.txcommon.log import logger
from .queues import log_to_queues

def _get_formatted_message(label, context):
    """
    Return a message that is a rendered template with the given context using
    the default language of the system.
    """
    current_language = get_language()

    # Setting the environment to the default language
    activate(settings.LANGUAGE_CODE)

    c = Context(context)
    template = 'notification/%s/notice.html' % label
    try:
        msg = loader.get_template(template).render(c)
    except TemplateDoesNotExist:
        logger.error("Template '%s' doesn't exist." % template)
        msg = None

    # Reset environment to original language
    activate(current_language)

    return msg

def _user_counting(query):
    """
    Get a LogEntry queryset and return a list of dictionaries with the
    counting of times that the users appeared on the queryset.

    Example of the resultant dictionary:
    [{'user__username': u'editor', 'number': 5},
    {'user__username': u'guest', 'number': 1}]
    """
    query_result = query.values('user__username').annotate(
        number=models.Count('user')).order_by('-number')

    # Rename key from 'user__username' to 'username'
    result=[]
    for entry in query_result:
        result.append({'username': entry['user__username'],
                       'number': entry['number']})
    return result

def _distinct_action_time(query, limit=None):
    """
    Distinct rows by the 'action_time' field, keeping in the query only the
    entry with the highest 'id' for the related set of entries with equal
    'action_time'.

    If 'limit' is set, the function  will return the 'limit'-most-recent
    actionlogs.

    Example:

        For the following query set:

            id |          action_time
            ----+----------------------------
            1 | 2010-03-11 10:55:26.32941-03
            2 | 2010-03-11 10:55:26.32941-03
            3 | 2010-03-11 13:48:22.202596-09
            4 | 2010-03-11 13:48:53.505697-03
            5 | 2010-03-11 13:48:53.505697-03
            6 | 2010-03-11 13:51:09.013079-05
            7 | 2010-03-11 13:51:09.013079-05
            8 | 2010-03-11 13:51:09.013079-05

        After passing through this function the query will be:

            id |          action_time
            ----+----------------------------
            2 | 2010-03-11 10:55:26.32941-03
            3 | 2010-03-11 13:48:22.202596-09
            5 | 2010-03-11 13:48:53.505697-03
            8 | 2010-03-11 13:51:09.013079-05

        Rows with the same 'action_time' are eliminated, keeping the one with
        highest 'id'.
    """
    pks = query.defer('object_id', 'content_type').distinct()
    if limit:
        pks = pks.order_by('-id')[:limit]
    else:
        # For some reason, when using defer() the Meta ordering
        # is not respected so we have to set it explicitly.
        pks = pks.order_by('-action_time')
    return pks.select_related('user')

class LogEntryManager(models.Manager):
    def by_object(self, obj, limit=None):
        """Return LogEntries for a related object."""
        ctype = ContentType.objects.get_for_model(obj)
        q = self.filter(content_type__pk=ctype.pk, object_id=obj.pk)
        return _distinct_action_time(q, limit)

    def by_user(self, user, limit=None):
        """Return LogEntries for a specific user."""
        q = self.filter(user__pk__exact=user.pk)
        return _distinct_action_time(q, limit)

    def by_object_last_week(self, obj):
        """Return LogEntries of the related object for the last week."""
        last_week_date = datetime.datetime.today() - datetime.timedelta(days=7)
        ctype = ContentType.objects.get_for_model(obj)
        return self.filter(content_type__pk=ctype.pk, object_id=obj.pk,
            action_time__gt=last_week_date)

    def by_user_and_public_projects(self, user, limit=None):
        """
        Return LogEntries for a specific user and his actions on public projects.
        """
        # Avoiding circular import troubles. get_model didn't make it.
        from transifex.projects.models import Project
        ctype = ContentType.objects.get(model='project')
        q = self.filter(user__pk__exact=user.pk, content_type=ctype,
                object_id__in=Project.objects.filter(private=False))
        return _distinct_action_time(q, limit)

    def for_projects_by_user(self, user):
        """Return project LogEntries for a related user."""
        ctype = ContentType.objects.get(model='project')
        return self.filter(user__pk__exact=user.pk, content_type__pk=ctype.pk)

    def top_submitters_by_project_content_type(self, number=10):
        """
        Return a list of dicts with the ordered top submitters for the
        entries of the 'project' content type.
        """
        return self.top_submitters_by_content_type('projects.project', number)

    def top_submitters_by_team_content_type(self, number=10):
        """
        Return a list of dicts with the ordered top submitters for the
        entries of the 'team' content type.
        """
        return self.top_submitters_by_content_type('teams.team', number)

    def top_submitters_by_language_content_type(self, number=10):
        """
        Return a list of dicts with the ordered top submitters for the
        entries of the 'language' content type.
        """
        return self.top_submitters_by_content_type('languages.language', number)

class LogEntry(models.Model):
    """A Entry in an object's log."""
    user = models.ForeignKey(User, verbose_name=_('User'), blank=True,
        null=True, related_name="actionlogs")

    object_id = models.IntegerField(blank=True, null=True, db_index=True)
    content_type = models.ForeignKey(ContentType, blank=True, null=True,
                                     related_name="actionlogs")

    object = generic.GenericForeignKey('content_type', 'object_id')

    action_type = models.ForeignKey(NoticeType, verbose_name=_('Action type'))
    action_time = models.DateTimeField(_('Action time'), db_index=True)
    object_name = models.CharField(blank=True, max_length=200)
    message = models.TextField(blank=True, null=True)

    # Managers
    objects = LogEntryManager()

    class Meta:
        verbose_name = _('log entry')
        verbose_name_plural = _('log entries')
        ordering = ('-action_time',)

    def __unicode__(self):
        return u'%s.%s.%s' % (self.action_type, self.object_name, self.user)

    def __repr__(self):
        return smart_unicode("<LogEntry %d (%s)>" % (self.id,
                                                     self.action_type.label))

    def save(self, *args, **kwargs):
        """Save the object in the database."""
        if self.action_time is None:
           self.action_time = datetime.datetime.now()
        super(LogEntry, self).save(*args, **kwargs)

    def message_safe(self):
        """Return the message as HTML"""
        return self.message
    message_safe.allow_tags = True
    message_safe.admin_order_field = 'message'

    @property
    def action_type_short(self):
        """
        Return a shortened, generalized version of an action type.

        Useful for presenting an image signifying an action type. Example::
        >>> from notification.models import  NoticeType
        >>> nt = NoticeType(label='project_added')
        >>> zlog = LogEntry(action_type=nt)
        >>> nt
        <NoticeType: project_added>
        >>> zlog.action_type
        <NoticeType: project_added>
        >>> zlog.action_type_short
        'added'
        """
        return self.action_type.label.split('_')[-1]

def action_logging(user, object_list, action_type, message=None, context=None):
    """
    Add ActionLog using a set of parameters.

    user:
      The user that did the action.
    object_list:
      A list of objects that should be created the actionlog for.
    action_type:
      Label of a type of action from the NoticeType model.
    message:
      A message to be included at the actionlog. If no message is passed
      it will try do render a message using the notice.html from the
      notification application.
    context:
      To render the message using the notification files, sometimes it is
      necessary to pass some vars by using a context.

    Usage::

        al = 'project_added'
        context = {'project': object}
        action_logging(request.user, [object], al , context=context):
    """
    if not getattr(settings, 'ACTIONLOG_ENABLED', None):
        return

    if context is None:
        context = {}

    if message is None:
        message = _get_formatted_message(action_type, context)

    action_type_obj = NoticeType.objects.get(label=action_type)

    time = datetime.datetime.now()

    try:
        for object in object_list:
            l = LogEntry(
                    user_id = user.pk,
                    content_type = ContentType.objects.get_for_model(object),
                    object_id = object.pk,
                    object_name = force_unicode(object)[:200],
                    action_type = action_type_obj,
                    action_time = time,
                    message = message)
            l.save()
            if settings.USE_REDIS:
                log_to_queues(object, user, time, action_type_obj, message)
    except TypeError:
        raise TypeError("The 'object_list' parameter must be iterable")
