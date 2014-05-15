# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
# The MIT License (MIT)
# DnsCherry
# Copyright (c) 2014 Carpentier Pierre-Francois


import cherrypy
import ldap
import dnscherry.auth

SESSION_KEY = '_cp_username'

class Auth(dnscherry.auth.Auth):

    def __init__(self, config):
        self.logout_button = True
        self.userdn = self._get_param('auth.ldap.userdn', config)
        self.loginattribut = self._get_param('auth.ldap.loginattribut', config)
        self.groupdn = self._get_param('auth.ldap.groupdn', config, False)
        if self.groupdn:
            self.groupattribut = self._get_param('auth.ldap.groupattribut', config, 'uniqueMember')
        self.binddn = self._get_param('auth.ldap.binddn', config)
        self.bindpassword = self._get_param('auth.ldap.bindpassword', config)
        self.uri = self._get_param('auth.ldap.uri', config)
        self.ca = self._get_param('auth.ldap.ca', config, False)
        self.starttls = self._get_param('auth.ldap.starttls', config, 'off')
        self.checkcert = self._get_param('auth.ldap.checkcert', config, 'on')

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
