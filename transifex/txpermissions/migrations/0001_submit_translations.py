# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from authority.models import Permission

class Migration(DataMigration):

    def forwards(self, orm):
        """
        Rename permission with the ``project_perm.submit_file`` codename into
        ``project_perm.submit_translations``.
        """
        Permission.objects.filter(codename="project_perm.submit_file"
            ).update(codename="project_perm.submit_translations")

    def backwards(self, orm):
        """
        Rename permission with the ``project_perm.submit_translations`` back
        into ``project_perm.submit_file`` codename.
        """
        Permission.objects.filter(codename="project_perm.submit_translations"
            ).update(codename="project_perm.submit_file")

    models = {}

    complete_apps = ['txpermissions']
