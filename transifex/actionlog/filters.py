from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

import django_filters
from actionlog.models import LogEntry
from ajax_select.fields import AutoCompleteSelectWidget

class LogEntryFilter(django_filters.FilterSet):
    action_time = django_filters.DateRangeFilter()
    user = django_filters.ModelChoiceFilter(queryset=User.objects.all(),
        widget=AutoCompleteSelectWidget('users'),
        help_text=_('Search for a username or leave it blank'))

    class Meta:
        model = LogEntry
        fields = ['user', 'action_type', 'action_time']
