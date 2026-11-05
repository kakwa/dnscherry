#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import pytest
from unittest.mock import MagicMock
import cherrypy
from dnscherry.auth import Auth, SESSION_KEY
from dnscherry import MissingParameter


class TestBaseAuth(object):
    """Unit tests for the base class dnscherry.auth.Auth."""

    def test_init_stores_logger(self):
        """__init__ stores the passed logger on self.logger."""
        logger = MagicMock()
        auth = Auth({}, logger)
        assert auth.logger is logger

    def test_init_default_logger(self):
        """__init__ with no logger leaves self.logger as None."""
        auth = Auth({})
        assert auth.logger is None

    def test_check_credentials_default(self):
        """Base Auth.check_credentials returns True (default implementation)."""
        auth = Auth({}, None)
        assert auth.check_credentials('any', 'any') is True

    # _get_param
    def test_get_param_found(self):
        """_get_param returns the value when the key is present."""
        auth = Auth({}, None)
        assert auth._get_param('key', {'key': 'value'}) == 'value'

    def test_get_param_default(self):
        """_get_param returns the default when the key is absent and a default is given."""
        auth = Auth({}, None)
        assert auth._get_param('missing', {}, 'default') == 'default'

    def test_get_param_missing_raises(self):
        """_get_param raises MissingParameter when key is absent and no default."""
        auth = Auth({}, None)
        with pytest.raises(MissingParameter):
            auth._get_param('missing', {})

    # _logger
    def test_logger_present(self):
        """_logger forwards severity/message to logger.error when a logger exists."""
        logger = MagicMock()
        auth = Auth({}, logger)
        auth._logger(logging.CRITICAL, 'hello')
        logger.error.assert_called_once_with(
            msg='hello', severity=logging.CRITICAL)

    def test_logger_absent(self):
        """_logger is a no-op when no logger is configured."""
        auth = Auth({}, None)
        # must not raise
        auth._logger(logging.CRITICAL, 'hello')

    # check_auth
    def test_check_auth_with_session(self):
        """check_auth returns the username stored in the session."""
        auth = Auth({}, None)
        cherrypy.session = {SESSION_KEY: 'alice'}
        assert auth.check_auth() == 'alice'

    def test_check_auth_without_session(self):
        """check_auth raises HTTPRedirect to /signin when there is no session."""
        auth = Auth({}, None)
        cherrypy.session = {}
        with pytest.raises(cherrypy.HTTPRedirect):
            auth.check_auth()

    # end_session
    def test_end_session_with_user(self):
        """end_session clears the session, resets login and returns the username."""
        auth = Auth({}, None)
        cherrypy.request = MagicMock()
        cherrypy.session = {SESSION_KEY: 'bob'}
        result = auth.end_session()
        assert result == 'bob'
        assert cherrypy.request.login is None
        assert cherrypy.session[SESSION_KEY] is None

    def test_end_session_without_user(self):
        """end_session raises HTTPRedirect to /signin when there is no session user."""
        auth = Auth({}, None)
        cherrypy.session = {}
        with pytest.raises(cherrypy.HTTPRedirect):
            auth.end_session()
