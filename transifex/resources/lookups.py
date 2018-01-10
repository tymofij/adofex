from django.db.models import Q
from transifex.resources.models import Resource

class ResourcesLookup(object):
    """
    A lookup class, used by django-ajax-select app to search Project
    Resource objects.
    """
    def get_query(self, q, request):
        """
        Return a query set.

        You also have access to request.user if needed.
        """
        return Resource.objects.for_user(request.user).filter(
                                        Q(slug__istartswith=q) |
                                        Q(name__istartswith=q) |
                                        Q(project__slug__istartswith=q) |
                                        Q(project__name__istartswith=q))

    def format_item(self, resource):
        """Simple display of an resource object when displayed in the list."""
        return unicode(resource)

    def format_result(self, resource):
        """
        A more verbose display, used in the search results display.

        It may contain html and multi-lines.
        """
        return u"%s" % (resource)

    def get_objects(self, ids):
        """Given a list of ids, return the resource objects ordered."""
        return Resource.objects.filter(pk__in=ids).order_by('name')
