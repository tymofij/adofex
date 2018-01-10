from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from transifex.txcommon.fields import UnicodeRegexField


help_text = _("Required. 30 characters or fewer. Unicode alphanumeric "
              "characters only (letters, digits and underscores).")

error_message = _("This value must contain only unicode letters, "
                  "numbers and underscores.")

# Overrides django.contrib.auth.forms.UserCreationForm and changes
# username to accept unicode character in the username.
class UserCreationForm(UserCreationForm):
    # The regex must be a string
    username = UnicodeRegexField(label=_("Username"), max_length=30,
        regex=u'^\w+$', help_text=help_text, error_message=error_message)

# Overrides django.contrib.auth.forms.UserChangeForm and changes
# username to accept unicode character in the username.
class UserChangeForm(UserChangeForm):
    # The regex must be a string
    username = UnicodeRegexField(label=_("Username"), max_length=30,
        regex=u'^\w+$', help_text=help_text, error_message=error_message)

class UserProfileAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'last_login',
        'date_joined', 'is_active', 'is_staff',)
    form = UserChangeForm
    add_form = UserCreationForm

admin.site.unregister(User)
admin.site.register(User, UserProfileAdmin)
