from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (logout as auth_logout,
                                       login as auth_login)

from transifex.simpleauth.forms import RememberMeAuthForm
from transifex.simpleauth.util import clean_next


@login_required
def logout(request, template_name='simpleauth/logged_out.html'):
    """Logout the user from the website and redirect back."""
    next = clean_next(request.GET.get('next'))
    auth_logout(request, next_page=next, template_name=template_name)
    return HttpResponseRedirect(next)


def login(request, template_name='simpleauth/signin.html'):
    """Login the user to the website and redirect back."""
    next = clean_next(request.GET.get('next'))
    
    if request.user.is_authenticated():
        return HttpResponseRedirect(next)
    
    try:
        if request.POST['remember_me'] == 'on':
            # By default keep the user logged in for 3 weeks
            login_duration = getattr(settings, 'LOGIN_DAYS', 21) * 60 * 60 * 24
    except:
        login_duration = 0
    request.session.set_expiry(login_duration)
    return auth_login(request, template_name=template_name,
                      redirect_field_name='next',
                      authentication_form=RememberMeAuthForm)


@login_required
def account_settings(request, template_name='simpleauth/settings.html'):
    """Account settings page."""
    msg = request.GET.get('msg', '')
    return render_to_response(template_name,
                  {'msg': msg,},
                  context_instance=RequestContext(request))

def profile_public(request, username, template_name='simpleauth/profile_public.html'):
    """Public profile page."""
    user = get_object_or_404(User, username=username)
    return render_to_response(template_name,
                  {'user': user,},
                  context_instance=RequestContext(request))

