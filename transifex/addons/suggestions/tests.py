from django.db import IntegrityError
from django.core.urlresolvers import reverse
from django.utils import simplejson as json
from transifex.txcommon.tests.base import BaseTestCase



class SuggestionsViewsTests(BaseTestCase):

    def setUp(self):
        super(SuggestionsViewsTests, self).setUp()
        self.entity = self.resource.entities[0]
        self.URL_PREFIX = '/entities/%s/lang/%s/' % (self.entity.id,
                                                     self.language.code)
    def testAnonymousPagesStatusCode(self):
        #TODO: Why is the following 302 instead of 200?
        pages = {302: [(self.URL_PREFIX + 'snippet'),],
                 #400: [(self.URL_PREFIX + 'create'),
                 #      (self.URL_PREFIX + '1/vote-up/')],
                 404: [(self.URL_PREFIX + '2/vote-up/'),]}
        self.assert_url_statuses(pages, self.client["anonymous"])

    #def testMemberPagesStatusCode(self):
    #    raise NotImplementedError

    def _create_entity_suggestion(self):
        url = reverse('suggestion_create',
            args=[self.entity.id, self.language.code],)
        post_vars = {'suggestion_string': 'Hey!'}
        resp = self.client['team_member'].post(url, data=post_vars)
        self.assertEqual(resp.status_code, 200)
        suggestion = self.entity.suggestions.filter(language=self.language).latest()
        return suggestion

    def test_create_entitysuggestion(self):
        suggestion = self._create_entity_suggestion()
        self.assertTrue(suggestion.string == 'Hey!')

    def test_get_snippet(self):
        # Create a suggestion:
        suggestion = self._create_entity_suggestion()
        url = reverse('tab_suggestions_snippet',
            args=[self.entity.id, self.language.code])
        resp = self.client['anonymous'].get(url)
        self.assertContains(resp, 'Hey!', status_code=200)
        self.assertTemplateUsed(resp, 'tab_suggestions_snippet.html')

    def _vote_up(self, suggestion):
        url = reverse('suggestion_vote_up',
            args=[self.entity.id, self.language.code, suggestion.id],)
        resp = self.client['team_member'].post(url)
        self.assertEqual(resp.status_code, 200)
        return resp

    def _vote_down(self, suggestion):
        url = reverse('suggestion_vote_down',
            args=[self.entity.id, self.language.code, suggestion.id],)
        resp = self.client['team_member'].post(url)
        self.assertEqual(resp.status_code, 200)
        return resp

    def test_votes(self):
        latest_sug = self.entity.suggestions.filter(language=self.language).latest
        self._create_entity_suggestion()
        s = latest_sug()
        self.assertEqual(s.score_rounded, 0)
        self._vote_up(s)
        s = latest_sug()
        self.assertEqual(s.score_rounded, 1)
        self._vote_up(s)
        s = latest_sug()
        self.assertEqual(s.score_rounded, 1)
        self._vote_down(s)
        s = latest_sug()
        self.assertEqual(s.score_rounded, 0)
        self._vote_down(s)
        s = latest_sug()
        self.assertEqual(s.score_rounded, -1)
        self._vote_down(s)
        s = latest_sug()
        self.assertEqual(s.score_rounded, -1)
        self._vote_up(s)
        s = latest_sug()
        self.assertEqual(s.score_rounded, 0)


    #def test_private_project(self):
    #    """Test access to various methods if the project is private."""
    #    raise NotImplementedError



class SuggestionsModelsTests(BaseTestCase):

    def setUp(self):
        super(SuggestionsModelsTests, self).setUp()
        self.entity = self.resource.entities[0]
        self.suggestion = self.entity.suggestions.create(
            language=self.language, string="Hey!", user=self.user["registered"])

    def test_votes(self):
        u = self.user["registered"]
        s = self.suggestion
        self.assertEqual(s.score_rounded, 0)
        s.vote_up(u)
        self.assertEqual(s.score_rounded, 1)
        s.vote_up(u)
        self.assertEqual(s.score_rounded, 1)
        s.vote_down(u)
        self.assertEqual(s.score_rounded, 0)
        s.vote_down(u)
        self.assertEqual(s.score_rounded, -1)
        s.vote_down(u)
        self.assertEqual(s.score_rounded, -1)
        s.vote_up(u)
        self.assertEqual(s.score_rounded, 0)

    def _create_suggestion(self):
        suggestion = self.entity.suggestions.create(
            language=self.language, string="Hey!", user=self.user["registered"])

    def test_double_suggestion(self):
        self.assertRaises(IntegrityError, self._create_suggestion)


