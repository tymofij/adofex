# -*- coding: utf-8 -*-

from south.db import db
from django.db import models
from transifex.txcommon.models import *
from userprofile.countries import CountryField

class Migration:

    depends_on = (
        ("languages", "0001_initial"),
    )

    def forwards(self, orm):

        # Adding model 'Profile'
        db.create_table('txcommon_profile', (
            ('looking_for_work', models.BooleanField(_('Looking for work?'), default=False)),
            ('about', models.TextField(_('About yourself'), max_length=140, blank=True)),
            ('surname', models.CharField(_('Surname'), max_length=255, blank=True)),
            ('firstname', models.CharField(_('First name'), max_length=255, blank=True)),
            ('country', CountryField(null=True, blank=True)),
            ('twitter', models.URLField(_('Twitter'), blank=True)),
            ('native_language', models.ForeignKey(orm['languages.Language'], null=True, verbose_name=_('Native Language'), blank=True)),
            ('longitude', models.DecimalField(null=True, max_digits=10, decimal_places=6, blank=True)),
            ('creation_date', models.DateTimeField(default=datetime.datetime(2009, 7, 30, 13, 13, 50, 217271))),
            ('blog', models.URLField(_('Blog'), blank=True)),
            ('user', models.ForeignKey(orm['auth.User'], unique=True)),
            ('latitude', models.DecimalField(null=True, max_digits=10, decimal_places=6, blank=True)),
            ('linked_in', models.URLField(_('LinkedIn'), blank=True)),
            ('id', models.AutoField(primary_key=True)),
            ('location', models.CharField(max_length=255, blank=True)),
        ))
        db.send_create_signal('txcommon', ['Profile'])



    def backwards(self, orm):

        # Deleting model 'Profile'
        db.delete_table('txcommon_profile')



    models = {
        'auth.user': {
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'languages.language': {
            'Meta': {'ordering': "('name',)", 'db_table': "'translations_language'"},
            '_stub': True,
            'id': ('models.AutoField', [], {'primary_key': 'True'})
        },
        'txcommon.profile': {
            'about': ('models.TextField', ["_('About yourself')"], {'max_length': '140', 'blank': 'True'}),
            'blog': ('models.URLField', ["_('Blog')"], {'blank': 'True'}),
            'country': ('CountryField', [], {'null': 'True', 'blank': 'True'}),
            'creation_date': ('models.DateTimeField', [], {'default': 'datetime.datetime(2009, 7, 30, 13, 13, 50, 293400)'}),
            'firstname': ('models.CharField', ["_('First name')"], {'max_length': '255', 'blank': 'True'}),
            'id': ('models.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('models.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '6', 'blank': 'True'}),
            'linked_in': ('models.URLField', ["_('LinkedIn')"], {'blank': 'True'}),
            'location': ('models.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'longitude': ('models.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '6', 'blank': 'True'}),
            'looking_for_work': ('models.BooleanField', ["_('Looking for work?')"], {'default': 'False'}),
            'native_language': ('models.ForeignKey', ['Language'], {'null': 'True', 'verbose_name': "_('Native Language')", 'blank': 'True'}),
            'surname': ('models.CharField', ["_('Surname')"], {'max_length': '255', 'blank': 'True'}),
            'twitter': ('models.URLField', ["_('Twitter')"], {'blank': 'True'}),
            'user': ('models.ForeignKey', ['User'], {'unique': 'True'})
        }
    }

    complete_apps = ['txcommon']
