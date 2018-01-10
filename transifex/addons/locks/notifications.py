# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_noop as _
from transifex.txcommon.notifications import NOTICE_TYPES

# TODO: Move to signal based architecture
#       This would make heavy use of underlying database
#       and require modifications for Notice model
#       (the "show_to_user" field is missing)
#       Signal based architecture would be much better
#       For addons system also

NOTICE_TYPES += [
            {
                "label": "project_resource_language_lock_expiring",
                "display": _("Lock expiration"),
                "description": _("when a lock for a translation resource will "
                    "expire"),
                "default": 0,
                "show_to_user": True,
            },
]
