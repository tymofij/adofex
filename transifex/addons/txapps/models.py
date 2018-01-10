# -*- coding: utf-8 -*-

"""
Models for txapps support.
"""

from django.db import models
from django.utils.translation import ugettext_lazy as _
from picklefield import PickledObjectField
from transifex.txcommon.validators import validate_http_url


class TxAppManager(models.Manager):
    """Manager for the tx apps."""

    def enable_app_for_project(self, txapp, project):
        """Enale an app for a project.

        Args:
            txapp: A TxApp.
            project: A project.
        """
        txapp.projects.add(project)

    def disable_app_for_project(self, txapp, project):
        """Disable an app for a project.

        Args:
            txapp: A TxApp.
            project: A project.
        """
        txapp.projects.remove(project)



class TxApp(models.Model):
    """A tx app."""

    slug = models.SlugField(
        _("Slug"), unique=True, max_length=30, help_text=_(
            "A short label to be used in the URL, containing only "
            "letters, numbers, underscores or hyphens."
        )
    )
    name = models.CharField(
        _("Name"), max_length=50, help_text=_("A short name.")
    )
    description = models.CharField(
        _("Description"), max_length=200,
        help_text=_("A small description for the app.")
    )
    url = models.URLField(
        _("URL"), unique=True, verify_exists=False, validators=[validate_http_url, ],
        help_text=_("The URL where the app is hosted.")
    )
    team_allowed = PickledObjectField(
        _("Allowed URLs"), null=True,
        help_text=_("URLs allowed to be accessed by team members.")
    )

    # foreign keys
    projects = models.ManyToManyField(
        'projects.project', related_name='apps',
        verbose_name=_("Projects"), blank=True,
        help_text=_("The projects that have enabled this app.")
    )

    objects = TxAppManager()

    def __unicode__(self):
        return u"<TxApp %s>" % self.slug

    def save(self, **kwargs):
        """Save the object.

        Make sure the URL does not end with a slash.
        """
        if self.url.endswith('/'):
            self.url = self.url[:-1]
        super(TxApp, self).save(**kwargs)

    def access_is_allowed(self, user, project, path):
        """Return True, if the user is allowed to access the path specified.

        Args:
            user: The user who wants to access the path.
            project: The project accessed.
            path: The path to access.
        Returns:
            Trueo or False.
        """
        # most common cases first
        if user == project.owner:
            return True
        if self.team_allowed is None:
            return False
        if path in self.team_allowed and user in project.team_members:
            return True
        return False
