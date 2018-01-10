import os

from django.conf import settings
from django.contrib.auth import models
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core import management
from django.core.urlresolvers import reverse
from django.db.models import get_model
from django.test import TestCase
from django.test.client import Client

from authority.models import Permission
from django_addons.autodiscover import autodiscover_notifications

from transifex.txcommon.tests.base import BaseTestCase, USER_ROLES,\
        NoticeTypes, skip
from transifex.txcommon.log import logger
from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.projects.permissions.project import ProjectPermission
from transifex.teams.models import Team
from django.utils import unittest

# TODO: POST requests should also be tested everywhere (teams, tr. actions etc.)

Watch = get_model('repowatch', 'Watch')
POFileLock = get_model('locks', 'POFileLock')

class PrivateProjectTest(BaseTestCase):
    """
    Test private projects overall.

    Permissions, get, post return codes etc.
    """
    @skip
    def test_project_list_with_anonymous_user(self):
        """
        Test that project list pages contain only the public project and not
        the private, if the user is anonymous.
        """

        ### project list ALL
        # Issue a GET request.
        response = self.client['anonymous'].get(reverse('project_list'))

        # Check that the response is 200 OK.
        self.failUnlessEqual(response.status_code, 200)

        # Check that the rendered context contains all public projects (see setup)
        self.failUnlessEqual(len(response.context['project_list']),
            Project.objects.filter(private=False).count())

        # Ensure that private project does NOT appear
        for project in response.context['project_list']:
            self.failIfEqual(project.slug, self.project_private.slug)

        ### project list RECENT
        # Issue a GET request.
        response = self.client['anonymous'].get(reverse('project_list_recent'))

        # Check that the response is 200 OK.
        self.failUnlessEqual(response.status_code, 200)

        # Check that the rendered context contains all (public) projects (see setup)
        self.failUnlessEqual(len(response.context['project_list']),
            Project.objects.filter(private=False).count())

        # Ensure that private project does NOT appear
        self.failIfEqual(response.context['project_list'][0].slug, self.project_private.slug)

        #TODO: FEATURED, OPEN TRANSLATIONS list testing

    @skip
    def test_project_list_with_logged_in_user(self):
        """
        Test that project list pages contain only the public project and not
        the private, if the user is logged in.
        """

        ### project list ALL
        # Issue a GET request.
        response = self.client['registered'].get(reverse('project_list'))

        # Check that the response is 200 OK.
        self.failUnlessEqual(response.status_code, 200)

        # Check that the rendered context contains all public projects (see setup)
        self.failUnlessEqual(len(response.context['project_list']),
            Project.objects.filter(private=False).count())

        # Ensure that private project does NOT appear
        for project in response.context['project_list']:
            self.failIfEqual(project.slug, self.project_private.slug)

        ### project list RECENT
        # Issue a GET request.
        response = self.client['registered'].get(reverse('project_list_recent'))

        # Check that the response is 200 OK.
        self.failUnlessEqual(response.status_code, 200)

        # Check that the rendered context contains all (public) projects (see setup)
        self.failUnlessEqual(len(response.context['project_list']),
            Project.objects.filter(private=False).count())

        # Ensure that private project does NOT appear
        for project in response.context['project_list']:
            self.failIfEqual(project.slug, self.project_private.slug)


    def test_project_detail(self):
        """
        Check private project details access.
        """

        # Check anonymous user and logged in user with no permissions
        for user in ['anonymous', 'registered']:
            response = self.client[user].get(self.urls['project_private'])
            self.failUnlessEqual(response.status_code, 403)

        # Check people who should have access to the private project
        for user in ['maintainer', 'team_coordinator', 'team_member',
                'reviewer']: # 'writer',
            response = self.client[user].get(self.urls['project_private'])
            self.failUnlessEqual(response.status_code, 200)

    def test_resource_details(self):
        """
        Check private project components' detail access.
        """

        # Check anonymous user and logged in user with no permissions
        for user in ['anonymous', 'registered']:
            response = self.client[user].get(self.urls['resource_private'])
            self.failUnlessEqual(response.status_code, 403)

        # Check people who should have access to the private project
        for user in ['maintainer', 'team_coordinator', 'team_member',
                'reviewer']: # 'writer',
            response = self.client[user].get(self.urls['resource_private'])
            self.failUnlessEqual(response.status_code, 200)

    def test_widgets(self):
        """
        Test if the permissions to project widgets page are the correct ones.
        """
        #'/projects/p/priv_test/''/projects/p/priv_test/widgets/'
        url = reverse('project_widgets', kwargs={'project_slug':self.project_private.slug})

        # Check anonymous user and logged in user with no permissions
        for user in ['anonymous', 'registered']:
            response = self.client[user].get(url)
            self.failUnlessEqual(response.status_code, 403)

        # Check people who should have access to the private project
        for user in ['maintainer', 'writer', 'team_coordinator',
                'team_member', 'reviewer']:
            response = self.client[user].get(url)
            self.failUnlessEqual(response.status_code, 403)

    def test_search_project(self):
        """
        Test that searching for the private project does not return it.

        We also check the appearance of the public project
        """
        URL = reverse('search')
        TERMS_1_1 = {'q': self.project_private.slug}
        TERMS_1_2 = {'q': self.resource_private.slug}
        TERMS_1_3 = {'q': self.project_private.name}


        # All type of users should not see private projects in search results!
        for user in USER_ROLES:
            response = self.client[user].get(URL, TERMS_1_1)
            self.failUnlessEqual(response.status_code, 200)
            self.assertFalse(self.project_private in response.context['results'])

            response = self.client[user].get(URL, TERMS_1_2)
            self.failUnlessEqual(response.status_code, 200)
            self.assertFalse(self.project_private in response.context['results'])

            response = self.client[user].get(URL, TERMS_1_3)
            self.failUnlessEqual(response.status_code, 200)
            self.assertFalse(self.project_private in response.context['results'])

    def test_teams_access(self):
        """
        Check private project teams' pages access.
        """
        URLs = {
            'anonymous' : {
                403 : [
                    '/projects/p/%s/language/%s/' % (self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/members/' % (self.project_private.slug, self.language.code)
                ],
                302 : [
                    '/projects/p/%s/languages/add/' % self.project_private.slug,
                    '/projects/p/%s/language/%s/edit/' % (self.project_private.slug,
                        self.language.code),
                    '/projects/p/%s/language/%s/delete/' % (self.project_private.slug,
                         self.language.code),
                    '/projects/p/%s/language/%s/request/' % (self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/approve/%s/' % (self.project_private.slug, self.language.code,
                        self.user['team_member'].username),
                    '/projects/p/%s/language/%s/deny/%s/' % (self.project_private.slug, self.language.code,
                        self.user['team_member'].username),
                    '/projects/p/%s/language/%s/withdraw/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/leave/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/languages/request/' % self.project_private.slug,
                    '/projects/p/%s/language/%s/approve/' % (self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/deny/' %(self.project_private.slug, self.language.code),
                ]
            },
            'registered' : {
                403 : [
                    '/projects/p/%s/language/%s/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/members/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/languages/add/' % self.project_private.slug,
                    '/projects/p/%s/language/%s/edit/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/delete/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/request/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/approve/%s/' % (self.project_private.slug, self.language.code,
                        self.user['team_member'].username),
                    '/projects/p/%s/language/%s/deny/%s/' % (self.project_private.slug, self.language.code,
                        self.user['team_member'].username),
                    '/projects/p/%s/language/%s/withdraw/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/leave/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/languages/request/' % self.project_private.slug,
                    '/projects/p/%s/language/%s/approve/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/deny/' %(self.project_private.slug, self.language.code)
                ]
            },
            'maintainer' : {
                200 : [
                    '/projects/p/%s/language/%s/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/members/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/languages/add/' % self.project_private.slug,
                    '/projects/p/%s/language/%s/edit/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/delete/' %(self.project_private.slug, self.language.code)
                ],
                302 : [
                    '/projects/p/%s/language/%s/request/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/leave/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/languages/request/' % self.project_private.slug
                ],
                404 : [
                    '/projects/p/%s/language/%s/approve/%s/' % (self.project_private.slug, self.language.code,
                        self.user['team_member'].username),
                    '/projects/p/%s/language/%s/deny/%s/' % (self.project_private.slug, self.language.code,
                        self.user['team_member'].username),
                    '/projects/p/%s/language/%s/withdraw/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/approve/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/deny/' %(self.project_private.slug, self.language.code)
                ],
            },
            #'writer' : {
            #    200 : [
            #        '/projects/p/%s/languages/',
            #        '/projects/p/%s/language/%s/' %(self.project_private.slug, self.language.code)
            #    ],
            #    302 : [
            #        '/projects/p/%s/language/%s/request/' %(self.project_private.slug, self.language.code),
            #        '/projects/p/%s/language/%s/leave/' %(self.project_private.slug, self.language.code),
            #        '/projects/p/%s/languages/request/'
            #    ],
            #    404 : [
            #        '/projects/p/%s/language/%s/withdraw/' %(self.project_private.slug, self.language.code)
            #    ],
            #    403 : [
            #        '/projects/p/%s/languages/add/',
            #        '/projects/p/%s/language/%s/edit/' %(self.project_private.slug, self.language.code),
            #        '/projects/p/%s/language/%s/delete/' %(self.project_private.slug, self.language.code),
            #        '/projects/p/%s/language/%s/approve/%s/' % (self.project_private.slug, self.language.code,
            #            self.user['team_member'].username),
            #        '/projects/p/%s/language/%s/deny/%s/' % (self.project_private.slug, self.language.code,
            #            self.user['team_member'].username),
            #        '/projects/p/%s/language/%s/approve/' %(self.project_private.slug, self.language.code),
            #        '/projects/p/%s/language/%s/deny/' %(self.project_private.slug, self.language.code)
            #    ]
            #},
            'team_coordinator' : {
                200 : [
                    '/projects/p/%s/language/%s/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/members/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/edit/' %(self.project_private.slug, self.language.code)
                ],
                302 : [
                    '/projects/p/%s/language/%s/request/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/leave/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/languages/request/' % self.project_private.slug
                ],
                404 : [
                    '/projects/p/%s/language/%s/withdraw/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/approve/%s/' % (self.project_private.slug, self.language.code,
                        self.user['team_member'].username),
                    '/projects/p/%s/language/%s/deny/%s/' % (self.project_private.slug, self.language.code,
                        self.user['team_member'].username)
                ],
                403 : [
                    '/projects/p/%s/languages/add/' % self.project_private.slug,
                    '/projects/p/%s/language/%s/delete/' %(self.project_private.slug, self.language.code),
                    # TODO: Add a second team to check if coordinator has access too.
                    '/projects/p/%s/language/%s/approve/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/deny/' %(self.project_private.slug, self.language.code)
                ]
            },
            'team_member' : {
                200 : [
                    '/projects/p/%s/language/%s/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/members/' %(self.project_private.slug, self.language.code)
                ],
                302 : [
                    '/projects/p/%s/language/%s/request/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/leave/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/languages/request/' % self.project_private.slug
                ],
                404 : [
                    '/projects/p/%s/language/%s/withdraw/' %(self.project_private.slug, self.language.code),
                ],
                403 : [
                    '/projects/p/%s/languages/add/' % self.project_private.slug,
                    '/projects/p/%s/language/%s/edit/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/delete/' %(self.project_private.slug, self.language.code),
                    # TODO: Add a second team to check if coordinator has access too.
                    '/projects/p/%s/language/%s/approve/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/deny/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/approve/%s/' % (self.project_private.slug, self.language.code,
                        self.user['team_member'].username),
                    '/projects/p/%s/language/%s/deny/%s/' % (self.project_private.slug, self.language.code,
                        self.user['team_member'].username)
                ]
            },
            'reviewer' : {
                200 : [
                    '/projects/p/%s/language/%s/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/members/' %(self.project_private.slug, self.language.code)
                ],
                302 : [
                    '/projects/p/%s/language/%s/request/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/leave/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/languages/request/' % self.project_private.slug
                ],
                404 : [
                    '/projects/p/%s/language/%s/withdraw/' %(self.project_private.slug, self.language.code),
                ],
                403 : [
                    '/projects/p/%s/languages/add/' % self.project_private.slug,
                    '/projects/p/%s/language/%s/edit/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/delete/' %(self.project_private.slug, self.language.code),
                    # TODO: Add a second team to check if coordinator has access too.
                    '/projects/p/%s/language/%s/approve/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/deny/' %(self.project_private.slug, self.language.code),
                    '/projects/p/%s/language/%s/approve/%s/' % (self.project_private.slug, self.language.code,
                        self.user['team_member'].username),
                    '/projects/p/%s/language/%s/deny/%s/' % (self.project_private.slug, self.language.code,
                        self.user['team_member'].username)
                ]
            }
        }

        for user in URLs.keys():
            for status_code in URLs[user].keys():
                for url in URLs[user][status_code]:
                    response = self.client[user].get(url)
                    self.failUnlessEqual(response.status_code, status_code,
                        "Wrong status code for user '%s' and url '%s' ( %s != %s)" % (
                        user, url, response.status_code,status_code))

    def test_view_strings(self):
        """
        Check access to view lotte for a resource in a private project (read
        only access)
        """

        # Check access to lotte for a language with a team.
        URL = self.urls['translate_private']

        for user in ['anonymous']:
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 302)

        for user in ['registered']:
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 403)

        for user in ['maintainer', 'team_coordinator', 'team_member',
                'reviewer']:# 'writer',
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 200)

        # Check access to lotte for a language without a team.
        URL = reverse('translate_resource', kwargs={'project_slug':self.project_private.slug,
            'resource_slug':self.resource_private.slug,
            'lang_code': self.language_ar.code })

        for user in ['anonymous']:
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 302)

        for user in ['registered', 'team_coordinator', 'team_member',
                'reviewer']:
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 403)

        for user in ['maintainer']: #'writer',
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 200)

    def test_edit_strings(self):
        """
        Check access to view lotte for a resource in a private project
        """

        # Check access to lotte for a language with a team.
        URL = self.urls['translate_private']

        for user in ['anonymous']:
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 302)

        # Maybe this should be 404?
        for user in ['registered']:
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 403)

        for user in ['maintainer',  'team_coordinator', 'team_member',
                'reviewer']: # 'writer'?
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 200)

        # Check access to lotte for a language without a team.
        URL = reverse('translate_resource', kwargs={'project_slug':self.project_private.slug,
            'resource_slug':self.resource_private.slug,
            'lang_code': self.language_ar.code })

        for user in ['anonymous']:
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 302)

        for user in ['registered']:
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 403)

        for user in ['team_coordinator', 'team_member', 'reviewer']:
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 403)

        for user in ['maintainer']: # 'writer'?
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 200)

    def test_download_file(self):
        """
        Check access to download translation file for a resource in a private
        project.
        """

        # Check who has access to download pofile for language with team
        URL = reverse('download_for_translation', kwargs={'project_slug':self.project_private.slug,
            'resource_slug':self.resource_private.slug,
            'lang_code': self.language.code })

        for user in ['anonymous']:
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 302)

        for user in ['registered']:
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 403) # better 404?

        for user in ['maintainer', 'team_coordinator', 'team_member',
                'reviewer']: #'writer'?
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 302) # why not 200?

        # Check who has access to download pofile for language without team
        URL = reverse('translate_resource', kwargs={'project_slug':self.project_private.slug,
            'resource_slug':self.resource_private.slug,
            'lang_code': self.language_ar.code })

        for user in ['anonymous']:
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 302)

        for user in ['team_coordinator', 'team_member', 'registered',
                'reviewer']:
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 403)

        for user in ['maintainer']: # 'writer'?
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 200)

    #def test_submit_file(self):
        #"""
        #Check access to submit pofile in a component of a private project.
        #"""
        #URL = reverse('component_edit_file', kwargs={'project_slug':self.project_private.slug,
        #    'component_slug':'priv_component',
        #    'filename': self.FILEPATHS[0] })
        #
        ## POST Requests
        ## Anonymous user should not have access to submit files!
        #response = self.client.post(URL, follow=True)
        ## Login required will redirect use to the login page
        #self.failUnlessEqual(response.status_code, 200)
        #self.failUnlessEqual(('http://testserver/accounts/login/?next=%s' %
        #    (URL), 302), response.redirect_chain[0])
        #
        ## Logged in user without permissions should not have acces too!
        #test_user = User.objects.create_user('test_login', 'test@transifex.net',
        #    'test_login')
        #self.assertTrue(self.client.login(username='test_login',
        #    password='test_login'))
        #response = self.client.post(URL)
        #self.failUnlessEqual(response.status_code, 403)
        #self.client.logout()
        #
        ## Maintainer should have permission to submit files
        ## (Owner should have been put to maintainers!)
        #self.assertTrue(self.client.login(username='priv_owner',
        #    password='priv_owner'))
        #response = self.client.post(URL, follow=True)
        #self.failUnlessEqual(response.status_code, 200)
        #self.client.logout()
        #
        ## Check that a submitter (writer) has access to submit file.
        #self.assertTrue(self.client.login(username='priv_submitter',
        #    password='priv_submitter'))
        #response = self.client.post(URL, follow=True)
        #self.failUnlessEqual(response.status_code, 200)
        #self.client.logout()
        #
        ##TODO: ONLY team members and coordinators of the specific team where
        ## the file belongs to must have access to it.
        #
        ## Check that a team coordinator (writer) has access to submit a file of his team
        #self.assertTrue(self.client.login(username='priv_coordinator',
        #    password='priv_coordinator'))
        #response = self.client.post(URL, follow=True)
        #self.failUnlessEqual(response.status_code, 200)
        #self.client.logout()
        #
        ## Check that a team member (writer) has access to submit a file of his team.
        #self.assertTrue(self.client.login(username='priv_member',
        #    password='priv_member'))
        #response = self.client.post(URL, follow=True)
        #self.failUnlessEqual(response.status_code, 200)
        #self.client.logout()


    def test_lock_unlock_file(self):
        """
        Check access to lock and unlock pofile in a component of a private project.
        """
        URL = reverse('resource_language_lock', kwargs={'project_slug':self.project_private.slug,
            'resource_slug': self.resource_private.slug,
            'language_code': self.language.code} )

        # POST Requests
        for user in ['anonymous']:
            # the redirect works for the login page but we get 200 status? how
            # come?? XXX! FIXME
            response = self.client[user].post(URL, follow=True)
            self.failUnlessEqual(response.status_code, 200)

        for user in ['registered']:
            # Anonymous and registered user should not have access to lock the files!
            response = self.client[user].post(URL, follow=True)
            self.failUnlessEqual(response.status_code, 403)

        for user in ['maintainer', 'team_coordinator', 'team_member',
                'reviewer']: #'writer',
            response = self.client[user].post(URL, follow=True)
            self.failUnlessEqual(response.status_code, 200)

        URL = reverse('resource_language_lock', kwargs={'project_slug':self.project_private.slug,
            'resource_slug': self.resource_private.slug,
            'language_code': self.language_ar.code})

        for user in ['anonymous']: #, 'writer'
            # the redirect works for the login page but we get 200 status? how
            # come?? XXX! FIXME
            response = self.client[user].post(URL, follow=True)
            self.failUnlessEqual(response.status_code, 200)

        # Why do team_co && team_member return 200? XXX ! FIXME
        for user in ['registered']:# 'team_coordinator','team_member'
            response = self.client[user].post(URL, follow=True)
            self.failUnlessEqual(response.status_code, 403)

        for user in ['maintainer']: #, 'writer'
            response = self.client[user].post(URL, follow=True)
            self.failUnlessEqual(response.status_code, 200)


    def test_watch_unwatch_file(self):
        """
        Check access to watch/unwatch file in a component of a private project.
        """
        from notification.models import NoticeType

        URL = reverse('resource_translation_toggle_watch',
            kwargs={ 'project_slug':self.project_private.slug,
                'resource_slug': self.resource_private.slug,
                'language_code': self.language.code })

        # POST Requests
        for user in ['anonymous']:
            response = self.client[user].post(URL)
            self.failUnlessEqual(response.status_code, 302)

        for user in ['registered']:
            response = self.client[user].post(URL, follow=True)
            self.failUnlessEqual(response.status_code, 403)

        for user in ['maintainer', 'team_coordinator', 'team_member',
                'reviewer']: #'writer',
            response = self.client[user].post(URL, follow=True)
            self.failUnlessEqual(response.status_code, 200)

        URL = reverse('resource_language_lock', kwargs={'project_slug':self.project_private.slug,
            'resource_slug': self.resource_private.slug,
            'language_code': self.language_ar.code})

        for user in ['anonymous']:
            response = self.client[user].post(URL)
            self.failUnlessEqual(response.status_code, 302)

        # Why do team_co && team_member return 200? XXX ! FIXME
        for user in ['registered']: # , 'team_coordinator', 'team_member'
            # Anonymous and registered user should not have access to lock the files!
            response = self.client[user].post(URL, follow=True)
            self.failUnlessEqual(response.status_code, 403)

        for user in ['maintainer']: # , 'writer'
            response = self.client[user].post(URL, follow=True)
            self.failUnlessEqual(response.status_code, 200)


    def test_watch_unwatch_project(self):
        """
        Check access to watch/unwatch project in a component of a private project.
        """
        from notification.models import NoticeType

        URL = reverse('project_toggle_watch',
            kwargs={ 'project_slug':self.project_private.slug})

        # POST Requests
        for user in ['anonymous']:
            response = self.client[user].post(URL)
            self.failUnlessEqual(response.status_code, 302)

        for user in ['registered']:
            response = self.client[user].post(URL, follow=True)
            self.failUnlessEqual(response.status_code, 403)

        for user in ['maintainer', 'team_coordinator', 'team_member',
                'reviewer']: # 'writer',
            response = self.client[user].post(URL, follow=True)
            self.failUnlessEqual(response.status_code, 200)

    def test_charts(self):
        """
        Check access to component charts.
        """
        # images and charts urls
        URLs = [
            reverse('chart_resource_image', kwargs={'project_slug':self.project_private.slug,
                'resource_slug': self.resource_private.slug}),
            reverse('chart_resource_js', kwargs={'project_slug':self.project_private.slug,
                'resource_slug': self.resource_private.slug}),
            reverse('chart_resource_html', kwargs={'project_slug':self.project_private.slug,
                'resource_slug': self.resource_private.slug}),
            reverse('chart_resource_json', kwargs={'project_slug':self.project_private.slug,
                'resource_slug': self.resource_private.slug})
        ]

        for user in ['anonymous', 'registered']:
            for url in URLs:
                response = self.client[user].get(url)
                self.failUnlessEqual(response.status_code, 403)

        # For now charts are disabled for private projects
        for user in ['maintainer', 'writer', 'team_coordinator',
                'team_member', 'reviewer']:
            for url in URLs:
                response = self.client[user].get(url)
                self.failUnlessEqual(response.status_code, 403)

    def test_timeline(self):
        """
        Check access to component charts.
        """
        URL = reverse('project_timeline', kwargs={'project_slug':self.project_private.slug,})

        # Only maintainers have access to the project timeline ???

        for user in ['anonymous']:
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 302)

        for user in ['registered', 'writer']:
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 403)

        for user in ['maintainer', 'team_coordinator',
                'team_member', 'reviewer']:
            response = self.client[user].get(URL)
            self.failUnlessEqual(response.status_code, 200)

    def test_public_to_private(self):
        """
        Test the process of transforming a public project to private.
        """
        pass


    def test_private_to_public(self):
        """
        Test the process of transforming a public project to private.
        """
        pass


class ProjectLookupsTests(BaseTestCase):

    def test_private_projects_ajax_lookup(self):
        """Test that a private project isn't present in lookups.

        This AJAX lookup/dropdown is present in the Team Outsource form.
        """

        public_project = "Test Project"
        private_project = "Test Private Project"

        # Test that a private project is not visible to a random user
        self.assertTrue(self.user['registered'] not in self.project_private.maintainers.all())
        resp = self.client['registered'].get('/ajax/ajax_lookup/projects', {'q': 'p', 'limit': '150', })
        self.assertContains(resp, public_project, status_code=200)
        self.assertNotContains(resp, private_project, status_code=200)

        # Test that a private project is visible to its maintainer
        self.assertTrue(self.user['maintainer'] in self.project_private.maintainers.all())
        resp = self.client['maintainer'].get('/ajax/ajax_lookup/projects', {'q': 'p', 'limit': '150', })
        self.assertContains(resp, public_project, status_code=200)
        self.assertContains(resp, private_project, status_code=200)

        # Test that a private project is visible to a member of its teams
        self.assertTrue(self.user['team_member'] in self.team_private.members.all())
        self.assertFalse(self.user['team_member'] in self.project_private.maintainers.all())
        resp = self.client['team_member'].get('/ajax/ajax_lookup/projects', {'q': 'p', 'limit': '150', })
        self.assertContains(resp, public_project, status_code=200)
        self.assertContains(resp, private_project, status_code=200)

        # Test that a private project is visible to a reviewer of its teams
        self.assertTrue(self.user['reviewer'] in self.team_private.members.all())
        self.assertFalse(self.user['reviewer'] in self.project_private.maintainers.all())
        resp = self.client['reviewer'].get('/ajax/ajax_lookup/projects', {'q': 'p', 'limit': '150', })
        self.assertContains(resp, public_project, status_code=200)
        self.assertContains(resp, private_project, status_code=200)

