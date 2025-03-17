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

from .base_impl cimport (
    Address,
    AddressList,
    AUTH_MODE_DEFAULT,
    AUTH_MODE_PRELIM,
    AUTH_MODE_SYSASM,
    AUTH_MODE_SYSBKP,
    AUTH_MODE_SYSDBA,
    AUTH_MODE_SYSDGD,
    AUTH_MODE_SYSKMT,
    AUTH_MODE_SYSOPER,
    AUTH_MODE_SYSRAC,
    BaseConnImpl,
    BaseCursorImpl,
    BaseDbObjectAttrImpl,
    BaseDbObjectImpl,
    BaseDbObjectTypeImpl,
    BaseDeqOptionsImpl,
    BaseEnqOptionsImpl,
    BaseMsgPropsImpl,
    BaseQueueImpl,
    BaseLobImpl,
    BaseParser,
    BasePoolImpl,
    BaseVarImpl,
    PipelineOpImpl,
    PipelineOpResultImpl,
    PIPELINE_OP_TYPE_CALL_FUNC,
    PIPELINE_OP_TYPE_CALL_PROC,
    PIPELINE_OP_TYPE_COMMIT,
    PIPELINE_OP_TYPE_EXECUTE,
    PIPELINE_OP_TYPE_EXECUTE_MANY,
    PIPELINE_OP_TYPE_FETCH_ALL,
    PIPELINE_OP_TYPE_FETCH_MANY,
    PIPELINE_OP_TYPE_FETCH_ONE,
    BindVar,
    Buffer,
    ConnectParamsImpl,
    convert_oracle_data_to_python,
    convert_oracle_data_to_arrow,
    convert_date_to_python,
    CS_FORM_IMPLICIT,
    CS_FORM_NCHAR,
    DbType,
    Description,
    DescriptionList,
    DRIVER_NAME,
    DRIVER_VERSION,
    ENCODING_UTF8,
    ENCODING_UTF16,
    GrowableBuffer,
    PY_TYPE_NUM_FLOAT,
    PY_TYPE_NUM_INT,
    PY_TYPE_NUM_DECIMAL,
    PY_TYPE_NUM_STR,
    ORA_TYPE_NUM_BFILE,
    ORA_TYPE_NUM_BINARY_DOUBLE,
    ORA_TYPE_NUM_BINARY_FLOAT,
    ORA_TYPE_NUM_BINARY_INTEGER,
    ORA_TYPE_NUM_BLOB,
    ORA_TYPE_NUM_BOOLEAN,
    ORA_TYPE_NUM_CHAR,
    ORA_TYPE_NUM_CLOB,
    ORA_TYPE_NUM_CURSOR,
    ORA_TYPE_NUM_DATE,
    ORA_TYPE_NUM_INTERVAL_DS,
    ORA_TYPE_NUM_INTERVAL_YM,
    ORA_TYPE_NUM_JSON,
    ORA_TYPE_NUM_LONG,
    ORA_TYPE_NUM_LONG_RAW,
    ORA_TYPE_NUM_NUMBER,
    ORA_TYPE_NUM_OBJECT,
    ORA_TYPE_NUM_RAW,
    ORA_TYPE_NUM_ROWID,
    ORA_TYPE_NUM_TIMESTAMP,
    ORA_TYPE_NUM_TIMESTAMP_LTZ,
    ORA_TYPE_NUM_TIMESTAMP_TZ,
    ORA_TYPE_NUM_UROWID,
    ORA_TYPE_NUM_VARCHAR,
    ORA_TYPE_NUM_VECTOR,
    OracleMetadata,
    OracleData,
    OsonDecoder,
    OsonEncoder,
    POOL_GETMODE_FORCEGET,
    POOL_GETMODE_NOWAIT,
    POOL_GETMODE_TIMEDWAIT,
    POOL_GETMODE_WAIT,
    PoolParamsImpl,
    PURITY_DEFAULT,
    PURITY_NEW,
    PURITY_SELF,
    PY_TYPE_ASYNC_LOB,
    PY_TYPE_DATE,
    PY_TYPE_DATETIME,
    PY_TYPE_DB_OBJECT,
    PY_TYPE_DECIMAL,
    PY_TYPE_INTERVAL_YM,
    PY_TYPE_LOB,
    PY_TYPE_TIMEDELTA,
    TNS_LONG_LENGTH_INDICATOR,
    TNS_NULL_LENGTH_INDICATOR,
    decode_uint16be,
    decode_uint32be,
    decode_date,
    VectorDecoder,
    VectorEncoder,
    encode_uint16be,
)

from .base_impl import (
    DB_TYPE_BLOB,
    DB_TYPE_CLOB,
    DB_TYPE_NCLOB,
    DB_TYPE_BINARY_INTEGER,
    DB_TYPE_CURSOR,
    DB_TYPE_NUMBER,
    DB_TYPE_OBJECT,
    DB_TYPE_XMLTYPE,
)

from .interchange.nanoarrow_bridge cimport (
    OracleArrowArray,
)

ctypedef unsigned char char_type

# flag whether the cryptography package exists
cdef object CRYPTOGRAPHY_IMPORT_ERROR = None

include "impl/thin/constants.pxi"
include "impl/thin/utils.pyx"
include "impl/thin/crypto.pyx"
include "impl/thin/capabilities.pyx"
include "impl/thin/transport.pyx"
include "impl/thin/packet.pyx"
include "impl/thin/messages/base.pyx"
include "impl/thin/messages/aq_base.pyx"
include "impl/thin/messages/aq_array.pyx"
include "impl/thin/messages/aq_deq.pyx"
include "impl/thin/messages/aq_enq.pyx"
include "impl/thin/messages/auth.pyx"
include "impl/thin/messages/commit.pyx"
include "impl/thin/messages/connect.pyx"
include "impl/thin/messages/data_types.pyx"
include "impl/thin/messages/end_pipeline.pyx"
include "impl/thin/messages/execute.pyx"
include "impl/thin/messages/fetch.pyx"
include "impl/thin/messages/lob_op.pyx"
include "impl/thin/messages/logoff.pyx"
include "impl/thin/messages/ping.pyx"
include "impl/thin/messages/protocol.pyx"
include "impl/thin/messages/fast_auth.pyx"
include "impl/thin/messages/rollback.pyx"
include "impl/thin/messages/session_release.pyx"
include "impl/thin/messages/tpc_change_state.pyx"
include "impl/thin/messages/tpc_switch.pyx"
include "impl/thin/protocol.pyx"
include "impl/thin/queue.pyx"
include "impl/thin/connection.pyx"
include "impl/thin/statement.pyx"
include "impl/thin/statement_cache.pyx"
include "impl/thin/cursor.pyx"
include "impl/thin/var.pyx"
include "impl/thin/dbobject.pyx"
include "impl/thin/dbobject_cache.pyx"
include "impl/thin/lob.pyx"
include "impl/thin/pool.pyx"
