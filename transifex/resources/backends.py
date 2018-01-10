# -*- coding: utf-8 -*-

"""
Various backend commands for resource models.

These are used by views and the API.
"""

from itertools import ifilter
from django.utils.translation import ugettext as _
from django.db import IntegrityError, DatabaseError
from transifex.txcommon.log import logger
from transifex.resources.models import Resource
from transifex.resources.formats.exceptions import FormatError
from transifex.resources.formats.registry import registry
from transifex.resources.formats.compilation import Mode
from transifex.resources.formats.utils.decorators import need_language


class BackendError(Exception):
    pass


class ResourceBackendError(BackendError):
    pass


class FormatsBackendError(BackendError):
    pass


class ResourceBackend(object):
    """Backend for resources.

    This class handles creating new resources.
    """

    def create(self, project, slug, name, method, source_language,
               content, user=None, extra_data={}):
        """Create a new resource.

        Any extra arguments will be passed to the Resource initialization
        method as is.

        There is no transaction used. The caller is supposed to handle this.

        Args:
            project: A Project instance which the resource will belong to.
            slug: The slug of the resource.
            name: The name of the resource.
            method: The i18n method of theresource.
            source_language: A Language instance of the source language set.
            content: The content of the resource's source file.
            user: The user that creates the resource.
            extra_data: Any extra info for the Resource constructor.
        Returns:
            A two-elements tuple. The first element is the number of added
            strings and the second the number of updated strings.
        """
        # save resource
        try:
            r = Resource(
                project=project, source_language=source_language,
                slug=slug, name=name
            )
            r.i18n_method = method
            r.full_clean()
            for key in ifilter(lambda k: k != "content", extra_data.iterkeys()):
                setattr(r, key, extra_data[key])
        except Exception, e:
            logger.warning(
                "Error while creating resource %s for project %s: %s" % (
                    slug, project.slug, e
                ), exc_info=True
            )
            raise ResourceBackendError("Invalid arguments given: %s" % e)
        try:
            r.save()
        except IntegrityError, e:
            logger.warning("Error creating resource %s: %s" % (r, e))
            raise ResourceBackendError("Error saving resource: %s" % e)
        except DatabaseError, e:
            msg = _("Error creating resource: %s")
            logger.warning(msg % e)
            raise ResourceBackendError(msg % e)
        # save source entities
        try:
            fb = FormatsBackend(r, source_language, user)
        except AttributeError, e:
            raise ResourceBackendError(_(
                "The content type of the request is not valid."
            ))
        try:
            return fb.import_source(
                content, filename=extra_data.get('filename')
            )
        except FormatsBackendError, e:
            raise ResourceBackendError(unicode(e))
        except Exception, e:
            logger.error(
                "Unexamined exception raised: %s" % e, exc_info=True
            )
            raise ResourceBackendError(unicode(e))


class FormatsBackend(object):
    """Backend for formats operations."""

    def __init__(self, resource, language, user=None):
        """Initializer.

        Args:
            resource: The resource the translations will belong to.
            language: The language of the translation.
        """
        self.resource = resource
        self.language = language
        self.user = user

    def import_source(self, content, filename=None):
        """Parse some content which is of a particular i18n type and save
        it to the database.

        Args:
            content: The content to parse.
            filename: The filename of the uploaded content (if any).
        Returns:
            A two-element tuple (pair). The first element is the number of
            strings added and the second one is the number of those updated.
        """
        if self.language is None:
            msg = _("No language specified, when importing source file.")
            logger.error(msg)
            raise FormatsBackendError(msg)
        handler = self._get_handler(
            self.resource, self.language, filename=filename
        )
        if handler is None:
            msg = "Files of type %s are not supported."
            logger.error(msg % self.resource.i18n_method)
            raise FormatsBackendError(msg % self.resource.i18n_method)
        return self._import_content(handler, content, True)

    @need_language
    def import_translation(self, content):
        """Parse a translation file for a resource.

        Args:
            content: The content to parse.
        Returns:
            A two element tuple(pair). The first element is the number of
            strings added and the second one is the number of those upadted.
        """
        handler = self._get_handler(self.resource, self.language)
        if handler is None:
            msg = "Files of type %s are not supported."
            logger.error(msg % self.resource.i18n_method)
            raise FormatsBackendError(msg % self.resource.i18n_method)
        return self._import_content(handler, content, False)

    def _get_handler(self, resource, language, filename=None):
        """Get the appropriate hanlder for the resource."""
        return registry.appropriate_handler(
            resource, language, filename=filename
        )

    def _import_content(self, handler, content, is_source):
        """Import content to the database.

        Args:
            content: The content to save.
            is_source: A flag to indicate a source or a translation file.
        Returns:
            A two element tuple(pair). The first element is the number of
            strings added and the second one is the number of those upadted.
        """
        try:
            handler.bind_resource(self.resource)
            handler.set_language(self.language)
            handler.bind_content(content)
            handler.parse_file(is_source=is_source)
            return handler.save2db(is_source=is_source, user=self.user)
        except FormatError, e:
            raise FormatsBackendError(unicode(e))

    def compile_translation(self, pseudo_type=None, mode=None):
        """Compile the translation for a resource in a specified language.

        There is some extra care for PO/POT resources. If there is no
        language specified, return a POT file, otherwise a PO.

        The argument ``mode`` allows for different handling of a
        translation, depending on whether it is for *viewing* or *translating
        it. This is necessary for formats that do not fallback to the source
        language in case of empty translations.

        Args:
            pseudo_type: The pseudo_type (if any).
            mode: The mode for compiling this translation.
        Returns:
            The compiled template.
        """
        if mode is None:
            mode = Mode.DEFAULT
        handler = registry.appropriate_handler(
            resource=self.resource, language=self.language
        )
        handler.bind_resource(self.resource)
        handler.set_language(self.language)
        content = handler.compile(pseudo=pseudo_type, mode=mode)
        return content if isinstance(content, basestring) else ''


def content_from_uploaded_file(files, encoding='UTF-8'):
    """Get the content of an uploaded file.

    We only return the content of the first file.

    Args:
        files: A dictionary with file objects. Probably, request.FILES.
        encoding: The encoding of the file.
    Returns:
        The content of the file as a unicode string.
    """
    files = files.values()
    if not files:
        return ''
    return files[0].read()


def filename_of_uploaded_file(files):
    """Get the filename of he uploaded file."""
    files = files.values()
    if not files:
        return None
    return files[0].name
