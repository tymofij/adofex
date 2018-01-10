# -*- coding: utf-8 -*-

"""
Validators to use in model fields.
"""

from django.core.exceptions import ValidationError


def validate_http_url(url):
    """Validate that the url is for HTTP/HTTPS."""
    if not url.startswith(('http://', 'https://', )):
        raise ValidationError(u'Only HTTP and HTTPS protocols are allowed')
