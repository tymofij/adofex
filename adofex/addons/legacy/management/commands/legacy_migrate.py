# -*- coding: utf-8 -*-

from transifex.projects.models import Project
from transifex.languages.models import Language

from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.utils.encoding import smart_unicode
from legacy import models as legacy

class Command(BaseCommand):
    help = "Copies all data from legacy Babelzilla DB to Transifex"

    def handle(self, **options):
        from transifex.resources.models import Resource, SourceEntity, Translation
        from transifex.resources.handlers import invalidate_stats_cache

        en = Language.objects.get(code='en-US')

        try:
            Project.objects.all().delete()
        except:
            pass

        for e in legacy.Extension.objects.all():
            p = Project(slug=e.slug, name=smart_unicode(e.name), description=smart_unicode(e.description), homepage=e.homepage, source_language=en)
            p.save()
            for f in legacy.File.objects.filter(extension=e):
                r = Resource(name=f.name, project=p, slug=slugify(f.name)+str(f.id))
                r.save()
                for s in legacy.String.objects.filter(file=f, extension=e):
                    entity, created = SourceEntity.objects.get_or_create(resource=r, string=s.name)
                    try:
                        lang = Language.objects.get(code=s.language.name)
                    except Language.DoesNotExist:
                        print "Language {0} not found in TX".format(s.language.name)
                        continue
                    try:
                        Translation(string=smart_unicode(s.string), resource=r, source_entity=entity, language=lang).save()
                    except:
                        print
                        print s.id
                        print

        for r in Resource.objects.all():
            for l in Language.objects.filter(pk__in=Translation.objects.filter(resource=r).order_by('language').values_list('language', flat=True).distinct()):
                invalidate_stats_cache(r, l)