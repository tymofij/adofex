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

    def clean_xpifile(self):
        "Make sure that the uploaded file is a valid XPI file."
        xpifile = self.cleaned_data['xpifile']
        if xpifile:
            try:
                xpi = XPIManager(xpifile, name=xpifile.name)
                if xpi.test():
                    raise
            except:
                raise forms.ValidationError(_("File doesn't seem to be valid XPI"))
        return xpifile

    bzid = forms.IntegerField(label=_("Extension ID"), max_value=9999, required=False)
