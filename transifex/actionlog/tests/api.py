#-*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.utils import simplejson
from transifex.txcommon.tests import base
from transifex.actionlog.models import *

class ActionlogAPITests(base.BaseTestCase):
    def setUp(self, *args, **kwargs):
        super(ActionlogAPITests, self).setUp(*args, **kwargs)

    def test_project_actionlogs(self):
        """Test API for global actionlogs and per project actionlogs"""
        for user in self.client.keys():
            #Test global actionlogs
            resp = self.client[user].get(reverse('global_actionlogs'), {'limit':10})
            if user == 'anonymous':
                self.assertEqual(resp.status_code, 401)
            else:
                self.assertEqual(resp.status_code, 200)

            #Test actionlogs for a public project
            resp = self.client[user].get(reverse('project_actionlogs',
                args=['project1']))
            if user == 'anonymous':
                self.assertEqual(resp.status_code, 401)
            else:
                self.assertEqual(resp.status_code, 200)

            #Test actionlogs for a private project
            resp = self.client[user].get(reverse('project_actionlogs',
                args=['project2']))
            if user == 'anonymous':
                self.assertEqual(resp.status_code, 401)
            else:
                if user in ['maintainer', 'team_member', 'team_coordinator',
                        'reviewer']:
                    self.assertEqual(resp.status_code, 200)
                else:
                    self.assertEqual(resp.status_code, 401)

        resp = self.client['maintainer'].get(reverse('project_actionlogs',
            args=['project_foo']))
        self.assertEqual(resp.status_code, 404)

    def test_team_actionlogs(self):
        """Test actionlogs API for teams"""
        for user in self.client.keys():
            #Test actionlogs for all teams in a public project
            resp = self.client[user].get(reverse('project_teams_actionlogs',
                args=['project1']))
            if user == 'anonymous':
                self.assertEqual(resp.status_code, 401)
            else:
                self.assertEqual(resp.status_code, 200)

            #Test actionlogs for all teams in a private project
            resp = self.client[user].get(reverse('project_teams_actionlogs',
                args=['project2']))
            if user in ['maintainer', 'team_coordinator', 'team_member',
                    'reviewer']:
                self.assertEqual(resp.status_code, 200)
            else:
                self.assertEqual(resp.status_code, 401)

            #Test actionlogs for a team in a public project
            resp = self.client[user].get(reverse('project_team_actionlogs',
                args=['project1', self.language.code]))
            if user == 'anonymous':
                self.assertEqual(resp.status_code, 401)
            else:
                self.assertEqual(resp.status_code, 200)

            #Test actionlogs for a team in a private project
            resp = self.client[user].get(reverse('project_team_actionlogs',
                args=['project2', self.language.code]))
            if user in ['maintainer', 'team_coordinator', 'team_member',
                    'reviewer']:
                self.assertEqual(resp.status_code, 200)
            else:
                self.assertEqual(resp.status_code, 401)

        resp = self.client['maintainer'].get(reverse('project_team_actionlogs',
            args=['project1', 'team_foo']))
        self.assertEqual(resp.status_code, 404)

    def test_release_actionlogs(self):
        """Test actionlogs API for releases"""
        for user in self.client.keys():
            #Test actionlogs for all releases in a public project
            resp = self.client[user].get(reverse('project_releases_actionlogs',
                args=['project1']))
            if user == 'anonymous':
                self.assertEqual(resp.status_code, 401)
            else:
                self.assertEqual(resp.status_code, 200)

            #Test actionlogs for all releases in a private project
            resp = self.client[user].get(reverse('project_releases_actionlogs',
                args=['project2']))
            if user in ['maintainer', 'team_coordinator', 'team_member',
                    'reviewer']:
                self.assertEqual(resp.status_code, 200)
            else:
                self.assertEqual(resp.status_code, 401)

            #Test actionlogs for a release in a public project
            resp = self.client[user].get(reverse('project_release_actionlogs',
                args=['project1', 'releaseslug1']))
            if user == 'anonymous':
                self.assertEqual(resp.status_code, 401)
            else:
                self.assertEqual(resp.status_code, 200)

            #Test actionlogs for a release in a private project
            resp = self.client[user].get(reverse('project_release_actionlogs',
                args=['project2', 'releaseslug2']))
            if user in ['maintainer', 'team_coordinator', 'team_member',
                    'reviewer']:
                self.assertEqual(resp.status_code, 200)
            else:
                self.assertEqual(resp.status_code, 401)

        resp = self.client['maintainer'].get(reverse('project_release_actionlogs',
            args=['project1', 'release_foo']))
        self.assertEqual(resp.status_code, 404)

    def test_resource_actionlogs(self):
        """Test actionlogs API for resources"""
        for user in self.client.keys():
            #Test actionlogs for all resources in a public project
            resp = self.client[user].get(reverse('project_resources_actionlogs',
                args=['project1']))
            if user == 'anonymous':
                self.assertEqual(resp.status_code, 401)
            else:
                self.assertEqual(resp.status_code, 200)

            #Test actionlogs for all resources in a private project
            resp = self.client[user].get(reverse('project_resources_actionlogs',
                args=['project2']))
            if user in ['maintainer', 'team_coordinator', 'team_member',
                    'reviewer']:
                self.assertEqual(resp.status_code, 200)
            else:
                self.assertEqual(resp.status_code, 401)

            #Test actionlogs for a resource in a public project
            resp = self.client[user].get(reverse('project_resource_actionlogs',
                args=['project1', 'resource1']))
            if user == 'anonymous':
                self.assertEqual(resp.status_code, 401)
            else:
                self.assertEqual(resp.status_code, 200)

            #Test actionlogs for a resource in a private project
            resp = self.client[user].get(reverse('project_resource_actionlogs',
                args=['project2', 'resource1']))
            if user in ['maintainer', 'team_coordinator', 'team_member',
                    'reviewer']:
                self.assertEqual(resp.status_code, 200)
            else:
                self.assertEqual(resp.status_code, 401)

        resp = self.client['maintainer'].get(reverse('project_resource_actionlogs',
            args=['project1', 'res_foo']))
        self.assertEqual(resp.status_code, 404)

    def test_user_actionlogs(self):
        """Test actionlogs API for a user"""
        l = LogEntry.objects.create(user=self.user['maintainer'],
                action_type=NoticeType.objects.get(label='project_changed'),
                content_type=ContentType.objects.get(model='project'),
                object_id = self.project_private.id,
                object = self.project_private,
                message='The project with slug project2 has been changed')
        for user in self.client.keys():
            resp = self.client[user].get(reverse('user_actionlogs',
                args=['maintainer']))
            if user == 'anonymous':
                self.assertEqual(resp.status_code, 401)
                continue
            else:
                self.assertEqual(resp.status_code, 200)
            if user == 'maintainer':
                self.assertContains(resp, 'project2')
            else:
                self.assertNotContains(resp, 'project2')

        resp = self.client['maintainer'].get(reverse('user_actionlogs',
            args=['foo']))
        self.assertEqual(resp.status_code, 404)
