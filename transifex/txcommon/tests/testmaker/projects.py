#coding: utf-8
from django.core import management
from django.test import TestCase
from django.core.urlresolvers import reverse
from django_addons.autodiscover import autodiscover_notifications
from transifex.txcommon.tests.base import BaseTestCase, skip

# TODO: Most of these are really unnecessary and will break again at some point
# so they should be removed.

class TestmakerBase(BaseTestCase):
    pass


class TestmakerAnonymous(TestmakerBase):

    login_url = reverse('userena_signin')

    def test__128272158449(self):
        r = self.client["anonymous"].get(self.login_url)
        self.assertEqual(r.status_code, 200)
        self.assertTrue("id_identification" in r.content)


class TestmakerLoggedIn(TestmakerBase):

    def setUp(self, *args, **kwargs):
        super(TestmakerLoggedIn, self).setUp(*args, **kwargs)
        self.c = self.client["team_member"]

    @skip
    def test_projects_128272193615(self):
        r = self.c.get('/projects/', {})
        self.assertEqual(r.status_code, 200)
        self.assertTrue("Test Project" in r.content)

    def test_projectspexample_128272202817(self):
        r = self.c.get('/projects/p/project1/', {})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(unicode(r.context["project"]), u"""Test Project""")
        self.assertEqual(unicode(r.context["languages"][0]), u"""Afrikaans (af)""")

    def test_projectspexampleeditaccess_12828136919(self):
        r = self.c.get('/projects/p/project1/edit/access/', {})
        self.assertEqual(r.status_code, 403)

    # Timeline
    def test_projectspexampletimeline_12828136955(self):
        r = self.c.get('/projects/p/project1/timeline/', {})
        self.assertEqual(r.status_code, 200)

    def test_projectspexampletimeline_128281374911(self):
        r = self.c.get('/projects/p/project1/timeline/', {'action_time': '', 'action_type': '2', })
        self.assertEqual(r.status_code, 200)

    # Widgets
    def test_projectspexamplewidgets_12828136967(self):
        r = self.c.get('/projects/p/project1/widgets/', {})
        self.assertEqual(r.status_code, 200)

    def test_projectspexampleresourceresource1chart_128281369682(self):
        r = self.c.get('/projects/p/project1/resource/resource1/chart/', {})
        self.assertEqual(r.status_code, 200)

    def test_projectspexampleresourceresource1chartinc_js_128281369702(self):
        r = self.c.get('/projects/p/project1/resource/resource1/chart/inc_js/', {})
        self.assertEqual(r.status_code, 200)

    def test_projectspexampleresourceresource1chartimage_png_12828136972(self):
        r = self.c.get('/projects/p/project1/resource/resource1/chart/image_png/', {})
        self.assertEqual(r.status_code, 302)

    def test_projectspexampleresourceresource1chartjson_128281369791(self):
        r = self.c.get('/projects/p/project1/resource/resource1/chart/json/', {'tqx': 'reqId:0', })
        self.assertEqual(r.status_code, 200)

    # Teams
    def test_projectspexampleteamsadd_128281371426(self):
        r = self.c.get('/projects/p/project1/languages/add/', {})
        self.assertEqual(r.status_code, 403)

    def test_projectspexampleteamsadd_128281371653(self):
        r = self.c.post('/projects/p/project1/languages/add/', {'language': '', 'creator': '', 'mainlist': '', 'save_team': 'Save team', 'members_text': '', 'next': '', 'project': '1', 'coordinators': '|', 'coordinators_text': '', 'members': '|', }, follow=True)
        self.assertEqual(r.status_code, 403)

    def test_ajaxajax_lookupusers_128281371984(self):
        r = self.c.get('/ajax/ajax_lookup/users', {'q': 'ed', 'timestamp': '1282813719831', 'limit': '150', })
        self.assertContains(r, 'editor', status_code=200)

    def test_projectspexampleteamsadd_128281372177(self):
        r = self.c.post('/projects/p/project1/languages/add/', {'language': '1', 'creator': '1', 'mainlist': '', 'save_team': 'Save team', 'members_text': '', 'next': '', 'project': '1', 'coordinators': '|1|', 'coordinators_text': '', 'members': '|', }, follow=True)
        self.assertEqual(r.status_code, 403)
        r = self.c.get('/projects/p/project1/language/af/delete/', {})
        self.assertEqual(r.status_code, 403)

    def test_projectspexampleteamafdelete_128282090157(self):
        r = self.c.post('/projects/p/project1/language/ar/delete/', {'team_delete': "Yes, I'm sure!", })
        self.assertEqual(r.status_code, 403)
        r = self.c.get('/projects/p/project1/language/ar/', {})
        self.assertEqual(r.status_code, 200)

    # Edit project
    def test_projectspexampleedit_128281375582(self):
        r = self.c.get('/projects/p/project1/edit/', {})
        self.assertEqual(r.status_code, 403)

    # Other
    def test_faviconico_128281378356(self):
        r = self.c.get('/favicon.ico', {})
        self.assertNotEqual(r.status_code, 404)

