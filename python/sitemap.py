"""
The sitemap for locked session
"""

import cherrypy, sessionlock, testpages
from base import session, template

class Root(object):
  @cherrypy.expose
  def index(self):
    return template.render('index')

  locksession = sessionlock.Controller()
  testpages = testpages.Controller()
  
root = cherrypy.tree.mount(Root(), '/', config='sessionlock.config')
