from django.core.urlresolvers import reverse
from transifex.txcommon.tests.base import (Project, Language, Team, AuPermission,
    BaseTestCase, USER_ROLES, create_users_and_clients, skip)
from transifex.txcommon.tests.utils import (check_page_status,
    convert_url_roles, assert_status_code)

URL_ROLES = {
    '(301, )':[
        'GET:/projects/p/project1/access/pm/add',
    ],
    '(403, )':[
        'POST:/projects/p/project1/access/pm/1/delete/',
        'POST:/projects/p/project1/access/rq/1/delete/',
        'POST:/projects/p/project1/access/rq/1/approve/',
    ],
    '(200, {}, "This project does not maintain its own translation teams")':[
        'GET:/projects/p/project1/languages/add/',
        'GET:/projects/p/project1/language/pt_BR/',
        'GET:/projects/p/project1/language/pt_BR/members/',
        'GET:/projects/p/project1/language/pt_BR/edit/',
        'GET:/projects/p/project1/language/pt_BR/delete/',
        'POST:/projects/p/project1/language/pt_BR/request/',
        'POST:/projects/p/project1/language/pt_BR/approve/diegobz/',
        'POST:/projects/p/project1/language/pt_BR/deny/diegobz/',
        'POST:/projects/p/project1/language/pt_BR/withdraw/',
        'POST:/projects/p/project1/language/pt_BR/leave/',
        'POST:/projects/p/project1/languages/request/',
        'POST:/projects/p/project1/language/el/approve/',
        'POST:/projects/p/project1/language/el/deny/',
    ],
}

URL_ROLES_FREE = {
    '(301, )':[
        'GET:/projects/p/project1/access/pm/add',
    ],
    '(403, )':[
        'POST:/projects/p/project1/access/pm/1/delete/',
        'POST:/projects/p/project1/access/rq/1/delete/',
        'POST:/projects/p/project1/access/rq/1/approve/',
    ],
    '(200, {}, "Free for all")':[
        'GET:/projects/p/project1/languages/add/',
        'GET:/projects/p/project1/language/pt_BR/',
        'GET:/projects/p/project1/language/pt_BR/members/',
        'GET:/projects/p/project1/language/pt_BR/edit/',
        'GET:/projects/p/project1/language/pt_BR/delete/',
        'POST:/projects/p/project1/language/pt_BR/request/',
        'POST:/projects/p/project1/language/pt_BR/approve/diegobz/',
        'POST:/projects/p/project1/language/pt_BR/deny/diegobz/',
        'POST:/projects/p/project1/language/pt_BR/withdraw/',
        'POST:/projects/p/project1/language/pt_BR/leave/',
        'POST:/projects/p/project1/languages/request/',
        'POST:/projects/p/project1/language/el/approve/',
        'POST:/projects/p/project1/language/el/deny/',
    ],
}

URL_ROLES_OUTSOURCE = {
    '(301, )':[
        'GET:/projects/p/project1/access/pm/add',
    ],
    '(403, )':[
        'POST:/projects/p/project1/access/pm/1/delete/',
        'POST:/projects/p/project1/access/rq/1/delete/',
        'POST:/projects/p/project1/access/rq/1/approve/',
    ],
    '(200, {}, "Outsourcing")':[
        'GET:/projects/p/project1/language/pt_BR/',
        'GET:/projects/p/project1/language/pt_BR/members/',
        'GET:/projects/p/project1/language/pt_BR/edit/',
        'GET:/projects/p/project1/language/pt_BR/delete/',
        'POST:/projects/p/project1/language/pt_BR/request/',
        'POST:/projects/p/project1/language/pt_BR/approve/diegobz/',
        'POST:/projects/p/project1/language/pt_BR/deny/diegobz/',
        'POST:/projects/p/project1/language/pt_BR/withdraw/',
        'POST:/projects/p/project1/language/pt_BR/leave/',
        'POST:/projects/p/project1/language/el/approve/',
        'POST:/projects/p/project1/language/el/deny/',
    ],
    '(200, {}, "Child project")': [
        'GET:/projects/p/project1/languages/add/',
        'POST:/projects/p/project1/languages/request/',
     ]
}

class ProjectAccessControlTestCase(BaseTestCase):
    """
    Test if all project URLs return correct status code depending on each
    user role.
    """
    EXTRA_USER_ROLES = ['outsource_writer', 'outsource_team_member',
        'outsource_maintainer']

    def setUp(self):
        super(ProjectAccessControlTestCase, self).setUp()
        if 'anonymous' in USER_ROLES:
            USER_ROLES.remove('anonymous')
        # Extending users and clients
        extra_users, extra_clients = create_users_and_clients(
                self.EXTRA_USER_ROLES)
        self.user.update(extra_users)
        self.client.update(extra_clients)

        # Create an extra project to use it as the outsource
        self.project_outsource = Project.objects.get_or_create(
            slug="project1_outsource", name="Test Outsource Project",
            source_language=self.language_en
        )[0]
        self.project_outsource.maintainers.add(self.user['outsource_maintainer'])

        # Add django-authority permission for outsource writer
        self.perm_outsource = AuPermission(codename='project_perm.submit_translations',
            approved=True, user=self.user['outsource_writer'],
            content_object=self.project_outsource,
            creator=self.user['maintainer'])
        self.perm_outsource.save()

        # Create a team to the outsource project
        self.team_outsource = Team.objects.get_or_create(
            language=self.language, project=self.project_outsource,
            creator=self.user['maintainer'])[0]
        self.team_outsource.coordinators.add(self.user['team_coordinator'])
        self.team_outsource.members.add(self.user['outsource_team_member'])

    def tearDown(self):
        USER_ROLES.extend(self.EXTRA_USER_ROLES)
        super(ProjectAccessControlTestCase, self).tearDown()
        for u in self.EXTRA_USER_ROLES:
            USER_ROLES.remove(u)
        USER_ROLES.append('anonymous')


    def testAnyoneCanSubmit(self):
        """Check URL access when anyone can submit to a project."""
        self.project.anyone_submit = True
        self.project.save()

        for user_role in USER_ROLES:
            check_page_status(self, user_role, convert_url_roles(URL_ROLES_FREE))

        # Check if a simple registered user can open up Lotte
        expected_code = 200
        url = '/projects/p/project1/resource/resource1/l/pt_BR/'
        for user_role in ['registered']:
            response = self.client[user_role].get(url)
            assert_status_code(self, response, expected_code, url,
                user_role)


    def testOutsourcedAccess(self):
        """Check URL access when a project outsources its access control."""

        self.project.outsource = self.project_outsource
        self.project.save()

        for user_role in USER_ROLES:
            check_page_status(self, user_role, convert_url_roles(URL_ROLES_OUTSOURCE))

        # Check if a writer and a team member of the outsource project can
        # open up Lotte
        expected_code = 200
        url = '/projects/p/project1/resource/resource1/l/pt_BR/'
        for user_role in self.EXTRA_USER_ROLES:
            response = self.client[user_role].get(url)
            assert_status_code(self, response, expected_code, url,
                user_role)

    def testOriginalMaintainer(self):
        """
        Even if a project is outsourced, its maintainer needs to be able to
        edit the source language and add translations as well.
        """

        self.project.outsource = self.project_outsource
        self.project.save()

        maintainer = self.project.maintainers.all()[0]

        # Check if the maintainer can add translations.
        expected_code = 200
        url = reverse('translate_resource', args=[self.project.slug,
            self.resource.slug, self.language.code])
        response = self.client[maintainer.username].get(url)
        assert_status_code(self, response, expected_code, url,
            str(maintainer.username))

        # Check if the maintainer can edit the resource
        expected_code = 200
        url = reverse('resource_edit', args=[self.project.slug,
            self.resource.slug])
        response = self.client[maintainer.username].get(url)
        assert_status_code(self, response, expected_code, url,
            str(maintainer.username))

    def test_project_access_control_edit(self):
        """Test edit of project access control"""
        url = reverse('project_access_control_edit', args=[self.project.slug,])
        resp = self.client['maintainer'].get(url)
        self.assertContains(resp, '<label for="id_access_control_1">'\
                '<input checked="checked" name="access_control" value='\
                '"limited_access"', status_code=200)

        #change access control to outsourced access
        DATA = {'project_type':'outsourced', 'access_control':"free_for_all",
                'next': url, 'outsource': '22'}
        resp = self.client['maintainer'].post(url, DATA, follow=True)
        self.assertContains(resp, '<label for="id_project_type_2"><input'\
                ' checked="checked" name="project_type" value="outsourced"',
                status_code=200)

        #change access control to outsourced with not outsource field filled
        DATA = {'project_type':'outsourced', 'next': url, 'outsource': ''}
        resp = self.client['maintainer'].post(url, DATA, follow=True)
        self.assertContains(resp, 'This field is required', status_code=200)

        #change access control to typical and free for all
        DATA = {'project_type':'typical', 'access_control':"free_for_all", 'next': url, 'outsource': ''}
        resp = self.client['maintainer'].post(url, DATA, follow=True)
        self.assertContains(resp, 'Free for all', status_code=200)

        #change access control to typical with limited access
        DATA = {'project_type':'typical', 'access_control':"limited_access", 'next': url, 'outsource': ''}
        resp = self.client['maintainer'].post(url, DATA, follow=True)
        self.assertNotContains(resp, 'Free for all', status_code=200)

        #change access control to typical with not access_control field filled
        DATA = {'project_type':'typical', 'next': url, 'outsource': ''}
        resp = self.client['maintainer'].post(url, DATA, follow=True)
        self.assertContains(resp, 'This field is required', status_code=200)

    @skip
    def test_project_hub_access_control_edit(self):
        """Test edit of project hub access control"""
        url = reverse('project_access_control_edit', args=[self.project.slug,])

        #change access control as hub and free for all
        DATA = {'project_type':'hub', 'access_control':"free_for_all",
                'next': url, 'outsource': ''}
        resp = self.client['maintainer'].post(url, DATA, follow=True)
        self.assertContains(resp, 'Free for all')
        self.assertContains(resp, 'Hub')

        #change access control as hub with limited access
        DATA = {'project_type':'hub', 'access_control':"limited_access", 'next': url, 'outsource': ''}
        resp = self.client['maintainer'].post(url, DATA, follow=True)
        self.assertNotContains(resp, 'Free for all')
        self.assertContains(resp, 'Hub')

        #change access control as hub with not access_control field filled
        DATA = {'project_type':'hub', 'next': url, 'outsource': ''}
        resp = self.client['maintainer'].post(url, DATA, follow=True)
        self.assertContains(resp, 'This field is required', status_code=200)

    def test_public_project_can_outsource_from_my_private_project(self):
        url = reverse('project_detail',
            kwargs={'project_slug': self.project.slug})

        self.project_private.is_hub = True
        self.project_private.save()

        response = self.client['maintainer'].post(url, {
            'project_type': "outsourced",
            'outsource': self.project_private.id,
            'next': url}
            )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'projects/project_detail.html')
