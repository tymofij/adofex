import re
from datetime import date
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned

from transifex.languages.models import Language
from transifex.resources.models import Resource


class CopyrightManager(models.Manager):
    def assign(self, language, resource, owner, year=None, user=None):
        """Add copyright for a specific year to an object.

        If there is no copyright object, create. Otherwise, update if
        necessary.

        Should be called from Copyright.objects. Calling it from related models
        won't work.
        """

        if year is None:
            year = date.today().year
        if user is None:
            # Find if the email is registered to the db
            email = re.search('<(.*?)>', owner)
            if email is not None and email.group(1):
                try:
                    user = User.objects.get(email=email.group(1))
                except User.DoesNotExist, e:
                    pass
                except MultipleObjectsReturned:
                    users = User.objects.filter(email=email.group(1))
                    for u in users:
                        if u.first_name and u.last_name:
                            user = u
                            break
                        user = u

        #FIXME: Make this work with foreign-key calls, for example:
        #       tresource.objects.assign(owner=, year=)
        _qs = super(CopyrightManager, self).get_query_set()
        copyright, created = _qs.get_or_create(
            owner=owner, language=language, resource=resource,
            defaults={'years': year}
        )
        if not created:
            # Copyright exists, let's update it
            years = copyright.years.split(',')
            if not year in years:
                years.append(year)
                copyright.years = ','.join(sorted(years))

        # User must be separately created, to that get_or_create works
        copyright.user = user
        copyright.save()

        return copyright


class Copyright(models.Model):
    """A model holding copyrights.

    This should be representing a statement such as:
    # John Doe <jhon@doe.org> 2014.

    Years are stored in a CommaSeparatedIntegerField.
    """

    # The copyright owner. We don't make this a foreign key, since
    # it might or might not be a user in our database.
    owner = models.CharField(_('Owner'), max_length=255,
        help_text=_("The copyright owner in text form."))

    # The copyright owner, in case the assignment is happening inside Tx.
    # No reason to use this -- only for backup purposes.
    user = models.ForeignKey(User, blank=True, null=True,
        related_name='copyrights',
        verbose_name=_('User'),
        help_text=_("The Transifex user who owns the copyright, if applicable."))

    language = models.ForeignKey(
        Language, verbose_name=_("Language"),
        help_text=_("Language of the translation.")
    )

    resource = models.ForeignKey(
        Resource, verbose_name=_("Resource"),
        help_text = _("The resource this copyright is on.")
    )

    years = models.CommaSeparatedIntegerField(_('Copyright years'),
        max_length=80,
        help_text=_("The years the copyright is active in."))

    comment = models.CharField(_('Comment'),
        max_length=255,
        help_text=_("A comment for this copyright."),)

    IMPORT_CHOICES = (
        ('T', 'Transifex (Lotte/API)'),
        ('P', 'Po files'),
    )
    imported_by = models.CharField(
        max_length=1, choices=IMPORT_CHOICES,
        null=True, blank=True,
        verbose_name=_("Imported by"),
        help_text=_("How this copyright notice was created.")
    )

    # De-normalized fields

    # Store the years in a concise form. Responsible to convert years
    # 2010, 2011, 2012, 2013 to 2010-2013.
    years_text = models.CharField(_('Copyright Years Text'),
        max_length=50,
        help_text=_("Textual representation of the copyright years."))

    # Timestamps
    created = models.DateTimeField(auto_now_add=True, editable=False)
    last_update = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        unique_together = (('language', 'resource', 'owner'), )

    def __unicode__(self):
        return u'%(years)s %(owner)s' % {
            'years': self.years_text,
            'owner': self.owner
        }

    def __str__(self):
        return (u'%(owner)s, %(years)s.' % {
            'years': str(self.years_text),
            'owner': self.owner
        }).encode('UTF-8')

    def save(self, *args, **kwargs):
        """Override save to de-normalize the years_text."""
        self.years_text = self._compress_years(self.years)
        super(Copyright, self).save(*args, **kwargs)

    def _compress_years(self, years):
        #FIXME: Convert list of years to list of year periods
        # ie. 2010,2011,2012 to 2010-2012.
        return ", ".join(years.split(','))


    objects = CopyrightManager()

