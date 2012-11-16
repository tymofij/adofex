# -*- coding: utf-8 -*-

import re
from django.db.models import get_model
from django.conf import settings
from transifex.projects.signals import project_created, project_deleted
from transifex.projects.models import Project

def outsource_to_mozilla(sender, **kwargs):
    """
    Outsources translation of the newborn project to general Mozilla project
    """
    try:
        mozilla = Project.objects.get(slug='mozilla')
        sender.outsource = mozilla
        sender.save()
    except Project.DoesNotExist:
        pass

def connect():
    project_created.connect(outsource_to_mozilla)
