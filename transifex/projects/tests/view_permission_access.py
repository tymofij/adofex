from django.utils.datastructures import SortedDict
from transifex.txcommon.tests.base import BaseTestCase
from transifex.txcommon.tests.utils import check_page_status

"""
The following variable stores the roles for testing URLs against the different
types of user access on the system.

See txcommon.tests.utils.check_page_status for more info.
"""

#Project URLs
URL_ROLES = SortedDict({
    'GET:/projects/add/':{
        'anonymous':(302,),
        'registered':(200,),
        'maintainer':(200,),
        'writer':(200,),
        'team_coordinator':(200,),
        'team_member':(200,),
        'reviewer':(200,),
        },
    'GET:/projects/feed/':{
        'anonymous':(200,),
        'registered':(200,),
        'maintainer':(200,),
        'writer':(200,),
        'team_coordinator':(200,),
        'team_member':(200,),
        'reviewer':(200,),
        },
    'GET:/projects/p/project1/':{
        'anonymous':(200,),
        'registered':(200,),
        'maintainer':(200,),
        'writer':(200,),
        'team_coordinator':(200,),
        'team_member':(200,),
        'reviewer':(200,),
        },
    'GET:/projects/p/project1/edit/':{
        'anonymous':(302,),
        'registered':(403,),
        'maintainer':(200,),
        'writer':(403,),
        'team_coordinator':(403,),
        'team_member':(403,),
        'reviewer':(403,),
        },
    'GET:/projects/p/project1/edit/access/':{
        'anonymous':(302,),
        'registered':(403,),
        'maintainer':(200,),
        'writer':(403,),
        'team_coordinator':(403,),
        'team_member':(403,),
        'reviewer':(403,),
        },
    'GET:/projects/p/project1/access/pm/add/':{
        'anonymous':(302,),
        'registered':(403,),
        'maintainer':(200,),
        'writer':(403,),
        'team_coordinator':(403,),
        'team_member':(403,),
        'reviewer':(403,),
        },
    #'POST:/projects/p/project1/access/pm/1/delete/':{
        #'anonymous':(302,),
        #'registered':(403,),
        #'maintainer':(302,),
        #'writer':(403,),
        #'team_coordinator':(403,),
        #'team_member':(403,),
        #},
    #'POST:/projects/p/project1/access/rq/1/delete/':{
        #'anonymous':(302,),
        #'registered':(403,),
        #'maintainer':(404,),
        #'writer':(403,),
        #'team_coordinator':(403,),
        #'team_member':(403,),
        #},
    #'POST:/projects/p/project1/access/rq/1/approve/':{
        #'anonymous':(302,),
        #'registered':(403,),
        #'maintainer':(302,),
        #'writer':(403,),
        #'team_coordinator':(403,),
        #'team_member':(403,),
        #},
    'GET:/projects/p/project1/delete/':{
        'anonymous':(302,),
        'registered':(403,),
        'maintainer':(200,),
        'writer':(403,),
        'team_coordinator':(403,),
        'team_member':(403,),
        'reviewer':(403,),
        },
})

# Resource URLs
URL_ROLES.update({
    'GET:/projects/p/project1/resource/resource1/':{
        'anonymous':(200,),
        'registered':(200,),
        'maintainer':(200,),
        'writer':(200,),
        'team_coordinator':(200,),
        'team_member':(200,),
        'reviewer':(200,),
        },
    'GET:/projects/p/project1/resource/resource1/edit/':{
        'anonymous':(403,),
        'registered':(403,),
        'maintainer':(200,),
        'writer':(403,),
        'team_coordinator':(403,),
        'team_member':(403,),
        'reviewer':(403,),
        },
    'GET:/projects/p/project1/resource/resource1/delete/':{
        'anonymous':(403,),
        'registered':(403,),
        'maintainer':(302,),
        'writer':(403,),
        'team_coordinator':(403,),
        'team_member':(403,),
        'reviewer':(403,),
        },
    'POST:/projects/p/project1/resource/resource1/l/pt_BR/':{
        'anonymous':(302,),
        'registered':(403,),
        'maintainer':(200,),
        'writer':(200,),
        'team_coordinator':(200,),
        'team_member':(200,),
        'reviewer':(200,),
        },
    'GET:/projects/p/project1/resource/resource1/l/pt_BR/view/':{
        'anonymous':(200,),
        'registered':(200, {}, "#stringset_table"),
        'maintainer':(200, {}, "#stringset_table"),
        'writer':(200, {}, "#stringset_table"),
        'team_coordinator':(200, {}, "#stringset_table"),
        'team_member':(200, {}, "#stringset_table"),
        'reviewer':(200, {}, "#stringset_table"),
        },
    'GET:/projects/p/project1/resource/resource1/l/pt_BR/download/for_use/':{
        'anonymous':(302,),
        'registered':(302,),
        'maintainer':(302,),
        'writer':(302,),
        'team_coordinator':(302,),
        'team_member':(302,),
        'reviewer':(302,),
        },
    'GET:/projects/p/project1/resource/resource1/l/pt_BR/download/for_translation/':{
        'anonymous':(302,),
        'registered':(302,),
        'maintainer':(302,),
        'writer':(302,),
        'team_coordinator':(302,),
        'team_member':(302,),
        'reviewer':(302,),
        },
    'GET:/projects/p/project1/resource/resource1/l/pt_BR/download/reviewed/':{
        'anonymous':(302,),
        'registered':(302,),
        'maintainer':(302,),
        'writer':(302,),
        'team_coordinator':(302,),
        'team_member':(302,),
        'reviewer':(302,),
        },
})

# Release URLs
URL_ROLES.update({
    'GET:/projects/p/project1/add-release/':{
        'anonymous':(302,),
        'registered':(403,),
        'maintainer':(200,),
        'writer':(403,),
        'team_coordinator':(403,),
        'team_member':(403,),
        'reviewer':(403,),
        },
    'GET:/projects/p/project1/r/releaseslug1/':{
        'anonymous':(200,),
        'registered':(200,),
        'maintainer':(200,),
        'writer':(200,),
        'team_coordinator':(200,),
        'team_member':(200,),
        'reviewer':(200,),
        },
    'GET:/projects/p/project1/r/releaseslug1/edit/':{
        'anonymous':(302,),
        'registered':(403,),
        'maintainer':(200,),
        'writer':(403,),
        'team_coordinator':(403,),
        'team_member':(403,),
        'reviewer':(403,),
        },
    'GET:/projects/p/project1/r/releaseslug1/delete/':{
        'anonymous':(302,),
        'registered':(403,),
        'maintainer':(302,),
        'writer':(403,),
        'team_coordinator':(403,),
        'team_member':(403,),
        'reviewer':(403,),
        },
    'GET:/projects/p/project1/r/releaseslug1/l/pt_BR/':{
        'anonymous':(200,),
        'registered':(200,),
        'maintainer':(200,),
        'writer':(200,),
        'team_coordinator':(200,),
        'team_member':(200,),
        'reviewer':(200,),
        },
})

# Team URLs
URL_ROLES.update({
    'GET:/projects/p/project1/languages/add/':{
        'anonymous':(302,),
        'registered':(403,),
        'maintainer':(200,),
        'writer':(403,),
        'team_coordinator':(403,),
        'team_member':(403,),
        'reviewer':(403,),
        },
    'GET:/projects/p/project1/language/pt_BR/':{
        'anonymous':(200,),
        'registered':(200,),
        'maintainer':(200,),
        'writer':(200,),
        'team_coordinator':(200,),
        'team_member':(200,),
        'reviewer':(200,),
        },
    'GET:/projects/p/project1/language/pt_BR/members/':{
        'anonymous':(200,),
        'registered':(200,),
        'maintainer':(200,),
        'writer':(200,),
        'team_coordinator':(200,),
        'team_member':(200,),
        'reviewer':(200,),
        },
    'GET:/projects/p/project1/language/pt_BR/edit/':{
        'anonymous':(302,),
        'registered':(403,),
        'maintainer':(200,),
        'writer':(403,),
        'team_coordinator':(200,),
        'team_member':(403,),
        'reviewer':(403,),
        },
    'GET:/projects/p/project1/language/pt_BR/delete/':{
        'anonymous':(302,),
        'registered':(403,),
        'maintainer':(200,),
        'writer':(403,),
        'team_coordinator':(403,),
        'team_member':(403,),
        'reviewer':(403,),
        },
    'POST:/projects/p/project1/language/pt_BR/request/':{
        'anonymous':(302,),
        'registered':(302,),
        'maintainer':(302,),
        'writer':(302,),
        'team_coordinator':(302,),
        'team_member':(302,),
        'reviewer':(302,),
        },
    'POST:/projects/p/project1/language/pt_BR/approve/diegobz/':{
        'anonymous':(302,),
        'registered':(403,),
        'maintainer':(404,),
        'writer':(403,),
        'team_coordinator':(404,),
        'team_member':(403,),
        'reviewer':(403,),
        },
    'POST:/projects/p/project1/language/pt_BR/deny/diegobz/':{
        'anonymous':(302,),
        'registered':(403,),
        'maintainer':(404,),
        'writer':(403,),
        'team_coordinator':(404,),
        'team_member':(403,),
        'reviewer':(403,),
        },
    'POST:/projects/p/project1/language/pt_BR/withdraw/':{
        'anonymous':(302,),
        'registered':(404,),
        'maintainer':(404,),
        'writer':(404,),
        'team_coordinator':(404,),
        'team_member':(404,),
        'reviewer':(404,),
        },
    'POST:/projects/p/project1/language/pt_BR/leave/':{
        'anonymous':(302,),
        'registered':(302,),
        'maintainer':(302,),
        'writer':(302,),
        'team_coordinator':(302,),
        'team_member':(302,),
        'reviewer':(302,),
        },
    'POST:/projects/p/project1/languages/request/':{
        'anonymous':(302,),
        'registered':(302,),
        'maintainer':(302,),
        'writer':(302,),
        'team_coordinator':(302,),
        'team_member':(302,),
        'reviewer':(302,),
        },
    'POST:/projects/p/project1/language/el/approve/':{
        'anonymous':(302,),
        'registered':(403,),
        'maintainer':(404,),
        'writer':(403,),
        'team_coordinator':(403,),
        'team_member':(403,),
        'reviewer':(403,),
        },
    'POST:/projects/p/project1/language/el/deny/':{
        'anonymous':(302,),
        'registered':(403,),
        'maintainer':(404,),
        'writer':(403,),
        'team_coordinator':(403,),
        'team_member':(403,),
        'reviewer':(403,),
        },
})



class ViewPermissionAccessTestCase(BaseTestCase):
    """
    Test if all project URLs return correct status code depending on each
    user role.
    """
    def testAnonymousUser(self):
        """Check URL access for anonymous user."""
        check_page_status(self, 'anonymous', URL_ROLES)

    def testRegisteredUser(self):
        """Check URL access for authenticated (guest) user."""
        check_page_status(self, 'registered', URL_ROLES)

    def testMaintainerUser(self):
        """Check URL access for authenticated project maintainer."""
        check_page_status(self, 'maintainer', URL_ROLES)

    def testWriterUser(self):
        """Check URL access for authenticated project writer."""
        check_page_status(self, 'writer', URL_ROLES)

    def testTeamCoordinatorUser(self):
        """Check URL access for authenticated team coordinator."""
        check_page_status(self, 'team_coordinator', URL_ROLES)

    def testTeamMemberUser(self):
        """Check URL access for authenticated team member."""
        check_page_status(self, 'team_member', URL_ROLES)

    def testReviewerUser(self):
        """Check URL access for authenticated reviewer."""
        check_page_status(self, 'reviewer', URL_ROLES)
