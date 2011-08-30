from datetime import date, datetime

from django.db import models

from transifex.projects.models import Project
from django.contrib.auth.models import User

class XpiFile(models.Model):
    """
    File residing in filesystem that was uploaded by user
    """
    project = models.OneToOneField(Project)
    filename = models.CharField(blank=False, null=False, max_length=200)
    added_date = models.DateTimeField(null=False, default=datetime.now)
    user = models.ForeignKey(User, blank=True, null=True)
