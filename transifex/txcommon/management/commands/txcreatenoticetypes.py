import os
from django.core.management.base import NoArgsCommand
from notification import models as notification
from transifex.txcommon.notifications import NOTICE_TYPES

def create_notice_types():
    for n in NOTICE_TYPES:
        notification.create_notice_type(n["label"], n["display"],
                                        n["description"], n["default"])


class Command(NoArgsCommand):
    help = ('Create or Update the notice types used in the ActionLog and '
           'Notification apps')

    requires_model_validation = True
    can_import_settings = False

    def handle_noargs(self, **options):
        verbose = int(options.get('verbosity'))
        if verbose:
            self.stdout.write("Creating or updating notice types\n")
        create_notice_types()
        if verbose:
            self.stdout.write(
                "Default set of notice types initialized successfully.\n"
            )
