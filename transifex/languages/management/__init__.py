
from django.db.models import signals, get_model
#from transifex.languages import models as lang_app

Language = get_model('languages', 'Language')

def create_languages(app, created_models, verbosity, **kwargs):
    from django.core.management import call_command
    if Language in created_models and kwargs.get('interactive', True):
        msg = ("\nTransifex's language tables were just initialized.\n"
               "Would you like to populate them now with a standard set of "
               "languages? (yes/no): ")
        confirm = raw_input(msg)
        while 1:
            if confirm not in ('yes', 'no'):
                confirm = raw_input('Please enter either "yes" or "no": ')
                continue
            if confirm == 'yes':
                call_command("txlanguages", interactive=True)
            break

# South's migrate does not accept a --noinput flag. Because we want to be able
# to call these in a non-interactive way, we're disabling it for now and asking
# the user installing Tx to call txcreatelanguages manually.
#signals.post_syncdb.connect(create_languages,
#    sender=lang_app, dispatch_uid = "languages.management.create_languages")
