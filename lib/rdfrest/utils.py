#    This file is part of RDF-REST <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Universite de Lyon <http://www.universite-lyon.fr>
#
#    RDF-REST is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RDF-REST is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with RDF-REST.  If not, see <http://www.gnu.org/licenses/>.

"""
I define useful functions and classes for RDF RESTful services.
"""
from functools import wraps
from random import choice
from rdflib import BNode, URIRef
from urlparse import SplitResult, urlsplit

def cache_result(callabl):
    """Decorator for caching the result of a callable.

    It is assumed that `callabl` only has a `self` parameter, and always
    returns the same value.
    """
    cache_name = "__cache_%s" % callabl.__name__
    
    @wraps(callabl)
    def wrapper(self):
        "the decorated callable"
        ret = getattr(self, cache_name, None)
        if not hasattr(self, cache_name):
            ret = callabl(self)
            setattr(self, cache_name, ret)
        else:
            ret = getattr(self, cache_name)
        return ret
    return wrapper

def check_new(graph, node):
    """Check that node is absent from graph.
    """
    if next(graph.predicate_objects(node), None) is not None:
        return False
    if next(graph.subject_predicates(node), None) is not None:
        return False
    return True

def coerce_to_uri(obj, base=None):
    """I convert `obj` to a URIRef.
    
    :param obj:  either an `rdflib.URIRef`, an object with a `uri` attribute
                 (assumed to be a URIRef) or a string-like URI.
    :param base: if provided, a string-like absolute URI used to resolve `obj`
                 if it is itself a string.

    :rtype: rdflib.URIRef
    """
    assert obj is not None
    ret = obj
    if not isinstance(ret, URIRef):
        ret = getattr(ret, "uri", None) or str(ret)
    if not isinstance(ret, URIRef):
        ret = URIRef(ret, base)
    return ret

def coerce_to_node(obj, base=None):
    """I do the same as :func:`coerce_to_uri` above, but in addition:

    * if `obj` is None, I will return a fresh BNode
    * if `obj` is a BNode, I will return it
    """
    if obj is None:
        return BNode()
    elif isinstance(obj, BNode):
        return obj
    else:
        return coerce_to_uri(obj, base)

def extsplit(path_info):
    """Split a URI path into the extension-less path and the extension.
    """
    dot = path_info.rfind(".")
    slash = path_info.rfind("/")
    if dot < slash:
        return path_info, None
    else:
        return path_info[:dot], path_info[dot+1:]
    #

def make_fresh_uri(graph, prefix, suffix=""):
    """Creates a URIRef which is not in graph, with given prefix and suffix.
    """
    length = 2
    while True:
        node = URIRef("%s%s%s" % (prefix, random_token(length), suffix))
        if check_new(graph, node):
            return node
        length += 1

def parent_uri(uri):
    """Retun the parent URI of 'uri'.

    :type uri: basestring
    """
    return uri[:uri[:-1].rfind("/")+1]

def random_token(length, characters="abcdefghijklmnopqrstuvwxyz0123456789"):
    """Create a random opaque string.

    :param length:     the length of the string to generate
    :param characters: the range of characters to use
    """
    return "".join( choice(characters) for i in range(length) )

def replace_node(graph, old_node, new_node):
    """Replace a node by another in `graph`.

    :type graph:    rdflib.Graph
    :type old_node: rdflib.Node
    :type new_node: rdflib.Node
    """
    add_triple = graph.add
    rem_triple = graph.remove
    subst = lambda x: (x == old_node) and new_node or x
    for triple in graph:
        # heuristics: most triple will involve old_node,
        # (this method is used with posted graphs to name the created resource)
        # so we transform all triples,
        # without even checking if they contain old_node
        rem_triple(triple)
        add_triple([ subst(i) for i in triple ])
    old_node = new_node

def urisplit(url):
    """A better urlsplit.

    It differentiates empty querystring/fragment from none.
    e.g.::

      urisplit('http://a.b/c/d') -> ('http', 'a.b', '/c/d', None, None)
      urisplit('http://a.b/c/d?') -> ('http', 'a.b', '/c/d', '', None)
      urisplit('http://a.b/c/d#') -> ('http', 'a.b', '/c/d', None, '')
      urisplit('http://a.b/c/d?#') -> ('http', 'a.b', '/c/d', '', '')

    """
    ret = list(urlsplit(url))

    if ret[4] == '' and url[-1] != '#':
        ret[4] = None
        before_fragment = -1
    else:
        # there is a (possibly empty) fragment
        # -> remove it and the '#', to test query-string below
        before_fragment = - (len(ret[4]) + 2)

    if ret[3] == '' and url[before_fragment] != '?':
        ret[3] = None

    return SplitResult(*ret)
    
class Diagnosis(object):
    """I contain a list of problems and eval to True if there is no problem.
    """
    # too few public methods #pylint: disable=R0903
    def __init__(self, title="diagnosis", errors=None):
        self.title = title
        if errors is None:
            errors = []
        else:
            errors = list(errors)
        self.errors = errors

    def __nonzero__(self):
        return len(self.errors) == 0

    def __iter__(self):
        return iter(self.errors)

    def __str__(self):
        if self.errors:
            return "%s: ko\n* %s" % (self.title, "\n* ".join(self.errors))
        else:
            return "%s: ok" % self.title

    def __repr__(self):
        return "Diagnosis(%r, %r)" % (self.title, self.errors)

    def __and__(self, rho):
        if isinstance(rho, Diagnosis):
            return Diagnosis(self.title, self.errors + rho.errors)
        elif self:
            return rho
        else:
            return self

    def __rand__(self, lho):
        if isinstance(lho, Diagnosis):
            return Diagnosis(lho.title, lho + self.errors)
        elif not lho:
            return lho
        else:
            return self

    def append(self, error_msg):
        """Append a problem to this diagnosis.
        """
        self.errors.append(error_msg)
