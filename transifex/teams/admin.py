from django.contrib import admin
from transifex.teams.models import Team

class TeamAdmin(admin.ModelAdmin):
    search_fields = ['project__name', 'language__name',
        'coordinators__username', 'members__username', 'reviewers__username']
    list_display = ['project', 'language']

admin.site.register(Team, TeamAdmin)
