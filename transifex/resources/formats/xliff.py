# -*- coding: utf-8 -*-

"""
XLIFF file parser for Python

see http://docs.oasis-open.org/xliff/v1.2/os/xliff-core.htm for documentation
of XLIFF format
"""

from __future__ import absolute_import
import re, collections
import xml.dom.minidom
import xml.parsers.expat
from copy import copy
from xml.sax.saxutils import escape as xml_escape
from django.utils.translation import ugettext, ugettext_lazy as _
from django.db.models import get_model
from transifex.txcommon.log import logger
from transifex.txcommon.exceptions import FileCheckError
from transifex.languages.models import Language
from .core import Handler, ParseError, CompileError
from .compilation import PluralCompiler, SimpleCompilerFactory
from .resource_collections import StringSet, GenericTranslation
from .utils.decorators import *
from .utils.hash_tag import hash_tag, escape_context, hash_regex,\
        pluralized_hash_regex, _HashRegex

# Resources models
Resource = get_model('resources', 'Resource')
Translation = get_model('resources', 'Translation')
SourceEntity = get_model('resources', 'SourceEntity')
Template = get_model('resources', 'Template')

plural_regex = _HashRegex(plurals=True).plural_regex

class XliffParseError(ParseError):
    pass


class XliffCompileError(CompileError):
    pass


plural_id_regex = re.compile(r'.+\[\d\]')

class XliffCompiler(PluralCompiler):
    """Compiler for xliff files."""

    def getElementByTagName(self, element, tagName, noneAllowed = False):
        elements = element.getElementsByTagName(tagName)
        if not noneAllowed and not elements:
            raise XliffCompileError(_("Element '%s' not found!" % tagName))
        if len(elements) > 1:
            raise XliffCompileError(_("Multiple '%s' elements found!" % tagName))
        return elements[0]

    def get_plural_index(self, count, rule):
        return count

    def _apply_translations(self, translations, text):
        if isinstance(text, str):
            text = text.decode('UTF-8')
        regex = pluralized_hash_regex()
        return regex.sub(
            lambda m: translations.get(m.group(0), m.group(0)), text
        )

    def _update_plural_hashes(self, translations, content):
        """Modify template content to handle plural data in target language"""
        i18n_type = self.resource.i18n_type
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        doc = xml.dom.minidom.parseString(content)
        root = doc.documentElement
        source_language = self.resource.source_language
        rules = self.language.get_pluralrules_numbers()
        source_rules = source_language.get_pluralrules_numbers()
        if self.language == self.resource.source_language:
            return content
        for group_node in root.getElementsByTagName("group"):
            if group_node.attributes.has_key('restype') and \
                    group_node.attributes['restype'].value == "x-gettext-plurals":
                trans_unit_nodes = group_node.getElementsByTagName("trans-unit")
            else:
                continue
            cont = False
            for n, node in enumerate(trans_unit_nodes):
                node_id = node.attributes.get('id') and\
                        node.attributes.get('id').value
                try:
                    target = self.getElementByTagName(node, 'target')
                except XliffCompileError, e:
                    cont = True
                    break
                if target:
                    target_text = target.firstChild.data or ''
                    if not plural_regex.match(target_text):
                        cont = True
                        break
                if n == 0:
                    id_text = node_id[:-3]
                else:
                    if id_text != node_id[:-3]:
                        cont = True
                        break
            if n != len(source_rules) - 1:
                continue
            if cont:
                continue
            for count,rule in enumerate(rules):
                index = self.get_plural_index(count, rule)
                if rule in source_rules:
                    clone = trans_unit_nodes[source_rules.index(rule)
                            ]
                else:
                    clone = trans_unit_nodes[source_rules.index(5)
                            ].cloneNode(deep=True)
                target = self.getElementByTagName(clone, "target")
                clone.setAttribute("id", id_text + '[%d]'%count)
                target.firstChild.data = target.firstChild.data[:-1] +\
                        '%d' % index
                if rule not in source_rules:
                    for n, r in enumerate(source_rules):
                        if rule < r:
                            break
                    indent_node = trans_unit_nodes[
                            n].previousSibling.cloneNode(deep=True)
                    group_node.insertBefore(
                        indent_node, trans_unit_nodes[n].previousSibling)
                    group_node.insertBefore(
                            clone, trans_unit_nodes[n].previousSibling)
        content = doc.toxml()
        return content

    def _post_compile(self):
        super(XliffCompiler, self)._post_compile()
        doc = xml.dom.minidom.parseString(
            self.compiled_template.encode('UTF-8')
        )
        root = doc.documentElement
        for node in root.getElementsByTagName("target"):
            value = ""
            for child in node.childNodes:
                value += child.toxml()
            if not value.strip() or self.language == self.resource.source_language:
                parent = node.parentNode
                parent.removeChild(node.previousSibling)
                parent.removeChild(node)
        self.compiled_template = doc.toxml()


class XliffHandler(SimpleCompilerFactory, Handler):
    name = "XLIFF *.XLF file handler"
    format = "XLIFF files (*.xlf)"
    method_name = 'XLIFF'
    format_encoding = 'UTF-8'

    HandlerParseError = XliffParseError
    HandlerCompileError = XliffCompileError

    CompilerClass = XliffCompiler

    def _get_context(self, trans_unit_node, context):
        return context

    def _getText(self, nodelist):
        rc = []
        for node in nodelist:
            if hasattr(node, 'data'):
                rc.append(node.data)
            else:
                rc.append(node.toxml())
        return ''.join(rc)

    def _serialize_occurrences(self, occurrences):
        """Serialize the occurrences list for saving to db."""
        return ', '.join(
            [':'.join([i for i in t ]) for t in occurrences]
        )

    def _parse(self, is_source, lang_rules):
        """
        Parses XLIFF file and exports all entries as GenericTranslations.
        """
        resource = self.resource

        context = []
        content = self.content.encode('utf-8')
        try:
            self.doc = xml.dom.minidom.parseString(content)
            root = self.doc.documentElement

            if root.tagName != "xliff":
                raise XliffParseError(_("Root element is not 'xliff'"))
            if not root.attributes.get('version', None):
                raise self.HandlerParseError(_("Root element 'xliff' "\
                        "does not have a 'version' attribute"))
            for node in root.childNodes:
                if node.nodeType == node.ELEMENT_NODE and \
                        node.localName == "file":
                    self.parse_tag_file(node, is_source)
        except Exception, e:
            raise self.HandlerParseError(e.message)

        return self.doc.toxml()

    def parse_tag_file(self, file_node, is_source=False):
        self.trans_unit_id_list = []
        xliff_source_language_code = file_node.attributes.get(
                'source-language').value
        source_language = Language.objects.by_code_or_alias_or_none(
                xliff_source_language_code)
        original = file_node.attributes.get('original').value
        datatype = file_node.attributes.get('datatype').value
        target_language_node = file_node.attributes.get('target-language')
        xliff_target_language_code = target_language_node and\
                target_language_node.value or ''
        target_language = Language.objects.by_code_or_alias_or_none(
                xliff_target_language_code)
        if self.resource and source_language != self.resource.source_language:
            raise self.HandlerParseError(_("Source language code "\
                "'%(source_lang_code)s' in XLIFF file does not map to "\
                "source language for the resource: "\
                "'%(resource_source_language)s'.") % {
                    'source_lang_code': xliff_source_language_code,
                    'resource_source_language': self.resource.source_language
                })
        if target_language and target_language != self.language:
            raise self.HandlerParseError(_("Target language code "\
                "'%(target_lang_code)s' in XLIFF file does not map "\
                "to the translation language: '%(translation_language)s'"\
                " for which it was uploaded.") % {
                    'target_lang_code': xliff_target_language_code,
                    'translation_language': self.language
                })
        context = [original, source_language, datatype]
        for node in file_node.childNodes:
            if node.nodeType == node.ELEMENT_NODE and node.localName == "body":
                self.parse_tag_body(node, is_source, context=copy(context))

    def parse_tag_body(self, body_node, is_source=False, context=[]):
        for node in body_node.childNodes:
            if node.nodeType == node.ELEMENT_NODE and node.localName == "group":
                self.parse_tag_group(node, is_source, context=copy(context),
                        occurrence=[])
            if node.nodeType == node.ELEMENT_NODE and node.localName == "trans-unit":
                self.parse_tag_trans_unit(node, is_source, context=copy(context),
                        occurrence=[])
            # there is no way to handle bin-unit in transifex

    def parse_tag_group(self, group_node, is_source=False, context=[],
            comment=[], occurrence=[]):
        if is_source:
            for node in group_node.childNodes:
                if node.nodeType == node.ELEMENT_NODE and node.localName == "context-group":
                    # context-group has to be in XML before occurence of trans-unit, so it
                    # is ok to populate context this way
                    occurrence.extend(self.parse_tag_context_group(node))
                if node.nodeType == node.ELEMENT_NODE and node.localName == "note":
                    comment.extend(self.parse_tag_note(node))
        if group_node.attributes.get('restype', None) and\
                group_node.attributes['restype'].value == "x-gettext-plurals":
            pluralized = True
            nplural_file = 0
            nplural = self.language.get_pluralrules_numbers()
            nplural_names = self.language.get_pluralrules()
            plural_forms = len(nplural)
            trans_unit_nodes = []
            common_id = ''
            for node in group_node.childNodes:
                if node.nodeType == node.ELEMENT_NODE and node.localName == "trans-unit":
                    node_id = node.attributes.get('id', '').value
                    if not plural_id_regex.match(node_id):
                        return
                    if nplural_file == 0:
                        common_id = node_id[:-3]
                    else:
                        if node_id[:-3] != common_id:
                            return
                    if int(node_id[-2:-1]) != nplural_file:
                        return
                    nplural_file += 1
                    trans_unit_nodes.append(node)
            if len(trans_unit_nodes) != plural_forms:
                return
            source = ""
            target = ""
            source_node = trans_unit_nodes[nplural.index(1)
                    ].getElementsByTagName("source")[0]
            if len(source_node.childNodes)>1:
                source = self._getText(source_node.childNodes)
            else:
                source = source_node.firstChild.data
            context.extend([common_id])
            for n, node in enumerate(trans_unit_nodes):
                rule = nplural[n]
                self.parse_tag_trans_unit(node, is_source,
                        context=copy(context), occurrence=copy(occurrence),
                        source_string = source, rule=rule)
        else:
            for node in group_node.childNodes:
                if node.nodeType == node.ELEMENT_NODE and\
                        node.localName == "group":
                    self.parse_tag_group(node, is_source, context=copy(context),
                            comment=copy(comment), occurrence=copy(occurrence))
                if node.nodeType == node.ELEMENT_NODE and\
                        node.localName == "trans-unit":
                    self.parse_tag_trans_unit(node, is_source, context=copy(context),
                            comment=copy(comment), occurrence=copy(occurrence))
            # TODO prop-group, note, count-group
            # there is no way to handle bin-unit in transifex

    def parse_tag_trans_unit(self, trans_unit_node, is_source=False,
            context=[], source_string=None, rule=None,
            comment=[], occurrence=[]):
        source = ""
        trans_unit_id = trans_unit_node.attributes.get('id', None) and\
                trans_unit_node.attributes.get('id', None).value or ''
        if not rule and not trans_unit_id:
            return
        if trans_unit_id in self.trans_unit_id_list:
            return
        else:
            self.trans_unit_id_list.append(trans_unit_id)
        source_node = trans_unit_node.getElementsByTagName("source")[0]
        if len(source_node.childNodes)>1:
            for i in source_node.childNodes:
                source += i.toxml()
        else:
            source = source_node.firstChild.data
        if source_string:
            pluralized = True
        else:
            pluralized = False
            context.extend([trans_unit_id])
        for node in trans_unit_node.childNodes:
            if node.nodeType == node.ELEMENT_NODE and\
                    node.localName == "context-group" and\
                    not source_string and not rule:
                occurrence.extend(self.parse_tag_context_group(
                    node, is_source))
            elif node.nodeType == node.ELEMENT_NODE and\
                    node.localName == 'note' and not pluralized:
                comment.extend(self.parse_tag_note(node))
            # TODO prop-group, note, count-group, alt-trans
        # TODO seq-source
        context = escape_context(context)
        context = self._get_context(trans_unit_node, context)
        translation = ""
        target = None
        if trans_unit_node.getElementsByTagName("target"):
            target = trans_unit_node.getElementsByTagName('target')[0]
            if len(target.childNodes)>1:
                translation = self._getText(target.childNodes)
            else:
                if target.firstChild:
                    translation = target.firstChild.data
                else:
                    translation = u""
        else:
            translation = u""
        if is_source:
            translation = translation or source
            if pluralized:
                source = source_string
            if not target:
                target = self.doc.createElement("target")
            target.childNodes = []
            if source_string and rule:
                target.appendChild(self.doc.createTextNode(
                    ("%(hash)s_pl_%(rule)s" % {'hash': hash_tag(
                        source_string, context),
                        'rule':self.language.get_pluralrules_numbers().index(
                            rule)})
                ))
            else:
                target.appendChild(self.doc.createTextNode(
                        ("%(hash)s_tr" % {'hash': hash_tag(
                            source, context)})
                ))
            if translation and not translation.strip():
                return
            indent_node = source_node.previousSibling.cloneNode(True)
            if source_node.nextSibling:
                trans_unit_node.insertBefore(target, source_node.nextSibling)
                trans_unit_node.insertBefore(indent_node, source_node.nextSibling)
            else:
                trans_unit_node.appendChild(indent_node)
                trans_unit_node.appendChild(target)
        else:
            if pluralized:
                source = source_string
            if not translation:
                return
            # TODO - do something with inline elements

        occurrence = list(set(occurrence))
        if not is_source and not pluralized:
            if trans_unit_node.attributes.get('approved', None) and\
                    trans_unit_node.attributes.get(
                            'approved').value == 'no':
               self._add_suggestion_string(
                    source, translation, context=context,
                    occurrences=self._serialize_occurrences(occurrence)
               )
               return
        if pluralized:
            self.stringset.add(GenericTranslation(
                    source, translation, context=context,
                    rule=rule, pluralized=True,
                    occurrences=self._serialize_occurrences(occurrence),
                    comment='\n'.join(comment)
             ))
        else:
            self.stringset.add(GenericTranslation(
                    source, translation, context=context,
                    occurrences=self._serialize_occurrences(occurrence),
                    comment='\n'.join(comment)
             ))

    def parse_tag_context_group(self, context_group_node, is_source=False):
        result = []
        if context_group_node.attributes.get('purpose', '') and \
                context_group_node.attributes.get(
                        'purpose', '').value == 'location':
            sourcefile = ''
            linenumber = ''
            for node in context_group_node.childNodes:
                if node.nodeType == node.ELEMENT_NODE and\
                        node.localName == "context":
                    if node.attributes.get('context-type', '') and \
                            node.attributes.get('context-type', '').value ==\
                            'sourcefile':
                        sourcefile = self.parse_tag_context(node)
                    elif node.attributes.get('context-type', '') and \
                            node.attributes.get('context-type', '').value ==\
                            'linenumber':
                        linenumber = self.parse_tag_context(node)
                if sourcefile and linenumber:
                    result.append((sourcefile, linenumber))
        return result

    def parse_tag_context(self, context_node):
        content =  self._getText(context_node.childNodes)
        context_type = context_node.attributes.get('context-type','') and\
                context_node.attributes.get('context-type','').value or ''
        return content

    def parse_tag_note(self, note_node):
        if note_node.attributes.get('from', '') and \
                note_node.attributes.get('from', '').value == 'developer':
            note =  self._getText(note_node.childNodes)
            if note:
                return [note]
        return []

    def _escape(self, s):
        return xml_escape(s, {"'": "&apos;", '"': '&quot;'})


