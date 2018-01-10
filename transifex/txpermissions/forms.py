from django.utils.translation import ugettext_lazy as _

from ajax_select.fields import AutoCompleteField, AutoCompleteWidget
from authority.forms import UserPermissionForm


class UserAjaxPermissionForm(UserPermissionForm):
    """
    A class for building a permission form using an ajax autocomplete field.

    This class mimics the functionality of UserPermissionForm in django
    authority application, but instead of a Charfield for user field, uses
    an AutoCompleteField as specified by ajax_select application. Usernames
    are retrieved asynchronously with ajax calls and filling of the input field
    occurs with an automatic way.
    """

    user = AutoCompleteField('users', required=True, label=_('User'),
        help_text=_('Search for a username'))
