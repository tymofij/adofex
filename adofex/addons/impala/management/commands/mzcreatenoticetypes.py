import os
from django.core.management.base import NoArgsCommand
from notification import models as notification
from django.utils.translation import ugettext_noop as _

NOTICE_TYPES = [
            {
                "label": "project_message",
                "display": _("Project message"),
                "description": _("when a project sends messages to its watchers"),
                "default": 2,
                "show_to_user": True,
            },
        ]

class Command(NoArgsCommand):
    help = ('Create or Update the notice types used in Notification apps')

    requires_model_validation = True
    can_import_settings = False

    def handle_noargs(self, **options):
        self.stdout.write("Adofex-specific notice types\n")
        for n in NOTICE_TYPES:
            self.stdout.write("Creating %s\n" % n["label"])
            notification.create_notice_type(n["label"], n["display"],
                                            n["description"], n["default"])
        self.stdout.write("Default set of notice types initialized successfully.\n")
