# -*- coding: utf-8 -*-
"""Unit tests for dnscherry/__init__.py — covers methods not exercised by
the integration test suite (test_DnsCherry.py).
"""
import logging
import pytest
from unittest.mock import MagicMock, call
from socket import error as socket_error

import cherrypy
import dns.tsig
import dns.exception
from dns.tsig import PeerBadKey
from dns.rdatatype import UnknownRdatatype

from dnscherry import (
    syslog_error,
    NoRecordSelected,
    WrongDnsUpdateMethod,
    MissingParameter,
    DnsCherry,
    SESSION_KEY,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def make_app():
    """Return a bare DnsCherry instance with the minimal attributes that
    the methods under test expect to exist."""
    app = DnsCherry()
    app.temp_error = MagicMock()
    app.temp_error.render.return_value = 'ERROR_PAGE'
    app.auth = MagicMock()
    app.auth.logout_button = True
    app.zone_list = {'example.com': {'ip': '127.0.0.1'}}
    app.zone_default = 'example.com'
    app.notifications = {}
    app.type_displayed = ['A', 'CNAME', 'AAAA']
    app.type_written = ['A', 'CNAME', 'AAAA']
    app.default_ttl = '86400'
    return app


# ---------------------------------------------------------------------------
# syslog_error
# ---------------------------------------------------------------------------

class TestSyslogError:

    def test_traceback_true_msg_empty_no_exception(self, monkeypatch):
        mock_cherrypy_log = MagicMock()
        monkeypatch.setattr(cherrypy, 'log', mock_cherrypy_log)
        mock_log = mock_cherrypy_log.error_log
        syslog_error(traceback=True, msg='', context='')
        # 1: log(severity, 'Python Exception:')  [initial]
        # 2: log(severity, 'Python Exception:')  [exc is (None,None,None)]
        # 3: log(severity, 'NoneType: None\n')   [from format_exception]
        assert mock_log.log.call_count == 3
        assert mock_log.log.call_args_list[0] == call(logging.INFO, 'Python Exception:')

    def test_no_traceback_no_context(self, monkeypatch):
        mock_cherrypy_log = MagicMock()
        monkeypatch.setattr(cherrypy, 'log', mock_cherrypy_log)
        mock_log = mock_cherrypy_log.error_log
        syslog_error(msg='hello', context='')
        assert mock_log.log.call_count == 1
        assert mock_log.log.call_args_list[0] == call(logging.INFO, 'hello')

    def test_no_traceback_with_context(self, monkeypatch):
        mock_cherrypy_log = MagicMock()
        monkeypatch.setattr(cherrypy, 'log', mock_cherrypy_log)
        mock_log = mock_cherrypy_log.error_log
        syslog_error(msg='hello', context='ctx')
        assert mock_log.log.call_count == 1
        assert mock_log.log.call_args_list[0] == call(logging.INFO, 'ctx hello')

    def test_traceback_true_with_active_exception(self, monkeypatch):
        mock_cherrypy_log = MagicMock()
        monkeypatch.setattr(cherrypy, 'log', mock_cherrypy_log)
        mock_log = mock_cherrypy_log.error_log
        try:
            raise ValueError('boom')
        except ValueError:
            syslog_error(msg='err', context='', traceback=True)
        # call 1: log(INFO, 'err')  [initial, context empty]
        # calls 2+: traceback lines (ValueError: boom)
        assert mock_log.log.call_count >= 2
        assert mock_log.log.call_args_list[0] == call(logging.INFO, 'err')
        # last call should contain 'ValueError'
        last_msg = mock_log.log.call_args_list[-1][0][1]
        assert 'ValueError' in last_msg or 'boom' in last_msg

    def test_custom_severity(self, monkeypatch):
        mock_cherrypy_log = MagicMock()
        monkeypatch.setattr(cherrypy, 'log', mock_cherrypy_log)
        mock_log = mock_cherrypy_log.error_log
        syslog_error(msg='x', severity=logging.ERROR, context='')
        assert mock_log.log.call_args_list[0] == call(logging.ERROR, 'x')


# ---------------------------------------------------------------------------
# Exception classes
# ---------------------------------------------------------------------------

class TestExceptions:

    def test_missing_parameter_attributes(self):
        e = MissingParameter('dns', 'default.zone')
        assert e.section == 'dns'
        assert e.key == 'default.zone'

    def test_no_record_selected_is_exception(self):
        assert issubclass(NoRecordSelected, Exception)

    def test_wrong_dns_update_method_is_exception(self):
        assert issubclass(WrongDnsUpdateMethod, Exception)


# ---------------------------------------------------------------------------
# _get_param
# ---------------------------------------------------------------------------

class TestGetParam:

    def test_key_found(self):
        app = make_app()
        config = {'dns': {'default.zone': 'example.com'}}
        assert app._get_param('dns', 'default.zone', config) == 'example.com'

    def test_section_missing_default_given(self):
        app = make_app()
        config = {}
        assert app._get_param('dns', 'default.zone', config, 'fallback') == 'fallback'

    def test_key_missing_default_given(self):
        app = make_app()
        config = {'dns': {}}
        assert app._get_param('dns', 'nonexistent', config, 'fallback') == 'fallback'

    def test_section_missing_no_default_raises(self):
        app = make_app()
        config = {}
        with pytest.raises(MissingParameter) as exc_info:
            app._get_param('dns', 'default.zone', config)
        assert exc_info.value.section == 'dns'
        assert exc_info.value.key == 'default.zone'

    def test_key_missing_no_default_raises(self):
        app = make_app()
        config = {'dns': {}}
        with pytest.raises(MissingParameter) as exc_info:
            app._get_param('dns', 'nonexistent', config)
        assert exc_info.value.section == 'dns'
        assert exc_info.value.key == 'nonexistent'

    def test_default_none_explicit_raises(self):
        app = make_app()
        config = {}
        with pytest.raises(MissingParameter):
            app._get_param('dns', 'default.zone', config, None)


# ---------------------------------------------------------------------------
# _select_algorithm
# ---------------------------------------------------------------------------

class TestSelectAlgorithm:

    def test_hmac_md5(self):
        app = make_app()
        assert app._select_algorithm('hmac-md5') == dns.tsig.HMAC_MD5

    def test_hmac_sha1(self):
        app = make_app()
        assert app._select_algorithm('hmac-sha1') == dns.tsig.HMAC_SHA1

    def test_hmac_sha224(self):
        app = make_app()
        assert app._select_algorithm('hmac-sha224') == dns.tsig.HMAC_SHA224

    def test_hmac_sha256(self):
        app = make_app()
        assert app._select_algorithm('hmac-sha256') == dns.tsig.HMAC_SHA256

    def test_hmac_sha384(self):
        app = make_app()
        assert app._select_algorithm('hmac-sha384') == dns.tsig.HMAC_SHA384

    def test_hmac_sha512(self):
        app = make_app()
        assert app._select_algorithm('hmac-sha512') == dns.tsig.HMAC_SHA512

    def test_case_insensitive(self):
        app = make_app()
        assert app._select_algorithm('HMAC-MD5') == dns.tsig.HMAC_MD5
        assert app._select_algorithm('Hmac-Sha512') == dns.tsig.HMAC_SHA512

    def test_unknown_returns_none(self):
        app = make_app()
        assert app._select_algorithm('unknown-algo') is None


# ---------------------------------------------------------------------------
# _validate_domain
# ---------------------------------------------------------------------------

class TestValidateDomain:

    def test_valid_simple_domain(self):
        app = make_app()
        assert app._validate_domain('example.com') is True

    def test_valid_subdomain(self):
        app = make_app()
        assert app._validate_domain('www.example.com') is True

    def test_valid_hyphen(self):
        app = make_app()
        assert app._validate_domain('my-host.example.com') is True

    def test_valid_with_digits(self):
        app = make_app()
        assert app._validate_domain('host1.example2.com') is True

    def test_invalid_empty(self):
        app = make_app()
        assert app._validate_domain('') is False

    def test_invalid_underscore(self):
        app = make_app()
        assert app._validate_domain('under_score.com') is False

    def test_invalid_trailing_dot_in_tld(self):
        app = make_app()
        # '...' is clearly invalid (no valid domain labels)
        assert app._validate_domain('...') is False

    def test_invalid_spaces(self):
        app = make_app()
        assert app._validate_domain('has space.com') is False


# ---------------------------------------------------------------------------
# _reraise
# ---------------------------------------------------------------------------

class TestReraise:

    def test_raises_given_exception(self):
        app = make_app()
        with pytest.raises(ValueError):
            app._reraise(ValueError('test'))

    def test_raises_custom_exception(self):
        app = make_app()
        with pytest.raises(NoRecordSelected):
            app._reraise(NoRecordSelected())


# ---------------------------------------------------------------------------
# _zone_where_port
# ---------------------------------------------------------------------------

class TestZoneWherePort:

    def test_with_port(self):
        app = make_app()
        app.zone_list = {'example.com': {'ip': '10.0.0.1', 'port': '8053'}}
        assert app._zone_where_port('example.com') == ('10.0.0.1', 8053)

    def test_without_port_defaults_to_53(self):
        app = make_app()
        app.zone_list = {'example.com': {'ip': '10.0.0.1'}}
        assert app._zone_where_port('example.com') == ('10.0.0.1', 53)

    def test_strips_ip_whitespace(self):
        app = make_app()
        app.zone_list = {'example.com': {'ip': '  10.0.0.1  ', 'port': '53'}}
        assert app._zone_where_port('example.com') == ('10.0.0.1', 53)


# ---------------------------------------------------------------------------
# _parse_zones
# ---------------------------------------------------------------------------

class TestParseZones:

    def test_single_zone(self):
        app = make_app()
        app.zone_list = {}
        config = {'dns.zones': {
            'ip.example.com': '127.0.0.1',
            'key.example.com': 'ujE=',
            'algorithm.example.com': 'hmac-md5',
        }}
        app._parse_zones(config)
        assert app.zone_list == {
            'example.com': {
                'ip': '127.0.0.1',
                'key': 'ujE=',
                'algorithm': 'hmac-md5',
            }
        }

    def test_two_zones(self):
        app = make_app()
        app.zone_list = {}
        config = {'dns.zones': {
            'ip.example.com': '127.0.0.1',
            'ip.example2.com': '10.0.0.2',
        }}
        app._parse_zones(config)
        assert 'example.com' in app.zone_list
        assert 'example2.com' in app.zone_list
        assert app.zone_list['example.com']['ip'] == '127.0.0.1'
        assert app.zone_list['example2.com']['ip'] == '10.0.0.2'

    def test_empty(self):
        app = make_app()
        app.zone_list = {}
        app._parse_zones({'dns.zones': {}})
        assert app.zone_list == {}


# ---------------------------------------------------------------------------
# _get_loglevel
# ---------------------------------------------------------------------------

class TestGetLoglevel:

    def test_debug(self):
        app = make_app()
        assert app._get_loglevel('debug') == logging.DEBUG

    def test_notice(self):
        app = make_app()
        assert app._get_loglevel('notice') == logging.INFO

    def test_info(self):
        app = make_app()
        assert app._get_loglevel('info') == logging.INFO

    def test_warning(self):
        app = make_app()
        assert app._get_loglevel('warning') == logging.WARNING

    def test_warn_alias(self):
        app = make_app()
        assert app._get_loglevel('warn') == logging.WARNING

    def test_error(self):
        app = make_app()
        assert app._get_loglevel('error') == logging.ERROR

    def test_err_alias(self):
        app = make_app()
        assert app._get_loglevel('err') == logging.ERROR

    def test_critical(self):
        app = make_app()
        assert app._get_loglevel('critical') == logging.CRITICAL

    def test_crit_alias(self):
        app = make_app()
        assert app._get_loglevel('crit') == logging.CRITICAL

    def test_alert(self):
        app = make_app()
        assert app._get_loglevel('alert') == logging.CRITICAL

    def test_emergency(self):
        app = make_app()
        assert app._get_loglevel('emergency') == logging.CRITICAL

    def test_emerg_alias(self):
        app = make_app()
        assert app._get_loglevel('emerg') == logging.CRITICAL

    def test_unknown_defaults_to_info(self):
        app = make_app()
        assert app._get_loglevel('nonexistent') == logging.INFO


# ---------------------------------------------------------------------------
# _add_notification / _empty_notification
# ---------------------------------------------------------------------------

class TestNotifications:

    def test_add_notification_new_user(self, monkeypatch):
        app = make_app()
        mock_session = MagicMock()
        mock_session.get.return_value = 'alice'
        monkeypatch.setattr(cherrypy, 'session', mock_session, raising=False)
        app._add_notification('hello world')
        assert app.notifications == {'alice': ["hello world"]}

    def test_add_notification_escapes_single_quotes(self, monkeypatch):
        app = make_app()
        mock_session = MagicMock()
        mock_session.get.return_value = 'alice'
        monkeypatch.setattr(cherrypy, 'session', mock_session, raising=False)
        app._add_notification("it's a test")
        assert app.notifications['alice'] == ["it\\'s a test"]

    def test_add_notification_existing_user_appends(self, monkeypatch):
        app = make_app()
        mock_session = MagicMock()
        mock_session.get.return_value = 'alice'
        monkeypatch.setattr(cherrypy, 'session', mock_session, raising=False)
        app.notifications = {'alice': ['first']}
        app._add_notification('second')
        assert app.notifications['alice'] == ['first', 'second']

    def test_empty_notification_with_messages(self, monkeypatch):
        app = make_app()
        mock_session = MagicMock()
        mock_session.get.return_value = 'alice'
        monkeypatch.setattr(cherrypy, 'session', mock_session, raising=False)
        app.notifications = {'alice': ['msg1', 'msg2']}
        result = app._empty_notification()
        assert result == ['msg1', 'msg2']
        assert app.notifications['alice'] == []

    def test_empty_notification_no_messages(self, monkeypatch):
        app = make_app()
        mock_session = MagicMock()
        mock_session.get.return_value = 'bob'
        monkeypatch.setattr(cherrypy, 'session', mock_session, raising=False)
        app.notifications = {}
        result = app._empty_notification()
        assert result == []
        assert app.notifications['bob'] == []

    def test_empty_notification_none_username(self, monkeypatch):
        app = make_app()
        mock_session = MagicMock()
        mock_session.get.return_value = None
        monkeypatch.setattr(cherrypy, 'session', mock_session, raising=False)
        app.notifications = {}
        result = app._empty_notification()
        assert result == []
        assert app.notifications[None] == []


# ---------------------------------------------------------------------------
# _error_handler
# ---------------------------------------------------------------------------

class TestErrorHandler:

    def _setup(self, monkeypatch):
        app = make_app()
        mock_error = MagicMock()
        monkeypatch.setattr(cherrypy.log, 'error', mock_error)
        # set response.status to a known initial value
        monkeypatch.setattr(cherrypy.response, 'status', 200)
        return app, mock_error

    def test_form_error(self, monkeypatch):
        app, mock_error = self._setup(monkeypatch)
        result = app._error_handler(dns.exception.FormError(), 'example.com')
        assert result == 'ERROR_PAGE'
        assert cherrypy.response.status == 500
        # temp_error.render called with danger alert
        render_kwargs = app.temp_error.render.call_args[1]
        assert render_kwargs['alert'] == 'danger'
        assert 'Unable to get Zone' in render_kwargs['message']

    def test_socket_error(self, monkeypatch):
        app, mock_error = self._setup(monkeypatch)
        result = app._error_handler(socket_error(), 'example.com')
        assert result == 'ERROR_PAGE'
        assert cherrypy.response.status == 500
        render_kwargs = app.temp_error.render.call_args[1]
        assert render_kwargs['alert'] == 'danger'
        assert 'Unable to contact DNS' in render_kwargs['message']

    def test_key_error(self, monkeypatch):
        app, mock_error = self._setup(monkeypatch)
        result = app._error_handler(KeyError('example.com'), 'example.com')
        assert result == 'ERROR_PAGE'
        assert cherrypy.response.status == 400
        render_kwargs = app.temp_error.render.call_args[1]
        assert render_kwargs['alert'] == 'warning'
        assert 'not configured' in render_kwargs['message']

    def test_peer_bad_key(self, monkeypatch):
        app, mock_error = self._setup(monkeypatch)
        result = app._error_handler(PeerBadKey(), 'example.com')
        assert result == 'ERROR_PAGE'
        assert cherrypy.response.status == 500
        render_kwargs = app.temp_error.render.call_args[1]
        assert render_kwargs['alert'] == 'danger'
        assert 'refused by DNS' in render_kwargs['message']

    def test_syntax_error(self, monkeypatch):
        app, mock_error = self._setup(monkeypatch)
        result = app._error_handler(dns.exception.SyntaxError(), 'example.com')
        assert result == 'ERROR_PAGE'
        assert cherrypy.response.status == 400
        render_kwargs = app.temp_error.render.call_args[1]
        assert render_kwargs['alert'] == 'warning'
        assert 'Wrong form data' in render_kwargs['message']

    def test_no_record_selected(self, monkeypatch):
        app, mock_error = self._setup(monkeypatch)
        result = app._error_handler(NoRecordSelected(), 'example.com')
        assert result == 'ERROR_PAGE'
        assert cherrypy.response.status == 400
        render_kwargs = app.temp_error.render.call_args[1]
        assert render_kwargs['alert'] == 'warning'
        assert 'No record selected' in render_kwargs['message']

    def test_unknown_rdatatype(self, monkeypatch):
        app, mock_error = self._setup(monkeypatch)
        result = app._error_handler(UnknownRdatatype(), 'example.com')
        assert result == 'ERROR_PAGE'
        assert cherrypy.response.status == 500
        render_kwargs = app.temp_error.render.call_args[1]
        assert render_kwargs['alert'] == 'danger'
        assert 'Unknown record type' in render_kwargs['message']

    def test_generic_exception(self, monkeypatch):
        app, mock_error = self._setup(monkeypatch)
        result = app._error_handler(Exception('something weird'), 'example.com')
        assert result == 'ERROR_PAGE'
        assert cherrypy.response.status == 500
        render_kwargs = app.temp_error.render.call_args[1]
        assert render_kwargs['alert'] == 'danger'
        assert 'Unkwown error' in render_kwargs['message']

    def test_invalid_zone_name(self, monkeypatch):
        app, mock_error = self._setup(monkeypatch)
        result = app._error_handler(ValueError('x'), 'bad_zone!')
        assert result == 'ERROR_PAGE'
        assert cherrypy.response.status == 400
        render_kwargs = app.temp_error.render.call_args[1]
        assert render_kwargs['alert'] == 'warning'
        assert 'Bad zone name' in render_kwargs['message']
        # zone passed to render is zone_default
        assert render_kwargs['current_zone'] == 'example.com'

    def test_logs_debug_traceback(self, monkeypatch):
        app, mock_error = self._setup(monkeypatch)
        app._error_handler(ValueError('x'), 'example.com')
        # first call to cherrypy.log.error is the debug traceback log
        first_call = mock_error.call_args_list[0][1]
        assert first_call['msg'] == ''
        assert first_call['severity'] == logging.DEBUG
        assert first_call['traceback'] is True


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------

class TestLogin:

    def test_login_success(self, monkeypatch):
        app = make_app()
        app.auth.check_credentials.return_value = True
        mock_error = MagicMock()
        monkeypatch.setattr(cherrypy.log, 'error', mock_error)
        mock_session = {}
        monkeypatch.setattr(cherrypy, 'session', mock_session, raising=False)
        mock_request = MagicMock()
        monkeypatch.setattr(cherrypy, 'request', mock_request)

        with pytest.raises(cherrypy.HTTPRedirect) as exc_info:
            app.login('admin', 'password')

        # redirect to '/'
        assert exc_info.value.args[0][0].endswith('/')
        # session updated
        assert mock_session[SESSION_KEY] == 'admin'
        assert mock_request.login == 'admin'
        # logged at INFO level
        assert mock_error.call_args_list[0][1]['severity'] == logging.INFO
        assert 'login success' in mock_error.call_args_list[0][1]['msg']

    def test_login_failure(self, monkeypatch):
        app = make_app()
        app.auth.check_credentials.return_value = False
        mock_error = MagicMock()
        monkeypatch.setattr(cherrypy.log, 'error', mock_error)
        mock_session = {}
        monkeypatch.setattr(cherrypy, 'session', mock_session, raising=False)
        mock_request = MagicMock()
        monkeypatch.setattr(cherrypy, 'request', mock_request)

        with pytest.raises(cherrypy.HTTPRedirect) as exc_info:
            app.login('admin', 'wrongpass')

        # redirect to /signin
        assert exc_info.value.args[0][0].endswith('/signin')
        # session NOT updated
        assert SESSION_KEY not in mock_session
        # logged at WARNING level
        assert mock_error.call_args_list[0][1]['severity'] == logging.WARNING
        assert 'login failed' in mock_error.call_args_list[0][1]['msg']


# ---------------------------------------------------------------------------
# logout
# ---------------------------------------------------------------------------

class TestLogout:

    def test_logout(self, monkeypatch):
        app = make_app()
        app.auth.end_session.return_value = 'admin'
        mock_error = MagicMock()
        monkeypatch.setattr(cherrypy.log, 'error', mock_error)

        with pytest.raises(cherrypy.HTTPRedirect) as exc_info:
            app.logout()

        # redirect to /signin
        assert exc_info.value.args[0][0].endswith('/signin')
        # end_session was called
        app.auth.end_session.assert_called_once()
        # logged at INFO level with user name
        assert mock_error.call_args_list[0][1]['severity'] == logging.INFO
        assert 'admin' in mock_error.call_args_list[0][1]['msg']


# ---------------------------------------------------------------------------
# del_record
# ---------------------------------------------------------------------------

class TestDelRecord:

    def test_no_record_raises_error_handler(self, monkeypatch):
        app = make_app()
        mock_error = MagicMock()
        monkeypatch.setattr(cherrypy.log, 'error', mock_error)
        mock_request = MagicMock()
        monkeypatch.setattr(cherrypy, 'request', mock_request)
        app.auth.check_auth.return_value = 'admin'
        # _error_handler is called with NoRecordSelected
        app._error_handler = MagicMock(return_value='ERROR_PAGE')

        result = app.del_record(record=None, zone='example.com')
        assert result == 'ERROR_PAGE'
        # _error_handler called with NoRecordSelected class (not instance)
        call_arg = app._error_handler.call_args[0][0]
        assert call_arg is NoRecordSelected

    def test_string_record_converted_to_list(self, monkeypatch):
        app = make_app()
        mock_error = MagicMock()
        monkeypatch.setattr(cherrypy.log, 'error', mock_error)
        mock_request = MagicMock()
        monkeypatch.setattr(cherrypy, 'request', mock_request)
        mock_session = MagicMock()
        mock_session.get.return_value = 'admin'
        monkeypatch.setattr(cherrypy, 'session', mock_session, raising=False)
        app.auth.check_auth.return_value = 'admin'
        app._manage_record = MagicMock()

        # single record as string: "key;type;content;class;ttl"
        with pytest.raises(cherrypy.HTTPRedirect) as exc_info:
            app.del_record(record='www;A;1.2.3.4;IN;300', zone='example.com')

        # _manage_record called once with action='del'
        assert app._manage_record.call_count == 1
        kwargs = app._manage_record.call_args[1]
        assert kwargs['action'] == 'del'
        assert kwargs['key'] == 'www'
        assert kwargs['type'] == 'A'
        # redirect to /?zone=example.com
        assert 'zone=example.com' in exc_info.value.args[0][0]

    def test_list_of_records(self, monkeypatch):
        app = make_app()
        mock_error = MagicMock()
        monkeypatch.setattr(cherrypy.log, 'error', mock_error)
        mock_request = MagicMock()
        monkeypatch.setattr(cherrypy, 'request', mock_request)
        mock_session = MagicMock()
        mock_session.get.return_value = 'admin'
        monkeypatch.setattr(cherrypy, 'session', mock_session, raising=False)
        app.auth.check_auth.return_value = 'admin'
        app._manage_record = MagicMock()

        records = ['www1;A;1.1.1.1;IN;300', 'www2;A;2.2.2.2;IN;600']
        with pytest.raises(cherrypy.HTTPRedirect):
            app.del_record(record=records, zone='example.com')

        assert app._manage_record.call_count == 2

    def test_manage_record_raises_returns_error_page(self, monkeypatch):
        app = make_app()
        mock_error = MagicMock()
        monkeypatch.setattr(cherrypy.log, 'error', mock_error)
        mock_request = MagicMock()
        monkeypatch.setattr(cherrypy, 'request', mock_request)
        mock_session = MagicMock()
        mock_session.get.return_value = 'admin'
        monkeypatch.setattr(cherrypy, 'session', mock_session, raising=False)
        app.auth.check_auth.return_value = 'admin'
        app._manage_record = MagicMock(side_effect=PeerBadKey())
        app._error_handler = MagicMock(return_value='ERROR_PAGE')

        result = app.del_record(record='www;A;1.2.3.4;IN;300', zone='example.com')
        assert result == 'ERROR_PAGE'
        app._error_handler.assert_called_once()


# ---------------------------------------------------------------------------
# add_record
# ---------------------------------------------------------------------------

class TestAddRecord:

    def test_add_record_success(self, monkeypatch):
        app = make_app()
        mock_error = MagicMock()
        monkeypatch.setattr(cherrypy.log, 'error', mock_error)
        mock_request = MagicMock()
        monkeypatch.setattr(cherrypy, 'request', mock_request)
        mock_session = MagicMock()
        mock_session.get.return_value = 'admin'
        monkeypatch.setattr(cherrypy, 'session', mock_session, raising=False)
        app.auth.check_auth.return_value = 'admin'
        app._manage_record = MagicMock()

        with pytest.raises(cherrypy.HTTPRedirect) as exc_info:
            app.add_record(key='www', ttl='300', type='A',
                           zone='example.com', content='1.2.3.4')

        app._manage_record.assert_called_once()
        args = app._manage_record.call_args[0]
        assert args[0] == 'www'
        assert args[5] == 'add'
        # redirect to /?zone=example.com
        assert 'zone=example.com' in exc_info.value.args[0][0]
        # notification added
        assert len(app.notifications.get('admin', [])) == 1

    def test_add_record_manage_raises_returns_error(self, monkeypatch):
        app = make_app()
        mock_error = MagicMock()
        monkeypatch.setattr(cherrypy.log, 'error', mock_error)
        mock_request = MagicMock()
        monkeypatch.setattr(cherrypy, 'request', mock_request)
        app.auth.check_auth.return_value = 'admin'
        app._manage_record = MagicMock(side_effect=dns.exception.SyntaxError())
        app._error_handler = MagicMock(return_value='ERROR_PAGE')

        result = app.add_record(key='www', ttl='300', type='A',
                                zone='example.com', content='1.2.3.4')
        assert result == 'ERROR_PAGE'
        app._error_handler.assert_called_once()


# ---------------------------------------------------------------------------
# index (exception path only — success path is covered by integration tests)
# ---------------------------------------------------------------------------

class TestIndex:

    def test_refresh_zone_raises_returns_error_page(self, monkeypatch):
        app = make_app()
        mock_error = MagicMock()
        monkeypatch.setattr(cherrypy.log, 'error', mock_error)
        mock_request = MagicMock()
        mock_request.query_string = ''
        monkeypatch.setattr(cherrypy, 'request', mock_request)
        app.auth.check_auth.return_value = 'admin'
        app._refresh_zone = MagicMock(side_effect=socket_error())
        app._error_handler = MagicMock(return_value='ERROR_PAGE')

        result = app.index(zone='example.com')
        assert result == 'ERROR_PAGE'
        app._error_handler.assert_called_once()
        # called with the exception and zone
        call_args = app._error_handler.call_args[0]
        assert isinstance(call_args[0], socket_error)
        assert call_args[1] == 'example.com'


# ---------------------------------------------------------------------------
# refresh (zone=None → uses zone_default)
# ---------------------------------------------------------------------------

class TestRefreshDefaultZone:

    def test_refresh_none_uses_default_zone(self, monkeypatch):
        app = make_app()
        app.zone_default = 'default.example.com'
        app.zone_list = {'default.example.com': {'ip': '127.0.0.1'}}

        mock_zone_obj = MagicMock()
        mock_zone_obj.nodes = {}
        mock_from_xfr = MagicMock(return_value=mock_zone_obj)
        mock_xfr = MagicMock()
        monkeypatch.setattr('dnscherry.dns.zone.from_xfr', mock_from_xfr)
        monkeypatch.setattr('dnscherry.dns.query.xfr', mock_xfr)

        result = app._refresh_zone(None)
        assert result == []
        # xfr called with the default zone
        assert mock_xfr.call_args[0][1] == 'default.example.com'


# ---------------------------------------------------------------------------
# reload() — log handler configuration branches
# ---------------------------------------------------------------------------

def _make_reload_app(monkeypatch, access_handler, error_handler):
    """Build a bare DnsCherry instance with mocks sufficient for reload()
    to run through the log-handler section without side effects."""
    import builtins
    app = DnsCherry.__new__(DnsCherry)

    mock_cherrypy_log = MagicMock()
    mock_access_log = MagicMock()
    mock_error_log = MagicMock()
    mock_cherrypy_log.access_log = mock_access_log
    mock_cherrypy_log.error_log = mock_error_log
    monkeypatch.setattr(cherrypy, 'log', mock_cherrypy_log)

    # mock template lookup so reload() doesn't need real template files
    mock_lookup_cls = MagicMock()
    mock_template = MagicMock()
    mock_lookup_cls.return_value.get_template.return_value = mock_template
    monkeypatch.setattr('dnscherry.lookup.TemplateLookup', mock_lookup_cls)

    # mock SysLogHandler to avoid connecting to /dev/log
    monkeypatch.setattr('dnscherry.logging.handlers.SysLogHandler',
                        MagicMock)

    config = {
        'resources': {'template_dir': '/tmp'},
        'dns': {'default.zone': 'example.com', 'default.ttl': '3600'},
        'dns.zones': {},
        'global': {
            'log.level': 'debug',
            'log.access_handler': access_handler,
            'log.error_handler': error_handler,
        },
        'auth': {'auth.module': 'dnscherry.auth.modNone'},
    }
    return app, config, mock_cherrypy_log


class TestReloadLogHandlers:

    def test_access_handler_syslog(self, monkeypatch):
        app, config, mock_log = _make_reload_app(
            monkeypatch, 'syslog', 'none')
        app.reload(config)
        # handlers list cleared, then a new handler added
        assert mock_log.access_log.addHandler.call_count == 1

    def test_access_handler_file(self, monkeypatch):
        app, config, mock_log = _make_reload_app(
            monkeypatch, 'file', 'none')
        app.reload(config)
        # 'file' means pass — no handler added
        assert mock_log.access_log.addHandler.call_count == 0

    def test_access_handler_none(self, monkeypatch):
        app, config, mock_log = _make_reload_app(
            monkeypatch, 'none', 'file')
        app.reload(config)
        # null handler added
        assert mock_log.access_log.addHandler.call_count == 1

    def test_error_handler_syslog(self, monkeypatch):
        app, config, mock_log = _make_reload_app(
            monkeypatch, 'file', 'syslog')
        app.reload(config)
        # syslog error handler replaces cherrypy.log.error
        assert mock_log.error_log.addHandler.call_count == 1

    def test_error_handler_file(self, monkeypatch):
        app, config, mock_log = _make_reload_app(
            monkeypatch, 'file', 'file')
        app.reload(config)
        # 'file' means pass — no handler added
        assert mock_log.error_log.addHandler.call_count == 0

    def test_error_handler_none(self, monkeypatch):
        app, config, mock_log = _make_reload_app(
            monkeypatch, 'none', 'none')
        app.reload(config)
        # null handler added for error log
        assert mock_log.error_log.addHandler.call_count == 1

    def test_log_level_set(self, monkeypatch):
        app, config, mock_log = _make_reload_app(
            monkeypatch, 'none', 'none')
        app.reload(config)
        # both logs get the configured level
        import logging as _logging
        assert mock_log.error_log.setLevel.called
        assert mock_log.access_log.setLevel.called


# ---------------------------------------------------------------------------
# reload() — MissingParameter error path
# ---------------------------------------------------------------------------

class TestReloadMissingParam:

    def test_reload_missing_template_dir_calls_error_and_exits(
            self, monkeypatch):
        import builtins
        app = DnsCherry.__new__(DnsCherry)
        mock_cherrypy_log = MagicMock()
        monkeypatch.setattr(cherrypy, 'log', mock_cherrypy_log)
        mock_exit = MagicMock(side_effect=SystemExit(1))
        monkeypatch.setattr(builtins, 'exit', mock_exit)

        config = {'dns': {'default.zone': 'example.com'}}
        with pytest.raises(SystemExit):
            app.reload(config)

        # error logged with the missing parameter info
        assert mock_cherrypy_log.error.called
        call_kwargs = mock_cherrypy_log.error.call_args[1]
        assert 'template_dir' in call_kwargs['msg']
        assert 'resources' in call_kwargs['msg']
        # exit(1) called
        assert mock_exit.call_args[0][0] == 1


# ---------------------------------------------------------------------------
# _manage_record
# ---------------------------------------------------------------------------

class TestManageRecord:

    @staticmethod
    def _app_with_zone(zone_info):
        app = make_app()
        app.zone_list['example.com'] = dict(zone_info)
        return app

    def test_del_record(self, monkeypatch):
        import dns.update, dns.query
        app = self._app_with_zone({
            'ip': '127.0.0.1', 'key': 'secret', 'algorithm': 'hmac-md5'
        })
        mock_from_text = MagicMock(return_value='MOCK_KEYRING')
        mock_update_cls = MagicMock()
        mock_tcp = MagicMock()
        monkeypatch.setattr(dns.tsigkeyring, 'from_text', mock_from_text)
        monkeypatch.setattr(dns.update, 'Update', mock_update_cls)
        monkeypatch.setattr(dns.query, 'tcp', mock_tcp)

        app._manage_record(
            key='foo', zone='example.com', type='A', action='del'
        )

        # keyring built from the zone key
        mock_from_text.assert_called_once_with(
            {'example.com': 'secret'}
        )
        # TSIG update with the zone name and the selected algorithm
        mock_update_cls.assert_called_once_with(
            'example.com.',
            keyring='MOCK_KEYRING',
            keyalgorithm=dns.tsig.HMAC_MD5
        )
        mock_update = mock_update_cls.return_value
        mock_update.delete.assert_called_once_with('foo', 'A')
        mock_update.add.assert_not_called()
        # the update message is sent to the zone server
        mock_tcp.assert_called_once_with(
            mock_update, '127.0.0.1', port=53
        )

    def test_del_record_with_port(self, monkeypatch):
        import dns.update, dns.query
        app = self._app_with_zone({
            'ip': '127.0.0.1', 'port': '5353',
            'key': 'secret', 'algorithm': 'hmac-sha512'
        })
        mock_from_text = MagicMock()
        mock_update_cls = MagicMock()
        mock_tcp = MagicMock()
        monkeypatch.setattr(dns.tsigkeyring, 'from_text', mock_from_text)
        monkeypatch.setattr(dns.update, 'Update', mock_update_cls)
        monkeypatch.setattr(dns.query, 'tcp', mock_tcp)

        app._manage_record(
            key='bar', zone='example.com', type='AAAA', action='del'
        )

        mock_update_cls.assert_called_once_with(
            'example.com.',
            keyring=mock_from_text.return_value,
            keyalgorithm=dns.tsig.HMAC_SHA512
        )
        mock_update = mock_update_cls.return_value
        mock_update.delete.assert_called_once_with('bar', 'AAAA')
        mock_tcp.assert_called_once_with(
            mock_update, '127.0.0.1', port=5353
        )

    def test_add_record(self, monkeypatch):
        import dns.update, dns.query
        app = self._app_with_zone({
            'ip': '127.0.0.1', 'key': 'secret', 'algorithm': 'hmac-md5'
        })
        mock_update_cls = MagicMock()
        mock_tcp = MagicMock()
        monkeypatch.setattr(dns.tsigkeyring, 'from_text', MagicMock())
        monkeypatch.setattr(dns.update, 'Update', mock_update_cls)
        monkeypatch.setattr(dns.query, 'tcp', mock_tcp)

        # ttl given as str, type given as int: both are coerced
        app._manage_record(
            key='www', ttl='3600', type=1, zone='example.com',
            content='1.2.3.4', action='add'
        )

        mock_update = mock_update_cls.return_value
        mock_update.add.assert_called_once_with(
            'www', 3600, '1', '1.2.3.4'
        )
        mock_update.delete.assert_not_called()
        mock_tcp.assert_called_once_with(
            mock_update, '127.0.0.1', port=53
        )

    def test_unknown_action_raises(self, monkeypatch):
        import dns.update, dns.query
        app = self._app_with_zone({
            'ip': '127.0.0.1', 'key': 'secret', 'algorithm': 'hmac-md5'
        })
        mock_update_cls = MagicMock()
        mock_tcp = MagicMock()
        monkeypatch.setattr(dns.tsigkeyring, 'from_text', MagicMock())
        monkeypatch.setattr(dns.update, 'Update', mock_update_cls)
        monkeypatch.setattr(dns.query, 'tcp', mock_tcp)

        with pytest.raises(WrongDnsUpdateMethod):
            app._manage_record(
                key='foo', zone='example.com', type='A', action='update'
            )

        # nothing was applied or sent
        mock_update = mock_update_cls.return_value
        mock_update.add.assert_not_called()
        mock_update.delete.assert_not_called()
        mock_tcp.assert_not_called()
