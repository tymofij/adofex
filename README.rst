=======================
 Transifex Adofex
=======================

Transifex Adofex still is a project to provide a web service to localize
legacy Mozilla extensions (XPI, pre-Firefox 57). It is a set of Transifex addons and few views,
and relies on forked Transifex instanse.

Installation Instructions
=========================

1. Setup Transifex fork somewhere. This can be either in your
   Python path or elsewhere::

    mkdir ~/devel
    cd ~/devel
    git git clone -b adofex git://github.com/tymofij/transifex.git

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
     ./manage.py mzcreatenoticetypes
     ./manage.py check_permissions
     ./manage.py collectstatic

   To enable registered users create projects, you have to give
   permission "Can add project" to the 'registered' group

.. _`Installation Instructions`: http://docs.transifex.org/intro/install.html

That's it!

Downloading resources
=====================

 * http://adofex.clear.com.ua/projects/p/PROJECT/download/replaced/
   (missing entities replaced with en-US)
 * http://adofex.clear.com.ua/projects/p/PROJECT/download/empty/
   (missing entities set to "")
 * http://adofex.clear.com.ua/projects/p/PROJECT/download/skipped/
   (missing entities not present at all)


Command-Line Tool
=================

Allows you interact with Adofex without visiting the site.
Adofex needs a little improved Transifex client, please see

https://github.com/tymofij/transifex-client/tree/adofex
