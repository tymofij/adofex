# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        """Remove extra space from zh_TW.Big5 code."""
        try:
            zw_tw_big5 = orm['languages.Language'].objects.get(code='zh_TW.Big5 ')
            zw_tw_big5.code = 'zh_TW.Big5'
            zw_tw_big5.save()
        except orm['languages.Language'].DoesNotExist:
            pass


    def backwards(self, orm):
        """Add the extra space to zh_TW.Big5 code."""
        try:
            zw_tw_big5 = orm['languages.Language'].objects.get(code='zh_TW.Big5')
            zw_tw_big5.code = 'zh_TW.Big5 '
            zw_tw_big5.save()
        except orm['languages.Language'].DoesNotExist:
            pass


    models = {
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
        }
    }

    complete_apps = ['languages']
