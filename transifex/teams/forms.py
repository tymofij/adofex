from django import forms
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.teams.models import Team, TeamRequest
from transifex.txcommon.widgets import SelectWithDisabledOptions

from ajax_select.fields import AutoCompleteField, AutoCompleteSelectMultipleField


class TeamSimpleForm(forms.ModelForm):
    coordinators = AutoCompleteSelectMultipleField(
        'users', label=_("Coordinators"), required=True,
        help_text=_("Coordinators are people that can manage the members of "\
                    "the team, for example. Search for usernames.")
                )

    members = AutoCompleteSelectMultipleField(
        'users', label=_("Members"), required=False,
        help_text=_("Members are actually people that can submit "\
                    "translations. Search for usernames.")
    )

    reviewers = AutoCompleteSelectMultipleField(
        'users', label=_("Reviewers"), required=False,
        help_text=_("Reviewers are team members that can proofread "\
                    "translations and mark them as reviewed. Search for "\
                    "usernames.")
    )

    class Meta:
        model = Team
        fields = ('language', 'coordinators', 'members', 'reviewers', 'mainlist',
            'project', 'creator')

    def __init__(self, project, language=None, *args, **kwargs):
        super(TeamSimpleForm, self).__init__(*args, **kwargs)
        self.fields['project'].widget = forms.HiddenInput()
        self.fields['project'].initial = project.pk
        self.fields['creator'].widget = forms.HiddenInput()

        if language:
            self.fields['language'].initial = language.pk

        # Lets filter the language field based on the teams already created.
        # We don't need to enable a language if there is a team for it already.
        # Also, when editing the team details the language must not be changeable
        # to other complete different languages. It only accepts changing
        # language among languages with the same general code, such as pt,
        # pt_BR, pt_PT.
        instance = kwargs.get('instance', None)
        if instance:
            # Getting general language code. 'pt_BR' turns into 'pt'
            general_code = instance.language.code.split('_')[0]

            # Create list of languages to be disabled excluding the current
            # language and also languages for the same general code that do not
            # have a team already created for the related project.
            self.disabled_langs = Language.objects.exclude(
                Q(code=instance.language.code) |
                ~Q(teams__project=project), Q(code__startswith=general_code)
                ).values_list('pk', flat=True)

            # We don't need an empty label
            self.fields["language"].empty_label = None
        
        # For languages with no teams
        elif language:
            # Allow only the selected language to be in the list
            self.disabled_langs = Language.objects.exclude(
                code=language.code).values_list('pk', flat=True)

            # We don't need an empty label
            self.fields["language"].empty_label = None
        else:
            # Create list of languages to be disabled excluding the current
            # language and also the language of teams already created.
            self.disabled_langs = Team.objects.filter(project=project).exclude(
                language=language).values_list('language__pk', flat=True)

        # Setting custom widget with list of ids that should be disabled
        self.fields["language"].widget = SelectWithDisabledOptions(
            choices=[(l.pk, l) for l in Language.objects.all()],
            disabled_choices=self.disabled_langs)

    def clean_language(self):
        """Make sure language doesn't get a invalid value."""
        data = self.cleaned_data['language']
        if isinstance(data, Language):
            pk = data.pk
        else:
            pk = int(data)
        if pk in self.disabled_langs:
            raise forms.ValidationError(_(u'Enter a valid value.'))
        return data

    def clean(self):
        cleaned_data = self.cleaned_data
        coordinators = cleaned_data.get("coordinators")
        members = cleaned_data.get("members")
        reviewers = cleaned_data.get("reviewers")

        if coordinators and members:
            intersection = set(coordinators).intersection(members)
            if intersection:
                users = [User.objects.get(pk=c).username for c in intersection]
                raise forms.ValidationError(_("User(s) %s cannot be in "
                    "both Coordinators and Members lists. Please make "
                    "sure that the lists are unique.") % ', '.join(users))

        if coordinators and reviewers:
            intersection = set(coordinators).intersection(reviewers)
            if intersection:
                users = [User.objects.get(pk=c).username for c in intersection]
                raise forms.ValidationError(_("User(s) %s cannot be in "
                    "both Coordinators and Reviewers lists. Please make "
                    "sure that the lists are unique.") % ', '.join(users))

        if members and reviewers:
            intersection = set(members).intersection(reviewers)
            if intersection:
                users = [User.objects.get(pk=c).username for c in intersection]
                raise forms.ValidationError(_("User(s) %s cannot be in "
                    "both Members and Reviewers lists. Please make "
                    "sure that the lists are unique.") % ', '.join(users))

        return cleaned_data


class TeamRequestSimpleForm(forms.ModelForm):
    class Meta:
        model = TeamRequest
        fields = ('language', 'project', 'user')

    def __init__(self, project, language_code=None, *args, **kwargs):
        super(TeamRequestSimpleForm, self).__init__(*args, **kwargs)
        self.fields['project'].widget = forms.HiddenInput()
        self.fields['project'].initial = project.pk
        self.fields['user'].widget = forms.HiddenInput()

        # Create list of languages to be disabled excluding the current
        # language_code and also the language of teams already created.
        self.disabled_langs = Team.objects.filter(project=project).exclude(
            language__code=language_code).values_list('language__pk', flat=True)

        # Setting custom widget with list of ids that should be disabled
        self.fields["language"].widget = SelectWithDisabledOptions(
            choices=[(l.pk, l) for l in Language.objects.all()],
            disabled_choices=self.disabled_langs)

    def clean_language(self):
        """Make sure language doesn't get a invalid value."""
        data = self.cleaned_data['language']
        if isinstance(data, Language):
            pk = data.pk
        else:
            pk = int(data)
        if pk in self.disabled_langs:
            raise forms.ValidationError(_(u'Enter a valid value.'))
        return data


class ProjectsFilterForm(forms.Form):

    project = forms.ModelChoiceField(queryset=Project.objects.all(),
        empty_label=_('All child projects'), required=False,)

    def __init__(self, project, *args, **kwargs):
        super(ProjectsFilterForm, self).__init__(*args, **kwargs)

        project = self.fields["project"].queryset.filter(
            Q(id=project.id) | Q(outsource=project))
        self.fields["project"].queryset = project
