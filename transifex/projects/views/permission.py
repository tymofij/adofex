# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.utils.datastructures import MultiValueDictKeyError

from authority.models import Permission
from authority.views import permission_denied
from transifex.projects.forms import ProjectAccessControlForm
from transifex.projects.models import Project
from transifex.projects.permissions import *
from transifex.projects.permissions.project import ProjectPermission

# Temporary
from transifex.txcommon import notifications as txnotification

from transifex.txcommon.decorators import one_perm_required_or_403, access_off
from transifex.txcommon.log import logger
from transifex.txcommon.views import permission_denied
from transifex.txpermissions.views import (add_permission_or_request,
                                 approve_permission_request,
                                 delete_permission_or_request)

def _get_project_and_permission(project_slug, permission_pk):
    """
    Handler to return a project and a permission instance or a 404 error, based
    on the slugs passed by parameter.
    """
    project = get_object_or_404(Project, slug=project_slug)
    ctype = ContentType.objects.get_for_model(Project)
    permission = get_object_or_404(Permission, object_id=project.pk,
                                   content_type=ctype, id=permission_pk)
    return project, permission

@access_off(permission_denied)
@login_required
@one_perm_required_or_403(pr_project_add_perm,
    (Project, 'slug__exact', 'project_slug'))
def project_add_permission(request, project_slug):
    """
    Return a view with a form for adding a permission for a user.

    This view is an abstraction of a txpermissions.views method to be able to
    apply granular permission on it using a decorator.
    """
    project = get_object_or_404(Project, slug=project_slug)

    # When adding a permission it's necessary to query the user object in
    # order to be able to pass the extra_context for the notification/actionlog
    try:
        username = request.POST['user']
        sendto = User.objects.get(username=username)
    except (MultiValueDictKeyError, User.DoesNotExist):
        sendto=None

    notice = {
            'type': 'project_submit_access_granted',
            'object': project,
            'sendto': [sendto],
            'extra_context': {'project': project,
                              'user_request': sendto,
                              'user_action': request.user,
            },
        }
    return add_permission_or_request(request, project,
        view_name='project_add_permission',
        approved=True,
        extra_context={
            'project_permission': True,
            'project': project,
            'project_access_control_form': ProjectAccessControlForm(instance=project),
            'notice': notice,
        },
        template_name='projects/project_form_permissions.html')


#@login_required
#def project_add_permission_request(request, project_slug):
    #"""
    #Return a view with a form for adding a request of permission for a user.

    #This view is an abstraction of a txpermissions.views method.
    #"""
    #project = get_object_or_404(Project, slug=project_slug)
    #notice = {
            #'type': 'project_submit_access_requested',
            #'object': project,
            #'sendto': project.maintainers.all(),
            #'extra_context': {'project': project,
                              #'user_request': request.user
            #},
        #}
    #return add_permission_or_request(request, project,
        #view_name='project_add_permission_request',
        #approved=False,
        #extra_context={
            #'project_permission': True,
            #'project': project,
            #'project_permission_form': ProjectAccessControlForm(instance=project),
            #'notice': notice
        #},
        #template_name='projects/project_form_permissions.html')


@access_off(permission_denied)
@login_required
@one_perm_required_or_403(pr_project_approve_perm,
    (Project, 'slug__exact', 'project_slug'))
def project_approve_permission_request(request, project_slug, permission_pk):
    project, permission=_get_project_and_permission(project_slug, permission_pk)
    notice = {
            'type': 'project_submit_access_granted',
            'object': project,
            'sendto': [permission.user],
            'extra_context': {'project': project,
                              'user_request': permission.user,
                              'user_action': request.user,
            },
        }
    return approve_permission_request(request, permission,
                                      extra_context={ 'notice': notice })


@access_off(permission_denied)
@login_required
@one_perm_required_or_403(pr_project_delete_perm,
    (Project, 'slug__exact', 'project_slug'))
def project_delete_permission(request, project_slug, permission_pk):
    """
    View for deleting a permission of a user.

    This view is an abstraction of a txpermissions.views method to be able to
    apply granular permission on it using a decorator.
    """
    project, permission=_get_project_and_permission(project_slug, permission_pk)
    notice = {
            'type': 'project_submit_access_revoked',
            'object': project,
            'sendto': [permission.user],
            'extra_context': {'project': project,
                              'user_request': permission.user,
                              'user_action': request.user,
            },
        }
    return delete_permission_or_request(request, permission, True,
                                        extra_context={ 'notice': notice })


@access_off(permission_denied)
@login_required
def project_delete_permission_request(request, project_slug, permission_pk):
    """
    View for deleting a request of permission of a user.

    This view is an abstraction of a txpermissions.views method.
    """
    project, permission=_get_project_and_permission(project_slug, permission_pk)

    # It's necessary to distinguish between maintainer and normal users that
    # did the request
    if request.user.id==permission.user.id:
        notice_type = 'project_submit_access_request_withdrawn'
        sendto = project.maintainers.all()
    else:
        notice_type = 'project_submit_access_request_denied'
        sendto = [permission.user]

    notice = {
            'type': notice_type,
            'object': project,
            'sendto': sendto,
            'extra_context': {'project': project,
                              'user_request': permission.user,
                              'user_action': request.user,
            },
        }

    check = ProjectPermission(request.user)
    if check.maintain(project) or \
        request.user.has_perm('authority.delete_permission') or \
        request.user.pk == permission.creator.pk:
        return delete_permission_or_request(request, permission, False,
                                            extra_context={ 'notice': notice },)


    check = ProjectPermission(request.user)
    if check.maintain(project) or \
            request.user.has_perm('authority.delete_permission') or \
            request.user.pk == permission.creator.pk:
        return delete_permission_or_request(request, permission, False)

    return permission_denied(request)

