# -*- coding: utf-8 -*-
from django.contrib import admin
from transifex.addons.gtranslate.models import Gtranslate

class GtranslateAdmin(admin.ModelAdmin):
    search_fields = ['project', 'project__name']
    raw_id_fields = ('project', )


admin.site.register(Gtranslate, GtranslateAdmin)
