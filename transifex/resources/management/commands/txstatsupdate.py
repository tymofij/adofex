# -*- coding: utf-8 -*-
from optparse import make_option, OptionParser
import os.path
import sys
from django.core.management.base import (BaseCommand, LabelCommand, CommandError)
from django.db.models import get_model
from django.conf import settings

class Command(LabelCommand):
    """
    Management Command Class about resource source file updating
    """
    help = "This command creates the necessary objects for every resource"\
           " and forces statistics to be recalculated."
    args = "<project_slug1.resource_slug1 project_slug1.resource_slug2>"

    can_import_settings = True

    def handle(self, *args, **options):

        Resource = get_model('resources', 'Resource')
        Translation = get_model('resources', 'Translation')
        Language = get_model('languages', 'Language')
        RLStats = get_model('resources', 'RLStats')
        Team = get_model('teams', 'Team')

        verbosity = int(options.get('verbosity',1))

        if not args:
            resources = Resource.objects.all()
        else:
            resources = []
            for arg in args:
                try:
                    prj, res = arg.split('.')
                    resources.extend(Resource.objects.filter(project__slug=prj,
                        slug=res) or None)
                except TypeError, e:
                    raise Exception("Unknown resource %s.%s" % (prj, res))
                except ValueError, e:
                    raise Exception("Argument %s is not in the correct format"
                        % arg)

        num = len(resources)

        if num == 0:
            sys.stderr.write("No resources suitable for updating found. Exiting...\n")
            sys.exit()


        if verbosity:
            sys.stdout.write("A total of %s resources are listed for updating.\n" % num)

        for seq, r in enumerate(resources):
            if verbosity:
                sys.stdout.write((u"Updating resource %s.%s (%s of %s)\n" %
                    ( r.project.slug, r.slug, seq+1, num)).encode('UTF-8'))

            # Update resource fields
            r.update_total_entities()
            r.update_wordcount()

            # Get a list of the available languages
            langs = list(Translation.objects.filter(
                resource=r).order_by('language').values_list(
                'language',flat=True).distinct())

            # Update stats
            for lang in langs:
                lang = Language.objects.get(id=lang)
                if verbosity:
                    sys.stdout.write("Calculating statistics for language %s.\n" % lang)
                rl, created = RLStats.objects.get_or_create(resource=r, language=lang)
                rl.update()

            if r.project.outsource:
                teams = Team.objects.filter(project=r.project.outsource)
            else:
                teams = Team.objects.filter(project=r.project)

            # Exclude all rlstats that were already created
            teams = teams.exclude(language__id__in=langs)

            for team in teams:
                lang = team.language
                # Add team languages to the existing languages
                langs.append(lang.id)
                if verbosity:
                    sys.stdout.write("Calculating statistics for team language %s.\n" % lang)
                rl,created = RLStats.objects.get_or_create(resource=r, language=lang)
                rl.update()

            # Add source language to the existing languages
            langs.append(r.source_language.id)

            # For all existing languages that don't have a translation or
            # don't have a corresponding team, delete RLStat object
            rlstats = RLStats.objects.filter(resource=r)
            for stat in rlstats:
                if not stat.language.id in langs:
                    stat.delete()
