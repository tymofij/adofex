from transifex.projects.models import Project
from transifex.teams.models import Team
from transifex.txcommon.tests import base

class TestTeamModels(base.BaseTestCase):

    def test_available_teams(self):
        """
        Test whether monkey-patch of Project class with a 'available_teams'
        instance method returns the desired result.
        """
        # There must be only 1 'pt_BR' team
        self.assertEquals(self.project.available_teams.count(), 1)

        # Create a new 'ar' team for self.project
        team = Team.objects.get_or_create(language=self.language_ar,
            project=self.project, creator=self.user['maintainer'])[0]

        # Create a secondary project and set it to outsource access to self.project
        project = Project.objects.get_or_create(slug="foo",
            defaults={'name':"Foo Project"},
            source_language=self.language_en)[0]
        project.outsource = self.project

        # There must be 2 teams. One 'pt_BR' and a 'ar' one.
        self.assertEquals(project.available_teams.count(), 2)

    def test_teams_for_user(self):
        for user in ['reviewer', 'team_member', 'team_coordinator',
                'maintainer']:
            if user == 'maintainer':
                self.assertFalse(Team.objects.for_user(self.user[user]))
            else:
                self.assertEqual(set(Team.objects.for_user(self.user[user]
                    ).values_list('pk')),
                        set(Team.objects.filter(pk__in=[self.team.pk,
                            self.team_private.pk]).values_list('pk'))
                )


