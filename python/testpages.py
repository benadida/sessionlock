"""
Some Test Pages
"""

import cherrypy
from base import session,cookie,utils,template


##
## Controller
##

class Controller:

    @cherrypy.expose
    def one(self, num=0, var1=None, var2=None, var3=None, **args):
        num = int(num)
        return template.render('testpages/index')

    @cherrypy.expose
    def ajax(self, num=0, **args):
        num = int(num)
        return template.render('testpages/ajax')

    @cherrypy.expose
    def stress(self, num=0):
        return template.render('testpages/stress')
