# -*- coding: utf-8 -*-
import os
from mock import Mock
from piston.utils import rc
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.test import TransactionTestCase, TestCase
from django.conf import settings
from django.utils import unittest
from django.contrib.auth.models import User, Permission
from transifex.txcommon.tests.base import Users, TransactionNoticeTypes,\
                            TransactionUsers, TransactionBaseTestCase,\
                            BaseTestCase
from transifex.txcommon.utils import log_skip_transaction_test
from transifex.resources.models import Resource, RLStats, SourceEntity
from transifex.resources.api import (ResourceHandler,
        TranslationObjectsHandler, NoContentError, BadRequestError,
        ForbiddenError, NotFoundError)
from transifex.resources.formats.registry import registry
from transifex.resources.formats.utils.hash_tag import hash_tag
from transifex.resources.tests.api.base import APIBaseTests
from transifex.projects.models import Project
from transifex.languages.models import Language
from transifex.settings import PROJECT_PATH


class TestResourceAPI(APIBaseTests):

    def setUp(self):
        super(TestResourceAPI, self).setUp()
        self.po_file = os.path.join(self.pofile_path, "pt_BR.po")
        self.url_resources = reverse(
            'apiv2_resources', kwargs={'project_slug': 'project1'}
        )
        self.url_resources_private = reverse(
            'apiv2_resources', kwargs={'project_slug': 'project2'}
        )
        self.url_resource = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'project1', 'resource_slug': 'resource1'}
        )
        self.url_resource_private = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'project2', 'resource_slug': 'resource1'}
        )
        self.url_new_project = reverse(
            'apiv2_projects'
        )
        self.url_create_resource = reverse(
            'apiv2_resources', kwargs={'project_slug': 'new_pr'}
        )
        self.url_new_resource = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'new_pr', 'resource_slug': 'r1', }
        )
        self.url_new_translation = reverse(
            'apiv2_translation',
            kwargs={
                'project_slug': 'new_pr',
                'resource_slug': 'new_r',
                'lang_code': 'el'
            }
        )

    def test_get(self):
        res = self.client['anonymous'].get(self.url_resources)
        self.assertEquals(res.status_code, 401)
        res = self.client['registered'].get(
            reverse(
                'apiv2_resource',
                kwargs={'project_slug': 'not_exists', 'resource_slug': 'resource1'}
            )
        )
        self.assertEquals(res.status_code, 404)
        res = self.client['registered'].get(self.url_resources)
        self.assertEquals(res.status_code, 200)
        self.assertFalse('created' in simplejson.loads(res.content)[0])
        res = self.client['registered'].get(self.url_resources)
        self.assertEquals(res.status_code, 200)
        self.assertEquals(len(simplejson.loads(res.content)), 1)
        self.assertFalse('created' in simplejson.loads(res.content)[0])
        res = self.client['registered'].get(self.url_resources_private)
        self.assertEquals(res.status_code, 401)
        res = self.client['maintainer'].get(self.url_resources_private + "?details")
        self.assertEquals(res.status_code, 501)
        res = self.client['maintainer'].get(self.url_resources_private)
        self.assertEquals(res.status_code, 200)
        self.assertEqual(len(simplejson.loads(res.content)), 1)
        self.assertFalse('created' in simplejson.loads(res.content)[0])
        self.assertTrue('slug' in simplejson.loads(res.content)[0])
        self.assertTrue('name' in simplejson.loads(res.content)[0])
        res = self.client['anonymous'].get(self.url_resource)
        self.assertEquals(res.status_code, 401)
        url_not_exists = self.url_resource[:-1] + "none/"
        res = self.client['registered'].get(url_not_exists)
        self.assertEquals(res.status_code, 404)
        res = self.client['registered'].get(self.url_resource_private)
        self.assertEquals(res.status_code, 401)
        res = self.client['maintainer'].get(self.url_resource_private)
        self.assertEquals(res.status_code, 200)
        res = self.client['maintainer'].get(self.url_resource_private)
        self.assertEquals(res.status_code, 200)
        data = simplejson.loads(res.content)
        self.assertEquals(len(data), 5)
        self.assertTrue('slug' in  data)
        self.assertTrue('name' in data)
        self.assertTrue('source_language', data)
        res = self.client['maintainer'].get(self.url_resource_private + "?details")
        self.assertEquals(res.status_code, 200)
        data = simplejson.loads(res.content)
        self.assertTrue('source_language_code' in data)
        self._create_resource()
        res = self.client['registered'].get(self.url_new_resource)
        self.assertEquals(res.status_code, 200)
        data = simplejson.loads(res.content)
        self.assertTrue('source_language_code' in data)
        res = self.client['registered'].get(
            self.url_new_resource + "content/"
        )
        self.assertEquals(res.status_code, 200)
        data = simplejson.loads(res.content)
        self.assertTrue('content' in data)
        res = self.client['registered'].get(
            self.url_new_resource + "content/?file"
        )
        self.assertEquals(res.status_code, 200)


    def test_post_errors(self):
        res = self.client['anonymous'].post(
            self.url_resource, content_type='application/json'
        )
        self.assertEquals(res.status_code, 401)
        res = self.client['registered'].post(
            self.url_resource, content_type='application/json'
        )
        self.assertEquals(res.status_code, 403)
        self._create_resource()
        url = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'new_pr', 'resource_slug': 'new_r'}
        )
        res = self.client['registered'].post(
            url, content_type='application/json'
        )
        self.assertContains(res, "POSTing to this url is not allowed", status_code=400)
        res = self.client['registered'].post(
            self.url_create_resource,
            data=simplejson.dumps({
                    'name': "resource1",
                    'slug': 'r1',
                    'foo': 'foo'
            }),
            content_type='application/json'
        )
        self.assertContains(res, "Field 'foo'", status_code=400)
        res = self.client['registered'].post(
            self.url_create_resource,
            data=simplejson.dumps({
                    'name': "resource1",
                    'name': "resource2",
                    'slug': 'r2',
            }),
            content_type='application/json'
        )
        self.assertContains(res, "Field 'i18n_type'", status_code=400)

        f = open(self.po_file)
        res = self.client['registered'].post(
            self.url_create_resource,
            data={
                    'name': "resource1",
                    'name': "resource2",
                    'slug': 'r.2+',
                    'i18n_type': 'PO',
                    'attachment': f,
            },
        )
        f.close()
        self.assertContains(res, "Invalid arguments given", status_code=400)


    def test_post_files(self):
        self._create_project()
        # send files
        f = open(self.po_file)
        res = self.client['registered'].post(
            self.url_create_resource,
            data={
                'name': "resource1",
                'slug': 'r1',
                'i18n_type': 'PO',
                'name': 'name.po',
                'attachment': f
            },
        )
        f.close()
        r = Resource.objects.get(slug='r1', project__slug='new_pr')
        self.assertEquals(len(r.available_languages_without_teams), 1)

    def test_put(self):
        self._create_resource()
        res = self.client['anonymous'].put(
            self.url_create_resource,
            data=simplejson.dumps({}),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 401)
        res = self.client['registered'].put(
            self.url_create_resource,
            data=simplejson.dumps({}),
            content_type='application/json'
        )
        self.assertContains(res, "No resource", status_code=400)
        url = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'new_pr_not', 'resource_slug': 'r1'}
        )
        res = self.client['registered'].put(
            url, data=simplejson.dumps({}),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 404)
        url = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'new_pr', 'resource_slug': 'r1'}
        )
        res = self.client['registered'].put(
            url, data=simplejson.dumps({}),
            content_type='application/json'
        )
        self.assertContains(res, "Empty request", status_code=400)
        url = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'new_pr', 'resource_slug': 'r1'}
        )
        res = self.client['registered'].put(
            url,
            data=simplejson.dumps({
                    'i18n_type': "PO",
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 400)
        res = self.client['registered'].put(
            url,
            data=simplejson.dumps({
                    'foo': 'foo',
            }),
            content_type='application/json'
        )
        self.assertContains(res,"Field 'foo'", status_code=400)

    def test_delete(self):
        res = self.client['anonymous'].delete(self.url_resource)
        self.assertEquals(res.status_code, 401)
        res = self.client['registered'].delete(self.url_resource)
        self.assertEquals(res.status_code, 403)
        self._create_resource()
        url = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'new_pr', 'resource_slug': 'r1'}
        )
        res = self.client['registered'].delete(url)
        self.assertEquals(res.status_code, 204)

    def _create_project(self):
        res = self.client['registered'].post(
            self.url_new_project,
            data=simplejson.dumps({
                    'slug': 'new_pr', 'name': 'Project from API',
                    'source_language_code': 'el',
                    'maintainers': 'registered',
                    'description': 'desc',
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 201)

    def _create_resource(self):
        self._create_project()
        with open(self.po_file) as f:
            content = f.read()
        res = self.client['registered'].post(
            self.url_create_resource,
            data=simplejson.dumps({
                    'name': "resource1",
                    'slug': 'r1',
                    'i18n_type': 'PO',
                    'content': content,
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 201)
        r = Resource.objects.get(slug='r1', project__slug='new_pr')
        self.assertEquals(len(r.available_languages_without_teams), 1)


@unittest.skipUnless(settings.DATABASES['default']['ENGINE'].endswith(
        'postgresql_psycopg2'), log_skip_transaction_test(
            "Skipping transaction test because database backend"
            " is not postgres."))
class TestTransactionResourceCreate(TransactionUsers, TransactionNoticeTypes,
                                    TransactionTestCase):

    def setUp(self):
        super(TestTransactionResourceCreate, self).setUp()
        self.pofile_path = os.path.join(
            settings.TX_ROOT, 'resources/tests/lib/pofile'
        )
        self.po_file = os.path.join(self.pofile_path, "pt_BR.po")
        self.url_resources = reverse(
            'apiv2_resources', kwargs={'project_slug': 'project1'}
        )
        self.url_resources_private = reverse(
            'apiv2_resources', kwargs={'project_slug': 'project2'}
        )
        self.url_resource = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'project1', 'resource_slug': 'resource1'}
        )
        self.url_resource_private = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'project2', 'resource_slug': 'resource1'}
        )
        self.url_new_project = reverse(
            'apiv2_projects'
        )
        self.url_create_resource = reverse(
            'apiv2_resources', kwargs={'project_slug': 'new_pr'}
        )
        self.url_new_resource = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'new_pr', 'resource_slug': 'r1', }
        )
        self.url_new_translation = reverse(
            'apiv2_translation',
            kwargs={
                'project_slug': 'new_pr',
                'resource_slug': 'new_r',
                'lang_code': 'el'
            }
        )

    def test_long_slug(self):
        """Test error in case of a very long slug."""
        res = self.client['registered'].post(
            self.url_new_project,
            data=simplejson.dumps({
                    'slug': 'new_pr', 'name': 'Project from API',
                    'source_language_code': 'el',
                    'maintainers': 'registered',
                    'description': 'desc',
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 201)
        with open(self.po_file) as f:
            content = f.read()
        res = self.client['registered'].post(
            self.url_create_resource,
            data=simplejson.dumps({
                    'name': "resource1",
                    'slug': 'a-very-long-slug' * 10,
                    'i18n_type': 'PO',
                    'content': content,
            }),
            content_type='application/json'
        )
        self.assertContains(res, 'value for slug is too long', status_code=400)

    def test_post_errors(self):
        res = self.client['registered'].post(
            self.url_new_project,
            data=simplejson.dumps({
                    'slug': 'new_pr', 'name': 'Project from API',
                    'source_language_code': 'el',
                    'maintainers': 'registered',
                    'description': 'desc',
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 201)
        with open(self.po_file) as f:
            content = f.read()
        res = self.client['registered'].post(
            self.url_create_resource,
            data=simplejson.dumps({
                    'name': "resource1",
                    'slug': 'r1',
                    'i18n_type': 'PO',
                    'content': content,
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 201)
        r = Resource.objects.get(slug='r1', project__slug='new_pr')
        self.assertEquals(len(r.available_languages_without_teams), 1)
        res = self.client['registered'].post(
            self.url_create_resource,
            data=simplejson.dumps({
                    'name': "resource1",
                    'slug': 'r1',
                    'i18n_type': 'PO',
                    'content': content,
            }),
            content_type='application/json'
        )
        self.assertContains(res, "already exists", status_code=400)
        res = self.client['registered'].post(
            self.url_create_resource,
            data=simplejson.dumps({
                    'name': "resource2",
                    'slug': 'r2',
                    'i18n_type': 'PO',
            }),
            content_type='application/json'
        )
        self.assertContains(res, "No content", status_code=400)
        self.assertRaises(
            Resource.DoesNotExist,
            Resource.objects.get,
            slug="r2", project__slug="new_pr"
        )


class TestTranslationAPI(APIBaseTests):

    def setUp(self):
        super(TestTranslationAPI, self).setUp()
        self.po_file = os.path.join(self.pofile_path, "pt_BR.po")
        self.url_resources = reverse(
            'apiv2_resources', kwargs={'project_slug': 'project1'}
        )
        self.url_resources_private = reverse(
            'apiv2_resources', kwargs={'project_slug': 'project2'}
        )
        self.url_resource = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'project1', 'resource_slug': 'resource1'}
        )
        self.url_resource_private = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'project2', 'resource_slug': 'resource1'}
        )
        self.url_new_project = reverse(
            'apiv2_projects'
        )
        self.url_create_resource = reverse(
            'apiv2_resources', kwargs={'project_slug': 'new_pr'}
        )
        self.url_new_resource = reverse(
            'apiv2_resource',
            kwargs={'project_slug': 'new_pr', 'resource_slug': 'r1', }
        )
        self.url_new_translation = reverse(
            'apiv2_translation',
            kwargs={
                'project_slug': 'new_pr',
                'resource_slug': 'new_r',
                'lang_code': 'el'
            }
        )

    def test_get_translation(self):
        res = self.client['anonymous'].get(self.url_new_translation)
        self.assertEquals(res.status_code, 401)
        res = self.client['registered'].get(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'project1',
                    'resource_slug': 'resource-not',
                    'lang_code': 'en_US',
                }
            )
        )
        self.assertEquals(res.status_code, 404)
        res = self.client['registered'].get(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'project1',
                    'resource_slug': 'resource1',
                    'lang_code': 'en_US',
                }
            )
        )
        self.assertEquals(len(simplejson.loads(res.content)), 2)
        self.assertEquals(res.status_code, 200)
        url = "".join([
                reverse(
                    'apiv2_translation',
                    kwargs={
                        'project_slug': 'project1',
                        'resource_slug': 'resource1',
                            'lang_code': 'en_US',
                    }),
                "?file"
        ])
        res = self.client['registered'].get(url)
        self.assertEquals(res.status_code, 200)

    def test_delete_translations(self):
        self._create_resource()
        f = open(self.po_file)
        res = self.client['registered'].put(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'fi'
                }
            ),
            data={
                'name': 'name.po',
                'attachment': f
            },
        )
        f.close()
        self.assertEquals(res.status_code, 200)
        res = self.client['anonymous'].delete(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'fi'
                }
            )
        )
        self.assertEquals(res.status_code, 401)
        res = self.client['registered'].delete(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'fi'
                }
            )
        )
        self.assertEquals(res.status_code, 204)
        res = self.client['registered'].delete(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'el'
                }
            )
        )
        self.assertContains(res, "source language", status_code=400)
        res = self.client['registered'].delete(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'no_resource',
                    'lang_code': 'fi'
                }
            )
        )
        self.assertEquals(res.status_code, 404)
        res = self.client['registered'].delete(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'no_project',
                    'resource_slug': 'r1',
                    'lang_code': 'fi'
                }
            )
        )
        self.assertEquals(res.status_code, 404)
        res = self.client['registered'].delete(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'en_NN'
                }
            )
        )
        self.assertEquals(res.status_code, 404)
        res = self.client['registered'].delete(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'no_project',
                    'resource_slug': 'r1',
                    'lang_code': 'source'
                }
            )
        )
        self.assertEquals(res.status_code, 404)
        res = self.client['maintainer'].delete(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'fi'
                }
            )
        )
        self.assertEquals(res.status_code, 403)
        res = self.client['registered'].delete(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'fi'
                }
            )
        )
        self.assertEquals(res.status_code, 404)
        res = self.client['registered'].delete(
            reverse(
                'apiv2_source_content',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                }
            )
        )
        self.assertContains(res, "source language", status_code=400)

    def test_put_translations(self):
        self._create_resource()
        # test strings
        res = self.client['registered'].post(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'el_GR',
                }
            )
        )
        self.assertEquals(res.status_code, 405)
        res = self.client['registered'].put(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'el',
                }
            )
        )
        self.assertContains(res, "No file", status_code=400)
        with open(self.po_file) as f:
            content = f.read()
        res = self.client['registered'].put(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr_not',
                    'resource_slug': 'r1',
                    'lang_code': 'el',
                }
            ),
            data=simplejson.dumps([{
                    'content': content,
            }]),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 404)
        r = Resource.objects.get(slug="r1", project__slug="new_pr")
        self.assertEquals(len(r.available_languages_without_teams), 1)
        res = self.client['registered'].put(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'el',
                }
            ),
            data=simplejson.dumps({
                    'content': content,
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 200)
        self.assertEquals(len(r.available_languages_without_teams), 1)
        res = self.client['registered'].put(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'enb'
                }
            ),
            data=simplejson.dumps({
                    'content': content,
            }),
            content_type='application/json'
        )
        self.assertContains(res, "language code", status_code=400)

        # test files
        res = self.client['registered'].put(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'fi'
                }
            ),
            data={},
        )
        self.assertContains(res, "No file", status_code=400)
        f = open(self.po_file)
        res = self.client['registered'].put(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'fi'
                }
            ),
            data={
                'name': 'name.po',
                'attachment': f
            },
        )
        f.close()
        self.assertEquals(res.status_code, 200)
        self.assertEquals(len(r.available_languages_without_teams), 2)

        res = self.client['anonymous'].post(self.url_new_translation)
        self.assertEquals(res.status_code, 401)

        f = open(self.po_file)
        res = self.client['registered'].put(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'el',
                }
            ),
            data={
                'name': 'name.po',
                'attachment': f
            },
        )
        f.close()
        self.assertEquals(res.status_code, 200)

    def test_rlstats_updated(self):
        self._create_project()
        content = 'key = value'
        res = self.client['registered'].post(
            self.url_create_resource,
            data=simplejson.dumps({
                    'name': "resource1",
                    'slug': 'r1',
                    'i18n_type': 'INI',
                    'content': content,
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 201)
        translation = u'key = τιμή'
        res = self.client['registered'].put(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                    'lang_code': 'fi',
                }
            ),
            data=simplejson.dumps({
                    'content': translation,
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 200)
        r = Resource.objects.get(slug='r1', project__slug='new_pr')
        l = Language.objects.by_code_or_alias('fi')
        rl = RLStats.objects.get(resource=r, language=l)
        self.assertEquals(rl.translated_perc, 100)
        content += '\nother = other'
        res = self.client['registered'].put(
            reverse(
                'apiv2_source_content',
                kwargs={
                    'project_slug': 'new_pr',
                    'resource_slug': 'r1',
                }
            ),
            data=simplejson.dumps({
                    'content': content,
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 200)
        rl = RLStats.objects.get(resource=r, language=l)
        self.assertEquals(rl.translated_perc, 50)

    def test_unicode_resource_name(self):
        self._create_project()
        with open(self.po_file) as f:
            content = f.read()
        res = self.client['registered'].post(
            self.url_create_resource,
            data=simplejson.dumps({
                    'name': "rα",
                    'slug': 'r1',
                    'i18n_type': 'PO',
                    'content': content,
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 201)
        url = "".join([
                reverse(
                    'apiv2_translation',
                    kwargs={
                        'project_slug': 'new_pr',
                        'resource_slug': 'r1',
                            'lang_code': 'en_US',
                    }),
                "?file"
        ])
        res = self.client['registered'].get(url)
        self.assertEquals(res.status_code, 200)

    def _create_project(self):
        res = self.client['registered'].post(
            self.url_new_project,
            data=simplejson.dumps({
                    'slug': 'new_pr', 'name': 'Project from API',
                    'source_language_code': 'el',
                    'maintainers': 'registered',
                    'description': 'desc',
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 201)

    def _create_resource(self):
        self._create_project()
        with open(self.po_file) as f:
            content = f.read()
        res = self.client['registered'].post(
            self.url_create_resource,
            data=simplejson.dumps({
                    'name': "resource1",
                    'slug': 'r1',
                    'i18n_type': 'PO',
                    'content': content,
            }),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 201)
        r = Resource.objects.get(slug='r1', project__slug='new_pr')
        self.assertEquals(len(r.available_languages_without_teams), 1)


class TestStatsAPI(APIBaseTests):

    def setUp(self):
        super(TestStatsAPI, self).setUp()
        self.content = 'KEY1="Translation"\nKEY2="Translation with "_QQ_"quotes"_QQ_""'
        self.project_slug = 'new_pr'
        self.resource_slug='r1'
        self.url_new_project = reverse(
            'apiv2_projects'
        )
        self.url_create_resource = reverse(
            'apiv2_resources', kwargs={'project_slug': self.project_slug}
        )
        self._create_project()
        self._create_resource()

    def test_get_stats(self):
        r = Resource.objects.get(slug='r1')
        greek = 'KEY1="Μετάφραση"\nKEY2="Μετάφραση με "_QQ_"εισαγωγικά"_QQ_""'
        res = self.client['registered'].put(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': self.project_slug,
                    'resource_slug': self.resource_slug,
                    'lang_code': 'el'
                }
            ),
            data=simplejson.dumps({'content': greek}),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 200)
        res = self.client['registered'].get(
            reverse(
                'apiv2_stats',
                kwargs={
                    'project_slug': self.project_slug,
                    'resource_slug': self.resource_slug,
                    'lang_code': 'el',
                }
            )
        )
        self.assertEquals(res.status_code, 200)
        data = simplejson.loads(res.content)
        self.assertEquals(data['completed'], '100%')
        german = 'KEY1="Übersetzung"\nKEY2="Übersetzung mit "_QQ_"Zitate"_QQ_""'
        res = self.client['registered'].put(
            reverse(
                'apiv2_translation',
                kwargs={
                    'project_slug': self.project_slug,
                    'resource_slug': self.resource_slug,
                    'lang_code': 'af'
                }
            ),
            data=simplejson.dumps({'content': german}),
            content_type='application/json'
        )
        self.assertEquals(res.status_code, 200)
        res = self.client['registered'].get(
            reverse(
                'apiv2_stats',
                kwargs={
                    'project_slug': self.project_slug,
                    'resource_slug': self.resource_slug,
                    'lang_code': 'af',
                }
            )
        )
        self.assertEquals(res.status_code, 200)
        data = simplejson.loads(res.content)
        self.assertEquals(data['completed'], '100%')
        res = self.client['registered'].get(
            reverse(
                'apiv2_stats',
                kwargs={
                    'project_slug': self.project_slug,
                    'resource_slug': self.resource_slug,
                }
            )
        )
        self.assertEquals(res.status_code, 200)
        data = simplejson.loads(res.content)
        self.assertEquals(data['el']['completed'], '100%')
        self.assertEquals(data['af']['completed'], '100%')

    def _create_project(self):
        res = self.client['registered'].post(
            self.url_new_project,
            data=simplejson.dumps({
                    'slug': self.project_slug, 'name': 'Project from API',
                    'source_language_code': 'el',
                    'maintainers': 'registered',
                    'description': 'desc',
            }),
            content_type='application/json'
        )

    def _create_resource(self):
        res = self.client['registered'].post(
            self.url_create_resource,
            data=simplejson.dumps({
                    'name': "resource1",
                    'slug': self.resource_slug,
                    'i18n_type': 'INI',
                    'content': self.content,
            }),
            content_type='application/json'
        )

class TestFormatsAPI(APIBaseTests):
    def test_formats_api(self):
        res = self.client['registered'].get(
            reverse('supported_formats')
        )
        self.assertEqual(res.status_code, 200)
        json = simplejson.loads(res.content)
        self.assertEqual(registry.available_methods, json)


class UnitTestTranslationObjectsHandler(TestCase):
    def setUp(self):
        self.obj = TranslationObjectsHandler()
    def test_get_fieldmap(self):
        expected_fieldmap = {
            'source_entity__string': 'key',
            'source_entity__context': 'context',
            'string': 'translation',
            'reviewed': 'reviewed',
            'source_entity__pluralized': 'pluralized'
        }
        fieldmap = self.obj._get_fieldmap(False)
        self.assertEqual(fieldmap, expected_fieldmap)

        expected_fieldmap.update({
            'wordcount': 'wordcount',
            'last_update': 'last_update',
            'user__username': 'user',
            'source_entity__position': 'position',
            'source_entity__occurrences': 'occurrences',
        })

        fieldmap = self.obj._get_fieldmap(True)
        self.assertEqual(fieldmap, expected_fieldmap)

    def test_get_fields_for_translation_value_query_set(self):
        fieldmap = {
            'source_entity__string': 'key',
            'source_entity__context': 'context',
            'string': 'translation',
            'reviewed': 'reviewed',
            'source_entity__pluralized': 'pluralized'
        }
        expected_fields = [
            'source_entity__id',
            'source_entity__string',
            'source_entity__context', 'string',
            'reviewed', 'source_entity__pluralized',
            'rule',
        ]
        fields = self.obj._get_fields_for_translation_value_query_set(fieldmap)
        fields.sort()
        expected_fields.sort()
        self.assertEqual(fields, expected_fields)

        fieldmap.update({
            'wordcount': 'wordcount',
            'last_update': 'last_update',
            'user__username': 'user',
            'source_entity__position': 'position',
            'source_entity__occurrences': 'occurrences',
        })

        expected_fields.extend([
            'wordcount', 'last_update', 'user__username',
            'source_entity__position', 'source_entity__occurrences',
        ])
        fields = self.obj._get_fields_for_translation_value_query_set(fieldmap)
        fields.sort()
        expected_fields.sort()
        self.assertEqual(fields, expected_fields)

    def test_get_translation_query_filters(self):
        request = Mock()
        resource = Mock()
        language = Mock()
        request.GET = {}
        filters = self.obj._get_translation_query_filters(request,
                resource, language)
        expected_filters = {'resource': resource, 'language':language}
        self.assertEqual(filters, expected_filters)

        request.GET['key'] = 'foo'
        filters = self.obj._get_translation_query_filters(request,
                resource, language)
        expected_filters['source_entity__string__icontains'] = 'foo'
        self.assertEqual(filters, expected_filters)

        request.GET['context'] = 'bar'
        filters = self.obj._get_translation_query_filters(request,
                resource, language)
        expected_filters['source_entity__context__icontains'] = 'bar'
        self.assertEqual(filters, expected_filters)

    def test_validate_translations_json_data(self):
        self.assertRaises(NoContentError,
                self.obj._validate_translations_json_data, None)
        self.assertRaises(BadRequestError,
                self.obj._validate_translations_json_data, {'foo':'bar'})
        self.assertRaises(NoContentError,
                self.obj._validate_translations_json_data, "")
        self.assertTrue(self.obj._validate_translations_json_data([{}]))

    def test_user_has_update_perms(self):
        self.assertFalse(self.obj._user_has_update_perms(
                can_submit_translations=False
            ))
        translation_objs = [Mock()]
        translation_objs[0].reviewed = False
        self.assertFalse(self.obj._user_has_update_perms(
                can_submit_translations=True,
            ))
        self.assertFalse(self.obj._user_has_update_perms(
                accept_translations=True,
            ))
        self.assertFalse(self.obj._user_has_update_perms(
                is_maintainer=True,
            ))

        self.assertFalse(self.obj._user_has_update_perms(
                can_submit_translations=True,
                accept_translations=True,
            ))

        self.assertTrue(self.obj._user_has_update_perms(
                translation_objs=translation_objs,
                can_submit_translations=True,
                accept_translations=True,
                translation_reviewed=False
            ))

        self.assertFalse(self.obj._user_has_update_perms(
                can_submit_translations=True,
                accept_translations=True,
                translation_objs=translation_objs,
                translation_reviewed=True
            ))

        self.assertTrue(self.obj._user_has_update_perms(
                is_maintainer=True,
                translation_objs=translation_objs,
                translation_reviewed=False
            ))

        translation_objs[0].reviewed = True
        self.assertFalse(self.obj._user_has_update_perms(
                can_submit_translations=True,
                accept_translations=True,
                translation_objs=translation_objs,
                translation_reviewed=False
            )
        )
        self.assertTrue(self.obj._user_has_update_perms(
                can_submit_translations=True,
                accept_translations=True,
                can_review=True,
                translation_objs=translation_objs,
                translation_reviewed=True
            )
        )

    def test_collect_updated_translations(self):
        t1 = Mock()
        t1.rule = 5
        t1.reviewed = True
        user = Mock()
        translation = {'translation': 'foo', 'reviewed': False}

        se_id = 1
        trans_obj_dict = {se_id: [t1]}
        updated_translations = []
        pluralized = False
        self.obj._collect_updated_translations(translation, trans_obj_dict,
                se_id, updated_translations, user, pluralized)
        self.assertTrue(t1 in updated_translations)
        self.assertEqual(t1.user, user)
        self.assertEqual(t1.reviewed, False)
        self.assertEqual(t1.string, 'foo')

        t2 = Mock()
        t2.rule = 1
        t2.reviewed = False
        translation = {'translation':{'1':'foo1', '5':'foo5'}}
        updated_translations = []
        trans_obj_dict[se_id].append(t2)
        pluralized = True
        self.obj._collect_updated_translations(translation, trans_obj_dict,
                se_id, updated_translations, user, pluralized)
        self.assertTrue(t1 in updated_translations)
        self.assertTrue(t2 in updated_translations)
        self.assertEqual(t2.user, user)
        self.assertEqual(t2.reviewed, False)
        self.assertEqual(t2.string, 'foo1')
        self.assertEqual(t1.string, 'foo5')

    def test_is_pluralized(self):
        translation = {'key': 'foo', 'context': ''}
        translation['translation'] =  {1: 'one', 5: 'other'}
        nplurals = [1, 5]
        self.assertTrue(self.obj._is_pluralized(translation,nplurals))
        translation['translation'] = {0: 'zero', 1: 'one', 5: 'other'}
        nplurals = [1, 5]
        self.assertRaises(BadRequestError, self.obj._is_pluralized,
                translation, nplurals)
        translation['translation'] =  {1: 'one', 5: 'other'}
        nplurals = [0, 1, 5]
        self.assertRaises(BadRequestError, self.obj._is_pluralized,
                translation, nplurals)
        translation['translation'] = '   '
        nplurals = [1, 5]
        self.assertFalse(self.obj._is_pluralized(translation,
            nplurals))
        translation['translation'] = 'foo'
        self.assertFalse(self.obj._is_pluralized(translation,
            nplurals))

    def test_get_update_fieldmap_and_fields(self):
        keys = ['source_entity_id', 'key', 'context', 'user',
                'reviewed', 'pluralized']
        field_map, fields = self.obj._get_update_fieldmap_and_fields(keys)
        self.assertEqual(field_map, {
                'source_entity__string': 'key',
                'source_entity__context': 'context',
                'user__username': 'user',
                'reviewed': 'reviewed',
                'source_entity__pluralized': 'pluralized'
            }
        )
        expected_fields = field_map.keys()
        expected_fields.extend(['rule'])
        expected_fields.sort()
        fields.sort()
        self.assertEqual(fields, expected_fields)


class SystemTestTranslationStrings(BaseTestCase):
    def test_requested_objects(self):
        obj = TranslationObjectsHandler()
        self.assertRaises(NotFoundError,
                obj._requested_objects,
                'foo', 'resource1', 'foo')
        self.assertRaises(NotFoundError,
                obj._requested_objects,
                'project1', 'foo', 'foo')
        self.assertRaises(NotFoundError,
                obj._requested_objects,
                'project1', 'resource1', 'foo')
        self.assertEqual(
                obj._requested_objects(
                    'project1', 'resource1', 'ar'),
                (self.project, self.resource, self.language_ar))

    def test_validate_language_is_not_source_language(self):
        obj = TranslationObjectsHandler()
        value = obj._validate_language_is_not_source_language(
                self.project.source_language, self.language)
        self.assertRaises(ForbiddenError,
                obj._validate_language_is_not_source_language,
                self.project.source_language, self.language_en)

    def test_read_translations(self):
        response = self.client['team_member'].get(reverse(
            'translation_strings',
            args=['project1', 'resource1', self.language_ar.code]))
        self.assertEqual(response.status_code, 200)


class SystemTestPutTranslationStrings(TransactionBaseTestCase):
    """Test updating translation strings"""
    def _setUp_test_put_translations(self):
        """Create some source strings and translations"""
        self = create_sample_translations(self)

    def test_put_translations(self):
        """test updating translation strings"""
        self._setUp_test_put_translations()
        response = self.client['team_member'].get(reverse(
            'translation_strings',
            args=['project1', 'resource1', self.language_ar.code]),
            data={'details':''})
        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        for index, item in enumerate(json):
            if item['key'] == 'pluralized_String1' and item['context'] == 'Context1':
                item['source_entity_hash'] = hash_tag(item['key'], item['context'])
                item['translation'] = {'0': '0', '1': '1', '2': '2', '3': '3',
                        '4': '4', '5': '5'}
                json[index] = item
            if item['key'] == 'String2' and item['context'] == 'Context2':
                item['source_entity_hash'] = hash_tag(item['key'], item['context'])
                item.pop('key')
                item.pop('context')
                item['translation'] = 'fooo'
                item['user'] = 'team_member'
                item['reviewed'] = True
                json[index] = item

        response = self.client['maintainer'].put(reverse(
            'translation_strings',
            args=['project1', 'resource1', self.language_ar.code]),
            data = simplejson.dumps(json),
            content_type="application/json")

        expected_json = []
        self.assertEqual(response.status_code, 403)
        for item in json:
            item.pop('user')
        response = self.client['maintainer'].put(reverse(
            'translation_strings',
            args=['project1', 'resource1', self.language_ar.code]),
            data = simplejson.dumps(json),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)


def create_sample_translations(cls):
    self = cls

    self.source_entity1 = SourceEntity.objects.create(string='String2',
        context='Context2', occurrences='Occurrences2',
        resource=self.resource)
    self.source_entity2 = SourceEntity.objects.create(string='String3',
        context='Context3', occurrences='Occurrences3',
        resource=self.resource)
    self.source_entity3 = SourceEntity.objects.create(string='String4',
        context='Context4', occurrences='Occurrences4',
        resource=self.resource)
    self.source_entity4 = SourceEntity.objects.create(string='String5',
        context='context5',occurrences='Occurreneces5',
        resource=self.resource)

    for se in SourceEntity.objects.all():
        se.string_hash = hash_tag(se.string, se.context or '')
        se.save()

    # Set some custom translation data
    # Source strings
    self.source_string1 = self.source_entity1.translations.create(
        string="String2",
        language = self.language_en,
        user=self.user['maintainer'], rule=5,
        resource=self.resource
    )

    self.source_string2 = self.source_entity2.translations.create(
        string="String3",
        language = self.language_en,
        user=self.user['maintainer'], rule=5,
        resource=self.resource
    )

    self.source_string3 = self.source_entity3.translations.create(
        string="String4",
        language = self.language_en,
        user=self.user['maintainer'], rule=5,
        resource=self.resource
    )

    self.source_string4 = self.source_entity4.translations.create(
        string="String with arguments: %s %d",
        language = self.language_en,
        user=self.user['maintainer'], rule=5,
        resource=self.resource
    )

    self.source_string_plural1 = \
            self.source_entity_plural.translations.create(
        string="SourceArabicTrans1",
        language=self.language_en,
        user=self.user["maintainer"], rule=1,
        resource=self.resource
    )
    self.source_string_plural2 = \
            self.source_entity_plural.translations.create(
        string="SourceArabicTrans2",
        language=self.language_en,
        user=self.user["maintainer"], rule=5,
        resource=self.resource
    )
    # Translation strings
    self.source_entity1.translations.create(
        string="ArabicString2", language=self.language_ar,
        user=self.user["maintainer"], rule=5,
        resource=self.resource
    )
    self.source_entity2.translations.create(
        string="", language=self.language_ar,
        user=self.user["maintainer"], rule=5,
        resource=self.resource
    )

    self.source_entity_plural.translations.create(
        string="ArabicTrans0", language=self.language_ar,
        user=self.user["maintainer"], rule=0,
        resource=self.resource
    )
    self.source_entity_plural.translations.create(
        string="ArabicTrans1", language=self.language_ar,
        user=self.user["maintainer"], rule=1,
        resource=self.resource
    )
    self.source_entity_plural.translations.create(
        string="ArabicTrans2", language=self.language_ar,
        user=self.user["maintainer"], rule=2,
        resource=self.resource
    )
    self.source_entity_plural.translations.create(
        string="ArabicTrans3", language=self.language_ar,
        user=self.user["maintainer"], rule=3,
        resource=self.resource
    )
    self.source_entity_plural.translations.create(
        string="ArabicTrans4", language=self.language_ar,
        user=self.user["maintainer"], rule=4,
        resource=self.resource
    )
    self.source_entity_plural.translations.create(
        string="ArabicTrans5", language=self.language_ar,
        user=self.user["maintainer"], rule=5,
        resource=self.resource
    )
    return self


class SystemTestSingleTranslationHandler(BaseTestCase):
    def setUp(self):
        """Create some source strings and translations"""
        super(SystemTestSingleTranslationHandler, self).setUp()
        self = create_sample_translations(self)

    def test_single_translation_handler(self):
        # read
        string_hash = self.source_entity1.string_hash
        response = self.client['team_member'].get(reverse('translation_string',
            args=[self.project.slug, self.resource.slug, self.language_ar.code,
                string_hash]),)

        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        self.assertEqual(json['translation'], self.source_entity1.translations.\
                get(language=self.language_ar).string)

        # update
        json['translation'] = 'Hello world'
        response = self.client['team_member'].put(reverse('translation_string',
            args=[self.project.slug, self.resource.slug, self.language_ar.code,
                string_hash]),
            data=simplejson.dumps(json),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        response = self.client['team_coordinator'].put(reverse('translation_string',
            args=[self.project.slug, self.resource.slug, self.language_ar.code,
                string_hash]),
            data=simplejson.dumps(json),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        json['user'] = 'team_member'
        response = self.client['maintainer'].put(reverse('translation_string',
            args=[self.project.slug, self.resource.slug, self.language_ar.code,
                string_hash]),
            data=simplejson.dumps(json),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        self.team.language=self.language_ar
        self.team.save()
        json['reviewed'] = True
        response = self.client['maintainer'].put(reverse('translation_string',
            args=[self.project.slug, self.resource.slug, self.language_ar.code,
                string_hash]),
            data=simplejson.dumps(json),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        json['user'] = 'team_coordinator'
        response = self.client['team_coordinator'].put(reverse(
            'translation_string', args=[self.project.slug,
                self.resource.slug, self.language_ar.code,
                string_hash]),
            data=simplejson.dumps(json),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(simplejson.loads(response.content)['translation'],
                'Hello world')
        self.assertEqual(simplejson.loads(response.content)['reviewed'],
                True)
        json['user'] = 'team_member'
        response = self.client['team_coordinator'].put(reverse(
            'translation_string', args=[self.project.slug,
                self.resource.slug, self.language_ar.code,
                string_hash]),
            data=simplejson.dumps(json),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        string_hash = self.source_entity_plural.string_hash
        response = self.client['team_member'].get(reverse('translation_string',
            args=[self.project.slug, self.resource.slug, self.language_ar.code,
                string_hash]),)

        self.assertEqual(response.status_code, 200)
        json = simplejson.loads(response.content)
        expected_translations = {}
        for translation in self.source_entity_plural.translations.filter(
                language=self.language_ar):
            expected_translations[str(translation.rule)] = translation.string
        self.assertEqual(json['translation'], expected_translations)

        json['translation']['0'] = 'foo'
        json['reviewed'] = False
        self.source_entity_plural.translations.filter(language=self.language_ar
                ).update(reviewed=True)
        response = self.client['maintainer'].put(reverse('translation_string',
            args=[self.project.slug, self.resource.slug, self.language_ar.code,
                string_hash]),
            data=simplejson.dumps(json),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(simplejson.loads(response.content)['translation'],
                json['translation'])
        self.assertEqual(self.source_entity_plural.translations.get(
            rule=0).string, json['translation']['0'])
        self.assertFalse(self.source_entity_plural.translations.filter(
            language=self.language_ar)[0].reviewed)

        source_entity = self.resource.source_entities.create(
                string="FOO", context="None",
                string_hash = hash_tag("FOO", "None"))
        string_hash = source_entity.string_hash
        response = self.client['team_member'].get(reverse('translation_string',
            args=[self.project.slug, self.resource.slug, self.language_ar.code,
                string_hash]),)

        self.assertEqual(response.status_code, 404)
        response = self.client['maintainer'].put(reverse('translation_string',
            args=[self.project.slug, self.resource.slug, self.language_ar.code,
                string_hash]),
            data=simplejson.dumps({
                'translation': 'foo bar'
            }),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 404)

