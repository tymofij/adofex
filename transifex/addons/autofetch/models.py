import gc
from django.db import models
from django.utils.translation import ugettext_lazy as _

from transifex.resources.models import Resource
from transifex.txcommon.log import logger
from transifex.resources.formats.registry import registry

import os
import urllib2, urlparse
from uuid import uuid4


class URLInfo(models.Model):

   # URL info for remote fetching/updating
    source_file_url = models.URLField(_('Source file URL'),
        null=True, blank=True, verify_exists=True,
        help_text=_("A URL pointing to the source file of this resource"\
            " to be used for automatic updates."))
    auto_update = models.BooleanField(_("Automatically update source file"),
        default=False, help_text=_("A boolean field indicating whether the"\
        " file should be automatically updated by pulling and merging from"\
        " the given URL."))

    # Foreign keys
    resource = models.OneToOneField(Resource, verbose_name=_('Resource'),
        blank=False, null=False, related_name='url_info', unique=True,
        help_text=_("The translation resource."))

    class Meta:
        verbose_name = _('url handler')
        ordering  = ('resource',)

    def __unicode__(self):
        return "%s.%s" % (self.resource.project.slug, self.resource.slug)

    def update_source_file(self, fake=False):
        """
        Fetch source file from remote url and import it, updating existing
        entries.
        """
        try:
            source_file = urllib2.urlopen(self.source_file_url)
        except:
            logger.error("Could not pull source file for resource %s (%s)" %
                (self.resource.full_name, self.source_file_url))
            raise

        filename = ''
        if source_file.info().has_key('Content-Disposition'):
                # If the response has Content-Disposition, we try to take
                # filename from it
                content = source_file.info()['Content-Disposition']
                if 'filename' in content:
                    filename = content.split('filename')[1]
                    filename = filename.replace('"', '').replace("'", ""
                        ).replace("=", "").replace('/', '-').strip()

        if filename == '':
            parts = urlparse.urlsplit(self.source_file_url)
            #FIXME: This still might end empty
            filename = parts.path.split('/')[-1]

        try:
            if not self.resource.i18n_method:
                msg = "No i18n method defined for resource %s"
                logger.error(msg % self.resource)
                return
            parser = registry.appropriate_handler(
                self.resource, language=self.resource.source_language,
                filename=filename
            )
            language = self.resource.source_language
            content = source_file.read()
            parser.bind_content(content)
            parser.set_language(language)
            parser.bind_resource(self.resource)
            parser.is_content_valid()
            parser.parse_file(is_source=True)
            strings_added, strings_updated = 0, 0
            if not fake:
                strings_added, strings_updated = parser.save2db(is_source=True)
        except Exception,e:
            logger.error("Error importing source file for resource %s.%s (%s): %s" %
                ( self.resource.project.slug, self.resource.slug,
                    self.source_file_url, str(e)))
            raise
        finally:
            source_file.close()
            gc.collect()

        return strings_added, strings_updated
