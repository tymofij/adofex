class LegacyRouter(object):
    """To avoid all those .using() clauses
    """
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'legacy':
            return 'legacy'

    def allow_syncdb(self, db, model):
        if db == 'legacy':
            return model._meta.app_label == 'legacy'
        elif model._meta.app_label == 'legacy':
            return False
