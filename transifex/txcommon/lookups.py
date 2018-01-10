from django.contrib.auth.models import User
from django.db.models import Q

def format_user(user):
    """
    Format user object to be displayed as username + full name if possible.
    """
    user_data = [user.username]
    
    full_name = user.get_full_name()
    if full_name:
        user_data.append(full_name)
    
    return u' - '.join(user_data)


class UsersLookup(object):
    """A lookup class, used by django-ajax-select app to search model data."""

    def get_query(self,q,request):
        """
        Return a query set.

        You also have access to request.user if needed.
        """
        return User.objects.filter(Q(username__istartswith=q) | 
            Q(first_name__istartswith=q) | Q(last_name__istartswith=q))

    def format_item(self,user):
        """Simple display of an object when displayed in the list of objects """
        return unicode(user)

    def format_result(self,user):
        """
        A more verbose display, used in the search results display.

        It may contain html and multi-lines.
        """
        return format_user(user)

    def get_objects(self,ids):
        """Given a list of ids, return the objects ordered."""
        return User.objects.filter(pk__in=ids).order_by('username','last_name')
