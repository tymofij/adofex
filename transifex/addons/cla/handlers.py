from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from django.contrib import messages
from cla.models import Cla, ClaSignature
from transifex.projects.forms import ProjectAccessControlForm
from transifex.projects.signals import pre_team_request, pre_team_join, cla_create, project_access_control_form_start, ClaNotSignedError

def handle_pre_team(sender, **kwargs):
    project = kwargs['project']
    user = kwargs['user']
    cla_sign = kwargs['cla_sign']
    try:
        cla = project.cla
        if cla_sign:
            ClaSignature(cla=cla, user=user).save()
        try:
            cla.clasignature_set.get(user=user)
        except ClaSignature.DoesNotExist, e:
            raise ClaNotSignedError
    except Cla.DoesNotExist, e:
        pass

def handle_cla_create(sender, **kwargs):
    project = kwargs['project']
    license_text = kwargs['license_text']
    request = kwargs['request']
    if license_text:
        try:
            cla = Cla.objects.get(project=project)
            if license_text != cla.license_text:
                cla.license_text = license_text
                cla.save()
                messages.success(request, _(
                    "You have updated this project's CLA."
                ))
        except Cla.DoesNotExist, e:
            Cla(project=project, license_text=license_text).save()
            messages.success(request, _(
                "You have added a CLA to this project."
            ))
    else:
        try:
            project.cla.delete()
            messages.success(request, _(
                "You have deleted this project's CLA."
            ))
        except Cla.DoesNotExist, e:
            pass

def handle_project_access_control_form_start(sender, **kwargs):
    form = kwargs['instance']
    project = kwargs['project']
    form.fields['cla_enable'] = forms.BooleanField(
        help_text=_("Enforce a CLA for this project"),
        required=False
    )
    form.fields['cla_license_text'] = forms.CharField(
        help_text=_("License text"),
        required=False,
        widget=forms.widgets.Textarea(attrs={'cols': "80", 'rows': "10"})
    )
    if project:
        try:
            cla = project.cla
            form.fields['cla_enable'].initial = True
            form.fields['cla_license_text'].initial = cla.license_text
        except Cla.DoesNotExist, e:
            pass

    def get_clean_cla_license_text_method(form):
        def clean_cla_license_text():
            if 'cla_enable' in form.data and \
                    form.cleaned_data['cla_enable'] and \
                    not form.cleaned_data['cla_license_text']:
                raise ValidationError(u'This field is required.')
            if 'cla_enable' not in form.data or \
                    not form.cleaned_data['cla_enable']:
                return u''
            return form.cleaned_data['cla_license_text']
        return clean_cla_license_text
    form.clean_cla_license_text = get_clean_cla_license_text_method(form)

def connect():
    pre_team_request.connect(handle_pre_team)
    pre_team_join.connect(handle_pre_team)
    cla_create.connect(handle_cla_create)
    project_access_control_form_start.connect(
        handle_project_access_control_form_start,
        sender=ProjectAccessControlForm
    )
