from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import ugettext as _

class RememberMeAuthForm(AuthenticationForm):
    """Form for adding an extra 'remember me' field."""
    remember_me = forms.BooleanField(label=_("Remember me"),
    widget=forms.CheckboxInput, required=False)

