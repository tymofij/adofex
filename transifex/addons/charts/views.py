# -*- coding: utf-8 -*-
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from transifex.projects.models import Project
from transifex.resources.models import Resource, RLStats
from transifex.txcommon.context_processors import site_url_prefix_processor
from transifex.txcommon.utils import key_sort

# For interactive charts:
import gviz_api

# For image charts:
from pygooglechart import StackedHorizontalBarChart, Axis

NUM_LANGS = 14

class PLStat(object):
    def __init__(self, translated_perc, language):
        self.language = language
        self.translated_perc = translated_perc

def get_sorted_stats(obj, project=False):
    if project:
        stats = []
        for i in obj:
            try:
                translated_perc = int((float(i.translated)/i.total)*100)
            except Exception, e:
                translated_perc = 0

            stats.append((translated_perc, i.object))
        stats.sort()
        stats.reverse()
        _stats = []
        for stat in stats[:NUM_LANGS]:
            _stats.append(PLStat(stat[0], stat[1]))
        return _stats
    else:
        return key_sort(obj, '-translated_perc')[:NUM_LANGS]

def get_image_url(obj, project=False):
    """
    Returns URL for the static image
    """
    height = 210

    trans = []
    fuzzy = []
    labels_left = []
    labels_right = []

    stats = get_sorted_stats(obj, project)
    for stat in stats:
        t = stat.translated_perc
        trans.append(t)
        labels_left.append(stat.language.name.encode('utf-8'))
        labels_right.append("%s%%" % t)

    labels_left.reverse()
    labels_right.reverse()

    chart = StackedHorizontalBarChart(
        width = 350,
        height = 14 + 13 * len(stats),
        x_range=(0, 100))
    chart.set_bar_width(9)
    chart.set_colours(['78dc7d', 'dae1ee', 'efefef']) # Green, dark gray, light gray
    chart.set_axis_labels(Axis.LEFT, labels_left)
    chart.set_axis_labels(Axis.RIGHT, labels_right)
    chart.add_data(trans)
    return chart.get_url()

def get_gviz_json(obj, project=False):
    """
    Returns JSON data of Google Visualization API
    """
    description = { "lang": ("string", "Language"),
                    "trans": ("number", "Translated")}
    data = []
    stats = get_sorted_stats(obj, project)
    for stat in stats:
        trans = stat.translated_perc
        data.append({
            "lang": stat.language.name,
            "trans": trans})
    data_table = gviz_api.DataTable(description)
    data_table.LoadData(data)
    return data_table.ToJSonResponse(columns_order=("lang", "trans"))

def chart_resource_image(request, project_slug, resource_slug):

    resource = get_object_or_404(Resource, slug=resource_slug,
                                    project__slug=project_slug)
    if resource.project.private:
        raise PermissionDenied
    return HttpResponseRedirect(get_image_url(RLStats.objects.by_resource(resource)))

def chart_project_image(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    if project.private:
        raise PermissionDenied
    return HttpResponseRedirect(get_image_url(
        RLStats.objects.by_project_language_aggregated(project
            ), True))

def chart_resource_html_js(request, project_slug, resource_slug, template_name):
    resource = get_object_or_404(Resource, slug=resource_slug,
                                    project__slug=project_slug)
    if resource.project.private:
        raise PermissionDenied
    return render_to_response(template_name,
        {   "project" : resource.project,
            "resource" : resource, },
        RequestContext(request, {}, [site_url_prefix_processor]))

def chart_project_html_js(request, project_slug, template_name):
    project = get_object_or_404(Project, slug=project_slug)
    if project.private:
        raise PermissionDenied
    return render_to_response(template_name,
        {"project" : project},
        RequestContext(request, {}, [site_url_prefix_processor]))

def chart_resource_json(request, project_slug, resource_slug):
    resource = get_object_or_404(Resource, slug=resource_slug,
                                    project__slug=project_slug)
    if resource.project.private:
        raise PermissionDenied
    return HttpResponse(content = get_gviz_json(
        RLStats.objects.by_resource(resource)))

def chart_project_json(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    if project.private:
        raise PermissionDenied
    return HttpResponse(content = get_gviz_json(
        RLStats.objects.by_project_language_aggregated(project
            ), True))
