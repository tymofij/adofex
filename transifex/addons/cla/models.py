from django.contrib.auth.models import User
from django.db import models
from django.db.models import permalink
from django.db.models.signals import pre_save
from django.utils.translation import ugettext_lazy as _
from transifex.projects.models import Project

class Cla(models.Model):
    license_text = models.TextField(
        null=False,
        blank=False,
        help_text=_("This is the CLA text, keep it in markdown format.")
    )
    project = models.OneToOneField(
        Project,
        help_text=_("The project that this CLA belongs to.")
    )
    users = models.ManyToManyField(User, through='ClaSignature')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    def __unicode__(self):
        return u'CLA: %s' % self.project

    @permalink
    def get_absolute_url(self):
        return ('cla_view', None, {'project_slug': self.project.slug})

    def get_users_url(self):
        return "%susers/" % self.get_absolute_url()

def handle_cla_pre_save(sender, **kwargs):
    cla = kwargs['instance']
    try:
        old_cla = Cla.objects.get(id=cla.id)
        if old_cla.license_text != cla.license_text:
            cla.clasignature_set.all().delete()
    except Cla.DoesNotExist, e:
        pass

pre_save.connect(handle_cla_pre_save, sender=Cla)

class ClaSignature(models.Model):
    user = models.ForeignKey(User)
    cla = models.ForeignKey(Cla)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together=('user', 'cla', )

    def __unicode__(self):
        return u'%s: %s' % (self.cla, self.user)