from django.contrib import admin
from transifex.releases.models import Release

class ReleaseAdmin(admin.ModelAdmin):
    search_fields = ['name', 'description', 'project__name', 'resources__name']
    list_display = ['name', 'description', 'project']

admin.site.register(Release, ReleaseAdmin)
