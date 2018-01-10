import os
from django.conf import settings
from django.db.models.loading import get_model
from django.contrib.auth.models import User
from django.test import TestCase

from transifex.languages.models import Language
from transifex.resources.models import Resource
from transifex.resources.formats.pofile import POHandler
from transifex.txcommon.tests.base import BaseTestCase

from copyright.handlers import lotte_copyrights, save_copyrights

Copyright = get_model('copyright', 'Copyright')

class CopyrightTests(BaseTestCase):

    def test_manager(self):
        """Test manager's methods and attributes."""

        # Create basic copyright
        cr = Copyright.objects.assign(
            language=self.language_en, resource=self.resource,
            owner='John Doe', year='2014')
        self.assertEqual(str(cr), "John Doe, 2014.")

        # Test existing copyright
        cr = Copyright.objects.assign(
            language=self.language_en, resource=self.resource,
            owner='John Doe', year='2014')
        self.assertEqual(str(cr), "John Doe, 2014.")

        # Create consecutive copyright year
        cr = Copyright.objects.assign(
            language=self.language_en, resource=self.resource,
            owner='John Doe', year='2015')
        self.assertEqual(str(cr), "John Doe, 2014, 2015.")

        # Create non-consecutive copyright year
        cr = Copyright.objects.assign(
            language=self.language_en, resource=self.resource,
            owner='John Doe', year='2018')
        self.assertEqual(str(cr), "John Doe, 2014, 2015, 2018.")

        # Create another copyright holder
        cr = Copyright.objects.assign(
            language=self.language_en, resource=self.resource,
            owner='Django Reinhardt', year='2010')
        self.assertEqual(str(cr), "Django Reinhardt, 2010.")


    def copyright_text_load(self):
        """Test the conversion of a copyright text to db objects."""
        sample_text = "Copyright (C) 2007-2010 Indifex Ltd."
        # load sample text
        # test db objects

    def test_poheader_load_soureclang(self):
        """Test load of existing PO file with copyright headers."""

        test_file = os.path.join(settings.TX_ROOT,
                                 './resources/tests/lib/pofile/copyright.po')
        handler = POHandler(test_file)
        handler.bind_resource(self.resource)
        handler.set_language(self.resource.source_language)
        handler.parse_file(is_source=True)
        handler.save2db(is_source=True)
        c = Copyright.objects.filter(
            resource=self.resource, language=self.resource.source_language
        )
        self.assertEquals(len(c), 3)

    def test_user_from_db(self):
        cr = Copyright.objects.assign(
            language=self.language_en, resource=self.resource,
            owner='Test Test <test@test.org>', year='2010')
        self.assertTrue(cr.user is None)
        u = User.objects.create(username='test', email='test@test.org')
        cr = Copyright.objects.assign(
            language=self.language_en, resource=self.resource,
            owner='Test Test <test@test.org>', year='2010')
        self.assertTrue(cr.user == u)

    def test_lotte_copyrights(self):
        c = Copyright.objects.filter(
            resource=self.resource, language=self.language_en
        )
        self.assertEquals(len(c), 0)
        lotte_copyrights(
            sender=None, resource=self.resource, language=self.language_en,
            user=self.user['maintainer']
        )
        c = Copyright.objects.filter(
            resource=self.resource, language=self.language_en
        )
        self.assertEquals(len(c), 1)
        lotte_copyrights(
            sender=None, resource=self.resource, language=self.language_en,
            user=self.user['maintainer']
        )
        c = Copyright.objects.filter(
            resource=self.resource, language=self.language_en
        )
        self.assertEquals(len(c), 1)

    def test_multiple_emails(self):
        u1 = User.objects.create(
            username='copy1', email='copy@copy.org'
        )
        u2 = User.objects.create(
            username='copy2', email='copy@copy.org',
            first_name='Copy', last_name='Cat'
        )
        lotte_copyrights(
            None, resource=self.resource, language=self.language_en, user=u1
        )
        c = Copyright.objects.filter(
            resource=self.resource, language=self.language_en
        )
        self.assertEquals(len(c), 1)
        self.assertEquals(c[0].user, u1)
        lotte_copyrights(
            None, resource=self.resource, language=self.language_en, user=u2
        )
        c = Copyright.objects.filter(
            resource=self.resource, language=self.language_en
        )
        self.assertEquals(len(c), 2)
        self.assertIn(c[0].user, [u1, u2])
        self.assertIn(c[1].user, [u1, u2])
        save_copyrights(
            None, resource=self.resource, language=self.language_en,
            copyrights=[('Copy Cat <copy@copy.org>', ['2011', ]), ]
        )
        c = Copyright.objects.filter(
            resource=self.resource, language=self.language_en
        )
        self.assertEquals(len(c), 2)

        # no first/last names
        u1 = User.objects.create(
            username='copycat1', email='copy@cat.org'
        )
        u2 = User.objects.create(
            username='copycat2', email='copy@cat.org'
        )
        save_copyrights(
            None, resource=self.resource_private, language=self.language_en,
            copyrights=[('Copy Cat <copy@cat.org>', ['2011', ]), ]
        )
        c = Copyright.objects.filter(
            resource=self.resource_private, language=self.language_en
        )
        self.assertEquals(len(c), 1)
        self.assertEquals(c[0].user, u2)

