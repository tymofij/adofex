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
from impala.models import XpiFile

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
                    uploaded_xpi = request.FILES['xpifile']

                    filename = "%s-%s.xpi" % (project.id, project_slug)
                    saved_xpi = file(
                        os.path.join(settings.XPI_DIR,filename), "w")
                    saved_xpi.write(uploaded_xpi.read())
                    saved_xpi.close()
                    uploaded_xpi.seek(0)

                    xpi_row = XpiFile.objects.get_or_create(project=project)[0]
                    xpi_row.filename = filename
                    xpi_row.user = request.user
                    xpi_row.save()

                    bundle = XpiBundle(uploaded_xpi, project,
                                        name=uploaded_xpi.name)
                    # just in case we fail on save()
                    messages = bundle.messages
                    bundle.save()
                    messages = bundle.messages
                except:
                    messages += ["ERROR importing translations from XPI file"]
            elif form.cleaned_data['bzid']:
                try:
                    tar = StringIO.StringIO(urllib2.urlopen(
                        BZ_URL % form.cleaned_data['bzid']).read())
                    bundle = TarBundle(tar, project)
                    # just in case we fail on save()
                    messages = bundle.messages
                    bundle.save()
                    messages = bundle.messages
                except:
                    messages +=["ERROR importing translations from BabelZilla"]
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

def release_language_download(request, project_slug, release_slug,
                                                    lang_code, skip=False):
    """
    Download all resources in given release/language in one handy ZIP file
    """
    project = get_object_or_404(Project, slug=project_slug)
    release = get_object_or_404(Release, slug=release_slug, project=project)
    language = get_object_or_404(Language, code=lang_code)

    zip_buffer = StringIO()
    zip_file = zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED)
    for resource in Resource.objects.filter(releases=release):
        template = _compile_translation_template(resource, language, skip)
        zip_file.writestr(resource.name, template)

    zip_file.close()
    zip_buffer.flush()
    zip_contents = zip_buffer.getvalue()
    zip_buffer.close()

    response = HttpResponse(mimetype='application/zip')
    response['Content-Disposition'] = 'filename=%s_%s_%s.zip' % \
        (project_slug, release_slug, lang_code)
    response.write(zip_contents)
    return response


def release_language_install(request, project_slug, release_slug, lang_code):
    project = get_object_or_404(Project, slug=project_slug)
    release = get_object_or_404(Release, slug=release_slug, project=project)
    language = get_object_or_404(Language, code=lang_code)
    xpi = get_object_or_404(XpiFile, project=project)

    zip_contents = file(os.path.join(settings.XPI_DIR,xpi.filename), "r").read()
    zip_buffer = StringIO(zip_contents)
    zip_file = zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED)

    zip_file.close()
    zip_buffer.flush()
    zip_contents = zip_buffer.getvalue()
    zip_buffer.close()

    response = HttpResponse(mimetype='application/x-xpinstall')
    response['Content-Disposition'] = 'filename=%s.xpi' % project_slug
    response.write(zip_contents)
    return response


def release_download(request, project_slug, release_slug, skip=False):
    """
    Download all resources in given release in one handy ZIP file
    """
    project = get_object_or_404(Project, slug=project_slug)
    release = get_object_or_404(Release, slug=release_slug, project=project)

    resources = Resource.objects.filter(releases=release)
    zip_buffer = StringIO()
    zip_file = zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED)
    for stat in RLStats.objects.select_related('language'
                        ).by_release_aggregated(release):
        for resource in resources:
            template = _compile_translation_template(resource, stat.object, skip)
            zip_file.writestr("%s/%s" % (stat.object.code, resource.name), template)

    zip_file.close()
    zip_buffer.flush()
    zip_contents = zip_buffer.getvalue()
    zip_buffer.close()

    response = HttpResponse(mimetype='application/zip')
    response['Content-Disposition'] = 'filename=%s_%s.zip' % (project_slug, release_slug)
    response.write(zip_contents)
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
