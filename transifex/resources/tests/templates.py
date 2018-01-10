# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.urlresolvers import reverse
from transifex.languages.models import Language
from transifex.resources.models import SourceEntity
from transifex.teams.models import Team
from transifex.txcommon.tests.base import BaseTestCase

class ResourcesTemplateTests(BaseTestCase):


    def test_create_resource_template_tag(self):
        """Ensure that button and the form is appeared correctly."""
        resp = self.client['maintainer'].get(self.urls['project_resources'])
        self.assertTemplateUsed(resp, 'projects/project_resources.html')
        self.assertContains(resp, "Create Resource")
        for user in ['anonymous', 'registered','team_member']:
            resp = self.client[user].get(self.urls['project'])
            self.assertNotContains(resp, "Create Resource")

    def test_priority_table_snippet(self):
        """ Check that priority td is presented correctly."""
        priority_dict = {
                'Normal': 0,
                'High': 1,
                'Urgent': 2
        }
        resp = self.client['maintainer'].get(self.urls['project_resources'])
        self.assertTemplateUsed(resp, 'projects/project_resources.html')
        self.assertContains(resp,
                            'id="priority_%s"' %
                            (self.resource.slug ,),
                            status_code=200)
        self.assertContains(resp,
                            '<img class="res_tipsy_enable" src="%spriorities/images/%s.png"' %
                            (settings.STATIC_URL,
                             priority_dict.get(self.resource.priority.display_level) ))
        for user in ['anonymous', 'registered','team_member']:
            resp = self.client[user].get(self.urls['project'])
            self.assertNotContains(resp,
                                   'id="priority_%s"' %
                                   (self.resource.slug ,),
                                   status_code=200)

    def test_available_langs_per_resource(self):
        """ Test that the correct number of resource languages appear in template."""
        self.assertEqual(type(self.resource.available_languages.count()), int)
        for user in ['anonymous', 'registered','team_member', 'maintainer']:
            resp = self.client[user].get(self.urls['resource'])
            self.assertContains(
                resp, "Available languages (%s)" % (
                    self.resource.available_languages.count()
                ))

    def test_total_strings_per_resource(self):
        """Test that resource.total_entities return the correct amount of
        strings in the resource_list page."""
        self.resource.update_total_entities()
        self.assertEqual(self.resource.total_entities,
                         SourceEntity.objects.filter(
                             resource=self.resource).count())

    def test_javascript_snippet_cycle_priority(self):
        """Test if we include the ajax triggering js for priority changes."""
        resp = self.client['maintainer'].get(self.urls['project_resources'])
        self.assertTemplateUsed(resp, 'projects/project_resources.html')
        self.assertContains(resp,
                            'var resource_priority_cycle_url = \'%s\';'%
                            (reverse('cycle_resource_priority',
                                     args=[self.project.slug, "1111111111"]),),
                            status_code=200)
        # self.assertContains(resp,
        #                     'title="Click the flags to modify the importance of a resource."')
        # All the other user classes should not see these snippets
        for user in ['anonymous', 'registered','team_member']:
            resp = self.client[user].get(self.urls['project_resources'])
            self.assertNotContains(resp,
                                'var resource_priority_cycle_url = \'%s\';'%
                                (reverse('cycle_resource_priority',
                                         args=[self.project.slug, "1111111111"]),),
                                status_code=200)
            self.assertNotContains(resp,
                                'title="Click the flags to modify the importance of a resource."')

    def test_translate_resource_button(self):
        """Test that translate resource button appears in resource details."""
        # Test the response contents
        for user in ['team_member', 'maintainer']:
            resp = self.client[user].get(self.urls['resource'])
            self.assertTemplateUsed(resp, 'resources/resource_detail.html')
            msg = 'id="start_new_translation" class="i16 buttonized action"'
            self.assertContains(resp, msg, status_code=200)
        # The anonymous users and the non-team members must not see the button
        for user in ['anonymous', 'registered']:
            resp = self.client[user].get(self.urls['resource'])
            self.assertNotContains(resp, msg, status_code=200)

    def test_resource_edit_button(self):
        """Test that resource edit button is rendered correctly in details."""
        # Test the response contents
        resp = self.client['maintainer'].get(self.urls['resource'])
        self.assertTemplateUsed(resp, 'resources/resource_detail.html')
        self.assertContains(resp, 'Edit resource', status_code=200)
        # In any other case of user this should not be rendered
        for user in ['anonymous', 'registered', 'team_member']:
            resp = self.client[user].get(self.urls['resource'])
            self.assertNotContains(resp, 'Edit resource', status_code=200)

    def test_delete_translation_resource_button(self):
        """Test that delete translation resource button is rendered correctly."""
        resp = self.client['maintainer'].get(self.urls['resource_edit'])
        self.assertTemplateUsed(resp, 'resources/resource_form.html')
        self.assertContains(resp, 'Delete resource', status_code=200)
        # In any other case of user this should not be rendered
        for user in ['anonymous', 'registered', 'team_member']:
            resp = self.client[user].get(self.urls['resource_edit'])
            self.assertNotContains(resp, 'Forbidden_access', status_code=403)

    def test_disabled_visit_team_resource_actions(self):
        """Test that resource actions page will work even when there is no
        RLStat object, allowing to start translations for new languages."""
        # We chose Finnish language which has no corresponding project team.
        lang = Language.objects.by_code_or_alias('fi')
        resp = self.client['maintainer'].get(
            reverse('resource_actions', args=[self.resource.project.slug,
                self.resource.slug, lang.code]),
        )
        self.assertTemplateUsed(resp, 'resources/resource_actions.html')
        self.assertEqual(resp.status_code, 200)

    def test_resource_details_team_and_zero_percent(self):
        """Test that languages with teams and 0% are presented."""
        self.project.team_set.filter(language=self.language).delete()
        resp = self.client['anonymous'].get(self.urls['resource'])
        self.assertContains(resp, self.language_ar.name, status_code=200,
            msg_prefix="Do not show 0% languages if there is no respective team.")
        self.assertNotContains(resp, '<div class="stats_string_resource"> 0% </div>')

        # Test with a new team.
        t = Team.objects.create(language=self.language_ar, project=self.project,
                                creator=self.user['maintainer'])
        resp = self.client['anonymous'].get(self.urls['resource'])
        self.assertContains(resp, self.language_ar.name, status_code=200,
            msg_prefix="Show a 0% language if there is a respective team.")
        self.assertContains(resp, '<div class="stats_string_resource">\n'
            '    0%\n  </div>')
