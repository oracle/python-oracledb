#------------------------------------------------------------------------------
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
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
# base_impl.pyx
#
# Cython file for the base implementation that the thin and thick
# implementations use.
#------------------------------------------------------------------------------

# cython: language_level=3

cimport cython
cimport cpython
cimport cpython.datetime as cydatetime

from libc.stdint cimport int8_t, int16_t, int32_t, int64_t
from libc.stdint cimport uint8_t, uint16_t, uint32_t, uint64_t
from libc.stdint cimport UINT8_MAX, UINT16_MAX, UINT32_MAX, UINT64_MAX
from libc.stdlib cimport atoi, atof
from libc.string cimport memcpy
from cpython cimport array

from .interchange.nanoarrow_bridge cimport (
    NANOARROW_TIME_UNIT_SECOND,
    NANOARROW_TIME_UNIT_MILLI,
    NANOARROW_TIME_UNIT_MICRO,
    NANOARROW_TIME_UNIT_NANO,
    NANOARROW_TYPE_BOOL,
    NANOARROW_TYPE_BINARY,
    NANOARROW_TYPE_DECIMAL128,
    NANOARROW_TYPE_DOUBLE,
    NANOARROW_TYPE_FLOAT,
    NANOARROW_TYPE_INT64,
    NANOARROW_TYPE_LARGE_BINARY,
    NANOARROW_TYPE_LARGE_STRING,
    NANOARROW_TYPE_STRING,
    NANOARROW_TYPE_TIMESTAMP,
)

import array

import base64
import copy
import datetime
import decimal
import getpass
import inspect
import json
import os
import random
import secrets
import socket
import ssl
import string
import sys
import time
import warnings

cydatetime.import_datetime()

# Python types used by the driver
cdef type PY_TYPE_ASYNC_CURSOR
cdef type PY_TYPE_ASYNC_LOB
cdef type PY_TYPE_BOOL = bool
cdef type PY_TYPE_CURSOR
cdef object PY_TYPE_DATAFRAME
cdef type PY_TYPE_DATE = datetime.date
cdef type PY_TYPE_DATETIME = datetime.datetime
cdef type PY_TYPE_DECIMAL = decimal.Decimal
cdef type PY_TYPE_DB_OBJECT
cdef type PY_TYPE_DB_OBJECT_TYPE
cdef type PY_TYPE_JSON_ID
cdef type PY_TYPE_INTERVAL_YM
cdef type PY_TYPE_LOB
cdef type PY_TYPE_MESSAGE
cdef type PY_TYPE_MESSAGE_QUERY
cdef type PY_TYPE_MESSAGE_ROW
cdef type PY_TYPE_MESSAGE_TABLE
cdef type PY_TYPE_SPARSE_VECTOR
cdef type PY_TYPE_TIMEDELTA = datetime.timedelta
cdef type PY_TYPE_VAR
cdef type PY_TYPE_FETCHINFO

# enumerations used by the driver in connect parameters
cdef object ENUM_AUTH_MODE
cdef object ENUM_POOL_GET_MODE
cdef object ENUM_PURITY

cdef const char* DRIVER_NAME = "python-oracledb"
cdef const char* DRIVER_VERSION
cdef const char* DRIVER_INSTALLATION_URL = \
        "https://python-oracledb.readthedocs.io/en/" \
        "latest/user_guide/initialization.html"
cdef const char* ENCODING_UTF8 = "UTF-8"
cdef const char* ENCODING_UTF16 = "UTF-16BE"

# protocols registered with the library
REGISTERED_PROTOCOLS = {}

# password types registered with the library
REGISTERED_PASSWORD_TYPES = {}

# params hooks registered with the library
REGISTERED_PARAMS_HOOKS = []

include "impl/base/types.pyx"
include "impl/base/constants.pxi"
include "impl/base/decoders.pyx"
include "impl/base/encoders.pyx"
include "impl/base/metadata.pyx"
include "impl/base/utils.pyx"
include "impl/base/defaults.pyx"
include "impl/base/pipeline.pyx"
include "impl/base/converters.pyx"
include "impl/base/buffer.pyx"
include "impl/base/parsers.pyx"
include "impl/base/oson.pyx"
include "impl/base/vector.pyx"
include "impl/base/connect_params.pyx"
include "impl/base/pool_params.pyx"
include "impl/base/connection.pyx"
include "impl/base/pool.pyx"
include "impl/base/cursor.pyx"
include "impl/base/var.pyx"
include "impl/base/bind_var.pyx"
include "impl/base/dbobject.pyx"
include "impl/base/lob.pyx"
include "impl/base/soda.pyx"
include "impl/base/queue.pyx"
include "impl/base/subscr.pyx"
