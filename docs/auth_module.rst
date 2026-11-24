Auth modules
============

Configuration
-------------

modNone
~~~~~~~

No interactive login—useful with SSO in front of DnsCherry. To attribute actions to a user, an HTTP header may supply the username (then every request must carry it).

.. sourcecode:: ini

    [auth]

    auth.module = 'dnscherry.auth.modNone'
    # optional:
    # auth.none.user_header_name = 'AUTH_USER'

modHtpasswd
~~~~~~~~~~~

File-based users (`htpasswd` format).

.. warning::

    Requires **passlib** (``pip install 'dnscherry[auth_htpasswd]'`` or ``pip install passlib``).

.. sourcecode:: ini

    [auth]

    auth.module = 'dnscherry.auth.modHtpasswd'
    auth.htpasswd.file = '/etc/dnscherry/users.db'

modLdap
~~~~~~~

LDAP bind + search authentication.

.. warning::

    Requires **python-ldap** (included in default installs; extras: ``pip install 'dnscherry[auth_ldap]'``).

.. sourcecode:: ini

    [auth]

    auth.module = 'dnscherry.auth.modLdap'
    auth.ldap.userdn = 'ou=People,dc=example,dc=org'
    auth.ldap.user.filter.tmpl = '(uid=%(login)s)'
    # optional group restriction (if unset, any user under userdn may log in)
    auth.ldap.groupdn = 'cn=itpeople,ou=Groups,dc=example,dc=org'
    auth.ldap.group.filter.tmpl = '(member=%(userdn)s)'
    auth.ldap.binddn = 'cn=dnscherry,dc=example,dc=org'
    auth.ldap.bindpassword = 'password'
    auth.ldap.uri = 'ldap://ldap.dnscherry.org'
    auth.ldap.ca = '/etc/dnscherry/TEST-cacert.pem'
    auth.ldap.starttls = 'on'
    auth.ldap.checkcert = 'on'
    auth.ldap.timeout = 2

Custom modules
--------------

Subclass ``dnscherry.auth.Auth`` and implement ``__init__`` and ``check_credentials``:

.. sourcecode:: python

    import cherrypy
    import dnscherry.auth
    import logging

    class Auth(dnscherry.auth.Auth):

        def __init__(self, config, logger=None):
            self.logger = logger
            self.logout_button = False
            self.param1 = self._get_param('auth.mymod.param1', 'hello')
            self.param2 = self._get_param('auth.mymod.param2')
            self._logger(logging.DEBUG, 'my module is initialized')

        def check_credentials(self, username, password):
            return username == 'george' and password == 'password'
