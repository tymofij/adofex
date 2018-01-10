# -*- coding: utf-8 -*-

from django import forms
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.conf import settings
from transifex.projects.signals import project_created, project_deleted, \
        project_form_init, post_proj_save_m2m


def delete_gtranslate(sender, **kwargs):
    """
    Delete a Gtranslate object after its corresponding projet has been deleted.
    """
    GtModel = get_model('gtranslate', 'Gtranslate')
    try:
        gt = GtModel.objects.get(project=sender)
        gt.delete()
    except GtModel.DoesNotExist, e:
        pass


def add_auto_translate_field(sender, **kwargs):
    """Add the field for the API key in project edit form."""
    form = kwargs['form']
    project = form.instance

    GtModel = get_model('gtranslate', 'Gtranslate')
    try:
        auto_translate = GtModel.objects.get(project=project)
        api_key = auto_translate.api_key
        choice = auto_translate.service_type
    except GtModel.DoesNotExist:
        api_key = ''
        choice = ''

    form.fields['auto_translate_select_service'] = forms.ChoiceField(
        choices=GtModel.available_services, required=False,
        label=_("Auto Translate Service"), initial=choice,
        help_text=_(
            "Select the type of service you want to use for the "
            "auto-translate service. Leave it blank, if you do not "
            "want to have the feature enabled. You will have to insert "
            "your API key for the service, too."
        )
    )
    form.fields['auto_translate_api_key'] = forms.CharField(
        max_length=255, required=False, label=_("Auto Translate API Key"),
        initial=api_key, help_text=_(
            "Enter the API key that Transifex will use for the auto-translate "
            "service you have chosen."
        )
    )

    old_clean = getattr(form, "clean", None)
    def new_clean():
        service_type = form.cleaned_data['auto_translate_select_service']
        api_key = form.cleaned_data['auto_translate_api_key']
        if service_type and not api_key:
            raise ValidationError(_("You have to select an API key, too."))
        elif not service_type and api_key:
            raise ValidationError(_(
                "You have to select a service for the auto-translate "
                "feature, too."
            ))
        if old_clean:
            return old_clean()
        else:
            return form.cleaned_data
    form.clean = new_clean


def save_auto_translate(sender, **kwargs):
    """Save a web hook, after saving a project (if defined)."""
    GtModel = get_model('gtranslate', 'Gtranslate')
    project = kwargs['instance']
    form = kwargs['form']
    service_type = form.cleaned_data['auto_translate_select_service']
    api_key = form.cleaned_data['auto_translate_api_key']

    if service_type and api_key:
        try:
            auto_translate, created = GtModel.objects.get_or_create(
                project=project
            )
            auto_translate.service_type = service_type
            auto_translate.api_key = api_key
            auto_translate.save()
        except Exception, e:
            msg = "Error saving auto-translate service for project %s: %s"
            logger.error(msg % (project, e))
    else:
        try:
            auto_translate = GtModel.objects.get(project=project)
            auto_translate.delete()
        except GtModel.DoesNotExist:
            pass


def connect():
    project_deleted.connect(delete_gtranslate)
    project_form_init.connect(add_auto_translate_field)
    post_proj_save_m2m.connect(save_auto_translate)
