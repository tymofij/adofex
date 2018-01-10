from django.core.urlresolvers import reverse
from transifex.txcommon.tests.base import BaseTestCase


class PrioritiesModelTests(BaseTestCase):
    """Testcase which includes all the tests referring to models interaction."""

    def setUp(self):
        super(PrioritiesModelTests, self).setUp()

    def tearDown(self):
        super(PrioritiesModelTests, self).tearDown()

    def test_priority_creation(self):
        """Test priority creation through signal handler."""
        self.assertTrue(self.resource.priority)

    def test_priority_rotation(self):
        """Test priority level cycling."""
        self.resource.priority.cycle()
        self.assertEqual(self.resource.priority.get_level_display(), 'High')
        self.resource.priority.cycle()
        self.assertEqual(self.resource.priority.get_level_display(), 'Urgent')
        self.resource.priority.cycle()
        self.assertEqual(self.resource.priority.get_level_display(), 'Normal')

class PrioritiesViewTests(BaseTestCase):
    """Testcase which includes all the tests referring to models interaction."""

    def setUp(self):
        super(PrioritiesViewTests, self).setUp()
        self.cycle_resource_priority_url = reverse('cycle_resource_priority',
            args=[self.project.slug, self.resource.slug])

    def tearDown(self):
        super(PrioritiesViewTests, self).tearDown()

    def test_priority_cycle_view(self):
        """Test priority cycle view."""
        self.assertTrue(self.resource.priority)
        # Test the response contents
        resp = self.client['maintainer'].get(self.cycle_resource_priority_url)
        self.assertContains(resp, 'High', status_code=200)
        self.assertTemplateUsed(resp, 'resource_priority_snippet.html')

        resp = self.client['anonymous'].get(self.cycle_resource_priority_url)
        self.assertEqual(resp.status_code, 403)

        resp = self.client['registered'].get(self.cycle_resource_priority_url)
        self.assertEqual(resp.status_code, 403)

        resp = self.client['team_member'].get(self.cycle_resource_priority_url)
        self.assertEqual(resp.status_code, 403)
