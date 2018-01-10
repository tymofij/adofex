# -*- coding: utf-8 -*-
from django.http import HttpResponseBadRequest
from django.utils.translation import ugettext as _

def reject_legacy_api(request, *args, **kwargs):
    return HttpResponseBadRequest(_("This version of API is obsolete. "\
            "Please have a look at %(url)s for details."
            ) % {'url': 'http://help.transifex.com/features/api/'\
                    'index.html#api-index' }
    )

