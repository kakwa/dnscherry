# -*- coding: utf-8 -*-
# vim:set expandtab tabstop=4 shiftwidth=4:

# Form based authentication for CherryPy. Requires the
# Session tool to be loaded.
#

import cherrypy

SESSION_KEY = '_cp_username'

class Auth(object):

    def __init__(self, config):
        pass

    def check_credentials(self, username, password):
        return True

    def check_auth(self):
        return True

    def end_session(self):
        sess = cherrypy.session
        username = sess.get(SESSION_KEY, None)
        sess[SESSION_KEY] = None
        if username:
            cherrypy.request.login = None
            return username
        else:
            return 'unknow'

