# -*- coding: utf-8 -*-

from django.conf import settings

try:
    ENABLE_TXTESTSUITE = settings.ENABLE_TXTESTSUITE
except Exception, e:
    ENABLE_TXTESTSUITE = False

if ENABLE_TXTESTSUITE:
    from transifex.addons.txtestsuite.tests.base2 import *
else:
    from transifex.txcommon.tests.base_legacy import *
