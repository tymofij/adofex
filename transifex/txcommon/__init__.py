import os

version_info = (1, 3, 0, 'devel')

_verpart = ''
if version_info[3] != 'final':
    _verpart = version_info[3]

version = '.'.join(str(v) for v in version_info[:3]) + _verpart

try:
    from mercurial import hg, ui
    # Take the revision of the updated/working none/changeset
    revision = 'r%s' % hg.repository(ui.ui(),
        __file__.split('/transifex/txcommon')[0])[None].parents()[0].rev()
except Exception:
    revision = ''

# A 'final' version should have its revision hidden even in the full version
if revision and _verpart:
    version_full = version + '-' + revision
else:
    version_full = version

del _verpart

def import_to_python(import_str):
    """Given a string 'a.b.c' return object c from a.b module."""
    mod_name, obj_name = import_str.rsplit('.', 1)
    obj = getattr(__import__(mod_name, {}, {}, ['']), obj_name)
    return obj
