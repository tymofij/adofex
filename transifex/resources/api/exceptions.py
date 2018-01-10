# -*- coding: utf-8 -*-

"""
Exceptions related to the API operations.
"""

class BadRequestError(Exception):
    pass


class NoContentError(Exception):
    pass


class NotFoundError(Exception):
    pass

class ForbiddenError(Exception):
    pass
