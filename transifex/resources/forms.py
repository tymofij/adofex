from uuid import uuid4
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from transifex.txcommon.exceptions import FileCheckError
from transifex.languages.models import Language
from transifex.resources.formats.registry import registry
from transifex.languages.models import Language, language_choice_list
from transifex.resources.models import Resource
from transifex.resources.formats.core import ParseError
from transifex.resources.backends import ResourceBackend, \
        ResourceBackendError, content_from_uploaded_file


class ResourceForm(forms.ModelForm):

    sourcefile = forms.FileField(label=_("Source File"), required=False)

    class Meta:
        model = Resource
        exclude = ('project', 'resource_group', 'i18n_type', 'source_language')


class CreateResourceForm(forms.ModelForm):
    """Form to create a new resource."""

    i18n_choices = sorted(registry.descriptions(), key=lambda m: m[1])
    i18n_choices.insert(0, ('', '-' * 10))

    source_file = forms.FileField(label=_("Resource File"))
    i18n_method = forms.ChoiceField(
        label=_("I18N Type"), choices=i18n_choices,
        help_text=_(
            "The type of i18n method used in this resource (%s)" % \
                ', '.join(sorted(m[1] for m in registry.descriptions()))
        )
    )

    class Meta:
        model = Resource
        fields = ('source_file', 'name', 'i18n_method', )


class ResourceTranslationForm(forms.Form):
    """
    Form to to be used for creating new translations.
    """

    language_choices = language_choice_list()
    language_choices.insert(0, ('', '-' * 10))

    translation_file = forms.FileField(label=_("Translation File"))
    target_language = forms.ChoiceField(
        label=_('Language'), choices=language_choices,
        help_text=_("The language of the translation.")
    )


class UpdateTranslationForm(forms.Form):
    """Form used when uploading a new translation file."""

    translation_file = forms.FileField(label=_("Translation File"))
    target_language = forms.ChoiceField(
        label=_('Language'), widget=forms.HiddenInput,
        choices=language_choice_list(),
        help_text=_("The language of the translation.")
    )



class ResourcePseudoTranslationForm(forms.Form):
    """Form to be used for getting pseudo translation files"""

    pseudo_type = forms.ChoiceField(label=_("Pseudo type"), required=True,
        choices=[(k, v) for k, v in settings.PSEUDO_TYPES.items()],
        widget=forms.widgets.RadioSelect, initial='MIXED',
        help_text=_("For more info about each pseudo translation type, please "
            "refer to the docs."))
