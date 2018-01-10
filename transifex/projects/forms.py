from django import forms
from django.db import models
from django.utils.translation import ugettext as _
from django.db.models import permalink
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import widgets
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.contrib.auth import authenticate

from ajax_select.fields import AutoCompleteSelectMultipleField
from tagging.forms import TagField
from tagging_autocomplete.widgets import TagAutocomplete

from transifex.projects.models import Project
from transifex.projects.signals import (project_access_control_form_start,
                                        project_form_init, project_form_save,
                                        project_private_check,
                                        project_type_check)
from transifex.txcommon.widgets import SplitSelectDateTimeWidget


class ProjectForm(forms.ModelForm):
    maintainers = AutoCompleteSelectMultipleField(
        'users', label=_("Maintainers"), required=True,
        help_text=_('Search for a username')
    )
    tags = TagField(label=_("Tags"), widget=TagAutocomplete(), required=False)

    class Meta:
        model = Project
        exclude = ('anyone_submit', 'outsource', 'owner')
        fields = (
            'name', 'slug', 'description', 'trans_instructions', 'tags',
            'long_description', 'maintainers', 'private', 'homepage', 'feed',
            'bug_tracker', 'source_language', 'logo',
        )

    def __init__(self, *args, **kwargs):
        # we need this because the number of private projects validation may
        # depend on the owner's subscription
        self.owner = kwargs.pop('owner', None)

        super(ProjectForm, self).__init__(*args, **kwargs)
        # Disable the source_language widget when updating
        if self.instance and self.instance.id:
            if self.instance.resources.count():
                self.fields['source_language'].required = False
                self.fields['source_language'].widget.attrs['disabled'] = 'disabled'
        project_form_init.send(sender=ProjectForm, form=self)

    def save(self, *args, **kwargs):
        retval = super(ProjectForm, self).save(*args, **kwargs)
        project_form_save.send(sender=ProjectForm, form=self, instance=retval)
        return retval

    def clean_private(self):
        project_private_check.send(sender=ProjectForm, instance=self)
        return self.cleaned_data['private']

    def clean_tags(self):
        project_tags_list = self.cleaned_data['tags']
        tags = list(set([tag.strip() for tag in project_tags_list.split(',')])) or []
        for i in tags:
            if not i.strip():
                tags.remove(i)
        tags.append(u'')
        project_tags_list = ', '.join(tags)
        return project_tags_list

    def clean_source_language(self):
        if self.instance and self.instance.id:
            if self.instance.resources.count():
                return self.instance.source_language
            else:
                return self.cleaned_data['source_language']
        else:
            return self.cleaned_data['source_language']


class ProjectDeleteForm(forms.Form):
    """
    A form used to check the user password before deleting a project.
    """
    password = forms.CharField(widget=forms.PasswordInput,
                               label=_('Your password'))

    def __init__(self, request, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super(ProjectDeleteForm, self).__init__(*args, **kwargs)

    def clean(self):
        password = self.cleaned_data.get('password')
        if password:
            self.user_cache = authenticate(username=self.request.user.username, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(_("Invalid password."))

        return self.cleaned_data


class RadioFieldRenderer(widgets.RadioFieldRenderer):
    """
    An object used by RadioSelect to enable customization of radio widgets.
    """
    def get_class(self, v, v2):
        """
        Return the string 'selected' if both values are equal.

        This is used to set a class attr on the selected radio button.
        """
        if v==v2:
            return 'selected'
        else:
            return ''

    def render(self):
        """Outputs a <ul> for this set of radio fields."""
        help_text = self.attrs.get('help_text', {})
        return mark_safe(u'<ul>\n%s\n</ul>' % u'\n'.join(
            [u'<li class="%s"><span>%s</span><p class="helptext">%s</p></li>'
                % (self.get_class(w.value, w.choice_value),
                   force_unicode(w),
                   help_text.get(w.choice_value, '')) for w in self]))


class ProjectAccessControlForm(forms.ModelForm):
    """Form to handle the Access Control options of a project."""
    type_options = [
        {'typical': {
            'label': _('Typical project'),
            'help_text': _(
                "Access control and teams are managed under a single project. "
                "Best option for most cases.")
            }
        },
        {'hub': {
            'label': _('Project hub'),
            'help_text': _(
                "Option for a parent project which will host translation teams "
                "and will acts as an umbrella to others. Ideal for organizations "
                "with multiple products."),
            }
        },
        {'outsourced': {
            'label': _('Outsourced project'),
            'help_text': _(
                "Option for the child of a hub project. This project will have no "
                "teams of its own but will re-use the parent's ones."),
            }
        },
    ]

    access_control_options = [
        {'free_for_all': {
            'label': _('Free for all'),
            'help_text': _(
                "Allow any logged-in user to submit files to my project. "
                "<a href=\"http://www.youtube.com/watch?v=DCX3ZNDZAwY\" "
                "target=\"_blank\">Imagine</a> all the people, sharing all the "
                "world. Recommended for quick translations, and when a "
                "post-translation, pre-commit review process is in place.")
            }
        },
        {'limited_access': {
            'label': _('Limited access (teams)'),
            'help_text': _(
                "Give access to specific people. Language teams will have "
                "access to their language's files only, and global writers "
                "will have access to all translation files. Recommended for "
                "most projects."),
            }
        },
    ]

    # Setting up some vars based on the 'types_options' var
    types = []
    types_help = {}
    types_help2 = []
    for o in type_options:
        for k, v in o.items():
            types.append((k, v['label']))
            types_help.update({k: v['help_text']})
            types_help2.append((v['label'], v['help_text']))
    types_help2 = '<br/><br/>'.join(
        ['<b>%s</b>: %s' % (v[0], v[1]) for v in types_help2])
        
    # Setting up some vars based on the 'access_control_options' var
    access_control_types = []
    access_control_help = {}
    access_control_help2 = []
    for o in access_control_options:
        for k, v in o.items():
            access_control_types.append((k, v['label']))
            access_control_help.update({k: v['help_text']})
            access_control_help2.append((v['label'], v['help_text']))
    access_control_help2 = '<br/><br/>'.join(
        ['<b>%s</b>: %s' % (v[0], v[1]) for v in access_control_help2])

    
    project_type = forms.ChoiceField(choices=types, required=True,
        #widget=forms.RadioSelect, #help_text=types_help2,
        widget=forms.RadioSelect(renderer=RadioFieldRenderer,
        attrs={'help_text': types_help})
        )

    access_control = forms.ChoiceField(choices=access_control_types,
        required=True, 
        #widget=forms.RadioSelect, #help_text=access_control_help2,
        widget=forms.RadioSelect(renderer=RadioFieldRenderer,
        attrs={'help_text': access_control_help})
        )

    class Meta:
        model = Project
        fields = ('project_type', 'outsource', 'access_control')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ProjectAccessControlForm, self).__init__(*args, **kwargs)       
        self.project = kwargs.get('instance', None)

        outsource_required = False
        access_control_required = True
        project_type_initial = None
        access_control_initial = None

        self.hub_request = self.project.hub_request

        # Disable all form fields if there is a open hub request
        if self.hub_request:
            for f in self.fields:
                self.fields[f].widget.attrs['disabled'] = 'disabled'
        if args:
            if 'outsourced' == args[0].get('project_type'):
                outsource_required = True
                access_control_required = False
        elif self.project:
            
            if self.project.anyone_submit:
                access_control_initial = 'free_for_all'
            else:
                access_control_initial = 'limited_access'

            if self.project.outsource:
                access_control_initial = None
                project_type_initial = 'outsourced'
                outsource_required = True
                access_control_required = False
            else:
                if not access_control_initial:
                    access_control_initial = 'limited_access'
                if self.project.is_hub:
                    project_type_initial = 'hub'
                else:
                    project_type_initial = 'typical'

        if project_type_initial:
            self.fields['project_type'].initial = project_type_initial
        
        if access_control_initial:
            self.fields['access_control'].initial = access_control_initial
        
        self.fields['access_control'].required = access_control_required
        self.fields['outsource'].required = outsource_required
        
        self.fields['outsource'].label = _('Outsource access to')
        
        ## Filtering project list
        if self.user:
            projects = Project.objects.for_user(self.user).filter(is_hub=True
                ).exclude(id=self.project.id).only('id', 'name')
        else:
            projects = Project.objects.filter(is_hub=True
                ).exclude(models.Q(id=self.project.id) | models.Q(private=True))

        self.fields["outsource"].queryset = projects
        
        project_access_control_form_start.send(sender=ProjectAccessControlForm,
            instance=self, project=self.project)

    def clean(self):
        cleaned_data = self.cleaned_data
        project_type = cleaned_data.get('project_type')
        outsource = cleaned_data.get('outsource', None)
        project_type_msg = ''
        
        if project_type != 'outsourced' and outsource:
            project_type_msg = _("Project type do not accept outsource project")
            
        elif (self.project.is_hub and project_type != 'hub' and 
            self.project.outsourcing.all()):
            project_type_msg = _("This project is being used "
                "as outsource by other projects, thus it can not be set "
                "to other project type until having all the outsourced "
                "projects disassociated to it.")

        if project_type_msg:
            self._errors["project_type"] = self.error_class([project_type_msg])
            del cleaned_data["project_type"]

        return cleaned_data

    def clean_project_type(self):
        project_type_check.send(sender=ProjectForm, instance=self)
        return self.cleaned_data['project_type']
