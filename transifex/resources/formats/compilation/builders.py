# -*- coding: utf-8 -*-

"""
Classes to build the set of translations to use for compilation.

These builders are responsible to fetch all translations to be
used, when compiling a template.
"""

import itertools
import collections
from django.db.models import Count
from transifex.resources.models import SourceEntity, Translation


class TranslationsBuilder(object):
    """Builder to fetch the set of translations to use."""

    single_fields = ['source_entity_id', 'string']
    plural_fields = ['source_entity_id', 'string', 'rule']

    def __init__(self, resource, language):
        """Set the resource and language for the translation."""
        self.resource = resource
        self.language = language
        self.pluralized = False

    def __call__(self):
        """Get the translation strings for the resource.

        The returned translations are for the specified language.

        Returns:
            A dictionary with the translated strings. The keys are the id of
            the source entity this translation corresponds to and values are
            the translated strings.
        """
        # TODO Should return plurals
        raise NotImplementedError

    def _get_source_strings(self, ids):
        """Get a list of the source strings of the resource.

        Args:
            The ids to fetch source strings for.
        """
        return Translation.objects.filter(
            source_entity__in=ids, language=self.resource.source_language
        ).values_list(*self._fields).order_by()

    def _single_output(self, iterable):
        """Output of builder for non-pluralized formats."""
        return dict(iterable)

    def _plurals_output(self, iterable):
        """Output of builder for pluralized formats."""
        res = collections.defaultdict(dict)
        for t in iterable:
            res[t[0]][t[2]] = t[1]
        return res

    def _set_pluralized(self, p):
        """Choose between pluralized and non-pluralized version."""
        if p:
            self._output = self._plurals_output
            self._fields = self.plural_fields
        else:
            self._output = self._single_output
            self._fields = self.single_fields
    pluralized = property(fset=_set_pluralized)


class AllTranslationsBuilder(TranslationsBuilder):
    """Builder to fetch all translations."""

    def __call__(self):
        """Get the translation strings that match the specified
        source_entities.
        """
        translations = Translation.objects.filter(
            resource=self.resource, language=self.language
        ).values_list(*self._fields).order_by().iterator()
        return self._output(translations)


class EmptyTranslationsBuilder(TranslationsBuilder):
    """Builder to fetch no translations."""

    def __init__(self, *args, **kwargs):
        super(EmptyTranslationsBuilder, self).__init__(None, None)

    def __call__(self):
        """Return an empty dictionary."""
        return self._output('')


class ReviewedTranslationsBuilder(TranslationsBuilder):
    """Builder to fetch only reviewed strings."""

    def __call__(self):
        """Get the translation strings that match the specified source_entities
        and have been reviewed.
        """
        translations = Translation.objects.filter(
            reviewed=True, resource=self.resource, language=self.language
        ).values_list(*self._fields).order_by().iterator()
        return self._output(translations)


class SourceTranslationsBuilder(TranslationsBuilder):
    """Builder to use source strings in case of missing strings."""

    def __call__(self):
        """Get the translation strings that match the specified
        source entities. Use the source strings for the missing
        ones.
        """
        translations = Translation.objects.filter(
            resource=self.resource, language=self.language
        ).values_list(*self._fields).order_by()
        source_entities = set(SourceEntity.objects.filter(
                resource=self.resource
        ).values_list('id', flat=True).order_by())
        missing_ids = source_entities - set(map(lambda x: x[0], translations))
        if not missing_ids:
            iterable = translations
        else:
            source_strings = self._get_source_strings(missing_ids)
            iterable = itertools.chain(translations, source_strings)
        return self._output(iterable)


class ReviewedSourceTranslationsBuilder(TranslationsBuilder):
    """Builder to fetch only reviewed translations and fill the others
    with the source strings.
    """

    def __call__(self):
        """Get the translation strings that match the specified
        source entities. Use the source strings for the missing
        ones.
        """
        translations = Translation.objects.filter(
            reviewed=True, resource=self.resource, language=self.language
        ).values_list(*self._fields).order_by()
        source_entities = set(SourceEntity.objects.filter(
                resource=self.resource
        ).values_list('id', flat=True).order_by())
        missing_ids = source_entities - set(map(lambda x: x[0], translations))
        if not missing_ids:
            iterable = translations
        else:
            source_strings = self._get_source_strings(missing_ids)
            iterable = itertools.chain(translations, source_strings)
        return self._output(iterable)


class _MarkSourceMixin(object):
    """Mixin to provide a method to return source strings marked."""

    def _get_source_strings(self, ids):
        """Mark the source strings with a _txss before returning them."""
        strings = super(_MarkSourceMixin, self)._get_source_strings(ids)
        res = []
        for s in strings:
            res.append(list(s))
            res[-1][1] = s[1] + '_txss'
        return res


class MarkedSourceTranslationsBuilder(_MarkSourceMixin,
                                      SourceTranslationsBuilder):
    """Mark the source strings, so that the compiler knows how to
    handle those.
    """


class ReviewedMarkedSourceTranslationsBuilder(
    _MarkSourceMixin, ReviewedSourceTranslationsBuilder
):
    """Mark the source strings, so that the compiler knows how to
    handle those.
    """
