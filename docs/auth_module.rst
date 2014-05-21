Auth Modules
============

Configuration
-------------

modNone
~~~~~~~

This module is used if no authentification is needed, for example, with a Single Sign On in front of DnsCherry.

However, in order to trace who made which action, the user name can be provided in an http header, 
in that case, having the http header in each request is mandatory.

Configuration:

.. sourcecode:: ini

    [auth]
    
    # auth module to load
    auth.module = 'dnscherry.auth.modNone'
    # optional http header handling.
    #auth.none.user_header_name = 'AUTH_USER'

modHtpasswd
~~~~~~~~~~~

This module uses an htpasswd file as a users database.

.. warning::

    This module requires installing **python-passlib**.

Configuration:

.. sourcecode:: ini

    [auth]
 
    # name of the auth module
    auth.module = 'dnscherry.auth.modHtpasswd'
    # path to htpasswd file
    auth.htpasswd.file = '/etc/dnscherry/users.db'


modLdap
~~~~~~~

This module authentificates users against an ldap server.

.. warning::

    This module requires installing **python-ldap**, 

.. warning::

    As python-ldap is not compatible with python 3.x, DnsCherry must be launched with python 2.7.

Configuration:

.. sourcecode:: ini

    [auth]
 
    # name of the auth module
    auth.module = 'dnscherry.auth.modLdap'
    # base dn where to search user
    auth.ldap.userdn = 'ou=People,dc=example,dc=org'
    # ldap login filter
    auth.ldap.user.filter.tmpl = '(uid=%(login)s)'
    # base dn for group (optional) 
    # (if empty, all user in userdn can access dnscherry)
    auth.ldap.groupdn = 'cn=itpeople,ou=Groups,dc=example,dc=org'
    # ldap group filter (optional, except if auth.ldap.groupdn is defined) 
    auth.ldap.group.filter.tmpl = '(member=%(userdn)s)'
    # bind dn
    auth.ldap.binddn = 'cn=dnscherry,dc=example,dc=org' 
    # bind password
    auth.ldap.bindpassword = 'password'
    # ldap uri
    auth.ldap.uri = 'ldap://ldap.dnscherry.org'
    # ldap CA file (optional, used for ssl/tls)
    auth.ldap.ca = '/etc/dnscherry/TEST-cacert.pem'
    # enable starttls (optional, default off, don't use it with ldaps)
    auth.ldap.starttls = 'on'
    # check certificat (optional, default on)
    auth.ldap.checkcert = 'on'

Implementing your own auth modules
----------------------------------

Implementing your own modules should be fairly easy, 
just create a python module with a class inheriting from dnscherry.auth.Auth, 
and implement the **__init__** and **check_credentials** methods:


.. sourcecode:: python

    import cherrypy
    import dnscherry.auth
    import logging

    class Auth(dnscherry.auth.Auth):
    
        def __init__(self, config, logger=None):
            """ module initialization
            initialize the auth module
            the 'auth' section of the ini file is passed by 'config'
            @hash config: the 'auth' section of the ini file
            @logger logger: the dnscherry error logger
            """
            self.logger = logger
            
            # get param1, with default value 'hello'
            self.param1 = self._get_param('auth.mymod.param1', 'hello')

            # get param2, with no default value 
            # if not provided in the 'auth' section, DnsCherry will emit 
            # a log telling that the parameter is missing and exit(1)
            self.param2 = self._get_param('auth.mymod.param2')
            
            # emit a custom log 
            self._logger(
                 logging.DEBUG,
                 'my module is initialized'
            )

    
        def check_credentials(self, username, password):
            """ Check credential function (called on login)
            @str username: the login to check
            @str password: the password to check
            @rtype: bool (True if authentificated, False otherwise)
            """
            
            # simple module checking only one user/password
            return username == 'george' and password == 'password'


