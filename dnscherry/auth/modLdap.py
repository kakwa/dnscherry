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
        self.user_filter_tmpl = self._get_param('auth.ldap.user.filter.tmpl', config)
        self.groupdn = self._get_param('auth.ldap.groupdn', config, False)

        if self.groupdn:
            self.user_group_tmpl = self._get_param('auth.ldap.group.filter.tmpl', config)

        self.binddn = self._get_param('auth.ldap.binddn', config)
        self.bindpassword = self._get_param('auth.ldap.bindpassword', config)
        self.uri = self._get_param('auth.ldap.uri', config)
        self.ca = self._get_param('auth.ldap.ca', config, False)
        self.starttls = self._get_param('auth.ldap.starttls', config, 'off')
        self.checkcert = self._get_param('auth.ldap.checkcert', config, 'on')

    def check_credentials(self, username, password):
        ldap_client = ldap.initialize(self.uri)
        ldap_client.set_option(ldap.OPT_REFERRALS, 0)
        ldap_client.simple_bind_s(self.binddn, self.bindpassword)
        user_filter = self.user_filter_tmpl % {
            'login': username
            }

        r = ldap_client.search_s(self.userdn, 
                ldap.SCOPE_SUBTREE,
                user_filter
                 )
        if len(r) == 0:
            return False

        dn_entry = r[0][0]

        try:
            ldap_auth = ldap.initialize(self.uri)
            ldap_auth.set_option(ldap.OPT_REFERRALS, 0)
            ldap_auth.simple_bind_s(dn_entry, password)
        except ldap.INVALID_CREDENTIALS:
            return False

        return True
