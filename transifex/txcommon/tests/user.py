# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from transifex.txcommon.tests.base import BaseTestCase
from transifex.txcommon.user import get_username


class TestSocialAuth(BaseTestCase):
    """Test the social auth custom steps."""

    def test_case_insensitivity_in_username_generation(self):
        """Test that we case-insensitively search for exisitng usernames."""
        User.objects.create(username='me')
        username = get_username({'username': 'Me'}, None)
        self.assertNotEqual(username, 'Me')

