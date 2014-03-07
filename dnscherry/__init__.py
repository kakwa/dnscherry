from easyzone import easyzone
import cherrypy

class DnsCherry(object):

    def _get_jpeg_data(self):
        """This method should return the jpeg data"""
        return ""

    @cherrypy.expose
    def index(self):
        cherrypy.response.headers['Content-Type'] = 'application/jpeg'
        return self._get_jpeg_data()

cherrypy.quickstart(HelloWorld())
