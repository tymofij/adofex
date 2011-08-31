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

# Monkeypatching to style helptext, not needed since django 1.3
major, minor = django.get_version().split('.')[:2]
if int(major) == 1 and int(minor) < 3:
    def as_ul_helptext(self):
        "Returns this form rendered as HTML <li>s -- excluding the <ul></ul>."
        return self._html_output(
            normal_row = u'<li%(html_class_attr)s>%(errors)s%(label)s %(field)s%(help_text)s</li>',
            error_row = u'<li>%s</li>',
            row_ender = '</li>',
            help_text_html = u' <span class="helptext">%s</span>',
            errors_on_separate_row = False)

    from django.forms import BaseForm
    BaseForm.as_ul = as_ul_helptext

if __name__ == "__main__":
    execute_manager(settings)
