from django.contrib.syndication.views import feed

from transifex.projects.models import Project
from transifex.projects.permissions import pr_project_private_perm
from transifex.txcommon.decorators import one_perm_required_or_403

# Feeds
def slug_feed(request, slug=None, param='', feed_dict=None):
    """
    Override default feed, using custom (including nonexistent) slug.

    Provides the functionality needed to decouple the Feed's slug from
    the urlconf, so a feed mounted at "^/feed" can exist.

    See also http://code.djangoproject.com/ticket/6969.
    """
    if slug:
        url = "%s/%s" % (slug, param)
    else:
        url = param
    return feed(request, url, feed_dict)


@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'param'), anonymous_access=True)
# This is used for the feeds of a specific project
def project_feed(request, slug=None, param='', feed_dict=None):
    """
    Override default feed, using custom (including nonexistent) slug.

    Provides the functionality needed to decouple the Feed's slug from
    the urlconf, so a feed mounted at "^/feed" can exist.

    See also http://code.djangoproject.com/ticket/6969.
    """
    if slug:
        url = "%s/%s" % (slug, param)
    else:
        url = param
    return feed(request, url, feed_dict)

@one_perm_required_or_403(pr_project_private_perm,
    (Project, 'slug__exact', 'param'), anonymous_access=True)
# This is used for the feeds of a specific project
def timeline_feed(request, slug=None, param='', feed_dict=None):
    """
    Override default feed, using custom (including nonexistent) slug.

    Provides the functionality needed to decouple the Feed's slug from
    the urlconf, so a feed mounted at "^/feed" can exist.

    See also http://code.djangoproject.com/ticket/6969.
    """
    if slug:
        url = "%s/%s" % (slug, param)
    else:
        url = param
    return feed(request, url, feed_dict)
