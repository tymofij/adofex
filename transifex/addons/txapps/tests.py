# -*- coding: utf-8 -*-

from __future__ import with_statement
import requests
from mock import patch
from django.test import TestCase
from transifex.txcommon.tests.base import Users, BaseTestCase
from txapps.views import _root_namespace, _remove_namespace_from_path, \
        _add_namespace_to_path, _forward_to_app
from txapps.models import TxApp
from txapps.exceptions import RemoteTxAppError


class TestTxApp(Users, TestCase):
    """Test Transifex's TxApp support."""

    @classmethod
    def setUpClass(cls):
        app_slug = 'test_txapp'
        cls.app = TxApp.objects.create(
            slug=app_slug, name='Test TxApp',
            description='Desc', url='http://127.0.0.1'
        )
        cls.root_path = 'root/path/'
        cls.namespace_path = ''.join([cls.root_path, app_slug])

    @classmethod
    def tearDownClass(cls):
        cls.app.delete()

    def test_finding_root_namespace(self):
        """Test root namespaces."""
        path = '/'.join([self.namespace_path, 'overview'])
        res = _root_namespace(path, self.app)
        self.assertEquals(res, self.namespace_path)

    def test_path_sent_to_txapp(self):
        """Test the extraction of the path sent to TxApp."""
        path_wanted = 'overview/'
        path = '/'.join([self.namespace_path, path_wanted])
        res = _remove_namespace_from_path(self.namespace_path, path)
        self.assertEquals(res, path_wanted)

    def test_adding_namespace_to_path(self):
        """Test the insertion of the namespace path to a path
        returned by a TxApp.
        """
        path_returned = 'token/'
        full_path = '/'.join([self.namespace_path, path_returned])
        self.assertEquals(
            full_path,
            _add_namespace_to_path(self.namespace_path, path_returned)
        )
        path_returned = '/token/'
        full_path = ''.join([self.namespace_path, path_returned])
        self.assertEquals(
            full_path,
            _add_namespace_to_path(self.namespace_path, path_returned)
        )

    def test_forward_request_to_app(self):
        """Test forwarding a request to TxApp."""
        class Response(object):
            def __init__(self, ok, content, status_code):
                self.ok = ok
                self.content = content
                self.status_code = status_code

        with patch('requests.post') as mock:
            mock.return_value = Response(True, '"OK"', 200)
            res = _forward_to_app(self.app.url, 'POST')
            self.assertEquals(res, "OK")

        with patch('requests.post') as mock:
            mock.return_value = Response(False, '"Error"', 404)
            self.assertRaises(
                RemoteTxAppError, _forward_to_app, self.app.url, 'POST'
            )

class TestTxAppPermissions(BaseTestCase):
    """Test permissions in tx apps."""

    def setUp(self):
        super(TestTxAppPermissions, self).setUp()
        app_slug = 'test_txapp'
        self.app = TxApp.objects.create(
            slug=app_slug, name='Test TxApp',
            description='Desc', url='http://127.0.0.1'
        )
        self.root_path = 'root/path/'
        self.namespace_path = ''.join([self.root_path, app_slug])
        TxApp.objects.enable_app_for_project(self.app, self.project)

    def test_no_exceptions(self):
        """Test permissions."""
        user = self.project.owner
        path = 'foo'
        self.assertTrue(self.app.access_is_allowed(user, self.project, path))
        for user in [self.user['team_member'], self.user['registered'], ]:
            self.assertFalse(
                self.app.access_is_allowed(user, self.project, path)
            )

    def test_exceptions(self):
        path_allowed = 'allowed'
        path_not_allowed = 'notallowed'
        self.app.team_allowed = [path_allowed]
        self.app.save()
        user = self.project.owner
        self.assertTrue(
            self.app.access_is_allowed(user, self.project, path_allowed)
        )
        self.assertTrue(
            self.app.access_is_allowed(user, self.project, path_not_allowed)
        )
        user = self.user['team_member']
        self.assertTrue(self.app.access_is_allowed(
                user, self.project, path_allowed)
        )
        self.assertFalse(
            self.app.access_is_allowed(user, self.project, path_not_allowed)
        )
