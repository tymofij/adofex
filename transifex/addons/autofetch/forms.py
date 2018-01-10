from django import forms
from autofetch.models import URLInfo


class URLInfoForm(forms.ModelForm):
    class Meta:
        model = URLInfo
        fields = ('source_file_url','auto_update', )

