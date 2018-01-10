# -*- coding: utf-8 -*-
import base64

def create_auth_string(username, password):
    """
    Initialization for client login since piston doesn't support a
    single signon and we need an explicit auth request.
    """
    credentials = base64.encodestring("%s:%s" % (username, password)).rstrip()
    auth_string = 'Basic %s' % credentials

    return auth_string

# Original stringset for POST test
ORIGINAL = {
    "strings": [
        {
            "string": "Cancel",
            "context": "lib/testpack.js:9",
            "occurrences": "lib/testpack.js:9"
        },
        {
            "string": "Next",
            "context": "lib/testpack.js:18",
            "occurrences": "lib/testpack.js:18"
        },
        {
            "string": "Cancel",
            "context": "lib/testpack.js:19",
            "occurrences": "lib/testpack.js:19"
        }
    ]
}

# Translation for PUT test
TRANSLATION = {
    "strings": [
        {
            "string": "Cancel",
            "value": "Άκυρο",
            "context": "lib/testpack.js:9",
            "occurrences": "lib/testpack.js:9"
        },
        {
            "string": "Next",
            "value": "Επόμενο",
            "context": "lib/testpack.js:18",
            "occurrences": "lib/testpack.js:18"
        },
        {
            "string": "Cancel",
            "value": "Άκυρο",
            "context": "lib/testpack.js:19",
            "occurrences": "lib/testpack.js:19"
        }
]}


