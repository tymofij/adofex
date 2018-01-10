from django.contrib import admin
from models import Language

class LanguageAdmin(admin.ModelAdmin):
    search_fields = ['name', 'code', 'code_aliases']

admin.site.register(Language, LanguageAdmin)

