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
        return self.ht.check_password(username, password)

    def check_auth(self):
        username = cherrypy.session.get(SESSION_KEY)
        if username:
           return username
        else:
           raise cherrypy.HTTPRedirect("/signin")
