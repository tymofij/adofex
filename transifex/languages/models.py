from datetime import datetime
from django.contrib import admin
from django.db import models
from django.db.models import permalink, get_model
from django.core.cache import cache
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


class LanguageManager(models.Manager):
    def by_code_or_alias(self, code):
        """
        Return a language that matches either with the code or something
        inside the code_aliases field.
        """
        if not code:
            raise Language.DoesNotExist("No language matched the query.")
        lang = cache.get('languages:code_or_alias:%s' % code, None)
        if lang is None:
            lang = Language.objects.get(
                models.Q(code=code) |
                models.Q(code_aliases__contains=' %s ' % code)
            )
            cache.set('languages:code_or_alias:%s' % code, lang)
        return lang

    def by_code_or_alias_or_none(self, code):
        """
        Return a language that matches either with the code or something
        inside the code_aliases field. If no match is found return None.
        """
        try:
            return self.by_code_or_alias(code)
        except Language.DoesNotExist:
            return None

    def by_code_or_alias_or_404(self, code):
        """
        Return a language matches the code or something in code_aliases.

        If no match is found, raise a 404 exception.

        This method should be used in views.
        """
        try:
            return self.by_code_or_alias(code)
        except Language.DoesNotExist:
            raise Http404


class Language(models.Model):
    """
    A spoken language or dialect, with a distinct locale.
    """
    nplural_choices = ((0, u'unknown'), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6))

    name = models.CharField(_('Name'), unique=True, max_length=50,
        help_text="The name of the language including dialect, script, etc.")
    description = models.CharField(_('Description'), blank=True, max_length=255)
    code = models.CharField(_('Code'), unique=True, max_length=50,
        help_text=("The primary language code, used in file naming, etc."
                   "(e.g. pt_BR for Brazilian Portuguese.)"))
    code_aliases = models.CharField(_('Code aliases'), max_length=100,
        help_text=("A space-separated list of alternative locales."),
        null=True, blank=True, default='')
    specialchars = models.CharField(_("Special Chars"), max_length=255,
        help_text=_("Enter any special characters that users might find"
                    " difficult to type"),
        blank=True)
    nplurals = models.SmallIntegerField(_("Number of Plurals"), default=0,
        choices=nplural_choices)
    pluralequation = models.CharField(_("Plural Equation"), max_length=255,
        blank=True)

    # Plural rules
    rule_zero = models.CharField(_("Rule zero"), max_length=255,
        blank=True, null=True)
    rule_one = models.CharField(_("Rule one"), max_length=255,
        blank=True, null=True)
    rule_two = models.CharField(_("Rule two"), max_length=255,
        blank=True, null=True)
    rule_few = models.CharField(_("Rule few"), max_length=255,
        blank=True, null=True)
    rule_many = models.CharField(_("Rule many"), max_length=255,
        blank=True, null=True)
    rule_other = models.CharField(_("Rule other"), max_length=255,
        blank=False, null=False, default="everything")


    # Managers
    objects = LanguageManager()

    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.code)

    class Meta:
        verbose_name = _('language')
        verbose_name_plural = _('languages')
        #FIXME: Remove the 'translations' prefix.
        db_table  = 'translations_language'
        ordering  = ('name',)

    def save(self, *args, **kwargs):
        # It's needed to ensure that when we compare this field with the
        # 'contain' action, we will always take the whole alias for a
        # language, instead of part of it. We compare the alias with spaces
        # at the beginning and at the end of it.
        # TODO: check if alias does not already exist
        if not self.code_aliases.startswith(' '):
            self.code_aliases=' %s' % self.code_aliases
        if not self.code_aliases.endswith(' '):
            self.code_aliases='%s ' % self.code_aliases

        super(Language, self).save(*args, **kwargs)

    def get_rule_name_from_num(self, num):
        if num == 0:
            return 'zero'
        elif num == 1:
            return 'one'
        elif num == 2:
            return 'two'
        elif num == 3:
            return 'few'
        elif num == 4:
            return 'many'
        elif num == 5:
            return 'other'

    def get_rule_num_from_name(self, name):
        if name == 'zero':
            return 0
        elif name == 'one':
            return 1
        elif name == 'two':
            return 2
        elif name == 'few':
            return 3
        elif name == 'many':
            return 4
        elif name == 'other':
            return 5

    def get_pluralrules(self):
        rules=[]
        if self.rule_zero:
            rules.append('zero')
        if self.rule_one:
            rules.append('one')
        if self.rule_two:
            rules.append('two')
        if self.rule_few:
            rules.append('few')
        if self.rule_many:
            rules.append('many')
        rules.append('other')
        return rules

    def get_pluralrules_numbers(self):
        rules=[]
        if self.rule_zero:
            rules.append(0)
        if self.rule_one:
            rules.append(1)
        if self.rule_two:
            rules.append(2)
        if self.rule_few:
            rules.append(3)
        if self.rule_many:
            rules.append(4)
        rules.append(5)
        return rules


class LanguagesAsChoices(object):

    def __init__(self):
        self._cache = None

    def __call__(self):
        if self._cache is None:
            self._cache = [(l.code, l) for l in Language.objects.all()]
        return self._cache

language_choice_list = LanguagesAsChoices()

