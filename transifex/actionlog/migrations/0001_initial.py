
from south.db import db
from django.db import models
from actionlog.models import *

class Migration:

    def forwards(self, orm):

        # Adding model 'LogEntry'
        db.create_table('actionlog_logentry', (
            ('action_time', models.DateTimeField()),
            ('content_type', models.ForeignKey(orm['contenttypes.ContentType'], related_name="tx_object", null=True, blank=True)),
            ('object_id', models.IntegerField(null=True, blank=True)),
            ('object_name', models.CharField(max_length=200, blank=True)),
            ('user', models.ForeignKey(orm['auth.User'], related_name="tx_user_action", null=True, blank=True)),
            ('action_type', models.ForeignKey(orm['notification.NoticeType'])),
            ('message', models.TextField(null=True, blank=True)),
            ('id', models.AutoField(primary_key=True)),
        ))
        db.send_create_signal('actionlog', ['LogEntry'])



    def backwards(self, orm):

        # Deleting model 'LogEntry'
        db.delete_table('actionlog_logentry')



    models = {
        'auth.user': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label','model'),)", 'db_table': "'django_content_type'"},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'notification.noticetype': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'actionlog.logentry': {
            'Meta': {'ordering': "('-action_time',)"},
            'action_time': ('models.DateTimeField', [], {}),
            'action_type': ('models.ForeignKey', ['NoticeType'], {}),
            'content_type': ('models.ForeignKey', ['ContentType'], {'related_name': '"tx_object"', 'null': 'True', 'blank': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'message': ('models.TextField', [], {'null': 'True', 'blank': 'True'}),
            'object_id': ('models.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'object_name': ('models.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'user': ('models.ForeignKey', ['User'], {'related_name': '"tx_user_action"', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['actionlog']
