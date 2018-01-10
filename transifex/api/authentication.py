import binascii
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth import authenticate
from piston.authentication import HttpBasicAuthentication

class CustomHttpBasicAuthentication(HttpBasicAuthentication):
    """
    Basic Http Authenticator that also checks if the user is currently
    registered with Django.
    """

    def is_authenticated(self, request):
        auth_string = request.META.get('HTTP_AUTHORIZATION', None)

        if auth_string:

            try:
                (authmeth, auth) = auth_string.split(" ", 1)

                if not authmeth.lower() == 'basic':
                    return False

                auth = auth.strip().decode('base64')
                (username, password) = auth.split(':', 1)
            except (ValueError, binascii.Error):
                return False


            request.user = self.auth_func(username=username, password=password) \
                or AnonymousUser()

        return not request.user in (False, None, AnonymousUser())
