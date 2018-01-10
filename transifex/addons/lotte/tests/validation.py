# -*- coding: utf-8 -*-

from django.core.urlresolvers import reverse
from django.test import TransactionTestCase
from transifex.txcommon.tests.base import SampleData
from transifex.resources.models import Translation

try:
    import json
except ImportError:
    import simplejson as json


class LotteValidationTest(SampleData, TransactionTestCase):

    def test_push_translation_strings(self):
        """Test the push translation view warnings and errors"""

        cases = {
            200: {
                # 'source': ('trans', 'message')
                'foo': [ ('foo', ''),
                    ('     ', 'Translation string only contains whitespaces'),
                    ('foo(', 'Translation string doesn\'t contain the same number'),
                    ('foo)', 'Translation string doesn\'t contain the same number'),
                    ('foo{', 'Translation string doesn\'t contain the same number'),
                    ('foo}', 'Translation string doesn\'t contain the same number'),
                    ('foo[', 'Translation string doesn\'t contain the same number'),
                    ('foo]', 'Translation string doesn\'t contain the same number')],
                'foo\n': [ ('foo\n', ''), ],
                'foo 123': [
                    ('foo123', ''),
                    ('foo', 'Number 123 is in the source string but not')],
                'This is a url http://goatse.cx/': [
                    ('This is a url http://goatse.cx/', ''),
                    ('This is a url http://http://lemonparty.org/', 'The following url is either missing from the')],
                'This is an email email@example.com': [
                    ('This is an email email@example.com', ''),
                    ('This is an email email2@example.com', 'The following email is either missing from the')],
                'This is an email email@example.com': [
                    ('This is an email email@example.com', ''),
                    ('This is an email email2@example.com', 'The following email is either missing from the')],
                '%(count)s animals were hurt for this unit test': [
                    ('%(count)s animals were hurt for this unit test', '')],
            },
            400: {
                'foo': [
                    ('foo\n', 'Translation should not end with a newline'),
                    ('\nfoo', 'Translation should not start with a newline'),
                ],
                'foo\n': [
                    ('foo','Translation must end with a newline'),
                    ('\nfoo', 'Translation should not start with a newline')
                ],
                '%(count)s animals were hurt for this unit test': [
                    ('No animals were hurt for this unit test', 'The number of arguments seems to differ'),
                    ('%(count)s animals were hurt for this unit test by %(ppl)s people',
                     'The number of arguments seems to differ')]
            }
        }

        source_translation = self.source_entity.get_translation(self.language_en.code)

        for code in cases.keys():
            for source in cases[code].keys():
                for item in cases[code][source]:
                    translation, message = item
                    source_translation.string = source
                    source_translation.save()
                    resp = self.client['maintainer'].post(reverse('push_translation',
                        args=[self.project.slug, self.language.code]),
                        json.dumps({'strings':[{'id':source_translation.id,
                            'translations':{'other':translation}}]}),
                        content_type='application/json')
                    if message:
                        self.assertTrue(message in resp.content)
                    self.assertEqual(resp.status_code, 200)
                    self.assertEqual(Translation.objects.filter(source_entity__resource=self.resource,
                        language = self.language, string=translation).count(),
                        1 if code == 200 else 0,
                        "Check failed for translation '%s' against source '%s'" % (
                        translation, source))

                    # Update existing translation
                    resp = self.client['maintainer'].post(reverse('push_translation',
                        args=[self.project.slug, self.language.code]),
                        json.dumps({'strings':[{'id': source_translation.id,
                            'translations':{'other':translation}}]}),
                        content_type='application/json')
                    self.assertEqual(resp.status_code, 200)
                    translations = Translation.objects.filter(
                        source_entity__resource=self.resource,
                        language = self.language, string=translation)
                    self.assertEqual(translations.count(),
                        1 if code == 200 else 0,
                        "Check failed for translation '%s' against source '%s'" % (
                        translation, source))

    def test_push_translation_plural_strings(self):
        """Test the push translation view warnings and errors"""

        cases = {
            200: [{
                # 'source': ('trans', 'message')
                    'one': 'foo1',
                    'other': 'foo5',
                    'message': '',
                    'translations': {
                        'one': 'foo1',
                        'other': 'foo5',},
                }, {
                    'one': 'foo1',
                    'other': 'foo5\n',
                    'message': '',
                    'translations': {
                        'one': 'foo1',
                        'other': 'foo5\n',},
                }, {
                    'one': 'foo1\n',
                    'other': 'foo5',
                    'message': '',
                    'translations': {
                        'one': 'foo1\n',
                        'other': 'foo5',},
                }, {
                    'one': 'foo(',
                    'other': 'foo5',
                    'message': 'Translation string doesn\'t contain the same',
                    'translations': {
                        'one': 'foo',
                        'other': 'foo5)',},
                }, {
                    'one': 'foo{',
                    'other': 'foo5',
                    'message': 'Translation string doesn\'t contain the same',
                    'translations': {
                        'one': 'foo{}',
                        'other': 'foo5',},
                }, {
                    'one': 'foo[',
                    'other': 'foo5]',
                    'message': 'Translation string doesn\'t contain the same',
                    'translations': {
                        'one': 'foo[',
                        'other': 'foo5[]',},
                }, {
                    'one': 'email me@example.com',
                    'other': 'no email',
                    'message': '',
                    'translations': {
                        'one': 'email me@example.com',
                        'other': 'no email',},
                }, {
                    'one': 'email me@example.com',
                    'other': 'no email',
                    'message': 'The following email is either missing from the',
                    'translations': {
                        'one': 'no email',
                        'other': 'email me@example.com',},
                }, {
                    'one': 'url http://goatse.cx',
                    'other': 'no url',
                    'message': '',
                    'translations': {
                        'one': 'url http://goatse.cx',
                        'other': 'no url',},
                }, {
                    'one': 'url http://goatse.cx',
                    'other': 'no url',
                    'message': 'The following url is either missing from the',
                    'translations': {
                        'one': 'no url',
                        'other': 'url http://goatse.cx',},
                }, {
                    'one': 'foo1',
                    'other': 'foo5',
                    'message': 'Number 5 is in the source string but not',
                    'translations': {
                        'one': 'foo1',
                        'other': 'foo',},
                }, {
                    'one': 'foo1',
                    'other': 'foo5',
                    'message': 'Number 1 is in the source string but not',
                    'translations': {
                        'one': 'foo',
                        'other': 'foo5',},
                }, {
                    'one': '1 animal was hurt for this unit test',
                    'other': '%(count)s animals were hurt for this unit test',
                    'message': '',
                    'translations': {
                        'one': '1 animals was hurt for this unit test',
                        'other': '%(count)s animals were hurt for this unit test',},
                }, {
                    'one': '%(count)s animals were hurt for this unit test',
                    'other': '%(count)s animals were hurt for this unit test',
                    'message': '',
                    'translations': {
                        'one': '%(count)s animals were hurt for this unit test',
                        'other': '%(count)s animals were hurt for this unit test',},
                }, {
                    'one': 'foo1\n',
                    'other': 'foo5\n',
                    'message': '',
                    'translations': {
                        'one': 'foo1\n',
                        'other': 'foo5\n',},
                }],
            400: [{
                    'one': '1 animal was hurt for this unit test',
                    'other': '%(count)s animals were hurt for this unit test',
                    'message': 'The number of arguments seems to differ',
                    'translations': {
                        'one': '1 animals was hurt for this unit test',
                        'other': 'A lot of animals were hurt for this unit test',},
                }, {
                    'one': '1 animal was hurt for this unit test',
                    'other': '%(count)s animals were hurt for this unit test',
                    'message': 'The number of arguments seems to differ',
                    'translations': {
                        'one': '%(count) animals was hurt for this unit test',
                        'other': '%(count) animals were hurt for this unit test',},
                }, {
                    'one': 'efoo1\n',
                    'other': 'efoo5',
                    'message': 'Translation must end with a newline',
                    'translations': {
                        'one': 'efoo1',
                        'other': 'efoo5',},
                }, {
                    'one': 'efoo1',
                    'other': 'efoo5',
                    'message': 'Translation should not end with a newline',
                    'translations': {
                        'one': 'efoo1\n',
                        'other': 'efoo5',},
                }, {
                    'one': 'efoo1',
                    'other': 'efoo5',
                    'message': 'Cannot save unless plural translations are either',
                    'translations': {
                        'one': '',
                        'other': 'efoo5',},
                }, {
                    'one': 'efoo1',
                    'other': 'efoo5',
                    'message': 'Cannot save unless plural translations are either',
                    'translations': {
                        'one': 'efoo1',
                        'other': '',},
                }]
        }


        source_translation_1 = self.source_entity_plural.get_translation(self.language_en.code,
            rule=1)
        if not source_translation_1:
            self.source_entity_plural.translations.create(
                string='default',
                rule=1,
                source_entity=self.source_entity_plural,
                language=self.language_en,
                user=self.user['registered'],
                resource=self.resource
            )
            source_translation_1 = self.source_entity_plural.get_translation(self.language_en.code,
                rule=1)

        source_translation_5 = self.source_entity_plural.get_translation(self.language_en.code,
            rule=5)
        if not source_translation_5:
            self.source_entity_plural.translations.create(
                string='default',
                rule=5,
                source_entity=self.source_entity_plural,
                language=self.language_en,
                user=self.user['registered'],
                resource=self.resource
            )
            source_translation_5 = self.source_entity_plural.get_translation(self.language_en.code,
                rule=5)

        for code in cases.keys():
            for item in cases[code]:
                source_1 = item['one']
                source_5 = item['other']
                message = item['message']
                trans_1 = item['translations']['one']
                trans_5 = item['translations']['other']
                source_translation_1.string = source_1
                source_translation_1.save()
                source_translation_5.string = source_5
                source_translation_5.save()
                resp = self.client['maintainer'].post(reverse('push_translation',
                    args=[self.project.slug, self.language.code]),
                    json.dumps({'strings':[{'id':source_translation_5.id,
                        'translations':{'other':trans_5, 'one':trans_1}}]}),
                    content_type='application/json')
                if message:
                    self.assertTrue(message in resp.content, "Message '%s'"\
                        " couldn't be found in the response." % message)
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(Translation.objects.filter(source_entity__resource=self.resource,
                    language = self.language, string=trans_5,rule=5).count(),
                    1 if code == 200 else 0)
                self.assertEqual(Translation.objects.filter(source_entity__resource=self.resource,
                    language = self.language, string=trans_1,rule=1).count(),
                    1 if code == 200 else 0)

                    # Update existing translation
                resp = self.client['maintainer'].post(reverse('push_translation',
                    args=[self.project.slug, self.language.code]),
                    json.dumps({'strings':[{'id':source_translation_5.id,
                        'translations':{'other':trans_5, 'one':trans_1}}]}),
                    content_type='application/json')
                if message:
                    self.assertTrue(message in resp.content, "Message '%s'"\
                        " couldn't be found in the response." % message)
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(Translation.objects.filter(source_entity__resource=self.resource,
                    language = self.language, string=trans_5,rule=5).count(),
                    1 if code == 200 else 0)
                self.assertEqual(Translation.objects.filter(source_entity__resource=self.resource,
                    language = self.language, string=trans_1,rule=1).count(),
                    1 if code == 200 else 0)
