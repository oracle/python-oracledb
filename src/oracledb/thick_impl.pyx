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
# thick_impl.pyx
#
# Cython file for interfacing with ODPI-C.
#------------------------------------------------------------------------------

# cython: language_level=3

cimport cython
cimport cpython
cimport cpython.datetime as cydatetime
from cpython cimport array

import array
import datetime
import decimal

cydatetime.import_datetime()

from . import constants, driver_mode, errors, exceptions
from .subscr import Message, MessageQuery, MessageRow, MessageTable

from . import __version__ as VERSION

from .base_impl cimport (
    BaseConnImpl,
    BaseCursorImpl,
    BaseDbObjectImpl,
    BaseDbObjectAttrImpl,
    BaseDbObjectTypeImpl,
    BaseDeqOptionsImpl,
    BaseEnqOptionsImpl,
    BaseLobImpl,
    BaseMsgPropsImpl,
    BasePoolImpl,
    BaseQueueImpl,
    BaseSodaCollImpl,
    BaseSodaDbImpl,
    BaseSodaDocImpl,
    BaseSodaDocCursorImpl,
    BaseSubscrImpl,
    BaseVarImpl,
    BindVar,
    C_DEFAULTS,
    ConnectParamsImpl,
    DbType,
    DB_TYPE_NUM_CURSOR,
    FetchInfoImpl,
    PoolParamsImpl,
    get_preferred_num_type,
    NUM_TYPE_FLOAT,
    NUM_TYPE_INT,
    NUM_TYPE_DECIMAL,
    VectorDecoder,
    VectorEncoder,
)
from libc.string cimport memchr, memcpy, memset

include "impl/thick/odpi.pxd"

cdef type PY_TYPE_DATE = datetime.date
cdef type PY_TYPE_DATETIME = datetime.datetime
cdef type PY_TYPE_DECIMAL = decimal.Decimal
cdef type PY_TYPE_JSON_ID
cdef type PY_TYPE_INTERVAL_YM
cdef type PY_TYPE_DB_OBJECT
cdef type PY_TYPE_LOB
cdef type PY_TYPE_TIMEDELTA = datetime.timedelta

cdef struct DriverInfo:
    dpiContext *context
    dpiVersionInfo client_version_info
    bint soda_use_json_desc

cdef DriverInfo driver_info = \
        DriverInfo(NULL, dpiVersionInfo(0, 0, 0, 0, 0, 0), True)

driver_context_params = None

include "impl/thick/buffer.pyx"
include "impl/thick/connection.pyx"
include "impl/thick/pool.pyx"
include "impl/thick/cursor.pyx"
include "impl/thick/lob.pyx"
include "impl/thick/json.pyx"
include "impl/thick/var.pyx"
include "impl/thick/dbobject.pyx"
include "impl/thick/soda.pyx"
include "impl/thick/queue.pyx"
include "impl/thick/subscr.pyx"
include "impl/thick/utils.pyx"
