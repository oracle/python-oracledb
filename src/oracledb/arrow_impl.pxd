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
# arrow_impl.pxd
#
# Cython definition file declaring the classes used for implementing the Arrow
# interface.
#------------------------------------------------------------------------------

# cython: language_level = 3

from libc.stdint cimport int8_t, uint8_t, int16_t, uint16_t
from libc.stdint cimport int32_t, uint32_t, int64_t, uint64_t
from cpython cimport array

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
        ArrowSchema** children
        void (*release)(ArrowSchema*)

    cpdef enum ArrowType:
        NANOARROW_TYPE_BOOL
        NANOARROW_TYPE_BINARY
        NANOARROW_TYPE_DECIMAL128
        NANOARROW_TYPE_DOUBLE
        NANOARROW_TYPE_FLOAT
        NANOARROW_TYPE_INT8
        NANOARROW_TYPE_INT64
        NANOARROW_TYPE_LARGE_BINARY
        NANOARROW_TYPE_LARGE_STRING
        NANOARROW_TYPE_LIST
        NANOARROW_TYPE_NA
        NANOARROW_TYPE_STRING
        NANOARROW_TYPE_STRUCT
        NANOARROW_TYPE_TIMESTAMP
        NANOARROW_TYPE_UINT8
        NANOARROW_TYPE_UINT32
        NANOARROW_TYPE_UNINITIALIZED

    cpdef enum ArrowTimeUnit:
        NANOARROW_TIME_UNIT_SECOND
        NANOARROW_TIME_UNIT_MILLI
        NANOARROW_TIME_UNIT_MICRO
        NANOARROW_TIME_UNIT_NANO


cdef class ArrowArrayImpl:
    cdef:
        int32_t precision
        int32_t scale
        str name
        ArrowType arrow_type
        ArrowTimeUnit time_unit
        int time_factor
        ArrowArray *arrow_array
        ArrowSchema *arrow_schema
        ArrowType child_arrow_type

    cdef int _set_time_unit(self, ArrowTimeUnit time_unit) except -1
    cdef int append_bytes(self, void* ptr, int64_t num_bytes) except -1
    cdef int append_decimal(self, void* ptr, int64_t num_bytes) except -1
    cdef int append_double(self, double value) except -1
    cdef int append_float(self, float value) except -1
    cdef int append_int64(self, int64_t value) except -1
    cdef int append_last_value(self, ArrowArrayImpl array) except -1
    cdef int append_null(self) except -1
    cdef int append_sparse_vector(self, int64_t num_dimensions,
                                  array.array indices,
                                  array.array values) except -1
    cdef int append_vector(self, array.array value) except -1
    cdef int finish_building(self) except -1
    cdef int populate_from_metadata(self, ArrowType arrow_type, str name,
                                    int8_t precision, int8_t scale,
                                    ArrowTimeUnit time_unit,
                                    ArrowType child_arrow_type) except -1


cdef class DataFrameImpl:
    cdef:
        list arrays
