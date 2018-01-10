# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'WebHook.kind'
        db.add_column('webhooks_webhook', 'kind', self.gf('django.db.models.fields.CharField')(default='a', max_length=1), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'WebHook.kind'
        db.delete_column('webhooks_webhook', 'kind')


    models = {
        'actionlog.logentry': {
            'Meta': {'ordering': "('-action_time',)", 'object_name': 'LogEntry'},
            'action_time': ('django.db.models.fields.DateTimeField', [], {}),
            'action_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['notification.NoticeType']"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'actionlogs'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'object_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'actionlogs'", 'null': 'True', 'to': "orm['auth.User']"})
        },
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
        'notification.noticetype': {
            'Meta': {'object_name': 'NoticeType'},
            'default': ('django.db.models.fields.IntegerField', [], {}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'display': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '40'})
        },
        'projects.project': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Project'},
            'anyone_submit': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'bug_tracker': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
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
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'projects_owning'", 'null': 'True', 'to': "orm['auth.User']"}),
            'private': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'}),
            'tags': ('tagging_autocomplete.models.TagAutocompleteField', [], {'null': 'True'}),
            'trans_instructions': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        },
        'webhooks.webhook': {
            'Meta': {'object_name': 'WebHook'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'default': "'a'", 'max_length': '1'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'webhook'", 'to': "orm['projects.Project']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['webhooks']
