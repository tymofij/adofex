# -*- coding: utf-8 -*-

"""
Redis backend.
"""

import cPickle as pickle
import functools
from redis import StrictRedis, ConnectionError
from django.conf import settings
from transifex.txcommon.log import logger


def redis_exception_handler(func):
    """Decorator to handle redis backend exceptions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConnectionError, e:
            logger.critical("Cannot connect to redis: %s" % e, exc_info=True)
        except Exception, e:
            logger.error("Error from redis: %s" % e, exc_info=True)
    return wrapper


class TxRedis(object):
    """Wrapper class around redis for Transifex."""

    def __init__(self, host=None, port=None, db=None):
        if host is None:
            host = settings.REDIS_HOST
        if port is None:
            port = settings.REDIS_PORT
        if db is None:
            db = settings.REDIS_DATABASE
        self._r = StrictRedis(host=host, port=port, db=db)

    def __getattr__(self, name):
        """Forward all method calls to redis."""
        return getattr(self._r, name)


class TxRedisMapper(TxRedis):
    """A redis wrapper which provides support for objects, too."""

    set_methods = ['set', 'lpush', 'rpush', ]
    get_methods = ['get', 'lrange', 'lpop',]

    def __getattr__(self, name):
        """Send all method calls to redis, while serializing arguments and
        results.

        Using pickle for (de)serialization. For argument serialization,
        he must provide the data in a dictionary named `data`.
        """
        attr = getattr(self._r, name)
        if name in self.set_methods:
            def new_attr(*args, **kwargs):
                if kwargs:      # argument serialization
                    data = pickle.dumps(kwargs.pop('data'))
                    args = list(args)
                    # value data almost always goes to the end
                    # override the other methods manually
                    args.append(data)
                return attr(*args, **kwargs)
            return functools.update_wrapper(new_attr, attr)
        elif name in self.get_methods:
            def new_attr(*args, **kwargs):
                res = attr(*args, **kwargs)
                if isinstance(res, basestring):
                    return pickle.loads(res)
                elif isinstance(res, list):
                    new_res = []
                    for r in res:
                        new_res.append(pickle.loads(r))
                    return new_res
                else:
                    return res
            return functools.update_wrapper(new_attr, attr)
        else:
            return super(TxRedisMapper, self).__getattr__(name)
