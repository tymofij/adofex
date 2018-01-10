from django import forms

class ClaForm(forms.Form):
    cla_sign = forms.BooleanField('cla_sign')
