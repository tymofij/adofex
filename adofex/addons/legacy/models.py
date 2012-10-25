from django.db import models

class User(models.Model):
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=150)
    username = models.CharField(max_length=255, db_column='members_l_username')
    # banned = models.IntegerField(db_column='member_banned') # field not found
    date_joined_timestamp = models.IntegerField(db_column='joined')
    last_login_timestamp = models.IntegerField(db_column='last_visit')

    class Meta:
        db_table = 'ibf_members'


class Extension(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(db_column='safe_name')
    owner = models.ForeignKey(User, db_column='owner_id')
    description = models.TextField()
    filepath = models.CharField(db_column='path', max_length=255)
    homepage = models.URLField(blank=True, verify_exists=False, db_column='homepageURL')
    lastupdate = models.DateField(blank=True, null=True)
    schema = models.CharField(db_column='locale_path', max_length=255)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'extensions'


class File(models.Model):
    # aka Resource
    name = models.CharField(max_length=100)
    extension = models.ForeignKey(Extension)
    type = models.CharField(max_length=10)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'files'


class Language(models.Model):
    name = models.CharField(max_length=10)
    longname = models.CharField(max_length=100)

    def __unicode__(self):
        return self.longname

    class Meta:
        db_table = 'languages'


class String(models.Model):
    extension = models.ForeignKey(Extension, db_column='ext_id')
    file = models.ForeignKey(File)
    language = models.ForeignKey(Language)
    name = models.CharField("entity name", max_length=255)
    string = models.TextField()

    def __unicode__(self):
        return "{0}({1})".format(self.name, self.language.name)

    class Meta:
        db_table = 'strings'


class Group(models.Model):
    # aka Team
    id = models.IntegerField(primary_key=True, db_column='group_id')
    extension = models.ForeignKey(Extension, db_column='ext_id')
    language = models.ForeignKey(Language, db_column='lang_id')
    lang_name = models.CharField(max_length=10)
    members = models.ManyToManyField(User, through='Membership')

    def __repr__(self):
        return "<%s:%s>" % (self.__class__.__name__, self.lang_name)

    class Meta:
        db_table = 'wts_groups'

class Membership(models.Model):
    user = models.ForeignKey(User, db_column='member_id')
    group = models.ForeignKey(Group)
    permissions = models.CharField(max_length=1)

    class Meta:
        db_table = 'wts_group_member'
