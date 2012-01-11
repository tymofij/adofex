# -*- ceoding: utf-8 -*-
import os, zipfile, time, shutil, urllib2
from  StringIO import  StringIO

from validator.chromemanifest import ChromeManifest

from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.simple import direct_to_template
from django.template import RequestContext

from transifex.projects.models import Project
from transifex.resources.models import Resource
from transifex.releases.models import Release, RLStats
from transifex.languages.models import Language
from transifex.resources.formats.registry import registry
from transifex.projects.permissions import pr_resource_add_change
from transifex.txcommon.decorators import one_perm_required_or_403
from transifex.txcommon.log import logger
from notification.models import ObservedItem, send

from impala.forms import ImportForm, MessageForm
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

                    uploaded_xpi.seek(0)
                    saved_xpi.write(uploaded_xpi.read())
                    uploaded_xpi.seek(0)
                    saved_xpi.close()

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
                    logger.exception("ERROR importing translations from XPI file")
                    messages += ["ERROR importing translations from XPI file"]
            elif form.cleaned_data['bzid']:
                try:
                    tar = StringIO(urllib2.urlopen(
                        BZ_URL % form.cleaned_data['bzid']).read())
                    bundle = TarBundle(tar, project)
                    # just in case we fail on save()
                    messages = bundle.messages
                    bundle.save()
                    messages = bundle.messages
                except:
                    logger.exception("ERROR importing translations from BabelZilla")
                    messages +=["ERROR importing translations from BabelZilla"]
    else:
        form = ImportForm()

    return direct_to_template(request, 'moz_import.html', {
        'form': form,
        'project': project,
        'moz_import': True,
        'work_messages': messages,
        })



@login_required
@one_perm_required_or_403(pr_resource_add_change,
    (Project, 'slug__exact', 'project_slug'))
def message_watchers(request, project_slug):
    """
    View to send messages to project watchers
    """
    project = get_object_or_404(Project, slug=project_slug)

    ct = ContentType.objects.get(name="project")
    observing_user_ids = ObservedItem.objects.filter(
        content_type=ct, object_id=project.id).values_list("user")
    observing_users = User.objects.filter(id__in=observing_user_ids)
    sent = False

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            send(observing_users, "project_message", {
                'project': project,
                'subject': form.cleaned_data['subject'],
                'message': form.cleaned_data['message'],
                })
            sent = True
    else:
        form = MessageForm()

    return direct_to_template(request, 'message_watchers.html', {
        'form': form,
        'project': project,
        'message_watchers': True,
        'observing_users': observing_users,
        'sent': sent,
        })



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

    zip_orig = zipfile.ZipFile(os.path.join(settings.XPI_DIR,xpi.filename), "r")

    zip_buffer = StringIO()
    zip_file = zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED)

    # copy all the contents from original file except META-INF,
    # to make it unsigned
    for item in zip_orig.infolist():
        if not (item.filename.startswith('META-INF') or
                item.filename == 'chrome.manifest'):
            fn = item.filename
            data = zip_orig.read(item.filename)
            zip_file.writestr(item, data)

    # write our localization
    for resource in Resource.objects.filter(releases=release):
        template = _compile_translation_template(resource, language)
        zip_file.writestr("tx-locale/%s/%s" % (lang_code, resource.name), template)

    chrome_str = zip_orig.read("chrome.manifest")
    manifest = ChromeManifest(chrome_str, "manifest")

    zip_file.writestr("chrome.manifest", chrome_str +\
        "\nlocale %(predicate)s %(code)s tx-locale/%(code)s/\n" % {
            'predicate': list(manifest.get_triples("locale"))[0]['predicate'],
            'code': lang_code,
        })

    zip_file.close()
    zip_buffer.flush()
    zip_contents = zip_buffer.getvalue()

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

    response = HttpResponse(mimetype='application/zip')
    response['Content-Disposition'] = 'filename=%s_%s.zip' % (project_slug, release_slug)
    response.write(zip_contents)
    return response


def _compile_translation_template(resource=None, language=None, skip=False):
    """
    Given a resource and a language we create the translation file
    """
    handler = registry.handler_for(resource.i18n_method)
    handler.bind_resource(resource)
    handler.set_language(language)

    if not skip:
        # Monkey-patch handler to combine results with the source locale
        def combine_strings(source_entities, language):
            source_entities = list(source_entities)
            result = old_get_strings(source_entities, language)
            for entity in source_entities:
                if not result.get(entity, None):
                    trans = handler._get_translation(entity, source_language, 5)
                    if trans:
                        logger.debug(trans.string)
                        result[entity] = trans.string
            return result
        source_language = resource.source_language
        old_get_strings = handler._get_translation_strings
        handler._get_translation_strings = combine_strings

    handler.compile()

    if not skip:
        handler._get_translation_strings = old_get_strings

    return handler.compiled_template
