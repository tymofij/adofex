from django.contrib import admin
from cla.models import Cla, ClaSignature

class ClaAdmin(admin.ModelAdmin):
    list_display = ('project', 'created_at','modified_at')
    ordering = ('created_at',)

class ClaSignatureAdmin(admin.ModelAdmin):
    list_display = ('cla', 'user','created_at')
    ordering = ('created_at',)

admin.site.register(Cla, ClaAdmin)
admin.site.register(ClaSignature, ClaSignatureAdmin)