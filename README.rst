dnscherry
=========

.. image:: https://badges.gitter.im/Join%20Chat.svg
   :alt: Join the chat at https://gitter.im/kakwa/dnscherry
   :target: https://gitter.im/kakwa/dnscherry?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

Small cherrypy application to manage dns zone files

.. image:: https://secure.travis-ci.org/kakwa/dnscherry.png?branch=master
    :target: http://travis-ci.org/kakwa/dnscherry
    :alt: Travis CI

.. image:: https://pypip.in/d/dnscherry/badge.png
    :target: https://pypi.python.org/pypi/dnscherry
    :alt: Number of PyPI downloads

----

:PyPI: `Package <https://pypi.python.org/pypi/dnscherry>`_
:Doc: `Documentation <http://dnscherry.readthedocs.org>`_
:License: MIT
:Author: Pierre-Francois Carpentier - copyright 2014

----

Description
===========

Dnscherry is a small cherrypy application to manage dns zones.
It can add/delete records from any dns server using tsig and
dynamic updates.


Screenshots
===========

.. image:: https://raw.githubusercontent.com/kakwa/dnscherry/master/docs/assets/main_screen.png

License
=======

Dnscherry is released under the MIT public license.

Installation
============

Quick installation guide:

.. sourcecode:: bash

    $ pip install dnscherry
    
    # edit configuration according to your dns setup
    $ vim /etc/dnscherry/dnscherry.ini

    # launch dnscherryd
    dnscherryd -c /etc/dnscherry/dnscherry.ini

It should be accessible from your browser on http://localhost:8080.
