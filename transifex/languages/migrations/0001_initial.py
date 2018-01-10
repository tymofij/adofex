
from south.db import db
from django.db import models
from transifex.languages.models import Language

class Migration:

    def forwards(self, orm):

        # Adding model 'Language'
        db.create_table('translations_language', (
            ('code_aliases', models.CharField(_('Code aliases'), default='', max_length=100, null=True)),
            ('code', models.CharField(_('Code'), max_length=50, unique=True)),
            ('description', models.CharField(_('Description'), max_length=255, blank=True)),
            ('pluralequation', models.CharField(_("Plural Equation"), max_length=255, blank=True)),
            ('nplurals', models.SmallIntegerField(_("Number of Plurals"), default=0)),
            ('specialchars', models.CharField(_("Special Chars"), max_length=255, blank=True)),
            ('id', models.AutoField(primary_key=True)),
            ('name', models.CharField(_('Name'), max_length=50, unique=True)),
        ))
        db.send_create_signal('languages', ['Language'])



    def backwards(self, orm):

        # Deleting model 'Language'
        db.delete_table('translations_language')



    models = {
        'languages.language': {
            'Meta': {'ordering': "('name',)", 'db_table': "'translations_language'"},
            'code': ('models.CharField', ["_('Code')"], {'max_length': '50', 'unique': 'True'}),
            'code_aliases': ('models.CharField', ["_('Code aliases')"], {'default': "''", 'max_length': '100', 'null': 'True'}),
            'description': ('models.CharField', ["_('Description')"], {'max_length': '255', 'blank': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'name': ('models.CharField', ["_('Name')"], {'max_length': '50', 'unique': 'True'}),
            'nplurals': ('models.SmallIntegerField', ['_("Number of Plurals")'], {'default': '0'}),
            'pluralequation': ('models.CharField', ['_("Plural Equation")'], {'max_length': '255', 'blank': 'True'}),
            'specialchars': ('models.CharField', ['_("Special Chars")'], {'max_length': '255', 'blank': 'True'})
        }
    }

    complete_apps = ['languages']
