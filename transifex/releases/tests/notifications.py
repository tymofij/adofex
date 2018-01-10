# -*- coding: utf-8 -*-
import os, datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test.client import Client
from transifex.txcommon.tests import base, utils
from transifex.projects.models import Project
from transifex.resources.formats.pofile import POHandler
from transifex.resources.models import Resource
from transifex.releases.handlers import notify_string_freeze, \
    notify_translation_deadline
from transifex.txcommon.utils import key_sort


class ReleaseNotificationTests(base.BaseTestCase):
    """Test notification of events around releases."""

    def _gen_assert_msg(self, msg):
        if settings.TX_ROOT != settings.PROJECT_PATH:
            return msg.lstrip('[localhost] ')
        return msg

    def setUp(self):
        self.current_path = os.path.split(__file__)[0]
        super(ReleaseNotificationTests, self).setUp()
        self.pofile_path = os.path.join(
            settings.TX_ROOT, 'resources/tests/lib/pofile')

        # Brand new objects named with 3 suffix
        # self.project3 outsources its access to self.project and
        # self.resource3 is part of self.release which belongs to self.project
        self.maintainer3 = User.objects.create_user('maintainer3',
            'maintainer3@localhost', 'PASSWORD')
        self.project3 = Project.objects.create(slug="project3",
            name="Project3", owner=self.maintainer3,
            source_language=self.language_en)
        self.project3.maintainers.add(self.maintainer3)
        self.project3.outsource = self.project
        self.project3.save()
        self.resource3 = Resource.objects.create(slug="resource3",
            name="Resource3", project=self.project3, i18n_type='PO',
            source_language=self.language_en)
        self.release.resources.add(self.resource3)

        # Brand new objects named with 4 suffix
        # self.project4 DO NOT outsources its access to self.project and
        # self.resource4 is part of self.release which belongs to self.project
        self.maintainer4 = User.objects.create_user('maintainer4',
            'maintainer4@localhost', 'PASSWORD')
        self.project4 = Project.objects.create(slug="project4",
            name="Project4", owner=self.maintainer4,
            source_language=self.language_en)
        self.project4.maintainers.add(self.maintainer4)
        self.project4.save()
        self.resource4 = Resource.objects.create(slug="resource4",
            name="Resource4", project=self.project4, i18n_type='PO',
            source_language=self.language_en)
        self.release.resources.add(self.resource4)


    def test_before_string_freeze_notifications(self):
        """
        Check whether notifications are sent to the correct people whenever
        the string freeze period approaches.
        """
        timestamp = datetime.datetime.now() + datetime.timedelta(hours=47)
        self.release.stringfreeze_date = timestamp
        self.release.save()

        notify_string_freeze()

        # Sorted mails list
        mails = key_sort(mail.outbox, 'to')

        self.assertEqual(len(mails), 2)
        self.assertEqual(mails[0].subject, self._gen_assert_msg(
            '[localhost] Release about to '
            'enter the string freeze period: Release1'))

        self.assertEqual(mails[0].to, ['maintainer3@localhost'])
        self.assertEqual(mails[1].to, ['maintainer@localhost'])


    def test_in_string_freeze_notifications(self):
        """
        Check whether notifications are sent to the correct people whenever
        the string freeze period starts.
        """
        timestamp = datetime.datetime.now() - datetime.timedelta(hours=1)
        self.release.stringfreeze_date = timestamp
        self.release.notifications.before_stringfreeze = True
        self.release.notifications.save()
        self.release.save()

        notify_string_freeze()

        # Sorted mails list
        mails = key_sort(mail.outbox, 'to')

        self.assertEqual(len(mails), 5)
        self.assertEqual(mails[0].subject, self._gen_assert_msg(
            '[localhost] Release is in string '
            'freeze period: Release1'))

        self.assertEqual(mails[0].to, ['maintainer3@localhost'])
        self.assertEqual(mails[1].to, ['maintainer@localhost'])
        self.assertEqual(mails[2].to, ['reviewer@localhost'])
        self.assertEqual(mails[3].to, ['team_coordinator@localhost'])
        self.assertEqual(mails[4].to, ['team_member@localhost'])


    def test_before_trans_deadline_notifications(self):
        """
        Check whether notifications are sent to the correct people whenever a
        the translation deadline approaches.
        """
        timestamp = datetime.datetime.now() + datetime.timedelta(hours=47)
        self.release.develfreeze_date = timestamp
        self.release.save()

        notify_translation_deadline()

        # Sorted mails list
        mails = key_sort(mail.outbox, 'to')

        self.assertEqual(len(mails), 3)
        self.assertEqual(mails[0].subject, self._gen_assert_msg(
            '[localhost] Release about '
            'to hit the translation deadline: Release1'))

        self.assertEqual(mails[0].to, ['reviewer@localhost'])
        self.assertEqual(mails[1].to, ['team_coordinator@localhost'])
        self.assertEqual(mails[2].to, ['team_member@localhost'])


    def test_hit_trans_deadline_notifications(self):
        """
        Check whether notifications are sent to the correct people whenever a
        translation period is over.
        """
        timestamp = datetime.datetime.now() - datetime.timedelta(hours=1)
        self.release.develfreeze_date = timestamp
        self.release.notifications.before_trans_deadline = True
        self.release.notifications.save()
        self.release.save()

        notify_translation_deadline()

        # Sorted mails list
        mails = key_sort(mail.outbox, 'to')

        self.assertEqual(len(mails), 5)
        self.assertEqual(mails[0].subject, self._gen_assert_msg(
            '[localhost] Release has '
            'hit the translation deadline: Release1'))

        self.assertEqual(mails[0].to, ['maintainer3@localhost'])
        self.assertEqual(mails[1].to, ['maintainer@localhost'])
        self.assertEqual(mails[2].to, ['reviewer@localhost'])
        self.assertEqual(mails[3].to, ['team_coordinator@localhost'])
        self.assertEqual(mails[4].to, ['team_member@localhost'])


    def test_string_freeze_breakage_outsourced(self):
        """Check string breakage for outsourced projects."""

        timestamp = datetime.datetime.now() - datetime.timedelta(hours=1)
        timestamp2 = datetime.datetime.now() + datetime.timedelta(hours=1)
        self.release.stringfreeze_date = timestamp
        self.release.develfreeze_date = timestamp2
        self.release.save()

        ## Loading POT (en_US) into the self.resource3
        handler = POHandler('%s/tests.pot' % self.pofile_path)
        handler.set_language(self.language_en)
        handler.parse_file(is_source=True)
        # Resource 3 - Outsourced
        handler.bind_resource(self.resource3)
        # We are listing to the post_save_translation signal raised in
        # _post_save2db method.
        handler.save2db(is_source=True)

        # Sorted mails list
        mails = key_sort(mail.outbox, 'to')

        self.assertEqual(len(mails), 3)
        self.assertEqual(mails[0].subject, self._gen_assert_msg(
            '[localhost] Release string '
            'freeze breakage: Release1'))

        self.assertEqual(mails[0].to, ['maintainer3@localhost'])
        self.assertEqual(mails[1].to, ['maintainer@localhost'])
        self.assertEqual(mails[2].to, ['team_coordinator@localhost'])


    def test_string_freeze_breakage(self):
        """Check string breakage for non-outsourced projects."""

        timestamp = datetime.datetime.now() - datetime.timedelta(hours=1)
        timestamp2 = datetime.datetime.now() + datetime.timedelta(hours=1)
        self.release.stringfreeze_date = timestamp
        self.release.develfreeze_date = timestamp2
        self.release.save()

        ## Loading POT (en_US) into the self.resource4
        handler = POHandler('%s/tests.pot' % self.pofile_path)
        handler.set_language(self.language_en)
        handler.parse_file(is_source=True)
        # Resource 4 - Not outsourced
        handler.bind_resource(self.resource4)
        # We are listing to the post_save_translation signal raised in
        # _post_save2db method.
        handler.save2db(is_source=True)

        # Should not send any notification once the project do not outsources
        # its teams
        self.assertEqual(len(mail.outbox), 0)
