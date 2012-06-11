#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    This file is part of KTBS <http://liris.cnrs.fr/silex/2009/ktbs>
#    Copyright (C) 2012 Françoise Conil <fconil@liris.cnrs.fr> / SILEX
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
Nose unit-testing for the kTBS base client API.

Resource
  get_uri() → uri
  get_sync_status() → str
      return "ok" if the resource is in sync with the data at its URI,
      else any other string describing the reason why it is not.
  get_readonly() → bool
      return true if this resource is not modifiable
  remove()
      remove this resource from the KTBS
      If the resource can not be removed, an exception must be raised.
  get_label() → str
      returns a user-friendly label
  set_label(str)
      set a user-friendly label
  reset_label()
      reset the user-friendly label to its default value

Model (Resource)
  get_base() → Base
  get_unit() → str
      TODO find stable reference to unit names
  set_unit(unit:str)
  get(id:uri) → ObselType | AttributeType | RelationType
      return the element of this model identified by the URI, or null
  list_parents(include_indirect:bool?) → [Model]
      list parent models
      Note that some of these models may not belong to the same KTBS, and may
      be readonly —see get_readonly.
      include_indirect defaults to false and means that parent's parents should
      be returned as well.
  list_attribute_types(include_inherited:bool?) → [AttributeType]
      include_inherited defaults to true and means that attributes types
      from inherited models should be included
  list_relation_types(include_inherited:bool?) → [RelationType]
      include_inherited defaults to true and means that relation types
      from inherited models should be included
  list_obsel_types(include_inherited:bool?) → [ObselType]
      include_inherited defaults to true and means that obsel types
      from inherited models should be included

  add_parent(m:Model)
  remove_parent(m:Model)
  create_obsel_type(label:str, supertypes:[ObselType]?, id:uri?) → ObselType
      NB: if id is not provided, label is used to mint a human-friendly URI
  create_attribute_type(label:str, obsel_type:ObselType?, data_type:uri?,
                        value_is_list:bool?, id:uri?) → AttributeType
      the data_type uri is an XML-Schema datatype URI;
      value_is_list indicates whether the attributes accepts a single value
      (false, default) or a list of values (true).
      NB: if data_type represent a "list datatype", value_is_list must not be
      true
      NB: if id is not provided, label is used to mint a human-friendly URI
      TODO specify a minimum list of datatypes that must be supported
      TODO define a URI for representing "list of X" for each supported datatype
  create_relation_type(label:str, origin:ObselType?, destination:ObselType?,
                       supertypes:[RelationType]?, id:uri?) → RelationType
      NB: if id is not provided, label is used to mint a human-friendly URI
"""
from unittest import TestCase, skip

from os.path import abspath, dirname, join
from subprocess import Popen, PIPE

from rdflib import URIRef

from ktbs.namespaces import KTBS

from ktbs.client.root import KtbsRoot

KTBS_ROOT = "http://localhost:8001/"

class TestKtbsClientModelResource(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)
        cls.base = cls.root.create_base(id="BaseTest/", label="Test base")
        cls.model = cls.base.create_model(id="ModelTest", label="Test model")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    def test_get_model_uri(self):
        reference_uri = URIRef(KTBS_ROOT + "BaseTest/ModelTest")
        assert self.model.get_uri() == reference_uri

    @skip("Resource.get_sync_status() is not yet implemented")
    def test_get_sync_status(test):
        assert self.model.get_sync_status() == "ok"

    def test_get_readonly(self):
        assert self.model.get_readonly() == False

    def test_get_model_label(self):
        assert self.model.get_label() == "Test model"

    def test_set_base_label(self):
        self.model.set_label("New model label")
        assert self.model.get_label() == "New model label"

    @skip("Resource.reset_label() is not yet implemented")
    def test_reset_model_label(self):
        self.model.reset_label()
        assert self.model.get_label() == "Test model"

    @skip("Resource.remove() does not work : 405 Not Allowed")
    def test_remove_model(self):
        model_uri = self.model.get_uri()
        self.model.remove()
        assert self.base.get(model_uri) == None

class TestKtbsClientModel(TestCase):

    process = None

    @classmethod
    def setUpClass(cls):
        cls.process = Popen([join(dirname(dirname(abspath(__file__))),
                              "bin", "ktbs")], stderr=PIPE)
        # then wait for the server to actually start:
        # we know that it will write on its stderr when ready
        cls.process.stderr.read(1)
        cls.root = KtbsRoot(KTBS_ROOT)
        cls.base = cls.root.create_base(id="BaseTest/", label="Test base")
        cls.model = cls.base.create_model(id="ModelWithID", label="Test model")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()

    def test_get_base(self):
        base = self.model.get_base()
        assert base.get_uri() == self.base.get_uri()
