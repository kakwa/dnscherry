# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
# The MIT License (MIT)
# DnsCherry
# Copyright (c) 2014 Carpentier Pierre-Francois

import cherrypy
import ldap
import dnscherry.auth
import logging

SESSION_KEY = '_cp_username'


class CaFileDontExist(Exception):
    def __init__(self, cafile):
        self.cafile = cafile
        self.log = "CA file %(cafile)s does not exist" % {'cafile': cafile}


class Auth(dnscherry.auth.Auth):

    def __init__(self, config, logger=None):

        self.logger = logger
        self.logout_button = True
        self.userdn = self._get_param('auth.ldap.userdn', config)
        self.user_filter_tmpl = self._get_param(
            'auth.ldap.user.filter.tmpl',
            config
            )
        self.groupdn = self._get_param('auth.ldap.groupdn', config, False)

        if self.groupdn:
            self.group_filter_tmpl = self._get_param(
                'auth.ldap.group.filter.tmpl',
                config
                )

        self.binddn = self._get_param('auth.ldap.binddn', config)
        self.bindpassword = self._get_param('auth.ldap.bindpassword', config)
        self.uri = self._get_param('auth.ldap.uri', config)
        self.ca = self._get_param('auth.ldap.ca', config, False)
        self.starttls = self._get_param('auth.ldap.starttls', config, 'off')
        self.checkcert = self._get_param('auth.ldap.checkcert', config, 'on')
        self.timeout = self._get_param('auth.ldap.timeout', config, 1)

    def _connect(self):
        ldap_client = ldap.initialize(self.uri)
        ldap_client.set_option(ldap.OPT_REFERRALS, 0)
        ldap.set_option(ldap.OPT_TIMEOUT, self.timeout)

        if self.starttls == 'on':
            ldap.set_option(ldap.OPT_X_TLS_DEMAND, True)
        else:
            ldap.set_option(ldap.OPT_X_TLS_DEMAND, False)
        # set the CA file if declared and if necessary
        if self.ca and self.checkcert == 'on':
            # check if the CA file actually exists
            if os.path.isfile(self.ca):
                ldap.set_option(ldap.OPT_X_TLS_CACERTFILE, self.ca)
            else:
                raise CaFileDontExist(self.ca)
        if self.checkcert == 'off':
            # this is dark magic
            # remove any of these two lines and it doesn't work
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
            ldap_client.set_option(
                ldap.OPT_X_TLS_REQUIRE_CERT,
                ldap.OPT_X_TLS_NEVER
                )
        else:
            # this is even darker magic
            ldap_client.set_option(
                ldap.OPT_X_TLS_REQUIRE_CERT,
                ldap.OPT_X_TLS_DEMAND
                )
            # it doesn't make sense to set it to never
            # (== don't check certifate)
            # but it only works with this option...
            # ... and it checks the certificat
            # (I've lost my sanity over this)
            ldap.set_option(
                ldap.OPT_X_TLS_REQUIRE_CERT,
                ldap.OPT_X_TLS_NEVER
                )

        if self.starttls == 'on':
            try:
                ldap_client.start_tls_s()
            except ldap.OPERATIONS_ERROR:
                self._logger(
                    logging.ERROR,
                    "cannot use starttls with ldaps:// uri (uri: " +
                    self.uri + ")"
                )
                raise cherrypy.HTTPError(
                        "500",
                        "Configuration Error, contact administrator"
                        )
        try:
            ldap_client.simple_bind_s(self.binddn, self.bindpassword)
        except ldap.INVALID_CREDENTIALS:
            self._logger(
                    logging.ERROR,
                    "Configuration error, wrong credentials, "
                    "unable to connect to ldap with '" + self.binddn + "'"
                )
            raise cherrypy.HTTPError(
                    "500",
                    "Configuration Error, contact administrator"
                    )
        except ldap.SERVER_DOWN:
            self._logger(
                    logging.ERROR,
                    "Unable to contact ldap server '" +
                    self.uri +
                    "', check 'auth.ldap.uri' and ssl/tls configuration",
                )
            raise cherrypy.HTTPError(
                    "500",
                    "Configuration Error, contact administrator"
                    )
        return ldap_client

    def check_credentials(self, username, password):

        ldap_client = self._connect()

        user_filter = self.user_filter_tmpl % {
            'login': username
            }

        r = ldap_client.search_s(
                self.userdn,
                ldap.SCOPE_SUBTREE,
                user_filter
                )
        if len(r) == 0:
            ldap_client.unbind_s()
            return False

        dn_entry = r[0][0]

        try:
            ldap_auth = ldap.initialize(self.uri)
            if self.starttls == 'on':
                ldap_auth.start_tls_s()
            ldap_auth.set_option(ldap.OPT_REFERRALS, 0)
            ldap_auth.simple_bind_s(dn_entry, password)
            ldap_auth.unbind_s()
        except ldap.INVALID_CREDENTIALS:
            ldap_client.unbind_s()
            return False

        if self.groupdn:
            group_filter = self.group_filter_tmpl % {
                    'userdn': dn_entry
                    }
            r = ldap_client.search_s(
                    self.groupdn,
                    ldap.SCOPE_SUBTREE,
                    group_filter
                    )
            if len(r) == 0:
                ldap_client.unbind_s()
                return False

        ldap_client.unbind_s()
        return True
