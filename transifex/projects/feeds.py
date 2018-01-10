from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from django.contrib.sites.models import Site
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from actionlog.models import LogEntry
from transifex.projects.models import Project

current_site = Site.objects.get_current()

class LatestProjects(Feed):
    title = _("Latest projects on %(site_name)s") % {
        'site_name': current_site.name }
    link = current_site.domain
    description = _("Updates on changes and additions to registered projects.")

    def items(self):
        return Project.public.order_by('-created')[:10]


class ProjectFeed(Feed):

    def get_object(self, bits):
        # In case of "/rss/name/foo/bar/baz/", or other such clutter,
        # check that the bits parameter has only one member.
        if len(bits) != 1:
            raise ObjectDoesNotExist
        return Project.objects.get(slug__exact=bits[0])

    def title(self, obj):
        return _("%(site_name)s: Resources in %(project)s") % {
            'site_name': current_site.name,
            'project': obj.name }

    def description(self, obj):
        return _("Latest resources in project %s.") % obj.name

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def items(self, obj):
        return obj.resources.order_by('-name')[:50]

class ProjectTimelineFeed(Feed):  

    def get_object(self, bits):
        # In case of "/rss/name/foo/bar/baz", or other such clutter
        # check that the bits parameter has only one member.
        if len(bits) != 1:
            raise ObjectDoesNotExist
        return Project.objects.get(slug__exact=bits[0])
        
    def title(self, obj):
        return _("%(site_name)s: Timeline for %(project)s") % {
            'site_name':current_site.name,
            'project':obj.name }
            
    def description(self, obj):
        return _("History of the project %s.") % obj.name
        
    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return  obj.get_absolute_url()

    def items(self, obj):
        return obj.get_action_logs()[:10]

    def item_link(self, obj):
        return obj.object.get_absolute_url()
