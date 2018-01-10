# -*- coding: utf-8 -*-
from django.contrib.auth.models import AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_noop as _
from notification.models import ObservedItem, is_observing, send


# This is temporary
NOTICE_TYPES = [
            {
                "label": "project_added",
                "display": _("New project created"),
                "description": _("when a new project is created"),
                "default": 1,
                "show_to_user": False,
            },
            {
                "label": "project_changed",
                "display": _("Project modified"),
                "description": _("when a project is changed"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_deleted",
                "display": _("Project deleted"),
                "description": _("when a project is deleted"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_submit_access_requested",
                "display": _("Requested submit access to project"),
                "description": _("when a user request access to submit files "
                                 "to a project"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_submit_access_request_denied",
                "display": _("Denied submit access to project"),
                "description": _("when a maintainer denies a user access "
                                 "to submit files to a project"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_submit_access_request_withdrawn",
                "display": _("Withdrew request for submit access to project"),
                "description": _("when a user withdraws the request for "
                                 "access to submit files to a project"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_submit_access_granted",
                "display": _("Granted submit access to project"),
                "description": _("when a maintainer grants a user access "
                                 "to submit files to a project"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_submit_access_revoked",
                "display": _("Revoked submit access to project"),
                "description": _("when a maintainer revokes the access of an "
                                 "user to submit files to a project"),
                "default": 2,
                "show_to_user": True,
            },

            # Outsourcing requests
            {
                "label": "project_hub_join_requested",
                "display": _("Requested to join a project hub"),
                "description": _("when a project requests to join a "
                                 "project hub"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_hub_join_approved",
                "display": _("Approved to join project hub"),
                "description": _("when a project is approved to join a "
                                 "project hub"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_hub_join_denied",
                "display": _("Denied to join project hub"),
                "description": _("when a project is denied to join a "
                                 "project  hub"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_hub_join_withdrawn",
                "display": _("Withdrew request to join project hub"),
                "description": _("when a project decides not to "
                                 "join a project hub"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_hub_left",
                "display": _("Project left project hub"),
                "description": _("when a project leaves a "
                                 "project hub"),
                "default": 2,
                "show_to_user": False,
            },

            # Project releases

            {
                "label": "project_release_added",
                "display": _("Release added to project"),
                "description": _("when a release is added to a project"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_release_changed",
                "display": _("Release modified"),
                "description": _("when a release of a project is modified"),
                "default": 2,
                "show_to_user": True,
            },
            {   "label": "project_release_deleted",
                "display": _("Release deleted"),
                "description": _("when a release of a project is deleted"),
                "default": 2,
                "show_to_user": True,
            },
            {   "label": "project_release_before_stringfreeze",
                "display": _("Release about to enter the string freeze period"),
                "description": _("when a release of a project is about to "
                                 "enter the String Freeze period"),
                "default": 2,
                "show_to_user": True,
            },
            {   "label": "project_release_in_stringfreeze",
                "display": _("Release is in string freeze period"),
                "description": _("when a release of a project is on enter "
                                 "the String Freeze period"),
                "default": 2,
                "show_to_user": True,
            },
            {   "label": "project_release_before_trans_deadline",
                "display": _("Release about to hit the translation deadline"),
                "description": _("when a release of a project is about to "
                                 "hit the Translation Deadline date"),
                "default": 2,
                "show_to_user": True,
            },
            {   "label": "project_release_hit_trans_deadline",
                "display": _("Release has hit the translation deadline"),
                "description": _("when a release of a project hits the "
                                 "Translation Deadline date"),
                "default": 2,
                "show_to_user": True,
            },
            {   "label": "project_release_stringfreeze_breakage",
                "display": _("Release string freeze breakage"),
                "description": _("when a release of a project has a "
                                 "string freeze breakage"),
                "default": 2,
                "show_to_user": True,
            },

            # Teams

            {
                "label": "project_team_added",
                "display": _("New team created"),
                "description": _("when a new translation team is added "
                                 "to a project"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_changed",
                "display": _("Team modified"),
                "description": _("when a translation team of a project "
                                 "is modified"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_deleted",
                "display": _("Team removed"),
                "description": _("when a translation team of a project "
                                 "is removed"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_requested",
                "display": _("Requested team creation"),
                "description": _("when the creation of a translation team is "
                                 "requested for a project"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_request_denied",
                "display": _("Denied request for team creation"),
                "description": _("when the creation of a translation team "
                                 "for a project is denied by a maintainer"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_join_requested",
                "display": _("Requested to join translation team"),
                "description": _("when a user requests to join a "
                                 "project translation team"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_join_approved",
                "display": _("Approved to join translation team"),
                "description": _("when a user is approved as a member of a "
                                 "project translation team"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_join_denied",
                "display": _("Denied to join translation team"),
                "description": _("when a user is denied as a member of a "
                                 "project translation team"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_join_withdrawn",
                "display": _("Withdrew request to join team"),
                "description": _("when a user decides not to "
                                 "join a project translation team"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_team_left",
                "display": _("User left translation team"),
                "description": _("when a user leaves a "
                                 "project translation team"),
                "default": 2,
                "show_to_user": True,
            },

            # Reports

            {
                "label": "project_report_weekly_maintainers",
                "display": _("Weekly project report for maintainers"),
                "description": _("when you receive the weekly report of "
                                 "projects that you maintain."),
                "default": 2,
                "show_to_user": True,
            },

            {   "label": "user_nudge",
                "display": _("User nudge"),
                "description": _("when a user nudges you"),
                "default": 2,
                "show_to_user": True,
            },

            # Resources

            {
                "label": "project_resource_added",
                "display": _("Resource created"),
                "description": _("when a new resource is added to a project"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_resource_changed",
                "display": _("Resource modified"),
                "description": _("when a resource of a project is changed"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_resource_deleted",
                "display": _("Resource deleted"),
                "description": _("when a resource of a project is deleted"),
                "default": 2,
                "show_to_user": True,
            },
            {   # Used only for ActionLog purposes.
                "label": "project_resource_translated",
                "display": _("Resource translated"),
                "description": _("when a translation is sent to a project "
                    "resource"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_resource_translation_changed",
                "display": _("Resource translation updated"),
                "description": _("when a resource translation you are "
                    "watching changes"),
                "default": 2,
                "show_to_user": True,
            },
            {
                "label": "project_resource_full_reviewed",
                "display": _("Resource translation fully reviewed"),
                "description": _("when a resource translation of one of your "
                    "projects becomes fully reviewed"),
                "default": 2,
                "show_to_user": True,
            },
    ]


# Overwriting this function temporarily, until the upstream patch
# http://github.com/jezdez/django-notification/commit/a8eb0980d2f37b799ff55dbc3a386c97ad479f99
# be accepted on http://github.com/pinax/django-notification
def send_observation_notices_for(observed, signal='post_save', extra_context=None):
    """
    Send a notice for each registered user about an observed object.
    """
    observed_items = ObservedItem.objects.all_for(
        observed, signal
    ).select_related('user', 'notice_type', 'observed_object')
    for item in observed_items:
        if extra_context is None:
            extra_context = {}

        context = {
            "observed": item.observed_object,
        }
        context.update(extra_context)

        send([item.user], item.notice_type.label, context)
    return observed_items
