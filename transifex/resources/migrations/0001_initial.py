# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    depends_on = (
        ("projects", "0001_initial"),
        # ("storage", "0001_initial"),
        ("languages", "0001_initial"),
    )

    def forwards(self, orm):

        # Adding model 'Resource'
        db.create_table('resources_resource', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=50, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('source_file', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['storage.StorageFile'], null=True, blank=True)),
            ('i18n_type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('accept_translations', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_update', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('source_language', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['languages.Language'])),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='resources', null=True, to=orm['projects.Project'])),
            ('_order', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('resources', ['Resource'])

        # Adding unique constraint on 'Resource', fields ['slug', 'project']
        db.create_unique('resources_resource', ['slug', 'project_id'])

        # Adding model 'SourceEntity'
        db.create_table('resources_sourceentity', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('string', self.gf('django.db.models.fields.TextField')()),
            ('string_hash', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('context', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('position', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('occurrences', self.gf('django.db.models.fields.TextField')(max_length=1000, null=True, blank=True)),
            ('flags', self.gf('django.db.models.fields.TextField')(max_length=100, blank=True)),
            ('developer_comment', self.gf('django.db.models.fields.TextField')(max_length=1000, blank=True)),
            ('pluralized', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_update', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('resource', self.gf('django.db.models.fields.related.ForeignKey')(related_name='source_entities', to=orm['resources.Resource'])),
            ('_order', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('resources', ['SourceEntity'])

        # Adding unique constraint on 'SourceEntity', fields ['string_hash', 'context', 'resource']
        db.create_unique('resources_sourceentity', ['string_hash', 'context', 'resource_id'])

        # Adding model 'Translation'
        db.create_table('resources_translation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('string', self.gf('django.db.models.fields.TextField')()),
            ('string_hash', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('rule', self.gf('django.db.models.fields.IntegerField')(default=5)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_update', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('source_entity', self.gf('django.db.models.fields.related.ForeignKey')(related_name='translations', to=orm['resources.SourceEntity'])),
            ('language', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['languages.Language'], null=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True)),
            ('_order', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('resources', ['Translation'])

        # Adding unique constraint on 'Translation', fields ['source_entity', 'language', 'rule']
        db.create_unique('resources_translation', ['source_entity_id', 'language_id', 'rule'])

        # Adding model 'Template'
        db.create_table('resources_template', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('content', self.gf('txcommon.db.models.CompressedTextField')(null=False, blank=False)),
            ('resource', self.gf('django.db.models.fields.related.ForeignKey')(related_name='source_file_template', unique=True, to=orm['resources.Resource'])),
        ))
        db.send_create_signal('resources', ['Template'])


    def backwards(self, orm):

        # Removing unique constraint on 'Translation', fields ['source_entity', 'language', 'rule']
        db.delete_unique('resources_translation', ['source_entity_id', 'language_id', 'rule'])

        # Removing unique constraint on 'SourceEntity', fields ['string_hash', 'context', 'resource']
        db.delete_unique('resources_sourceentity', ['string_hash', 'context', 'resource_id'])

        # Removing unique constraint on 'Resource', fields ['slug', 'project']
        db.delete_unique('resources_resource', ['slug', 'project_id'])

        # Deleting model 'Resource'
        db.delete_table('resources_resource')

        # Deleting model 'SourceEntity'
        db.delete_table('resources_sourceentity')

        # Deleting model 'Translation'
        db.delete_table('resources_translation')

        # Deleting model 'Template'
        db.delete_table('resources_template')


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
            'code_aliases': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'null': 'True'}),
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
        'projects.project': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Project'},
            'anyone_submit': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'bug_tracker': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'feed': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'homepage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_description': ('django.db.models.fields.TextField', [], {'max_length': '1000', 'blank': 'True'}),
            'long_description_html': ('django.db.models.fields.TextField', [], {'max_length': '1000', 'blank': 'True'}),
            'maintainers': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'projects_maintaining'", 'null': 'True', 'to': "orm['auth.User']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'outsource': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']", 'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'}),
            'tags': ('tagging.fields.TagField', [], {})
        },
        'resources.resource': {
            'Meta': {'ordering': "('_order',)", 'unique_together': "(('slug', 'project'),)", 'object_name': 'Resource'},
            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'accept_translations': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'i18n_type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'resources'", 'null': 'True', 'to': "orm['projects.Project']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '50', 'db_index': 'True'}),
            'source_file': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['storage.StorageFile']", 'null': 'True', 'blank': 'True'}),
            'source_language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['languages.Language']"})
        },
        'resources.sourceentity': {
            'Meta': {'ordering': "('_order',)", 'unique_together': "(('string_hash', 'context', 'resource'),)", 'object_name': 'SourceEntity'},
            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'context': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'developer_comment': ('django.db.models.fields.TextField', [], {'max_length': '1000', 'blank': 'True'}),
            'flags': ('django.db.models.fields.TextField', [], {'max_length': '100', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'occurrences': ('django.db.models.fields.TextField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'pluralized': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'position': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'resource': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'source_entities'", 'to': "orm['resources.Resource']"}),
            'string': ('django.db.models.fields.TextField', [], {}),
            'string_hash': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'resources.template': {
            'Meta': {'ordering': "['resource']", 'object_name': 'Template'},
            'content': ('txcommon.db.models.CompressedTextField', [], {'null': 'False', 'blank': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'resource': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'source_file_template'", 'unique': 'True', 'to': "orm['resources.Resource']"})
        },
        'resources.translation': {
            'Meta': {'ordering': "('_order',)", 'unique_together': "(('source_entity', 'language', 'rule'),)", 'object_name': 'Translation'},
            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['languages.Language']", 'null': 'True'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'rule': ('django.db.models.fields.IntegerField', [], {'default': '5'}),
            'source_entity': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'translations'", 'to': "orm['resources.SourceEntity']"}),
            'string': ('django.db.models.fields.TextField', [], {}),
            'string_hash': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'})
        },
        'storage.storagefile': {
            'Meta': {'object_name': 'StorageFile'},
            'bound': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['languages.Language']", 'null': 'True'}),
            'mime_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'size': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'total_strings': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        }
    }

    complete_apps = ['resources']
