import cherrypy

cherrypy.config.update('server.config')

import sitemap

cherrypy.server.quickstart()
cherrypy.engine.start()

