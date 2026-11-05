#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from unittest.mock import MagicMock
import cherrypy
from dnscherry.auth.modNone import Auth

# Provide a mock request object for header lookups
cherrypy.request = MagicMock()
cherrypy.request.headers = {}
cherrypy.request.query_string = ''


class TestModNone(object):

    def test_init_no_header_config(self):
        """When 'auth.user_header_name' is absent, user_header_name is None."""
        auth = Auth({}, None)
        assert auth.user_header_name is None
        assert auth.logout_button is False

    def test_init_with_header_config(self):
        """When 'auth.user_header_name' is present, reads 'auth.none.user_header_name'."""
        config = {
            'auth.user_header_name': 'X-User',
            'auth.none.user_header_name': 'X-User',
        }
        auth = Auth(config, None)
        assert auth.user_header_name == 'X-User'

    def test_check_auth_no_header_name(self):
        """check_auth returns 'unknown user' when user_header_name is None."""
        auth = Auth({}, None)
        assert auth.check_auth() == 'unknown user'

    def test_check_auth_header_present(self):
        """check_auth returns header value when the header is present."""
        config = {
            'auth.user_header_name': 'X-User',
            'auth.none.user_header_name': 'X-User',
        }
        auth = Auth(config, None)
        cherrypy.request.headers = {'X-User': 'testuser'}
        assert auth.check_auth() == 'testuser'

    def test_check_auth_header_missing(self):
        """check_auth raises HTTPError 403 when the header is absent."""
        config = {
            'auth.user_header_name': 'X-User',
            'auth.none.user_header_name': 'X-User',
        }
        auth = Auth(config, None)
        cherrypy.request.headers = {}
        with pytest.raises(cherrypy.HTTPError) as exc_info:
            auth.check_auth()
        assert "403" in exc_info.value.status
