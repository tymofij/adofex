from django.http import HttpResponse

class BAD_REQUEST(HttpResponse):
    """
    A class extending HttpResponse for creating user friendly error messages
    on HTTP 400 errors from the API.
    """
    def __init__(self, content='',status=400,content_type="text/plain"):
        super(BAD_REQUEST, self).__init__(content=content, status=status,
            content_type=content_type)


class FORBIDDEN_REQUEST(HttpResponse):
    """
    A class extending HttpResponse for creating user friendly error messages
    on HTTP 403 errors from the API.
    """
    def __init__(self, content='',status=403,content_type="text/plain"):
        super(FORBIDDEN_REQUEST, self).__init__(content=content, status=status,
            content_type=content_type)

class NOT_FOUND_REQUEST(HttpResponse):
    """
    A class extending HttpResponse for creating user friendly error messages
    on HTTP 404 errors from the API.
    """
    def __init__(self, content='',status=404,content_type="text/plain"):
        super(NOT_FOUND_REQUEST, self).__init__(content=content, status=status,
            content_type=content_type)
