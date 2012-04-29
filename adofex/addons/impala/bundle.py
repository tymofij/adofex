from django.conf import settings

import os
from validator.xpi import XPIManager
from validator.chromemanifest import ChromeManifest
from StringIO import StringIO
import tarfile

from django.template.defaultfilters import slugify

from transifex.projects.models import Project
from transifex.resources.models import Resource
from transifex.languages.models import Language
from transifex.resources.formats.dtd import DTDHandler
from transifex.resources.formats.mozillaproperties import MozillaPropertiesHandler
from transifex.resources.formats.registry import registry

from django.utils.safestring import mark_safe
from django.template.defaultfilters import escape

def _get_handler(filename):
    """ Returns proper Handler to handle given filename """
    if filename[-4:] == '.dtd':
        return DTDHandler
    elif filename[-11:] == '.properties':
        return MozillaPropertiesHandler
    else: # skip it, some unknown file
        return None


class Bundle(object):
    """
    Represents a file with localizations in it, grouped by languages
    """
    def __init__(self, project=None, release=None):
        "Reads file, stores its information and guesses source"
        self.project = project
        self.release = release
        self.locales = {}
        self.resources = {}
        self.source_lang = None
        self.messages = []

    def log(self, message, style=""):
        "Logs some message"
        if style:
            message = '<span style="%s">%s</span>' % \
                (style.replace('"', r'\"'), escape(message))
            message = mark_safe(message)
        self.messages.append(message)

    def bind_project(self, project):
        "Assigns a project to the bundle"
        self.project = project

    def prepare_resources(self):
        """
        Fills in self.resources, getting them from DB or creating if needed
        requires self.project and self.source_lang to be set
        """
        for (filename, data) in self.locales[self.source_lang].items():
            Handler = _get_handler(filename)
            if not Handler:
                continue
            try:
                resource = Resource.objects.get(slug=slugify(filename),
                    project=self.project)
            except Resource.DoesNotExist:
                resource = Resource(name=filename, slug=slugify(filename),
                    project=self.project, source_language=self.source_lang,
                    i18n_method=registry.guess_method(filename))
                resource.save()
            self.resources[filename] = resource

    def _do_save(self, lang, files, is_source=False):
        """
        Does the actual saving of file list for lang
        """
        self.log("%s" % lang, "font-style:italic")
        for (filename, data) in files.items():
            # whether that file is present in source ones
            if filename not in self.resources:
                continue
            Handler = _get_handler(filename)
            handler = Handler(filename=filename, resource=self.resources[filename], language=lang, content=data)
            handler.parse_file(is_source=is_source)
            updated, added = handler.save2db(is_source=is_source)
            self.log("%s: %s updated, %s added" %
                (filename, updated, added), style="padding-left:12px" )

    def save(self):
        """
        Parses the files and saves the translations in DB
        """
        if not self.source_lang:
            self.find_source()

        if not self.resources:
            self.prepare_resources()

        # let's save English
        self._do_save(self.source_lang, self.locales[self.source_lang],
                        is_source=True)
        # and the rest
        for (lang, files) in self.locales.items():
            # we have already saved English
            if lang != self.source_lang:
                self._do_save(lang, files)


    def _get_lang(self, code):
        """
        Guesses language by its code
        Returns either exact match, or dead obvious replacement (af for af_ZA)
        """
        try:
            return Language.objects.get(code=code)
        except Language.DoesNotExist:
            try:
                lang = Language.objects.get(
                    code=code.replace("_", "-").split("-")[0])
                self.log("Locale %s SUBSTITUTED for %s" % (lang, code))
                return lang
            except Language.DoesNotExist:
                raise Language.DoesNotExist

    def find_source(self):
        """
        Finds source language.
        TODO: hmm.. that is English anyway.
        Gotta replace it with check for en-US presence
        """
        # now let's find out the source locale
        if self.locales:
            # Use the first locale by default
            self.source_lang = self.locales.keys()[0]
            # Try to find en-US, as this is where the majority of users is
            for lang in self.locales.keys():
                if lang.code in ('en-US', 'en'):
                    self.source_lang = lang
                    return
            raise Exception("Source language was not found")
        else:
            raise Exception("No locales to search for source language")


class XpiBundle(Bundle):
    """
    Represents XPI extension package
    """

    def __init__(self, filename, project=None, release=None, name=None):
        """
        Fills in a list of locales from the chrome.manifest file.
        """
        Bundle.__init__(self, project, release)
        self.xpi = XPIManager(filename, name=name)
         # here we will store managers for jarfiles
        self.jarfiles = {}
        chrome = ChromeManifest(self.xpi.read("chrome.manifest"), "manifest")
        locales = list(chrome.get_triples("locale"))

        if not locales:
            return None

        # read the list
        for locale in locales:
            code, location = locale["object"].split()

            # finding out the language of the locale
            try:
                lang = self._get_lang(code)
            except Language.DoesNotExist:
                self.log("Locale %s SKIPPED" % code, "font-weight:bold")
                continue

            # Locales can be bundled in JARs
            jarred = location.startswith("jar:")
            if jarred:
                # We just care about the JAR path
                location = location[4:]
                split_location = location.split("!", 2)
                # Ignore malformed JAR URIs.
                if len(split_location) < 2:
                    continue
                jarname, location = split_location

                # missing file mentioned
                if jarname not in self.xpi:
                    continue
                # may be we have already read this one
                if jarname in self.jarfiles:
                    package = self.jarfiles[jarname]
                else:
                    jar = StringIO(self.xpi.read(jarname))
                    package = XPIManager(jar, mode="r", name=jarname)
            else:
                package = self.xpi

            # and now we read files from there
            location = location.strip('/')
            result = {}
            for f in package.package_contents():
                f = f.strip("/")
                if f.startswith(location) and f != location:
                    result[f.split("/")[-1]] = package.read(f)

            # file with same name in different jars can get overwritten
            if lang not in self.locales:
                self.locales[lang] = result
            else:
                self.locales[lang].update(result)


class TarBundle(Bundle):
    """
    Represents .tar.gz and tar.gz localization bundles
    """

    def __init__(self, fileobject, project=None, release=None, name=None):
        """
        Fills in a list of locales from top directory names.
        """
        Bundle.__init__(self, project, release)
        self.tar = tarfile.open(fileobj=fileobject)
        # walk top dirs
        for d in [d for d in self.tar.getmembers() if d.isdir()]:
            # finding out the language of the locale
            try:
                lang = self._get_lang(d.name)
            except Language.DoesNotExist:
                self.log("Locale %s SKIPPED" % d.name, "font-weight:bold")
                continue

            self.locales[lang] = {}
            files = [f for f in self.tar.getmembers()
                if f.isfile() and f.name.startswith(d.name)]
            for f in files:
                filename = f.name.split('/')[-1]
                self.locales[lang][filename] = self.tar.extractfile(f.name)
