# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.db import transaction, DatabaseError, IntegrityError
from django.http import HttpResponse, HttpResponseServerError
from django.utils import simplejson
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import slugify

from piston.handler import BaseHandler
from piston.utils import rc, throttle, require_mime

from transifex.actionlog.models import action_logging
from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.projects.permissions import *
from transifex.projects.permissions.project import ProjectPermission
from transifex.projects.signals import post_submit_translation, post_resource_save
from transifex.resources.decorators import method_decorator
from transifex.resources.formats.registry import registry
from transifex.resources.handlers import get_project_teams
from transifex.resources.models import *
from transifex.teams.models import Team
from transifex.txcommon.log import logger
from transifex.txcommon.decorators import one_perm_required_or_403
from transifex.txcommon.utils import paginate
from transifex.api.utils import BAD_REQUEST
from uuid import uuid4

# Temporary
from transifex.txcommon import notifications as txnotification


class ProjectHandler(BaseHandler):
    """
    API handler for model Project.
    """
    allowed_methods = ('GET','POST','PUT','DELETE')
    details_fields = (
        'slug', 'name', 'description', 'long_description', 'homepage', 'feed',
        'created', 'anyone_submit', 'bug_tracker', 'trans_instructions',
        'tags', 'outsource', ('maintainers', ('username', )),
        ('owner', ('username', )), ('resources', ('slug', 'name', )),
        'teams', 'source_language_code',
    )
    default_fields = ('slug', 'name', 'description', 'source_language_code', )
    fields = default_fields
    allowed_fields = (
        'name', 'slug', 'description', 'long_description', 'private',
        'homepage', 'feed', 'anyone_submit', 'hidden', 'bug_tracker',
        'trans_instructions', 'tags', 'maintainers', 'outsource',
        'source_language_code',
    )
    exclude = ()

    @classmethod
    def source_language_code(cls, p):
        """Add the source language as a field."""
        return p.source_language.code

    @classmethod
    def teams(cls, p):
        """Show the language codes for which there are teams as list.

        Return an empty list in case there are no teams defined.
        """
        team_set = get_project_teams(p)
        return team_set.values_list('language__code', flat=True)

    def read(self, request, project_slug=None, api_version=1):
        """
        Get project details in json format
        """
        # Reset fields to default value
        ProjectHandler.fields = ProjectHandler.default_fields
        if "details" in request.GET.iterkeys():
            if project_slug is None:
                return rc.NOT_IMPLEMENTED
            ProjectHandler.fields = ProjectHandler.details_fields
        return self._read(request, project_slug)

    @require_mime('json')
    @method_decorator(one_perm_required_or_403(pr_project_add))
    def create(self, request, project_slug=None, api_version=1):
        """
        API call to create new projects via POST.
        """
        data = getattr(request, 'data', None)
        if project_slug is not None:
            return BAD_REQUEST("POSTing to this url is not allowed.")
        if data is None:
            return BAD_REQUEST(
                "At least parameters 'slug', 'name' and "
                "'source_language' are needed."
            )
        return self._create(request, data)

    @require_mime('json')
    @method_decorator(one_perm_required_or_403(pr_project_add_change,
        (Project, 'slug__exact', 'project_slug')))
    def update(self, request, project_slug, api_version=1):
        """
        API call to update project details via PUT.
        """
        if project_slug is None:
            return BAD_REQUEST("Project slug not specified.")
        data = request.data
        if data is None:
            return BAD_REQUEST("Empty request.")
        return self._update(request, project_slug, data)

    @method_decorator(one_perm_required_or_403(pr_project_delete,
        (Project, 'slug__exact', 'project_slug')))
    def delete(self, request, project_slug=None, api_version=1):
        """
        API call to delete projects via DELETE.
        """
        if project_slug is None:
            return BAD_REQUEST("Project slug not specified.")
        return self._delete(request, project_slug)

    def _read(self, request, project_slug):
        """
        Return a list of projects or the details for a specific project.
        """
        if project_slug is None:
            # Use pagination
            p = Project.objects.for_user(request.user)
            res, msg = paginate(
                p, request.GET.get('start'), request.GET.get('end')
            )
            if res is None:
                return BAD_REQUEST(msg)
            return res
        else:
            try:
                p = Project.objects.get(slug=project_slug)
                perm = ProjectPermission(request.user)
                if not perm.private(p):
                    return rc.FORBIDDEN
            except Project.DoesNotExist:
                return rc.NOT_FOUND
            return p

    def _create(self, request, data):
        """
        Create a new project.
        """
        mandatory_fields = ('slug', 'name', 'source_language_code', )
        msg = "Field '%s' is required to create a project."
        for field in mandatory_fields:
            if field not in data:
                return BAD_REQUEST(msg % field)
        if 'owner' in data:
            return BAD_REQUEST("Owner cannot be set explicitly.")

        try:
            self._check_fields(data.iterkeys())
        except AttributeError, e:
            return BAD_REQUEST("Field '%s' is not available." % e.message)

        # outsource and maintainers are ForeignKey
        outsource = data.pop('outsource', {})
        maintainers = data.pop('maintainers', {})

        lang = data.pop('source_language_code')
        try:
            source_language = Language.objects.by_code_or_alias(lang)
        except Language.DoesNotExist:
            return BAD_REQUEST("Language %s does not exist." % lang)

        try:
            p = Project(**data)
            p.source_language = source_language
        except Exception:
            return BAD_REQUEST("Invalid arguments given.")
        try:
            p.full_clean()
        except ValidationError, e:
            return BAD_REQUEST("%s" % e)
        try:
            p.save()
        except IntegrityError:
            return rc.DUPLICATE_ENTRY

        p.owner = request.user
        if outsource:
            try:
                outsource_project = Project.objects.get(slug=outsource)
            except Project.DoesNotExist:
                p.delete()
                return BAD_REQUEST("Project for outsource does not exist.")
            p.outsource = outsource_project

        if maintainers:
            for user in maintainers.split(','):
                try:
                    u = User.objects.get(username=user)
                except User.DoesNotExist:
                    p.delete()
                    return BAD_REQUEST("User %s does not exist." % user)
                p.maintainers.add(u)
        else:
            p.maintainers.add(p.owner)
        p.save()
        return rc.CREATED

    def _update(self, request, project_slug, data):
        try:
            self._check_fields(data.iterkeys(), extra_exclude=['slug'])
        except AttributeError, e:
            return BAD_REQUEST("Field '%s' is not available." % e)

        outsource = data.pop('outsource', {})
        maintainers = data.pop('maintainers', {})
        try:
            p = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            return BAD_REQUEST("Project not found")

        lang = data.pop('source_language_code', None)
        if lang is not None:
            try:
                source_language = Language.objects.by_code_or_alias(lang)
            except Language.DoesNotExist:
                return BAD_REQUEST('Specified source language does not exist.')
            if p.resources.count() == 0:
                p.source_language = source_language
            else:
                msg = (
                    "The project has resources. Changing its source "
                    "language is not allowed."
                )
                return BAD_REQUEST(msg)

        try:
            for key,value in data.items():
                setattr(p, key,value)

            # Outsourcing
            if outsource:
                if outsource == p.slug:
                    return BAD_REQUEST("Original and outsource projects are the same.")
                try:
                    outsource_project = Project.objects.get(slug=outsource)
                except Project.DoesNotExist:
                    return BAD_REQUEST("Project for outsource does not exist.")
                p.outsource = outsource_project

            # Handler m2m with maintainers
            if maintainers:
                # remove existing maintainers and add new ones
                p.maintainers.clear()
                for user in maintainers.split(','):
                    try:
                        p.maintainers.add(User.objects.get(username=user))
                    except User.DoesNotExist:
                        return BAD_REQUEST("User %s does not exist." % user)
            p.save()
        except Exception, e:
            return BAD_REQUEST("Error parsing request data: %s" % e)
        return rc.ALL_OK

    def _delete(self, request, project_slug):
        try:
            project = Project.objects.get(slug=project_slug)
        except Project.DoesNotExist:
            return rc.NOT_FOUND
        try:
            project.delete()
        except:
            return rc.INTERNAL_ERROR
        return rc.DELETED

    def _check_fields(self, fields, extra_exclude=[]):
        """
        Check if supplied fields are allowed to be given in a
        POST or PUT request.

        Args:
            fields: An iterable of fields to check.
            extra_exclude: A list of fields that should not be used.
        Raises:
            AttributeError, in case a field is not in the allowed fields
                or is in the ``extra_exclude`` list.
        """
        for field in fields:
            if field not in self.allowed_fields or field in extra_exclude:
                raise AttributeError(field)
