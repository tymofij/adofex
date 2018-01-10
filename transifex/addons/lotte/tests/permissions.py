# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.db.models.loading import get_model
from django.utils import simplejson as json
from transifex.txcommon.tests.base import BaseTestCase
from utils import *

Translation = get_model('resources', 'Translation')


class LottePermissionsTests(BaseTestCase):

    def setUp(self):
        super(LottePermissionsTests, self).setUp()
        self.entity = self.resource.entities[0]
        self.DataTable_params = default_params()

    def tearDown(self):
        super(LottePermissionsTests, self).tearDown()

    def test_anon(self):
        """
        Test anonymous user
        """
        login_url = reverse('userena_signin')

        # Test main lotte page
        page_url = reverse('translate_resource', args=[
            self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '%s?next=%s' % (login_url, page_url))

        # Test view_strings
        page_url = reverse('view_strings', args=[
            self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 200)

        # Test exit
        page_url = reverse('exit_lotte', args=[
            self.project.slug, self.language.code])
        # GET
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '%s?next=%s' % (login_url, page_url))
        # POST
        resp = self.client['anonymous'].post(page_url)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '%s?next=%s' % (login_url, page_url))

        # Test delete translation
        page_url = reverse('delete_translation', args=[
            self.project.slug, self.language.code])
        # GET
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        # POST
        resp = self.client['anonymous'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Test stringset handling Ajax call
        page_url = reverse('stringset_handling',
            args=[self.project.slug, self.resource.slug, self.language.code])
        # POST
        resp = self.client['anonymous'].post(page_url, self.DataTable_params)
        self.assertEqual(resp.status_code, 200)
        # GET
        resp = self.client['anonymous'].get(page_url, self.DataTable_params)
        self.assertEqual(resp.status_code, 200)

        # Create source language translation. This is needed to push
        # additional translations
        source_trans = Translation.objects.get(
            source_entity=self.source_entity, language = self.language_en,
            rule=5
        )
        trans_lang = self.language.code
        trans = "foo"
        # Create new translation
        resp = self.client['anonymous'].post(reverse('push_translation',
            args=[self.project.slug, trans_lang,]),
            json.dumps({'strings':[{'id':source_trans.id,'translations':{ 'other': trans}}]}),
            content_type='application/json' )
        self.assertEqual(resp.status_code, 302)
        source_trans.delete()

        # Test translation details
        page_url = reverse('tab_details_snippet',
            args=[self.entity.id, self.language.code])
        # Test the response contents
        resp = self.client['anonymous'].get(page_url)
        self.assertEqual(resp.status_code, 200)
       
        # Test access for developer_comment_extra view
        data = {'source_entity_id':self.entity.id,
            'comment_extra': 'Extra comment'}
        page_url = reverse('developer_comment_extra',
            args=[self.project.slug])
        # Test the response contents
        resp = self.client['anonymous'].post(page_url, data)
        self.assertEqual(resp.status_code, 302)
        self.assertRedirects(resp, '%s?next=%s' % (login_url, page_url))

    def test_registered(self):
        """
        Test random registered user
        """
        # Test main lotte page
        page_url = reverse('translate_resource', args=[
            self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 403)

        # Check access to main lotte page for resource not accepting
        # translations.
        self.resource.accept_translations = False
        self.resource.save()
        page_url = reverse('translate_resource', args=[
            self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        self.resource.accept_translations = True
        self.resource.save()

        # Test view_strings
        page_url = reverse('view_strings', args=[
            self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 200)

        # Test exit
        page_url = reverse('exit_lotte', args=[
            self.project.slug, self.language.code])
        # GET
        resp = self.client['registered'].get(page_url, follow=True)
        self.assertEqual(resp.status_code, 405)
        # POST
        resp = self.client['registered'].post(page_url, follow=True)
        self.assertEqual(resp.status_code, 403)

        # Test delete translation
        page_url = reverse('delete_translation', args=[
            self.project.slug, self.language.code])
        # GET
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        # POST
        resp = self.client['team_member'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Test stringset handling Ajax call
        page_url = reverse('stringset_handling',
            args=[self.project.slug, self.resource.slug, self.language.code])
        # POST
        resp = self.client['registered'].post(page_url, self.DataTable_params)
        self.assertEqual(resp.status_code, 200)
        # GET
        resp = self.client['registered'].get(page_url, self.DataTable_params)
        self.assertEqual(resp.status_code, 200)

        # Create source language translation. This is needed to push
        # additional translations
        source_trans = Translation.objects.get(
            source_entity=self.source_entity,
            language = self.language_en, rule=5
        )
        trans_lang = self.language.code
        trans = "foo"
        # Create new translation
        resp = self.client['registered'].post(reverse('push_translation',
            args=[self.project.slug, trans_lang,]),
            json.dumps({'strings':[{'id':source_trans.id,'translations':{ 'other': trans}}]}),
            content_type='application/json' )
        self.assertEqual(resp.status_code, 403)
        source_trans.delete()

        # Test translation details
        page_url = reverse('tab_details_snippet',
            args=[self.entity.id, self.language.code])
        # Test the response contents
        resp = self.client['registered'].get(page_url)
        self.assertEqual(resp.status_code, 200)

        # Test access for developer_comment_extra view
        data = {'source_entity_id':self.entity.id,
            'comment_extra': 'Extra comment'}
        page_url = reverse('developer_comment_extra',
            args=[self.project.slug])
        # Test the response contents
        resp = self.client['registered'].post(page_url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Permission error.')

    def test_team_member(self):
        """
        Test team_member permissions
        """
        # Test main lotte page
        page_url = reverse('translate_resource', args=[
            self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 200)

        # Check access to main lotte page for resource not accepting
        # translations.
        self.resource.accept_translations = False
        self.resource.save()
        page_url = reverse('translate_resource', args=[
            self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        self.resource.accept_translations = True
        self.resource.save()

        # Test view_strings
        page_url = reverse('view_strings', args=[
            self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 200)

        # Test exit
        page_url = reverse('exit_lotte', args=[
            self.project.slug, self.language.code])
        # GET
        resp = self.client['team_member'].get(page_url, follow=True)
        self.assertEqual(resp.status_code, 405)
        # POST
        resp = self.client['team_member'].post(page_url, '{"updated": "updated"}',
            content_type='application/json', follow=True)
        self.assertEqual(resp.status_code, 200)

        # Test delete translation
        page_url = reverse('delete_translation', args=[
            self.project.slug, self.language.code])
        # GET
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        # POST
        resp = self.client['team_member'].post(page_url)
        self.assertEqual(resp.status_code, 403)

        # Test stringset handling Ajax call
        page_url = reverse('stringset_handling',
            args=[self.project.slug, self.resource.slug, self.language.code])
        # POST
        resp = self.client['team_member'].post(page_url, self.DataTable_params)
        self.assertEqual(resp.status_code, 200)
        # GET
        resp = self.client['team_member'].get(page_url, self.DataTable_params)
        self.assertEqual(resp.status_code, 200)

        # Test main lotte page for other team. This should fail
        page_url = reverse('translate_resource', args=[
            self.project.slug, self.resource.slug, 'el'])
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 403)

        # Create source language translation. This is needed to push
        # additional translations
        source_trans = Translation.objects.get(
            source_entity=self.source_entity,
            language = self.language_en, rule=5
        )
        trans_lang = self.language.code
        trans = "foo"
        # Create new translation
        resp = self.client['team_member'].post(reverse('push_translation',
            args=[self.project.slug, trans_lang,]),
            json.dumps({'strings':[{'id':source_trans.id,'translations':{ 'other': trans}}]}),
            content_type='application/json' )
        self.assertEqual(resp.status_code, 200)

        # Create new translation in other team. Expect this to fail
        resp = self.client['team_member'].post(reverse('push_translation',
            args=[self.project.slug, 'ru']),
            json.dumps({'strings':[{'id':source_trans.id,'translations':{ 'other': trans}}]}),
            content_type='application/json' )
        self.assertEqual(resp.status_code, 403)
        source_trans.delete()

        # Test translation details
        page_url = reverse('tab_details_snippet',
            args=[self.entity.id, self.language.code])
        # Test the response contents
        resp = self.client['team_member'].get(page_url)
        self.assertEqual(resp.status_code, 200)

        # Test access for developer_comment_extra view
        data = {'source_entity_id':self.entity.id,
            'comment_extra': 'Extra comment'}
        page_url = reverse('developer_comment_extra',
            args=[self.project.slug])
        # Test the response contents
        resp = self.client['team_member'].post(page_url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Permission error.')


    def test_maintainer(self):
        """
        Test maintainer permissions
        """
        # Test main lotte page
        page_url = reverse('translate_resource', args=[
            self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 200)

        # Check access to main lotte page for resource not accepting
        # translations.
        self.resource.accept_translations = False
        self.resource.save()
        page_url = reverse('translate_resource', args=[
            self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 403)
        self.resource.accept_translations = True
        self.resource.save()

        # Test view_strings
        page_url = reverse('view_strings', args=[
            self.project.slug, self.resource.slug, self.language.code])
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 200)

        # Test exit
        page_url = reverse('exit_lotte', args=[
            self.project.slug, self.language.code])
        # GET
        resp = self.client['maintainer'].get(page_url, follow=True)
        self.assertEqual(resp.status_code, 405)
        # POST
        resp = self.client['maintainer'].post(page_url, '{"updated": "updated"}',
            content_type='application/json', follow=True)
        self.assertEqual(resp.status_code, 200)

        # Test delete translation
        page_url = reverse('delete_translation', args=[
            self.project.slug, self.language.code])
        # GET
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 400)
        # POST
        #resp = self.client['maintainer'].post(page_url, json.dumps(
            #{"to_delete":[self.entity.id]}),
            #content_type='application/json')
        #self.assertEqual(resp.status_code, 200)

        # Test stringset handling Ajax call
        page_url = reverse('stringset_handling',
            args=[self.project.slug, self.resource.slug, self.language.code])
        # POST
        resp = self.client['maintainer'].post(page_url, self.DataTable_params)
        self.assertEqual(resp.status_code, 200)
        # GET
        resp = self.client['maintainer'].get(page_url, self.DataTable_params)
        self.assertEqual(resp.status_code, 200)

        # Create source language translation. This is needed to push
        # additional translations
        source_trans = Translation.objects.get(
            source_entity=self.source_entity,
            language = self.language_en, rule=5
        )
        trans_lang = self.language.code
        trans = "foo"
        # Create new translation
        resp = self.client['maintainer'].post(reverse('push_translation',
            args=[self.project.slug, trans_lang,]),
            json.dumps({'strings':[{'id':source_trans.id,'translations':{ 'other': trans}}]}),
            content_type='application/json' )
        self.assertEqual(resp.status_code, 200)
        source_trans.delete()

        # Test translation details
        page_url = reverse('tab_details_snippet',
            args=[self.entity.id, self.language.code])
        # Test the response contents
        resp = self.client['maintainer'].get(page_url)
        self.assertEqual(resp.status_code, 200)

        # Test access for developer_comment_extra view
        data = {'source_entity_id':self.entity.id,
            'comment_extra': 'Extra comment'}
        page_url = reverse('developer_comment_extra',
            args=[self.project.slug])
        # Test the response contents
        resp = self.client['maintainer'].post(page_url, data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Extra comment')
