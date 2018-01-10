import os
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test.client import Client
from transifex.projects.models import Project
from transifex.resources.models import Resource
from transifex.txcommon.tests.base import BaseTestCase
from transifex.addons.autofetch.models import URLInfo

class TestFetchUrl(BaseTestCase):

    def setUp(self):
        super(TestFetchUrl, self).setUp()

        # Sanity checks
        self.assertTrue(
            Project.objects.count() >= 1,
            msg = "Base test case didn't create any projects"
        )
        self.assertTrue(
            Resource.objects.count() >= 1,
            msg = "Base test case didn't create any resources"
        )
        # Generate watch URLs
        self.url_fetch_url = reverse(
            'fetch_url', args=[self.project.slug, self.resource.slug]
        )

    def test_fetch_url(self):
        """Test fetch url"""
        resp = self.client['maintainer'].get(self.url_fetch_url)
        self.assertContains(
            resp, '"status": 404, "message": "URL not set for this resource."',
            status_code=200
        )

        source_url = os.path.join(
            settings.TX_ROOT, 'resources/tests/lib/pofile/tests.pot'
        )
        url_info = URLInfo.objects.create(
            source_file_url='file://' + source_url,
            auto_update=True, resource = self.resource
        )
        resp = self.client['maintainer'].get(self.url_fetch_url)
        self.assertContains(
            resp,
            '"status": 200, "message": "Source file updated successfully."',
            status_code=200
        )

        source_url = '/'.join(source_url.split('/')[:-1]) + '/tests1/pot'
        url_info.source_file_url = 'file://' + source_url
        url_info.save()
        resp = self.client['maintainer'].get(self.url_fetch_url)
        self.assertContains(
            resp,
            '"status": 500, "message": "Error updating source file."',
            status_code=200
        )
