# -*- coding: utf-8 -*-
from piston.handler import BaseHandler, AnonymousBaseHandler
from piston.utils import rc, throttle
from transifex.releases.models import Release
from transifex.api.utils import BAD_REQUEST


class ReleaseHandler(BaseHandler):
    """
    Release Handler for CRUD operations.
    """

    allowed_methods = ('GET',)
    model = Release
    fields = ('slug', 'name', 'release_date', ('resources', ('slug', 'name', ('project', ('slug', )))))
    exclude = ()

    def read(self, request, project_slug, release_slug=None, api_version=1):
        """
        Get details of a release.
        """
        try:
            return Release.objects.get(
                slug=release_slug, project__slug=project_slug
            )
        except Release.DoesNotExist:
            return BAD_REQUEST(
                "Release %s.%s does not exist." % (project_slug, release_slug)
            )
