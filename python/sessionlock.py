"""
A number of functions for locksession
"""

import cherrypy
import hmac,sha
from datetime import datetime,timedelta
from base import session,cookie,utils,template,config

##
## Checking the connection and Session
##

LS_SIG = 'ls_sig'
LS_TIMESTAMP = 'ls_timestamp'

def check_ssl():
    return cherrypy.request.base[:6] == 'https:'

def check_session():
    """
    called as a hook on every request to make sure it is authentic
    """

    cherrypy.serving.LOCKSESSION_STATUS = False

    if cherrypy.request.params.has_key(LS_TIMESTAMP) or cherrypy.request.params.has_key(LS_SIG):
        if not cherrypy.request.params.has_key(LS_TIMESTAMP) or not cherrypy.request.params.has_key(LS_SIG):
            try:
                del cherrypy.request.params[LS_SIG]
            except: pass
            try:
                del cherrypy.request.params[LS_TIMESTAMP]
            except: pass
            return
        
        timestamp_str = cherrypy.request.params[LS_TIMESTAMP]
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%SZ')
        sig = cherrypy.request.params[LS_SIG]

        del cherrypy.request.params[LS_SIG]

        diff = datetime.utcnow() - timestamp

        # more than 5 minutes ago?
        if diff > timedelta(0, 300):
            print "timeout: " + str(diff)
            return

        # check the hash
        token = cherrypy.session.get('token',None)
        if not token:
            print "no token"
            return

        url = cherrypy.request.path_info + '?'
        keys = cherrypy.request.params.keys()
        keys.sort()
        url += '&'.join(utils.urlencode(k) + '=' + utils.urlencode(cherrypy.request.params[k]) for k in keys)
        print "URL to sign is: " + url

        # now the timestamp should be removed before the rest of the processing
        del cherrypy.request.params[LS_TIMESTAMP]

        mac = hmac.new(token, url, sha)

        if sig != mac.hexdigest():
            return

        cherrypy.serving.LOCKSESSION_STATUS = True



cherrypy.tools.locksession = cherrypy.Tool('before_handler', check_session)

##
## Controller
##

class Controller:

    @cherrypy.expose
    def test(self):
        return template.render('locksession/test')

    @cherrypy.expose
    def token_setup(self, return_url=None):
        token = utils.random_string(20)
        session.put('token',token)
        cookie.set('token',token, secure_p=True)
        if return_url:
            raise cherrypy.HTTPRedirect(return_url)
        else:
            return template.render('locksession/token_setup')

    @cherrypy.expose
    def token_get_ssl(self):
        if not session.has('token'):
            cookie.set('token','', secure_p=True)
        return template.render('locksession/token_get_ssl')

    @cherrypy.expose
    def token_get(self):
        return template.render('locksession/token_get')
