# -*- coding: utf-8 -*-
"""Module for handling suggestions in resources."""

from django.conf import settings
from suggestions.models import Suggestion
from transifex.txcommon.log import logger
from transifex.resources.models import Translation, SourceEntity
from transifex.resources.formats.utils.string_utils import percent_diff


class SuggestionFormat(object):
    """Base class for suggestion formats."""

    def __init__(self, resource, language, user):
        self.resource = resource
        self.language = language
        self.user = user


    def _convert_to_suggestions(self, source, dest, user=None, langs=None):
        """This function takes all translations that belong to source and
        adds them as suggestion to dest. Both source and dest are
        SourceEntity objects.

        The langs can contain a list of all languages for which the conversion
        will take place. Defaults to all available languages.
        """
        if langs:
            translations = Translation.objects.filter(source_entity=source,
                language__in=langs, rule=5)
        else:
            translations = Translation.objects.filter(source_entity=source, rule=5)

        for t in translations:
            # Skip source language translations
            if t.language == dest.resource.source_language:
                continue

            tr, created = Suggestion.objects.get_or_create(
                string = t.string,
                source_entity = dest,
                language = t.language
            )

            # If the suggestion was created and we have a user assign him as the
            # one who made the suggestion
            if created and user:
                tr.user = user
                tr.save()
        return

    def create_suggestions(self, original, new):
        """Create new suggestions.

        Find similar strings in original and new lists.

        Args:
            original: Original set of resources.
            new: Set of new resources.
        """
        raise NotImplementedError

    def add_from_strings(self, strings):
        """Add the strings as suggestions.

        Args:
            strings: An iterable of strings to add as suggestions
        """
        for j in strings:
            # Check SE existence
            try:
                se = SourceEntity.objects.get(
                    string = j.source_entity, context = j.context or "None",
                    resource = self.resource
                )
            except SourceEntity.DoesNotExist:
                logger.warning(
                    "Source entity %s does not exist" % j.source_entity
                )
                continue
            Suggestion.objects.get_or_create(
                string = j.translation, source_entity = se,
                language = self.language
            )


class KeySuggestionFormat(SuggestionFormat):
    """Class for formats the suggestions for which are based on
    similarities of keys.
    """
    pass


class ContentSuggestionFormat(SuggestionFormat):
    """Class for formats the suggestions of which are based on similarities
    of the content.
    """

    def create_suggestions(self, original, new):
        iterations = len(original)*len(new)
        # If it's not over the limit, then do it
        if iterations < settings.MAX_STRING_ITERATIONS:
            for se in original:
                for ne in new:
                    try:
                        old_trans = Translation.objects.get(source_entity=se,
                            language=se.resource.source_language, rule=5)
                        new_trans = Translation.objects.get(source_entity=ne,
                            language=se.resource.source_language, rule=5)
                    except Translation.DoesNotExist:
                        # Source language translation should always exist
                        # but just in case...
                        continue
                    # find Levenshtein distance
                    if percent_diff(old_trans.string, new_trans.string) < settings.MAX_STRING_DISTANCE:
                        self._convert_to_suggestions(se, ne, self.user)
                        break
