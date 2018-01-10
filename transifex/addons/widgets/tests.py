# -*- coding: utf-8 -*-
from transifex.txcommon.tests.base import BaseTestCase
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test.client import Client
from transifex.projects.models import Project

class TestCharts(BaseTestCase):
    def setUp(self):
        super(TestCharts, self).setUp()

    def tearDown(self):
        super(TestCharts, self).tearDown()

    def test_main(self):
        # Check if widgets page is available
        resp = self.client['registered'].get(reverse('project_widgets',
            kwargs={'project_slug': self.project.slug}))
        self.assertEqual(resp.status_code, 200)
        # Check if we got correct file
        self.assertTrue("code_snippet" in resp.content)