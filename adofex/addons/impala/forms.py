# -*- coding: utf-8 -*-
import os, zipfile

from django.conf import settings
from django import forms
from django.utils.translation import ugettext as _
from validator.xpi import XPIManager

class ImportForm(forms.Form):
    """
    Form to handle uploads (.xpi files) and Babelzilla IDs
    """
    xpifile = forms.FileField(label=_("XPI File"), required=False)
    bzid = forms.IntegerField(label=_("Extension ID"), max_value=9999, required=False)

class MessageForm(forms.Form):
    """
    Form to send messages to the people watching the project
    """
    subject = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea)

from userena.forms import EditProfileForm as UserenaEditProfileForm
from userena.utils import get_profile_model

class EditProfileForm(UserenaEditProfileForm):
    def __init__(self, *args, **kw):
        super(forms.ModelForm, self).__init__(*args, **kw)

    def clean_tags(self):
        user_tags_list = self.cleaned_data['tags']
        tags = list(set([tag.strip() for tag in user_tags_list.split(',')])) or []
        for i in tags:
            if not i.strip():
                tags.remove(i)
        tags.append(u'')
        user_tags_list = ', '.join(tags)
        return user_tags_list

    class Meta:
        model = get_profile_model()
        exclude = ('user', 'privacy', 'mugshot', )
        fields = (
            'first_name', 'last_name', 'location', 'languages', 'tags', 'blog',
            'twitter', 'about'
        )