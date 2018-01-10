import os
import glob
from django.core.management.base import CommandError, BaseCommand
from optparse import make_option
from django.core.management.commands.compilemessages import compile_messages

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--locale', '-l', default=None, dest='locale',
            help='The locale to process (e.g. pt_BR). Default is to process all.'),
    )
    help = "Compiles .po files to .mo files for use with builtin gettext support for Transifex."

    requires_model_validation = False
    can_import_settings = False

    def handle(self, *args, **options):
        locale = options.get('locale')

        # The hacking part is here
        if not locale:
            if os.path.isdir(os.path.join('conf', 'locale')):
                localedir = os.path.abspath(os.path.join('conf', 'locale'))
            elif os.path.isdir('locale'):
                localedir = os.path.abspath('locale')
            else:
                raise CommandError("This script should be run from the Transifex project tree.")

            # Only for directories under the locale dir, compile_messages
            locale_dirs = filter(os.path.isdir, glob.glob('%s/*' % localedir))
            for locale_dir in locale_dirs:
                locale = os.path.basename(locale_dir)
                compile_messages(self.stderr, locale)
        else:
            compile_messages(self.stderr, locale)
