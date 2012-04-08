#!/usr/bin/env python
import django
from django.core.management import execute_manager, setup_environ

try:
    import settings # Assumed to be in the same directory.
except ImportError:
    import os
    import sys

    dname = os.path.dirname(__file__)
    sfile = 'settings.py'
    err = sys.stderr.write

    err("ERROR: Cannot locate `%s/%s'\n" % (dname, sfile))
    err("Please re-run `django-admin.py' on the appropriate `%s' file.\n" % sfile)
    sys.exit(1)

# lets settle up
setup_environ(settings)

if __name__ == "__main__":
    execute_manager(settings)
