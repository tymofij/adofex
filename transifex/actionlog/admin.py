from django.contrib import admin
from actionlog.models import LogEntry

class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'message_safe', 'user', 'generic_object',
        'action_time')
    search_fields = ('action_type__label', 'message')

    def generic_object(self, obj):
        return "<%s: %s>" % (obj.content_type.model.title(),
        obj.content_type.get_object_for_this_type(pk=obj.object_id))
    generic_object.short_description = 'Generic object'
    generic_object.admin_order_field = 'content_type'

admin.site.register(LogEntry, LogEntryAdmin)