# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:
# The MIT License (MIT)
# DnsCherry
# Copyright (c) 2014 Carpentier Pierre-Francois


import cherrypy
from passlib.apache import HtpasswdFile
import dnscherry.auth

SESSION_KEY = '_cp_username'

class Auth(dnscherry.auth.Auth):

    def __init__(self, config, logger=None):
        self.logout_button = True
        self.htpasswdfile = self._get_param('auth.htpasswd.file', config, None)
        self.ht = HtpasswdFile(self.htpasswdfile)

    def check_credentials(self, username, password):
        try:
            return self.ht.check_password(username, password)
        #older versions of passlib doesn't have check_password
        except AttributeError:
            username = str(username)
            password = str(password)
            return self.ht.verify(username, password)

