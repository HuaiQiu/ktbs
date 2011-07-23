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

"""I provide standard exception for RDF-REST.
"""

class RdfRestException(Exception):
    """The common superclass of all RDF-REST exceptions.
    """
    pass

class CanNotProceedError(RdfRestException):
    """An error raised when the state of the RDF-REST service prevents from
    completing a request.

    For example: a resource can not be deleted because other resources depend
    on it.
    """
    pass

class InvalidDataError(RdfRestException):
    """An error raised when RDF data is not acceptable.
    """
    pass

class InvalidParametersError(RdfRestException):
    """An error raised when query-string parameters are not acceptable.

    This means that the query-string parameters correspond to no
    resource. If the parameters are recognized but do not support the
    intended operation, `MethodNotAllowedError` should be raised
    instead.
    """
    pass

class MethodNotAllowedError(NotImplementedError, RdfRestException):
    """An error raised when an RDF-REST method is not supported.

    :param message: the message of this exception
    :param allowed: a list of the allowed operations
    """
    def __init__(self, message, allowed=("head", "get")):
        NotImplementedError.__init__(self)
        RdfRestException.__init__(self, message)
        self.allowed = list(allowed)

class ParseError(RdfRestException):
    """An error during parsing a user-provided content.

    :param message:  the message of this exception
    :param original: if provided, the original exception that caused this error
    """
    def __init__(self, message, original=None):
        RdfRestException.__init__(self, message)
        self.original = original

class SerializeError(RdfRestException):
    """An error during serializing a graph.

    Can be raised by specialized serializers that are not able to serialize
    arbitrary RDF graphs.
    """
    pass
