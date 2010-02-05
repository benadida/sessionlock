"""
Utilities for Page

Ben Adida - ben@adida.net
2005-04-11
"""

import urllib, urllib2, re, sys, datetime, urlparse, string, random
import cherrypy
import threading
import simplejson
from base import htmlsanitizer, config

# takes a dictionary and makes sure all values are lists
def listify(d):
    new_d = dict()
    
    for (k,v) in d.items():
        # if it's not a list make it a list
        if not isinstance(v,list):
            v = [v]
        
        new_d[k] = v
    
    return new_d

    
def log(msg):
    if config.DEBUG and config.PYTHON_DEBUG:
        _log(msg)
        
def sql_log(msg):
    if config.DEBUG and config.SQL_DEBUG:
        _log(msg)

def _log(msg):
    prepend = '============>'
    cherrypy.log(prepend + ' ' + msg.encode('utf-8'))
    

def parent_vars(level, extra_vars = None):
    """
    Goes up the indicated number of levels and returns the equivalent of calling locals()
    in that scope
    """
    try: 1/0
    except: frame = sys.exc_traceback.tb_frame

    # Go up in the frame stack
    for i in range(level+1): frame = frame.f_back

    loc, glob = frame.f_locals, frame.f_globals
    

    if extra_vars != None:
        loc = loc.copy()
        for key in extra_vars.keys():
            loc[key] = extra_vars[key]
            
    return loc


def load_url(url):
    """
    Loads and returns the content of a URL.
    No streaming for now.
    """

    req = urllib2.Request(url = url)
    f = urllib2.urlopen(req)
    return f.read()

def get_select_options(html, select_name):
    """
    Takes a chunk of HTML, looks for a select, and outputs a list of options of that select.

    Looks only at value='', not at the pretty display.
    """

    # a regular expression to match the select block
    pattern = re.compile('<select *name="%s"[^>]*>(.*?)</select>' % select_name, re.MULTILINE | re.IGNORECASE | re.DOTALL)
    m = pattern.search(html)
    if (m == None):
        # we have no match, try another pattern
        pattern = re.compile('<select *name=%s[^>]*>(.*?)</select>' % select_name, re.MULTILINE | re.IGNORECASE | re.DOTALL)
        m = pattern.search(html)

    select_block = m.group()

    # extract the options from the select block
    pattern = re.compile('<option[^>]*value="(.*?)">(.*?)</option>', re.IGNORECASE)
    options = pattern.findall(select_block)

    return options

def csv_safe(string):
    """
    Make a string safe for a CSV field
    """
    # let's backslash all the quotation marks anyways
    string = str(string)
    string = string.replace('"','\\"')

    if "," not in string and "\n" not in string:
        return string

    return '"' + string + '"'

def js_sq_safe(sol, depth=1, escape_newlines = True):
    """
    Make a string or a list safe for Javascript
    """
    if not sol:
        return ''
           
    if isinstance(sol, list):
        l = []
        for el in sol:
            l.append(_js_sq_safe(el, depth, escape_newlines))
        return l
    else:
        return _js_sq_safe(sol, depth, escape_newlines)

def _js_sq_safe(string, depth, escape_newlines):
    repl_str = "\\" * depth + "'"
    string = string.replace("'",repl_str)

    if escape_newlines:
        string = string.replace('\r\n',"\\n")
        string = string.replace('\r',"\\n")
        string = string.replace("\n","\\n")
        
    return string

def js_dq_safe(sol, depth=1):
  """
  Make a string or a list safe for Javascript
  """
  if not sol:
      return ''
         
  if isinstance(sol, list):
      l = []
      for el in sol:
          l.append(_js_dq_safe(el))
      return l
  else:
      return _js_dq_safe(sol, depth)

def _js_dq_safe(string, depth=1):
    """
    Make a string safe for Javascript
    """
    repl_str = "\\" * depth + '"'
    string = string.replace('"',repl_str)
    return string    

def html_dq_safe(string):
    """
    Make a string safe for HTML with double quotes
    """
    if not string:
        return string
    string = string.replace('"','&quot;')
    return string
    
def trunc_string(string, length=50):
    """
    Make a string short enough for display
    """
    if len(string)>length:
        return "%s..." % string[:length-3]
    else:
        return string

def urlencode(str):
    """
    URL encode
    """
    if not str:
        return ""

    return urllib.quote(str)

def urlencodeall(str):
    """
    URL encode everything even unresreved chars
    """
    if not str:
        return ""

    return string.join(['%' + s.encode('hex') for s in str], '')

def urldecode(str):
    if not str:
        return ""

    return urllib.unquote(str)

def get_url():
    full_url = cherrypy.request.path
    if cherrypy.request.queryString != None and cherrypy.request.queryString != "":
        full_url += "?" + cherrypy.request.queryString

    return full_url
        
def JSONtoDict(json):
    x=simplejson.loads(json.decode('utf-8'))
    return x
    
def isBlank(s):
    if not isinstance(s, str):
      return True
    else:
      return (len(s.strip()) == 0 )
      
def dictToURLParams(d):
    return '&'.join([i + '=' + urlencode(v) for i,v in d.items()])
##
## XML escaping and unescaping
## 

def xml_escape(s):
    raise Exception('not implemented yet')

def xml_unescape(s):
    new_s = s.replace('&lt;','<').replace('&gt;','>')
    return new_s
    
##
## XSS attack prevention
##

def xss_strip_all_tags(s):
    """
    Strips out all HTML.
    """
    return s
    def fixup(m):
        text = m.group(0)
        if text[:1] == "<":
            return "" # ignore tags
        if text[:2] == "&#":
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        elif text[:1] == "&":
            import htmlentitydefs
            entity = htmlentitydefs.entitydefs.get(text[1:-1])
            if entity:
                if entity[:2] == "&#":
                    try:
                        return unichr(int(entity[2:-1]))
                    except ValueError:
                        pass
                else:
                    return unicode(entity, "iso-8859-1")
        return text # leave as is
        
    return re.sub("(?s)<[^>]*>|&#?\w+;", fixup, s)
    
def xss_strip_unsafe_tags(s):
    """
    Strips any HTML that could be dangerous
    """
    return htmlsanitizer._sanitizeHTML(s, 'utf-8', None)
    
# simple url checking / validation

def url_check(url):
  """
  Parses a URL and errors out if its not scheme http or https or has no net location
  """
  
  url_tuple = urlparse.urlparse(url)
  if url_tuple[0] == 'http' or url_tuple[0] == 'https' and url_tuple[1] != "":
    return url
  else:
    raise Exception('bad url')

def url_truncate(url):
  """
  Parses a URL and truncates it after the domain part
  """
  
  url_tuple = urlparse.urlparse(url)
  return url_tuple[0] + '://' + url_tuple[1]
  
def url_get_domain(url):
    """
    Parses a URL and truncates it after the domain part
    """

    url_tuple = urlparse.urlparse(url)
    return url_tuple[1]
 
def over_ssl_p():
    return cherrypy.request.scheme == 'https'


random.seed()

def random_string(length=20):
    random.seed()
    ALPHABET = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    r_string = ''
    for i in range(length):
        r_string += random.choice(ALPHABET)

    return r_string
    

