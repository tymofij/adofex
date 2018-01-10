import logging
from django.db.models import get_app
from django.db.models.signals import *
from django.conf import settings

"""
Standard logging facilities for Transifex applications.

To use the common logger, use something like the following::

  from txcommon.log import logger
  logger.debug("foo")
"""

_logger = logging.getLogger('tx')


def log_model(model):
    """
    Register standard receivers for a model with a 'name' attribute.

    Called after the declaration of a model in ``models.py``. Eg.:

    >>> from txcommon.log import log_model
    >>> from django import models
    >>> class Person(models.Model):
    ...     pass
    >>> log_model(Person)

    """

    from transifex.txcommon.log.receivers import post_save_named, post_delete_named
    if model:
        #logger.debug("Registered logging for model %s" % model.__name__)
        post_save.connect(post_save_named, sender=model)
        post_delete.connect(post_delete_named, sender=model)

# We still require logger to be a module-level variable
logger = _logger
