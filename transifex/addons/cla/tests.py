"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from cla.models import Cla, ClaSignature
from transifex.projects.models import Project
from transifex.resources.models import Language
from transifex.txcommon.tests.base import BaseTestCase


class CLAMixin(BaseTestCase):

    def setUp(self):
        super(CLAMixin, self).setUp()
        self.cla = Cla(
            project=self.project,
            license_text="You have to agree to this test contribution license "\
                          "agreement before you contribute to my project."
        )
        self.cla.save()
        assert self.cla
        assert self.cla.id


class ModelApiTest(CLAMixin):

    def test_assign_signature(self):
        rel = ClaSignature(user=self.user['registered'], cla=self.cla)
        rel.save()
        assert rel
        assert rel.id
        self.assertEqual(rel.user, self.user['registered'])
        self.assertEqual(rel.cla, self.cla)
        self.assertEqual(self.user['registered'].cla_set.all()[0], self.cla)
        self.assertEqual(self.cla.users.all()[0], self.user['registered'])
        assert rel.created_at

    def test_signatures_get_deleted_on_cla_delete(self):
        rel = ClaSignature(user=self.user['registered'], cla=self.cla)
        rel.save()
        self.cla.delete()
        self.assertRaises(ClaSignature.DoesNotExist,
                          lambda: ClaSignature.objects.get(id=rel.id))

    def test_signatures_get_deleted_on_cla_update(self):
        rel = ClaSignature(user=self.user['registered'], cla=self.cla)
        rel.save()
        self.cla.license_text = "changed license text"
        self.cla.save()
        self.assertRaises(ClaSignature.DoesNotExist,
                          lambda: ClaSignature.objects.get(id=rel.id))


class UserExperienceTest(CLAMixin):
    @classmethod
    def setUpClass(cls):
        super(UserExperienceTest, cls).setUpClass()
        cls.language_fr = Language.objects.get(code='fr')

    def setUp(self):
        super(UserExperienceTest, self).setUp()
        self.post_url = reverse("project_access_control_edit",
                args=[self.project.slug])
        resp = self.client['maintainer'].post(self.post_url, {
            'project_type': "typical", 'access_control': "limited_access",
            'cla_enable': True, 'next': self.post_url,
            'cla_license_text': "this is the CLA of project kbairak",
        })

    def test_cla_sign(self):
        response = self.client['registered'].get(
            reverse('cla_project_sign', args=[self.project.slug])
        )
        self.assertEqual(response.status_code, 403)
        response = self.client['team_member'].get(
            reverse('cla_project_sign', args=[self.project.slug])
        )
        self.assertEqual(response.status_code, 200)
        response = self.client['team_member'].post(
            reverse('cla_project_sign', args=[self.project.slug]),
            {'cla_sign': 'on'}, follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You have signed the CLA")

    def test_cla_not_saved_is_cla_textarea_empty(self):
        response = self.client['maintainer'].post(self.post_url, {
            'project_type': "typical", 'access_control': "limited_access",
            'cla_enable': True, 'cla_license_text': "", 'next': self.post_url
        })
        self.assertContains(response, "This field is required.", count=1)

    def test_team_request_reject_if_not_cla(self):
        response = self.client['registered'].get(
            reverse('project_detail', args=[self.project.slug])
        )
        self.assertContains(response, "Request language")
        response = self.client['registered'].post(
            reverse('team_request', args=[self.project.slug]),
            {'language': self.language_fr.pk},
            follow=True
        )
        self.assertContains(response, 'Contribution License Agreement', count=1)

    def test_team_request_accept_if_cla(self):
        response = self.client['registered'].get(
            reverse('project_detail', args=[self.project.slug]),
        )
        self.assertContains(response, "Request language")
        response = self.client['registered'].post(
            reverse('team_request', args=[self.project.slug]),
            {'cla_sign': True, 'language': self.language_fr.pk},
            follow=True
        )
        self.assertContains(response, 'French')

    def test_cla_checkbox_shown_in_team_request(self):
        response = self.client['registered'].get(
            reverse('project_detail', args=[self.project.slug]),
        )
        self.assertContains(response, "I have read and agree with this project", count=1)

    def test_team_join_reject_if_not_cla(self):
        self.client['team_coordinator'].post(
            reverse('team_request', args=[self.project.slug]),
            {'cla_sign': True, 'language': self.language_fr.pk}
        )
        self.client['maintainer'].post(
            reverse('team_request_approve', args=[self.project.slug, 'fr']),
            {'team_request_approve': "Approve"}
        )
        response = self.client['registered'].get(
            reverse('team_detail', args=[self.project.slug, 'fr'])
        )
        self.assertContains(response, 'Join language translation')
        response = self.client['registered'].post(
            reverse('team_join_request', args=[self.project.slug, 'fr']),
            {'team_join': "Join this Team"},
            follow=True
        )
        self.assertContains(response, 'Contribution License Agreement')

    def test_team_join_accept_if_cla(self):
        self.client['team_coordinator'].post(
            reverse('team_request', args=[self.project.slug]),
            {'cla_sign': True, 'language': self.language_fr.pk}
        )
        self.client['maintainer'].post(
            reverse('team_request_approve', args=[self.project.slug, 'fr']),
            {'team_request_approve': "Approve"}
        )
        response = self.client['registered'].get(
            reverse('team_detail', args=[self.project.slug, 'fr']),
        )
        self.assertContains(response, 'Join language translation')
        response = self.client['registered'].post(
            reverse('team_join_request', args=[self.project.slug, 'fr']),
            {'cla_sign': True, 'team_join': "Join this Team"},
            follow=True
        )
        self.assertContains(response, 'You requested to join')

    def test_cla_checkbox_shown_in_join(self):
        response = self.client['team_coordinator'].get(
            reverse("project_detail", args=[self.project.slug])
        )
        response = self.client['team_coordinator'].post(
            reverse('team_request', args=[self.project.slug]),
            {'cla_sign': True, 'language': self.language_fr.pk},
            follow=True
        )
        self.client['maintainer'].post(
            reverse('team_request_approve', args=[self.project.slug, 'fr']),
            {'team_request_approve': "Approve"}
        )
        response = self.client['registered'].get(
            reverse('team_detail', args=[self.project.slug, 'fr']),
        )
        self.assertContains(response, "I have read and agree with this project")

    def test_show_cla(self):
        response = self.client['registered'].get(self.cla.get_absolute_url())
        self.assertContains(response, "this is the CLA of project kbairak")

    def test_show_signed_users(self):
        self.client['team_coordinator'].post(
            reverse('team_request', args=[self.project.slug]),
            {'cla_sign': True, 'language': self.language_fr.pk}
        )
        response = self.client['maintainer'].get(self.cla.get_users_url())
        self.assertContains(response, "team_coordinator")

    def test_dont_show_signed_users_if_not_project_maintainer(self):
        self.client['team_coordinator'].post(
            reverse('team_request', args=[self.project.slug]),
            {'cla_sign': True, 'language': self.language_fr.pk}
        )
        response = self.client['team_coordinator'].get(self.cla.get_users_url())
        self.assertEqual(response.status_code, 403)

    def test_outsourced_project_save(self):
        self.project_private.is_hub = True
        self.project_private.save()
        response = self.client['maintainer'].post(self.post_url, {
            'project_type': "outsourced",
            'outsource': self.project_private.id,
            'next': self.post_url,
            'cla_license_text': ''
        }, follow=True)
        assert self.project in self.project_private.outsourcing.all()

__test__ = {"doctest": """
Another way to test that 1 + 1 is equal to 2.

>>> 1 + 1 == 2
True
"""}

