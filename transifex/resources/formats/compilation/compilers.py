# -*- coding: utf-8 -*-

"""
Compiler classes.

Classes that handle compiling a template.
"""

from __future__ import absolute_import
import re
from transifex.resources.models import SourceEntity
from ..exceptions import UninitializedCompilerError
from ..utils.hash_tag import hash_regex, pluralized_hash_regex


class Compiler(object):
    """Class to compile translation files.

    There is a set of translation strings obtained from
    the database, while the template is given by the caller.

    We use extra builders for the steps of fetching the set of
    translations (``translations``) for the language and for the
    type of translation we want (``tdecorator). This allows for
    full customization of those steps. See
    http://en.wikipedia.org/wiki/Builder_pattern.
    """

    def __init__(self, resource, **kwargs):
        """Set the variables of the object.

        The object is not fully initialized, unless the two
        builders have been set.

        Allows subclasses to add extra keyword arguments.

        Args:
            resource: The resource which the compilation is for.
        """
        self.resource = resource
        for arg, value in kwargs.items():
            setattr(self, arg, value)
        self._initialized = False
        self._translations = None
        self._tdecorator = None

    def _set_tset(self, t):
        self._tset = t
    translation_set = property(fset=_set_tset)

    def _set_tdecorator(self, a):
        self._tdecorator = a
    translation_decorator = property(fset=_set_tdecorator)

    def compile(self, template, language):
        """Compile the template using the database strings.

        The result is the content of the translation file.

        There are three hooks a subclass can call:
          _pre_compile: This is called first, before anything takes place.
          _examine_content: This is called, to have a look at the content/make
              any adjustments before it is used.
          _post_compile: Called at the end of the process.

        Args:
            template: The template to compile. It must be a unicode string.
            language: The language of the translation.
        Returns:
            The compiled template as a unicode string.
        """
        self.language = language
        if self._tset is None or self._tdecorator is None:
            msg = "One of the builders has not been set."
            raise UninitializedCompilerError(msg)
        self._pre_compile(template)
        content = self._examine_content(template)
        self._compile(content)
        self._post_compile()
        del self.language
        return self.compiled_template

    def _apply_translations(self, translations, text):
        """Apply the translations to the text.

        Args:
            translations: A list of translations to use.
            text: The text to apply the translations.
        Returns:
            The text with the translations applied.
        """
        regex = hash_regex()
        return regex.sub(
            lambda m: translations.get(m.group(0), m.group(0)), text
        )

    def _compile(self, content):
        """Internal compile function.

        Subclasses must override this method, if they need to change
        the compile behavior.

        Args:
            content: The content (template) of the resource.
        """
        stringset = self._get_source_strings()
        existing_translations = self._tset()
        replace_translations = {}
        suffix = '_tr'
        for string in stringset:
            trans = self._visit_translation(
                self._tdecorator(existing_translations.get(string[0], u""))
            )
            replace_translations[string[1] + suffix] = trans
        content = self._apply_translations(replace_translations, content)
        self.compiled_template = content

    def _examine_content(self, content):
        """Peek into the template before any string is compiled."""
        return content

    def _get_source_strings(self):
        """Return the source strings of the resource."""
        return SourceEntity.objects.filter(
            resource=self.resource
        ).values_list(
            'id', 'string_hash', 'pluralized'
        ).order_by()

    def _visit_translation(self, s):
        """Have a chance to handle translation strings."""
        return s

    def _post_compile(self, content=None):
        """Do any work after the compilation process."""
        pass

    def _pre_compile(self, content=None):
        """Do any work before compiling the translation."""
        pass


class PluralCompiler(Compiler):
    """Compiler that handles plurals, too."""

    def _apply_translations(self, translations, text):
        """Apply the translations to the text.

        Args:
            translations: A list of translations to use.
            text: The text to apply the translations.
        Returns:
            The text with the translations applied.
        """
        regex = pluralized_hash_regex()
        return regex.sub(
            lambda m: translations.get(m.group(0), m.group(0)), text
        )

    def _compile(self, content):
        """Internal compile function.

        Subclasses must override this method, if they need to change
        the compile behavior.

        Args:
            content: The content (template) of the resource.
        """
        stringset = self._get_source_strings()
        existing_translations = self._tset()
        replace_translations = {}
        suffix = '_tr'
        plural_forms = self.language.get_pluralrules_numbers()
        for string in stringset:
            forms = existing_translations.get(string[0], {})
            if string[2]:       # is plural
                for index, form in enumerate(plural_forms):
                    trans = self._visit_translation(
                        self._tdecorator(forms.get(form, u""))
                    )
                    hash_key = string[1] + '_pl_' + str(index)
                    replace_translations[hash_key] = trans
            else:
                trans = self._visit_translation(
                    self._tdecorator(forms.get(5, u""))
                )
                replace_translations[string[1] + suffix] = trans
        content = self._update_plural_hashes(replace_translations, content)
        content = self._apply_translations(replace_translations, content)
        self.compiled_template = content

    def _pre_compile(self, content=None):
        """Set the translations builder to pluralized mode."""
        self._tset.pluralized = True

    def _update_plural_hashes(self, translations, content):
        """Create the necessary plural hashes to replace them later.

        Args:
            translations: A dictionary with the translations and the rules.
            content: The content to use.
        Returns:
            The content with all necessary plural hashes.
        """
        raise NotImplementedError
