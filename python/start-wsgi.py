import cherrypy

cherrypy.config.update('server.config')

import sitemap

cherrypy.engine.start()

try:
  from flup.server.scgi import WSGIServer
  WSGIServer(sitemap.root).run()
finally:
  cherrypy.engine.stop()