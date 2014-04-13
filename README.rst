dnscherry
=========

Small cherrypy application to manage dns zone files

.. image:: https://secure.travis-ci.org/kakwa/dnscherry.png?branch=master
    :target: http://travis-ci.org/kakwa/dnscherry
    :alt: Travis CI

.. .. image:: https://pypip.in/d/dnscherry/badge.png
..    :target: https://pypi.python.org/pypi/dnscherry
..    :alt: Number of PyPI downloads

----

:PyPI: Comming soon 
:Doc: Comming soon 
:License: MIT
:Author: Pierre-Francois Carpentier - copyright 2014

----

Description
===========

Dnscherry is a small cherrypy application to manage dns zones.
It can add/delete records from any dns server using tsig and
dynamic updates.

**It's still a work in progress.**

Screenshots
===========

.. image:: https://raw.githubusercontent.com/kakwa/dnscherry/master/docs/images/main_screen.png

License
=======

Dnscherry is released under the MIT public license.

Installation
============

Quick installation guide:

.. sourcecode:: bash

    $ python setup.py install
    
    # edit configuration according to your dns setup
    $ vim /etc/dnscherry/dnscherry.ini

    # launch dnscherryd
    dnscherryd -c /etc/dnscherry/dnscherry.ini

Now, it should be accessible from your browser.
