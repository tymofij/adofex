# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AnonymousUser
from django.db.models import F

from actionlog.models import action_logging
from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.projects.signals import post_release_save
from transifex.projects.permissions import *
from transifex.releases import RELEASE_ALL_DATA
from transifex.releases.models import Release
from transifex.releases.forms import ReleaseForm
from transifex.resources.models import Resource, RLStats

# Temporary
from transifex.txcommon import notifications as txnotification
from transifex.txcommon.decorators import one_perm_required_or_403
from transifex.txcommon.log import logger

from django.contrib.syndication.views import feed
from transifex.projects.permissions import pr_project_private_perm

@login_required
@one_perm_required_or_403(pr_release_add_change,
    (Project, 'slug__exact', 'project_slug'))
def release_create_update(request, project_slug, release_slug=None, *args, **kwargs):
    project = get_object_or_404(Project, slug__exact=project_slug)
    if release_slug:
        release = get_object_or_404(Release, slug=release_slug,
                                    project__slug=project_slug)
    else:
        release = None
    if request.method == 'POST':
        release_form = ReleaseForm(
            project, request.user, request.POST, instance=release
        )
        if release_form.is_valid():
            if release:
                nt = "project_release_changed"
                created = False
            else:
                nt = "project_release_added"
                created = True
            release = release_form.save()
            context = {'project': project,
                       'release': release,}
            object_list = [project, release]
            action_logging(request.user, object_list, nt, context=context)
            post_release_save.send(sender=None, instance=release,
                    created=created, user=request.user)
            return HttpResponseRedirect(
                reverse('release_detail',
                         args=[project_slug, release.slug]))
    else:
        release_form = ReleaseForm(project, request.user, instance=release)

    return render_to_response('projects/release_form.html', {
        'form': release_form,
        'project': project,
        'release': release,
    }, context_instance=RequestContext(request))


@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def release_detail(request, project_slug, release_slug):
    release = get_object_or_404(Release, slug=release_slug,
        project__slug=project_slug)
    resources = Resource.objects.select_related('project',
        'source_language').filter(releases=release, project__private=False
        ).order_by('project__name')

    source_languages = Language.objects.filter(
        id__in=resources.values('project__source_language')).distinct()

    if request.user in (None, AnonymousUser()):
        private_resources = []
    else:
        private_resources = Resource.objects.select_related('project',
            'source_language').for_user(request.user).filter(
            releases=release, project__private=True
            ).order_by('project__name').distinct()
    if not len(source_languages) == 1:
        source_languages = ()

    statslist = RLStats.objects.select_related('language', 'last_committer'
        ).for_user(request.user).by_release_aggregated(release)

    return render_to_response('projects/release_detail.html', {
        'release': release,
        'alldata_slug': RELEASE_ALL_DATA['slug'],
        'project': release.project,
        'resources': resources,
        'private_resources': private_resources,
        'source_languages' : source_languages,
        'statslist': statslist,
    }, context_instance=RequestContext(request))

@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def release_language_detail(request, project_slug, release_slug, language_code):

    language = get_object_or_404(Language, code__iexact=language_code)
    project = get_object_or_404(Project, slug__exact=project_slug)
    release = get_object_or_404(Release, slug__exact=release_slug,
        project__id=project.pk)

    stats = RLStats.objects.select_related('resource', 'resource__project',
        'lock', 'last_committer', 'resource__priority').public(
        ).by_release_and_language(release, language)

    private_stats = RLStats.objects.select_related('resource', 'resource__project',
        'lock', 'last_committer', 'resource__priority').for_user(request.user
            ).private().by_release_and_language(release, language)

    empty_rlstats = Resource.objects.select_related('project').filter(
        id__in=release.resources.all(), project__private=False).exclude(
        id__in=stats.values('resource'))

    empty_private_rlstats = Resource.objects.select_related('project'
        ).for_user(request.user).filter(id__in=release.resources.all(),
        project__private=True).exclude(id__in=private_stats.values('resource'))

    return render_to_response('projects/release_language_detail.html', {
        'project': project,
        'release': release,
        'language': language,
        'stats': stats,
        'empty_rlstats': empty_rlstats,
        'empty_private_rlstats': empty_private_rlstats,
        'private_stats': private_stats,
    }, context_instance=RequestContext(request))


@login_required
@one_perm_required_or_403(pr_release_delete,
    (Project, 'slug__exact', 'project_slug'))
def release_delete(request, project_slug, release_slug):
    release = get_object_or_404(Release, slug=release_slug,
                                project__slug=project_slug)
    if request.method == 'POST':
        import copy
        release_ = copy.copy(release)
        release.delete()
        messages.success(request,
                        _("The release '%s' was deleted.") % release.full_name)

        # ActionLog & Notification
        nt = 'project_release_deleted'
        context = {'release': release_,
                   'sender': request.user}
        action_logging(request.user, [release_.project], nt, context=context)
        if settings.ENABLE_NOTICES:
            txnotification.send_observation_notices_for(release_.project,
                                signal=nt, extra_context=context)

        return HttpResponseRedirect(reverse('project_detail',
                                     args=(project_slug,)))
    else:
        return HttpResponseRedirect(reverse('release_edit',
            args=(project_slug, release_slug)))


# Feeds
@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def release_feed(request, project_slug, release_slug, slug=None, param='',
    feed_dict=None,):
    param = '%s/%s' % (project_slug, release_slug)
    if slug:
        url = "%s/%s" % (slug, param)
    else:
        url = param
    return feed(request, url, feed_dict)


@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'project_slug'), anonymous_access=True)
def release_language_feed(request, project_slug, release_slug, language_code,
    slug=None, param='', feed_dict=None,):
    param = '%s/%s/%s' % (project_slug, release_slug, language_code)
    if slug:
        url = "%s/%s" % (slug, param)
    else:
        url = param
    return feed(request, url, feed_dict)