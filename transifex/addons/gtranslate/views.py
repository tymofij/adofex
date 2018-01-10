# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import simplejson
from transifex.projects.models import Project
from gtranslate.models import Gtranslate

def _get_canonical_name(target_lang):
    if '_' in target_lang or '-' in target_lang:
        return target_lang[:2]
    return target_lang

def translate(request, project_slug):
    """Wrapper view over the supported translation APIs. Captures the GET
    parameters and forwards the request to the suitable service."""
    source_lang = request.GET.get('source', None)
    target_lang = request.GET.get('target', None)
    term = request.GET.get('q', None)

    if not all([source_lang, target_lang, term]):
        return HttpResponse(status=400)

    target_lang = _get_canonical_name(target_lang)

    try:
        service = Gtranslate.objects.get(project__slug=project_slug)
        resp = service.translate(term, source_lang, target_lang)
        return HttpResponse(resp)
    except Gtranslate.DoesNotExist:
        return HttpResponse(simplejson.dumps({"error": "Auto-translate not available."}))

def languages(request, project_slug):
    """Thin wrapper over the translation APIs to check if the requested language
    is supported. If no services are enabled for the project, it has the ability
    to fallback to a common Transifex key for use by all projects.
    """
    target_lang = request.GET.get('target', None)
    if target_lang:
        target_lang = _get_canonical_name(target_lang)

    try:
        service = Gtranslate.objects.get(project__slug=project_slug)
        service_type = service.service_type
        if service_type == 'BT':
            cache_key = 'bing_translate'
        elif service_type == 'GT':
            cache_key = 'google_translate'
        if cache.get(cache_key, None):
            resp = cache.get(cache_key)
        else:
            resp = service.languages(target_lang)
            cache.set(cache_key, resp, 24*60*60)
        return HttpResponse(resp)
    except Gtranslate.DoesNotExist:
        return HttpResponse(simplejson.dumps({"error": "Auto-translate not available."}))
