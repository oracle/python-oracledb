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
# thin_impl.pyx
#
# Cython file for communicating with the server directly without the use of
# any Oracle Client library.
#------------------------------------------------------------------------------

# cython: language_level=3

cimport cython
cimport cpython
cimport cpython.datetime as cydatetime
cimport cpython.ref

from libc.stdint cimport int8_t, int16_t, int32_t, int64_t
from libc.stdint cimport uint8_t, uint16_t, uint32_t, uint64_t
from libc.string cimport memcpy, memset
from cpython cimport array

import array
import asyncio
import base64
import collections
import datetime
import decimal
import getpass
import hashlib
import inspect
import json
import os
import socket
import re
import secrets
import select
import ssl
import subprocess
import sys
import threading
import time
import uuid

try:
    import certifi
except ImportError:
    certifi = None
macos_certs = None

cydatetime.import_datetime()

from . import __version__ as VERSION

from . import constants, errors, exceptions

from .base_impl cimport (
    Address,
    AddressList,
    BaseConnImpl,
    BaseCursorImpl,
    BaseDbObjectAttrImpl,
    BaseDbObjectImpl,
    BaseDbObjectTypeImpl,
    BaseLobImpl,
    BasePoolImpl,
    BaseVarImpl,
    Buffer,
    BYTE_ORDER_LSB,
    BYTE_ORDER_MSB,
    ConnectParamsImpl,
    CS_FORM_IMPLICIT,
    CS_FORM_NCHAR,
    DbType,
    Description,
    DescriptionList,
    ENCODING_UTF8,
    ENCODING_UTF16,
    FetchInfoImpl,
    PoolParamsImpl,
    get_preferred_num_type,
    GrowableBuffer,
    NUM_TYPE_FLOAT,
    NUM_TYPE_INT,
    NUM_TYPE_DECIMAL,
    NUM_TYPE_STR,
    OsonDecoder,
    OsonEncoder,
    unpack_uint16,
    unpack_uint32,
    VectorDecoder,
    VectorEncoder,
    TNS_LONG_LENGTH_INDICATOR,
    TNS_NULL_LENGTH_INDICATOR,
)
from .base_impl import (
    DB_TYPE_BLOB,
    DB_TYPE_CLOB,
    DB_TYPE_NCLOB,
    DB_TYPE_BINARY_INTEGER,
    DB_TYPE_CURSOR,
    DB_TYPE_OBJECT,
    DB_TYPE_XMLTYPE,
)

ctypedef unsigned char char_type

# Python types
cdef type PY_TYPE_DATE = datetime.date
cdef type PY_TYPE_DATETIME = datetime.datetime
cdef type PY_TYPE_DECIMAL = decimal.Decimal
cdef type PY_TYPE_DB_OBJECT
cdef type PY_TYPE_INTERVAL_YM
cdef type PY_TYPE_LOB
cdef type PY_TYPE_ASYNC_LOB
cdef type PY_TYPE_TIMEDELTA = datetime.timedelta

# authorization modes
cdef uint32_t AUTH_MODE_DEFAULT = constants.AUTH_MODE_DEFAULT
cdef uint32_t AUTH_MODE_SYSASM = constants.AUTH_MODE_SYSASM
cdef uint32_t AUTH_MODE_SYSBKP = constants.AUTH_MODE_SYSBKP
cdef uint32_t AUTH_MODE_SYSDBA = constants.AUTH_MODE_SYSDBA
cdef uint32_t AUTH_MODE_SYSDGD = constants.AUTH_MODE_SYSDGD
cdef uint32_t AUTH_MODE_SYSKMT = constants.AUTH_MODE_SYSKMT
cdef uint32_t AUTH_MODE_SYSOPER = constants.AUTH_MODE_SYSOPER
cdef uint32_t AUTH_MODE_SYSRAC = constants.AUTH_MODE_SYSRAC

# purity values
cdef uint8_t PURITY_DEFAULT = constants.PURITY_DEFAULT
cdef uint8_t PURITY_NEW = constants.PURITY_NEW
cdef uint8_t PURITY_SELF = constants.PURITY_SELF

# pool get modes
cdef uint32_t POOL_GETMODE_FORCEGET = constants.POOL_GETMODE_FORCEGET
cdef uint32_t POOL_GETMODE_NOWAIT = constants.POOL_GETMODE_NOWAIT
cdef uint32_t POOL_GETMODE_WAIT = constants.POOL_GETMODE_WAIT
cdef uint32_t POOL_GETMODE_TIMEDWAIT = constants.POOL_GETMODE_TIMEDWAIT

# flag whether the cryptography package exists
cdef bint HAS_CRYPTOGRAPHY = True

include "impl/thin/constants.pxi"
include "impl/thin/utils.pyx"
include "impl/thin/crypto.pyx"
include "impl/thin/capabilities.pyx"
include "impl/thin/transport.pyx"
include "impl/thin/packet.pyx"
include "impl/thin/data_types.pyx"
include "impl/thin/messages.pyx"
include "impl/thin/protocol.pyx"
include "impl/thin/connection.pyx"
include "impl/thin/statement.pyx"
include "impl/thin/statement_cache.pyx"
include "impl/thin/cursor.pyx"
include "impl/thin/var.pyx"
include "impl/thin/dbobject.pyx"
include "impl/thin/dbobject_cache.pyx"
include "impl/thin/lob.pyx"
include "impl/thin/pool.pyx"
include "impl/thin/conversions.pyx"
