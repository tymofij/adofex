# -*- coding: utf-8 -*-
from django.db.models.signals import post_save
from django.utils.translation import ugettext as _
from models import ResourcePriority
from transifex.resources.models import Resource
from transifex.txcommon.log import logger


def priority_creation(**kwargs):
    """Create the default priority on Resource creation."""
    if 'created' in kwargs and kwargs['created'] is True:
        resource = kwargs['instance']
        if resource:
            ResourcePriority.objects.create(resource=resource)
            logger.debug("Resource %s: New ResourcePriority created." % (
                         resource.name))


def connect():
    """Django-addons method to connect handlers to specific signals."""

    # Deletion is automatically done (django cascading deletes)
    # On new usersubscription creation.
    post_save.connect(priority_creation, sender=Resource)

