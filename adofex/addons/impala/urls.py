# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from django.conf import settings

from transifex.resources.urls import PROJECT_URL, RESOURCE_LANG_URL_PARTIAL
from transifex.resources.formats.compilation import Mode
from impala.forms import EditProfileForm

from django.contrib.auth.decorators import login_required
from txcommon.views import profile_edit as txcommon_profile_edit

LANG_URL = PROJECT_URL + r'l/(?P<lang_code>[\-_@\w]+)/'
RESOURCE_LANG_URL = r"^projects/"+RESOURCE_LANG_URL_PARTIAL[1:]

urlpatterns = patterns('impala.views',
    url(regex = PROJECT_URL + r'import/$',
        view = "moz_import",
        name = "moz_import"
    ),
    url(regex = PROJECT_URL + r'message/$',
        view = "message_watchers",
        name = "message_watchers"
    ),

    # Language download
    url(
        regex = LANG_URL + 'download/xpi/$',
        view = "get_translation_xpi",
        name = "download_xpi_for_use",
    ),
    url(
        regex = LANG_URL + 'download/for_use/$',
        view = "get_translation_zip",
        name = "download_zip_for_use",
    ),
    url(
        regex = LANG_URL + 'download/for_translation/$',
        view = "get_translation_zip",
        name = "download_zip_for_translation",
        kwargs = {'mode':Mode.TRANSLATED}
    ),

    # Project download
    url(
        regex = PROJECT_URL+ r'download/replaced/$',
        view = "get_all_translations_zip",
        name = "download_big_zip_replaced",
    ),
    url(
        regex = PROJECT_URL+ r'download/empty/$',
        view = "get_all_translations_zip",
        name = "download_big_zip_empty",
        kwargs = {'mode':Mode.TRANSLATED}
    ),
    url(
        regex = PROJECT_URL+ r'download/skipped/$',
        view = "get_all_translations_zip",
        name = "download_big_zip_skipped",
        kwargs = {'skip':True}
    ),

    # redefine resource download urls to make them return simple filenames
    url(regex = RESOURCE_LANG_URL+'download/for_use/$',
        view  = "get_translation_file",
        name  = "download_for_use",
        kwargs = {'mode':Mode.DEFAULT}
    ),
    url(regex = RESOURCE_LANG_URL+'download/for_translation/$',
        view  = "get_translation_file",
        name  = 'download_for_translation',
        kwargs = {'mode':Mode.TRANSLATED}
    ),
    url(regex = RESOURCE_LANG_URL+'download/reviewed/$',
        view  = "get_translation_file",
        name='download_reviewed_translation',
        kwargs={'mode':Mode.REVIEWED}
    ),

    # redefine to change form to ours
    url(regex  = r'^accounts/(?P<username>(?!signout|signup|signin)[\.\w]+)/$',
        view   = login_required(txcommon_profile_edit),
        kwargs = {'edit_profile_form': EditProfileForm},
        name   = 'userena_profile_edit'
    ),

)
