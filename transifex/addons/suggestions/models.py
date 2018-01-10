# -*- coding: utf-8 -*-

from hashlib import md5
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from transifex.languages.models import Language
from transifex.resources.models import Resource, SourceEntity


class Suggestion(models.Model):
    """
    The representation of a suggestion for a translation on a source string.

    More or less it is a duplication of the Translation model with a different
    way to determine the unique instances.
    """

    string = models.TextField(_('String'), blank=False, null=False,
        help_text=_("The actual string content of suggestion."))
    string_hash = models.CharField(_('String Hash'), blank=False, null=False,
        max_length=32, editable=False,
        help_text=_("The hash of the suggestion string used for indexing"))
    score = models.FloatField(_('Score Value'), default=0, blank=True,
        help_text=_("A value which indicates the relevance of this suggestion"
                    " to the translation of the source string."))

    # Timestamps
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_update = models.DateTimeField(auto_now=True, editable=False)

    # Foreign Keys
    source_entity = models.ForeignKey(SourceEntity,
        verbose_name=_('Source Entity'), blank=False, null=False,
        related_name='suggestions',
        help_text=_("The source entity this suggestion instance"
                    " translates or affects."))

    language = models.ForeignKey(Language,
        verbose_name=_('Target Language'), blank=False, null=True,
        help_text=_("The language in which this translation string is written."))

    user = models.ForeignKey(User,
        verbose_name=_('User'), blank=False, null=True,
        help_text=_("The user who committed the specific suggestion."))

    def __unicode__(self):
        return self.string

    class Meta:
        unique_together = ('source_entity', 'language', 'string_hash',)
        verbose_name = _('suggestion')
        verbose_name_plural = _('suggestions')
        ordering  = ('-score',)
        order_with_respect_to = 'source_entity'
        get_latest_by = "created"

    def vote_up(self, user):
        try:
            existing_vote = self.votes.get(user=user)
            if existing_vote.vote_type == False:
                existing_vote.delete()
                self.score += 1
                self.save()
        except Vote.DoesNotExist:
            vote = self.votes.create(user=user, vote_type=True)
            self.score += 1
            self.save()


    def vote_down(self, user):
        try:
            existing_vote = self.votes.get(user=user)
            if existing_vote.vote_type == True:
                existing_vote.delete()
                self.score -= 1
                self.save()
        except Vote.DoesNotExist:
            vote = self.votes.create(user=user, vote_type=False)
            self.score -= 1
            self.save()


    def get_vote_or_none(self, user):
        try:
            self.votes.get(user=user)
        except Vote.DoesNotExist:
            return None

    @property
    def score_rounded(self):
        """Return a nice, rounded (integer) version of the score."""
        return int(self.score)

    def save(self, *args, **kwargs):
        # Encoding happens to support unicode characters
        self.string_hash = md5(self.string.encode('utf-8')).hexdigest()
        super(Suggestion, self).save(*args, **kwargs)


class Vote(models.Model):
    """
    A user vote for a suggestion.
    """
    suggestion = models.ForeignKey(Suggestion,
        verbose_name=_('Suggestion'), blank=False, null=False,
        related_name='votes',
        help_text=_("The suggestion about which the user is voting."))
    user = models.ForeignKey(User,
        verbose_name=_('User'), blank=False, null=False,
        related_name='votes',
        help_text=_("The user who voted for the specific suggestion."))

     # False = -1, True = +1
    vote_type = models.BooleanField()

    # Timestamps
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_update = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        unique_together = (('suggestion', 'user'))
        verbose_name = _('vote')
        verbose_name_plural = _('votes')

