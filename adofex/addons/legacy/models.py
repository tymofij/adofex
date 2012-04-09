from django.db import models

class Extension(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(db_column='safe_name')
    owner_id = models.IntegerField()
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


