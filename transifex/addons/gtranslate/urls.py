from django.conf.urls.defaults import *
from gtranslate.views import translate, languages

urlpatterns = patterns('',
    url('^ajax/projects/p/(?P<project_slug>[-\w]+)/autotranslate/$',
        translate, name='autotranslate_proxy'),
    url('^ajax/projects/p/(?P<project_slug>[-\w]+)/autotranslate/languages/$',
        languages, name='supported_langs'),
)