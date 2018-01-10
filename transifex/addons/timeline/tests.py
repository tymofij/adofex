# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.test.client import Client
from transifex.projects.models import Project
from transifex.txcommon.tests.base import BaseTestCase

class TestTimeline(BaseTestCase):

    def setUp(self):
        super(TestTimeline, self).setUp()

        # Sanity checks
        self.assertTrue(Project.objects.count() >= 1,
            msg="Base test case didn't create any projects"
        )

        self.url_user_timeline = reverse('user_timeline')
        self.url_user_profile = reverse('userena_profile_detail',
            args=[self.user['registered'].username])

        self.url_project_timeline = reverse('project_timeline',
            args=[self.project.slug])
        self.url_private_project_timeline = reverse('project_timeline',
            args=[self.project_private.slug])
        self.url_project_edit = reverse('project_edit',
            args=[self.project.slug])

    def test_regular(self):
        """Test regular registered user."""

        # Check user timeline page as regular user
        resp = self.client['registered'].get(self.url_user_timeline)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue("Timeline" in resp.content)
        a = ("The query returned " in resp.content)
        b = ("None available" in resp.content)
        self.assertTrue( a or b)

        # Check project timeline page as regular user
        resp = self.client['registered'].get(self.url_project_timeline)
        self.assertEqual(resp.status_code, 200)

        # Check private project timeline page as regular user
        resp = self.client['registered'].get(self.url_private_project_timeline)
        self.assertEqual(resp.status_code, 403)

        # Anonymous should require a login
        resp = self.client['anonymous'].get(self.url_project_timeline, follow=True)
        #FIXME
        #self.assertTemplateUsed(resp, 'userena/signin_form.html')
        self.assertContains(resp, 'input type="submit" class="i16 tick '\
                'buttonized" value="Sign in"', status_code=200)

        # Check whether link to user timeline is injected to profile page
        # Comment out since user timeline is not visible in the user profile
        # resp = self.client['registered'].get(self.url_user_profile)
        # self.assertEqual(resp.status_code, 200)
        # self.assertTrue("My Timeline" in resp.content)

    def test_maint(self):
        """Test maintainer."""

        # Check user timeline page as regular user
        resp = self.client['registered'].get(self.url_user_timeline)
        self.assertEqual(resp.status_code, 200)

        # Check project timeline as maintainer
        resp = self.client['maintainer'].get(self.url_project_timeline)
        self.assertEqual(resp.status_code, 200)

        # Fetch project edit page and check that timeline is there
        resp = self.client['maintainer'].get(self.url_project_edit)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.url_project_timeline in resp.content)
