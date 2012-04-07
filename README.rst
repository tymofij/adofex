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
    hg clone https://bitbucket.org/indifex/transifex

    pip install -r requirements.txt

2. Make sure the 'TX_ROOT' config option points to your upstream Transifex
   project directory.

   You may configure your project by editing the files in the 'settings'
   directory. Files matching the pattern ``settings/*-local.conf`` are ignored
   by Mercurial.

   Example: Create a config file to be executed before the base config file,
   and if needed, one executed afterwards. Here's an example of a
   '09-base-local.conf' file::

    TX_ROOT = '~/devel/transifex/transifex'

4. Create symlinks media in adofex pointing to transifex's media and templates::

    cd adofex
    ln -s ~/devel/transifex/transifex/static
    ln -s ~/devel/transifex/templates templates/transifex

5. Finally setup your DB, and run your project as described in the
   `Installation Instructions`_::

     ./manage.py syncdb --noinput
     ./manage.py migrate
     ./manage.py txcreatenoticetypes
     ./manage.py txlanguages
     ./manage.py mzlanguages
     ./manage.py collectstatic

   To enable registered users create projects, you have to give
   permission "Can add project" to the 'registered' group

.. _`Installation Instructions`: http://docs.transifex.org/intro/install.html

That's it!
