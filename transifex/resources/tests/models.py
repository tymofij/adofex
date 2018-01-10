# -*- coding: utf-8 -*-
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.conf import settings
from django.test import TestCase
from django.utils.hashcompat import md5_constructor
from hashlib import md5
from transifex.resources.models import *
from transifex.txcommon.tests.base import BaseTestCase


SAMPLE_STRING = 'Hello'
SAMPLE_STRINGS = ['%s_%s' % (SAMPLE_STRING, i) for i in range(1, 11)]
# TEXT SIZE: 9 paragraphs, 1000 words, 6701 bytes
SAMPLE_BIG_TEXT = ('Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean auctor mattis justo, in feugiat justo ullamcorper a. Etiam dapibus, dolor sagittis varius posuere, metus risus vehicula sem, eget tincidunt neque quam a augue. Lorem ipsum dolor sit amet, consectetur adipiscing elit. In scelerisque dignissim tempus. Pellentesque in orci mi. In quis enim pharetra ipsum euismod aliquam. Donec felis ipsum, sollicitudin id suscipit ut, sagittis quis libero. Cras vitae elit et metus adipiscing aliquet quis sed dui. Morbi in fringilla diam. Sed cursus fermentum posuere. Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus. Nullam metus dui, facilisis eu adipiscing vehicula, hendrerit a mauris. Quisque interdum diam eros. In et urna purus, vel vestibulum eros. Mauris euismod iaculis tincidunt.'

'Mauris quis arcu nibh, eget hendrerit erat. Fusce velit erat, consequat in tempor et, suscipit quis quam. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin justo sapien, semper a auctor eu, vestibulum sit amet felis. Vestibulum consectetur ultricies vestibulum. Suspendisse vestibulum eleifend convallis. Sed ultricies, est a cursus vulputate, sapien odio auctor massa, eget dapibus eros est sed diam. Sed enim odio, viverra ultricies vulputate id, consequat ac felis. Nam malesuada leo nec nisi tristique volutpat.'

'Mauris mollis leo eu mauris sodales a dignissim orci suscipit. Proin laoreet, dolor non fringilla rhoncus, risus nulla hendrerit orci, eu porttitor est nisi et risus. Nulla porta augue nec sem porttitor rutrum imperdiet massa elementum. Donec gravida lobortis ornare. Sed vulputate, elit non condimentum tincidunt, urna eros congue ligula, id iaculis sapien dui sit amet odio. Mauris eget gravida risus. Duis libero libero, tristique vel facilisis sed, dapibus in est. Nulla sit amet tristique eros. Mauris semper suscipit massa mattis dignissim. Curabitur nulla eros, rutrum sed semper a, feugiat condimentum lacus. Aenean aliquam tincidunt tellus sed semper. Phasellus scelerisque risus sit amet sem molestie sit amet adipiscing urna accumsan. Etiam ultricies ligula id ipsum interdum id tempor libero scelerisque. Aenean in elit eget purus malesuada fermentum. Phasellus sollicitudin interdum cursus. Phasellus faucibus consectetur quam, sit amet convallis libero ornare et.'

'Pellentesque quam tellus, malesuada ac posuere vel, bibendum in augue. Vivamus viverra ultricies quam, et tristique nulla gravida eu. Duis at nisi vel mauris posuere scelerisque sed non nunc. Integer sit amet nisi vitae nisi rhoncus ornare. Donec quis felis nisi, ut pulvinar neque. Integer gravida luctus lorem at ultrices. Ut consectetur dui et ante accumsan quis iaculis libero mollis. Aenean nisi diam, mollis ut ullamcorper quis, lobortis eu risus. Proin ultricies pharetra ultrices. Etiam sollicitudin nisl scelerisque justo molestie aliquet non a enim.'

'Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Integer mollis semper nibh, a sodales dui dictum ut. Nunc eu ipsum enim. Morbi varius rutrum consectetur. Aliquam lacus ligula, ornare et faucibus vitae, eleifend a ante. Duis lectus arcu, suscipit in lobortis eu, bibendum quis lacus. Ut sem leo, sollicitudin nec hendrerit accumsan, condimentum ac lorem. Donec facilisis, massa eget facilisis faucibus, lorem nisl pulvinar ligula, ut pretium dolor est id elit. Aenean suscipit fermentum facilisis. Cras eu urna odio, vel blandit est. Integer at leo arcu, sed varius leo. Vestibulum eu sapien libero. Quisque sed nulla sit amet nulla gravida tincidunt. Aliquam erat volutpat. Phasellus non lorem et diam accumsan faucibus vel ac est. Sed eu arcu leo. Etiam ultrices tempor dignissim.'

'Donec tempor lorem eu lectus congue pharetra. Nunc commodo nunc varius quam feugiat tristique. Curabitur a arcu lacus, nec interdum neque. Suspendisse facilisis auctor risus, id consectetur velit porta sed. Ut malesuada, elit non vestibulum imperdiet, ipsum sem facilisis massa, vel molestie odio justo ultrices felis. Sed sed lorem neque. Aenean nec quam quis massa congue feugiat quis in mi. Integer et arcu ipsum. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. Suspendisse facilisis venenatis ipsum, lacinia porta orci imperdiet at. Suspendisse dictum lacus id est bibendum pretium. Aenean in eros vel sem vulputate vehicula. Morbi est nisi, ultricies quis porttitor a, luctus venenatis libero. Donec ac nibh eu elit lacinia auctor. Nullam commodo porta eros, dapibus sodales urna tincidunt vitae. Ut luctus mi eget urna imperdiet sed scelerisque odio volutpat.'

'In euismod faucibus elit, non rutrum velit fermentum vel. Cras sit amet volutpat sem. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Nullam at magna lacus. Phasellus hendrerit accumsan metus, quis ultrices erat placerat sed. Nullam pretium, tellus vel tristique gravida, metus nibh scelerisque arcu, vel vehicula risus tellus non dolor. Cras at diam vitae leo pulvinar rhoncus. Duis consectetur rhoncus nulla, varius commodo metus vehicula sed. Ut suscipit velit eros. Praesent massa nunc, vestibulum ut porttitor sed, fermentum nec sem. Nunc id libero tellus, sed mattis risus. Proin tristique blandit est, interdum rhoncus diam sollicitudin ac. Vivamus interdum dignissim luctus. Nunc vel aliquam enim.'

'Donec non porttitor mi. Praesent in vestibulum turpis. Fusce elit odio, elementum vel tempus at, dictum eleifend nisi. Morbi ac risus diam. Donec a orci est, vel volutpat nunc. Suspendisse accumsan est ut ipsum vehicula id rutrum metus blandit. In vehicula lacinia ante at gravida. Aenean eu dui sapien, vel feugiat tortor. Sed urna arcu, consectetur ut mollis in, ultricies quis lectus. Etiam quis orci ipsum. Vivamus vitae enim vel augue euismod tincidunt nec sed nunc. Morbi condimentum sapien vitae mauris feugiat eu interdum ligula pretium. Curabitur non dolor diam. Maecenas adipiscing aliquam justo, id condimentum dui accumsan vitae. Mauris elementum pharetra erat nec mollis. Duis consectetur, nisi eu ornare pretium, diam risus rhoncus metus, non volutpat velit purus at dolor. Sed nec mi nulla. Curabitur vel dui vel velit cursus pharetra vel vitae eros. Vivamus odio odio, auctor a fermentum eu, tempor vitae massa.'

'Morbi ultricies euismod tellus, a tincidunt lacus luctus vel. Etiam commodo volutpat metus ac consequat. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia Curae; Suspendisse ac cursus dui. Class aptent taciti sociosqu ad litora. ')

class ResourcesModelTests(BaseTestCase):
    """Test the resources models."""

    def setUp(self):
        super(ResourcesModelTests, self).setUp()

    def tearDown(self):
        super(ResourcesModelTests, self).tearDown()

    def test_create_resource(self):
        """Test Resource model creation."""
        r = Resource.objects.create(
            name='Resource Model Test', slug='resource_model_test',
            i18n_type='PO', source_language=self.language_en,
            project=self.project
        )
        self.assertTrue(r)

    def test_rlstats_creation(self):
        """Test the creation of a RLStats for a project team on resource saving."""
        rls = RLStats.objects.get(resource=self.resource,
            language=self.team.language)

        self.assertTrue(rls)

    def test_resource_available_languages(self):
        """Test available languages for a resource with and without teams."""
        self.assertEqual(len(self.resource.available_languages), 3)
        self.assertEqual(len(self.resource.available_languages_without_teams), 2)

    def test_create_source_entity(self):
        """Test SourceEntity model creation."""
        s = SourceEntity.objects.create(string='Source Identifier 1',
                                        context='title',
                                        position=8,
                                        occurrences='/home/user1/test.py:18',
                                        flags='python-format',
                                        developer_comment='This is the title.',
                                        pluralized=False,
                                        resource=self.resource)
        self.assertTrue(s)
        self.assertEqual(s.string_hash, md5_constructor(':'.join([s.string,
            s.context_string]).encode('utf-8')).hexdigest())

    def test_create_translation_string(self):
        """Test TranslationString model creation."""
        t = Translation.objects.create(
            string='Buy me some BEER :)',
            rule=5,
            source_entity=self.source_entity,
            resource=self.resource,
            language=self.language,
            user=self.user['registered']
        )
        self.assertTrue(t)
        self.assertEqual(t.string_hash, md5(t.string.encode('utf-8')).hexdigest())

    def test_utf8_translation_string(self):
        """Test that utf-8 strings are saved correctly.

        WARNING! The 'u' character is important to be identified as unicode!
        """
        t = Translation.objects.create(
            string=u'Αγόρασε μου μια μπύρα :)',
            rule=5,
            source_entity=self.source_entity,
            resource=self.resource,
            language=self.language,
            user=self.user['registered']
        )
        self.assertTrue(t)
        self.assertEqual(t.string_hash, md5(t.string.encode('utf-8')).hexdigest())

    def test_plural_translations(self):
        """Test that plural forms for translations are created correctly."""
        self.source_entity.pluralized = True
        self.source_entity.save()
        t_one = Translation.objects.create(
            string=u'I want one beer :)', rule=1,
            source_entity=self.source_entity, resource=self.resource,
            language=self.language, user=self.user['registered']
        )
        t_other = Translation.objects.create(
            string=u'I want ten beers :)', rule=5,
            source_entity=self.source_entity, resource=self.resource,
            language=self.language, user=self.user['registered']
        )
        self.assertEqual(Translation.objects.filter(
            source_entity=self.source_entity, language=self.language).count(),
            len(self.language.get_pluralrules()))

    def test_translation_size(self):
        """Test that a big translation text is stored in the DB correctly.

        This depends to the corresponding DB engine.
        """
        t = Translation.objects.create(
            string=SAMPLE_BIG_TEXT, rule=5,
            source_entity=self.source_entity, resource=self.resource,
            language=self.language, user=self.user['registered']
        )
        self.assertTrue(t)
        self.assertEqual(t.string_hash,
                         md5(SAMPLE_BIG_TEXT.encode('utf-8')).hexdigest())

    def test_translation_integrity(self):
        """Test translation integrity.

        Translation uniqueness is based on the combination of 'source_entity',
        'language' and 'rule' fields.
        """
        t = Translation.objects.create(
            string="Hello", rule=5,
            source_entity=self.source_entity, resource=self.resource,
            language=self.language, user=self.user['registered']
        )
        t_error = Translation(
            string="Hello2", rule=5,
            source_entity=self.source_entity, resource=self.resource,
            language=self.language, user=self.user['maintainer']
        )
        self.assertRaises(IntegrityError, t_error.save)

    def test_source_entity_integrity(self):
        """Test source_entity integrity.

        SourceEntity uniqueness is based on the combination of 'string_hash',
         'context' and 'resource' fields.
        """
        s = SourceEntity.objects.create(
            string=SAMPLE_STRING, context="menu title", resource=self.resource
        )
        s_error = SourceEntity(
            string=SAMPLE_STRING, context="menu title", resource=self.resource
        )
        self.assertRaises(IntegrityError, s_error.save)


    def test_wordcounts(self):
        """Test word counts in the model."""
        # Manually get the number of words in the English string, just in case
        words_en = len(self.translation_en.string.split(None))

        # Test whether the Translation objects have the same words
        self.assertEquals(self.translation_en.wordcount, words_en)

        # Since this resource only has one translatable string, its wordcount
        # should match its wordcount.
        self.resource.update_wordcount()
        self.assertEquals(self.resource.wordcount,
                          self.translation_en.wordcount)

    def test_slug_validation(self):
        """Test that validation for slug works"""
        slug = "foo"
        r = Resource(slug=slug, name='r', project=self.project,
                source_language=self.language_en, i18n_type='PHP_DEFINE',)
        r.clean_fields()
        r.slug = "a.b.c+"
        self.assertRaises(ValidationError, r.clean_fields)



class RLStatsModelTests(BaseTestCase):
    """Test the resources models."""

    def test_rlstats_queries(self):
        q = RLStats.objects

        self.assertEqual(q.by_project(self.project).count(), 3)
        self.assertEqual(q.public().by_project(self.project).count(), 3)
        self.assertEqual(q.private().by_project(self.project).count(), 0)

        self.assertEqual(q.public().by_project(self.project_private).count(), 0)
        self.assertEqual(q.private().by_project(self.project_private).count(), 1)

        self.assertEqual(q.by_resource(self.resource).count(), 3)

        self.assertEqual(q.for_user(self.user['maintainer']).by_project(self.project).count(), 3)
        self.assertEqual(q.for_user(self.user['maintainer']).count(), 4)
        self.assertEqual(q.for_user(self.user['registered']).count(), 3)
        self.assertEqual(q.for_user(self.user['team_member']).count(), 4)

        self.assertEqual(q.for_user(self.user['registered']).by_project(self.project_private).count(), 0)
        self.assertEqual(q.for_user(self.user['team_member']).by_project(self.project_private).count(), 1)

        self.assertEqual(q.for_user(self.user['maintainer']).by_release(self.release).count(), 3)

        self.assertEqual(len([f for f in q.for_user(self.user['maintainer']).by_project_aggregated(self.project)]), 1)
        self.assertEqual(len([f for f in q.for_user(self.user['registered']).by_project_aggregated(self.project_private)]), 0)


class RLStatsModelWordsTests(BaseTestCase):
    """Test the word support of the RLStats model."""

    def test_source_lang(self):
        rls_en = self.resource.rlstats_set.get(language=self.language_en)
        words_en = len(self.translation_en.string.split(None))
        self.assertEqual(rls_en.translated_wordcount, words_en)

    def test_fully_translated_lang(self):
        # With 1 string translated, Arabic should be 50% translated
        # since we have two source entities
        words_ar = len(self.translation_ar.string.split(None))
        rls_ar = self.resource.rlstats_set.get(language=self.language_ar)
        self.assertEqual(rls_ar.translated_perc, 50)
        # FIXME: This is not implemented yet. All wordcounts are based on
        # source
        #self.assertEqual(rls_ar.untranslated_wordcount, 5)

    def test_partially_translated_lang(self):
        words_ar = len(self.translation_ar.string.split(None))
        # First, create more entities to have a <100% translation effort.
        self.create_more_entities()
        # Translated words should be the same as target language
        # FIXME: This is not implemented yet. All wordcounts are based on
        # source
        rls_ar = self.resource.rlstats_set.get(language=self.language_ar)
        rls_ar.update()
        #self.assertEqual(rls_ar.translated_wordcount, words_ar)

        # The remaining words should be equal to the words of the remaining
        # untranslated English string; in this case it's just the new string
        self.assertEqual(rls_ar.untranslated_wordcount, self.translation_en2.wordcount)

