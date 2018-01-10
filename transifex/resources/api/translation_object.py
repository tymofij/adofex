# -*- coding: utf-8 -*-

"""
API for Translation objects.
"""

from __future__ import absolute_import
from django.db import transaction
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import User
from piston.handler import BaseHandler
from piston.utils import rc, throttle, require_mime
from transifex.txcommon.decorators import one_perm_required_or_403
from transifex.txcommon.log import logger
from transifex.projects.permissions import *
from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.projects.permissions.project import ProjectPermission
from transifex.resources.decorators import method_decorator
from transifex.resources.models import Resource, SourceEntity, Translation
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.teams.models import Team
from transifex.resources.handlers import invalidate_stats_cache
from transifex.api.utils import BAD_REQUEST, FORBIDDEN_REQUEST,\
        NOT_FOUND_REQUEST
from .exceptions import BadRequestError, NoContentError, NotFoundError, \
        ForbiddenError


class BaseTranslationHandler(BaseHandler):

    allowed_methods = ('GET', 'PUT',)

    def _generate_dict_for_translation(self, trans_dict, translation,
            field_map, append, pluralized):
        """Generate or update a dictionary for a source_entity along
        with its translation(s).

        Args:
            trans_dict: A dictionary, may be empty or existing
            translation: A translation values dictionary
            field_map: A dictionary mapping the keys of dictionary
                       translation to the keys used in output JSON
            append: A Boolean, False if trans_dict exists already, else
                    False
            pluralized: A Boolean, True if source_entity is pluralized,
                    else False.

        Returns:
            A dictionary representing a source entity and its translations
            along with other aggregated attributes.
        """
        for key in field_map.keys():
            if pluralized and key == 'string':
                if append:
                    trans_dict[field_map[key]] = {translation['rule']:\
                            translation['string']}
                else:
                    trans_dict[field_map[key]][translation['rule']] =\
                            translation['string']
            elif pluralized and key == 'wordcount':
                if append:
                    trans_dict[field_map[key]] = translation['wordcount']
                else:
                    # Aggregated wordcount for pluralized translations
                    trans_dict[field_map[key]] += translation['wordcount']
            else:
                trans_dict[field_map[key]] = translation[key]
        return trans_dict

    def _update_result_if_single_translation(self, single, result):
        """
        Args:
            single: A boolean,
            result: A list of trans_dict(s)
        """
        # Generate translations dict for SingleTranslationHandler,
        # i.e, when single == True
        if single:
            if result:
                result = result[0]
            else:
                result = ""
        return result

    def _append_or_update_trans_dict(self, trans_dict, result, append,
            count, index):
        """
        Append or update trans_dict in *result* list.
        If append is True, append trans_dict to *result* and update count,
        else, update trans_dict already in *result* at position *index*.

        Args:
            trans_dict: A dictionary representing
                translation(s) belonging to a source entity.
            result: A list containing many trans_dict.
            append: A boolean, True if trans_dict is to be appended to
                result, else False
            count: An integer representing length of result
            index: An integer representing the position where a trans_dict
                has to be inserted in *result*
        Returns:
            An integer, representing the length of the length of the list
            *result*
        """
        if append:
            result.append(trans_dict)
            # increment count only if a trans_dict is appended to `result`
            count += 1
        else:
           result[index] = trans_dict
        return count

    def _generate_translations_dict(self, translations, field_map={},
                                    single=False):
        """
        Generate result to returned to the user for the related
        translations

        Args:
            translations: A list of translation values dictionaries
            field_map: A dictionary mapping the keys of dictionary
                       translation to the keys used in output JSON
            single: A boolean, True if it's for SingleTranslationHandler
        Returns:
            A dictionary
        """
        result = []
        # Dictionary `buf` maps `source_entity.id` to its index in array
        # `result`.
        buf = {}
        # count stores the index of a source_entity in the array 'result'
        count = 0
        for translation in translations:
            append = True
            pluralized = False

            # An dictionary representing translation(s) belonging to a source
            # entity along with other aggregated attributes
            trans_dict = dict()
            index = -1
            if translation.get('source_entity__pluralized'):
                if buf.get(translation.get('source_entity__id')) != None:
                    index = buf.get(translation.get('source_entity__id'))
                    trans_dict = result[index]
                    append = False
                else:
                    buf[translation.get('source_entity__id')] = count
                pluralized = True

            # Create/update a dictionary for a source entity
            trans_dict = self._generate_dict_for_translation(trans_dict,
                    translation, field_map, append, pluralized)
            count = self._append_or_update_trans_dict(trans_dict, result,
                    append, count, index)
        return self._update_result_if_single_translation(single, result)

    def _get_fieldmap(self, details=False):
        """
        Get fieldmap for Translation model.

        What is a fieldmap?
        A dictionary that maps django model attributes for Translation
        to humanized *keys* to be used in output JSON.

        Args:
            details: A Boolean, True if request contains `details`
                    as a GET parameter.

        Returns:
            A dictionary
        """
        field_map = {
                'source_entity__string': 'key',
                'source_entity__context': 'context',
                'string': 'translation',
                'reviewed': 'reviewed',
                'source_entity__pluralized': 'pluralized'
        }

        if details:
            field_map.update({
                'wordcount': 'wordcount',
                'last_update': 'last_update',
                'user__username': 'user',
                'source_entity__position': 'position',
                'source_entity__occurrences': 'occurrences',
            })
        return field_map

    def _get_fields_for_translation_value_query_set(self, field_map):
        """
        Get fields  which needs to be included in the ValueQuerySet
        for a Translation QuerySet.

        Args:
            field_map: A dictionary that maps django
            model attributes for Translation to humanized *keys*
            to be used in output JSON.
        Returns:
            A list containing the fields that need to be in a ValueQuerySet
            for Translation.
        """
        fields = ['source_entity__id', 'rule']
        fields.extend(field_map.keys())
        return fields

    def _get_translation_query_filters(self, request, resource,
            language):
        """
        Get filters for querying Translation
        Args:
            request: An HTTP request object
            resource: A Resource object
            language: A language object
        Returns:
            A dictionary
        """

        filters = {
                'resource': resource,
                'language': language,
        }

        if request.GET.get('key'):
            filters.update({'source_entity__string__icontains': \
                    request.GET.get('key')})

        if request.GET.get('context'):
            filters.update({'source_entity__context__icontains':\
                    request.GET.get('context')})

        return filters

    def _requested_objects(self, project_slug,
            resource_slug, language_code):
        """
        Get objects from request parameters if the related objects
        exist. In case an object does not exist, then raise an error.
        If all objects are found, return a tuple of the objects.

        Args:
            project_slug: A project slug
            resource_slug: A resource slug
            language_code: A language code
        Returns:
            If objects for all parameters are found, then return
            a tuple, (project, resource, language)
            else raise an error
        """
        try:
            resource = Resource.objects.get(slug=resource_slug,
                    project__slug=project_slug)
            project = resource.project
            language = Language.objects.by_code_or_alias(language_code)
        except Project.DoesNotExist, e:
            raise NotFoundError("Project with slug '%s' does not exist" % \
                    project_slug)
        except Resource.DoesNotExist, e:
            raise NotFoundError("Resource '%s.%s' does not exist" % \
                    (project_slug, resource_slug))
        except Language.DoesNotExist, e:
            raise NotFoundError("Language with code '%s' does not exist." %\
                    language_code)
        return (project, resource, language)

    def _validate_language_is_not_source_language(self, source_language,
            language):
        """
        Validate if source language is not target language.

        Args:
            source_language: A Language instance for source language
            language: A Language instance for target language
        Returns:
            if language == source language, raise ForbiddenError
            else, return True
        """
        if language == source_language:
            raise ForbiddenError("Forbidden to update translations "\
                    "in source language.")
        return True

    def _validate_translations_json_data(self, translations):
        """
        Validate if translations exist and are inside a list.
        Else, raise an error.
        """
        if not translations:
            raise NoContentError("Translations not found!")
        if not isinstance(translations, list):
            raise BadRequestError("Translations are not in a list!")
        return True

    def _translations_as_dict(self, translations, resource, language):
        """
        Get a dictionary where source_entity id is mapped to
        translations.

        Args:
            translations: A dictionary containing translation data
                          from request.data
            resource: A Resource instance
            language: A Language object

        Returns:
            A dictionary
        """
        query = Q()
        for translation in translations:
            if translation.has_key('source_entity_hash'):
                query |= Q(source_entity__string_hash=translation[
                    'source_entity_hash'])

        query &= Q(resource=resource, language=language)

        trans_obj_dict = {}
        for t in Translation.objects.filter(query).select_related(
                'source_entity', 'user').iterator():
            se = t.source_entity
            if trans_obj_dict.get(se.string_hash):
                trans_obj_dict.get(se.string_hash).append(t)
            else:
                trans_obj_dict[se.string_hash] = [t]

        return trans_obj_dict

    def _user_has_update_perms(self, translation_objs=None,
            translation_reviewed=False,  can_submit_translations=False,
            accept_translations=False, is_maintainer=False, can_review=False,):
        """
        Check if user has necessary permissions.
        Args:
            translation_objs: A dictionary mapping source_entity.string_has
                to translations
            translation_reviewed: A boolean, True if translation is reviewed
                in request JSON
            can_submit_translations: A boolean
            accept_translations: A boolean
            is_maintainer: A boolean
            can_review: A boolean
        Returns:
            A boolean
        """
        if (not can_submit_translations or\
            not accept_translations) and not\
                is_maintainer:
            return False
        if not translation_objs:
            return False
        reviewed = translation_objs[0].reviewed
        if (reviewed or translation_reviewed != reviewed) and\
                not can_review:
            return False
        return True

    def _collect_updated_translations(self, translation, trans_obj_dict,
            checksum, updated_translations, user, pluralized):
        """
        Collect only updated translations
        Args:
            translation: A dictionary representing a translation(s) in
                         request JSON
            trans_obj_dict: A dictionary mapping source_entity id to
                           translations
            checksum: An md5 checksum for a key and context
            updated_translations: A list of updated translations
            user: A User object
            pluaralized: A boolean
        """
        translations = []
        updated = False
        for t in trans_obj_dict.get(checksum):
            if translation.has_key('reviewed'):
                reviewed = translation.get('reviewed')
                if t.reviewed != reviewed:
                    updated = True
                    t.reviewed = reviewed
            if pluralized:
                new_translation = translation['translation'].get(str(t.rule))
            else:
                new_translation = translation['translation']
            if new_translation and t.string != new_translation:
                updated = True
                t.string = new_translation
                # Update author info for a translation only when the
                # translation strings is updated
                t.user = user
            translations.append(t)
            if updated:
                updated_translations.extend(translations)

    def _is_pluralized(self, translation, nplurals):
        """
        Check if a translation is pluralized with correct plural
        forms.

        Args:
            translation: A dictionary representing a translation(s) in
                         request JSON
            nplurals: A list containing plural rule numbers for a language
        Returns:
            A boolean, True if translation(s) are pluralized with correct
            plural forms, else False.
            In case of bad plural forms, it raises an error.
        """
        is_pluralized = False
        error = False
        if isinstance(translation.get('translation'), dict):
            plural_forms = translation.get('translation').keys()
            for rule in plural_forms:
                if not translation.get('translation').get(rule).strip():
                    plural_forms.pop(rule)
            plural_forms = [int(r) for r in plural_forms]
            plural_forms.sort()
            if plural_forms == nplurals:
                is_pluralized = True
            else:
                error = True
        if error:
            raise BadRequestError("Bad plural forms for "
                    "key: '%(se)s' and context: '%(context)s'." % {
                    'se': translation.get('key'),
                    'context': translation.get('context')})
        return is_pluralized

    @transaction.commit_on_success
    def _update_translations(self, updated_translations):
        """Bulk update translations
        Args:
            updated_translations: A list of updated Translation objects
        """
        Translation.objects.bulk_update(updated_translations)

    def _get_update_fieldmap_and_fields(self, keys):
        """Get fieldmap and fields for a PUT request.
        Args:
            keys: A list of dictionary keys for request.data
        Returns:
            A tuple, (dictionary, list)
        """
        field_map = {
                'source_entity__string': 'key',
                'source_entity__context': 'context',
                'string': 'translation',
                'reviewed': 'reviewed',
                'source_entity__pluralized': 'pluralized',
                'wordcount': 'wordcount',
                'last_update': 'last_update',
                'user__username': 'user',
                'source_entity__position': 'position',
                'source_entity__occurrences': 'occurrences',
        }

        fields = []
        field_map_ = {}
        for f in field_map.viewitems():
            if f[1] in keys:
                fields.append(f[0])
                field_map_[f[0]] = f[1]

        if 'source_entity__pluralized' not in fields:
            fields.append('source_entity__pluralized')
        if 'rule' not in fields:
            fields.append('rule')

        return (field_map_, fields)

    def _get_user_to_update_translation(self, project, check,
            request_user, author_name, is_maintainer=False):
        """
        Get user who will update a translation.

        Args:
            project: A Project instance
            check: A ProjectPermission instance for request_user
            request_user: A User instance, request.user
            author_name: A string, username for translation author
            is_maintainer: A boolean, True if user is a maintainer
                of the project

        Returns:
            A User instance
        """
        if is_maintainer or check.maintain(project):
            user = author_name and User.objects.get(username=author_name
                    ) or request_user
        else:
            user = request_user
        return user

    def _get_user_perms(self, user, project, resource, language,
            team, checksum, is_maintainer):
        """
        Get permissions for a user.

        Args:
            user: A User instance
            project: A Project instance
            resource: A Resource instance
            language: A Language instance
            team: A Team instance
            checksum: An md5 checksum representing a source entity
            is_maintiner: A boolean
        Returns:
            A dictionary containing various user permissions
        """
        check = ProjectPermission(user)
        can_review = check.proofread(project, language)
        can_submit_translations = check.submit_translations(
                team or resource.project)
        accept_translations = resource.accept_translations

        return {
            'can_review': can_review,
            'can_submit_translations': can_submit_translations,
            'accept_translations': accept_translations,
            'is_maintainer': check.maintain(project),
        }

    def _process_translation_dict(self, translation, project, resource,
            language, team, check, is_maintainer, request_user, se_ids,
            updated_translations, trans_obj_dict):
        """
        Process a translation dictionary in the JSON request and update
        se_ids and updated_translations lists.

        Args:
            translation: A dictionary representing a translation(group)
                in requested JSON
            project: A Project instance
            resource: A Resource instance
            language: A Language instance
            team: A Team instance
            check: A ProjectPermission instance for user
            request_user: A User instance issuing this request
            se_ids: A list containing all the SourceEntity ids whose
                translations have been updated.
            updated_translations: A list containing updated Translation
                instances.
            trans_obj_dict: A dictionary mapping source_entity.string_hash
                to a list of Translation objects.
        """
        if translation.has_key('source_entity_hash'):
            checksum = translation['source_entity_hash']
        else:
            return
        translation_objs = trans_obj_dict.get(checksum)
        se = translation_objs[0].source_entity
        se_id = se.id
        nplurals = language.get_pluralrules_numbers()
        user = self._get_user_to_update_translation(project,
                check, request_user, translation.get('user'),
                is_maintainer)
        # Get user permissions for the project
        user_perms = self._get_user_perms(user, project, resource,
                language, team, checksum, is_maintainer)
        # Check if user is allowed to updated the translation. This also takes
        # into account if a user is allowed to review a translation or modify
        # a reviewed translation.
        if not self._user_has_update_perms(translation_objs=translation_objs,
                translation_reviewed=translation.get('reviewed'),
                **user_perms):
            raise ForbiddenError("User '%(user)s' is not allowed to "
                    "update translation for '%(se)s' in language "
                    "'%(lang_code)s'." % {'user': user, 'se': se,
                    'lang_code': language.code})
        # Validate if a translation group is properly pluralized or
        # not. In case of improper plural forms, it raises an error.
        # Else, it returns True if translation group is pluralized,
        # otherwise False.
        pluralized = self._is_pluralized(translation, nplurals)
        self._collect_updated_translations(
                translation, trans_obj_dict, checksum,
                updated_translations, user, pluralized)
        se_ids.append(se_id)


class SingleTranslationHandler(BaseTranslationHandler):
    """Read and update a single translation"""

    def _get_fieldmap(self):
        """
        Returns a field_map

        A field_map is used to map the selected field names of Translation
        model with the field names used in the JSON representation of the
        translations.
        """
        field_map = {
                'source_entity__string': 'key',
                'source_entity__context': 'context',
                'string': 'translation',
                'reviewed': 'reviewed',
                'source_entity__pluralized': 'pluralized',
                'wordcount': 'wordcount',
                'last_update': 'last_update',
                'user__username': 'user',
                'source_entity__position': 'position',
                'source_entity__occurrences': 'occurrences',
        }
        return field_map

    @throttle(settings.API_MAX_REQUESTS, settings.API_THROTTLE_INTERVAL)
    @method_decorator(one_perm_required_or_403(
            pr_project_private_perm,
            (Project, 'slug__exact', 'project_slug')
    ))
    def read(self, request, project_slug, resource_slug,
            language_code, source_hash, api_version=2):
        """
        Read translations for a single source entity of a resource
        along with aggregated detailed info about the translations.
        """
        try:
            project, resource, language = self._requested_objects(
                    project_slug, resource_slug, language_code
            )
        except NotFoundError, e:
            return NOT_FOUND_REQUEST(unicode(e))

        translations = Translation.objects.filter(
            resource=resource, source_entity__string_hash=source_hash,
            language=language
        )
        if not translations:
            return rc.NOT_FOUND

        field_map = self._get_fieldmap()
        fields = self._get_fields_for_translation_value_query_set(field_map)
        return self._generate_translations_dict(
            translations.values(*fields), field_map, True
        )

    @require_mime('json')
    @throttle(settings.API_MAX_REQUESTS, settings.API_THROTTLE_INTERVAL)
    @method_decorator(one_perm_required_or_403(
            pr_project_private_perm,
            (Project, 'slug__exact', 'project_slug')
    ))
    def update(self, request, project_slug, resource_slug,
            language_code, source_hash, api_version=2):
        """
        Update existing translations for a source entity of a resource.
        """
        try:
            project, resource, language = \
                    self._requested_objects(project_slug,
                    resource_slug, language_code)
            # A translation in source language cannot be updated
            self._validate_language_is_not_source_language(
                    project.source_language, language)
            try:
                source_entity = SourceEntity.objects.get(
                        string_hash=source_hash, resource=resource)
            except SourceEntity.DoesNotExist, e:
                return rc.NOT_FOUND
            team = Team.objects.get_or_none(project, language.code)
            data = request.data
            # This is a hack to use the methods from TranslationObjectsHandler
            data['source_entity_hash'] = source_hash
            check = ProjectPermission(request.user)
            is_maintainer = check.maintain(project)
            # Allow only project members to issue this update request
            if not is_maintainer and  not (check.submit_translations(
                team or project) or check.proofread(project, language)):
                return FORBIDDEN_REQUEST(
                        "You are not allowed to update translations.")
            trans_obj_dict = self._translations_as_dict(
                    [data], resource, language)
            if not trans_obj_dict:
                return rc.NOT_FOUND
            updated_translations = []
            se_ids = []
            # All permission checks for a user is done here and
            # updated translations are collected in updated_tranlsations
            # and source_entity.id in se_ids
            self._process_translation_dict(data, project, resource,
                    language, team, check, is_maintainer, request.user,
                    se_ids, updated_translations, trans_obj_dict)
            # Updated translations are saved to db
            self._update_translations(updated_translations)

            translations = Translation.objects.filter(
                    source_entity=source_entity, language=language)
            field_map = self._get_fieldmap()
            fields = self._get_fields_for_translation_value_query_set(field_map)
            return self._generate_translations_dict(
                    Translation.objects.filter( source_entity__id__in=se_ids,
                        language=language).values(*fields), field_map, True)
        except NotFoundError, e:
            return NOT_FOUND_REQUEST(unicode(e))
        except NoContentError, e:
            return BAD_REQUEST(unicode(e))
        except ForbiddenError, e:
            return FORBIDDEN_REQUEST(unicode(e))
        except BadRequestError, e:
            return BAD_REQUEST(unicode(e))


class TranslationObjectsHandler(BaseTranslationHandler):
    """
    Read and update a set of translations in a language for a resource.
    """

    @throttle(settings.API_MAX_REQUESTS, settings.API_THROTTLE_INTERVAL)
    @method_decorator(one_perm_required_or_403(
            pr_project_private_perm,
            (Project, 'slug__exact', 'project_slug')
    ))
    def read(self, request, project_slug, resource_slug,
            language_code, api_version=2):
        """
        Read existing translations for multiple source entities
        of a resource. It also allows to filter source entities
        by key and/or context and takes a 'details' GET parameter
        to show detailed info about the translations.
        """
        try:
            project, resource, language = self._requested_objects(
                    project_slug, resource_slug, language_code
            )
        except NotFoundError, e:
            return NOT_FOUND_REQUEST(unicode(e))

        field_map =  self._get_fieldmap(request.GET.has_key('details'))
        fields = self._get_fields_for_translation_value_query_set(field_map)
        filters = self._get_translation_query_filters(
            request, resource, language
        )
        translations = Translation.objects.filter(**filters).values(*fields)
        return self._generate_translations_dict(translations, field_map)

    @require_mime('json')
    @throttle(settings.API_MAX_REQUESTS, settings.API_THROTTLE_INTERVAL)
    @method_decorator(one_perm_required_or_403(
            pr_project_private_perm,
            (Project, 'slug__exact', 'project_slug')
    ))
    def update(self, request, project_slug, resource_slug,
            language_code, api_version=2):
        """
        Update existing translations for multiple source entities
        of a resource at one go by permitted user(s).
        """
        try:
            project, resource, language = \
                    self._requested_objects(
                    project_slug, resource_slug, language_code)
            self._validate_language_is_not_source_language(
                    project.source_language, language)
            translations = request.data
            self._validate_translations_json_data(translations)
            team = Team.objects.get_or_none(project, language.code)

            check = ProjectPermission(request.user)
            # User must be a member of the project
            is_maintainer = check.maintain(project)
            # Allow only project members to issue this update request
            if not is_maintainer and  not (check.submit_translations(
                team or project) or check.proofread(project, language)):
                return FORBIDDEN_REQUEST(
                        "You are not allowed to update translations.")

            trans_obj_dict = self._translations_as_dict(
                    translations, resource, language)

            updated_translations = []
            se_ids = []
            for translation in translations:
                # All permission checks for a user is done here and
                # updated translations are collected in updated_tranlsations
                # and source_entity.id in se_ids
                self._process_translation_dict(translation, project, resource,
                        language, team, check, is_maintainer, request.user,
                        se_ids, updated_translations, trans_obj_dict)

            self._update_translations(updated_translations)

            keys = ['key', 'context', 'translation',
                    'reviewed', 'pluralized', 'wordcount',
                    'last_update', 'user', 'position', 'occurrences',]
            field_map, fields = self._get_update_fieldmap_and_fields(keys)

            return self._generate_translations_dict(
                    Translation.objects.filter( source_entity__id__in=se_ids,
                        language=language).values(*fields), field_map)
        except NotFoundError, e:
            return NOT_FOUND_REQUEST(unicode(e))
        except NoContentError, e:
            return BAD_REQUEST(unicode(e))
        except ForbiddenError, e:
            return FORBIDDEN_REQUEST(unicode(e))
        except BadRequestError, e:
            return BAD_REQUEST(unicode(e))
        except User.DoesNotExist, e:
            return BAD_REQUEST(unicode(e))
