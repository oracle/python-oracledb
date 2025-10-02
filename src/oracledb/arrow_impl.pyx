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
# arrow_impl.pyx
#
# Cython file for the Arrow implementation.
#------------------------------------------------------------------------------

# cython: language_level=3

cimport cpython

from libc.errno cimport EINVAL, EOVERFLOW
from libc.stdint cimport uintptr_t
from libc.string cimport memcpy, memset, strlen, strchr
from cpython cimport array

import array

from . import errors

cdef array.array float_template = array.array('f')
cdef array.array double_template = array.array('d')
cdef array.array int8_template = array.array('b')
cdef array.array uint8_template = array.array('B')
cdef array.array uint32_template

if array.array("I").itemsize == 4:
    uint32_template = array.array("I")
else:
    uint32_template = array.array("L")

include "impl/arrow/utils.pyx"
include "impl/arrow/schema.pyx"
include "impl/arrow/array.pyx"
include "impl/arrow/dataframe.pyx"
