# -*- coding: utf-8 -*-

from django.contrib import admin
from txapps.models import TxApp


class TxAppAdmin(admin.ModelAdmin):
    pass

admin.site.register(TxApp, TxAppAdmin)
