from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import redirect_to
import authority

from userena import views as userena_views

from txcommon.forms import EditProfileForm, CustomContactForm
from txcommon.feeds import UserFeed
from txcommon.views import profile_edit as txcommon_profile_edit

# Overriding 500 error handler
handler500 = 'views.server_error'

admin.autodiscover()
authority.autodiscover()

panel_url = getattr(settings,'DJANGO_ADMIN_PANEL_URL', 'admin')

urlpatterns = patterns('',)

if settings.ENABLE_ADDONS:
    urlpatterns += patterns('', (r'', include('django_addons.urls')))

PROJECTS_URL = '^projects/'

urlpatterns += patterns('',
    url(r'^$', 'txcommon.views.index', name='transifex.home'),
    url(PROJECTS_URL, include('projects.urls')),
    url(r'^search/$', 'txcommon.views.search', name='search'),
    url(r'^%s/doc/' % panel_url, include('django.contrib.admindocs.urls')),
    url(r'^%s/' % panel_url, include(admin.site.urls)),
    url(r'^languages/', include('languages.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^ajax/', include('ajax_select.urls')),
    url(r'^ajax/', include('projects.urls.ajax')),
    url(r'^ajax/', include('resources.urls.ajax')),
    url(r'^api/', include('api.urls')),
    url(r'^tagging_autocomplete/', include('tagging_autocomplete.urls')),
    url(r'^contact/$', 'contact_form.views.contact_form',
        {'form_class': CustomContactForm}, name='contact_form'),
)

if settings.ENABLE_CONTACT_FORM:
    urlpatterns += patterns('',
        url(r'^contact/', include('contact_form.urls'), name='contact'),
    )

urlpatterns += patterns('',
        url(r'^accounts/profile/(?P<username>.+)/feed/$', UserFeed(), name='user_feed')
)

if settings.ENABLE_SIMPLEAUTH:
    urlpatterns += patterns('',
        url(r'^accounts/', include('simpleauth.urls')),)
else:
    urlpatterns += patterns('',
        # Custom EditProfileForm
        url(regex   =   r'^accounts/(?P<username>(?!signout|signup|signin)[\.\w]+)/$',
            view    =   login_required(txcommon_profile_edit),
            kwargs  =   {'edit_profile_form': EditProfileForm},
            name    =   'userena_profile_edit'),

        url(regex   =   r'^accounts/(?P<username>[\.\w]+)/password/$',
            view    =   'txcommon.views.password_change_custom',
            name    =   'password_change_redirect'),

        url(regex   =   r'^accounts/(?P<username>[\.\w]+)/email/$',
            view    =   login_required(userena_views.email_change),
            name    =   'userena_email_change'),

        url(regex   =   r'^accounts/(?P<username>[\.\w]+)/password/$',
            view    =   login_required(userena_views.password_change),
            name    =   'userena_password_change'),

        url(regex   =   r'^accounts/(?P<username>[\.\w]+)/edit/$',
            view    =   login_required(userena_views.profile_edit),
            name    =   'userena_profile_edit'),

        url(regex   =   r'^accounts/',
            view    =   include('userena.urls')),

        url(regex   =   r'^accounts/profile/(?P<username>.+)/$',
            view    =   'txcommon.views.profile_public',
            name    =   'profile_public'),
    )

if settings.USE_SOCIAL_LOGIN:
    urlpatterns += patterns('',
        url(r'^accounts/', include('social_auth.urls')),
        url(r'^accounts/(?P<username>(?!signout|signup|signin)[\.\w]+)/social/$',
            view='txcommon.views.profile_social_settings', name='profile_social_settings'),
        # Ugly, see comments in view
        url(r'^profile/social/$', 'txcommon.views.profile_social_settings_redirect',
            name='profile-social-redirect'),
    )

if settings.ENABLE_NOTICES:
    urlpatterns += patterns('',
        url(r'^notices/feed/$', 'txcommon.views.feed_for_user', name="notification_feed_for_user"),
        (r'^notices/', include('notification.urls')),
    )

if settings.SERVE_MEDIA:
    urlpatterns += patterns('',
        url(r'^site_media/media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
        url(r'^', include('staticfiles.urls'))
   )
