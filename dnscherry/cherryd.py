import cherrypy
from dnscherry import DnsCherry

cherrypy.tree.mount(DnsCherry())
# CherryPy autoreload must be disabled for the flup server to work
cherrypy.config.update({'engine.autoreload.on':False})

