from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.conf import settings
from django.db.models.loading import get_model
from django.utils.translation import ugettext as _
from django.template.context import RequestContext
from django.template import loader
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from actionlog.models import action_logging
from authority.models import Permission
from authority.views import get_next
from notification import models as notification
from transifex.txpermissions.templatetags.txpermissions import (txadd_url_for_obj,
                                                      txrequest_url_for_obj,
                                                      txurl_for_obj)
from transifex.txpermissions.forms import UserAjaxPermissionForm

def _send_notice_save_action(request, notice):
    """
    Handler for manipulating notifications and save action logs

    The argument notice must have the following dictionary structure:

    notice = {
        'type': '<notice_type_label>',
        'object': <object>,
        'sendto': [<list_of_users_to_send_to>],
        'extra_context': {'var_needed_in_template': var_needed_in_template},
    }

    Explanation:
        `type`: It is the notice label related to the action
        `object`: It is the object that is suffering the action
        `sendto`: List of Users to sent the notification to
        `extra_context`: Any extra var used in the message templates
    """
    action_logging(request.user, [notice['object']], notice['type'],
                context=notice['extra_context'])
    if settings.ENABLE_NOTICES:
        notification.send(set(notice['sendto']),
            notice['type'], extra_context=notice['extra_context'])



def add_permission_or_request(request, obj, view_name, approved=False,
                   template_name = 'authority/permission_form.html',
                   extra_context={}):
    """
    View for adding either a permission or a permission request for a user.

    This view is a centralized place for adding permissions/requests for any
    kind of object through the whole Transifex.

    Following the upstream django-authority app, all the entries are considered
    requests until the field approved be set to True.

    For the extra_context, this view expect a key called 'notice' that MUST
    have a determinate dictionary structure to be able to send notifications
    and save action logs. See the `_send_notice_save_action` function docstring
    for more information.

    Example of `extra_context` with `notice` key:
        # See `_send_notice_save_action` docstring for the `notice` var below
        notice = {}
        extra_context.update({'notice': notice})

    If the key 'notice' is not found in the extra_context parameter, nothing is
    executed about notification and action log.
    """
    codename = request.POST.get('codename', None)
    next = get_next(request, obj)

    if request.method == 'POST':
        # POST method requires a permission codename
        if codename is None:
            return HttpResponseForbidden(next)
        form = UserAjaxPermissionForm(data=request.POST, obj=obj,
                                  approved=approved, perm=codename,
                                  initial=dict(codename=codename))
        if not approved:
            # Limit permission request to current user
            form.data['user'] = request.user
        if form.is_valid():
            permission = form.save(request)

            if extra_context.has_key('notice'):
                # ActionLog & Notification
                _send_notice_save_action(request, extra_context['notice'])

            if approved:
                msg = _('You added a permission.')
            else:
                msg = _('You added a permission request.')

            messages.info(request, msg)

            return HttpResponseRedirect(next)
    else:
        form = None

    context = {
        'form': form,
        'form_url': txurl_for_obj(view_name, obj),
        'next': next,
        'perm': codename,
        'approved': approved,
    }
    extra_context.update({'notice':None})
    context.update(extra_context)
    return render_to_response(template_name, context,
                              context_instance=RequestContext(request))


def approve_permission_request(request, requested_permission, extra_context={}):
    """
    View for approving/rejecting a user's permission request.

    This view is a centralized place for approving permission requests for any
    kind of object through the whole Transifex.

    Following the upstream django-authority app, all the entries are considered
    requests until the field approved be set to True.
    """
    requested_permission.approve(request.user)

    if extra_context.has_key('notice'):
        # ActionLog & Notification
        _send_notice_save_action(request, extra_context['notice'])

    messages.info(request, _('You approved the permission request.'))
    next = get_next(request, requested_permission)
    return HttpResponseRedirect(next)


def delete_permission_or_request(request, permission, approved, extra_context={}):
    """
    View for deleting either a permission or a permission request from a user.

    This view is a centralized place for deleting permission/requests for any
    kind of object through the whole Transifex.

    Following the upstream django-authority app, all the entries are considered
    requests until the field approved be set to True.
    """
    next = request.POST.get('next', '/')

    if approved:
        msg = _('You removed the permission.')
    else:
        msg = _('You removed the permission request.')

    permission.delete()

    if extra_context.has_key('notice'):
        # ActionLog & Notification
        _send_notice_save_action(request, extra_context['notice'])

    messages.info(request, msg)
    return HttpResponseRedirect(next)
