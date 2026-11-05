#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import os
import cherrypy
from unittest.mock import MagicMock
from passlib.apache import HtpasswdFile
from dnscherry.auth.modHtpasswd import Auth
from dnscherry import MissingParameter

cherrypy.log = MagicMock()

# Build a temporary htpasswd file used by all tests in this module
_ht = HtpasswdFile()
_ht.set_password('jwatson', 'passwordwatson')
_ht.set_password('admin', 'adminpass')
_TMP_HTFILE = os.path.join('/tmp/opencode', 'test_dnscherry_htpasswd')
_ht.save(_TMP_HTFILE)


class TestModHtpasswd(object):

    def test_init_success(self):
        """__init__ with a valid htpasswd file path succeeds."""
        config = {'auth.htpasswd.file': _TMP_HTFILE}
        auth = Auth(config, None)
        assert auth.logout_button is True
        assert auth.htpasswdfile == _TMP_HTFILE

    def test_init_missing_param(self):
        """__init__ without 'auth.htpasswd.file' raises MissingParameter."""
        with pytest.raises(MissingParameter):
            Auth({}, None)

    def test_check_credentials_success(self):
        """check_credentials returns True for valid user and password."""
        config = {'auth.htpasswd.file': _TMP_HTFILE}
        auth = Auth(config, None)
        assert auth.check_credentials('jwatson', 'passwordwatson') is True

    def test_check_credentials_wrong_password(self):
        """check_credentials returns False for a wrong password."""
        config = {'auth.htpasswd.file': _TMP_HTFILE}
        auth = Auth(config, None)
        assert auth.check_credentials('jwatson', 'wrongpass') is False

    def test_check_credentials_unknown_user(self):
        """check_credentials returns a falsy value for an unknown user."""
        config = {'auth.htpasswd.file': _TMP_HTFILE}
        auth = Auth(config, None)
        assert not auth.check_credentials('nouser', 'anypass')

    def test_check_credentials_attributeerror_fallback_to_verify(self):
        """When check_password raises AttributeError (older passlib),
        check_credentials falls back to ht.verify()."""
        config = {'auth.htpasswd.file': _TMP_HTFILE}
        auth = Auth(config, None)
        # simulate older passlib: check_password doesn't exist
        mock_ht = MagicMock()
        mock_ht.check_password.side_effect = AttributeError(
            'check_password not available')
        mock_ht.verify.return_value = True
        auth.ht = mock_ht
        result = auth.check_credentials('admin', 'adminpass')
        assert result is True
        mock_ht.verify.assert_called_once_with('admin', 'adminpass')
