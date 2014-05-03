# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:

import cherrypy
import dnscherry.auth

class Auth(dnscherry.auth.Auth):

    def __init__(self, config):
        # no need for a logout button
        self.logout_button = False
        if 'auth.user_header_name' in config:
            self.user_header_name = config['auth.none.user_header_name']
        else:
            self.user_header_name = None

    def check_auth(self):
        if self.user_header_name is None:
            return 'unknown user'
        else:
            if self.user_header_name in cherrypy.request.headers:
                return cherrypy.request.headers[self.user_header_name]
            else:
                raise cherrypy.HTTPError(
                    "403 Forbidden", "You are not allowed to access this resource.")
