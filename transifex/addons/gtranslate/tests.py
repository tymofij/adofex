# -*- coding: utf-8 -*-

from django.conf import settings
from transifex.txcommon.tests.base import BaseTestCase, Languages
from transifex.projects.models import Project
from handlers import *
from models import Gtranslate
from transifex.addons.gtranslate import is_gtranslate_allowed

class TestGtranslate(BaseTestCase):

    def test_delete(self):
        """Test, if a gtranslate entry is deleted, when the corresponding
        project is delete.
        """
        p = Project(slug="rm")
        p.name = "RM me"
        p.source_language = self.language_en
        p.save()
        Gtranslate.objects.create(project=p)
        p.delete()
        self.assertEquals(Gtranslate.objects.all().count(), 0)
