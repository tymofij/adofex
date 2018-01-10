# -*- coding: utf-8 -*-
import os
from django.conf import settings
from transifex.languages.models import Language
from transifex.txcommon.tests.base import BaseTestCase
from transifex.resources.formats.pofile import POHandler
from transifex.resources.models import Resource
from transifex.resources.tests.api.utils import ORIGINAL, TRANSLATION




class APIBaseTests(BaseTestCase):
    """Tests for the ResourceHandler API."""
    def setUp(self):
        self.current_path = os.path.split(__file__)[0]
        super(APIBaseTests, self).setUp()

        # Opening JSON data for pushing through the API
        self.data = ORIGINAL
        self.trans = TRANSLATION
        self.pofile_path = os.path.join(
            settings.TX_ROOT, 'resources/tests/lib/pofile'
        )

        # Loading POT (en_US) into the resource
        handler = POHandler('%s/tests.pot' % self.pofile_path)
        handler.set_language(self.language_en)
        handler.parse_file(is_source=True)
        handler.bind_resource(self.resource)
        handler.save2db(is_source=True)

        # Loading PO (pt_BR) into the resource
        handler.bind_file('%s/pt_BR.po' % self.pofile_path)
        handler.set_language(self.language)
        handler.parse_file()
        handler.save2db()
