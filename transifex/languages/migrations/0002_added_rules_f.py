# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    depends_on = (
        ("languages", "0001_initial"),
    )

    def forwards(self, orm):

        # Adding field 'Language.rule_zero'
        db.add_column('translations_language', 'rule_zero', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Adding field 'Language.rule_one'
        db.add_column('translations_language', 'rule_one', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Adding field 'Language.rule_two'
        db.add_column('translations_language', 'rule_two', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Adding field 'Language.rule_few'
        db.add_column('translations_language', 'rule_few', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Adding field 'Language.rule_many'
        db.add_column('translations_language', 'rule_many', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True), keep_default=False)

        # Adding field 'Language.rule_other'
        db.add_column('translations_language', 'rule_other', self.gf('django.db.models.fields.CharField')(default='everything', max_length=255), keep_default=False)

        # Changing field 'Language.code_aliases'
        db.alter_column('translations_language', 'code_aliases', self.gf('django.db.models.fields.CharField')(max_length=100, null=True))

        # Changing field 'Language.code'
        db.alter_column('translations_language', 'code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50))

        # Changing field 'Language.description'
        db.alter_column('translations_language', 'description', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True))

        # Changing field 'Language.pluralequation'
        db.alter_column('translations_language', 'pluralequation', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True))

        # Changing field 'Language.nplurals'
        db.alter_column('translations_language', 'nplurals', self.gf('django.db.models.fields.SmallIntegerField')())

        # Changing field 'Language.specialchars'
        db.alter_column('translations_language', 'specialchars', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True))

        # Changing field 'Language.name'
        db.alter_column('translations_language', 'name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50))


    def backwards(self, orm):

        # Deleting field 'Language.rule_zero'
        db.delete_column('translations_language', 'rule_zero')

        # Deleting field 'Language.rule_one'
        db.delete_column('translations_language', 'rule_one')

        # Deleting field 'Language.rule_two'
        db.delete_column('translations_language', 'rule_two')

        # Deleting field 'Language.rule_few'
        db.delete_column('translations_language', 'rule_few')

        # Deleting field 'Language.rule_many'
        db.delete_column('translations_language', 'rule_many')

        # Deleting field 'Language.rule_other'
        db.delete_column('translations_language', 'rule_other')

        # Changing field 'Language.code_aliases'
        db.alter_column('translations_language', 'code_aliases', self.gf('models.CharField')(_('Code aliases'), max_length=100, null=True))

        # Changing field 'Language.code'
        db.alter_column('translations_language', 'code', self.gf('models.CharField')(_('Code'), unique=True, max_length=50))

        # Changing field 'Language.description'
        db.alter_column('translations_language', 'description', self.gf('models.CharField')(_('Description'), max_length=255, blank=True))

        # Changing field 'Language.pluralequation'
        db.alter_column('translations_language', 'pluralequation', self.gf('models.CharField')(_("Plural Equation"), max_length=255, blank=True))

        # Changing field 'Language.nplurals'
        db.alter_column('translations_language', 'nplurals', self.gf('models.SmallIntegerField')(_("Number of Plurals")))

        # Changing field 'Language.specialchars'
        db.alter_column('translations_language', 'specialchars', self.gf('models.CharField')(_("Special Chars"), max_length=255, blank=True))

        # Changing field 'Language.name'
        db.alter_column('translations_language', 'name', self.gf('models.CharField')(_('Name'), unique=True, max_length=50))


    models = {
        'languages.language': {
            'Meta': {'object_name': 'Language', 'db_table': "'translations_language'"},
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
        }
    }

    complete_apps = ['languages']
