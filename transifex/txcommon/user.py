# -*- coding: utf-8 -*-
"""
User related class and functions.
"""

from uuid import uuid4
from django.conf import settings
from django.contrib.auth.models import User
from userena.models import UserenaSignup
from social_auth.models import UserSocialAuth
from social_auth.backends import USERNAME
USERNAME_MAX_LENGTH = UserSocialAuth.username_max_length()


class CreateUserFromSocial(object):
    """Create local users from a social auth mechanism.

    Perform every step to create new users to the system. This is a
    wrapper around userena.
    """

    def __call__(self, *args, **kwargs):
        """Create a new user to Transifex.

        For now, this is copied from social_auth.backends.pipeline.user.
        """
        user = kwargs.get('user')
        if user is not None:
            return {'user': user}
        username = kwargs.get('username')
        if username is None:
            return None
        details = kwargs.get('details')
        if details is not None:
            email = details.get('email')
        user = UserenaSignup.objects.create_user(
            username, email, password=None, active=True, send_email=False
        )
        # Activate user automatically
        user = UserenaSignup.objects.activate_user(user.userena_signup.activation_key)
        return {'user': user, 'is_new': True}


create_user = CreateUserFromSocial()


class GetUsername(object):
    """Choose a username for socially authenticated users.

    This is a wrapper around social_auth.backends.pipeline.user.get_username.
    """

    def __call__(self, details, user=None, *args, **kwargs):
        """Get a new username.

        We check for existing usernames in a case-insensitive way.
        """
        if user:
            return {'username': user.username}

        if getattr(settings, 'SOCIAL_AUTH_FORCE_RANDOM_USERNAME', False):
            username = uuid4().get_hex()
        elif details.get(USERNAME):
            username = details[USERNAME]
        elif settings.hasattr('SOCIAL_AUTH_DEFAULT_USERNAME'):
            username = settings.SOCIAL_AUTH_DEFAULT_USERNAME
            if callable(username):
                username = username()
        else:
            username = uuid4().get_hex()

        uuid_lenght = getattr(settings, 'SOCIAL_AUTH_UUID_LENGTH', 16)
        username_fixer = getattr(settings, 'SOCIAL_AUTH_USERNAME_FIXER',
                                 lambda u: u)

        short_username = username[:USERNAME_MAX_LENGTH - uuid_lenght]
        final_username = None

        while True:
            final_username = username_fixer(username)[:USERNAME_MAX_LENGTH]

            try:
                User.objects.get(username__iexact=final_username)
            except User.DoesNotExist:
                break
            else:
                # User with same username already exists, generate a unique
                # username for current user using username as base but adding
                # a unique hash at the end. Original username is cut to avoid
                # the field max_length.
                username = short_username + uuid4().get_hex()[:uuid_lenght]
        return {'username': final_username}

get_username = GetUsername()
