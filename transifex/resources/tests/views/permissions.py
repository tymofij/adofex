# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.core import serializers
from django.test.client import Client
from transifex.languages.models import Language
from transifex.resources.models import Resource, Translation
from transifex.txcommon.tests.base import BaseTestCase

from django.utils import simplejson as json


class PermissionsTest(BaseTestCase):
    """Test view permissions"""

    def seUp(self):
        super(PermissionsTest, self).setUp()

    def test_anon(self):
        """
        Test anonymous user
        """
        # Delete Translations
        page_url = reverse('resource_translations_delete',
            args=[self.project.slug, self.resource.slug,self.language.code])
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['anonymous'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check if resource gets deleted successfully
        page_url = reverse('resource_delete',
            args=[self.project.slug, self.resource.slug])
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['anonymous'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check if user is able to access resource details
        resp = self.client['anonymous'].get(reverse('resource_detail',
            args=[self.project.slug, self.resource.slug]))
        self.assertEqual(resp.status_code, 200)

        # Check if user is able to access resource edit
        page_url = reverse('resource_edit',
            args=[self.project.slug, self.resource.slug])
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['anonymous'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check the popup
        page_url = reverse('resource_actions',
            args=[self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['anonymous'].post(page_url)
        self.assertEqual(resp.status_code, 200)

        # Check the ajax view which returns more resources in project detail page.
        resp = self.client['anonymous'].post(reverse('project_resources',
            args=[self.project.slug, 5]))
        self.assertEqual(resp.status_code, 200)
        resp = self.client['anonymous'].post(reverse('project_resources_more',
            args=[self.project.slug, 5]))
        self.assertEqual(resp.status_code, 200)

        # Check that anonymous user is redirected to signin page
        page_url = reverse('clone_translate',
            args=[self.project.slug, self.resource.slug, self.language_en.code,
                  self.language.code])
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/accounts/signin/?next=%s' % page_url)
        resp = self.client['anonymous'].post(page_url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/accounts/signin/?next=%s' % page_url)

        # Check lock and get translation file perms
        page_url = reverse('lock_and_download_for_translation',
            args=[self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/accounts/signin/?next=%s' % page_url)
        resp = self.client['anonymous'].post(page_url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/accounts/signin/?next=%s' % page_url)

        # Check download file perms
        page_url = reverse('download_for_translation',
            args=[self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/accounts/signin/?next=%s' % page_url)
        resp = self.client['anonymous'].post(page_url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/accounts/signin/?next=%s' % page_url)

        #PRIVATE PROJECT CHECKS
        # Delete Translations
        page_url = reverse('resource_translations_delete',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language.code])
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['anonymous'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check if resource gets deleted successfully
        page_url = reverse('resource_delete',
            args=[self.project_private.slug, self.resource_private.slug])
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['anonymous'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check if user is able to access resource details
        resp = self.client['anonymous'].get(reverse('resource_detail',
            args=[self.project_private.slug, self.resource_private.slug]))
        self.assertEqual(resp.status_code, 403)

        # Check if user is able to access resource edit
        page_url = reverse('resource_edit',
            args=[self.project_private.slug, self.resource_private.slug])
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['anonymous'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check the popup
        page_url = reverse('resource_actions',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language_ar.code])
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['anonymous'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check the ajax view which returns more resources in project detail page.
        resp = self.client['anonymous'].post(reverse('project_resources',
            args=[self.project_private.slug, 5]))
        self.assertEqual(resp.status_code, 403)
        resp = self.client['anonymous'].post(reverse('project_resources_more',
            args=[self.project_private.slug, 5]))
        self.assertEqual(resp.status_code, 403)

        # Check that anonymous user is redirected to signin page
        page_url = reverse('clone_translate',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language_en.code,
                  self.language.code])
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/accounts/signin/?next=%s' % page_url)
        resp = self.client['anonymous'].post(page_url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/accounts/signin/?next=%s' % page_url)

        # Check lock and get translation file perms
        page_url = reverse('lock_and_download_for_translation',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language.code])
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/accounts/signin/?next=%s' % page_url)
        resp = self.client['anonymous'].post(page_url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/accounts/signin/?next=%s' % page_url)

        # Check download file perms
        page_url = reverse('download_for_translation',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language.code])
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/accounts/signin/?next=%s' % page_url)
        resp = self.client['anonymous'].post(page_url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '/accounts/signin/?next=%s' % page_url)


    def test_registered(self):
        """
        Test random registered user
        """
        # Delete Translations
        page_url = reverse('resource_translations_delete',
            args=[self.project.slug, self.resource.slug,self.language.code])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['registered'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check if resource gets deleted successfully
        page_url = reverse('resource_delete',
            args=[self.project.slug, self.resource.slug])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['registered'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check if user is able to access resource details
        page_url = reverse('resource_detail',
            args=[self.project.slug, self.resource.slug])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['registered'].post(page_url)
        self.assertEqual(resp.status_code, 200)

        # Check if user is able to access resource edit
        page_url = reverse('resource_edit',
            args=[self.project.slug, self.resource.slug])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['registered'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check the popup
        page_url = reverse('resource_actions',
            args=[self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['registered'].post(page_url)
        self.assertEqual(resp.status_code, 200)

        # Check the ajax view which returns more resources in project detail page.
        resp = self.client['registered'].post(reverse('project_resources',
            args=[self.project.slug, 5]))
        self.assertEqual(resp.status_code, 200)
        resp = self.client['registered'].post(reverse('project_resources_more',
            args=[self.project.slug, 5]))
        self.assertEqual(resp.status_code, 200)

        # Check clone language perms
        page_url = reverse('clone_translate',
            args=[self.project.slug, self.resource.slug, self.language_en.code,
                  self.language.code])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['registered'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check 'lock and get translation file' perms
        page_url = reverse('lock_and_download_for_translation',
            args=[self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['registered'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check download file perms
        page_url = reverse('download_for_translation',
            args=[self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 302)
        resp = self.client['registered'].post(page_url)
        self.assertEqual(resp.status_code, 302)

        # PRIVATE PROJECT CHECKS
        # Delete Translations
        page_url = reverse('resource_translations_delete',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language.code])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['registered'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check if resource gets deleted successfully
        page_url = reverse('resource_delete',
            args=[self.project_private.slug, self.resource_private.slug])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['registered'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check if user is able to access resource details
        page_url = reverse('resource_detail',
            args=[self.project_private.slug, self.resource_private.slug])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['registered'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check if user is able to access resource edit
        page_url = reverse('resource_edit',
            args=[self.project_private.slug, self.resource_private.slug])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['registered'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check the popup
        page_url = reverse('resource_actions',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language_ar.code])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['registered'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check the ajax view which returns more resources in project detail page.
        resp = self.client['registered'].post(reverse('project_resources',
            args=[self.project_private.slug, 5]))
        self.assertEqual(resp.status_code, 403)
        resp = self.client['registered'].post(reverse('project_resources_more',
            args=[self.project_private.slug, 5]))
        self.assertEqual(resp.status_code, 403)

        # Check clone language perms
        page_url = reverse('clone_translate',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language_en.code,
                  self.language.code])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['registered'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check 'lock and get translation file' perms
        page_url = reverse('lock_and_download_for_translation',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language.code])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['registered'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check download file perms
        page_url = reverse('download_for_translation',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language.code])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['registered'].post(page_url)
        self.assertEqual(resp.status_code, 403)


    def test_team_member(self):
        """
        Test team_member permissions
        """
        # Delete Translations
        page_url = reverse('resource_translations_delete',
            args=[self.project.slug, self.resource.slug,self.language.code])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['team_member'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check if resource gets deleted
        page_url = reverse('resource_delete',
            args=[self.project.slug, self.resource.slug])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['team_member'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check if user is able to access resource details
        page_url = reverse('resource_detail',
                           args=[self.project.slug, self.resource.slug])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['team_member'].post(page_url)
        self.assertEqual(resp.status_code, 200)

        # Check if user is able to access resource edit
        page_url = reverse('resource_edit',
                           args=[self.project.slug, self.resource.slug])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['team_member'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check the popup
        page_url = reverse('resource_actions',
            args=[self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['team_member'].post(page_url)
        self.assertEqual(resp.status_code, 200)

        # Check the ajax view which returns more resources in project detail page.
        resp = self.client['team_member'].post(reverse('project_resources',
            args=[self.project.slug, 5]))
        self.assertEqual(resp.status_code, 200)
        resp = self.client['team_member'].post(reverse('project_resources_more',
            args=[self.project.slug, 5]))
        self.assertEqual(resp.status_code, 200)

        # Check clone language perms
        page_url = reverse('clone_translate',
            args=[self.project.slug, self.resource.slug, self.language_en.code,
                  self.language.code])
        resp = self.client['team_member'].get(page_url ,follow=True)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['team_member'].post(page_url ,follow=True)
        self.assertEqual(resp.status_code, 200)
        # Check cloning to a non team-member language
        page_url = reverse('clone_translate',
            args=[self.project.slug, self.resource.slug, self.language_en.code,
                  self.language_ar.code])
        resp = self.client['team_member'].get(page_url ,follow=True)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['team_member'].post(page_url ,follow=True)
        self.assertEqual(resp.status_code, 403)

        # Check lock and get translation file perms for resource not accepting
        # translations.
        self.resource.accept_translations = False
        self.resource.save()
        page_url = reverse('lock_and_download_for_translation',
            args=[self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['team_member'].post(page_url)
        self.assertEqual(resp.status_code, 403)
        self.resource.accept_translations = True
        self.resource.save()

        # Check lock and get translation file perms
        page_url = reverse('lock_and_download_for_translation',
            args=[self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['team_member'].post(page_url)
        self.assertEqual(resp.status_code, 200)

        # Check download file perms
        page_url = reverse('download_for_translation',
            args=[self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 302)
        resp = self.client['team_member'].post(page_url)
        self.assertEqual(resp.status_code, 302)

        # PRIVATE PROJECT CHECKS
        # Delete Translations
        page_url = reverse('resource_translations_delete',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language.code])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['team_member'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check if resource gets deleted
        page_url = reverse('resource_delete',
            args=[self.project_private.slug, self.resource_private.slug])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['team_member'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check if user is able to access resource details
        page_url = reverse('resource_detail',
                           args=[self.project_private.slug,
                                 self.resource_private.slug])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['team_member'].post(page_url)
        self.assertEqual(resp.status_code, 200)

        # Check if user is able to access resource edit
        page_url = reverse('resource_edit',
                           args=[self.project_private.slug,
                                 self.resource_private.slug])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['team_member'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check the popup
        page_url = reverse('resource_actions',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language.code])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['team_member'].post(page_url)
        self.assertEqual(resp.status_code, 200)

        # Check the ajax view which returns more resources in project detail page.
        resp = self.client['team_member'].post(reverse('project_resources',
            args=[self.project_private.slug, 5]))
        self.assertEqual(resp.status_code, 200)
        resp = self.client['team_member'].post(reverse('project_resources_more',
            args=[self.project_private.slug, 5]))
        self.assertEqual(resp.status_code, 200)

        # Check clone language perms
        page_url = reverse('clone_translate',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language_en.code, self.language.code])
        resp = self.client['team_member'].get(page_url ,follow=True)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['team_member'].post(page_url ,follow=True)
        self.assertEqual(resp.status_code, 200)
        # Check cloning to a non team-member language
        page_url = reverse('clone_translate',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language_en.code, self.language_ar.code])
        resp = self.client['team_member'].get(page_url ,follow=True)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['team_member'].post(page_url ,follow=True)
        self.assertEqual(resp.status_code, 403)

        # Check lock and get translation file perms
        page_url = reverse('lock_and_download_for_translation',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language.code])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['team_member'].post(page_url)
        self.assertEqual(resp.status_code, 200)

        # Check download file perms
        page_url = reverse('download_for_translation',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language.code])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 302)
        resp = self.client['team_member'].post(page_url)
        self.assertEqual(resp.status_code, 302)


    def test_maintainer(self):
        """
        Test maintainer permissions
        """
        # Check if user is able to access resource details
        page_url = reverse('resource_detail',
                           args=[self.project.slug, self.resource.slug])
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['maintainer'].post(page_url)
        self.assertEqual(resp.status_code, 200)

        # Check if user is able to access resource edit
        page_url = reverse('resource_edit',
                           args=[self.project.slug, self.resource.slug])
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['maintainer'].post(page_url, follow=True)
        self.assertEqual(resp.status_code, 200)

        # Check the popup
        page_url = reverse('resource_actions',
            args=[self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['maintainer'].post(page_url)
        self.assertEqual(resp.status_code, 200)

        # Check the ajax view which returns more resources in project detail page.
        resp = self.client['maintainer'].post(reverse('project_resources',
            args=[self.project.slug, 5]))
        self.assertEqual(resp.status_code, 200)
        resp = self.client['maintainer'].post(reverse('project_resources_more',
            args=[self.project.slug, 5]))
        self.assertEqual(resp.status_code, 200)

        # Check clone language perms
        page_url = reverse('clone_translate',
            args=[self.project.slug, self.resource.slug, self.language_en.code,
                  self.language.code])
        resp = self.client['maintainer'].get(page_url ,follow=True)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['maintainer'].post(page_url ,follow=True)
        self.assertEqual(resp.status_code, 200)

        # Check lock and get translation file perms for resource not accepting
        # translations.
        self.resource.accept_translations = False
        self.resource.save()
        page_url = reverse('lock_and_download_for_translation',
            args=[self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        resp = self.client['maintainer'].post(page_url)
        self.assertEqual(resp.status_code, 403)
        self.resource.accept_translations = True
        self.resource.save()

        # Check lock and get translation file perms
        page_url = reverse('lock_and_download_for_translation',
            args=[self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['maintainer'].post(page_url)
        self.assertEqual(resp.status_code, 200)

        # Check download file perms
        page_url = reverse('download_for_translation',
            args=[self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 302)
        resp = self.client['maintainer'].post(page_url)
        self.assertEqual(resp.status_code, 302)

        # Delete Translations
        page_url = reverse('resource_translations_delete',
                           args=[self.project.slug,
                                 self.resource.slug,self.language.code])
        resp = self.client['maintainer'].get(page_url ,follow=True)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['maintainer'].post(page_url ,follow=True)
        self.assertEqual(resp.status_code, 200)

        # Check if resource gets deleted successfully
        page_url = reverse('resource_delete',
                           args=[self.project.slug, self.resource.slug])
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 302)
        resp = self.client['maintainer'].post(page_url,follow=True)
        self.assertEqual(resp.status_code, 200)

        # PRIVATE PROJECT CHECKS
        # Check if user is able to access resource details
        page_url = reverse('resource_detail',
                           args=[self.project_private.slug,
                                 self.resource_private.slug])
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['maintainer'].post(page_url)
        self.assertEqual(resp.status_code, 200)

        # Check if user is able to access resource edit
        page_url = reverse('resource_edit',
                           args=[self.project_private.slug,
                                 self.resource_private.slug])
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['maintainer'].post(page_url, follow=True)
        self.assertEqual(resp.status_code, 200)

        # Check the popup
        page_url = reverse('resource_actions',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language.code])
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['maintainer'].post(page_url)
        self.assertEqual(resp.status_code, 200)

        # Check the ajax view which returns more resources in project detail page.
        resp = self.client['maintainer'].post(reverse('project_resources',
            args=[self.project_private.slug, 5]))
        self.assertEqual(resp.status_code, 200)
        resp = self.client['maintainer'].post(reverse('project_resources_more',
            args=[self.project_private.slug, 5]))
        self.assertEqual(resp.status_code, 200)

        # Check clone language perms
        page_url = reverse('clone_translate',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language_en.code, self.language.code])
        resp = self.client['maintainer'].get(page_url ,follow=True)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['maintainer'].post(page_url ,follow=True)
        self.assertEqual(resp.status_code, 200)

        # Check lock and get translation file perms
        page_url = reverse('lock_and_download_for_translation',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language.code])
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['maintainer'].post(page_url)
        self.assertEqual(resp.status_code, 200)

        # Check download file perms
        page_url = reverse('download_for_translation',
            args=[self.project_private.slug, self.resource_private.slug,
                  self.language.code])
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 302)
        resp = self.client['maintainer'].post(page_url)
        self.assertEqual(resp.status_code, 302)

        # Delete Translations
        page_url = reverse('resource_translations_delete',
                           args=[self.project_private.slug,
                                 self.resource_private.slug, self.language.code])
        resp = self.client['maintainer'].get(page_url ,follow=True)
        self.assertEqual(resp.status_code, 200)
        resp = self.client['maintainer'].post(page_url ,follow=True)
        self.assertEqual(resp.status_code, 200)

        # Check if resource gets deleted successfully
        page_url = reverse('resource_delete',
                           args=[self.project_private.slug,
                                 self.resource_private.slug])
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 302)
        resp = self.client['maintainer'].post(page_url,follow=True)
        self.assertEqual(resp.status_code, 200)
