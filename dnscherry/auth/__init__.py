# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
# The MIT License (MIT)
# DnsCherry
# Copyright (c) 2014 Carpentier Pierre-Francois

import cherrypy
import dnscherry

SESSION_KEY = '_cp_username'

class Auth(object):

    def __init__(self, config, logger=None):
        """ module initialization
        initialize the auth module
        the 'auth' section of the ini file is passed by 'config'
        @hash config: the 'auth' section of the ini file
        @logger logger: the dnscherry error logger
        """
        self.logger = logger

    def check_credentials(self, username, password):
        """ Check credential function (called on login)
        @str username: the login to check
        @str password: the password to check
        @rtype: bool (True if authentificated, False otherwise)
        """
        return True

    def _get_param(self, key, config, default=None):
        """ Get configuration parameter "key" from config
        @str key: the key to get
        @dict config: the configuration (dictionnary)
        @str default: the default value if parameter "key" is not present
        @rtype: str (value of config['key'] if present default otherwith
        """
        if key in config:
            return config[key]
        if not default is None:
            return default
        else:
            raise dnscherry.MissingParameter('auth', key)

    def _logger(self, severity, message):
        if self.logger:
            self.logger.error(
                msg = message,
                severity = severity
                )


    def end_session(self):
        """ remove the session from the session database
        @rtype: str, the owner of the removed session
        """
        sess = cherrypy.session
        username = sess.get(SESSION_KEY, None)
        sess[SESSION_KEY] = None
        if username:
            cherrypy.request.login = None
            return username
        else:
            raise cherrypy.HTTPRedirect("/signin")

    def check_auth(self):
        """ check run at every hit on restricted pages
        this implementation checks if the user has a session
        if session is not valide, must redirect to /signin
        @rtype: str, the owner of the session
        """
        username = cherrypy.session.get(SESSION_KEY)
        if username:
           return username
        else:
           raise cherrypy.HTTPRedirect("/signin")
