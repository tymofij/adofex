# -*- coding: utf-8 -*-
from django.contrib import admin
from transifex.resources.models import *

class ResourceAdmin(admin.ModelAdmin):
    search_fields = ['slug', 'name', 'project__name', 'source_language__name', 'i18n_type']
    list_display = ['name', 'project', 'source_language', 'i18n_type']

class SourceEntityAdmin(admin.ModelAdmin):
    search_fields = ['string', 'string_hash', 'context', 'occurrences']
    list_display = ['string', 'context', 'resource', 'last_update']

class TranslationAdmin(admin.ModelAdmin):
    search_fields = ['string', 'string_hash', 'language__name',
        'source_entity__string']
    list_display = ['source_entity', 'string', 'language', 'last_update']
    list_display_links = ['string']

class TemplateAdmin(admin.ModelAdmin):
    search_fields = ['resource__name', 'resource__project__name',
        'resource__source_language__name']
    list_display = ['resource']


admin.site.register(Resource, ResourceAdmin)
admin.site.register(SourceEntity, SourceEntityAdmin)
admin.site.register(Translation, TranslationAdmin)
admin.site.register(Template, TemplateAdmin)
