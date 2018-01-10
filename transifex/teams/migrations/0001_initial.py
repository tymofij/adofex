
from south.db import db
from django.db import models
from transifex.teams.models import *

class Migration:

    def forwards(self, orm):

        # Adding model 'Team'
        db.create_table('teams_team', (
            ('id', orm['teams.Team:id']),
            ('project', orm['teams.Team:project']),
            ('language', orm['teams.Team:language']),
            ('mainlist', orm['teams.Team:mainlist']),
            ('creator', orm['teams.Team:creator']),
            ('created', orm['teams.Team:created']),
            ('modified', orm['teams.Team:modified']),
        ))
        db.send_create_signal('teams', ['Team'])

        # Adding model 'TeamRequest'
        db.create_table('teams_teamrequest', (
            ('id', orm['teams.TeamRequest:id']),
            ('project', orm['teams.TeamRequest:project']),
            ('language', orm['teams.TeamRequest:language']),
            ('user', orm['teams.TeamRequest:user']),
            ('created', orm['teams.TeamRequest:created']),
        ))
        db.send_create_signal('teams', ['TeamRequest'])

        # Adding model 'TeamAccessRequest'
        db.create_table('teams_teamaccessrequest', (
            ('id', orm['teams.TeamAccessRequest:id']),
            ('team', orm['teams.TeamAccessRequest:team']),
            ('user', orm['teams.TeamAccessRequest:user']),
            ('created', orm['teams.TeamAccessRequest:created']),
        ))
        db.send_create_signal('teams', ['TeamAccessRequest'])

        # Adding ManyToManyField 'Team.members'
        db.create_table('teams_team_members', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('team', models.ForeignKey(orm.Team, null=False)),
            ('user', models.ForeignKey(orm['auth.User'], null=False))
        ))

        # Adding ManyToManyField 'Team.coordinators'
        db.create_table('teams_team_coordinators', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('team', models.ForeignKey(orm.Team, null=False)),
            ('user', models.ForeignKey(orm['auth.User'], null=False))
        ))

        # Creating unique_together for [team, user] on TeamAccessRequest.
        db.create_unique('teams_teamaccessrequest', ['team_id', 'user_id'])

        # Creating unique_together for [project, language] on TeamRequest.
        db.create_unique('teams_teamrequest', ['project_id', 'language_id'])

        # Creating unique_together for [project, language] on Team.
        db.create_unique('teams_team', ['project_id', 'language_id'])



    def backwards(self, orm):

        # Deleting unique_together for [project, language] on Team.
        db.delete_unique('teams_team', ['project_id', 'language_id'])

        # Deleting unique_together for [project, language] on TeamRequest.
        db.delete_unique('teams_teamrequest', ['project_id', 'language_id'])

        # Deleting unique_together for [team, user] on TeamAccessRequest.
        db.delete_unique('teams_teamaccessrequest', ['team_id', 'user_id'])

        # Deleting model 'Team'
        db.delete_table('teams_team')

        # Deleting model 'TeamRequest'
        db.delete_table('teams_teamrequest')

        # Deleting model 'TeamAccessRequest'
        db.delete_table('teams_teamaccessrequest')

        # Dropping ManyToManyField 'Team.members'
        db.delete_table('teams_team_members')

        # Dropping ManyToManyField 'Team.coordinators'
        db.delete_table('teams_team_coordinators')



    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'languages.language': {
            'Meta': {'db_table': "'translations_language'"},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'code_aliases': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100', 'null': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'nplurals': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'pluralequation': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'specialchars': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'projects.project': {
            'anyone_submit': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'bug_tracker': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'feed': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'homepage': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_description': ('django.db.models.fields.TextField', [], {'max_length': '1000', 'blank': 'True'}),
            'long_description_html': ('django.db.models.fields.TextField', [], {'max_length': '1000', 'blank': 'True'}),
            'maintainers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'}),
            'tags': ('tagging.fields.TagField', [], {})
        },
        'teams.team': {
            'Meta': {'unique_together': "(('project', 'language'),)"},
            'coordinators': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['languages.Language']"}),
            'mainlist': ('django.db.models.fields.EmailField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']"})
        },
        'teams.teamaccessrequest': {
            'Meta': {'unique_together': "(('team', 'user'),)"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['teams.Team']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'teams.teamrequest': {
            'Meta': {'unique_together': "(('project', 'language'),)"},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['languages.Language']"}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['projects.Project']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['teams']
