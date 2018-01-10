# -*- coding: utf-8 -*-
import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.fields.related import OneToOneField
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _

import tagging
from tagging.fields import TagField
from tagging_autocomplete.models import TagAutocompleteField

from transifex.txcommon.log import logger
from userena import settings as userena_settings
from userena.models import UserenaBaseProfile

from social_auth.signals import pre_update
from social_auth.backends.twitter import TwitterBackend
from social_auth.backends.contrib.linkedin import LinkedinBackend
from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["tagging_autocomplete.models.TagAutocompleteField"])

Language = models.get_model('languages', 'Language')

class Profile(UserenaBaseProfile):
    """
    Profile class to used as a base for the django-profile app
    """
    user = models.OneToOneField(User, unique=True, verbose_name=_('user'),
        related_name='profile')

    languages = models.ManyToManyField(Language, verbose_name=_('Languages'),
        blank=True, null=True)
    tags = TagAutocompleteField(verbose_name=_('Interested in'), blank=True,
            null=True, help_text=_("Tags you may be interested in."))
    blog = models.URLField(_('Blog'), null=True, blank=True)
    linked_in = models.URLField(_('LinkedIn'), null=True, blank=True)
    twitter = models.URLField(_('Twitter'), null=True, blank=True)
    about = models.TextField(_('About yourself'), max_length=140, null=True,
        blank=True,
        help_text=_('Short description of yourself (140 chars).'))
    looking_for_work = models.BooleanField(_('Looking for work?'),
        default=False)

    latitude = models.DecimalField(max_digits=10, decimal_places=6,
        null=True, blank=True, editable=False)
    longitude = models.DecimalField(max_digits=10, decimal_places=6,
        null=True, blank=True, editable=False)
    location = models.CharField(_("Location"), max_length=255, null=True, blank=True,
        editable=True)

    class Meta:
        db_table = 'txcommon_userenaprofile'

    def language_codes(self):
        ''' returns list of languages spoken by that user
        '''
        return self.languages.all().values_list('code', flat=True)

try:
    tagging.register(Profile, tag_descriptor_attr='tagsobj')
except tagging.AlreadyRegistered, e:
    logger.debug('Tagging: %s' % str(e))

def exclusive_fields(inmodel, except_fields=[]):
    '''
    Returns a generator that yields the fields that belong only to the
    given model descendant

    ``except_fields`` is a list that allows to skip some fields based on theirs
    names
    '''
    for field, model in inmodel._meta.get_fields_with_model():
        if field.name in except_fields:
            yield field
        # Field belongs to an ancestor
        if model is not None:
            continue
        # Field relates to an ancestor
        if isinstance(field, OneToOneField) and (field.rel.to in
            inmodel.__bases__):
            continue
        yield field

def inclusive_fields(inmodel, except_fields=[]):
    '''
    Returns a generator that yields the fields that belong to the given
    model descendant or any of its ancestors

    ``except_fields`` is a list that allows to skip some fields based on theirs
    names
    '''
    for field, model in inmodel._meta.get_fields_with_model():
        # Field relates to the parent of the model it's on
        if isinstance(field, OneToOneField):
            # Passed model
            if (model is None) and (field.rel.to in inmodel.__bases__):
                continue
            # Ancestor model
            if (model is not None) and (field.rel.to in model.__bases__):
                continue
        if field.name in except_fields:
            continue
        yield field

# Signal Registration
import listeners
post_save.connect(listeners.add_user_to_registered_group, sender=User)

pre_update.connect(listeners.twitter_profile_values, sender=TwitterBackend)
pre_update.connect(listeners.linkedin_profile_values, sender=LinkedinBackend)
