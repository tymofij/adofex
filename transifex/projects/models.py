# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
from datetime import datetime
import tagging
from tagging.fields import TagField
from tagging_autocomplete.models import TagAutocompleteField
import markdown

from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.contenttypes import generic
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import validate_slug
from django.db import models, IntegrityError
from django.db.models import Sum
from django.db.models import permalink, get_model, Q
from django.dispatch import Signal
from django.forms import ModelForm
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType

from authority.models import Permission
from notification.models import ObservedItem
from userena.models import upload_to_mugshot
from easy_thumbnails.fields import ThumbnailerImageField

from transifex.actionlog.models import LogEntry
from transifex.txcommon.db.models import ChainerManager
from transifex.txcommon.log import log_model, logger
from transifex.languages.models import Language
from datastores import TxRedisMapper, redis_exception_handler
from .signals import project_created, project_deleted, \
        project_outsourced_changed
from .handlers import on_outsource_change

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["tagging_autocomplete.models.TagAutocompleteField"])

# Settings for the Project.logo field, based on the userena settings mugshot
# settings
PROJECT_LOGO_SETTINGS = {'size': (settings.PROJECT_LOGO_SIZE,
                                  settings.PROJECT_LOGO_SIZE),
                         'crop': settings.USERENA_MUGSHOT_CROP_TYPE}

class DefaultProjectQuerySet(models.query.QuerySet):
    """
    This is the default manager of the project model (assigned to objects field).
    """

    def watched_by(self, user):
        """
        Retrieve projects being watched by the specific user.
        """
        try:
            ct = ContentType.objects.get(name="project")
        except ContentType.DoesNotExist:
            pass
        observed_projects = [i[0] for i in list(set(ObservedItem.objects.filter(user=user, content_type=ct).values_list("object_id")))]
        watched_projects = []
        for object_id in observed_projects:
            try:
                watched_projects.append(Project.objects.get(id=object_id))
            except Project.DoesNotExist:
                pass
        return watched_projects

    def maintained_by(self,user):
        """
        Retrieve projects being maintained by the specific user.
        """
        return Project.objects.filter(maintainers__id=user.id)

    def translated_by(self, user):
        """
        Retrieve projects being translated by the specific user.

        The method returns all the projects in which user has been granted
        permission to submit translations.
        """
        try:
            ct = ContentType.objects.get(name="project")
        except ContentType.DoesNotExist:
            pass
        return Permission.objects.filter(user=user, content_type=ct, approved=True)

    def involved_with(self, user):
        """
        Returns all projects that the given user is involved in (as a project
        maintainer, team coordinator or team member).

        Includes private projects.
        """
        Team = get_model('teams', 'Team')
        return self.filter(
            Q(maintainers__in=[user]) |
            Q(team__in=Team.objects.for_user(user))
        ).distinct()

    def for_user(self, user):
        """
        Filter available projects based on the user doing the query. This
        checks permissions and filters out private projects that the user
        doesn't have access to.
        """
        projects = self
        if user in [None, AnonymousUser()]:
            projects = projects.filter(private=False)
        else:
            if not user.is_superuser:
                Team = get_model('teams', 'Team')
                projects = projects.exclude(
                    Q(private=True) & ~(Q(maintainers__in=[user]) |
                    Q(team__in=Team.objects.for_user(user)))).distinct()
        return projects

    def public(self):
        return self.filter(private=False)

    def private(self):
        return self.filter(private=True)


class PublicProjectManager(models.Manager):
    """
    Return a QuerySet of public projects.

    Usage: Projects.public.all()
    """

    def get_query_set(self):
        return super(PublicProjectManager, self).get_query_set().filter(private=False)

    def recent(self):
        return self.order_by('-created')

    def open_translations(self):
        #FIXME: This should look like this, more or less:
        #open_resources = Resource.objects.filter(accept_translations=True)
        #return self.filter(resource__in=open_resources).distinct()
        return self.all()


def validate_slug_not_in_blacklisted(value):
    blacklist = getattr(settings, "SUBDOMAIN_BLACKLIST", ())
    if value in blacklist:
        raise ValidationError("this slug is reverved")

class Project(models.Model):
    """
    A project is a group of translatable resources.
    """

    private = models.BooleanField(default=False, verbose_name=_('Private'),
        help_text=_('A private project is visible only by you and your team. '
                    'Moreover, private projects are limited according to billing '
                    'plans for the user account.'))
    slug = models.SlugField(_('Slug'), max_length=30, unique=True,
        validators=[validate_slug_not_in_blacklisted, validate_slug, ],
        help_text=_('A short label to be used in the URL, containing only '
                    'letters, numbers, underscores or hyphens.'))
    name = models.CharField(_('Name'), max_length=50,
        help_text=_('A short name or very short description.'))
    description = models.CharField(_('Description'), blank=False, max_length=255,
        help_text=_('A sentence or two describing the object.'))
    long_description = models.TextField(_('Long description'), blank=True,
        max_length=1000,
        help_text=_('A longer description (optional). Use Markdown syntax.'))
    homepage = models.URLField(_('Homepage'), blank=True, verify_exists=False)
    feed = models.CharField(_('Feed'), blank=True, max_length=255,
        help_text=_('An RSS feed with updates to the project.'))
    bug_tracker = models.URLField(_('Bug tracker'), blank=True,
        help_text=_('The URL for the bug and tickets tracking system '
                    '(Bugzilla, Trac, etc.)'))
    trans_instructions = models.URLField(_('Translator Instructions'), blank=True,
        help_text=_("A web page containing documentation or instructions for "
                    "translators, or localization tips for your community."))
    anyone_submit = models.BooleanField(_('Anyone can submit'),
        default=False, blank=False,
        help_text=_('Can anyone submit files to this project?'))

    hidden = models.BooleanField(_('Hidden'), default=False, editable=False,
        help_text=_('Hide this object from the list view?'))
    enabled = models.BooleanField(_('Enabled'),default=True, editable=False,
        help_text=_('Enable this object or disable its use?'))
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)

    tags = TagAutocompleteField(verbose_name=_('Tags'), blank=True, null=True)

    logo = ThumbnailerImageField(_('Logo'), blank=True, null=True,
        upload_to=upload_to_mugshot, resize_source=PROJECT_LOGO_SETTINGS,
        help_text=_('A logo image displayed for the project.'))

    # Relations
    maintainers = models.ManyToManyField(User, verbose_name=_('Maintainers'),
        related_name='projects_maintaining', blank=False, null=True)

    outsource = models.ForeignKey('Project', blank=True, null=True,
        verbose_name=_('Outsource project'), related_name="outsourcing",
        help_text=_('Project hub that owns the access control of this project.'))

    owner = models.ForeignKey(User, blank=True, null=True,
        verbose_name=_('Owner'), related_name='projects_owning',
        help_text=_('The user who owns this project.'))

    source_language = models.ForeignKey(
        Language, verbose_name=_('Source Language'),
        blank=False, null=False, db_index=False,
        help_text=_("The source language of this Resource.")
    )

    # Denormalized fields
    is_hub = models.BooleanField(_('Project Hub?'),
        default=False, blank=True,
        help_text=_('Is it a project hub that other regular projects can '
            'use to outsource teams to receive translations?'))

    # Normalized fields
    long_description_html = models.TextField(_('HTML Description'), blank=True,
        max_length=1000,
        help_text=_('Description in HTML.'), editable=False)

    # Reverse Relation for LogEntry GenericForeignkey
    # Allows to access LogEntry objects for a given project
    actionlogs = generic.GenericRelation(LogEntry,
        object_id_field="object_id", content_type_field="content_type")

    # Managers
    objects = ChainerManager(DefaultProjectQuerySet)
    public = PublicProjectManager()

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return repr(u'<Project: %s>' % self.name)

    class Meta:
        verbose_name = _('project')
        verbose_name_plural = _('projects')
        db_table  = 'projects_project'
        ordering  = ('name',)
        get_latest_by = 'created'

    def save(self, *args, **kwargs):
        """Save the object in the database."""
        long_desc = escape(self.long_description)
        self.long_description_html = markdown.markdown(long_desc)
        if self.id is None:
            is_new = True
        else:
            is_new = False
        super(Project, self).save(*args, **kwargs)
        if is_new:
            project_created.send(sender=self)

    def delete(self, *args, **kwargs):
        self.resources.all().delete()
        project_deleted.send(sender=self)
        super(Project, self).delete(*args, **kwargs)

    @permalink
    def get_absolute_url(self):
        return ('project_detail', None, { 'project_slug': self.slug })

    @property
    def hub_request(self):
        """
        Return a HubRequest object if a request to join a project hub exists.
        Otherwise it returns None.
        """
        try:
            return self.hub_requesting.all()[0]
        except IndexError:
            return None

    @property
    def wordcount(self):
        return self.resources.aggregate(Sum('wordcount'))['wordcount__sum'] or 0

    @property
    def num_languages(self):
        return Language.objects.filter(rlstats__resource__project=self).distinct().count()

    @property
    def max_hostable_wordcount(self):
        return self.num_languages * self.wordcount

    @property
    def entities(self):
        return self.resources.aggregate(Sum('total_entities'))['total_entities__sum'] or 0

    @property
    def team_members(self):
        """Return a queryset of all memebers of a project."""
        return User.objects.filter(
            Q(team_members__project=self) | Q(team_coordinators__project=self) |\
            Q(team_reviewers__project=self) | Q(projects_owning=self) |\
            Q(projects_maintaining=self)
        ).distinct()

    @property
    def team_member_count(self):
        return User.objects.filter(
            Q(team_members__project=self) | Q(team_coordinators__project=self) |\
            Q(projects_owning=self) | Q(projects_maintaining=self)
        ).distinct().count()

    def languages(self):
        """
        The languages this project's resources are being translated into
        excluding the source language, ordered by number of translations.
        """
        return Language.objects.filter(
            rlstats__resource__in=self.resources.all()
        ).exclude(code=self.source_language.code).order_by(
            '-rlstats__translated').distinct()

    def get_logo_url(self):
        """
        Returns the image containing the mugshot for the user.

        The mugshot can be a uploaded image or a Gravatar.

        :return:
            ``None`` when no default image is supplied by ``PROJECT_LOGO_DEFAULT``.
        """
        # First check for a uploaded logo image and if any return that.
        if self.logo:
            return self.logo.url
        # Check for a default image.
        elif getattr(settings, 'PROJECT_LOGO_DEFAULT', None):
            return os.path.join(settings.STATIC_URL, settings.PROJECT_LOGO_DEFAULT)
        else:
            return None

    def get_action_logs(self):
        """
        Return actionlog entries for the given project plus the actionlogs of
        the hub projects, in case it's a hub.
        """
        ids = [self.id]
        if self.is_hub:
            ids += self.outsourcing.all().values_list('id', flat=True)
        return LogEntry.objects.filter(
            content_type=ContentType.objects.get_for_model(Project),
            object_id__in=ids)


try:
    tagging.register(Project, tag_descriptor_attr='tagsobj')
except tagging.AlreadyRegistered, e:
    logger.debug('Tagging: %s' % str(e))

log_model(Project)


class HubRequest(models.Model):
    """
    Model to handle outsource requests of project to project hubs. A project
    only can have one request for a project hub and it can only be associated
    to a project hub once at a time.
    """
    project_hub = models.ForeignKey(Project, verbose_name=_('Project Hub'),
        blank=False, null=False, related_name="hub_requests",
        help_text=_("The project hub to outsource teams from."))

    project = models.ForeignKey(Project, verbose_name=_('Project'),
        unique=True, blank=False, null=False, related_name="hub_requesting",
        help_text=_("The project that wants to outsource teams from "
            "another project."))
    user = models.ForeignKey(User, verbose_name=_('User'),
        blank=False, null=False,
        help_text=_("The user who is requesting to join the project hub."))

    created = models.DateTimeField(auto_now_add=True, editable=False)

    def __unicode__(self):
        return u'%s.%s' % (self.project_hub.slug,
            self.project.slug)

    def __repr__(self):
        return '<HubRequest: %s.%s>' % (self.project_hub.slug,
            self.project.slug)

    class Meta:
        unique_together = ("project",)
        verbose_name = _('hub joining request')
        verbose_name_plural = _('hub joining requests')


# Connect to signals
project_outsourced_changed.connect(on_outsource_change)
