# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django_addons.errors import AddonError
from transifex.txcommon.log import logger
from transifex.projects.permissions.project import ProjectPermission
from transifex.resources.models import RLStats

class LockError(AddonError):
    pass

class LockManager(models.Manager):
    def expiring(self):
        """Return list of locks that are about to expire."""
        return self.filter(
            notified = False,
            expires__lt = datetime.now() +
            timedelta(seconds=settings.LOCKS_EXPIRE_NOTIF))

    def expired(self):
        """Return list of expired locks."""
        return self.filter(
            expires__lt = datetime.now() )

    def valid(self):
        """Return list of valid locks."""
        return self.filter(expires__gt = datetime.now() )

    def get_valid(self, resource, language):
        """
        Return valid (not expired) lock for the given resource and language.
        """
        try:
            return self.valid().get(rlstats__resource=resource,
                rlstats__language=language)
        except Lock.DoesNotExist:
            return None

    def get_or_none(self, resource, language):
        """
        Return lock for the given resource and language.
        """
        try:
            return self.get(rlstats__resource=resource,
                rlstats__language=language)
        except Lock.DoesNotExist:
            return None

    def create_update(self, resource, language, user):
        """
        Create new or update existing lock object for the given resource and
        language

        * Checks whether 'user' has permissions to create the lock.
        * Checks whether 'user' has reached max number of locks.
        * Checks whether the given resource and language was already locked
          by someone else.
        """

        # Permission check
        if not Lock.can_lock(resource, language, user):
            raise LockError(_("User '%(user)s' has no permission to submit "
               "translations for '%(resource)s' to '%(language)s'.") % {
               "user" : user, "resource" : resource, "language": language})

        now = datetime.now()

        # Lock limit check
        if settings.LOCKS_PER_USER != None:
            locks = self.filter(
                owner = user,
                expires__gt = now)
            if len(locks) >= settings.LOCKS_PER_USER:
                raise LockError(_("User '%(user)s' already has maximum "
                "allowed %(locks)i locks.") % {"user" : user,
                "locks" : settings.LOCKS_PER_USER})

        expires = now + timedelta(seconds=settings.LOCKS_LIFETIME)

        rlstats, created = RLStats.objects.get_or_create(resource=resource,
            language=language)

        #Get existing lock if any, else create new one
        lock, created = self.get_or_create(rlstats=rlstats, defaults={'owner':user, 'expires':expires})
        # The new lock is not created and lock is not expired and user is not the owner
        if not created:
            if lock.expires and lock.expires > now and lock.owner != user:
                raise LockError(_("This resource language is already locked "
                    "by '%s'") % lock.owner)
            else:
                # Overwrite old owner
                lock.owner = user
            # Update expiration date
            lock.expires = expires

        # Set notified flag to False meaning that expiration notification
        # has not been sent about this lock yet
        lock.notified = False
        lock.save()
        return lock

class Lock(models.Model):
    """
    A lock/hold a Resource's language.

    This usually denotes something that someone is working on and shouldn't
    be touched by others.
    """
    enabled = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    modified = models.DateTimeField(auto_now=True, editable=False)
    notified = models.BooleanField(default=False, help_text="Whether "
        "the owner was notified that the lock expired")
    expires = models.DateTimeField(help_text="Time the lock expired.")

    # ForeignKeys
    owner = models.ForeignKey(User)
    rlstats = models.OneToOneField('resources.RLStats', null=False, blank=False,
        related_name='lock')

    # Managers
    objects = LockManager()

    def __unicode__(self):
        return u"%(rlstats)s (%(owner)s)" % {
            'rlstats': self.rlstats,
            'owner': self.owner}

    def __repr__(self):
        return u"<Lock: %(rlstats)s (%(owner)s)>" % {
            'rlstats': self.rlstats,
            'owner': self.owner}

    class Meta:
        db_table = 'addons_locks_lock'
        unique_together = ('rlstats',)
        ordering  = ('-created',)
        get_latest_by = 'created'

    def can_unlock(self, user):
        """
        Perform permission check whether 'user' can unlock the Lock instance.
        """
        perm = ProjectPermission(user)
        return (self.owner == user) or perm.coordinate_team(
            project=self.rlstats.resource.project, language=self.rlstats.language)

    @staticmethod
    def can_lock(resource, language, user):
        """
        Perform permission check whether 'user' can create a Lock.

        CAUTION: It does not perform lock counting check!
        """
        perm = ProjectPermission(user)
        if resource.accept_translations and (
            perm.submit_translations(resource.project, language) or
            perm.coordinate_team(project=resource.project, language=language)):
            return True
        return False

    def delete_by_user(self, user, *args, **kwargs):
        """
        Delete the instance of Lock whether the 'user' has permission to do so.
        """
        if not self.can_unlock(user):
            raise LockError(_("User '%(user)s' is not allowed to remove "
                "lock '%(lock)s'") % { "user" : user, "lock" : self})
        return super(Lock, self).delete(*args, **kwargs)

    def valid(self):
        """Return True if lock is valid. Not expired."""
        return self.expires >= datetime.now()
