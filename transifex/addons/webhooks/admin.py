# -*- coding: utf-8 -*-

from django.contrib import admin
from webhooks.models import WebHook


class WebHookAdmin(admin.ModelAdmin):
    pass

admin.site.register(WebHook, WebHookAdmin)
