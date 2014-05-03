# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:

import cherrypy
import ldap
import dnscherry.auth

SESSION_KEY = '_cp_username'

class Auth(dnscherry.auth.Auth):

    def __init__(self, config):
        self.logout_button = True
        self.userdn = config['auth.ldap.userdn']
        self.loginattribut = config['auth.ldap.loginattribut']
        self.groupdn = config['auth.ldap.groupdn']
        self.groupattribut = config['auth.ldap.groupattribut']
        self.binddn = config['auth.ldap.binddn']
        self.bindpassword = config['auth.ldap.bindpassword']
        self.uri = config['auth.ldap.uri']
        self.ca = config['auth.ldap.ca']
        self.starttls = config['auth.ldap.starttls']
        self.checkcert = config['auth.ldap.checkcert']

    def check_credentials(self, username, password):
        username = re.sub(',.*','', username)
        user_dn_entry = '%(loginattr)=%(user)s,%(userdn)' % {
                'loginattr': self.loginattribut,
                'user': username,
                'userdn': self.userdn
                }
        try:
            # build a client
            ldap_client = ldap.initialize(self.uri)
            # perform a synchronous bind
            ldap_client.set_option(ldap.OPT_REFERRALS, 0)
            ldap_client.simple_bind_s(user_dn_entry, password)
            return True
        except ldap.INVALID_CREDENTIALS:
            ldap_client.unbind()
            return False
        except ldap.SERVER_DOWN:
            raise cherrypy.HTTPError(
                "500", "Ldap serveur unavailable")

    def check_auth(self):
        username = cherrypy.session.get(SESSION_KEY)
        if username:
           return username
        else:
           raise cherrypy.HTTPRedirect("/signin")
