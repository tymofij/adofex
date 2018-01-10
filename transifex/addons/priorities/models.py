# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _

from transifex.resources.models import Resource

PRIORITY_LEVELS = (
    ('0', _('Normal')),
    ('1', _('High')),
    ('2', _('Urgent')),
)


class ResourcePriority(models.Model):
    """
    A priority level associated with one Resource item.
    """
    resource = models.OneToOneField(Resource, related_name='priority',
        help_text=_("The resource associated with this priority."))
    level = models.CharField(_('Priority Levels'),
        max_length=1, choices=PRIORITY_LEVELS, default='0',
        help_text=_("The priority levels, indicating the importance of "
                    "completing translations for the resource."))

    def __unicode__(self):
        return u'%s' % (self.get_level_display(),)

    def __repr__(self):
        return u'<ResourcePriority: %s>' % (self.get_level_display(),)

    @property
    def display_level(self):
        return self.get_level_display()

    class Meta:
        verbose_name = _('resource priority')
        verbose_name_plural = _('resource priorities')

    def cycle(self):
        """Cycle through the states of the priority object."""
        self.level = str((int(self.level) + 1) % int(len(PRIORITY_LEVELS)))
        self.save()


def level_display(level):
    """Return the display name for the specified level."""
    for lvl, name in PRIORITY_LEVELS:
        if lvl == level:
            return name
