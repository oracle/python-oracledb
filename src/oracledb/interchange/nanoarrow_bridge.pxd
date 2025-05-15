#------------------------------------------------------------------------------
# Copyright (c) 2025, Oracle and/or its affiliates.
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
# nanoarrow_bridge.pxd
#
# Cython definition file declaring the classes used for bridging between the
# nanoarrow C interface and Python.
#------------------------------------------------------------------------------

# cython: language_level = 3

from libc.stdint cimport int8_t, uint8_t, int16_t, uint16_t
from libc.stdint cimport int32_t, uint32_t, int64_t, uint64_t

cdef extern from "nanoarrow.h":

    cdef struct ArrowArray:
        int64_t length
        int64_t null_count
        int64_t offset
        int64_t n_buffers
        int64_t n_children
        ArrowArray** children
        const void** buffers
        void (*release)(ArrowArray*)

    cdef struct ArrowSchema:
        void (*release)(ArrowSchema*)

    cpdef enum ArrowType:
        NANOARROW_TYPE_BOOL
        NANOARROW_TYPE_BINARY
        NANOARROW_TYPE_DECIMAL128
        NANOARROW_TYPE_DOUBLE
        NANOARROW_TYPE_FLOAT
        NANOARROW_TYPE_INT64
        NANOARROW_TYPE_LARGE_BINARY
        NANOARROW_TYPE_LARGE_STRING
        NANOARROW_TYPE_STRING
        NANOARROW_TYPE_TIMESTAMP
        NANOARROW_TYPE_UNINITIALIZED

    cpdef enum ArrowTimeUnit:
        NANOARROW_TIME_UNIT_SECOND
        NANOARROW_TIME_UNIT_MILLI
        NANOARROW_TIME_UNIT_MICRO
        NANOARROW_TIME_UNIT_NANO


cdef class OracleArrowArray:
    """
    OracleArrowArray corresponds to a Column in the Relational model

    It uses functions defined in the Arrow C Data Interface
    to work with Arrow buffers and incrementally append values

    The only user-facing API in this object will be __arrow_c_array__()
    which is documented in the Arrow PyCapsule Interface. Arrow-backed
    DataFrame libraries will use __arrow_c_array__() to directly access
    the underlying arrow data

    """
    cdef:
        public int32_t precision
        public int32_t scale
        public str name
        public ArrowType arrow_type
        public ArrowTimeUnit time_unit
        double factor
        ArrowArray *arrow_array
        ArrowSchema *arrow_schema

    cdef str _schema_to_string(self)
    cdef int append_bytes(self, void* ptr, int64_t num_bytes) except -1
    cdef int append_decimal(self, void* ptr, int64_t num_bytes) except -1
    cdef int append_double(self, double value) except -1
    cdef int append_float(self, float value) except -1
    cdef int append_int64(self, int64_t value) except -1
    cdef int append_last_value(self, OracleArrowArray array) except -1
    cdef int append_null(self) except -1
    cdef int finish_building(self) except -1
