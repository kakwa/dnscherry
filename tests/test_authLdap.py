#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement
from __future__ import unicode_literals

import pytest
import sys
from sets import Set
from dnscherry.auth.modLdap import Auth, CaFileDontExist
import cherrypy
import logging
import ldap

cfg = {
'auth.ldap.module': 'dnscherry.backend.ldap',
'auth.ldap.groupdn': 'ou=groups,dc=example,dc=org',
'auth.ldap.userdn': 'ou=People,dc=example,dc=org',
'auth.ldap.binddn': 'cn=dnscherry,dc=example,dc=org',
'auth.ldap.bindpassword': 'password',
'auth.ldap.uri': 'ldap://ldap.dnscherry.org:389',
'auth.ldap.ca': './tests/test_env/etc/dnscherry/TEST-cacert.pem',
'auth.ldap.starttls': 'off',
'auth.ldap.checkcert': 'off',
'auth.ldap.user.filter.tmpl': '(uid=%(login)s)',
'auth.ldap.group.filter.tmpl': '(member=%(userdn)s)',
'auth.ldap.dn_user_attr': 'uid',
'auth.ldap.group_attr.member': "%(dn)s",
'auth.ldap.timeout': 10,
}


def syslog_error(msg='', context='',
        severity=logging.INFO, traceback=False):
    pass

cherrypy.log.error = syslog_error
attr = ['shéll', 'shell', 'cn', 'uid', 'uidNumber', 'gidNumber', 'home', 'userPassword', 'givenName', 'email', 'sn']


class TestError(object):

    def testNominal(self):
        inv = Auth(cfg, cherrypy.log)
        return True

    def testConnectSSLNoCheck(self):
        cfg2 = cfg.copy()
        cfg2['uri'] = 'ldaps://ldap.dnscherry.org:636'
        cfg2['checkcert'] = 'off'
        inv = Auth(cfg2, cherrypy.log)
        ldap = inv._connect()
        ldap.simple_bind_s(inv.binddn, inv.bindpassword)

    def testConnect(self):
        inv = Auth(cfg, cherrypy.log)
        ldap = inv._connect()
        ldap.simple_bind_s(inv.binddn, inv.bindpassword)
        return True

    def testConnectSSL(self):
        cfg2 = cfg.copy()
        cfg2['uri'] = 'ldaps://ldap.dnscherry.org:636'
        cfg2['checkcert'] = 'on'
        inv = Auth(cfg2, cherrypy.log)
        ldap = inv._connect()
        ldap.simple_bind_s(inv.binddn, inv.bindpassword)

    def testLdapUnavaible(self):
        cfg2 = cfg.copy()
        cfg2['uri'] = 'ldaps://notaldap:636'
        cfg2['checkcert'] = 'on'
        inv = Auth(cfg2, cherrypy.log)
        try:
            ldapc = inv._connect()
            ldapc.simple_bind_s(inv.binddn, inv.bindpassword)
        except ldap.SERVER_DOWN as e:
            return

    def testMissingCA(self):
        cfg2 = cfg.copy()
        cfg2['uri'] = 'ldaps://ldap.dnscherry.org:636'
        cfg2['checkcert'] = 'on'
        cfg2['ca'] = './test/cfg/not_a_ca.crt'
        try:
            inv = Auth(cfg2, cherrypy.log)
            ldapc = inv._connect()
        except CaFileDontExist as e:
            return

    def testConnectSSLWrongCA(self):
        cfg2 = cfg.copy()
        cfg2['uri'] = 'ldaps://ldap.dnscherry.org:636'
        cfg2['checkcert'] = 'on'
        inv = Auth(cfg2, cherrypy.log)
        ldapc = inv._connect()
        try:
            ldapc.simple_bind_s(inv.binddn, inv.bindpassword)
        except ldap.SERVER_DOWN as e:
            assert e[0]['info'] == 'TLS: hostname does not match CN in peer certificate'

    def testConnectStartTLS(self):
        cfg2 = cfg.copy()
        cfg2['uri'] = 'ldap://ldap.dnscherry.org:390'
        cfg2['checkcert'] = 'off'
        cfg2['starttls'] = 'on'
        cfg2['ca'] = './test/cfg/ca.crt'
        inv = Auth(cfg2, cherrypy.log)
        ldapc = inv._connect()
        ldapc.simple_bind_s(inv.binddn, inv.bindpassword)

    def testAuthSuccess(self):
        inv = Auth(cfg, cherrypy.log)
        ret = inv.check_credentials('jwatson', 'passwordwatson')
        assert ret == True

    def testAuthFailure(self):
        inv = Auth(cfg, cherrypy.log)
        res = inv.check_credentials('notauser', 'password') or inv.check_credentials('jwatson', 'notapassword')
        assert res == False

    def testMissingParam(self):
        cfg2 = {}
        return True
        try:
            inv = Auth(cfg2, cherrypy.log)
        except MissingKey:
            return
