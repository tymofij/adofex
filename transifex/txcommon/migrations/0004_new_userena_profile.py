# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Renaming field 'profile.native_language'
        db.rename_column('txcommon_profile', 'native_language_id', 'language_id')

        # Deleting field 'profile.surname'
        db.delete_column('txcommon_profile', 'surname')

        # Deleting field 'profile.firstname'
        db.delete_column('txcommon_profile', 'firstname')

        # Deleting field 'profile.creation_date'
        db.delete_column('txcommon_profile', 'creation_date')

        # Deleting field 'profile.country'
        db.delete_column('txcommon_profile', 'country')

        # Adding field 'Profile.mugshot'
        db.add_column('txcommon_profile', 'mugshot', self.gf('django.db.models.fields.files.ImageField')(default='', max_length=100, blank=True), keep_default=False)

        # Adding field 'Profile.privacy'
        db.add_column('txcommon_profile', 'privacy', self.gf('django.db.models.fields.CharField')(default='open', max_length=15), keep_default=False)

        # Changing field 'Profile.looking_for_work'
        db.alter_column('txcommon_profile', 'looking_for_work', self.gf('django.db.models.fields.BooleanField')())

        # Changing field 'Profile.about'
        db.alter_column('txcommon_profile', 'about', self.gf('django.db.models.fields.TextField')(max_length=140, null=True))

        # Changing field 'Profile.twitter'
        db.alter_column('txcommon_profile', 'twitter', self.gf('django.db.models.fields.URLField')(max_length=200, null=True))

        # Changing field 'Profile.location'
        db.alter_column('txcommon_profile', 'location', self.gf('django.db.models.fields.CharField')(max_length=255, null=True))

        # Changing field 'Profile.linked_in'
        db.alter_column('txcommon_profile', 'linked_in', self.gf('django.db.models.fields.URLField')(max_length=200, null=True))

        # Changing field 'Profile.blog'
        db.alter_column('txcommon_profile', 'blog', self.gf('django.db.models.fields.URLField')(max_length=200, null=True))

        # Changing field 'Profile.user'
        db.alter_column('txcommon_profile', 'user_id', self.gf('django.db.models.fields.related.OneToOneField')(unique=True, to=orm['auth.User']))


    def backwards(self, orm):
        
        # Renaming field 'profile.native_language'
        db.rename_column('txcommon_profile', 'language_id', 'native_language_id')
        
        # Adding field 'profile.surname'
        db.add_column('txcommon_profile', 'surname', self.gf('models.CharField')(_('Surname'), default='', max_length=255, blank=True), keep_default=False)

        # Adding field 'profile.firstname'
        db.add_column('txcommon_profile', 'firstname', self.gf('models.CharField')(_('First name'), default='', max_length=255, blank=True), keep_default=False)

        # Adding field 'profile.creation_date'
        db.add_column('txcommon_profile', 'creation_date', self.gf('models.DateTimeField')(default=datetime.datetime(2009, 7, 30, 13, 13, 50, 293400)), keep_default=False)

        # Adding field 'profile.country'
        db.add_column('txcommon_profile', 'country', self.gf('CountryField')(null=True, blank=True), keep_default=False)

        # Deleting field 'Profile.mugshot'
        db.delete_column('txcommon_profile', 'mugshot')

        # Deleting field 'Profile.privacy'
        db.delete_column('txcommon_profile', 'privacy')

        # Changing field 'Profile.looking_for_work'
        db.alter_column('txcommon_profile', 'looking_for_work', self.gf('models.BooleanField')(_('Looking for work?')))

        # Changing field 'Profile.about'
        db.alter_column('txcommon_profile', 'about', self.gf('models.TextField')(_('About yourself'), default='', max_length=140))

        # Changing field 'Profile.twitter'
        db.alter_column('txcommon_profile', 'twitter', self.gf('models.URLField')(_('Twitter'), default=''))

        # Changing field 'Profile.location'
        db.alter_column('txcommon_profile', 'location', self.gf('models.CharField')(default='', max_length=255))

        # Changing field 'Profile.linked_in'
        db.alter_column('txcommon_profile', 'linked_in', self.gf('models.URLField')(_('LinkedIn'), default=''))

        # Changing field 'Profile.blog'
        db.alter_column('txcommon_profile', 'blog', self.gf('models.URLField')(_('Blog'), default=''))

        # Changing field 'Profile.user'
        db.alter_column('txcommon_profile', 'user_id', self.gf('models.ForeignKey')(User, unique=True))


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'languages.language': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Language', 'db_table': "'translations_language'"},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'code_aliases': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'nplurals': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'pluralequation': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'rule_few': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'rule_many': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'rule_one': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'rule_other': ('django.db.models.fields.CharField', [], {'default': "'everything'", 'max_length': '255'}),
            'rule_two': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'rule_zero': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'specialchars': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'txcommon.profile': {
            'Meta': {'object_name': 'Profile'},
            'about': ('django.db.models.fields.TextField', [], {'max_length': '140', 'null': 'True', 'blank': 'True'}),
            'blog': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['languages.Language']", 'null': 'True', 'blank': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '6', 'blank': 'True'}),
            'linked_in': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '6', 'blank': 'True'}),
            'looking_for_work': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mugshot': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'privacy': ('django.db.models.fields.CharField', [], {'default': "'open'", 'max_length': '15'}),
            'twitter': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['txcommon']
