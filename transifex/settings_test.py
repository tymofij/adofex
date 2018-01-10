from settings import *

INSTALLED_APPS.remove('south')
LOGGING['loggers']['tx']['handlers'] = ['log_to_file',]

SOUTH_TESTS_MIGRATE = False
DISABLE_TRANSACTION_MANAGEMENT = True
ENABLE_NOTICES = True
NOTIFICATION_QUEUE_ALL = False