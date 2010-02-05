"""
Simple API for Cookie Handling
"""

import cherrypy

def set(name,value,secure_p=False,domain=None,path="/"):
    cookie = cherrypy.response.cookie
    cookie[name]=value
    cookie[name]['secure'] = secure_p
    cookie[name]['path'] = path

def get(name):
    return cherrypy.request.cookie[name]


