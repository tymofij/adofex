# -*- coding: utf-8 -*-
from piston.handler import BaseHandler
from piston.utils import rc
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.txcommon.log import logger
from django.db import transaction
from uuid import uuid4

class LanguageHandler(BaseHandler):
    """
    API call for retrieving languages available on Tx

    [
        {
            'code' : 'cd',
            'code_aliases : ' cd-al1 cd-al2 ... ',
            'name' : Language name'
        },
        ...
    ]
    """
    allowed_methods = ('GET',)
    model = Language
    fields = ('code', 'code_aliases', 'name')
    def read(self, request):
        logger.debug("Returned list of all languages")
        return Language.objects.all()
