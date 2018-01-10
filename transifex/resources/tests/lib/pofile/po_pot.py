# -*- coding: utf-8 -*-

"""
Test PO/POT Handler invocations.

There are two kinds:

  - get/read
  - put/create
"""

from __future__ import with_statement
import os
from mock import patch
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils import simplejson
from django.test import TestCase
from django.test.client import Client, RequestFactory
from transifex.txcommon.tests.base import BaseTestCase
from transifex.languages.models import Language
from transifex.resources.formats.registry import registry
from transifex.resources.views import update_translation
from transifex.resources.templatetags.upload_manager_tags import \
        upload_create_resource_form
from transifex.resources.backends import FormatsBackend
from transifex.resources.api import Translation
from transifex.resources.formats.pofile import POHandler, POTHandler


class TestApiInvocations(BaseTestCase):
    """Test PO/POT Handler invokations in the API.

    We need to test POST for resources and GET and PUT for translations and
    source content.
    """

    def setUp(self):
        super(TestApiInvocations, self).setUp()
        self.resource.i18n_type = 'PO'
        self.resource.save()
        self.source_url = reverse(
            'apiv2_source_content', kwargs={
                'project_slug': self.resource.project.slug,
                'resource_slug': self.resource.slug,
            }
        )
        self.translation_url = reverse(
            'apiv2_translation', kwargs={
                'project_slug': self.resource.project.slug,
                'resource_slug': self.resource.slug,
                'lang_code': 'el'
            }
        )

    @patch.object(POHandler, 'compile')
    def test_get(self, mock_po):
        """Test GET method for API.

        Test for both source content and translations, json and file
        responses.
        """
        for url in (self.source_url, self.translation_url):
            self.client['maintainer'].get(url)
            self.assertTrue(mock_po.called)
            res = self.client['maintainer'].get(url, data={'file' : ''})
            self.assertTrue(mock_po.called)
            attachment = res.items()[1][1]
            filename = attachment[30:-1]
            self.assertTrue(filename.endswith('po'))

    @patch.object(Translation, '_parse_translation')
    @patch.object(POHandler, 'is_content_valid')
    def test_put(self, _mock, mock):
        """Test PUT method for the API.

        Test filenames used.
        """
        # JSON APi
        mock.return_value = {
            'strings_added': 0,
            'strings_updated': 0,
            'redirect': reverse(
                'resource_detail',
                args=[self.resource.project.slug, self.resource.slug]
            )
        }
        self.client['maintainer'].put(
            self.translation_url,
            data=simplejson.dumps({'content': '', }),
            content_type='application/json'
        )
        self.assertTrue(mock.called)
        used_handler = mock.call_args[0][0]
        self.assertIsInstance(used_handler, type(registry.handler_for('PO')))

        res = self.client['maintainer'].put(
            self.source_url,
            data=simplejson.dumps({'content': '', }),
            content_type='application/json'
        )
        self.assertTrue(mock.called)
        self.assertIsInstance(used_handler, type(registry.handler_for('PO')))

        # filename API
        pofile_path = os.path.join(
            settings.TX_ROOT, 'resources/tests/lib/pofile'
        )
        po_filename = os.path.join(pofile_path, "pt_BR.po")
        pot_filename = os.path.join(pofile_path, "general/test.pot")
        po_class = type(registry.handler_for('PO'))
        pot_class = type(registry.handler_for('POT'))

        for url in (self.source_url, self.translation_url):
            with open(po_filename) as f:
                self.client['maintainer'].put(
                    url, data={
                        'name': 'name.po',
                        'attachment': f
                    },
                )
                self.assertTrue(mock.called)
                used_handler = mock.call_args[0][0]
                self.assertIsInstance(used_handler, po_class)
            with open(pot_filename) as f:
                self.client['maintainer'].put(
                    url, data={
                        'name': 'name.po',
                        'attachment': f
                    },
                )
                self.assertTrue(mock.called)
                used_handler = mock.call_args[0][0]
                self.assertIsInstance(used_handler, pot_class)


class TestViewsInvocations(BaseTestCase):
    """Test PO/POT Handler invokations in the views.

    Test for both source content and translations, json and file
    responses. Test for specific download of POT file, too.
    """

    def setUp(self):
        super(TestViewsInvocations, self).setUp()
        self.resource.i18n_type = 'PO'
        self.resource.save()
        self.pslug = self.resource.project.slug
        self.rslug = self.resource.slug
        self.rname = self.resource.name
        self.mclient = self.client['maintainer']

    @patch.object(POHandler, 'compile')
    @patch.object(POTHandler, 'compile')
    def test_get(self, mock_pot, mock_po):
        po_source_url = reverse(
            'download_for_translation', kwargs={
                'project_slug': self.pslug,
                'resource_slug': self.rslug,
                'lang_code': 'en'
            }
        )
        po_translation_url = reverse(
            'download_for_translation', kwargs={
                'project_slug': self.pslug,
                'resource_slug': self.rslug,
                'lang_code': 'el'
            }
        )
        pot_url = reverse(
            'download_pot', kwargs={
                'project_slug': self.pslug,
                'resource_slug': self.rslug,
            }
        )
        for url in (po_source_url, po_translation_url):
            res = self.mclient.get(url)
            self.assertTrue(mock_po.called)
            attachment = res.items()[3][1]
            filename = attachment[22:]
            self.assertTrue(filename.endswith('po'))

        res = self.mclient.get(pot_url)
        self.assertTrue(mock_pot.called)
        attachment = res.items()[3][1]
        filename = attachment[22:]
        self.assertTrue(filename.endswith('pot'))

    @patch.object(FormatsBackend, '_import_content')
    def test_put(self, import_mock):
        """Check file upload through views.

        Specifically,
        - resource_edit view
        - upload_create_resource_form
        - create_translation_form
        - update_translation_form
        """
        pofile_path = os.path.join(
            settings.TX_ROOT, 'resources/tests/lib/pofile'
        )
        po_filename = os.path.join(pofile_path, "pt_BR.po")
        pot_filename = os.path.join(pofile_path, "general/test.pot")
        po_class = type(registry.handler_for('PO'))
        pot_class = type(registry.handler_for('POT'))

        resource_edit_url = reverse(
            'resource_edit', kwargs={
                'project_slug': self.pslug,
                'resource_slug': self.rslug,
            }
        )
        filenames, klasses = [po_filename, pot_filename], [po_class, pot_class]
        for (filename, klass) in zip(filenames, klasses):
            with open(filename) as f:
                self.mclient.post(
                    resource_edit_url, data={
                        'sourcefile': f,
                        'slug': self.resource.slug,
                        'name': self.resource.name,
                    }
                )
                self.assertTrue(import_mock.called)
                used_handler = import_mock.call_args[0][0]
                self.assertIsInstance(used_handler, klass)

        # Test template tags
        factory = RequestFactory()

        # Create request for template tags
        url = reverse('project_detail', kwargs={'project_slug': self.pslug})
        for (filename, klass) in zip(filenames, klasses):
            with open(filename) as f:
                request = factory.post(
                    url, data={
                        'create_resource': True,
                        'create_form-name': 'Name',
                        'create_form-i18n_method': 'PO',
                        'create_form-source_file': f
                    }
                )
                # we need to patch the request.user object
                with patch.object(request, 'user', create=True) as mock:
                    mock.return_value = self.user['maintainer']
                    upload_create_resource_form(request, self.project)
                    self.assertTrue(import_mock.called)
                    used_handler = import_mock.call_args[0][0]
                    self.assertIsInstance(used_handler, klass)

        with open(po_filename) as f:
            lang_code = 'en_US'
            url = reverse(
                'update_translation',
                kwargs={
                    'project_slug': self.pslug,
                    'resource_slug': self.rslug,
                    'lang_code': lang_code,
                }
            )
            request = factory.post(
                url, data={
                    'name': po_filename,
                    'attachment': f
                }
            )
            # we need to patch the request.user object for the request
            with patch.object(request, 'user', create=True) as mock:
                mock.return_value = self.user['maintainer']
                update_translation(
                    request, project_slug=self.pslug,
                    resource_slug=self.rslug, lang_code=lang_code
                )
                self.assertTrue(import_mock.called)
                used_handler = import_mock.call_args[0][0]
                self.assertIsInstance(used_handler, po_class)

            request = factory.post(
                url, data={
                    'name': po_filename,
                    'attachment': f,
                    'language_code': 'en_US'
                }
            )
            # we need to patch the request.user object for the request
            with patch.object(request, 'user', create=True) as mock:
                mock.return_value = self.user['maintainer']
                update_translation(
                    request, project_slug=self.pslug, resource_slug=self.rslug
                )
                self.assertTrue(import_mock.called)
                used_handler = import_mock.call_args[0][0]
                self.assertIsInstance(used_handler, po_class)
