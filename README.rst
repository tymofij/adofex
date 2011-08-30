=======================
 Transifex Adofex
=======================

Transifex Adofex is a project to provide a web service to localize
Mozilla extensions. It is a set of Transifex addons and few patches
applied to Transifex itself (hopefully soon they will be merged in).

Installation Instructions
=========================

1. Setup Transifex normally somewhere. This can be either in your
   Python path or elsewhere::

    mkdir ~/devel
    cd ~/devel
    hg clone https://bitbucket.org/tymofiy/transifex

   Both requirements.txt and buildout.cfg in transifex are obsolete, refer to
   http://help.transifex.net/technical/install.html#install-dependencies
   or requirements.txt in this project.::

    pip install django==1.2.5
    pip install -r requirements.txt

   There is a bug in django-piston which makes its install with pip fail
   (__init__.py file in piston package is missing).
   See https://bitbucket.org/jespern/django-piston/issue/173/
   Tx folks recommend using their tarball and easy_install here::

    easy_install http://trac.transifex.org/files/deps/django-piston-0.2.3-devel-r278.tar.gz

2. Make sure the 'TX_ROOT' config option points to your upstream Transifex
   project directory.

   You may configure your project by editing the files in the 'settings'
   directory. Files matching the pattern ``settings/*-local.conf`` are ignored
   by Mercurial.

   Example: Create a config file to be executed before the base config file,
   and if needed, one executed afterwards. Here's an example of a
   '09-base-local.conf' file::

    TX_ROOT = '~/devel/transifex/transifex'

4. Create symlink media in adofex pointing to transifex's media::

    cd adofex
    ln -s ~/devel/transifex/transifex/media

5. Finally setup your DB, and run your project as described in the
   `Installation Instructions`_::

     ./manage.py syncdb --noinput
     ./manage.py migrate
     ./manage.py txcreatenoticetypes
     ./manage.py txlanguages
     ./manage.py mzlanguages
     ./manage.py build_static

.. _`Installation Instructions`: http://docs.transifex.org/intro/install.html

That's it!
