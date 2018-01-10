# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from views import chart_resource_image, chart_resource_html_js,\
        chart_resource_json, chart_project_image, chart_project_html_js,\
        chart_project_html_js, chart_project_json

urlpatterns = patterns('',
    # Provide URL for static image of chart
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/chart/image_png/$',
        view = chart_resource_image,
        name = 'chart_resource_image',),
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/chart/image_png/$',
        view = chart_project_image,
        name = 'chart_project_image',),

    # Serve includable JS
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/chart/inc_js/$',
        view = chart_resource_html_js,
        name = 'chart_resource_js',
        kwargs = {"template_name": "resource_chart_js.html"}),
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/chart/inc_js/$',
        view = chart_project_html_js,
        name = 'chart_project_js',
        kwargs = {"template_name": "project_chart_js.html"}),

    # Serve HTML code which loads JS data
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/chart/$',
        view = chart_resource_html_js,
        name = 'chart_resource_html',
        kwargs = {"template_name": "resource_chart.html"}),
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/chart/$',
        view = chart_project_html_js,
        name = 'chart_project_html',
        kwargs = {"template_name": "project_chart.html"}),

    # Serve JSON data for table/chart whatever
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/resource/(?P<resource_slug>[-\w]+)/chart/json/$',
        view = chart_resource_json,
        name = 'chart_resource_json',),
    url(
        regex = '^projects/p/(?P<project_slug>[-\w]+)/chart/json/$',
        view = chart_project_json,
        name = 'chart_project_json',),
)
