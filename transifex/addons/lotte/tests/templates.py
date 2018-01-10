# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from transifex.txcommon.tests.base import BaseTestCase
from transifex.resources.models import Translation
from utils import *

try:
    import json
except ImportError:
    import simplejson as json


class LotteTemplateTests(BaseTestCase):

    def setUp(self):
        super(LotteTemplateTests, self).setUp()
        # URLs
        self.translate_view_url = reverse('translate_resource',
            args=[self.project.slug, self.resource.slug, self.language.code])
        self.translate_content_arabic_url = reverse('stringset_handling',
            args=[self.project.slug, self.resource.slug, self.language_ar.code])

    def tearDown(self):
        super(LotteTemplateTests, self).tearDown()

    def test_breadcrumbs(self):
        resp = self.client['team_member'].get(self.translate_view_url)
        self.assertContains(resp, 'Translate')

    def test_filters(self):
        """Test that more languages, filter by users, resources appear."""

        # Test the response contents
        resp = self.client['team_member'].get(self.translate_view_url)
        self.assertTemplateUsed(resp, 'translate.html')
        self.assertContains(resp, 'More languages', status_code=200)
        self.assertContains(resp,
            'Show translations in<br /> the selected languages')
        self.assertContains(resp, '<input class="more_languages" type="checkbox"')
        self.assertContains(resp, 'Filter by users')
        self.assertContains(resp,
            'Show only the translations<br /> by the selected users')
        self.assertContains(resp, 'No active contributor!')

    def test_statistics_div(self):
        """Test that statistics div appears correctly."""

        # Test the response contents
        resp = self.client['team_member'].get(self.translate_view_url)
        self.assertTemplateUsed(resp, 'translate.html')

        self.assertContains(resp, 'Translated', status_code=200)
        self.assertContains(resp, 'Remaining')
        self.assertContains(resp, 'Modified')
        self.assertContains(resp, 'Total')
        self.assertContains(resp, ('<input id="translated" class="filters" '
            'type="checkbox"  name="only_translated"/>'))
        self.assertContains(resp, ('<input id="untranslated" class="filters" '
            'type="checkbox" checked="checked" name="only_untranslated"/>'))

    def test_footpanel_div(self):
        """Check that footpanel html snippet appears correctly."""
        # Test the response contents
        resp = self.client['team_member'].get(self.translate_view_url)
        self.assertTemplateUsed(resp, 'translate.html')

        self.assertContains(resp, 'General settings', status_code=200)
        self.assertContains(resp, 'Verbose editing')
        self.assertContains(resp, 'Auto save')

    def test_global_buttons(self):
        """Check that "Save all", "Delete translations", "Save and Exit" appear."""
        # Test the response contents
        resp = self.client['team_member'].get(self.translate_view_url)
        self.assertTemplateUsed(resp, 'translate.html')

        self.assertContains(resp, 'Save all', status_code=200)
        self.assertContains(resp, 'Save and Exit')
        # For the team_member "delete" should not appear
        self.assertNotContains(resp, 'Delete translations')

        # Test the response contents
        resp = self.client['maintainer'].get(self.translate_view_url)
        self.assertTemplateUsed(resp, 'translate.html')
        # For the team_member "delete" should not appear
        self.assertContains(resp, 'Delete translations')

    def test_push_translation_perms(self):
        """Test the push translation view"""
        for user in ['anonymous', 'registered']:
            pass

        for user in ['team_member', 'maintainer', 'team_coordinator']:
            pass
