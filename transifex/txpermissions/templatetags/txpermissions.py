from django import template
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User, AnonymousUser
from django.core.urlresolvers import reverse

from authority import permissions, get_check
from authority.models import Permission
from authority.templatetags.permissions import ResolverNode, url_for_obj

from transifex.projects.permissions.project import ProjectPermission
#FIXME: the module forms cannot be located else
from transifex.txpermissions.forms import UserAjaxPermissionForm

register = template.Library()

def _base_permission_form(context, obj, perm, view_name):
    """
    Handler for returning a dictionary with two basic fields (url and next) for
    the permission form, based on the arguments passed by parameter.
    """
    return {
        'next': context['request'].build_absolute_uri(),
        'url': reverse(view_name, kwargs={'project_slug': obj.slug,
                                          'permission_pk': perm.pk,}),
    }

@register.simple_tag
def txurl_for_obj(view_name, obj):
    """
    Return the reverse url for a given obj and view_name based on the
    object slug
    """
    return reverse(view_name, kwargs={'%s_slug' % obj._meta.module_name: obj.slug})


@register.simple_tag
def txadd_url_for_obj(obj):
    """Return the reverse url for adding permissions to an object"""
    return txurl_for_obj(u'%s_add_permission' % obj._meta.module_name, obj)


@register.simple_tag
def txrequest_url_for_obj(obj):
    """Return the reverse url for adding permission request to an object"""
    return txurl_for_obj(u'%s_add_permission_request' % obj._meta.module_name,
                         obj)


@register.inclusion_tag('txpermissions/permission_delete_form.html',
                        takes_context=True)
def txpermission_delete_form(context, obj, perm):
    """
    Render a html form to the delete view of the given permission. Return
    no content if the request-user has no permission to delete foreign
    permissions.
    """
    user = context['request'].user
    if user.is_authenticated():
        check = ProjectPermission(user)
        if (check.maintain(obj) or user.has_perm('authority.delete_permission')
            or user.pk == perm.creator.pk):
            return _base_permission_form(context, obj, perm,
                                         'project_delete_permission')
    return {'url': None}


@register.inclusion_tag('txpermissions/permission_request_delete_form.html',
                        takes_context=True)
def txpermission_request_delete_form(context, obj, perm):
    """
    Render a html form to the delete view of the given permission request.
    Return no content if the request-user has no permission to delete
    permissions.
    """
    user = context['request'].user
    if user.is_authenticated():
        check = ProjectPermission(user)
        form_kwargs = _base_permission_form(context, obj, perm,
                                            'project_delete_permission_request')
        if check.maintain(obj) or user.has_perm('authority.delete_permission'):
            form_kwargs['is_requestor'] = False
            return form_kwargs
        if not perm.approved and perm.user == user:
            form_kwargs['is_requestor'] = True
            return form_kwargs
    return {'url': None}


@register.inclusion_tag('txpermissions/permission_request_approve_form.html',
                        takes_context=True)
def txpermission_request_approve_form(context, obj, perm):
    """
    Render a html form to the approve view of the given permission request.
    Return no content if the request-user has no permission to delete
    permissions.
    """
    user = context['request'].user
    if user.is_authenticated():
        check = ProjectPermission(user)
        if (check.maintain(obj) or
            user.has_perm('authority.approve_permission_requests')):
            return _base_permission_form(context, obj, perm,
                                         'project_approve_permission_request')
    return {'url': None}


class PermissionFormNode(ResolverNode):

    @classmethod
    def handle_token(cls, parser, token, approved):
        bits = token.contents.split()
        tag_name = bits[0]
        kwargs = {
            'obj': cls.next_bit_for(bits, 'for'),
            'perm': cls.next_bit_for(bits, 'using', None),
            'template_name': cls.next_bit_for(bits, 'with', ''),
            'approved': approved,
        }
        return cls(**kwargs)

    def __init__(self, obj, perm=None, approved=False, template_name=None):
        self.obj = obj
        self.perm = perm
        self.approved = approved
        self.template_name = template_name

    def render(self, context):
        obj = self.resolve(self.obj, context)
        perm = self.resolve(self.perm, context)
        if self.template_name:
            template_name = [self.resolve(obj, context)
                             for obj in self.template_name.split(',')]
        else:
            template_name = 'txpermissions/permission_form.html'
        request = context['request']
        extra_context = {}
        if self.approved:
            check = ProjectPermission(request.user)
            if request.user.is_authenticated():
                if (check.maintain(obj)
                    or request.user.has_perm('authority.add_permission')):
                    extra_context = {
                        'form_url': txadd_url_for_obj(obj),
                        'next': request.build_absolute_uri(),
                        'approved': self.approved,
                        'form': UserAjaxPermissionForm(perm, obj,
                            approved=self.approved, initial=dict(codename=perm)),
                    }
        else:
            if request.user.is_authenticated() and not request.user.is_superuser:
                extra_context = {
                    'form_url': txrequest_url_for_obj(obj),
                    'next': request.build_absolute_uri(),
                    'approved': self.approved,
                    'form': UserAjaxPermissionForm(perm, obj,
                        approved=self.approved, initial=dict(
                        codename=perm, user=request.user.username)),
                }
        return template.loader.render_to_string(template_name, extra_context,
                            context_instance=template.RequestContext(request))


@register.tag
def txpermission_form(parser, token):
    """
    Render an "add permissions" form for the given object. If no object
    is given it will render a select box to choose from.

    Syntax::

        {% txpermission_form for OBJ using PERMISSION_LABEL.CHECK_NAME [with TEMPLATE] %}
        {% txpermission_form for project using "project_permission.add_project" %}

    """
    return PermissionFormNode.handle_token(parser, token, approved=True)


@register.tag
def txpermission_request_form(parser, token):
    """
    Render an "add permission requests" form for the given object. If no object
    is given it will render a select box to choose from.

    Syntax::

        {% txpermission_request_form for OBJ and PERMISSION_LABEL.CHECK_NAME [with TEMPLATE] %}
        {% txpermission_request_form for project using "project_permission.add_project" with "txpermissions/permission_request_form.html" %}

    """
    return PermissionFormNode.handle_token(parser, token, approved=False)
