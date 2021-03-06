#    This file is part of RDF-REST <http://champin.net/2012/rdfrest>
#    Copyright (C) 2011-2012 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
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
from rdflib.graph import Graph, ModificationException
from urllib.parse import quote_plus
import urllib.parse

def add_uri_params(uri, parameters):
    """Add query-string parameters to a given URI.

    :param basestring uri:        the URI to add the paramateres to
    :para  dict-like  parameters: the parameters to add to the URI

    """
    split = list(urisplit(uri))
    if split[3] is None:
        lst = []
    else:
        lst = [ split[3] ]
    for key, values in parameters.items():
        if not isinstance(values, list):
            values = [values]
        for val in values:
            lst.append("%s=%s" % (quote_plus(str(key)), quote_plus(str(val))))
    split[3] = "&".join(lst)
    return uriunsplit(split)

def bounded_description(node, graph, fill=None, prune=None):
    """Extract from graph a bounded description of node.

    :param node: the node (uri or blank) to return a description of
    :param graph: the graph from which to retrieve the description
    :param fill: if provided, fill this graph rather than a fresh one, and return it
    :param prune: if provided, a container of bnodes that should not be recursed into
    """
    if prune is None:
        prune = []
    triples = graph.triples
    if fill is None:
        ret = Graph()
    else:
        ret = fill
    add = ret.add
    waiting = {node}
    seen = set()
    while waiting:
        node = waiting.pop()
        for t_in in triples((None, None, node)):
            add(t_in)
            s = t_in[0]
            if isinstance(s, BNode) and s not in prune:
                if s not in seen:
                    waiting.add(s)
        for t_out in triples((node, None, None)):
            add(t_out)
            o = t_out[2]
            if isinstance(o, BNode) and o not in prune:
                if o not in seen:
                    waiting.add(o)
        seen.add(node)
    return ret

def cache_result(callabl):
    """Decorator for caching the result of a callable.

    It is assumed that `callabl` only has a `self` parameter, and always
    returns the same value.
    """
    cache_name = "__cache_%s" % callabl.__name__
    
    @wraps(callabl)
    def wrapper(self):
        "the decorated callable"
        # we use __dict__ below rather than hasattr,
        # so that, for class method, the cache is not inherited
        if not cache_name in self.__dict__:
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
    return uri[:uri.rfind("/", 0, -1)+1]

def random_token(length, characters="0123456789abcdefghijklmnopqrstuvwxyz",
                 firstlimit=10):
    """Create a random opaque string.

    :param length:     the length of the string to generate
    :param characters: the range of characters to use
    :param firstlimit: see below

    The parameter `firstlimit` is use to limit the first character of the token
    to a subrange of `characters`. The default behaviour is to first the first
    character of the token to be a digit, which makes it look more "tokenish".
    """
    if firstlimit is None:
        firstlimit = len(characters)
    lst = [ choice(characters[:firstlimit]) ] \
        + [ choice(characters) for _ in range(length-1) ]
    return "".join(lst)

def replace_node_dense(graph, old_node, new_node):
    """Replace a node by another in `graph`.

    :type graph:    rdflib.Graph
    :type old_node: rdflib.Node
    :type new_node: rdflib.Node

    IMPORTANT: this method assumes that old_node will be used in most triples,
    so performs the replacement on all triples.

    You might want to consider using :func:`replace_node_sparse` instead.

    """
    add_triple = graph.add
    rem_triple = graph.remove
    subst = lambda x: (x == old_node) and new_node or x
    all_triples = list(graph) # required as we will modify the graph
    for triple in all_triples:
        rem_triple(triple)
        add_triple([ subst(i) for i in triple ])

def replace_node_sparse(graph, old_node, new_node):
    """Replace a node by another in `graph`.

    :type graph:    rdflib.Graph
    :type old_node: rdflib.Node
    :type new_node: rdflib.Node

    IMPORTANT: this method assumes that old_node will be used in few triples,
    so it searches for those triples in order to replace them.

    You might want to consider using :func:`replace_node_dense` instead.
    """
    subst = lambda x: (x == old_node) and new_node or x
    todel = []
    toadd = []
    for triple in graph.triples((old_node, None, None)):
        todel.append(triple)
        toadd.append([ subst(i) for i in triple ])
    for triple in graph.triples((None, None, old_node)):
        if triple[0] == old_node: continue
        todel.append(triple)
        toadd.append([ subst(i) for i in triple ])
    rem_triple = graph.remove
    for triple in todel:
        rem_triple(triple)
    graph.addN( (s, p, o, graph) for (s, p, o) in toadd )

def urisplit(url):
    """A better urlsplit.

    It differentiates empty querystring/fragment from none.
    e.g.::

      urisplit('http://a.b/c/d') -> ('http', 'a.b', '/c/d', None, None)
      urisplit('http://a.b/c/d?') -> ('http', 'a.b', '/c/d', '', None)
      urisplit('http://a.b/c/d#') -> ('http', 'a.b', '/c/d', None, '')
      urisplit('http://a.b/c/d?#') -> ('http', 'a.b', '/c/d', '', '')

    """
    ret = list(urllib.parse.urlsplit(url))

    if ret[4] == '' and url[-1] != '#':
        ret[4] = None
        before_fragment = -1
    else:
        # there is a (possibly empty) fragment
        # -> remove it and the '#', to test query-string below
        before_fragment = - (len(ret[4]) + 2)

    if ret[3] == '' and url[before_fragment] != '?':
        ret[3] = None

    return urllib.parse.SplitResult(*ret)
    
def uriunsplit(split_uri):
    """A better urlunsplit.

    It differentiates empty querystring/fragment from none.
    e.g.::

      uriunsplit('http', 'a.b', '/c/d', None, None) -> 'http://a.b/c/d'
      uriunsplit('http', 'a.b', '/c/d', '', None) -> 'http://a.b/c/d?'
      uriunsplit('http', 'a.b', '/c/d', None, '') ->'http://a.b/c/d#'
      uriunsplit('http', 'a.b', '/c/d', '', '') -> 'http://a.b/c/d?#'

    """
    ret = urllib.parse.urlunsplit(split_uri)
    if split_uri[4] == "":
        ret += "#"
    if split_uri[3] == "":
        if split_uri[4] is None:
            ret += "?"
        else:
            prefix, suffix = ret.split('#', 1)
            ret = prefix + "?#" + suffix
    return ret

def wrap_exceptions(extype):
    """I return a function decorator wrapping all exceptions as `extype`.
    """
    assert issubclass(extype, BaseException), \
        "Did you write @wrap_exception instead of @wrap_exception(extype)?"
    def wrap_exceptions_decorator(func):
        """The decorator returned by wrap_exceptions"""
        @wraps(func)
        def wrapped(*args, **kw):
            """The decorated function"""
            try:
                return func(*args, **kw)
            except BaseException as ex:
                raise extype(ex)
        return wrapped
    return wrap_exceptions_decorator

def wrap_generator_exceptions(extype):
    """I return a generator decorator wrapping all exceptions as `extype`.
    """
    assert issubclass(extype, BaseException), \
        "Did you write @wrap_exception instead of @wrap_exception(extype)?"
    def wrap_generator_exceptions_decorator(func):
        """The decorator returned by wrap_generator_exceptions"""
        @wraps(func)
        def wrapped(*args, **kw):
            """The decorated function"""
            try:
                for i in func(*args, **kw):
                    yield i
            except BaseException as ex:
                raise extype(ex)
        return wrapped
    return wrap_generator_exceptions_decorator


    
class Diagnosis(object):
    """I contain a list of problems and eval to True if there is no problem.
    """
    # too few public methods #pylint: disable=R0903
    def __init__(self, title="diagnosis", errors=None, traceback=None):
        self.title = title
        if errors is None:
            errors = []
        else:
            errors = list(errors)
        self.errors = errors
        self.traceback = traceback

    def __bool__(self):
        return len(self.errors) == 0

    def __iter__(self):
        return iter(self.errors)

    def __str__(self):
        if self.errors:
            return "%s: ko\n* %s\n" % (self.title, "\n* ".join(self.errors))
        else:
            return "%s: ok" % self.title

    def __repr__(self):
        return "Diagnosis(%r, %r)" % (self.title, self.errors)

    def __and__(self, rho):
        if isinstance(rho, Diagnosis):
            return Diagnosis(self.title,
                             self.errors + rho.errors,
                             self.traceback or rho.traceback,
            )
        elif self:
            return rho
        else:
            return self

    def __rand__(self, lho):
        if isinstance(lho, Diagnosis):
            return Diagnosis(lho.title,
                             lho + self.errors,
                             lho.traceback or self.traceback,
            )
        elif not lho:
            return lho
        else:
            return self

    def append(self, error_msg):
        """Append a problem to this diagnosis.
        """
        self.errors.append(error_msg)


class ReadOnlyGraph(Graph):
    """A read-only version of rdflib.Graph.
    """
    # Invalid name #pylint: disable=C0103
    # Redefining built-in #pylint: disable=W0622

    def __init__(self, store_or_graph='default', identifier=None,
                 namespace_manager=None):
        if isinstance(store_or_graph, Graph):
            assert identifier is None and namespace_manager is None
            Graph.__init__(self, store_or_graph.store,
                           store_or_graph.identifier,
                           store_or_graph.namespace_manager)
        else:
            Graph.__init__(self, store_or_graph, identifier, namespace_manager)
        
    def destroy(self, configuration):
        """Raise a ModificationException as this graph is read-only.
        """
        raise ModificationException() #ReadOnlyGraph does not support this

    def commit(self):
        """Raise a ModificationException as this graph is read-only.
        """
        raise ModificationException() #ReadOnlyGraph does not support this

    def rollback(self):
        """Raise a ModificationException as this graph is read-only.
        """
        raise ModificationException() #ReadOnlyGraph does not support this
    
    def open(self, configuration, create=False):
        """Raise a ModificationException if create, as this graph is read-only.
        """
        if create:
            raise ModificationException() #ReadOnlyGraph does not support this
        else:
            Graph.open(self, configuration, create)

    def add(self, spo):
        """Raise a ModificationException as this graph is read-only.
        """
        (s, p, o) = spo
        raise ModificationException() #ReadOnlyGraph does not support this

    def addN(self, quads):
        """Raise a ModificationException as this graph is read-only.
        """
        raise ModificationException() #ReadOnlyGraph does not support this

    def remove(self, spo):
        """Raise a ModificationException as this graph is read-only.
        """
        (s, p, o) = spo
        raise ModificationException() #ReadOnlyGraph does not support this

    def __iadd__(self, other):
        """Raise a ModificationException as this graph is read-only.
        """
        raise ModificationException() #ReadOnlyGraph does not support this

    def __isub__(self, other):
        """Raise a ModificationException as this graph is read-only.
        """
        raise ModificationException() #ReadOnlyGraph does not support this

    def set(self, spo):
        """Raise a ModificationException as this graph is read-only.
        """
        (subject, predicate, object) = spo
        raise ModificationException() #ReadOnlyGraph does not support this

    def bind(self, prefix, namespace, override=True):
        """Raise a ModificationException as this graph is read-only.
        """
        raise ModificationException() #ReadOnlyGraph does not support this

    def parse(self, source=None, publicID=None, format=None,
              location=None, file=None, data=None, **args):
        """Raise a ModificationException as this graph is read-only.
        """
        raise ModificationException() #ReadOnlyGraph does not support this

    def load(self, source, publicID=None, format="xml"):
        """Raise a ModificationException as this graph is read-only.
        """
        raise ModificationException() #ReadOnlyGraph does not support this
