======================================================
    DnsCherry | Dns zones management wed interface
======================================================

|

.. image:: assets/banner.png

----

:Dev: `dnscherry source <https://github.com/kakwa/dnscherry>`_
:PyPI: `dnscherry package <http://pypi.python.org/pypi/dnscherry>`_
:License: MIT
:Author: Pierre-Francois Carpentier - copyright |copy| 2014

----

DnsCherry is a simple cherrypy application to manage dns zones.

It permits to add/delete records in one or several zones using 
Tsig hmac mechanizisms.

DnsCherry supports access controle via htpasswd files, ldap, http header, 
or any other authentification mechanizisms you can implement.

DnsCherry also provides logging of each connexion and modification threw 
syslog or directly to log files.

DnsCherry aims to be simple a simple to deploy and simple to use dns web interface.

*************
    Site Menu
*************

.. toctree::
    :maxdepth: 1
    
    install
    deploy
    auth_module
    changelog

*******************************
    Discussion / Help / Updates
*******************************

* IRC: `Freenode <http://freenode.net/>`_ ``#dnscherry`` channel
* Bugtracker: `Github <https://github.com/kakwa/dnscherry/issues>`_

----

.. image:: assets/python-powered.png
