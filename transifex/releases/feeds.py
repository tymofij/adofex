from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from django.contrib.sites.models import Site
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from transifex.languages.models import Language
from transifex.projects.models import Project
from transifex.resources.models import RLStats
from transifex.releases.models import Release

current_site = Site.objects.get_current()

class ReleaseFeed(Feed):
    """
    A feed for all the languages for this release.
    """

    def get_object(self, bits):
        if len(bits) != 2:
            raise ObjectDoesNotExist
        project_slug, release_slug = bits
        self.project = get_object_or_404(Project,
                                         slug__exact=project_slug)
        self.release = get_object_or_404(Release, slug__exact=release_slug,
                                         project__id=self.project.pk)
        return self.release

    def title(self, obj):
        return _("%(site_name)s: %(project)s :: %(release)s release") % {
            'site_name': current_site.name,
            'project': self.project.name,
            'release': obj.name,}

    def description(self, obj):
        return _("Translation statistics for all languages against "
                 "%s release.") % obj.name

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def items(self, obj):
        return RLStats.objects.by_release_aggregated(self.release)

    def item_link(self, obj):
        return self.release.get_absolute_url()


class ReleaseLanguageFeed(Feed):
    """
    A feed for all the languages for this release.
    """

    def get_object(self, bits):
        if len(bits) != 3:
            raise ObjectDoesNotExist
        project_slug, release_slug, language_code = bits
        self.project = get_object_or_404(Project, slug__exact=project_slug)
        self.release = get_object_or_404(Release, slug__exact=release_slug,
                                         project__id=self.project.pk)
        self.language = get_object_or_404(Language, code__exact=language_code)

        return self.release

    def title(self, obj):
        return _("%(site_name)s: %(project)s :: %(release)s release :: %(lang)s") % {
            'site_name': current_site.name,
            'project': self.project.name,
            'release': obj.name,
            'lang': self.language.name,}

    def description(self, obj):
        return _("Translation statistics for %(lang)s language against "
                 "%(release)s release.") % {'lang': self.language.name,
                                            'release': obj.name}

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def items(self, obj):
        return RLStats.objects.by_release_and_language(self.release,
            self.language)

    def item_link(self, obj):
        return obj.resource.get_absolute_url()
