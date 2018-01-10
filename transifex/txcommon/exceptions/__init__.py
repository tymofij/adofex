import sys
import traceback
from django.core.mail import mail_admins
from django.conf import settings
from transifex.txcommon.log import logger

class FileCheckError(Exception):
    """Exception for file checks errors"""
    pass

def handle_exception_mailing(request, exception):
    """Handle an exception if in production mode."""
    exc_info = sys.exc_info()
    subject, message = exception_email(request, exc_info)
    if not settings.DEBUG:
        logger.debug('Sending handled exception to admins.')
        mail_admins(('%s - %s') % (subject, exception.message), message,
            fail_silently=True)

def exception_email(request, exc_info):
    """Format email subject and message for exception reporting."""
    subject = 'Error (%s IP): %s' % ((request.META.get('REMOTE_ADDR') in
        settings.INTERNAL_IPS and 'internal' or 'EXTERNAL'), request.path)
    try:
        request_repr = repr(request)
    except:
        request_repr = "Request repr() unavailable"
    message = "%s\n\n%s" % (_get_traceback(exc_info), request_repr)
    return subject, message

def _get_traceback(exc_info=None):
    """Helper function to return the traceback as a string."""
    return '\n'.join(traceback.format_exception(*(exc_info or sys.exc_info())))

def log_exception():
    '''
    Log the latest exception
    '''
    logger.error(traceback.format_exc())
