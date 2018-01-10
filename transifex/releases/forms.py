from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from ajax_select.fields import AutoCompleteSelectMultipleField
from transifex.resources.models import Resource
from transifex.releases.models import Release
from transifex.releases import RELEASE_ALL_DATA, RESERVED_RELEASE_SLUGS

class ReleaseForm(forms.ModelForm):

    resources = AutoCompleteSelectMultipleField('resources', required=True,
        help_text=_('Search for a resource'))

    # FIXME: Weird, the following message should be displayed by default, but
    # it was necessary to make it explicit here be able to display the correct
    # 'invalid' message for datetime fields, which has a suggestion of the
    # format to be used.
    error_messages = {'invalid': _('Enter a valid date/time in '
        'YYYY-MM-DD HH:MM[:ss[.uuuuuu]] format.')}
    release_date = forms.DateTimeField(required=False,
        error_messages=error_messages)
    stringfreeze_date = forms.DateTimeField(required=False,
        error_messages=error_messages)
    develfreeze_date = forms.DateTimeField(required=False,
        error_messages=error_messages)

    class Meta:
        model = Release

    def __init__(self, project, user, *args, **kwargs):
        super(ReleaseForm, self).__init__(*args, **kwargs)
        projects = self.fields["project"].queryset.filter(slug=project.slug)
        self.fields["project"].queryset = projects
        self.fields["project"].empty_label = None
        self.user = user

        if not project.is_hub:
            queryset = Resource.objects.filter(project=project)
            self.fields["resources"] = forms.ModelMultipleChoiceField(
                queryset=queryset, required=True, 
                help_text=_('Select the resources to add to the Release. '
                    'Once this project is not a Project Hub, it is only '
                    'possible to choose resources that belong to this '
                    'project.'))

    def clean_resources(self):
        resources_list = self.cleaned_data['resources']
        for resource in resources_list:
            if not isinstance(resource, Resource):
                try:
                    resource = Resource.objects.select_related().get(pk=int(resource))
                except Resource.DoesNotExist, e:
                    raise ValidationError(_("Invalid resource used."))
            if resource.project.private:
                if self.user not in resource.project.maintainers.all():
                    raise ValidationError(
                     _("%s is an inaccessible private resource. "
                       "Remove it!" % resource.name)
                    )
        return resources_list

    def clean_slug(self):
        """Ensure that reserved slugs are not used."""
        slug = self.cleaned_data['slug']
        if slug in RESERVED_RELEASE_SLUGS:
            raise ValidationError(_("This value is reserved and cannot be used."))
        return slug

    def clean(self):
        """Check whether the dates of the release are valid."""
        cleaned_data = self.cleaned_data
        stringfreeze_date = cleaned_data.get('stringfreeze_date')
        develfreeze_date = cleaned_data.get('develfreeze_date')
        release_date = cleaned_data.get('release_date')

        if develfreeze_date and stringfreeze_date and \
            develfreeze_date <= stringfreeze_date:
            msg = _("Devel freeze date must be after the String freeze date.")
            self._errors["develfreeze_date"] = self.error_class([msg])
            del cleaned_data["develfreeze_date"]

        if release_date and stringfreeze_date and \
            release_date <= stringfreeze_date:
            msg = _("Release date must be after the String freeze date.")
            self._errors["release_date"] = self.error_class([msg])
            del cleaned_data["release_date"]

        elif release_date and develfreeze_date and \
            release_date <= develfreeze_date:
            msg = _("Release date must be after the Devel freeze date.")
            self._errors["release_date"] = self.error_class([msg])
            del cleaned_data["release_date"]

        return cleaned_data
