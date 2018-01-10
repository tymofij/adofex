from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.contrib.syndication.feeds import Feed
from django.contrib.sites.models import Site
from models import Language
from transifex.txcommon.utils import key_sort
current_site = Site.objects.get_current()

class AllLanguages(Feed):
    current_site = Site.objects.get_current()
    title = _("Languages on %(site_name)s") % {
        'site_name': current_site.name }
    link = current_site.domain
    description = _("The languages spoken on %s.") % current_site.name

    def items(self):
        return Language.objects.all()

    # FIXME: Pointing language details page link to language list page, once
    # it's disabled for now.
    def item_link(self, item):
        return reverse("language_list")
