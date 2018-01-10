# -*- coding: utf-8 -*-
from __future__ import with_statement
from django import template
from django.db import transaction
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.template.defaultfilters import slugify
from django.forms.util import ErrorList
from transifex.txcommon.utils import get_url_pattern
from transifex.languages.models import Language
from transifex.resources.forms import CreateResourceForm, \
        ResourceTranslationForm, UpdateTranslationForm
from transifex.resources.models import Resource
from transifex.resources.backends import ResourceBackend, FormatsBackend, \
        ResourceBackendError, FormatsBackendError, content_from_uploaded_file, \
        filename_of_uploaded_file

register = template.Library()


@register.inclusion_tag("resources/upload_create_resource_form.html")
def upload_create_resource_form(request, project, prefix='create_form'):
    """Form for creating a new resource."""
    resource = None
    display_form = False
    if request.method == 'POST' and request.POST.get('create_resource', None):
        cr_form = CreateResourceForm(
            request.POST, request.FILES, prefix=prefix
        )
        if cr_form.is_valid():
            name = cr_form.cleaned_data['name']
            slug = slugify(name)

            # Check if we already have a resource with this slug in the db.
            try:
                Resource.objects.get(slug=slug, project=project)
            except Resource.DoesNotExist:
                pass
            else:
                # if the resource exists, modify slug in order to force the
                # creation of a new resource.
                slug = slugify(name)
                identifier = Resource.objects.filter(
                    project=project, slug__icontains="%s_" % slug
                ).count() + 1
                slug = "%s_%s" % (slug, identifier)
            method = cr_form.cleaned_data['i18n_method']
            content = content_from_uploaded_file(request.FILES)
            filename = filename_of_uploaded_file(request.FILES)
            rb = ResourceBackend()
            try:
                with transaction.commit_on_success():
                    rb.create(
                        project, slug, name, method, project.source_language,
                        content, user=request.user,
                        extra_data={'filename': filename}
                    )
            except ResourceBackendError, e:
                cr_form._errors['source_file'] = ErrorList([e.message, ])
                display_form=True
            else:
                display_form = False
                resource = Resource.objects.get(slug=slug, project=project)
        else:
            display_form=True
    else:
        cr_form = CreateResourceForm(prefix=prefix)
        display_form = False

    return {
          'project' : project,
          'resource': resource,
          'create_resource_form': cr_form,
          'display_form': display_form,
    }


@register.inclusion_tag("resources/upload_resource_translation_button.html", takes_context=True)
def upload_resource_translation_button(context, request, resource, language=None,
     prefix='button', translate_online=False):
    """Form to add a translation.

    If the parameter translate online is given, a new button will appear next
    to the upload button which onclick will redirect the user to lotte.
    """
    if language or (request.POST and
                    request.POST.get('target_language', None)):
        return update_translation_form(context, request, resource, language)
    else:
        return create_translation_form(context, request, resource, language)


def create_translation_form(context, request, resource, language=None,
                            prefix='button', translate_online=True):
    form = ResourceTranslationForm(prefix=prefix)

    return {
        'project': resource.project,
        'resource': resource,
        'language' : language,
        'resource_translation_form': form,
        'translate_online': translate_online,
        'create': True,
    }


def update_translation_form(context, request, resource, language=None,
                            prefix='update_trans', translate_online=False):
    """Form to add a translation.

    If the parameter translate online is given, a new button will appear next
    to the upload button which onclick will redirect the user to lotte.
    """
    if language:
        initial = {"target_language": language.code, }
    else:
        initial = {}
    form = UpdateTranslationForm(prefix=prefix, initial=initial)

    return {
        'project': resource.project,
        'resource': resource,
        'language' : language,
        'update_translation_form': form,
        'translate_online': False,
        'create': False,
    }
