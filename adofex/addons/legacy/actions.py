# -*- coding: utf-8 -*-

from datetime import datetime
from legacy import models as legacy

from userena.models import UserenaSignup
from userena import signals as userena_signals
from userena import settings as userena_settings
from django.contrib.auth.models import User

from transifex.languages.models import Language

# sometimes people do register new accounts
# old_username -> new_username
NEW_USERNAMES = {
    'goofy': 'Goofy'
}

def migrate_user(username):
    """ Migrate given user to new system, or return existing one
    """
    new_username = NEW_USERNAMES.get(username, username)
    try:
        return User.objects.get(username=new_username)
    except User.DoesNotExist:
        pass
    u  = legacy.User.objects.get(username=username)
    user = UserenaSignup.objects.create_user(new_username,
                                            u.email,
                                            '',
                                            not userena_settings.USERENA_ACTIVATION_REQUIRED,
                                            userena_settings.USERENA_ACTIVATION_REQUIRED)
    user.first_name=u.name
    user.date_joined=datetime.fromtimestamp(u.date_joined_timestamp)
    user.last_login =datetime.fromtimestamp(u.last_login_timestamp)
    user.set_unusable_password()
    user.save()
    userena_signals.signup_complete.send(sender=None, user=user)
    return user

class LangLookup(object):
    """ Easy lookup for a language with given code
    """
    langs = {}

    @staticmethod
    def get(code):
        # FIXME: kinda duplicates Bundle._get_lang
        if code in LangLookup.langs:
            return LangLookup.langs[code]
        try:
            lang = Language.objects.get(code=code)
        except Language.DoesNotExist:
            try:
                # accept both '_' and '-' as separators
                lang = Language.objects.get(code=code.replace("_", "-").split("-")[0])
            except Language.DoesNotExist:
                print "Language {0} not found in TX".format(code)
                lang = None
        LangLookup.langs[code] = lang
        return lang