"""
A simple layer on top of cherrypy sessions
"""

import cherrypy

def get(k):
    return cherrypy.session[k]

def has(k):
    return cherrypy.session.has_key(k)

def put(k,v):
    cherrypy.session[k] = v

def clear(k):
    del cherrypy.session[k]
