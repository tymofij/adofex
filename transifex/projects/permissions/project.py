# -*- coding: utf-8 -*-
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

import authority
from authority.permissions import BasePermission
from transifex.projects.models import Project
from transifex.teams.models import Team
from transifex.txcommon.log import logger


def _check_outsource_project(obj):
    """
    Check if the project, to which the obj passed by parameter belongs, has
    outsourced the access control to another project.

    The parameter 'obj' can be a Project, Team instance, etc.

    Return a tuple '(project, team)'. The 'team' might be None.
    """
    outsourced_project = None
    if isinstance(obj, Project):
        if obj.outsource:
            project = obj.outsource
            outsourced_project = obj
        else:
            project = obj
        team = None
    elif isinstance(obj, Team):
        team = obj
        project = team.project
    return (project, team, outsourced_project)

class ProjectPermission(BasePermission):

    label = 'project_perm'
    checks = ('maintain', 'coordinate_team', 'proofread', 'submit_translations')

    def maintain(self, project=None):
        if project:
            if project.maintainers.filter(id=self.user.id) or \
                project.owner == self.user:
                return True
        return False
    maintain.short_description=_('Is allowed to maintain this project')

    def coordinate_team(self, project=None, language=None):
        if project:
            #Maintainer
            if self.maintain(project):
                return True
            if language:
                team = Team.objects.get_or_none(project, language.code)
                #Coordinator
                if team and self.user in team.coordinators.all():
                    return True
        return False
    coordinate_team.short_description = _("Is allowed to coordinate a "
        "team project")

    def proofread(self, project=None, language=None, any_team=False):
        if project:
            if self.maintain(project):
                # Maintainers can review
                return True

            if language:
                team = Team.objects.get_or_none(project, language.code)
                if team:
                    if self.user in team.reviewers.all() or self.user in team.coordinators.all():
                        return True
            elif any_team:
                user_teams = project.team_set.filter(
                    Q(reviewers=self.user)).distinct()
                if user_teams:
                    return True
        return False
    proofread.short_description = _("Is allowed to review translations for "
        "a team project")

    def submit_translations(self, obj, any_team=False):
        """
        Check whether a user can submit translations to a project.

        This method can receive two kinds of object through the parameter
        'obj', which can be Project and Team instances. Depending on the
        object type different checks are done.

        The parameter 'any_team' can be used when a it is necessary to verify
        that a user has submit access for at least one project team. If a
        Project object is passed and the parameter 'any_team' is False, the
        verification of access will only return True for maintainers and
        writers.
        """
        project, team = None, None
        if obj:
            # The `project` is the project against which we check the team
            # permissions. For writers/maintainers we need to check against the
            # `outsourced_project` if it exists.
            project, team, outsourced_project = _check_outsource_project(obj)
            if project:
                if project.anyone_submit:
                    return True
                # Maintainers
                # A maintainer should have access to his project only and not
                # to the project that are outsourced to his project as well
                if (outsourced_project and self.maintain(outsourced_project)):
                    return True
                if self.maintain(project) and not outsourced_project:
                    return True
                #Writers
                perm = '%s.submit_translations' % self.label
                if self.has_perm(perm, project):
                    return True
                if team:
                    # Coordinators or members
                    if self.user in team.coordinators.all() or \
                        self.user in team.members.all() or \
                        self.user in team.reviewers.all():
                        return True
                if any_team and not team:
                    user_teams = project.team_set.filter(
                        Q(coordinators=self.user)|
                        Q(members=self.user)|
                        Q(reviewers=self.user)
                    ).distinct()
                    if user_teams:
                        return True
        return False
    submit_translations.short_description = _("Is allowed to submit "
        "translations to this project")

    def private(self, project=None):
        """Test if a user has access to a private project."""
        if project:
            if project.private:
                # To avoid doing all the checks below!
                if self.user.is_anonymous():
                    return False
                # Maintainers, writers (submitters, coordinators, members)
                return self.maintain(project) or \
                    self.submit_translations(project, any_team=True) or\
                    self.proofread(project, any_team=True)
            else:
                # The project is public so let them continue
                return True
        return False
    private.short_description=_('Is allowed to browse this private project')

authority.register(Project, ProjectPermission)
