#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Integration tests for dnscherry.auth.modLdap.

These tests run against the local slapd instance provisioned by
tests/cfg/deploy.sh (ldap.dnscherry.org is mapped to 127.0.0.1 in
/etc/hosts).  Plain ldap:// on port 389, ldaps:// on port 636 and
StartTLS on port 389 are all expected to be available.

Configuration keys use the dotted 'auth.ldap.*' form that
dnscherry.auth.Auth._get_param() reads.
"""

from __future__ import with_statement
from __future__ import unicode_literals

import os

import cherrypy
import ldap
import pytest
from unittest.mock import MagicMock

from dnscherry import MissingParameter
from dnscherry.auth.modLdap import Auth, CaFileDontExist

HERE = os.path.dirname(os.path.abspath(__file__))
CA_FILE = os.path.join(HERE, 'cfg', 'etc', 'ldap', 'ssl', 'TEST-cacert.pem')

BASE_CFG = {
    'auth.ldap.userdn': 'ou=People,dc=example,dc=org',
    'auth.ldap.groupdn': 'ou=groups,dc=example,dc=org',
    'auth.ldap.binddn': 'cn=dnscherry,dc=example,dc=org',
    'auth.ldap.bindpassword': 'password',
    'auth.ldap.uri': 'ldap://ldap.dnscherry.org:389',
    'auth.ldap.ca': CA_FILE,
    'auth.ldap.starttls': 'off',
    'auth.ldap.checkcert': 'off',
    'auth.ldap.user.filter.tmpl': '(uid=%(login)s)',
    'auth.ldap.group.filter.tmpl': '(member=%(userdn)s)',
    'auth.ldap.dn_user_attr': 'uid',
    'auth.ldap.group_attr.member': '%(dn)s',
    'auth.ldap.timeout': 10,
}


def make_cfg(**overrides):
    """Return a full config dict with the given overrides applied.

    Override keys may be short ('uri', 'checkcert') or fully dotted
    ('auth.ldap.uri'); short keys are mapped into the 'auth.ldap'
    namespace, which is how dnscherry.auth.Auth._get_param() reads
    them (flat keys in the config dict).
    """
    cfg = dict(BASE_CFG)
    for key, value in overrides.items():
        if not key.startswith('auth.'):
            key = 'auth.ldap.' + key
        cfg[key] = value
    return cfg


def make_auth(**overrides):
    """Build an Auth instance backed by a mock logger."""
    return Auth(make_cfg(**overrides), MagicMock())


# ---------------------------------------------------------------------------
# Auth.__init__
# ---------------------------------------------------------------------------

class TestInit(object):

    def test_nominal(self):
        inv = make_auth()
        assert inv.uri == 'ldap://ldap.dnscherry.org:389'
        assert inv.userdn == 'ou=People,dc=example,dc=org'
        assert inv.groupdn == 'ou=groups,dc=example,dc=org'
        assert inv.binddn == 'cn=dnscherry,dc=example,dc=org'
        assert inv.ca == CA_FILE
        assert inv.starttls == 'off'
        assert inv.checkcert == 'off'
        assert inv.timeout == 10
        assert inv.user_filter_tmpl == '(uid=%(login)s)'
        assert inv.group_filter_tmpl == '(member=%(userdn)s)'
        assert inv.logout_button is True

    def test_defaults(self):
        # ca, starttls, checkcert and timeout are optional
        cfg = {k: v for k, v in BASE_CFG.items() if k not in (
            'auth.ldap.ca', 'auth.ldap.starttls',
            'auth.ldap.checkcert', 'auth.ldap.timeout')}
        inv = Auth(cfg, MagicMock())
        assert inv.ca is False
        assert inv.starttls == 'off'
        assert inv.checkcert == 'on'
        assert inv.timeout == 1

    def test_missing_required_param(self):
        cfg = {k: v for k, v in BASE_CFG.items()
               if k != 'auth.ldap.userdn'}
        with pytest.raises(MissingParameter) as exc:
            Auth(cfg, MagicMock())
        assert exc.value.section == 'auth'
        assert exc.value.key == 'auth.ldap.userdn'

    def test_groupdn_absent(self):
        cfg = {k: v for k, v in BASE_CFG.items()
               if k != 'auth.ldap.groupdn'}
        inv = Auth(cfg, MagicMock())
        assert inv.groupdn is False
        assert not hasattr(inv, 'group_filter_tmpl')

    def test_groupdn_without_group_filter(self):
        cfg = {k: v for k, v in BASE_CFG.items()
               if k != 'auth.ldap.group.filter.tmpl'}
        with pytest.raises(MissingParameter) as exc:
            Auth(cfg, MagicMock())
        assert exc.value.key == 'auth.ldap.group.filter.tmpl'


# ---------------------------------------------------------------------------
# Auth._connect — against the local slapd
# ---------------------------------------------------------------------------

class TestConnect(object):

    def test_plain_ldap_no_cert_check(self):
        client = make_auth()._connect()
        assert client is not None
        client.unbind_s()

    def test_plain_ldap_with_cert_check(self):
        # CA file is configured but TLS is not used on plain ldap://
        client = make_auth(checkcert='on')._connect()
        client.unbind_s()

    def test_starttls(self):
        client = make_auth(starttls='on', checkcert='on')._connect()
        client.unbind_s()

    def test_ldaps(self):
        client = make_auth(
            uri='ldaps://ldap.dnscherry.org:636',
            checkcert='on'
        )._connect()
        client.unbind_s()

    def test_ldaps_without_cert_check(self):
        client = make_auth(
            uri='ldaps://ldap.dnscherry.org:636',
            checkcert='off'
        )._connect()
        client.unbind_s()

    def test_starttls_with_ldaps_raises_http_error(self):
        # start_tls_s() on an already-TLS connection fails; modLdap
        # converts the ldap error into a 500 HTTPError and logs it
        auth = make_auth(
            uri='ldaps://ldap.dnscherry.org:636',
            starttls='on',
            checkcert='on'
        )
        with pytest.raises(cherrypy.HTTPError) as exc:
            auth._connect()
        # modLdap raises cherrypy.HTTPError("500", ...): the code is
        # stored as the string '500'
        assert str(exc.value.code) == '500'
        assert auth.logger.error.called

    def test_ca_file_does_not_exist(self):
        auth = make_auth(ca='/nonexistent/CA.pem', checkcert='on')
        with pytest.raises(CaFileDontExist) as exc:
            auth._connect()
        assert exc.value.cafile == '/nonexistent/CA.pem'
        assert 'CA.pem' in exc.value.log

    def test_wrong_bind_credentials(self):
        auth = make_auth(bindpassword='badpassword')
        with pytest.raises(cherrypy.HTTPError) as exc:
            auth._connect()
        # modLdap raises cherrypy.HTTPError("500", ...): the code is
        # stored as the string '500'
        assert str(exc.value.code) == '500'
        assert auth.logger.error.called

    def test_server_unavailable(self):
        # nothing listens on port 390
        auth = make_auth(uri='ldap://ldap.dnscherry.org:390')
        with pytest.raises(cherrypy.HTTPError) as exc:
            auth._connect()
        # modLdap raises cherrypy.HTTPError("500", ...): the code is
        # stored as the string '500'
        assert str(exc.value.code) == '500'
        assert auth.logger.error.called


# ---------------------------------------------------------------------------
# Auth.check_credentials — against the local slapd
# ---------------------------------------------------------------------------

class TestCheckCredentials(object):

    def test_valid_user_in_group(self):
        assert make_auth().check_credentials(
            'jwatson', 'passwordwatson') is True

    def test_valid_user_in_other_group(self):
        assert make_auth().check_credentials(
            'ssmith', 'passwordsmith') is True

    def test_valid_user_without_group(self):
        # ngroup exists in the directory but is a member of no group
        assert make_auth().check_credentials(
            'ngroup', 'passwordngroup') is False

    def test_unknown_user(self):
        assert make_auth().check_credentials(
            'nosuchuser', 'whatever') is False

    def test_wrong_password(self):
        assert make_auth().check_credentials(
            'ssmith', 'wrongpassword') is False

    def test_valid_user_without_groupdn(self):
        # without groupdn any authenticated user is accepted
        cfg = {k: v for k, v in BASE_CFG.items()
               if k != 'auth.ldap.groupdn'}
        assert Auth(cfg, MagicMock()).check_credentials(
            'ngroup', 'passwordngroup') is True

    def test_starttls(self):
        assert make_auth(starttls='on',
                         checkcert='on').check_credentials(
            'jwatson', 'passwordwatson') is True

    def test_ldaps(self):
        assert make_auth(
            uri='ldaps://ldap.dnscherry.org:636',
            checkcert='on'
        ).check_credentials('jwatson', 'passwordwatson') is True
