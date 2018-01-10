from django import forms
from django.contrib import admin
from django.utils.translation import ugettext, ungettext, ugettext_lazy as _
from django.contrib.contenttypes import generic
from transifex.projects.models import Project, HubRequest
#from authority.admin import PermissionInline
from authority.models import Permission
from authority import get_choices_for

class PermissionInline(generic.GenericTabularInline):
    model = Permission
    raw_id_fields = ('user', 'group', 'creator')
    extra = 1

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'codename':
            perm_choices = get_choices_for(self.parent_model)
            kwargs['label'] = _('permission')
            kwargs['widget'] = forms.Select(choices=perm_choices)
        return super(PermissionInline, self).formfield_for_dbfield(db_field, **kwargs)

class ProjectAdmin(admin.ModelAdmin):
    search_fields = ['name', 'description']
    list_display = ['name', 'description']

admin.site.register(Project, ProjectAdmin, inlines=(PermissionInline,))
admin.site.register(HubRequest)

