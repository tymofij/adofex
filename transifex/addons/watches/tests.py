# -*- coding: utf-8 -*-
import os
from django.core.urlresolvers import reverse
from django.test.client import Client
from transifex.projects.models import Project
from transifex.resources.models import Resource
from transifex.txcommon.tests.base import BaseTestCase, USER_ROLES, NoticeTypes
from transifex.resources.models import Resource
from transifex.releases.models import Release
from django.utils import simplejson
from django.conf import settings
from notification.models import ObservedItem

class TestWatches(BaseTestCase):

    def setUp(self):
        super(TestWatches, self).setUp()
        self.project_signals = ['project_changed',
                                'project_deleted',
                                'project_release_added',
                                'project_release_deleted',
                                'project_resource_added',
                                'project_resource_deleted']

        self.release_signals = ['project_release_changed',]

        self.resource_signals = ['project_resource_changed']
        # Sanity checks
        self.assertTrue( Project.objects.count() >= 1, msg = "Base test case didn't create any projects" )
        self.assertTrue( Resource.objects.count() >= 1, msg = "Base test case didn't create any resources")
        # Generate watch URLs
        self.url_project_toggle_watch = reverse('project_toggle_watch', args=[self.project.slug])
        self.url_resource_translation_toggle_watch = reverse('resource_translation_toggle_watch',
                args = [self.project.slug, self.resource.slug, self.language.code])

    def test_templates(self):
        """
        Test templates to see if it is properly rendered for different types of users
        """
        for user in USER_ROLES:
            resp = self.client[user].get(self.urls['project'])
            resp1 = self.client[user].get(self.urls['resource_actions'])
            if user != 'anonymous':
                if settings.ENABLE_NOTICES:
                    self.assertContains(resp, "watch_toggle(this, '/ajax/p/%s/toggle_watch/')"%self.project.slug, status_code=200)
                    self.assertContains(resp1, "watch_toggle(this, '/ajax/p/%s/resource/%s/l/%s/toggle_watch/')"%
                                        (self.project.slug, self.resource.slug, self.language.code), status_code=200)
                else:
                    self.assertNotContains(resp, "watch_toggle(this, '/ajax/p/%s/toggle_watch/')"%self.project.slug, status_code=200)
                    self.assertNotContains(resp1, "watch_toggle(this, '/ajax/p/%s/resource/%s/l/%s/toggle_watch/')"%
                                        (self.project.slug, self.resource.slug, self.language.code), status_code=200)


            else:
                self.assertNotContains(resp, '''onclick="watch_toggle(this, '/ajax/p/%s/toggle_watch/')" title="Watch it"'''%self.project.slug, status_code=200)
                self.assertNotContains(resp1, "watch_toggle(this, '/ajax/p/%s/resource/%s/l/%s/toggle_watch/')"%
                                    (self.project.slug, self.resource.slug, self.language.code), status_code=200)

    def test_project_toggle_watch(self):
        """
        Test toggle watch for project
        """
        for user in USER_ROLES:
            resp = self.client[user].post(self.url_project_toggle_watch, {},)
            if user != 'anonymous':
                self.assertEqual(resp.status_code, 200)
                json = simplejson.loads(resp.content)
                if settings.ENABLE_NOTICES:
                    self.assertTrue(json['project'])
                    self.assertEqual(json['url'], '/ajax/p/%s/toggle_watch/'%self.project.slug)
                    self.assertEqual(json['style'], 'watch_remove')
                    self.assertEqual(json['title'], 'Stop watching this project')
                    self.assertEqual(json['error'], None)
                    self.assertEqual(ObservedItem.objects.filter(content_type__model='project',
                        signal__in=self.project_signals, object_id=self.project.id, user__username=user).count(), 6)
                else:
                    self.assertEqual(json['error'], "Notification is not enabled")
            else:
                self.assertEqual(resp.status_code, 302)

        resp = self.client['maintainer'].post(self.urls['release_create'], {
            'slug': 'nice-release',
            'name': 'Nice Release',
            'project': self.project.id,
            'resources': self.project.resources.all()[0].id,
            'description': '',
            'release_date': '',
            'resources_text': '',
            'stringfreeze_date': '',
            'homepage': '',
            'long_description': '',
            'develfreeze_date': '',
        }, follow=True)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "projects/release_detail.html")

        r = Release.objects.get(slug='nice-release')
        self.assertEqual(ObservedItem.objects.filter(content_type__model='release',
            signal__in=self.release_signals, object_id=Release.objects.get(
                slug='nice-release', project=self.project).id,
                 user__username='maintainer').count(), 1)

        self.pofile_path = os.path.join(
            settings.TX_ROOT, 'resources/tests/lib/pofile'
        )
        self.po_file = os.path.join(self.pofile_path, "tests.pot")
        self.url_create_resource = reverse(
            'apiv2_resources', kwargs={'project_slug': self.project.slug}
        )
        with open(self.po_file) as f:
            content = f.read()

        res = self.client['maintainer'].post(
            self.url_create_resource,
            data=simplejson.dumps({
                    'name': "resource1",
                    'slug': 'r1',
                    'i18n_type': 'PO',
                    'content': content,
            }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 201)
        new_resource = Resource.objects.get(slug='r1', project=self.project)
        self.assertEqual(ObservedItem.objects.filter(content_type__model='resource',
            signal__in=self.resource_signals, object_id=new_resource.id).count(), 6)

        for user in USER_ROLES:
            resp = self.client[user].post(self.url_project_toggle_watch, {},)
            if user != 'anonymous':
                self.assertEqual(resp.status_code, 200)
                json = simplejson.loads(resp.content)
                if settings.ENABLE_NOTICES:
                    self.assertTrue(json['project'])
                    self.assertEqual(json['url'], '/ajax/p/%s/toggle_watch/'%self.project.slug)
                    self.assertEqual(json['style'], 'watch_add')
                    self.assertEqual(json['title'], 'Watch this project')
                    self.assertEqual(json['error'], None)
                else:
                    self.assertEqual(json['error'], "Notification is not enabled")
            else:
                self.assertEqual(resp.status_code, 302)

    def test_resource_translation_toggle_watch(self):
        """
        Test toggle watch for resource translation
        """
        for user in USER_ROLES:
            resp = self.client[user].post(self.url_resource_translation_toggle_watch, {},)
            if user not in ['anonymous', 'registered']:
                self.assertEqual(resp.status_code, 200)
                json = simplejson.loads(resp.content)
                if settings.ENABLE_NOTICES:
                    self.assertEqual(json['url'], '/ajax/p/%s/resource/%s/l/%s/toggle_watch/'%
                                     (self.project.slug, self.resource.slug, self.language.code))
                    self.assertEqual(json['style'], 'watch_remove')
                    self.assertEqual(json['title'], 'Stop watching')
                    self.assertEqual(json['error'], None)
                else:
                    self.assertEqual(json['error'], "Notification is not enabled")
            else:
                if user == 'anonymous':
                    self.assertEqual(resp.status_code, 302)
                else:
                    if settings.ENABLE_NOTICES:
                        self.assertEqual(resp.status_code, 403)
                    else:
                        self.assertContains(resp, "Notification is not enabled", status_code=200)

            resp = self.client[user].post(self.url_resource_translation_toggle_watch, {},)
            if user not in ['anonymous', 'registered']:
                self.assertEqual(resp.status_code, 200)
                json = simplejson.loads(resp.content)
                if settings.ENABLE_NOTICES:
                    self.assertEqual(json['url'], '/ajax/p/%s/resource/%s/l/%s/toggle_watch/'%
                                 (self.project.slug, self.resource.slug, self.language.code))
                    self.assertEqual(json['style'], 'watch_add')
                    self.assertEqual(json['title'], 'Watch it')
                    self.assertEqual(json['error'], None)
                else:
                    self.assertEqual(json['error'], "Notification is not enabled")
            else:
                if user == 'anonymous':
                    self.assertEqual(resp.status_code, 302)
                else:
                    if settings.ENABLE_NOTICES:
                        self.assertEqual(resp.status_code, 403)
                    else:
                        self.assertContains(resp, "Notification is not enabled", status_code=200)


