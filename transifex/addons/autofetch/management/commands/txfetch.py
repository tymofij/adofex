# -*- coding: utf-8 -*-
"""
File containing the necessary mechanics for the txlanguages management command.
"""
from optparse import make_option, OptionParser
import os.path
import sys
from django.core.management.base import (BaseCommand, LabelCommand, CommandError)
from django.db.models import get_model
from django.conf import settings

URLInfo = get_model("autofetch", "URLInfo")
Resource = get_model("resources", "Resource")

class Command(LabelCommand):
    """
    Management Command Class about resource source file updating
    """
    help = "Run this command to update resources which have provided a url"\
        " for their source\nfile. By default it updates all resources which"\
        " have auto_update set to True\nbut you can also specify the resources"\
        " you want updated by providing the project\nand resource slug."
    args = "<project_slug1.resource_slug1 project_slug1.resource_slug2>"
    option_list = LabelCommand.option_list + (
        make_option('--skip', action='store_true',
            dest='skip', default=False,
            help='Import data from a file or from the default '),
    )

    can_import_settings = True

    def handle(self, *args, **options):
        skip = options.get('skip')
        resource_urlhandlers = []
        if not args:
            resource_urlhandlers = URLInfo.objects.filter(auto_update=True)
        else:
            resources = []
            for arg in args:
                try:
                    prj, res = arg.split('.')
                    resources.extend(Resource.objects.filter(project__slug=prj,
                        slug=res) or None)
                except (ValueError, TypeError), e:
                    sys.stderr.write((u"No matching resource was found for %s\n" % arg).encode('UTF-8'))

            resource_urlhandlers = URLInfo.objects.filter(resource__in=resources)

        num = resource_urlhandlers.count()

        if num == 0:
            sys.stderr.write("No resources suitable for updating found. Exiting...\n")
            sys.exit()

        sys.stdout.write("A total of %s resources are listed for updating.\n" % num)

        for seq, handler in enumerate(resource_urlhandlers):
            sys.stdout.write((u"Updating resource %s.%s (%s of %s)\n" %
                ( handler.resource.project.slug, handler.resource.slug, seq+1,num)).encode('UTF-8'))
            try:
                handler.update_source_file()
            except Exception, e:
                sys.stderr.write((u"Error updating source file for resource %s.%s\n" %
                    ( handler.resource.project.slug, handler.resource.slug)).encode('UTF-8'))
                sys.stderr.write("Exception was: %s\n" % e)
                if skip:
                    continue
                sys.stderr.write("Aborting...\n")
                sys.exit(1)
            else:
               sys.stdout.write((u"Updated source file for resource %s.%s\n" %
                    (handler.resource.project.slug, handler.resource.slug)).encode('UTF-8'))
