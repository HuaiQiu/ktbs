# -*- coding: utf-8 -*-

#    This file is part of KTBS <http://liris.cnrs.fr/sbt-dev/ktbs>
#    Copyright (C) 2011 Pierre-Antoine Champin <pchampin@liris.cnrs.fr> /
#    Universite de Lyon <http://www.universite-lyon.fr>
#
#    KTBS is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    KTBS is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with KTBS.  If not, see <http://www.gnu.org/licenses/>.
"""
JSON-LD parser and serializer for KTBS.

"""

try:
    import pyld
except ImportError:
    pyld = None

if pyld:
    from json import loads
    from pyld.jsonld import triples
    from rdflib import BNode, Graph, Literal, URIRef

    from rdfrest.parser import register as register_parser
    from rdfrest.serializer import register as register_serializer
    from rdfrest.exceptions import ParseError

    from rdflib import RDF, RDFS
    from ktbs.namespaces import KTBS, KTBS_IDENTIFIERS

    def jsonld2graph(json, base_uri, graph, context=None):
        """
        I feed an rdflib 'graph' with the JSON-LD interpretation of 'json'.

        If 'json' contains no or an incomplete context, an additional 
        'context' can be provided.

        :param json: the JSON-LD interpretation of 'json'
        :param graph: an rdflib Graph()
        :param context: additional context if needed
        """
        
        def jld_callback(s, p, o):
            """
            Insert extracted (s, p, o) to an rdflib graph.

            :param s: subject
            :param p: predicate
            :param o: object
            """
            # Subject analysis
            if s[:2] == "_:":
                s = BNode(s[2:])
            else:
                s = URIRef(s, base_uri)

            # Object analysis
            if isinstance(o, dict):
                if "@iri" in o:
                    o = o["@iri"]
                    if o[:2] == "_:":
                        o = BNode(o[2:])
                    else:
                        o = URIRef(o, base_uri)
                else:
                    assert "@literal" in o
                    o = Literal(
                            o["@literal"],
                            lang = o.get("@language"),
                            datatype = o.get("@datatype"),
                            )
            else:
                o = Literal(o)

            # Predicate analysis
            if "@type" in p:
                p = RDF.type
            elif p.startswith("x-rev:"):
                p = URIRef(p[6:], base_uri)
                s, o = o, s
            else:
                p = URIRef(p, base_uri)

            graph.add((s, p, o))
            return (s, p, o)

        if context is not None:
            json = { u"@context": context, u"@subject": json }

        return list(triples(json, jld_callback))

    @register_parser("application/json")
    def parse_jsonld(content, base_uri=None, encoding="utf-8"):
        """I parse RDF content from JSON-LD.

        :param content:  a byte string
        :param base_uri: the base URI of `content`
        :param encoding: the character encoding of `content`

        :return: an RDF graph
        :rtype:  rdflib.Graph
        :raise: :class:`rdfrest.exceptions.ParseError`
        """
        graph = Graph()
        #TODO à coder :D
        #if isinstance(content, basestring):
        if encoding.lower() != "utf-8":
            content = content.decode(encoding).encode("utf-8")
        try:
            jsonData = loads(content)
            # expand KTBS context
            context = jsonData["@context"]
            if isinstance(context, basestring):
                if context != CONTEXT_URI:
                    raise Exception("invalid context URI: %s" % context)
                jsonData["@context"] = CONTEXT
            else:
                if not isinstance(context, list):
                    raise Exception("invalid context: %s" % context)
                try:
                    i = context.index(CONTEXT_URI)
                except ValueError:
                    raise Exception("invalid context, does not contains ktbs-jsonld-context")
                context[i] = CONTEXT
            # add implicit arc for POSTed data
            if jsonData["@type"] == "Base":
                jsonData.setdefault("inRoot", "")
            elif jsonData["@type"] in ():
                jsonData.setdefault("inBase", "")
            # ... then parse!
            jsonld2graph(jsonData, base_uri, graph)
        except Exception, ex:
            raise ParseError(ex.message or str(ex), ex)
        print graph.serialize(format="turtle")
        return graph


    @register_serializer("application/json", "json") 
    def serialize_json(graph, sregister, base_uri=None):
        """I serialize an RDF graph as JSON-LD.

        :param graph:     an RDF graph
        :type  graph:     rdflib.Graph
        :param sregister: the serializer register this serializer comes from
                          (useful for getting namespace prefixes and other info)
        :type  sregister: SerializerRegister
        :param base_uri:  the base URI to be used to serialize

        :return: an iterable of UTF-8 encoded byte strings
        :raise: :class:`~rdfrest.exceptions.SerializeError` if the serializer can
                not serialize this given graph.

        .. important::

            Serializers that may raise a
            :class:`~rdfrest.exceptions.SerializeError` must *not* be implemented
            as generators, or the exception will be raised too late (i.e. when the
            `HttpFrontend` tries to send the response.
        """

        #TODO à coder :D
        raise NotImplementedError()


CONTEXT_URI = "http://liris.cnrs.fr/silex/2011/ktbs-jsonld-context"

CONTEXT_JSON = """{
    "xsd": "http://www.w3.org/2001/XMLSchema#",

    "AttributeType": "http://liris.cnrs.fr/silex/2009/ktbs#AttributeType",
    "Base": "http://liris.cnrs.fr/silex/2009/ktbs#Base",
    "BuiltinMethod": "http://liris.cnrs.fr/silex/2009/ktbs#BuiltinMethod",
    "ComputedTrace": "http://liris.cnrs.fr/silex/2009/ktbs#ComputedTrace",
    "KtbsRoot": "http://liris.cnrs.fr/silex/2009/ktbs#KtbsRoot",
    "Method": "http://liris.cnrs.fr/silex/2009/ktbs#Method",
    "Obsel": "http://liris.cnrs.fr/silex/2009/ktbs#Obsel",
    "ObselType": "http://liris.cnrs.fr/silex/2009/ktbs#ObselType",
    "RelationType": "http://liris.cnrs.fr/silex/2009/ktbs#RelationType",
    "StoredTrace": "http://liris.cnrs.fr/silex/2009/ktbs#StoredTrace",
    "TraceModel": "http://liris.cnrs.fr/silex/2009/ktbs#TraceModel",

    "contains": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#contains", "@type": "@id" },
    "external": "http://liris.cnrs.fr/silex/2009/ktbs#external",
    "filter": "http://liris.cnrs.fr/silex/2009/ktbs#filter",
    "fusion": "http://liris.cnrs.fr/silex/2009/ktbs#fusion",
    "hasAttributeObselType": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasAttributeDomain", "@type": "@id" },
    "hasAttributeDatatype": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasAttributeRange", "@type": "@id" },
    "haBase": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasBase", "@type": "@id" },
    "begin": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasBegin", "@type": "xsd:integer" },
    "beginDT": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasBeginDT", "@type": "xsd:dateTime" },
    "hasBuiltinMethod": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasBuiltinMethod", "@type": "@id" },
    "hasDefaultSubject": "http://liris.cnrs.fr/silex/2009/ktbs#hasDefaultSubject",
    "end": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasEnd", "@type": "xsd:integer" },
    "endDT": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasEndDT", "@type": "xsd:dateTime" },
    "hasMethod": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasMethod", "@type": "@id" },
    "hasModel": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasModel", "@type": "@id" },
    "hasObselList": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasObselCollection", "@type": "@id" },
    "origin": "http://liris.cnrs.fr/silex/2009/ktbs#hasOrigin",
    "parameter": "http://liris.cnrs.fr/silex/2009/ktbs#hasParameter",
    "hasParentMethod": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasParentMethod", "@type": "@id" },
    "hasParentModel": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasParentModel", "@type": "@id" },
    "hasRelationOrigin": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasRelationDomain", "@type": "@id" },
    "hasRelationDestination": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasRelationRange", "@type": "@id" },
    "hasSource": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasSource", "@type": "@id" },
    "hasSourceObsel": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasSourceObsel", "@type": "@id" },
    "hasSubject": "http://liris.cnrs.fr/silex/2009/ktbs#hasSubject",
    "hasSuperObselType": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasSuperObselType", "@type": "@id" },
    "hasSuperRelationType": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasSuperRelationType", "@type": "@id" },
    "hasTrace": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasTrace", "@type": "@id" },
    "traceBegin": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasTraceBegin", "@type": "xsd:integer" },
    "traceBeginDT": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasTraceBeginDT", "@type": "xsd:dateTime" },
    "traceEnd": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasTraceEnd", "@type": "xsd:integer" },
    "traceEndDT": { "@id": "http://liris.cnrs.fr/silex/2009/ktbs#hasTraceEndDT", "@type": "xsd:dateTime" },
    "unit": "http://liris.cnrs.fr/silex/2009/ktbs#hasUnit",
    "parallel": "http://liris.cnrs.fr/silex/2009/ktbs#parallel",
    "sparql": "http://liris.cnrs.fr/silex/2009/ktbs#sparql",

    "inRoot": { "@id": "x-rev:http://liris.cnrs.fr/silex/2009/ktbs#hasBase", "@type": "@id" },
    "inBase": { "@id": "x-rev:http://liris.cnrs.fr/silex/2009/ktbs#hasBase", "@type": "@id" },

    "label": "http://www.w3.org/2004/02/skos/core#prefLabel"
}"""

CONTEXT = loads(CONTEXT_JSON)

# temporary patch to adapt new coercion style to old coercion style (until pyld is updated)
coerce = {}
for k, v in CONTEXT.items():
    if isinstance(v, dict):
        CONTEXT[k] = v["@id"]
        coerce_val = v["@type"]
        if coerce_val == "@id":
            coerce_val = "@iri"
        coerce_list = coerce.get(coerce_val)
        if coerce_list is None:
            coerce_list = []
            coerce[coerce_val] = coerce_list
        coerce_list.append(k)
CONTEXT["@coerce"] = coerce
