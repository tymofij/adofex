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
