# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from transifex.txcommon.tests import base, utils
from transifex.projects.models import Project

class ProjectViewsTests(base.BaseTestCase, base.NoticeTypes):

    # Note: The Project lookup field is tested elsewhere.
    def setUp(self, *args, **kwargs):
        super(ProjectViewsTests, self).setUp(*args, **kwargs)
        self.url_acc = reverse('project_access_control_edit', args=[self.project.slug])

    # Outsource tests
    def test_project_outsource_good(self):
        """Test that a private project is visible to its maintainer."""
        resp = self.client['maintainer'].get(self.url_acc, {})
        self.assertContains(resp, "Test Project", status_code=200)
        self.assertNotContains(resp, "Test Private Project", status_code=200)


    def test_project_outsource_bad(self):
        # Private project is not visible to another maintainer
        self.assertTrue(self.user['registered'] not in self.project_private.maintainers.all())
        self.project.maintainers.add(self.user['registered'])
        self.assertTrue(self.user['registered'] in self.project.maintainers.all())
        resp = self.client['registered'].get(self.url_acc, {})
        self.assertContains(resp, "Test Project", status_code=200)
        self.assertNotContains(resp, "Test Private Project", status_code=200)

        # Private project cannot be used by another maintainer to outsource
        resp = self.client['registered'].post(self.url_acc, {
            'outsource': self.project_private.id,
            'submit_access_control': 'Save Access Control Settings',
            'access_control': 'outsourced_access',
            'next': '/projects/p/desktop-effects/edit/access/', })
        self.assertFalse(self.project.outsource)
        self.assertTemplateUsed(resp, "projects/project_form_access_control.html")
        self.assertContains(resp, "Select a valid choice.")

    def test_trans_instructions(self):
        """Test the project.trans_instructions model field & templates."""
        self.project.trans_instructions = "http://help.transifex.net/"\
            "technical/contributing.html#updating-translation-files-po-files"
        self.project.save()
        resp = self.client['anonymous'].get(self.urls['project'])
        self.assertContains(resp, "contributing.html")
        self.assertContains(resp, "Translation help pages")

    def test_delete_project(self):
        url = reverse('project_delete', args=[self.project.slug])
        resp = self.client['maintainer'].get(url)
        self.assertContains(resp, "Delete project")
        user = self.user['maintainer']
        resp = self.client['maintainer'].post(url, {'password': base.PASSWORD}, follow=True)
        self.assertContains(resp, "was deleted.")
        self.assertTrue(Project.objects.filter(slug=self.project.slug).count() == 0)
        # Test messages:
        self.assertContains(resp, "message_success")

    def test_project_edit(self):
        resp = self.client['maintainer'].get(self.urls['project_edit'])
        self.assertContains(resp, "Edit the details of your project", status_code=200)
        self.assertContains(resp, self.project.maintainers.all()[0])
        self.assertNotContains(resp, "Owner")
        #save edited project
        DATA = {'project-bug_tracker':'',
                'project-description':'Test Project',
                'project-feed':'',
                'project-homepage':'',
                'project-long_description':'',
                'project-maintainers':'|%s|'%self.user['maintainer'].id,
                'project-maintainers_text':'',
                'project-name':'Test Project',
                'project-slug':'project1',
                'project-tags':'',
                'project-trans_instructions':''}
        resp = self.client['maintainer'].post(self.urls['project_edit'], DATA, follow=True)
        self.assertEqual(resp.status_code, 200)
