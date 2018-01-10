
"""
Logging receivers for signals by models, etc.
"""

def model_named(sender, message='', **kwargs):
    """
    Receive signals for objects with a .name attribute.
    """
    from txcommon.log import logger
    obj = kwargs['instance']
    logger.debug("%(msg)s %(obj)s %(name)s" %
                 {'msg': message,
                  'obj': sender.__name__,
                  'name': getattr(obj, 'name', '')})

def pre_save_named(sender, **kwargs):
    model_named(sender, message='About to save:', **kwargs)

def post_save_named(sender, **kwargs):
    model_named(sender, message='Saved:', **kwargs)

def pre_delete_named(sender, **kwargs):
    model_named(sender, message='About to delete:', **kwargs)

def post_delete_named(sender, **kwargs):
    model_named(sender, message='Deleted:', **kwargs)
