#------------------------------------------------------------------------------
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
#
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl and Apache License
# 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose
# either license.
#
# If you elect to accept the software under the Apache License, Version 2.0,
# the following applies:
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# soda.pyx
#
# Cython file defining the base SODA implementation classes (embedded in
# base_impl.pyx).
#------------------------------------------------------------------------------

cdef class BaseSodaDbImpl:

    @utils.CheckImpls("creating a SODA collection")
    def create_collection(self, str name, str metadata, bint map_mode):
        pass

    @utils.CheckImpls("creating a SODA binary/text document")
    def create_document(self, bytes content, str key, str media_type):
        pass

    @utils.CheckImpls("creating a SODA JSON document")
    def create_json_document(self, object content, str key):
        pass

    @utils.CheckImpls("getting a list of SODA collection names")
    def get_collection_names(self, str start_name, uint32_t limit):
        pass

    @utils.CheckImpls("opening a SODA collection")
    def open_collection(self, str name):
        pass


cdef class BaseSodaCollImpl:

    @utils.CheckImpls("creating an index on a SODA collection")
    def create_index(self, str spec):
        pass

    @utils.CheckImpls("dropping a SODA collection")
    def drop(self):
        pass

    @utils.CheckImpls("dropping an index on a SODA collection")
    def drop_index(self, str name, bint force):
        pass

    @utils.CheckImpls("getting the count of documents in a SODA collection")
    def get_count(self, object op):
        pass

    @utils.CheckImpls("getting a cursor for documents in a SODA collection")
    def get_cursor(self, object op):
        pass

    @utils.CheckImpls("getting the data guide for a SODA collection")
    def get_data_guide(self):
        pass

    @utils.CheckImpls("getting the metadata of a SODA collection")
    def get_metadata(self):
        pass

    @utils.CheckImpls("getting a document from a SODA collection")
    def get_one(self, object op):
        pass

    @utils.CheckImpls("inserting multiple documents into a SODA collection")
    def insert_many(self, list documents, str hint, bint return_docs):
        pass

    @utils.CheckImpls("inserting a single document into a SODA collection")
    def insert_one(self, BaseSodaDocImpl doc, str hint, bint return_doc):
        pass

    @utils.CheckImpls("removing documents from a SODA collection")
    def remove(self, object op):
        pass

    @utils.CheckImpls("replacing a document in a SODA collection")
    def replace_one(self, BaseSodaDocImpl doc_impl, bint return_doc):
        pass

    @utils.CheckImpls("saving a document in a SODA collection")
    def save(self, BaseSodaDocImpl doc, str hint, bint return_doc):
        pass

    @utils.CheckImpls("truncating a SODA collection")
    def truncate(self):
        pass


cdef class BaseSodaDocImpl:

    @utils.CheckImpls("getting the content of a SODA document")
    def get_content(self):
        pass

    @utils.CheckImpls("getting the created on date of a SODA document")
    def get_created_on(self):
        pass

    @utils.CheckImpls("getting the key of a SODA document")
    def get_key(self):
        pass

    @utils.CheckImpls("getting the last modified date of a SODA document")
    def get_last_modified(self):
        pass

    @utils.CheckImpls("getting the media type of a SODA document")
    def get_media_type(self):
        pass

    @utils.CheckImpls("getting the version of a SODA document")
    def get_version(self):
        pass


cdef class BaseSodaDocCursorImpl:

    @utils.CheckImpls("closing a SODA document cursor")
    def close(self):
        pass

    @utils.CheckImpls("getting the next document from a SODA document cursor")
    def get_next_doc(self):
        pass
