from django.conf.urls.defaults import *
from django.conf import settings
from transifex.languages.models import Language
from transifex.languages.feeds import AllLanguages
from transifex.languages.views import slug_feed

feeds = {
    'all': AllLanguages,
}

#TODO: Temporary until we import view from a common place
SLUG_FEED = 'languages.views.slug_feed'
urlpatterns = patterns('',
    url(
        regex = r'^feed/$',
        view = SLUG_FEED,
        name = 'languages_latest_feed',
        kwargs = {'feed_dict': feeds,
                  'slug': 'all'}),
)


urlpatterns += patterns('django.views.generic',
    url (
        name = 'language_list',
        regex = '^$',
        view = 'list_detail.object_list',
        kwargs = {"template_object_name" : "language",
                  'queryset': Language.objects.all()}
    ),
)
