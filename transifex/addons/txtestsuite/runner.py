from django.test.simple import DjangoTestSuiteRunner
from django.core import management
from django.db import (connections, DEFAULT_DB_ALIAS)

fixtures = ["sample_users", "sample_site", "sample_languages", "sample_data"]

class TxTestSuiteRunner(DjangoTestSuiteRunner):
    def setup_test_environment(self, **kwargs):
        super(TxTestSuiteRunner, self).setup_test_environment(**kwargs)

    def teardown_test_environment(self, **kwargs):
        super(TxTestSuiteRunner, self).teardown_test_environment(**kwargs)

    def setup_databases(self, **kwargs):
        return_val = super(TxTestSuiteRunner, self).setup_databases(**kwargs)
        databases = connections
        for db in databases:
            management.call_command('loaddata', *fixtures,
                    **{'verbosity': 0, 'database': db})
        return return_val

