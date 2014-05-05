# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:

import cherrypy
from passlib.apache import HtpasswdFile
import dnscherry.auth

SESSION_KEY = '_cp_username'

class Auth(dnscherry.auth.Auth):

    def __init__(self, config):
        self.logout_button = True
        self.ht = HtpasswdFile(config ['auth.htpasswd.file'])

    def check_credentials(self, username, password):
        try:
            return self.ht.check_password(username, password)
        #older versions of passlib doesn't have check_password
        except AttributeError:
            username = str(username)
            password = str(password)
            return self.ht.verify(username, password)

