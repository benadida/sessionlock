"""
Utils for Doing things with rdflib graphs

Ben Adida
2006-09-27
"""

import rdflib

# Dublin Core
DC = rdflib.Namespace("http://purl.org/dc/elements/1.1/")

# Prism
PRISM = rdflib.Namespace("http://prismstandard.org/namespaces/1.2/basic/")

# WD
WD = rdflib.Namespace("http://webda.sh/rdf/")

def _seq_cmp(x,y):
    return (int(x[0]) - int(y[0]))

# because rdflib sequences are broken
def fix_sequence(seq):
    seq._list.sort(_seq_cmp)