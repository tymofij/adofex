from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.contrib.syndication.feeds import FeedDoesNotExist, Feed as FeedClass
from django.contrib.syndication.views import Feed
from django.contrib.sites.models import Site
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.timesince import timesince

from transifex.actionlog.models import LogEntry
import re

from notification.feeds import NoticeUserFeed


class TxNoticeUserFeed(NoticeUserFeed, FeedClass):
    pass

class UserFeed(Feed):
    def get_object(self, request, username, url='feed/admin'):
        if not username:
            raise ObjectDoesNotExist
        return get_object_or_404(User, username__exact=username)

    def title(self, obj):
        return _("Recent activities by %(user)s" % {'user': obj.username })

    def description(self, obj):
        return _("Recent activities by user %s."%obj.username)

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return reverse('profile_public', args=[obj.username])

    def items(self, obj):
        return LogEntry.objects.by_user_and_public_projects(obj)

    def item_title(self, item):
        return _(item.action_type.display + ' ' + timesince(item.action_time) + ' ago.')

    def item_link(self, item):
        if not item:
            raise LogEntry.DoesNotExist
        if item.message:
            match = re.search(r'href=[\'"]?([^\'" >]+)', item.message)
            if match:
                return match.group(1)
            else:
                return '/'
        else:
            return '/'

    def item_description(self, item):
        return _(item.message or 'None')

