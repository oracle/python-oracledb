#------------------------------------------------------------------------------
# Copyright (c) 2020, 2023, Oracle and/or its affiliates.
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
# __init__.py
#
# Package initialization module.
#------------------------------------------------------------------------------

import sys

from .version import (
    __version__ as __version__
)

from .constants import *
from .exceptions import *

from .errors import (
    _Error as _Error
)

from .defaults import (
    defaults as defaults
)

from .connection import (
    connect as connect,
    Connection as Connection
)

from .cursor import (
    Cursor as Cursor
)

from .pool import (
    create_pool as create_pool,
    ConnectionPool as ConnectionPool
)

from .connect_params import (
    ConnectParams as ConnectParams
)

from .pool_params import (
    PoolParams as PoolParams
)

from .lob import (
    LOB as LOB
)

from .dbobject import (
    DbObject as DbObject,
    DbObjectType as DbObjectType
)

from .var import (
    Var as Var
)

from .dsn import (
    makedsn as makedsn
)

from .driver_mode import (
    is_thin_mode as is_thin_mode
)

from .base_impl import (

    # database types
    DB_TYPE_BFILE as DB_TYPE_BFILE,
    DB_TYPE_BINARY_DOUBLE as DB_TYPE_BINARY_DOUBLE,
    DB_TYPE_BINARY_FLOAT as DB_TYPE_BINARY_FLOAT,
    DB_TYPE_BINARY_INTEGER as DB_TYPE_BINARY_INTEGER,
    DB_TYPE_BLOB as DB_TYPE_BLOB,
    DB_TYPE_BOOLEAN as DB_TYPE_BOOLEAN,
    DB_TYPE_CHAR as DB_TYPE_CHAR,
    DB_TYPE_CLOB as DB_TYPE_CLOB,
    DB_TYPE_CURSOR as DB_TYPE_CURSOR,
    DB_TYPE_DATE as DB_TYPE_DATE,
    DB_TYPE_INTERVAL_DS as DB_TYPE_INTERVAL_DS,
    DB_TYPE_INTERVAL_YM as DB_TYPE_INTERVAL_YM,
    DB_TYPE_JSON as DB_TYPE_JSON,
    DB_TYPE_LONG as DB_TYPE_LONG,
    DB_TYPE_LONG_NVARCHAR as DB_TYPE_LONG_NVARCHAR,
    DB_TYPE_LONG_RAW as DB_TYPE_LONG_RAW,
    DB_TYPE_NCHAR as DB_TYPE_NCHAR,
    DB_TYPE_NCLOB as DB_TYPE_NCLOB,
    DB_TYPE_NUMBER as DB_TYPE_NUMBER,
    DB_TYPE_NVARCHAR as DB_TYPE_NVARCHAR,
    DB_TYPE_OBJECT as DB_TYPE_OBJECT,
    DB_TYPE_RAW as DB_TYPE_RAW,
    DB_TYPE_ROWID as DB_TYPE_ROWID,
    DB_TYPE_TIMESTAMP as DB_TYPE_TIMESTAMP,
    DB_TYPE_TIMESTAMP_LTZ as DB_TYPE_TIMESTAMP_LTZ,
    DB_TYPE_TIMESTAMP_TZ as DB_TYPE_TIMESTAMP_TZ,
    DB_TYPE_UNKNOWN as DB_TYPE_UNKNOWN,
    DB_TYPE_UROWID as DB_TYPE_UROWID,
    DB_TYPE_VARCHAR as DB_TYPE_VARCHAR,

    # API types
    BINARY as BINARY,
    DATETIME as DATETIME,
    NUMBER as NUMBER,
    ROWID as ROWID,
    STRING as STRING
)

from .thick_impl import (
    clientversion as clientversion,
    init_oracle_client as init_oracle_client
)

from .constructors import (
    Binary as Binary,
    Date as Date,
    DateFromTicks as DateFromTicks,
    Time as Time,
    TimeFromTicks as TimeFromTicks,
    Timestamp as Timestamp,
    TimestampFromTicks as TimestampFromTicks
)

package = sys.modules[__name__]
base_impl.init_base_impl(package)
thick_impl.init_thick_impl(package)
thin_impl.init_thin_impl(package)
del package

# future object used for managing backwards incompatible changes
class Future:

    def __getattr__(self, name):
        return None

    def __setattr__(self, name, value):
        pass

__future__ = Future()

# remove unnecessary symbols
del exceptions, errors, connection, pool, constants, driver_mode, sys
del constructors, dsn, lob, base_impl, thick_impl, thin_impl, utils, var
del connect_params, pool_params, subscr, aq, soda, cursor, dbobject

# general aliases (for backwards compatibility)
ObjectType = DbObjectType
Object = DbObject
SessionPool = ConnectionPool
version = __version__

# aliases for database types (for backwards compatibility)
BFILE = DB_TYPE_BFILE
BLOB = DB_TYPE_BLOB
BOOLEAN = DB_TYPE_BOOLEAN
CLOB = DB_TYPE_CLOB
CURSOR = DB_TYPE_CURSOR
FIXED_CHAR = DB_TYPE_CHAR
FIXED_NCHAR = DB_TYPE_NCHAR
INTERVAL = DB_TYPE_INTERVAL_DS
LONG_BINARY = DB_TYPE_LONG_RAW
LONG_STRING = DB_TYPE_LONG
NATIVE_INT = DB_TYPE_BINARY_INTEGER
NATIVE_FLOAT = DB_TYPE_BINARY_DOUBLE
NCHAR = DB_TYPE_NVARCHAR
OBJECT = DB_TYPE_OBJECT
NCLOB = DB_TYPE_NCLOB
TIMESTAMP = DB_TYPE_TIMESTAMP

# aliases for authhentication modes (for backwards compatibility)
DEFAULT_AUTH = AUTH_MODE_DEFAULT
SYSASM = AUTH_MODE_SYSASM
SYSBKP = AUTH_MODE_SYSBKP
SYSDBA = AUTH_MODE_SYSDBA
SYSDGD = AUTH_MODE_SYSDGD
SYSKMT = AUTH_MODE_SYSKMT
SYSOPER = AUTH_MODE_SYSOPER
SYSRAC = AUTH_MODE_SYSRAC
PRELIM_AUTH = AUTH_MODE_PRELIM

# aliases for pool "get" modes (for backwards compatibility)
SPOOL_ATTRVAL_WAIT = POOL_GETMODE_WAIT
SPOOL_ATTRVAL_NOWAIT = POOL_GETMODE_NOWAIT
SPOOL_ATTRVAL_FORCEGET = POOL_GETMODE_FORCEGET
SPOOL_ATTRVAL_TIMEDWAIT = POOL_GETMODE_TIMEDWAIT

# aliases for purity (for backwards compatibility)
ATTR_PURITY_DEFAULT = PURITY_DEFAULT
ATTR_PURITY_NEW = PURITY_NEW
ATTR_PURITY_SELF = PURITY_SELF

# aliases for subscription protocols (for backwards compatibility)
SUBSCR_PROTO_OCI = SUBSCR_PROTO_CALLBACK
