# -*- coding: utf-8 -*-
from django.dispatch import Signal

# 00:00:00
cron_nightly = Signal()

# 12:00:00
cron_daily = Signal()

# 06:00:00 || 18:00:00
cron_twicedaily = Signal()

# xx:00:00
cron_hourly = Signal()

cron_30min = Signal()

cron_15min = Signal()

cron_10min = Signal()

cron_5min = Signal()

cron_3min = Signal()

cron_1min = Signal()

cron_30sec = Signal()