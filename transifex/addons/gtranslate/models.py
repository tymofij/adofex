# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _
from transifex.projects.models import Project
import requests

class Gtranslate(models.Model):
    """
    Control integration with Google Translate and other machine
    translation services.
    """

    available_services = (
        ('', '-' * 20),
        ('GT', 'Google Translate'),
        ('BT', 'Bing Translator'),
    )

    service_language_urls = {
        'GT': 'https://www.googleapis.com/language/translate/v2/languages',
        'BT': 'http://api.microsofttranslator.com/V2/Ajax.svc/GetLanguagesForTranslate'
    }

    service_translate_urls = {
        'GT': 'https://www.googleapis.com/language/translate/v2',
        'BT': 'http://api.microsofttranslator.com/V2/Ajax.svc/TranslateArray'
    }

    api_key = models.CharField(
        max_length=255, verbose_name=_("API key"), blank=True,
        help_text=_("The API key for the auto-translate service.")
    )

    service_type = models.CharField(
        max_length=2, verbose_name=_("Service"),
        choices=available_services, blank=True,
        help_text=_("The service you want to use for auto-translation.")
    )

    project = models.OneToOneField(
        Project, unique=True,
        verbose_name=_("Project"),
        help_text=_("The project this setting applies to.")
    )

    def __unicode__(self):
        return unicode(self.project)

    def get_language_url(self):
        return self.service_language_urls.get(self.service_type, None)

    def get_translate_url(self):
        return self.service_translate_urls.get(self.service_type, None)

    def languages(self, target_lang=None):
        """Request to check if the given target language code is
        supported by the corresponding translation API.
        """
        if self.service_type == 'GT':
            params = {
                'key': self.api_key,
                'target': target_lang,
            }
        elif self.service_type == 'BT':
            params = {
                'appId': self.api_key,
            }
        r = requests.get(self.get_language_url(), params=params)
        return r.content

    def translate(self, term, source, target):
        """Build and send the actual request to the corresponding
        translation API and return the response content.
        """
        if self.service_type == 'GT':
            params = {
                'key': self.api_key,
                'q': term,
                'source': source,
                'target': target,
            }
        elif self.service_type == 'BT':
            params = {
                'appId': self.api_key,
                'texts': '["' + term + '"]',
                'from': source,
                'to': target,
                'options': '{"State": ""}'
            }
        r = requests.get(self.get_translate_url(), params=params)
        return r.content
