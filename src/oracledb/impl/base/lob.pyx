#------------------------------------------------------------------------------
# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
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
# lob.pyx
#
# Cython file defining the base Lob implementation class (embedded in
# base_impl.pyx).
#------------------------------------------------------------------------------

cdef class BaseLobImpl:

    @utils.CheckImpls("closing a LOB")
    def close(self):
        pass

    @utils.CheckImpls("checking if a BFILE exists")
    def file_exists(self):
        pass

    @utils.CheckImpls("freeing the lob object")
    def free_lob(self):
        pass

    @utils.CheckImpls("getting the chunk size of a LOB")
    def get_chunk_size(self):
        pass

    @utils.CheckImpls("getting the file name and directory alias of a BFILE")
    def get_file_name(self):
        pass

    @utils.CheckImpls("getting whether a LOB is open or not")
    def get_is_open(self):
        pass

    @utils.CheckImpls("getting the maximum amount that can be read from a LOB")
    def get_max_amount(self):
        pass

    @utils.CheckImpls("getting the size of a LOB")
    def get_size(self):
        pass

    @utils.CheckImpls("opening a LOB")
    def open(self):
        pass

    @utils.CheckImpls("reading data from a LOB")
    def read(self, uint64_t offset, uint64_t amount):
        pass

    @utils.CheckImpls("setting the file name an directory alias of a BFILE")
    def set_file_name(self, str dir_alias, str name):
        pass

    @utils.CheckImpls("trimming a LOB")
    def trim(self, uint64_t new_size):
        pass

    @utils.CheckImpls("writing data to a LOB")
    def write(self, object value, uint64_t offset):
        pass
