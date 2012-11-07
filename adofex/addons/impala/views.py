# -*- ceoding: utf-8 -*-
import os, zipfile, time, shutil, urllib2
from  StringIO import  StringIO

from validator.chromemanifest import ChromeManifest

from django.conf import settings
from django.contrib import messages
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
from transifex.teams.models import Team
from transifex.resources.backends import FormatsBackend, FormatsBackendError
from transifex.resources.formats.registry import registry
from transifex.resources.formats.compilation import Mode
from transifex.projects.permissions import pr_resource_add_change, pr_project_private_perm
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
                    if ".tar" in uploaded_xpi.name:
                        # tar = StringIO(urllib2.urlopen(
                        #           BZ_URL % form.cleaned_data['bzid']).read())
                        tar = StringIO(uploaded_xpi.read())
                        bundle = TarBundle(tar, project)
                    elif ".xpi" in uploaded_xpi.name:
                        # save the file for future recompiling
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
                        # parse it for strings
                        bundle = XpiBundle(uploaded_xpi, project,
                                            name=uploaded_xpi.name)
                    else:
                        raise Exception("Unknown file type")
                    # note bundle's messages just in case we fail on save()
                    messages = bundle.messages
                    bundle.save()
                    messages = bundle.messages
                except:
                    logger.exception("ERROR importing translations from file")
                    messages += ["ERROR importing translations from file"]
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
    user_ids = list(ObservedItem.objects.filter(
        content_type=ct, object_id=project.id).values_list("user", flat=True))

    for team in Team.objects.filter(project=project):
        user_ids.extend(list(team.members.values_list("id", flat=True,)))
        user_ids.extend(list(team.coordinators.values_list("id", flat=True,)))
        user_ids.extend(list(team.reviewers.values_list("id", flat=True,)))

    users = User.objects.filter(id__in=user_ids)
    sent = False

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            send(users, "project_message", {
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
        'observing_users': users,
        'sent': sent,
        })


def get_translation_zip(request, project_slug, lang_code, mode=None):
    """
    Download all resources in given language in one ZIP file
    """
    project = get_object_or_404(Project, slug=project_slug)
    language = get_object_or_404(Language, code=lang_code)

    zip_buffer = StringIO()
    zip_file = zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED)
    for resource in Resource.objects.filter(project=project):
        template = _compile_translation_template(resource, language, mode)
        zip_file.writestr(resource.name, template)

    zip_file.close()
    zip_buffer.flush()
    zip_contents = zip_buffer.getvalue()

    response = HttpResponse(mimetype='application/zip')
    response['Content-Disposition'] = 'filename=%s_%s.zip' % \
        (project_slug, lang_code)
    response.write(zip_contents)
    return response

def get_all_translations_zip(request, project_slug, mode=None, skip=None):
    """
    Download all resources/languages in given project in one big ZIP file
    """
    project = get_object_or_404(Project, slug=project_slug)
    resources = Resource.objects.filter(project=project)
    zip_buffer = StringIO()
    zip_file = zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED)
    for stat in RLStats.objects.for_user(request.user).by_project_language_aggregated(project):
        for resource in resources:
            template = _compile_translation_template(resource, stat.object, mode, skip)
            zip_file.writestr("%s/%s" % (stat.object.code, resource.name), template)

    zip_file.close()
    zip_buffer.flush()
    zip_contents = zip_buffer.getvalue()

    response = HttpResponse(mimetype='application/zip')
    response['Content-Disposition'] = 'filename=%s.zip' % (project_slug)
    response.write(zip_contents)
    return response


def get_translation_xpi(request, project_slug, lang_code):
    """ Compile project's XPI in given language
    """
    project = get_object_or_404(Project, slug=project_slug)
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
    for resource in Resource.objects.filter(project=project):
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


def _compile_translation_template(resource=None, language=None, mode=None, skip=None):
    """
    Given a resource and a language we create the translation file
    """
    # FIXME: doesn't work with Language from RLStats. DAFAQ?
    language = Language.objects.get(code=language.code)
    if not mode:
        mode = Mode.DEFAULT # meaning "for use"
    if not skip:
        return FormatsBackend(resource, language).compile_translation(mode=mode)

    from transifex.resources.formats.dtd import DTDHandler
    from transifex.resources.formats.mozillaproperties import MozillaPropertiesHandler
    from transifex.resources.models import Resource, SourceEntity, Translation
    handlers = {
        'DTD': DTDHandler(),
        'MOZILLAPROPERTIES': MozillaPropertiesHandler()
    }
    templates = {
        'DTD': '<!ENTITY %s "%s">',
        'MOZILLAPROPERTIES': '%s=%s',
    }
    en = Language.objects.get(code='en-US')
    res = []
    for t in Translation.objects.filter(resource=resource, language=language
        ).select_related('source_entity').order_by('source_entity__order'):
        res.append(templates[resource.i18n_type] % (t.source_entity.string, handlers[resource.i18n_type]._escape(t.string)))
    return "\n".join(res).encode('UTF-8')


# COPY: copied from resourses.views to change filename to simple
# Restrict access only for private projects (?)
# DONT allow anonymous access
@login_required
@one_perm_required_or_403(pr_project_private_perm, (Project, 'slug__exact', 'project_slug'))
def get_translation_file(request, project_slug, resource_slug, lang_code, **kwargs):
    """
    View to export all translations of a resource for the requested language
    and give the translation file back to the user.
    """
    resource = get_object_or_404(Resource, project__slug = project_slug, slug = resource_slug)
    language = get_object_or_404(Language, code=lang_code)
    try:
        fb = FormatsBackend(resource, language)
        template = fb.compile_translation(**kwargs)
    except Exception, e:
        messages.error(request, "Error compiling translation file.")
        logger.error("Error compiling '%s' file for '%s': %s" % (language, resource, str(e)))
        return HttpResponseRedirect(reverse('resource_detail',
            args=[resource.project.slug, resource.slug]),)
    response = HttpResponse(
        template, mimetype=registry.mimetypes_for(resource.i18n_method)[0]
    )
    response['Content-Disposition'] = ('attachment; filename=%s' % resource.name)
    return response