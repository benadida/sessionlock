"""
templating

Ben Adida (ben@adida.net)
"""

from Cheetah.Template import Template
import base.utils
from base import config
import Cheetah.Filters


PREFIX = config.root + '/templates/'

def render(template):
	return Template(file= PREFIX + template + ".tmpl", searchList = [base.utils.parent_vars(1)]).respond()

def renderString(string):
	return Template(string, searchList = [base.utils.parent_vars(1)]).respond()

class EncodeUnicode(Cheetah.Filters.Filter):
    def filter(self, val, **kw):
        """Encode Unicode strings, by default in UTF-8"""
        if kw.has_key('encoding'):
            encoding = kw['encoding']
        else:
            encoding='utf8'
                            
        if type(val) == type(u''):
            filtered = val.encode(encoding)
        else:
            filtered = str(val)
        return filtered
