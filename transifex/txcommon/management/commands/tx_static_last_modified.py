# -*- coding: utf-8 -*-

"""
Set the datetime of the last update of static pages.
"""

from __future__ import absolute_import
import hashlib
from datetime import datetime
from optparse import make_option
from django.core.management.base import BaseCommand
from datastores.txredis import TxRedisMapper, redis_exception_handler
from ...utils import STATIC_CACHE_KEY_LAST_MODIFIED, STATIC_CACHE_KEY_ETAG


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option(
            '--datetime', default=datetime.utcnow(), dest='when',
            help='The datetime of the last update.'
        ),
    )
    help = 'Set the date and time, when static pages in Transifex were updated.'

    def handle(self, *args, **options):
        when = options.get('when')
        self._set_datetime_mark(when)

    @redis_exception_handler
    def _set_datetime_mark(self, when):
        """Set the datetime mark for static pages to when."""
        r = TxRedisMapper()
        r.set(STATIC_CACHE_KEY_LAST_MODIFIED, data=when)
        etag = hashlib.md5(when.isoformat()).hexdigest()
        r.set(STATIC_CACHE_KEY_ETAG, data=etag)


