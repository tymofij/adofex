# -*- coding: utf-8 -*-
import os
from django.core import management
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils import unittest
from django.db.models.loading import get_model
from django.test import TestCase, TransactionTestCase
from django.test.client import Client
from django.contrib.auth.models import User, Group, Permission as DjPermission
from django.contrib.contenttypes.models import ContentType
from django.utils import unittest
from django_addons.autodiscover import autodiscover_notifications
from transifex.txcommon.notifications import NOTICE_TYPES
from transifex.txcommon.log import logger

# Load models
Language = get_model('languages', 'Language')
AuPermission = get_model('authority', 'Permission')
Project = get_model('projects', 'Project')
Resource = get_model('resources', 'Resource')
Release = get_model('releases', 'Release')
Team = get_model('teams', 'Team')
SourceEntity = get_model('resources', 'SourceEntity')

def skip(func):
    func_name = func.__name__
    def decorator(func):
        msg = "%s skipped. Please implement it in your project path."%func_name
        if settings.TX_ROOT != settings.PROJECT_PATH:
            logger.debug(msg)
        return unittest.skipUnless(settings.TX_ROOT == settings.PROJECT_PATH, msg)
    return decorator

# Please refer to the README file in the tests directory for more info about
# the various user roles.
USER_ROLES = [
    'anonymous',
    'registered',
    'maintainer',
    'writer',
    'team_coordinator',
    'team_member',
    'reviewer']
PASSWORD = '123412341234'


def deactivate_caching_middleware():
    list_middle_c = list(settings.MIDDLEWARE_CLASSES)
    try:
        list_middle_c.remove('django.middleware.cache.FetchFromCacheMiddleware')
    except ValueError:
        pass
    try:
        list_middle_c.remove('django.middleware.cache.UpdateCacheMiddleware')
    except ValueError:
        pass


def deactivate_csrf_middleware():
    list_middle_c = list(settings.MIDDLEWARE_CLASSES)
    try:
        list_middle_c.remove('external.csrf.middleware.CsrfMiddleware')
    except ValueError:
        pass
    settings.MIDDLEWARE_CLASSES = list_middle_c


class TestCaseMixin(object):

    @staticmethod
    def response_in_browser(resp, halt=True):
        """
        Useful for debugging it shows the content of a http response in the
        browser when called.
        """
        from transifex.txcommon.tests.utils import response_in_browser
        return response_in_browser(resp, halt=True)

def create_users_and_clients(USER_ROLES):
    registered = Group.objects.get(name="registered")
    registered.permissions.add(
        DjPermission.objects.get_or_create(
            codename='add_project', name='Can add project',
            content_type=ContentType.objects.get_for_model(Project))[0])

    user = {}
    client = {}

    # Create users, respective clients and login users
    for nick in USER_ROLES:
        client[nick] = Client()
        if nick != 'anonymous':
            # Create respective users
            if User.objects.filter(username=nick):
                user[nick] = User.objects.get(username=nick)
            else:
                user[nick] = User.objects.create_user(
                    nick, '%s@localhost' % nick, PASSWORD)
            user[nick].groups.add(registered)
            # Login non-anonymous personas
            client[nick].login(username=nick, password=PASSWORD)

    return user, client


class Users(TestCaseMixin):
    """A class to create users in setUp().

    Use this as a mixin.
    """

    fixtures = ["sample_users", "sample_site", "sample_languages", "sample_data"]

    def setUp(self):
        self.user, self.client = create_users_and_clients(USER_ROLES)
        for nick in USER_ROLES:
            if nick != 'anonymous':
                self.assertTrue(self.user[nick].is_authenticated())
        super(Users, self).setUp()

TransactionUsers = Users

class NoticeTypes(TestCaseMixin):
    """A class to create default notice types.

    Use this as a mixin in tests.
    """

    @classmethod
    def setUpClass(cls):
        from django.core import management
        management.call_command('txcreatenoticetypes', verbosity=0)
        super(NoticeTypes, cls).setUpClass()


class TransactionNoticeTypes(TestCaseMixin):
    """A class to create default notice types.

    Use this as a mixin in tests.
    """

    def setUp(self):
        from django.core import management
        management.call_command('txcreatenoticetypes', verbosity=0)
        super(TransactionNoticeTypes, self).setUp()


class Languages(TestCaseMixin):
    """A class to create default languages.

    Use this as a mixin in tests.
    """

    @classmethod
    def setUpClass(cls):
        from django.core import management
        management.call_command('txlanguages', verbosity=0)
        cls.language = Language.objects.get(code='pt_BR')
        cls.language_en = Language.objects.get(code='en_US')
        cls.language_ar = Language.objects.get(code='ar')
        #self.language_hi_IN = Language.objects.get(code='hi_IN')
        super(Languages, cls).setUpClass()


class TransactionLanguages(TestCaseMixin):
    """A class to create default languages.

    Use this as a mixin in transaction-based tests.
    """

    def setUp(self):
        from django.core import management
        management.call_command('txlanguages', verbosity=0)
        self.language = Language.objects.get(code='pt_BR')
        self.language_en = Language.objects.get(code='en_US')
        self.language_ar = Language.objects.get(code='ar')
        super(TransactionLanguages, self).setUp()


class Projects(Users):
    """A class to create sample projects.

    Use this as a mixin in tests.
    """

    fixtures = ["sample_users", "sample_languages", "sample_data", ]

    def setUp(self):
        super(Projects, self).setUp()
        self.project = Project.objects.get(slug='project1')
        self.project.maintainers.add(self.user['maintainer'])
        self.project.owner = self.user['maintainer']
        self.project.save()

        self.project_private = Project.objects.get(slug='project2')
        self.project_private.maintainers.add(self.user['maintainer'])
        self.project_private.owner = self.user['maintainer']
        self.project_private.save()

TransactionProjects = Projects

class Resources(Projects):
    """A class to create sample resources.

    Use this as a mixin in tests.
    """

    def setUp(self):
        # Create a resource
        super(Resources, self).setUp()
        self.resource = Resource.objects.create(
            slug="resource1", name="Resource1", project=self.project,
            i18n_type='PO'
        )
        self.resource_private = Resource.objects.create(
            slug="resource1", name="Resource1", project=self.project_private,
            i18n_type='PO'
        )

TransactionResources = Resources

class SourceEntities(Resources):
    """A class to create some sample source entities.

    Use this as a mixin in tests.
    """

    def setUp(self):
        super(SourceEntities, self).setUp()
        self.source_entity = SourceEntity.objects.create(
            string='String1', context='Context1', occurrences='Occurrences1',
            resource=self.resource
        )
        self.source_entity_private = SourceEntity.objects.create(
            string='String1', context='Context1', occurrences='Occurrences1',
            resource=self.resource_private
        )
        self.source_entity_plural = SourceEntity.objects.create(
            string='pluralized_String1', context='Context1',
            occurrences='Occurrences1_plural', resource= self.resource,
            pluralized=True
        )
        self.source_entity_plural_private = SourceEntity.objects.create(
            string='pluralized_String1', context='Context1',
            occurrences='Occurrences1_plural', resource= self.resource_private,
            pluralized=True
        )

TransactionSourceEntities = SourceEntities

class Translations(SourceEntities):
    """A class to create some sample translations.

    Use this as a mixin in tests.
    """

    def setUp(self):
        # Create one translation
        super(Translations, self).setUp()
        self.translation_en = self.source_entity.translations.create(
            string='Buy me some BEER :)',
            rule=5,
            source_entity=self.source_entity,
            language=self.language_en,
            user=self.user['registered'],
            resource=self.resource
        )
        self.translation_ar = self.source_entity.translations.create(
            string=u'This is supposed to be arabic text! αβγ',
            rule=5,
            source_entity=self.source_entity,
            language=self.language_ar,
            user=self.user['registered'],
            resource=self.resource
        )

TransactionTranslations = Translations

class SampleData(TransactionLanguages, TransactionTranslations,
        TransactionNoticeTypes):
    """A class that has all sample data defined."""

class TransactionBaseTestCase(SampleData, TransactionTestCase,):
    fixtures = ["sample_users", "sample_site", "sample_languages", "sample_data"]

    def __init__(self, *args, **kwargs):
        super(TransactionBaseTestCase, self).__init__(*args, **kwargs)

        # Useful for writing tests: Enter ipython anywhere w/ ``self.ipython()``
        try:
            from IPython.frontend.terminal.embed import InteractiveShellEmbed as shell
            self.ipython = shell()
        except ImportError:
            pass

        #FIXME: This should not happen, since it diverges away the test suite
        # from the actual deployment.
        # Remove the caching middlewares because they interfere with the
        # anonymous client.
        deactivate_caching_middleware()
        deactivate_csrf_middleware()
        # Disable actionlog, which in turn disables noticetype requirement.
        settings.ACTIONLOG_ENABLED = False

    def setUp(self):
        """Set up a sample set of base objects for inherited tests.

        If you are inheriting the class and overriding setUp, don't forget to
        call super::

          from transifex.txcommon.tests import (base, utils)
          class TestClassName(base.BaseTestCase)
              def setUp(self):
                  super(TestClassName, self).setUp()

        """
        super(TransactionBaseTestCase, self).setUp()

        # Add django-authority permission for writer
        self.permission = AuPermission.objects.create(
            codename='project_perm.submit_translations',
            approved=True, user=self.user['writer'],
            content_object=self.project, creator=self.user['maintainer'])

        # Create teams
        self.team = Team.objects.get_or_create(language=self.language,
            project=self.project, creator=self.user['maintainer'])[0]
        self.team_private = Team.objects.get_or_create(language=self.language,
            project=self.project_private, creator=self.user['maintainer'])[0]
        self.team.coordinators.add(self.user['team_coordinator'])
        self.team.members.add(self.user['team_member'])
        self.team.members.add(self.user['reviewer'])
        self.team_private.coordinators.add(self.user['team_coordinator'])
        self.team_private.members.add(self.user['team_member'])
        self.team_private.members.add(self.user['reviewer'])

        # Create a release
        self.release = Release.objects.create(slug="releaseslug1",
            name="Release1", project=self.project)
        self.release.resources.add(self.resource)
        self.release_private = Release.objects.create(slug="releaseslug2",
            name="Release2", project=self.project_private)
        self.release_private.resources.add(self.resource_private)


        # Create common URLs
        # Easier to call common URLs in your view/template unit tests.
        self.urls = {
            'project': reverse('project_detail', args=[self.project.slug]),
            'project_edit': reverse('project_edit', args=[self.project.slug]),
            'project_resources': reverse('project_resources', args=[self.project.slug]),
            'resource': reverse('resource_detail', args=[self.resource.project.slug, self.resource.slug]),
            'resource_actions': reverse('resource_actions', args=[self.resource.project.slug, self.resource.slug, self.language.code]),
            'resource_edit': reverse('resource_edit', args=[self.resource.project.slug, self.resource.slug]),
            'translate': reverse('translate_resource', args=[self.resource.project.slug, self.resource.slug, self.language.code]),
            'release': reverse('release_detail', args=[self.release.project.slug, self.release.slug]),
            'release_create': reverse('release_create', args=[self.project.slug]),
            'team': reverse('team_detail', args=[self.resource.project.slug,
                                                 self.language.code]),

            'project_private': reverse('project_detail', args=[self.project_private.slug]),
            'resource_private': reverse('resource_detail', args=[self.resource_private.project.slug, self.resource_private.slug]),
            'translate_private': reverse('translate_resource', args=[self.resource_private.project.slug, self.resource_private.slug, self.language.code]),
        }

        from django.core import management
        management.call_command('txstatsupdate', verbosity=0)


class BaseTestCase(Languages, NoticeTypes, Translations, TestCase):
    """Provide a solid test case for all tests to inherit from."""

    fixtures = ["sample_users", "sample_site", "sample_languages", "sample_data"]

    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)

        # Useful for writing tests: Enter ipython anywhere w/ ``self.ipython()``
        try:
            from IPython.frontend.terminal.embed import InteractiveShellEmbed as shell
            self.ipython = shell()
        except ImportError:
            pass

        #FIXME: This should not happen, since it diverges away the test suite
        # from the actual deployment.
        # Remove the caching middlewares because they interfere with the
        # anonymous client.
        deactivate_caching_middleware()
        deactivate_csrf_middleware()
        # Disable actionlog, which in turn disables noticetype requirement.
        settings.ACTIONLOG_ENABLED = False

    def setUp(self):
        """Set up a sample set of base objects for inherited tests.

        If you are inheriting the class and overriding setUp, don't forget to
        call super::

          from transifex.txcommon.tests import (base, utils)
          class TestClassName(base.BaseTestCase)
              def setUp(self):
                  super(TestClassName, self).setUp()

        """
        super(BaseTestCase, self).setUp()

        # Add django-authority permission for writer
        self.permission = AuPermission.objects.create(
            codename='project_perm.submit_translations',
            approved=True, user=self.user['writer'],
            content_object=self.project, creator=self.user['maintainer'])

        # Create teams
        self.team = Team.objects.get_or_create(language=self.language,
            project=self.project, creator=self.user['maintainer'])[0]
        self.team_private = Team.objects.get_or_create(language=self.language,
            project=self.project_private, creator=self.user['maintainer'])[0]
        self.team.coordinators.add(self.user['team_coordinator'])
        self.team.members.add(self.user['team_member'])
        self.team.members.add(self.user['reviewer'])
        self.team_private.coordinators.add(self.user['team_coordinator'])
        self.team_private.members.add(self.user['team_member'])
        self.team_private.members.add(self.user['reviewer'])

        # Create a release
        self.release = Release.objects.create(slug="releaseslug1",
            name="Release1", project=self.project)
        self.release.resources.add(self.resource)
        self.release_private = Release.objects.create(slug="releaseslug2",
            name="Release2", project=self.project_private)
        self.release_private.resources.add(self.resource_private)


        # Create common URLs
        # Easier to call common URLs in your view/template unit tests.
        self.urls = {
            'project': reverse('project_detail', args=[self.project.slug]),
            'project_edit': reverse('project_edit', args=[self.project.slug]),
            'project_resources': reverse('project_resources', args=[self.project.slug]),
            'resource': reverse('resource_detail', args=[self.resource.project.slug, self.resource.slug]),
            'resource_actions': reverse('resource_actions', args=[self.resource.project.slug, self.resource.slug, self.language.code]),
            'resource_edit': reverse('resource_edit', args=[self.resource.project.slug, self.resource.slug]),
            'translate': reverse('translate_resource', args=[self.resource.project.slug, self.resource.slug, self.language.code]),
            'release': reverse('release_detail', args=[self.release.project.slug, self.release.slug]),
            'release_create': reverse('release_create', args=[self.project.slug]),
            'team': reverse('team_detail', args=[self.resource.project.slug,
                                                 self.language.code]),

            'project_private': reverse('project_detail', args=[self.project_private.slug]),
            'resource_private': reverse('resource_detail', args=[self.resource_private.project.slug, self.resource_private.slug]),
            'translate_private': reverse('translate_resource', args=[self.resource_private.project.slug, self.resource_private.slug, self.language.code]),
        }

        from django.core import management
        management.call_command('txstatsupdate', verbosity=0)

    def tearDown(self):
        pass

    def create_more_entities(self, total=1):
        """A method to create more entities for those tests that require them."""
        self.source_entity2 = SourceEntity.objects.create(string='String2',
            context='Context1', occurrences='Occurrences1', resource=self.resource)
        self.translation_en2 = self.source_entity2.translations.create(
            string='Translation String 2',
            rule=5,
            source_entity=self.source_entity,
            resource=self.resource,
            language=self.language_en,
            user=self.user['registered'])
        self.resource.update_total_entities()
        self.resource.update_wordcount()

    # Custom assertions
    def assertNoticeTypeExistence(self, noticetype_label):
        """Assert that a specific noticetype was created."""
        found = False
        for n in NOTICE_TYPES:
             if n["label"] == noticetype_label:
                 found = True
        self.assertTrue(found, msg = "Notice type '%s' wasn't "
            "added" % noticetype_label)

    #FIXME: Port all status checks to this method.
    def assert_url_statuses(self, pages_dict, client):
        """Test whether a list of URLs return the correct status codes.

        'pages_dict':
          A dictionary of status codes, each one listing a
          set of pages to test whether they return that status code.
        'client': A django.test.client.Client object.

        >>> pages = {200: ['/', '/projects/',],
                     404: ['/foobar'],}
        >>> self.assert_url_statuses(pages, self.client["anonymous"])

        """

        for expected_code, pages in pages_dict.items():
            for page_url in pages:
                page = client.get(page_url)
                self.assertEquals(page.status_code, expected_code,
                    "Status code for page '%s' was %s instead of %s" %
                    (page_url, page.status_code, expected_code))


class BaseTestCaseTests(BaseTestCase):
    """Test the base test case itself."""

    @unittest.skipIf(settings.TX_ROOT != settings.PROJECT_PATH, 'Unsupported redirect')
    def test_basetest_users(self):
        """Test that basic users can function normally."""
        for role in USER_ROLES:
            # All users should be able to see the homepage
            resp = self.client[role].get('/')
            self.assertEquals(resp.status_code, 200)

