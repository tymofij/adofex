# -*- coding: utf-8 -*-

from __future__ import absolute_import
import codecs, copy, os, re
import gc
from django.utils import simplejson as json
from django.conf import settings
from django.db import transaction
from django.db.models import get_model
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext as _
from transifex.txcommon.log import logger
from transifex.languages.models import Language
from transifex.projects.permissions.project import ProjectPermission
from suggestions.models import Suggestion
from suggestions.formats import ContentSuggestionFormat
from transifex.actionlog.models import action_logging
from transifex.resources.handlers import invalidate_stats_cache
from transifex.resources.formats.exceptions import FormatError, ParseError, \
        CompileError
from .compilation import Compiler, NormalDecoratorBuilder, \
        PseudoDecoratorBuilder, AllTranslationsBuilder, \
        SourceTranslationsBuilder, ReviewedTranslationsBuilder, Mode
from transifex.resources.formats.pseudo import PseudoTypeMixin
from transifex.resources.formats.utils.decorators import *
from transifex.resources.signals import post_save_translation
from transifex.resources.formats.resource_collections import StringSet, \
        GenericTranslation, SourceEntityCollection, TranslationCollection
from transifex.teams.models import Team
from transifex.resources.tasks import send_notices_for_formats


"""
STRICT flag is used to switch between two parsing modes:
  True - minor bugs in source files are treated fatal
    In case of Qt TS handler this means that buggy location elements will
    raise exceptions.
  False - if we get all necessary information from source files
    we will pass
"""
STRICT=False

Resource = get_model('resources', 'Resource')
Translation = get_model('resources', 'Translation')
SourceEntity = get_model('resources', 'SourceEntity')
Template = get_model('resources', 'Template')


class CustomSerializer(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, GenericTranslation):
            d = {
                'source_entity' : obj.source_entity,
                'translation' : obj.translation,
            }
            if obj.occurrences:
                d['occurrences'] = obj.occurrences
            if obj.comments:
                d['comments'] = obj.comments
            if obj.context:
                d['context'] = obj.context
            if obj.rule:
                d['rule'] = obj.rule
            if obj.pluralized:
                d['pluralized'] = obj.pluralized

            return d

        if isinstance(obj, StringSet):
            return {
                #'filename' : obj.filename,
                'target_language' : obj.target_language,
                'strings' : obj.strings,
            }


class Handler(object):
    """Base class for writing file handlers for all the I18N types."""
    default_encoding = "UTF-8"
    method_name = None
    format_encoding = "UTF-8"

    HandlerParseError = ParseError
    HandlerCompileError = CompileError

    SuggestionFormat = ContentSuggestionFormat
    CompilerClass = Compiler

    linesep = '\n'

    @classmethod
    def accepts(cls, i18n_type):
        """Accept only files that have the correct type specified."""
        return i18n_type == cls.method_name

    def __init__(self, filename=None, resource=None, language=None, content=None):
        """
        Initialize a formats handler.
        """
        # Input filename for associated translation file
        self.filename = filename
        # The content of the translation file
        self.content = self._get_content(filename=filename, content=content)
        self.stringset = None # Stringset to extract entries from files

        self.resource = None # Associated resource
        self.language = None # Resource's source language

        self.template = None # Var to store raw template
        self.compiled_template = None # Var to store output of compile() method

        if resource:
            self.resource = resource
            self.language = resource.source_language
        if language:
            self.language = language

        self.key_dict = {}

        # Hold warning messages from the parser in a sorted dict way to avoid
        # duplicated messages and keep them in the order they were added.
        self.warning_messages = SortedDict()

    def _set_warning_message(self, key, message):
        """Set a warning message to the parser if it doesn't exist already."""
        if key not in self.warning_messages.keys():
            self.warning_messages[key] = message

    def _check_content(self, content):
        """
        Perform the actual check of the content.

        """
        # FIXME Make all code use return values instead of exceptions
        # FIXME Needs to deprecate API v1
        return (True, None)

    def is_content_valid(self, content=None):
        """Check whether the content is valid for the format.

        A subclass needs to override the _check_content method
        to customize the check.

        Args:
            content: The content to check.
        Returns:
            A tuple with two elements. The first is a boolean, a flag whether
            the content is valid. The second is the error message in case of
            errors.
        """
        if content is None:
            content = self.content
        return self._check_content(content)

    ####################
    # Helper functions #
    ####################

    def _get_content(self, filename=None, content=None):
        """Read the content of the specified file.

        Return either the `content` or the content of the file.
        """
        if content is not None:
            if isinstance(content, str):
                try:
                    return content.decode(self.format_encoding)
                except UnicodeDecodeError, e:
                    raise FormatError(unicode(e))
            else:
                return content
        if filename is None:
            return None
        return self._get_content_from_file(filename, self.format_encoding)

    def _get_content_from_file(self, filename, encoding):
        """Return the content of a file encoded with ``encoding``.

        Args:
            filename: The name of the file.
            encoding: THe encoding to use to open the file.
        Returns:
            The content of the file as a unicode string.
        """
        f = codecs.open(filename, 'r', encoding=encoding)
        try:
            return f.read()
        except IOError, e:
            logger.warning(
                "Error opening file %s with encoding %s: %s" %\
                    (filename, self.format_encoding, e),
                exc_info=True
            )
            raise FormatError(unicode(e))
        except Exception, e:
            logger.error("Unhandled exception: %s" % e, exc_info=True)
            raise
        finally:
            f.close()

    def _content_from_template(self, resource):
        """Return the content of the template for the specified resource.

        Args:
            resource: The resource the template of which we want.
        Returns:
            The template as a unicode string.
        """
        return Template.objects.get(
            resource=resource
        ).content.decode(self.default_encoding)

    def set_language(self, language):
        """Set the language for the handler."""
        if isinstance(language, Language):
            self.language = language
        else:
            try:
                self.language = Language.objects.by_code_or_alias(language)
            except Language.DoesNotExist, e:
                logger.warning(
                    "Language.DoesNotExist: %s" % e, exc_info=True
                )
                raise FormatError(unicode(e))
            except Exception, e:
                logger.error(unicode(e), exc_info=True)
                raise FormatError(unicode(e))

    def bind_content(self, content):
        """Bind some content to the handler."""
        self.content = self._get_content(content=content)

    def bind_file(self, filename):
        """Bind a file to an initialized POHandler."""
        if os.path.isfile(filename):
            self.filename = filename
            self.content = self._get_content(filename=filename)
        else:
            msg = _("Specified file %s does not exist." % filename)
            logger.error(msg)
            raise FormatError(msg)

    def bind_resource(self, resource):
        """Bind a resource to an initialized POHandler."""
        if isinstance(resource, Resource):
            self.resource = resource
            try:
                resource_template = self.resource.source_file_template
            except Template.DoesNotExist:
                resource_template = None
            self.compiled_template = self.compiled_template or resource_template
            self.language = self.language or resource.source_language
        else:
            msg = _("The specified object %s is not of type Resource" % resource)
            logger.error(msg)
            raise FormatsError(msg)

    def _find_linesep(self, s):
        """Find the line separator used in the file."""
        if "\r\n" in s:         # windows line ending
            self.linesep = "\r\n"
        else:
            self.linesep = "\n"

    def _prepare_line(self, line):
        """
        Prepare a line for parsing.

        Remove newline and whitespace characters.
        """
        return line.rstrip('\r\n').strip()

    ####################
    #  Core functions  #
    ####################

    def _get_translation(self, string, language, rule):
        try:
            return Translation.objects.get(
                resource=self.resource, source_entity=string,
                language=language, rule=rule
            ).order_by()
        except Translation.DoesNotExist, e:
            return None

    def _escape(self, s):
        """Escape special characters in string."""
        return s

    def _add_translation_string(self, *args, **kwargs):
        """Adds to instance a new translation string."""
        self.stringset.add(GenericTranslation(*args, **kwargs))

    def _add_suggestion_string(self, *args, **kwargs):
        """Adds to instance a new suggestion string."""
        self.suggestions.add(GenericTranslation(*args, **kwargs))

    @need_resource
    def compile(self, language=None, pseudo=None, mode=Mode.DEFAULT):
        """Compile the translation for the specified language.

        The actual output of the compilation depends on the arguments.

        Args:
            language: The language of the translation.
            pseudo: The pseudo type to use (if any).
            mode: The mode of the translation.
        Returns:
            The compiled template in the correct encoding.
        """
        if language is None:
            language = self.language
        content = self._content_from_template(self.resource)
        compiler = self.construct_compiler(language, pseudo, mode)
        try:
            return compiler.compile(
                content, language
            ).encode(self.format_encoding)
        except Exception, e:
            logger.error("Error compiling file: %s" % e, exc_info=True)
            raise self.HandlerCompileError(unicode(e))


    #######################
    #  save methods
    #######################

    def _context_value(self, context):
        """Convert the context for the database.

        Args:
            context: The context value calculated
        Returns:
            The correct value for the context to be used in the database.
        """
        return context or u'None'

    def _handle_update_of_resource(self, user):
        """Do extra stuff after a source language/translation has been updated.

        Args:
            user: The user that caused the update.
        """
        self._update_stats_of_resource(self.resource, self.language, user)

        if self.language == self.resource.source_language:
            nt = 'project_resource_changed'
        else:
            nt = 'project_resource_translated'
        context = {
            'project': self.resource.project,
            'resource': self.resource,
            'language': self.language,
            'sender': user
        }
        object_list = [self.resource.project, self.resource, self.language]
        team = Team.objects.get_or_none(project=self.resource.project,
                                        language_code=self.language.code)
        if team:
            object_list.append(team)

        # if we got no user, skip the log
        if user:
            action_logging(user, object_list, nt, context=context)

        if settings.ENABLE_NOTICES:
            send_notices_for_formats.delay(nt, context)

    def _init_source_entity_collection(self, se_list):
        """Initialize the source entities collection.

        Get a collection of source entity objects for the current resource.

        Args:
            se_list: An iterable of source entity objects.
        Returns:
            A SourceEntityCollection object.
        """
        source_entities = SourceEntityCollection()
        for se in se_list:
            source_entities.add(se)
        return source_entities

    def _init_translation_collection(self, se_ids):
        """Initialize the translations collections.

        Get a collection of translation objects for the current language.

        Args:
            se_ids: An iterable of source entities ids the translation
                objects are for.
        Returns:
            A TranslationCollection object.
        """
        qs = Translation.objects.filter(
            language=self.language, source_entity__in=se_ids).iterator()
        translations = TranslationCollection()
        for t in qs:
            translations.add(t)
        return translations

    def _pre_save2db(self, *args, **kwargs):
        """
        This is called before doing any actual work. Override in inherited
        classes to alter behaviour.
        """
        pass

    def _post_save2db(self, *args, **kwargs):
        """
        This is called in the end of the save2db method. Override if you need
        the behaviour changed.
        """
        kwargs.update({
            'resource': self.resource,
            'language': self.language
        })
        post_save_translation.send(sender=self, **kwargs)

    def _should_skip_translation(self, se, trans):
        """Check if current translation should be skipped, ie not saved to db.

        This should happen for empty translations (ie, untranslated strings)
        and for strings which are not correctly pluralized.

        Args:
            se: The source entity that corresponds to the translation.
            trans: The translation itself.
        Returns:
            True, if the specified translation must be skipped, ie not
            saved to database.
        """
        return not trans.translation or trans.pluralized != se.pluralized

    def _save_source(self, user, overwrite_translations):
        """Save source language translations to the database.

        Subclasses should override this method, if they need to customize
        the behavior of saving translations in the source language.

        Any fatal exception must be reraised.

        Args:
            user: The user that made the commit.
            overwrite_translations: A flag to indicate whether translations
                should be overrided.

        Returns:
            A tuple of number of strings added, updted and deleted.

        Raises:
            Any exception.
        """
        qs = SourceEntity.objects.filter(resource=self.resource).iterator()
        original_sources = list(qs) # TODO Use set() instead? Hash by pk
        updated_entities = set([])
        new_entities = []
        source_entities = self._init_source_entity_collection(original_sources)
        translations = self._init_translation_collection(source_entities.se_ids)

        strings_added = 0
        strings_updated = 0
        strings_deleted = 0
        try:
            for j in self.stringset:
                if j in source_entities:
                    se = source_entities.get(j)
                    if se in new_entities:
                        continue
                    # update source string attributes.
                    se.flags = j.flags or ""
                    se.pluralized = j.pluralized
                    se.developer_comment = j.comment or ""
                    se.occurrences = j.occurrences
                    se.order = j.order
                    # se.save()
                    updated_entities.add(se)
                else:
                    # Create the new SE
                    se = SourceEntity(
                        string = j.source_entity,
                        context = self._context_value(j.context),
                        resource = self.resource, pluralized = j.pluralized,
                        position = 1,
                        # FIXME: this has been tested with pofiles only
                        flags = j.flags or "",
                        developer_comment = j.comment or "",
                        occurrences = j.occurrences,
                        order = j.order
                    )
                    # Add it to list with new entities
                    new_entities.append(se)
                    source_entities.add(se)

            SourceEntity.objects.bulk_insert(new_entities)
            SourceEntity.objects.bulk_update(updated_entities)
            qs = SourceEntity.objects.filter(resource=self.resource).iterator()
            new_sources = list(qs) # TODO Use set() instead? Hash by pk
            source_entities = self._init_source_entity_collection(new_sources)
            new_translations = []
            updated_translations = set([])
            for j in self.stringset:
                se = source_entities.get(j)
                if self._should_skip_translation(se, j):
                    continue
                if (se, j) in translations:
                    tr = translations.get((se, j))
                    if overwrite_translations and tr.string != j.translation:
                        tr.string = j.translation
                        tr.user = user
                        updated_translations.add(tr)
                        strings_updated += 1
                else:
                    tr = Translation(
                        source_entity=se, language=self.language, rule=j.rule,
                        string=j.translation, user=user,
                        resource = self.resource
                    )
                    new_translations.append(tr)
                    # translations.add(tr)
                    if j.rule==5:
                        strings_added += 1
            Translation.objects.bulk_insert(new_translations)
            Translation.objects.bulk_update(updated_translations)
        except Exception, e:
            msg = "Error importing the entries into the database: %s"
            logger.error(msg % e)
            raise

        sg_handler = self.SuggestionFormat(self.resource, self.language, user)
        sg_handler.add_from_strings(self.suggestions)
        new_entities = SourceEntity.objects.exclude(
            pk__in=[s.pk for s in original_sources]
        ).filter(
            resource=self.resource
        ).iterator()
        untouched_ses = set(original_sources) - updated_entities
        sg_handler.create_suggestions(untouched_ses, list(new_entities))
        for se in untouched_ses:
            se.delete()
        self._update_template(self.template)

        strings_deleted = len(untouched_ses)
        del new_entities, original_sources, updated_entities, untouched_ses
        del new_sources
        return strings_added, strings_updated, strings_deleted

    def _save_translation(self, user, overwrite_translations):
        """Save other language translations to the database.

        Subclasses should override this method, if they need to customize
        the behavior of saving translations in other languages than the source
        one.

        Any fatal exception must be reraised.

        Args:
            user: The user that made the commit.
            overwrite_translations: A flag to indicate whether translations
                should be overrided.

        Returns:
            A tuple of number of strings added, updted and deleted.

        Raises:
            Any exception.
        """
        qs = SourceEntity.objects.filter(resource=self.resource).iterator()
        source_entities = self._init_source_entity_collection(qs)
        translations = self._init_translation_collection(source_entities.se_ids)
        new_translations = []
        updated_translations = set([])

        strings_added = 0
        strings_updated = 0
        strings_deleted = 0
        try:
            for j in self.stringset:
                if j not in source_entities:
                    continue
                else:
                    se = source_entities.get(j)

                if self._should_skip_translation(se, j):
                    continue
                if (se, j) in translations:
                    tr = translations.get((se, j))

                    # We also check if the user submitting the translation
                    # has reviewing privileges. Regular users shouldn't be
                    # able to modify a reviewed string.

                    # FIXME: This check shouldn't be needed but save2db is
                    # called with user=None all over the place, so do this
                    # for now to avoid breaking everything.
                    if user:
                        check = ProjectPermission(user)
                        review_perm = check.proofread(self.resource.project,
                            self.language)
                        if overwrite_translations and tr.string != j.translation:
                            if tr.reviewed:
                                if not review_perm:
                                    continue
                            tr.string = j.translation
                            tr.user = user
                            updated_translations.add(tr)
                            strings_updated += 1
                    else:
                        if overwrite_translations and tr.string != j.translation:
                            tr.string = j.translation
                            tr.user = user
                            updated_translations.add(tr)
                            strings_updated += 1
                else:
                    tr = Translation(
                        source_entity=se, language=self.language, rule=j.rule,
                        string=j.translation, user=user, resource=self.resource
                    )
                    new_translations.append(tr)
                    if j.rule==5:
                        strings_added += 1
            Translation.objects.bulk_insert(new_translations)
            Translation.objects.bulk_update(updated_translations)
        except Exception, e:
            logger.error(
                "There was a problem while importing the entries into the "
                "database. Entity: '%s'. Error: '%s'." % (
                    j.source_entity, e
                )
            )
            raise
        sg_handler = self.SuggestionFormat(self.resource, self.language, user)
        sg_handler.add_from_strings(self.suggestions)
        del new_translations, updated_translations, source_entities, translations
        return strings_added, strings_updated, strings_deleted

    def _update_stats_of_resource(self, resource, language, user):
        """Update the statistics for the resource.

        Also, invalidate any caches.
        """
        invalidate_stats_cache(resource, language, user=user)

    def _update_template(self, content):
        """Update the template of the resource.

        Args:
            content: The content of the template.
        """
        t, created = Template.objects.get_or_create(resource=self.resource)
        t.content = content
        t.save()

    @need_resource
    @need_language
    @need_stringset
    @transaction.commit_manually
    def save2db(self, is_source=False, user=None, overwrite_translations=True):
        """
        Saves parsed file contents to the database. duh
        """
        self._pre_save2db(is_source, user, overwrite_translations)
        try:
            if is_source:
                (added, updated, deleted) = self._save_source(
                    user, overwrite_translations
                )
            else:
                (added, updated, deleted) = self._save_translation(
                    user, overwrite_translations
                )
        except Exception, e:
            logger.warning(
                "Failed to save translations for language %s and resource %s."
                "Error was %s." % (self.language, self.resource, e),
                exc_info=True
            )
            transaction.rollback()
            return (0, 0)
        finally:
            gc.collect()
        try:
            self._post_save2db(
                is_source=is_source, user=user,
                overwrite_translations=overwrite_translations
            )
            if added + updated + deleted > 0:
                self._handle_update_of_resource(user)
        except Exception, e:
            logger.error("Unhandled exception: %s" % e, exc_info=True)
            transaction.rollback()
            raise FormatError(unicode(e))
        finally:
            gc.collect()
        transaction.commit()
        return (added, updated)

    ####################
    # parse methods
    ####################

    def _generate_template(self, obj):
        """Generate a template from the specified object.

        By default, we use the obj as a unicode string and encode it to
        str.

        Subclasses could override this.
        """
        return obj.encode(self.default_encoding)

    def _iter_by_line(self, content):
        """Iterate the content by line."""
        for line in content.split(self.linesep):
            yield line

    def _parse(self, is_source, lang_rules):
        """The actual functions that parses the content.

        Formats need to override this to provide the desired behavior.

        Two stringsets are available to subclasses:
        - self.stringset to save the translated strings
        - self.suggestions to save suggested translations

        Args:
            is_source: Flag to determine if this is a source file or not.
            lang_rules: rules for the language

        Returns:
            An object which, when used as an argument in
            `self._create_template()`, the template for the resource
            is generated.

        """
        raise NotImplementedError

    @need_content
    @need_language
    def parse_file(self, is_source=False, lang_rules=None):
        """Parse the content."""
        self.stringset = StringSet()
        self.suggestions = StringSet()
        self.is_content_valid()
        try:
            obj = self._parse(is_source, lang_rules)
        except self.HandlerParseError, e:
            msg = "Error when parsing file for resource %s: %s"
            logger.error(msg % (self.resource, e), exc_info=True)
            raise
        if self.resource and not self.stringset:
            msg = _("We're not able to extract any string from the file "
                    "uploaded for language %(language)s in resource "
                    "%(resource)s." % {'language': self.language,
                    'resource': self.resource})
            logger.error("Error during parsing for resource %s -> %s" % (
                self.resource, msg), exc_info=True)
            raise self.HandlerParseError(msg)
        if is_source:
            self.template = self._generate_template(obj)
