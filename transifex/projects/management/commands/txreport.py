from django.conf import settings
from django.core.management.base import LabelCommand, CommandError
from actionlog.models import LogEntry
from notification import models as notification
from transifex.projects.models import Project
from transifex.txcommon import rst

_HELP_TEXT = """Generate reports with the statistics and action logs for a period of time,
depending on the parameters, and send it by email.

Report types::
    weekly-maintainers: Sends reports of the last week activities to the project
                        maintainers.

A project slug can be passed too, in order to generate the report only for a
specific project.

Example::
    python manage.py txreport weekly-maintainers project-foo"""


class Command(LabelCommand):
    help = (_HELP_TEXT)

    args = '[report-type [project_slug, project_slug, ...]]'

    report_types = ['weekly-maintainers',]

    # Validation is called explicitly each time the server is reloaded.
    requires_model_validation = False

    def handle(self, *args, **options):
        """Override default method to make it work without arguments."""

        if not settings.ENABLE_NOTICES:
            raise CommandError("Notifications are not enable in the system.")
        if not args:
            raise CommandError("You need to specify the report type.")
        elif not args[0] in self.report_types:
            raise CommandError("Report type invalid.")

        if len(args)==1:
            projects = Project.objects.all()
        else:
            projects = Project.objects.filter(slug__in=list(args[1:]))

        if not projects:
            raise CommandError("No project found with the given slug(s).")
        else:
            self.projects = projects
            self.report_type = args[0]

        # Find the function name to be called based on the report_type
        function_report_type = self.report_type.replace('-','_')

        #Call the related function to the wanted report_type
        self.__getattribute__(function_report_type)()

    def weekly_maintainers(self):
        for project in self.projects:
            result = project_report_weekly_maintainers(project)


def project_report_weekly_maintainers(p):

    actionlogs = LogEntry.objects.by_object_last_week(p)[:30]
    nt = 'project_report_weekly_maintainers'
    context = {'project': p,
               'actionlogs': actionlogs}

    # Send notification for maintainers
    notification.send(p.maintainers.all(), nt, context)
