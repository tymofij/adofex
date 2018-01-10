# -*- coding: utf-8 -*-
from django.test.client import Client
from transifex.languages.models import Language
from transifex.resources.models import Resource
from transifex.txcommon.tests.base import BaseTestCase


class StatusCodesTest(BaseTestCase):
    """Test that all app URLs return correct status code.

    Moreover, this kind of tests are useful to list down the urls that are
    mounted to the resources app views.
    TODO: Maybe in the future, we need to refactor the tests according to
    request type, e.g. split them to GET and POST sets of URLs.
    """
    # TODO: Fill in the urls

    def setUp(self):
        super(StatusCodesTest, self).setUp()
        self.pages = {
            200: [
                ('/projects/p/%s/resource/%s/' %
                    (self.project.slug, self.resource.slug)),
                ('/projects/p/%s/resource/%s/l/pt_BR/view/' %
                    (self.project.slug, self.resource.slug)),
                ('/projects/p/%s/resources/1' %
                    (self.project.slug,)),
                ('/projects/p/%s/resources/1/more/' %
                    (self.project.slug,)),
                ('/ajax/p/%s/resource/%s/l/pt_BR/actions/' %
                    (self.project.slug, self.resource.slug)),
                ],
            302: [
                ('/projects/p/%s/resource/%s/edit/$' %
                    (self.project.slug, self.resource.slug)),
                ('/projects/p/%s/resource/%s/delete/$' %
                    (self.project.slug, self.resource.slug)),
                ('/projects/p/%s/resource/%s/l/pt_BR/download/for_use/' %
                    (self.project.slug, self.resource.slug)),
                ('/ajax/p/%s/resource/%s/l/pt_BR/download/lock/' %
                    (self.project.slug, self.resource.slug)),
                ],
            403: [
                ('/projects/p/%s/resource/%s/l/pt_BR/delete_all/' %
                    (self.project.slug, self.resource.slug)),
                ],
            404: [
                'projects/p/f00/resource/b4r/',
                ]}

    def testStatusCode(self):
        """Test that the response status code is correct"""

        client = Client()
        for expected_code, pages in self.pages.items():
            for page_url in pages:
                page = client.get(page_url)
                self.assertEquals(page.status_code, expected_code,
                    "Status code for page '%s' was %s instead of %s" %
                    (page_url, page.status_code, expected_code))
