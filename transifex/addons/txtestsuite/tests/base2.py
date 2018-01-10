# -*- coding: utf-8 -*-
import os, sys
from copy import copy
from django.core import management, mail
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils import unittest
from django.db.models.loading import get_model
from django.db import (connections, DEFAULT_DB_ALIAS,
        transaction, IntegrityError, DatabaseError)
from django.test import TestCase, TransactionTestCase
from django.test.testcases import (connections_support_transactions,
        disable_transaction_methods, restore_transaction_methods)
from django.test.client import Client
from django.contrib.auth.models import User, Group, Permission as DjPermission
from django.contrib.contenttypes.models import ContentType
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


if 'test' in sys.argv:
    # monkeypatch get_current() to avoid import errors when tables are not yet created
    from django.contrib.sites.models import Site
    try:
        Site.objects.get_current()
    except DatabaseError:
        def dummy_get_current():
            return Site(domain='localhost', name='transifex')
        Site.objects.get_current = dummy_get_current

    # and patch language_choice_list() for the same reason
    from transifex.languages import models as lang_models
    try:
        lang_models.language_choice_list()
    except DatabaseError:
        def dummy_language_choice_list():
                return [
                    ('af', 'Africaans'), ('ar', 'Arabic'), ('el', 'Greek'),
                    ('fi', 'Finnish'), ('pt_BR', 'Portuguese (Brazil)'),
                    ('en_US', 'English (United States)'), ('hi_IN', 'Hindi (India)')
                ]
        lang_models.language_choice_list = dummy_language_choice_list


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


class TransactionUsers(TestCaseMixin):
    """A class to create users in setUp().

    Use this as a mixin.
    """

    fixtures = ["sample_users", "sample_site", "sample_languages", "sample_data"]

    def setUp(self):
        self.user, self.client = create_users_and_clients(USER_ROLES)
        for nick in USER_ROLES:
            if nick != 'anonymous':
                self.assertTrue(self.user[nick].is_authenticated())

        super(TransactionUsers, self).setUp()

class Users(TestCaseMixin):
    """A class to create users in setUp().

    Use this as a mixin.
    """

    @classmethod
    def setUpClass(cls):
        registered = Group.objects.get(name="registered")
        registered.permissions.add(
            DjPermission.objects.get_or_create(
                codename='add_project', name='Can add project',
                content_type=ContentType.objects.get_for_model(Project))[0])

        cls._user = {}
        cls._client = {}

        # Create users, respective clients and login users
        for nick in USER_ROLES:
            cls._client[nick] = Client()
            if nick != 'anonymous':
                # Create respective users
                if User.objects.filter(username=nick):
                    cls._user[nick] = User.objects.get(username=nick)
                else:
                    cls._user[nick] = User.objects.create_user(
                        nick, '%s@localhost' % nick, PASSWORD)
                cls._user[nick].groups.add(registered)
                # Login non-anonymous personas
                cls._client[nick].login(username=nick, password=PASSWORD)
                #cls._assertTrue(cls._user[nick].is_authenticated())
        cls._client_dict = cls._client
        super(Users, cls).setUpClass()

class TransactionNoticeTypes(TestCaseMixin):
    """A class to create default notice types.

    Use this as a mixin in tests.
    """

    def setUp(self):
        from django.core import management
        management.call_command('txcreatenoticetypes', verbosity=0)
        super(TransactionNoticeTypes, self).setUp()


class NoticeTypes(TestCaseMixin):
    """A class to create default notice types.

    Use this as a mixin in tests.
    """

    @classmethod
    def setUpClass(cls):
        from django.core import management
        management.call_command('txcreatenoticetypes', verbosity=0)
        super(NoticeTypes, cls).setUpClass()

class Languages(TestCaseMixin):
    """A class to create default languages.

    Use this as a mixin in tests.
    """

    @classmethod
    def setUpClass(cls):
        from django.core import management
        management.call_command('txlanguages', verbosity=0)
        cls._language = Language.objects.get(code='pt_BR')
        cls._language_en = Language.objects.get(code='en_US')
        cls._language_ar = Language.objects.get(code='ar')
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

class TransactionProjects(TransactionUsers):
    """A class to create sample projects.

    Use this as a mixin in tests.
    """

    fixtures = ["sample_users", "sample_languages", "sample_data", ]

    def setUp(self):
        super(TransactionProjects, self).setUp()
        self.project = Project.objects.get(slug='project1')
        self.project.maintainers.add(self.user['maintainer'])
        self.project.owner = self.user['maintainer']
        self.project.save()

        self.project_private = Project.objects.get(slug='project2')
        self.project_private.maintainers.add(self.user['maintainer'])
        self.project_private.owner = self.user['maintainer']
        self.project_private.save()



class Projects(Users):
    """A class to create sample projects.

    Use this as a mixin in tests.
    """


    @classmethod
    def setUpClass(cls):
        super(Projects, cls).setUpClass()
        cls._project = Project.objects.get(slug='project1')
        cls._project.maintainers.add(cls._user['maintainer'])
        cls._project.owner = cls._user['maintainer']
        cls._project.save()

        cls._project_private = Project.objects.get(slug='project2')
        cls._project_private.maintainers.add(cls._user['maintainer'])
        cls._project_private.owner = cls._user['maintainer']
        cls._project_private.save()

class TransactionResources(TransactionProjects):
    """A class to create sample resources.

    Use this as a mixin in tests.
    """

    def setUp(self):
        # Create a resource
        super(TransactionResources, self).setUp()
        self.resource = Resource.objects.create(
            slug="resource1", name="Resource1", project=self.project,
            i18n_type='PO'
        )
        self.resource_private = Resource.objects.create(
            slug="resource1", name="Resource1", project=self.project_private,
            i18n_type='PO'
        )



class Resources(Projects):
    """A class to create sample resources.

    Use this as a mixin in tests.
    """

    @classmethod
    def setUpClass(cls):
        # Create a resource
        super(Resources, cls).setUpClass()
        cls._resource = Resource.objects.get_or_create(
            slug="resource1", name="Resource1", project=cls._project,
            i18n_type='PO'
        )[0]
        cls._resource_private = Resource.objects.get_or_create(
            slug="resource1", name="Resource1", project=cls._project_private,
            i18n_type='PO'
        )[0]


class TransactionSourceEntities(TransactionResources):
    """A class to create some sample source entities.

    Use this as a mixin in tests.
    """

    def setUp(self):
        super(TransactionSourceEntities, self).setUp()
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


class SourceEntities(Resources):
    """A class to create some sample source entities.

    Use this as a mixin in tests.
    """

    @classmethod
    def setUpClass(cls):
        super(SourceEntities, cls).setUpClass()
        cls._source_entity = SourceEntity.objects.get_or_create(
            string='String1', context='Context1', occurrences='Occurrences1',
            resource=cls._resource
        )[0]
        cls._source_entity_private = SourceEntity.objects.get_or_create(
            string='String1', context='Context1', occurrences='Occurrences1',
            resource=cls._resource_private
        )[0]
        cls._source_entity_plural = SourceEntity.objects.get_or_create(
            string='pluralized_String1', context='Context1',
            occurrences='Occurrences1_plural', resource= cls._resource,
            pluralized=True
        )[0]
        cls._source_entity_plural_private = SourceEntity.objects.get_or_create(
            string='pluralized_String1', context='Context1',
            occurrences='Occurrences1_plural', resource= cls._resource_private,
            pluralized=True
        )[0]


class TransactionTranslations(TransactionSourceEntities):
    """A class to create some sample translations.

    Use this as a mixin in tests.
    """

    def setUp(self):
        # Create one translation
        super(TransactionTranslations, self).setUp()
        self.translation_en = self.source_entity.translations.create(
            string='Buy me some BEER :)',
            rule=5,
            source_entity=self.source_entity,
            resource=self.resource,
            language=self.language_en,
            user=self.user['registered'],
        )
        self.translation_ar = self.source_entity.translations.create(
            string=u'This is supposed to be arabic text! αβγ',
            rule=5,
            source_entity=self.source_entity,
            resource=self.resource,
            language=self.language_ar,
            user=self.user['registered'],
        )


class Translations(SourceEntities):
    """A class to create some sample translations.

    Use this as a mixin in tests.
    """

    @classmethod
    def setUpClass(cls):
        # Create one translation
        super(Translations, cls).setUpClass()
        cls._translation_en = cls._source_entity.translations.get_or_create(
            string='Buy me some BEER :)',
            rule=5,
            source_entity=cls._source_entity,
            language=cls._language_en,
            user=cls._user['registered'],
            resource=cls._resource
        )[0]
        cls._translation_ar = cls._source_entity.translations.get_or_create(
            string=u'This is supposed to be arabic text! αβγ',
            rule=5,
            source_entity=cls._source_entity,
            language=cls._language_ar,
            user=cls._user['registered'],
            resource=cls._resource
        )[0]

class SampleData(TransactionLanguages, TransactionTranslations,
        TransactionNoticeTypes):
    """A class that has all sample data defined."""

class TransactionBaseTestCase(SampleData, TransactionTestCase,):
    fixtures = ["sample_users", "sample_site", "sample_languages", "sample_data"]

    def __init__(self, *args, **kwargs):
        super(TransactionBaseTestCase, self).__init__(*args, **kwargs)

        # Useful for writing tests: Enter ipython anywhere w/ ``self.ipython()``
        try:
            from IPython.terminal.embed import InteractiveShellEmbed as shell
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
        self.team.reviewers.add(self.user['reviewer'])
        self.team_private.coordinators.add(self.user['team_coordinator'])
        self.team_private.members.add(self.user['team_member'])
        self.team_private.reviewers.add(self.user['reviewer'])

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

    def __init__(self, *args, **kwargs):
        super(BaseTestCase, self).__init__(*args, **kwargs)

        # Useful for writing tests: Enter ipython anywhere w/ ``self.ipython()``
        try:
            from IPython.terminal.embed import InteractiveShellEmbed as shell
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

    @classmethod
    def setUpClass(cls):
        """Set up a sample set of class wide base objects for inherited tests.
        NOTE: Use this Test Suite with
          TEST_RUNNER = 'txtestrunner.runner.TxTestSuiteRunner'
        in settings.
        If you are inheriting the class and overriding setUpClass, don't forget to
        call super::

          from transifex.txcommon.tests import (base2, utils)
          class TestClassName(base2.BaseTestCase):
              @classmethod
              def setUpClass(self):
                  super(TestClassName, self).setUpClass()

        """
        super(BaseTestCase, cls).setUpClass()

        # Add django-authority permission for writer
        cls._permission = AuPermission.objects.create(
            codename='project_perm.submit_translations',
            approved=True, user=cls._user['writer'],
            content_object=cls._project, creator=cls._user['maintainer'])

        # Create teams
        cls._team = Team.objects.get_or_create(language=cls._language,
            project=cls._project, creator=cls._user['maintainer'])[0]
        cls._team_private = Team.objects.get_or_create(language=cls._language,
            project=cls._project_private, creator=cls._user['maintainer'])[0]
        cls._team.coordinators.add(cls._user['team_coordinator'])
        cls._team.members.add(cls._user['team_member'])
        cls._team.members.add(cls._user['reviewer'])
        cls._team_private.coordinators.add(cls._user['team_coordinator'])
        cls._team_private.members.add(cls._user['team_member'])
        cls._team_private.members.add(cls._user['reviewer'])

        # Create a release
        cls._release = Release.objects.get_or_create(slug="releaseslug1",
            name="Release1", project=cls._project)[0]
        cls._release.resources.add(cls._resource)
        cls._release_private = Release.objects.get_or_create(slug="releaseslug2",
            name="Release2", project=cls._project_private)[0]
        cls._release_private.resources.add(cls._resource_private)


        # Create common URLs
        # Easier to call common URLs in your view/template unit tests.
        cls._urls = {
            'project': reverse('project_detail', args=[cls._project.slug]),
            'project_edit': reverse('project_edit', args=[cls._project.slug]),
            'project_resources': reverse('project_resources', args=[cls._project.slug]),
            'resource': reverse('resource_detail', args=[cls._resource.project.slug, cls._resource.slug]),
            'resource_actions': reverse('resource_actions', args=[cls._resource.project.slug, cls._resource.slug, cls._language.code]),
            'resource_edit': reverse('resource_edit', args=[cls._resource.project.slug, cls._resource.slug]),
            'translate': reverse('translate_resource', args=[cls._resource.project.slug, cls._resource.slug, cls._language.code]),
            'release': reverse('release_detail', args=[cls._release.project.slug, cls._release.slug]),
            'release_create': reverse('release_create', args=[cls._project.slug]),
            'team': reverse('team_detail', args=[cls._resource.project.slug,
                                                 cls._language.code]),

            'project_private': reverse('project_detail', args=[cls._project_private.slug]),
            'resource_private': reverse('resource_detail', args=[cls._resource_private.project.slug, cls._resource_private.slug]),
            'translate_private': reverse('translate_resource', args=[cls._resource_private.project.slug, cls._resource_private.slug, cls._language.code]),
        }


        from django.core import management
        management.call_command('txstatsupdate', verbosity=0)

    def _pre_setup(self):
        if not connections_support_transactions():
            fixtures = ["sample_users", "sample_site", "sample_languages", "sample_data"]
            if getattr(self, 'multi_db', False):
                databases = connections
            else:
                databases = [DEFAULT_DB_ALIAS]
            for db in databases:
                management.call_command('flush', verbosity=0,
                interactive=False, database=db)
                management.call_command('loaddata', *fixtures, **{
                    'verbosity': 0, 'database': db})

        else:
            if getattr(self, 'multi_db', False):
                databases = connections
            else:
                databases = [DEFAULT_DB_ALIAS]

            for db in databases:
                transaction.enter_transaction_management(using=db)
                transaction.managed(True, using=db)
            disable_transaction_methods()
        mail.outbox = []

    def _post_teardown(self):
        if connections_support_transactions():
            # If the test case has a multi_db=True flag, teardown all databases.
            # Otherwise, just teardown default.
            if getattr(self, 'multi_db', False):
                databases = connections
            else:
                databases = [DEFAULT_DB_ALIAS]

            restore_transaction_methods()
            for db in databases:
                transaction.rollback(using=db)
                transaction.leave_transaction_management(using=db)
        for connection in connections.all():
            connection.close()

    def setUp(self):
        super(BaseTestCase, self).setUp()
        self.client = copy(self._client_dict)
        self.user = copy(self._user)
        self.language = copy(self._language)
        self.language_en = copy(self._language_en)
        self.language_ar = copy(self._language_ar)
        self.project = copy(self._project)
        self.project_private = copy(self._project_private)
        self.resource = copy(self._resource)
        self.resource_private = copy(self._resource_private)
        self.source_entity = copy(self._source_entity)
        self.source_entity_private = copy(self._source_entity_private)
        self.source_entity_plural = copy(self._source_entity_plural)
        self.source_entity_plural_private = copy(self._source_entity_plural_private)
        self.translation_en = copy(self._translation_en)
        self.translation_ar = copy(self._translation_ar)
        self.permission = copy(self._permission)
        self.team = copy(self._team)
        self.team_private = copy(self._team_private)
        self.release = copy(self._release)
        self.release_private = copy(self._release_private)
        self.urls = copy(self._urls)


    def tearDown(self):
        pass

    @classmethod
    def tearDownClass(cls):
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


class BaseTestCase2Tests(BaseTestCase):
    """Test the base test case itself."""

    @skip
    def test_basetest_users(self):
        """Test that basic users can function normally."""
        for role in USER_ROLES:
            print role
            # All users should be able to see the homepage
            resp = self.client[role].get('/')
            self.assertEquals(resp.status_code, 200)

