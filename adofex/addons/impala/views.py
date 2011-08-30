# -*- ceoding: utf-8 -*-
import os, zipfile, time, shutil, urllib2, StringIO

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.simple import direct_to_template
from django.template import RequestContext

from transifex.projects.models import Project
from transifex.resources.models import Resource
from transifex.releases.models import Release, RLStats
from transifex.languages.models import Language
from transifex.projects.permissions import pr_resource_add_change
from transifex.txcommon.decorators import one_perm_required_or_403

from impala.forms import ImportForm
from impala.bundle import XpiBundle, TarBundle

BZ_URL = "http://www.babelzilla.org/wts/download/locale/all/skipped/%s"

@login_required
@one_perm_required_or_403(pr_resource_add_change,
    (Project, 'slug__exact', 'project_slug'))
def moz_import(request, project_slug):
    """
    View to handle XPI upload requests
    """
    messages = []
    project = get_object_or_404(Project, slug=project_slug)
    if request.method == 'POST':
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data['xpifile']:
                try:
                    xpifile = request.FILES['xpifile']
                    bundle = XpiBundle(xpifile, project, name=xpifile.name)
                    bundle.save()
                    messages = bundle.messages
                except:
                    messages = ["ERROR importing translations from XPI file"]
            elif form.cleaned_data['bzid']:
                try:
                    tar = StringIO.StringIO(urllib2.urlopen(
                        BZ_URL % form.cleaned_data['bzid']).read())
                    bundle = TarBundle(tar, project)
                    bundle.save()
                    messages = bundle.messages
                except:
                    messages = ["ERROR importing translations from BabelZilla"]
    else:
        form = ImportForm()

    return direct_to_template(request, 'moz_import.html', {
        'form': form,
        'project': project,
        'moz_import': True,
        'work_messages': messages,
        })


import zipfile
from cStringIO import StringIO
from django.http import HttpResponse

def release_language_download(request, project_slug, release_slug, lang_code, skip=False):
    """
    Download all resources in given release/language in one handy ZIP file
    """
    project = get_object_or_404(Project, slug=project_slug)
    release = get_object_or_404(Release, slug=release_slug, project=project)
    language = get_object_or_404(Language, code=lang_code)

    response = HttpResponse(mimetype='application/zip')
    response['Content-Disposition'] = 'filename=%s_%s.zip' % (release_slug, lang_code)

    buffer = StringIO()
    zip = zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED)
    for resource in Resource.objects.filter(releases=release):
        template = _compile_translation_template(resource, language, skip)
        zip.writestr(resource.name, template)

    zip.close()
    buffer.flush()

    ret_zip = buffer.getvalue()
    buffer.close()
    response.write(ret_zip)
    return response


def release_download(request, project_slug, release_slug, skip=False):
    """
    Download all resources in given release in one handy ZIP file
    """
    project = get_object_or_404(Project, slug=project_slug)
    release = get_object_or_404(Release, slug=release_slug, project=project)

    response = HttpResponse(mimetype='application/zip')
    response['Content-Disposition'] = 'filename=%s.zip' % release_slug

    resources = Resource.objects.filter(releases=release)
    buffer = StringIO()
    zip = zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED)
    for stat in RLStats.objects.select_related('language'
                        ).by_release_aggregated(release):
        for resource in resources:
            template = _compile_translation_template(resource, stat.object, skip)
            zip.writestr("%s/%s" % (stat.object.code, resource.name), template)

    zip.close()
    buffer.flush()

    ret_zip = buffer.getvalue()
    buffer.close()
    response.write(ret_zip)
    return response

from transifex.resources.formats import get_i18n_handler_from_type

def _compile_translation_template(resource=None, language=None, skip=False):
    """
    Given a resource and a language we create the translation file
    """
    parser = get_i18n_handler_from_type(resource.i18n_type)
    handler = parser(resource=resource, language=language)
    handler.compile(skip=skip)
    return handler.compiled_template
