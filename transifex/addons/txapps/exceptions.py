# -*- coding: utf-8 -*-

"""
Exceptions used in TxApps.
"""


class RemoteTxAppError(Exception):
    """Exception raised when the remote TxApp returned an error."""

    def __init__(self, status_code, content, *args, **kwargs):
        self.status_code = status_code
        self.content = content

    def __unicode__(self):
        return u"TxApp error: status_code is %s, message is %s" % (
            self.status_code, self.content
        )
