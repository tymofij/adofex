# -*- coding: utf-8 -*-
from __future__ import absolute_import
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.dispatch import Signal
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Count, Q, get_model, F
from django.http import (HttpResponseRedirect, HttpResponse, Http404,
                         HttpResponseForbidden, HttpResponseBadRequest)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _
from django.forms.util import ErrorList

from authority.views import permission_denied

from actionlog.models import action_logging
from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.projects.permissions import *
from transifex.projects.permissions.project import ProjectPermission
from transifex.projects.signals import post_resource_delete
from transifex.teams.models import Team
from transifex.txcommon.decorators import one_perm_required_or_403
from transifex.txcommon.log import logger

from transifex.resources.forms import ResourceForm, ResourcePseudoTranslationForm
from transifex.resources.models import Translation, Resource, RLStats
from transifex.resources.handlers import (invalidate_object_templates,
    invalidate_stats_cache)
from transifex.resources.formats.registry import registry
from transifex.resources.backends import FormatsBackend, FormatsBackendError, \
        content_from_uploaded_file
from autofetch.forms import URLInfoForm
from autofetch.models import URLInfo
from .tasks import send_notices_for_resource_edited

Lock = get_model('locks', 'Lock')

# Restrict access only for private projects
# Allow even anonymous access on public projects
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def resource_detail(request, project_slug, resource_slug):
    """
    Return the details overview of a project resource.
    """
    resource = get_object_or_404(Resource.objects.select_related(),
        project__slug=project_slug, slug=resource_slug)

    try:
        autofetch_url = resource.url_info
    except ObjectDoesNotExist:
        autofetch_url = None

    statslist_src = RLStats.objects.select_related('language', 'last_committer',
        'lock','resource').by_resource(resource).filter(
            language = F('resource__source_language'))
    statslist = RLStats.objects.select_related('language', 'last_committer',
        'lock','resource').by_resource(resource).exclude(
            language = F('resource__source_language'))

    tmp = []
    for i in statslist_src:
        tmp.append(i)
    for i in statslist:
        tmp.append(i)
    statslist = tmp

    return render_to_response("resources/resource_detail.html", {
        'project': resource.project,
        'resource': resource,
        'autofetch_url': autofetch_url,
        'languages': Language.objects.order_by('name'),
        'statslist': statslist
    }, context_instance = RequestContext(request))


@one_perm_required_or_403(pr_resource_delete,
                          (Project, "slug__exact", "project_slug"))
def resource_delete(request, project_slug, resource_slug):
    """
    Delete a Translation Resource in a specific project.
    """
    resource = get_object_or_404(Resource, project__slug=project_slug,
        slug=resource_slug)

    if request.method == 'POST':
        import copy
        resource_ = copy.copy(resource)
        resource.delete()

        # Signal for logging
        post_resource_delete.send(sender=None, instance=resource_,
            user=request.user)

        messages.success(request,
            _("The translation resource '%s' was deleted.") % resource_.name)

        return HttpResponseRedirect(reverse('project_detail',
                                    args=[resource.project.slug]),)
    else:
        return HttpResponseRedirect(reverse('resource_edit',
            args=[resource.project.slug, resource.slug]))


@one_perm_required_or_403(pr_resource_add_change,
                          (Project, "slug__exact", "project_slug"))
def resource_edit(request, project_slug, resource_slug):
    """
    Edit the metadata of  a Translation Resource in a specific project.
    """
    resource = get_object_or_404(Resource, project__slug = project_slug,
                                  slug = resource_slug)
    try:
        urlinfo = URLInfo.objects.get(resource = resource)
    except URLInfo.DoesNotExist:
        urlinfo = None

    if request.method == 'POST':
        resource_form = ResourceForm(request.POST, request.FILES, instance=resource)
        if urlinfo:
            url_form = URLInfoForm(request.POST, instance=urlinfo,)
        else:
            url_form = URLInfoForm(request.POST,)
        if resource_form.is_valid() and url_form.is_valid():
            try:
                resource = resource_form.save(commit=False)
                if resource_form.cleaned_data['sourcefile'] is not None:
                    method = resource.i18n_method
                    content = content_from_uploaded_file(
                        {0: resource_form.cleaned_data['sourcefile'], }
                    )
                    filename = resource_form.cleaned_data['sourcefile'].name
                    save_source_file(
                        resource, request.user, content, method, filename
                    )

                urlinfo = url_form.save(commit=False)
                resource_new = resource_form.save()
                resource_new.save()
                urlinfo.resource = resource_new
                invalidate_object_templates(resource_new,
                    resource_new.source_language)
                if urlinfo.source_file_url:
                    try:
                        urlinfo.update_source_file(fake=True)
                    except Exception, e:
                        url_form._errors['source_file_url'] = _("The URL you provided"
                            " doesn't link to a valid file.")
                        return render_to_response('resources/resource_form.html', {
                            'resource_form': resource_form,
                            'url_form': url_form,
                            'resource': resource,
                        }, context_instance=RequestContext(request))
                    # If we got a URL, save the model instance
                    urlinfo.save()
                else:
                    if urlinfo.auto_update:
                        url_form._errors['source_file_url'] = _("You have checked"
                            " the auto update checkbox but you haven't provided a"
                            " valid url.")
                        return render_to_response('resources/resource_form.html', {
                            'resource_form': resource_form,
                            'url_form': url_form,
                            'resource': resource,
                        }, context_instance=RequestContext(request))
                    else:
                        if urlinfo.id:
                            urlinfo.delete()

                send_notices_for_resource_edited.delay(
                    resource_new, request.user
                )

                return HttpResponseRedirect(reverse('resource_detail',
                    args=[resource.project.slug, resource.slug]))
            except FormatsBackendError, e:
                resource_form._errors['sourcefile'] = ErrorList([unicode(e), ])
    else:
        if resource:
            initial_data = {}

        if urlinfo:
            url_form = URLInfoForm(instance=urlinfo,)
        else:
            url_form = URLInfoForm()
        resource_form = ResourceForm(instance=resource)

    return render_to_response('resources/resource_form.html', {
        'resource_form': resource_form,
        'url_form': url_form,
        'resource': resource,
    }, context_instance=RequestContext(request))


@transaction.commit_on_success
def save_source_file(resource, user, content, method, filename=None):
    """Save new source file.

    Called by the "edit resource" action.
    """
    fb = FormatsBackend(resource, resource.source_language, user)
    return fb.import_source(content, filename)


@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def resource_actions(request, project_slug=None, resource_slug=None,
                     target_lang_code=None):
    """
    AJAX view for the resource-language popup on the resource details page.
    """
    resource = get_object_or_404(
        Resource.objects.select_related('project'),
        project__slug=project_slug,
        slug=resource_slug
    )
    target_language = get_object_or_404(Language, code=target_lang_code)
    project = resource.project
    # Get the team if exists to use it for permissions and links
    team = Team.objects.get_or_none(project, target_lang_code)

    disabled_languages_ids = RLStats.objects.filter(resource=resource
        ).values_list('language', flat=True).distinct()

    languages = Language.objects.filter()

    lock = Lock.objects.get_valid(resource, target_language)

    # We want the teams to check in which languages user is permitted to translate.
    user_teams = []
    if getattr(request, 'user') and request.user.is_authenticated():
        user_teams = Team.objects.filter(project=resource.project).filter(
            Q(coordinators=request.user)|
            Q(members=request.user)).distinct()

    try:
        stats = RLStats.objects.select_related('lock').get(
            resource=resource, language=target_language)
    except RLStats.DoesNotExist:
        stats = RLStats(
            untranslated=resource.total_entities,
            resource=resource,
            language=target_language
        )

    wordcount = resource.wordcount
    show_reviewed_stats = resource.source_language != target_language

    return render_to_response("resources/resource_actions.html", {
        'project': project,
        'resource': resource,
        'target_language': target_language,
        'team': team,
        'languages': languages,
        'disabled_languages_ids': disabled_languages_ids,
        'lock': lock,
        'user_teams': user_teams,
        'stats': stats,
        'wordcount': wordcount,
        'show_reviewed_stats': show_reviewed_stats,
    }, context_instance = RequestContext(request))


# Restrict access only for private projects
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=False)
def resource_pseudo_translation_actions(request, project_slug=None,
    resource_slug=None):
    """
    Ajax view that returns an fancybox template snippet for resource specific
    pseudo translation file actions.
    """
    resource = get_object_or_404(Resource.objects.select_related('project'),
        project__slug = project_slug, slug = resource_slug)
    project = resource.project

    form = ResourcePseudoTranslationForm()

    return render_to_response("resources/resource_pseudo_translation_actions.html",
        { 'project' : project,
          'resource' : resource,
          'form': form,
        },
        context_instance = RequestContext(request))


# Restrict access only for private projects
# Allow even anonymous access on public projects
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def project_resources(request, project_slug=None, offset=None, **kwargs):
    """
    Ajax view that returns a table snippet for all the resources in a project.

    If offset is provided, then the returned table snippet includes only the
    rows beginning from the offset and on.
    """
    more = kwargs.get('more', False)
    MORE_ENTRIES = 5
    project = get_object_or_404(Project, slug=project_slug)
    total = Resource.objects.filter(project=project).count()
    begin = int(offset)
    end_index = (begin + MORE_ENTRIES)
    resources = Resource.objects.filter(project=project)[begin:]
    # Get the slice :)
    if more and (not end_index >= total):
        resources = resources[begin:end_index]

    statslist = RLStats.objects.by_resources(resources)

    return render_to_response("resources/resource_list_more.html", {
        'project': project,
        'statslist': statslist},
        context_instance = RequestContext(request))


# Restrict access only to : (The checks are done in the view's body)
# 1)those belonging to the specific language team (coordinators or members)
# 2)project maintainers
# 3)global submitters (perms given through access control tab)
# 4)superusers
@login_required
def clone_language(request, project_slug=None, resource_slug=None,
            source_lang_code=None, target_lang_code=None):
    '''
    Get a resource, a src lang and a target lang and clone all translation
    strings for the src to the target.

    The user is redirected to the online editor for the target language.
    '''

    resource = get_object_or_404(Resource, slug=resource_slug,
                                 project__slug=project_slug)

    # Permissions handling
    # Project should always be available
    project = get_object_or_404(Project, slug=project_slug)
    team = Team.objects.get_or_none(project, target_lang_code)
    check = ProjectPermission(request.user)
    if not check.submit_translations(team or project) or not \
        resource.accept_translations:
        return permission_denied(request)

    source_lang = get_object_or_404(Language, code=source_lang_code)
    target_lang = get_object_or_404(Language, code=target_lang_code)

    # get the strings which will be cloned
    strings = Translation.objects.filter(
                resource = resource,
                language = source_lang)

    # If the language we want to create, has the same plural rules with the
    # source, we also copy the pluralized translations!
    if not source_lang.get_pluralrules() == target_lang.get_pluralrules():
        strings = strings.exclude(source_entity__pluralized = True)

    # clone them in new translation
    for s in strings:
        Translation.objects.get_or_create(
            language=target_lang, string=s.string,
            source_entity=s.source_entity, rule=s.rule,
            resource=s.resource
        )

    invalidate_stats_cache(resource, target_lang, user=request.user)
    return HttpResponseRedirect(reverse('translate_resource', args=[project_slug,
                                resource_slug, target_lang_code]),)


# Restrict access only to maintainers of the projects.
@one_perm_required_or_403(pr_resource_translations_delete,
                          (Project, "slug__exact", "project_slug"))
def resource_translations_delete(request, project_slug, resource_slug, lang_code):
    """
    Delete the set of Translation objects for a specific Language in a Resource.
    """
    resource = get_object_or_404(Resource, project__slug = project_slug,
                                 slug = resource_slug)

    language = get_object_or_404(Language, code=lang_code)

    # Use a flag to denote if there is an attempt to delete the source language.
    is_source_language = False
    if resource.source_language == language:
        is_source_language = True

    if request.method == 'POST':
        Translation.objects.filter(resource=resource,
            language=language).delete()

        messages.success(request,
                        _("Deleted %(lang)s translation for resource "
                        "%(resource)s.") % {
                          'lang': language.name,
                          'resource': resource.name})
        invalidate_stats_cache(resource, language, user=request.user)
        return HttpResponseRedirect(reverse('resource_detail',
                                    args=[resource.project.slug, resource.slug]),)
    else:
        return render_to_response(
            'resources/resource_translations_confirm_delete.html',
            {'resource': resource,
             'language': language,
             'is_source_language': is_source_language},
            context_instance=RequestContext(request))


# Restrict access only for private projects
# DONT allow anonymous access
@login_required
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'))
def get_translation_file(request, project_slug, resource_slug, lang_code,
    **kwargs):
    """
    View to export all translations of a resource for the requested language
    and give the translation file back to the user.
    """
    resource = get_object_or_404(Resource, project__slug = project_slug,
        slug = resource_slug)

    language = get_object_or_404(Language, code=lang_code)

    try:
        fb = FormatsBackend(resource, language)
        template = fb.compile_translation(**kwargs)
    except Exception, e:
        messages.error(request, "Error compiling translation file.")
        logger.error("Error compiling '%s' file for '%s': %s" % (language,
            resource, str(e)))
        return HttpResponseRedirect(reverse('resource_detail',
            args=[resource.project.slug, resource.slug]),)

    response = HttpResponse(
        template, mimetype=registry.mimetypes_for(resource.i18n_method)[0]
    )
    _filename = "%(proj)s_%(res)s_%(lang)s%(type)s" % {
        'proj': smart_unicode(resource.project.slug),
        'res': smart_unicode(resource.slug),
        'lang': language.code,
        'type': registry.file_extension_for(resource, language)
    }

    # Prefix filename with mode, case it exists
    if kwargs.has_key('mode'):
        _filename = "%s_" % kwargs.get('mode').label + _filename

    response['Content-Disposition'] = ('attachment; filename=%s' % _filename)
    return response


# Restrict access only for private projects
# DONT allow anonymous access
@login_required
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'))
def get_pot_file(request, project_slug, resource_slug):
    """
    View to download the pot file of the resource.
    """
    resource = get_object_or_404(
        Resource, project__slug=project_slug, slug=resource_slug
    )
    try:
        fb = FormatsBackend(resource, None)
        template = fb.compile_translation()
    except Exception, e:
        messages.error(request, _("Error compiling the pot file."))
        logger.error(
            "Error compiling the pot file for %s: %s" % (resource, e)
        )
        return HttpResponseRedirect(reverse(
                'resource_detail', args=[resource.project.slug, resource.slug]
        ))
    response = HttpResponse(
        template, mimetype=registry.mimetypes_for(resource.i18n_method)[0]
    )
    _filename = "%(proj)s_%(res)s.pot" % {
        'proj': smart_unicode(resource.project.slug),
        'res': smart_unicode(resource.slug),
    }
    response['Content-Disposition'] = ('attachment; filename=%s' % _filename)
    return response


# Restrict access only to : (The checks are done in the view's body)
# 1)those belonging to the specific language team (coordinators or members)
# 2)project maintainers
# 3)global submitters (perms given through access control tab)
# 4)superusers
@login_required
def lock_and_get_translation_file(request, project_slug, resource_slug, lang_code):
    """
    Lock and download the translations file.

    View to lock a resource for the requested language and as a second step to
    download (export+download) the translations in a formatted file.
    """

    resource = get_object_or_404(Resource, project__slug = project_slug,
        slug = resource_slug)

    # Permissions handling
    # Project should always be available
    project = get_object_or_404(Project, slug=project_slug)
    team = Team.objects.get_or_none(project, lang_code)
    check = ProjectPermission(request.user)
    if not check.submit_translations(team or project) or not \
        resource.accept_translations:
        return permission_denied(request)

    language = get_object_or_404(Language, code=lang_code)
    lock = Lock.objects.get_valid(resource, language)
    can_lock = Lock.can_lock(resource, language, request.user)
    response = {}

    if not can_lock:
        #print_gray_text(You cannot assign this file to you)
        response['status'] = "FAILED"
        response['message'] = _("Sorry, you cannot lock this file!")
    else:
        # User can lock
        if not lock:
            try:
                # Lock the resource now
                Lock.objects.create_update(resource, language, request.user)
                response['status'] = 'OK'
                response['redirect'] = reverse('download_for_translation',
                    args=[resource.project.slug, resource.slug, lang_code])
            except:
                response['status'] = "FAILED"
                response['message'] = _("Failed to lock the resource!")
        else:
            if lock.owner == request.user:
                try:
                    # File already locked by me, so extend the lock period.
                    Lock.objects.create_update(resource, language, request.user)
                    response['status'] = 'OK'
                    response['redirect'] = reverse('download_for_translation',
                        args=[resource.project.slug, resource.slug, lang_code])
                except:
                    response['status'] = "FAILED"
                    response['message'] = _("Failed to extend lock period on "
                                            "the resource!")
            else:
                # File locked by someone else:
                response['status'] = "FAILED"
                response['message'] = _("You cannot lock it right now! (Locked "
                                        "by %s )" % (lock.owner,))

    return HttpResponse(simplejson.dumps(response), mimetype='application/json')


@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=False)
def update_translation(request, project_slug, resource_slug, lang_code=None):
    """Ajax view that gets an uploaded translation as a file and saves it.

    If the language is not specified, the translation does not exist yet.
    Othewise, this is an update.

    Returns:
        Either an error message, or nothing for success.
    """
    resource = get_object_or_404(
        Resource.objects.select_related('project'),
        project__slug=project_slug, slug=resource_slug
    )
    if lang_code is None:
        lang_code = request.POST.get('language_code', None)
    target_language = get_object_or_404(Language, code=lang_code)
    project = resource.project
    # Get the team if exists to use it for permissions and links
    team = Team.objects.get_or_none(project, lang_code)

    check = ProjectPermission(request.user)
    if (not check.submit_translations(team or resource.project) or\
            not resource.accept_translations) and not\
            check.maintain(resource.project):
        return HttpResponse(
            simplejson.dumps({
                    'msg': _("You are not allowed to upload a translation."),
                    'status': 403,
            }),
            status=403, content_type='text/plain'
        )

    content = content_from_uploaded_file(request.FILES)
    try:
        _save_translation(resource, target_language, request.user, content)
    except FormatsBackendError, e:
        return HttpResponse(
            simplejson.dumps({
                    'msg': unicode(e),
                    'status': 400,
            }),
            status=400, content_type='text/plain'
        )
    return HttpResponse(
        simplejson.dumps({
                'msg': "",
                'status': 200,
        }),
        status=200, content_type='text/plain'
    )


@transaction.commit_on_success
def _save_translation(resource, target_language, user, content):
    """Save a new translation file for the resource."""
    fb = FormatsBackend(resource, target_language, user)
    return fb.import_translation(content)
