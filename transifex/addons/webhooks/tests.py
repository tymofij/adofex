# -*- coding: utf-8 -*-

"""
Tests for the webhook addon.
"""

from __future__ import with_statement
from mock import patch
from django.core.exceptions import ValidationError
from transifex.txcommon.log import logger
from transifex.txcommon.tests.base import BaseTestCase
from webhooks.models import WebHook
from webhooks.handlers import visit_url, add_web_hook_field, save_web_hook
from transifex.resources.models import RLStats
from transifex.projects.forms import ProjectForm


class TestWebHooks(BaseTestCase):
    """Test the web hooks addon."""

    def setup():
        super(TestWebHooks, self).setUp()
        self.web_hook = WebHook.objects.create(
            project=self.project, url='https://127.0.0.1'
        )

    def test_no_hook(self):
        """Test the case where the project hasn't defined a web hook."""
        stats = RLStats.objects.get(
            resource=self.resource, language=self.language_en
        )
        with patch.object(logger, 'error') as log_mock:
            visit_url(sender=stats)
            self.assertFalse(log_mock.called)

    def test_wrong_url(self):
        """Test that an error occurs, if you try to create a web hook
        with a local URI.
        """
        hook = WebHook.objects.create(
            project=self.project, url='file:///etc/passwd'
        )
        self.assertRaises(ValidationError, hook.full_clean)

    def test_error_response(self):
        stats = RLStats.objects.get(
            resource=self.resource, language=self.language_en
        )
        web_hook = WebHook.objects.create(
            project=self.resource.project, url='https://127.0.0.1'
        )
        with patch.object(logger, 'error') as log_mock:
            visit_url(stats, post_function=_mock_error_request)
            self.assertTrue(log_mock.called)

    def test_successful_response(self):
        stats = RLStats.objects.get(
            resource=self.resource, language=self.language_en
        )
        web_hook = WebHook.objects.create(
            project=self.resource.project, url='https://127.0.0.1'
        )
        with patch.object(logger, 'error') as log_mock:
            visit_url(stats, post_function=_mock_successful_request)
            self.assertFalse(log_mock.called)


class TestWebHookHandlers(BaseTestCase):
    """Test signal handlers for project edit form."""

    def test_add_field(self):
        kwargs = {'form': ProjectForm()}
        add_web_hook_field(None, **kwargs)
        self.assertIn('webhook', kwargs['form'].fields)


def _mock_successful_request(*args, **kwargs):
    """Mock a request and return a success status code."""
    return MockResponse(200)


def _mock_error_request(*args, **kwargs):
    """Mock a request and return an error status code."""
    return MockResponse(400)


class MockResponse(object):
    """Mock a response object.

    Mimic the response object of the requests library.
    """

    def __init__(self, code):
        self.status_code = code
        self.ok = self.status_code == 200
