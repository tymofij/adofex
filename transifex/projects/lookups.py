from django.db.models import Q
from transifex.projects.models import Project

class ProjectsLookup(object):
    """A lookup class, used by django-ajax-select app to search Project objects."""

    def get_query(self, q, request):
        """
        Return a query set.

        You also have access to request.user if needed.
        """
        return Project.objects.for_user(request.user).filter(
                                      Q(slug__istartswith=q) |
                                      Q(name__istartswith=q))

    def format_item(self, project):
        """Simple display of an project object when displayed in the list."""
        return unicode(project)

    def format_result(self, project):
        """
        A more verbose display, used in the search results display.

        It may contain html and multi-lines.
        """
        return u"%s" % (project)

    def get_objects(self, ids):
        """Given a list of ids, return the projects ordered."""
        return Project.objects.filter(pk__in=ids).order_by('name')
