from transifex.txcommon.tests.base import USER_ROLES
from transifex.txcommon.log import logger

def getitem(list, index, default=None):
    """
    Return a value from a 'list' for the given 'index' or the 'default' value.
    """
    try:
        return list[index]
    except IndexError:
        return default

def assert_status_code(unittest, response, expected_code, url, user_role):
    unittest.assertEqual(response.status_code, expected_code,
        "Status code for page '%s' was %s instead of %s for the '%s' "
        "user role. \n%s" % (url, response.status_code, expected_code,
        user_role, response))


def check_page_status(unittest, user_role, url_roles):
    """
    Check if each URL set in 'url_roles' match its status_code with the
    response code status depending on the user role. Each URL can be added to
    the 'url_roles' dictionary using a predefined structure of data.

    unittest - It's a instance of a class that inherits
        txcommon.tests.base.BaseTestCase.
    user_role - One of the user roles allowed on
        txcommon.tests.base.BaseTestCase.
    url_roles - A structured dictionary containing the url to be tested.

    Structure of 'url_roles':
        url_roles = {'<REQUEST_METHOD>:<URL>':{
            '<USER_ROLE>':(<STATUS_CODE>, <DICT_OF_ARGS>,
                <EXPECTED_CONTENTS>, <UNEXPECTED_CONTENTS>, <FOLLOW_REDIRECT>),
            (...)
            },
        }

        <REQUEST_METHOD> - Might be 'GET' or 'POST'.
        <URL> - The url that must be tested.
        <USER_ROLE> - One of the user roles allowed on
            txcommon.tests.base.BaseTestCase. At least one user
            role is required.
        <STATUS_CODE> - Code of status for the HTTP response.
        <DICT_OF_ARGS> - Arguments that might be passed to the HTTP request.
            Not required.
        <EXPECTED_CONTENTS> - A string that might be found using
            assertContains on the response contents. Not required.
        <UNEXPECTED_CONTENTS> - A string that shouldn't be found. Not required.
        <FOLLOW_REDIRECT> - If it's a redirect, follow it

    Know issues:
        <EXPECTED_CONTENTS> usually does not work with the status code 302.
    """
    if not user_role in USER_ROLES:
        unittest.fail("Unknown user role: '%s'" % user_role)

    for url, date_dict in url_roles.items():
        try:
            expected_code = date_dict[user_role][0]
            args = getitem(date_dict[user_role], 1, {})
            expected_contents = getitem(date_dict[user_role], 2, None)
            unexpected_contents = getitem(date_dict[user_role], 3, None)
            follow_redirect = getitem(date_dict[user_role], 4, False)

            client = unittest.client[user_role]

            method, url = tuple(url.split(':'))
            if method == 'GET':
                response = client.get(url, args, follow=follow_redirect)
            elif method == 'POST':
                response = client.post(url, args, follow=follow_redirect)
            else:
                unittest.fail("Unknown method request: '%s'" % role)

            assert_status_code(unittest, response, expected_code, url,
                user_role)

            if expected_contents:
                unittest.assertContains(response, expected_contents,
                    status_code=expected_code)
            if unexpected_contents:
                unittest.assertNotContains(response, unexpected_contents,
                    status_code=expected_code)
        except KeyError:
            logger.info("User role '%s' not defined for the '%s' URL." % (
                user_role, url))


def convert_url_roles(url_with_roles_as_key):
    """
    Convert url roles from a dictionary using the roles as the key to a
    dictionary using the url as key.

    'url_with_roles_as_key' is a dict in the following format:

    url_with_roles_as_key = {
        '(301, )':[
            'GET:/projects/p/project1/access/pm/add',
        ],
        '(200, {}, "Translation Teams Off")':[
            'GET:/projects/p/project1/teams/',
        ],
    }

    Output:
        {'GET:/projects/p/project1/access/pm/add': {
            'anonymous': (301,),
            'maintainer': (301,),
            'registered': (301,),
            'team_coordinator': (301,),
            'team_member': (301,),
            'writer': (301,)},
        'GET:/projects/p/project1/teams/': {
            'anonymous': (200, {}, 'Translation Teams Off'),
            'maintainer': (200, {}, 'Translation Teams Off'),
            'registered': (200, {}, 'Translation Teams Off'),
            'team_coordinator': (200, {}, 'Translation Teams Off'),
            'team_member': (200, {}, 'Translation Teams Off'),
            'writer': (200, {}, 'Translation Teams Off')}}
        }
    """
    url_keys = {}
    for url_role, urls in url_with_roles_as_key.items():
        user_roles_dict={}
        url_role = eval(url_role)
        for user_role in USER_ROLES:
            user_roles_dict.update({user_role:url_role})
        for url in urls:
            url_keys.update({url:user_roles_dict})
    return url_keys


COLORS = ['BLACK', 'RED', 'GREEN', 'YELLOW', 'BLUE', 'MAGENTA', 'CYAN', 'WHITE']

def color_text(text, color_name, bold=False):
    """
    This command can be used to colorify command line output. If the shell
    doesn't support this or the --disable-colors options has been set, it just
    returns the plain text.

    Usage:
        print "%s" % color_text("This text is red", "RED")
    """
    return '\033[%s;%sm%s\033[0m' % (
        int(bold), COLORS.index(color_name) + 30, text)

def grep(haystack, needle, ln=0, color=None):
    """Highlight needle in haystack and return a few lines around it.

    Mimic UNIX's grep method. Search for a string (needle) in a text chunk
    (haystack).

    Return a list of matches. Each match will have ln number of lines
    before and after it (similar to "grep -C NUM"). The matching line will be
    highlighted with a color from a pre-defined list.

    Examples:

    >>> grep('a\nb\na1\na2\na3', 'b', 0)
    ['b']
    >>> grep('a\nb\na1\na2\na3', 'b', 1)
    ['a\nb\na1']
    >>> grep('a\nb\na1\na2\na3', 'b', 3)
    ['a\nb\na1\na2\na3']
    >>> grep('a\nb\na1\na2\na3', 'b', 3, 'RED')
    ['a\n\x1b[0;31mb\x1b[0m\na1\na2\na3']
    >>> grep('a\nb\na1\na2\na3', 'a')
    ['a', 'a1', 'a2', 'a3']
    >>> grep('a\nb\na1\na2\na3', 'a', 1)
    ['a\nb', 'b\na1\na2', 'a1\na2\na3', 'a2\na3']

    """

    #TODO: Merge two overlapping matches together.
    #TODO: Grep for more than one possible string (joined with logical OR).
    ret = []
    lines = haystack.split()
    for i, line in enumerate(lines):
        if needle in line:
            # Before
            first_possible = i-ln
            start = first_possible if first_possible >= 0 else 0
            before = '\n'.join(lines[start:i])
            # After
            last_possible = len(lines)
            end = i+1+ln if i+1+ln <= last_possible else last_possible
            after = '\n'.join(lines[i+1:end])
            # Let's join them with newlines if needed.
            txt = '%(before)s%(match)s%(after)s' % {
                'before': before + '\n' if before else '',
                'match': color_text(lines[i], color) if color else lines[i],
                'after': '\n' + after if after else ''}
            ret.append(txt)
    return ret

def highlight_grep(resp, text, context=2):
    """Highlight matches of text in response.content and print them.

    Particularly useful in tests with the django client to find some string
    in the response body. For example::

    >>> from txcommon.tests.utils import highlight_grep
    >>> resp = self.client.get(reverse('myUrlName', args=['foo']))
    >>> highlight_grep("SearchMe!")
    """

    res = grep(resp.content, text, context, 'RED')
    print ("\n===== Matches =====================================\n" +
           "\n---------------------------------------------------\n".join(res) +
           "\n===================================================\n")

def response_in_browser(resp, halt=True):
    """Open a browser and render the response's content.

    Use it in tests to visually present the response and find what you need
    with your browser's super tools such as 'View Source' and 'Inspect Element'.

    The browser will not render static media (e.g. CSS). To achieve this, run
    a separate Django server and setup your static serving variable to an
    absolute URI (e.g. STATIC_URL = 'http://localhost:8000/site_media/).
    This will trick the temporary window to show the test's HTML with the
    static files served from the server.

    Call it as follows::

    >>> from txcommon.tests.utils import response_in_browser
    >>> resp = self.client.get(reverse('myUrlName', args=['foo']))
    >>> response_in_browser(resp)

    More info http://miniblog.glezos.com/post/3388080372/tests-browser

    """

    import tempfile, webbrowser, time
    with tempfile.NamedTemporaryFile(suffix='.html') as f:
        f.write(resp.content)
        f.flush()
        webbrowser.open(f.name)
        if halt:
            raw_input("Press a key to continue with your tests...")
        else:
            # Wait a bit to give the chance to the browser to open the file.
            time.sleep(1)

