# -*- coding: utf-8 -*-
from django.dispatch import Signal

pre_proj_save = Signal(providing_args=['instance', 'form'])
post_proj_save_m2m = Signal(providing_args=['instance', 'form'])
pre_comp_prep = Signal(providing_args=['instance'])
post_comp_prep = Signal(providing_args=['instance'])
submission_error = Signal(providing_args=['filename', 'message'])
# Signal emitted when a new project is created
project_created = Signal()
project_deleted = Signal()

pre_set_stats = Signal(providing_args=['instance'])
post_set_stats = Signal(providing_args=['instance'])

# Resource signals
post_resource_save = Signal(providing_args=['instance', 'created', 'user'])
post_resource_delete = Signal(providing_args=['instance', 'user'])

# Release signals
post_release_save = Signal(providing_args=['instance', 'created', 'user'])

# SL Submit Translations signal
pre_submit_translation = Signal(providing_args=['instance'])
post_submit_translation = Signal(providing_args=['request', 'resource', 'language', 'modified'])

# This is obsolete:
sig_refresh_cache = Signal(providing_args=["resource"])
pre_refresh_cache = sig_refresh_cache
post_refresh_cache = Signal(providing_args=["resource"])

# This is obsolete:
sig_clear_cache = Signal(providing_args=["resource"])
pre_clear_cache = sig_clear_cache
post_clear_cache = Signal(providing_args=["resource"])

# Signals used by cla addon:
pre_team_request = Signal(providing_args=['project', 'user'])
pre_team_join = Signal(providing_args=['project', 'user'])
cla_create = Signal(providing_args=['project', 'license_text', 'request'])
project_access_control_form_start = Signal(providing_args=['instance', 'project'])

# Signals used by licenses addon
project_form_init = Signal(providing_args=['form'])
project_form_save = Signal(providing_args=['form', 'instance'])

#Signals used by subscriptions
project_private_check = Signal(providing_args=['instance'])
project_type_check = Signal(providing_args=['instance'])

# Cache signals
project_outsourced_changed = Signal(providing_args=['project'])

class ClaNotSignedError(Exception): pass
