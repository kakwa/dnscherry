==============
  DnsCherry 
==============

Dns management web interface.

----

:Dev: `dnscherry git <https://github.com/kakwa/dnscherry>`_
:PyPI: `dnscherry package <http://pypi.python.org/pypi/dnscherry>`_
:License: MIT
:Author: Pierre-Francois Carpentier - copyright © 2014

----

*************
  Site Menu
*************

.. toctree::
    :maxdepth: 1
    
    install
    deploy
    auth_module
    changelog

****************
  Presentation
****************

DnsCherry is cherrypy application to manage dns zones.

It's main functionalities are:

* add or delete records in one or several zones (using Tsig HMAC)
* access control with htpasswd files, ldap, http header (use it behind a SSO)
* modular auth mechanisms, custom authentication modules can easily be implemented
* traces for each action (add/delete record, connexions...) through logs (syslog or files)

DnsCherry aims to be a simple to deploy and to use Dns web interface.

**************
  Screenshot
**************

.. image:: assets/main_screen.png
    :width: 600 px

*******************************
  Discussion / Help / Updates
*******************************

* IRC: `Freenode <http://freenode.net/>`_ ``#dnscherry`` channel
* Bugtracker: `Github <https://github.com/kakwa/dnscherry/issues>`_

----

.. image:: assets/python-powered.png
.. image:: assets/cherrypy.png
