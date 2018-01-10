# -*- coding: utf-8 -*-

from django.test import TestCase
from datastores import TxRedisMapper
from transifex.txcommon.log import logger


class TestRedis(TestCase):

    def setUp(self):
        logger.critical("This will delete everything in db=1 i n redis.")
        self.r = TxRedisMapper(db=1)

    def tearDown(self):
        self.r.flushdb()

    def test_json_suffix(self):
        key = 'key'
        data = {'lang': 'en', 'code': 'en'}
        res = self.r.lpush(key, data=data)
        self.assertEquals(res, 1)
        res = self.r.lpop(key)
        self.assertEquals(res, data)
