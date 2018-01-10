# -*- coding: utf-8 -*-

"""
GNU Gettext .PO/.POT file handler/compiler
"""

from __future__ import absolute_import
import os, re
import itertools
import polib
from django.conf import settings
from django.db import transaction
from django.db.models import get_model
from django.utils.translation import ugettext, ugettext_lazy as _

from django.contrib.sites.models import Site

from transifex.txcommon.commands import run_command, CommandError
from transifex.txcommon.log import logger
from transifex.teams.models import Team
from transifex.resources.formats.utils.decorators import *
from transifex.resources.formats.utils.hash_tag import hash_tag,\
        escape_context, hash_regex
from transifex.resources.models import RLStats
from transifex.resources.signals import post_save_translation
from transifex.resources.formats.core import Handler
from transifex.resources.formats.exceptions import CompileError, ParseError
from .compilation import SimpleCompilerFactory, PluralCompiler, \
        EmptyDecoratorBuilder, EmptyTranslationsBuilder
from .resource_collections import StringSet, GenericTranslation
from .utils.string_utils import split_by_newline


Resource = get_model('resources', 'Resource')
Translation = get_model('resources', 'Translation')
SourceEntity = get_model('resources', 'SourceEntity')
Template = get_model('resources', 'Template')


class PoParseError(ParseError):
    pass


class PoCompileError(CompileError):
    pass


def msgfmt_check(po_contents, ispot=False, with_exceptions=True):
    """Run a `msgfmt -c` on the file contents.

    Raise a PoParseError in case the stderror has errors/warnings or
    the command execution returns Error.
    """
    try:
        if ispot:
            command = 'msgfmt -o /dev/null --check-format --check-domain -'
        else:
            command = 'msgfmt -o /dev/null -c -'
        status, stdout, stderr = run_command(
            command, _input=po_contents.encode('UTF-8'),
            with_extended_output=True, with_exceptions=with_exceptions
        )
        # Not sure why msgfmt sends its output to stderr instead of stdout
        #if 'warning:' in stderr or 'too many errors, aborting' in stderr:
        if 'too many errors, aborting' in stderr:
            logger.warning('msgfmt %s: %s' % (status, stderr, ))
            raise CommandError(command, status, stderr)
    except CommandError, e:
        logger.warning("pofile: The 'msgfmt -c' check failed.")
        raise PoParseError, ugettext("Your file failed a correctness check "
            "(msgfmt -c). It returned the following error:\n\n%s\n\n"
            "Please run this command on "
            "your system to see the errors for yourself." % e.stderr.lstrip('<stdin>:'))


class GettextHandler(SimpleCompilerFactory, Handler):
    """
    Translate Toolkit is using Gettext C library to parse/create PO files in Python
    TODO: Switch to Gettext C library
    """
    name = "GNU Gettext *.PO/*.POT handler"
    method_name = 'PO'
    format = "GNU Gettext Catalog (*.po, *.pot)"
    copyright_line = re.compile('^# (.*?), ((\d{4}(, ?)?)+)\.?$')

    HandlerParseError = PoParseError
    HandlerCompileError = PoCompileError

    def _check_content(self, content):
        try:
            po = polib.pofile(content)
        except IOError, e:
            logger.warning("Parse error: %s" % e, exc_info=True)
            raise PoParseError(unicode(e))

        # If file is empty, the method hangs so we should bail out.
        if not content:
            logger.warning("Pofile: File '%s' is empty." % self.filename)
            raise PoParseError("Uploaded file is empty.")

        # Msgfmt check
        if settings.FILECHECKS['POFILE_MSGFMT']:
            msgfmt_check(content, self.is_pot)

        # Check required header fields
        required_metadata = ['Content-Type', 'Content-Transfer-Encoding']
        for metadata in required_metadata:
            if not metadata in po.metadata:
                logger.warning(
                    "pofile: Required metadata '%s' not found." % metadata
                )
                raise PoParseError(
                    "Uploaded file header doesn't have '%s' metadata!" % metadata
                )

        # Save to avoid parsing it again
        self._po = po

    def __init__(self, filename=None, resource=None, language=None,
                 content=None):
        super(GettextHandler, self).__init__(
            filename=filename, resource=resource, language=language,
            content=content
        )
        self.copyrights = []

    def get_po_contents(self, pofile):
        """
        This function takes a pofile object and returns its contents
        """

        # FIXME: Temporary check until a version greater than polib-0.5.3 is out.
        # Patch sent to upstream.
        def charset_exists(charset):
            """Check whether or not ``charset`` is valid."""
            import codecs
            try:
                codecs.lookup(charset)
            except LookupError:
                return False
            return True

        if not charset_exists(pofile.encoding):
            pofile.encoding = polib.default_encoding

        content = pofile.__str__()
        stripped_content = ""
        for line in content.split('\n'):
            if not self._is_copyright_line(line):
                stripped_content += line + "\n"
        return stripped_content

    def _get_compiler(self, mode=None):
        """Construct the compiler to use."""
        return self.CompilerClass(
            resource=self.resource, format_encoding=self.format_encoding
        )

    def _escape(self, s):
        """
        Escape special chars and return the given string *st*.

        **Examples**:

        >>> escape('\\t and \\n and \\r and " and \\\\')
        '\\\\t and \\\\n and \\\\r and \\\\" and \\\\\\\\'
        """
        return s.replace('\\', '\\\\')\
                .replace('\n', '\\n')\
                .replace('\t', '\\t')\
                .replace('\r', '\\r')\
                .replace('\"', '\\"')

    def _post_save2db(self, *args, **kwargs):
        """Emit a signal for others to catch."""
        kwargs.update({'copyrights': self.copyrights})
        super(GettextHandler, self)._post_save2db(*args, **kwargs)

    def _parse(self, is_source, lang_rules):
        """
        Parse a PO file and create a stringset with all PO entries in the file.
        """
        if lang_rules:
            nplural = len(lang_rules)
        else:
            nplural = self.language.get_pluralrules_numbers()

        if not hasattr(self, '_po'):
            self.is_content_valid()

        self._parse_copyrights(self.content)
        try:
            self._po = polib.pofile(self.content)
        except IOError, e:
            raise PoParseError(unicode(e))

        for entry in self._po:
            pluralized = False
            same_nplural = True

            # skip obsolete entries
            if entry.obsolete:
                continue

            # treat fuzzy translation as nonexistent
            if "fuzzy" in entry.flags:
                if not is_source:
                    if not entry.msgid_plural:
                        self._add_suggestion_string(
                            entry.msgid, entry.msgstr,
                            context=escape_context(entry.msgctxt) or '',
                            occurrences=self._serialize_occurrences(entry.occurrences)
                        )
                    continue
                else:
                    # Drop fuzzy flag from template
                    entry.flags.remove("fuzzy")

            if entry.msgid_plural:
                pluralized = True
                if is_source:
                    nplural_file = len(entry.msgstr_plural.keys())
                    if nplural_file != 2:
                        raise PoParseError("Your source file is not a POT file and"
                            " the translation file you're using has more"
                            " than two plurals which is not supported."
                        )
                    # English plural rules
                    messages = [(1, entry.msgstr_plural['0'] or entry.msgid),
                                (5, entry.msgstr_plural['1'] or entry.msgid_plural)]
                    plural_keys = [0,1]
                else:
                    message_keys = entry.msgstr_plural.keys()
                    message_keys.sort()
                    nplural_file = len(message_keys)
                    messages = []
                    if nplural:
                        if len(nplural) != nplural_file:
                            logger.warning("Passed plural rules has nplurals=%s"
                                ", but '%s' file has nplurals=%s. String '%s'"
                                "skipped." % (len(nplural), self.filename,
                                nplural_file, entry.msgid))
                            self._set_warning_message('nplural',
                                ugettext("Pluralized entries of the file were "
                                "skipped because the nplural of the upload file "
                                "differs from the nplural (%s) for the given "
                                "language available in the system." %
                                len(nplural)))
                            same_nplural = False
                    else:
                        same_nplural = False

                    if not same_nplural:
                        # Skip half translated plurals
                        continue
                        # plural_keys = message_keys

                    for n, key in enumerate(message_keys):
                        messages.append((nplural[n], entry.msgstr_plural['%s' % n]))
            else:
                # pass empty strings for non source files
                if not is_source and entry.msgstr in ["", None]:
                    continue
                # Not pluralized, so no plural rules. Use 5 as 'other'.
                if is_source:
                    messages = [(5, entry.msgstr or entry.msgid)]
                else:
                    messages = [(5, entry.msgstr)]

            # Add messages with the correct number (plural)
            for number, msgstr in enumerate(messages):
                if entry.comment:
                    comment = entry.comment
                else:
                    comment = None
                if entry.flags:
                    flags = ', '.join( f for f in entry.flags)
                else:
                    flags = None
                context=escape_context(entry.msgctxt) or ''
                self._add_translation_string(
                    entry.msgid, msgstr[1], context=context,
                    occurrences=self._serialize_occurrences(entry.occurrences),
                    rule=msgstr[0], pluralized=pluralized, comment=comment,
                    flags=flags
                )

            if is_source:
                entry.msgstr = "%(hash)s_tr" % {
                    'hash': hash_tag(entry.msgid, context)
                }

                if entry.msgid_plural:
                    for n, rule in enumerate(plural_keys):
                        entry.msgstr_plural['%s' % n] = (
                            "%(hash)s_pl_%(key)s" % {
                                'hash':hash_tag(entry.msgid, context),
                                'key':n
                            }
                        )
        return self._po

    def _generate_template(self, po):
        return self.get_po_contents(po)

    def _parse_copyrights(self, content):
        """Read the copyrights (if any) from a gettext file."""
        pass

    def _get_copyright_from_line(self, line):
        """
        Get the copyright info from the line.

        Returns (owner, year) or None.
        """
        m = self.copyright_line.search(line)
        if m is None:
            return None
        owner = m.group(1)
        years = [y.strip() for y in m.group(2).split(',')]
        return (owner, years)

    def _is_copyright_line(self, line):
        return self.copyright_line.search(line) is not None

    def _get_copyright_lines():
        pass

    def _serialize_occurrences(self, occurrences):
        """Serialize the occurrences list for saving to db."""
        return ', '.join(
            [':'.join([i for i in t ]) for t in occurrences]
        )


class GettextCompiler(PluralCompiler):
    """Base compiler for gettext files."""

    def _pre_compile(self, content):
        super(GettextCompiler, self)._pre_compile(content)
        self.po = polib.pofile(content)
        self._update_headers(po=self.po)

    def _update_headers(self, po):
        """Update the headers of a compiled po file."""
        po.metadata['Project-Id-Version'] = self.resource.project.name
        content_type = u"text/plain; charset=%s" % self.format_encoding
        po.metadata['Content-Type'] = content_type
        # The above doesn't change the charset of the actual object, so we
        # need to do it for the pofile object as well.
        po.encoding = self.format_encoding
        revision_date = self.resource.created.strftime("%Y-%m-%d %H:%M+0000")
        po.metadata['PO-Revision-Date'] = revision_date
        plurals = "nplurals=%s; plural=%s;" % (
            self.language.nplurals, self.language.pluralequation
        )
        po.metadata['Plural-Forms'] = plurals
        # The following is in the specification but isn't being used by po
        # files. What should we do?
        po.metadata['Language'] = self.language.code

        bug_tracker = self.resource.project.bug_tracker
        if bug_tracker:
            po.metadata['Report-Msgid-Bugs-To'] = bug_tracker

        if 'fuzzy' in po.metadata_is_fuzzy:
            po.metadata_is_fuzzy.remove('fuzzy')

        try:
            team = Team.objects.get(
                language=self.language,
                project=self.resource.project.outsource or self.resource.project
            )
        except Team.DoesNotExist:
            pass
        else:
            if team.mainlist:
                team_contact = "<%s>" % team.mainlist
            else:
                team_contact = "(http://%s%s)" % (
                    Site.objects.get_current().domain,
                    team.get_absolute_url()
                )
            po.metadata['Language-Team'] = "%s %s" % (
                self.language.name, team_contact
            )

        stat = RLStats.objects.by_resource(
            self.resource
        ).by_language(self.language)
        if stat and stat[0].last_committer:
            u = stat[0].last_committer
            last_translator = "%s <%s>" % (
                u.get_full_name() or u.username , u.email
            )
            po.metadata['Last-Translator'] = last_translator
            translation_revision_date = stat[0].last_update.strftime(
                "%Y-%m-%d %H:%M+0000"
            )
            po.metadata['PO-Revision-Date'] = translation_revision_date
        return po

    def _update_plural_hashes(self, translations, content):
        """Update plural hashes for the target language."""
        for entry in itertools.ifilter(lambda e: e.msgid_plural, self.po):
            plural_keys = {}
            # last rule excluding other(5)
            lang_rules = self.language.get_pluralrules_numbers()
            # Initialize all plural rules up to the last
            string_hash = hash_tag(
                entry.msgid, escape_context(entry.msgctxt) or ''
            )
            for p in range(len(lang_rules)):
                plural_keys[p] = "%s_pl_%d" %(string_hash, p)
            entry.msgstr_plural = plural_keys
        return unicode(self.po)


class PoCompiler(GettextCompiler):
    """Compiler for PO files."""

    def _post_compile(self):
        """Add copyright headers, if any.

        We first try to find where to insert those. Then, we just concatenate
        them with the rest of the text.
        """
        super(PoCompiler, self)._post_compile()
        from transifex.addons.copyright.models import Copyright
        c = Copyright.objects.filter(
            resource=self.resource, language=self.language
        ).order_by('owner')
        copyrights_inserted = False
        lines = []
        for index, line in split_by_newline(self.compiled_template):
            if line.startswith('#'):
                if not line.startswith('# FIRST AUTHOR'):
                    lines.append(line)
            elif not copyrights_inserted:
                copyrights_inserted = True
                lines.append("# Translators:")
                for entry in c:
                    lines.append(
                        '# ' + entry.owner + ', ' + entry.years_text + "."
                    )
                lines.append(line)
            else:
                lines.append(line)
                break
        lines.append(self.compiled_template[index:])
        self.compiled_template = '\n'.join(lines)


class POHandler(GettextHandler):
    """Actual PO file implementation."""

    CompilerClass = PoCompiler

    @property
    def is_pot(self):
        return False

    def _parse_copyrights(self, content):
        """Read the copyrights (if any) from a po file."""
        # TODO remove FIRST AUTHOR line
        for line in content.split('\n'):
            if not line.startswith('#'):
                break
            c = self._get_copyright_from_line(line)
            if c is not None:
                self.copyrights.append(c)


class PotCompiler(GettextCompiler):
    """Compiler for POT files."""

    def __init__(self, *args, **kwargs):
        """Always use the empty applier for POT files."""
        super(PotCompiler, self).__init__(*args, **kwargs)
        self._tset = EmptyTranslationsBuilder()
        self._tdecorator = EmptyDecoratorBuilder()

    def _set_tdecorator(self, a):
        """Don't allow to change the translations decorator."""
    translation_decorator = property(fset=_set_tdecorator)

    def _set_tset(self, t):
        """Don't allow to change the translations set builder."""
    translation_set = property(fset=_set_tset)

    def _update_headers(self, po):
        project_name = self.resource.project.name.encode(self.format_encoding)
        content_type = "text/plain; charset=%s" % self.format_encoding
        po.metadata['Project-Id-Version'] = project_name
        po.metadata['Content-Type'] = content_type
        # The above doesn't change the charset of the actual object, so we
        # need to do it for the pofile object as well.
        po.encoding = self.format_encoding
        if self.resource.project.bug_tracker:
            bug_tracker = self.resource.project.bug_tracker.encode(self.format_encoding)
            po.metadata['Report-Msgid-Bugs-To'] = bug_tracker
        return po


class POTHandler(GettextHandler):
    """Separate class for POT files, which allows extra overrides."""

    name = "GNU Gettext *.POT handler"
    method_name = 'POT'
    format = "GNU Gettext Catalog (*.po, *.pot)"

    CompilerClass = PotCompiler

    @property
    def is_pot(self):
        return True

    def _get_translation(self, string, language, rule):
        # Override to avoid a db query.
        return ""

    def _update_plural_hashes(self, translations, content):
        """no-op method."""
        return content

    def set_language(self, language):
        """Accept a language set to None.

        This is useful when trying to GET a pot file.
        """
        if language is None:
            return
        super(POTHandler, self).set_language(language)
