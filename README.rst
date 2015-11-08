DnsCherry
=========

.. image:: https://raw.githubusercontent.com/kakwa/dnscherry/master/resources/static/img/apple-touch-icon-72-precomposed.png


.. image:: https://travis-ci.org/kakwa/dnscherry.svg?branch=master
    :target: https://travis-ci.org/kakwa/dnscherry
    
.. image:: https://coveralls.io/repos/kakwa/dnscherry/badge.svg 
    :target: https://coveralls.io/r/kakwa/dnscherry

.. image:: https://img.shields.io/pypi/dm/dnscherry.svg
    :target: https://pypi.python.org/pypi/dnscherry
    :alt: Number of PyPI downloads
    
.. image:: https://img.shields.io/pypi/v/dnscherry.svg
    :target: https://pypi.python.org/pypi/dnscherry
    :alt: PyPI version

.. image:: https://readthedocs.org/projects/dnscherry/badge/?version=latest
    :target: http://dnscherry.readthedocs.org/en/latest/?badge=latest
    :alt: Documentation Status

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
