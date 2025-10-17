# -----------------------------------------------------------------------------
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
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# __init__.py
#
# Package initialization module.
# -----------------------------------------------------------------------------

import collections
import sys
import warnings

if sys.version_info[:2] < (3, 9):
    message = (
        f"Python {sys.version_info[0]}.{sys.version_info[1]} is no longer "
        "supported by the Python core team. Therefore, support for it is "
        "deprecated in python-oracledb and will be removed in a future release"
    )
    warnings.warn(message)

from . import base_impl, thick_impl, thin_impl

from .base_impl import (
    ApiType as ApiType,
    DbType as DbType,
)

from .enums import (
    AuthMode as AuthMode,
    PipelineOpType as PipelineOpType,
    PoolGetMode as PoolGetMode,
    Purity as Purity,
    VectorFormat as VectorFormat,
)

from . import constants, version

from .arrow_array import (
    ArrowArray as ArrowArray,
)

from .constructors import (
    Binary as Binary,
    Date as Date,
    DateFromTicks as DateFromTicks,
    Time as Time,
    TimeFromTicks as TimeFromTicks,
    Timestamp as Timestamp,
    TimestampFromTicks as TimestampFromTicks,
)

from .dataframe import (
    DataFrame as DataFrame,
)

from .dbobject import (
    DbObject as DbObject,
    DbObjectAttr as DbObjectAttr,
    DbObjectType as DbObjectType,
)

from .defaults import (
    Defaults as Defaults,
)

from .driver_mode import (
    is_thin_mode as is_thin_mode,
)

from .dsn import (
    makedsn as makedsn,
)

from .errors import (
    _Error as _Error,
)

from .exceptions import (
    Warning as Warning,
    Error as Error,
    DatabaseError as DatabaseError,
    DataError as DataError,
    IntegrityError as IntegrityError,
    InterfaceError as InterfaceError,
    InternalError as InternalError,
    NotSupportedError as NotSupportedError,
    OperationalError as OperationalError,
    ProgrammingError as ProgrammingError,
)

from .fetch_info import (
    FetchInfo as FetchInfo,
)

from .future import (
    __future__ as __future__,
)

from .lob import (
    LOB as LOB,
    AsyncLOB as AsyncLOB,
)

from .pipeline import (
    Pipeline as Pipeline,
    PipelineOp as PipelineOp,
    PipelineOpResult as PipelineOpResult,
    create_pipeline as create_pipeline,
)

from .soda import (
    SodaDatabase as SodaDatabase,
    SodaCollection as SodaCollection,
    SodaDocument as SodaDocument,
    SodaDocCursor as SodaDocCursor,
    SodaOperation as SodaOperation,
)

from .sparse_vector import (
    SparseVector as SparseVector,
)

from .utils import (
    clientversion as clientversion,
    enable_thin_mode as enable_thin_mode,
    from_arrow as from_arrow,
    init_oracle_client as init_oracle_client,
    register_params_hook as register_params_hook,
    register_password_type as register_password_type,
    register_protocol as register_protocol,
    unregister_params_hook as unregister_params_hook,
)

from .var import (
    Var as Var,
)


# module attributes
apilevel: str = "2.0"
"""
A string constant stating the Python DB API level supported by python-oracledb.
"""

defaults: Defaults = Defaults()
"""
The defaults object for setting default behaviors of python-oracledb.
"""

paramstyle: str = "named"
"""
A string constant stating the type of parameter marker formatting expected by
the interface. Currently 'named' as in 'where name = :name'.
"""

threadsafety: int = 2
"""
An integer constant stating the level of thread safety that python-oracledb
supports. Currently 2, which means that threads may share the module and
connections, but not cursors. Sharing means that a thread may use a resource
without wrapping it using a mutex semaphore to implement resource locking.
"""

__version__: str = version.__version__
"""
A string constant stating the version of the module.
"""


# API types
BINARY: ApiType = base_impl.BINARY
"""
This type object is used to describe columns in a database that contain binary
data. The database types :data:`DB_TYPE_RAW` and :data:`DB_TYPE_LONG_RAW` will
compare equal to this value. If a variable is created with this type, the
database type :data:`DB_TYPE_RAW` will be used.
"""

DATETIME: ApiType = base_impl.DATETIME
"""
This type object is used to describe columns in a database that are dates.  The
database types :data:`DB_TYPE_DATE`, :data:`DB_TYPE_TIMESTAMP`,
:data:`DB_TYPE_TIMESTAMP_LTZ` and :data:`DB_TYPE_TIMESTAMP_TZ` will all compare
equal to this value. If a variable is created with this type, the database type
:data:`DB_TYPE_DATE` will be used.
"""

NUMBER: ApiType = base_impl.NUMBER
"""
This type object is used to describe columns in a database that are numbers.
The database types :data:`DB_TYPE_BINARY_DOUBLE`, :data:`DB_TYPE_BINARY_FLOAT`,
:data:`DB_TYPE_BINARY_INTEGER` and :data:`DB_TYPE_NUMBER` will all compare
equal to this value. If a variable is created with this type, the database type
:data:`DB_TYPE_NUMBER` will be used.
"""

ROWID: ApiType = base_impl.ROWID
"""
This type object is used to describe the pseudo column "rowid". The database
types :data:`DB_TYPE_ROWID` and :data:`DB_TYPE_UROWID` will compare equal to
this value. If a variable is created with this type, the database type
:data:`DB_TYPE_VARCHAR` will be used.
"""

STRING: ApiType = base_impl.STRING
"""
This type object is used to describe columns in a database that are strings.
The database types :data:`DB_TYPE_CHAR`, :data:`DB_TYPE_LONG`,
:data:`DB_TYPE_NCHAR`, :data:`DB_TYPE_NVARCHAR` and :data:`DB_TYPE_VARCHAR`
will all compare equal to this value. If a variable is created with this type,
the database type :data:`DB_TYPE_VARCHAR` will be used.
"""


# connection authorization modes
AUTH_MODE_DEFAULT: AuthMode = AuthMode.DEFAULT
"""
This constant is used to specify that default authentication is to take place.
This is the default value if no mode is passed at all.

It can be used for standalone and pooled connections in python-oracledb Thin
mode, and for standalone connections in Thick mode.

This constant deprecates the ``DEFAULT_AUTH`` constant that was used in the
obsolete cx_Oracle driver, and was the default ``mode`` value.
"""

AUTH_MODE_PRELIM: AuthMode = AuthMode.PRELIM
"""
This constant is used to specify that preliminary authentication is to be used.
This is needed for performing database startup and shutdown.

It can only be used in python-oracledb Thick mode for standalone connections.

This constant deprecates the ``PRELIM_AUTH`` constant that was used in the
obsolete cx_Oracle driver.
"""

AUTH_MODE_SYSASM: AuthMode = AuthMode.SYSASM
"""
This constant is used to specify that SYSASM access is to be acquired.

It can be used for standalone and pooled connections in python-oracledb Thin
mode, and for standalone connections in Thick mode.

This constant deprecates the ``SYSASM`` constant that was used in the obsolete
cx_Oracle driver.
"""

AUTH_MODE_SYSBKP: AuthMode = AuthMode.SYSBKP
"""
This constant is used to specify that SYSBACKUP access is to be acquired.

It can be used for standalone and pooled connections in python-oracledb Thin
mode, and for standalone connections in Thick mode.

This constant deprecates the ``SYSBKP`` constant that was used in the
obsolete cx_Oracle driver.
"""

AUTH_MODE_SYSDBA: AuthMode = AuthMode.SYSDBA
"""
This constant is used to specify that SYSDBA access is to be acquired.

It can be used for standalone and pooled connections in python-oracledb Thin
mode, and for standalone connections in Thick mode.

This constant deprecates the ``SYSDBA`` constant that was used in the obsolete
cx_Oracle driver.
"""

AUTH_MODE_SYSDGD: AuthMode = AuthMode.SYSDGD
"""
This constant is used to specify that SYSDG access is to be acquired.

It can be used for standalone and pooled connections in python-oracledb Thin
mode, and for standalone connections in Thick mode.

This constant deprecates the ``SYSDGD`` constant that was used in the obsolete
cx_Oracle driver.
"""

AUTH_MODE_SYSKMT: AuthMode = AuthMode.SYSKMT
"""
This constant is used to specify that SYSKM access is to be acquired.

It can be used for standalone and pooled connections in python-oracledb Thin
mode, and for standalone connections in Thick mode.

This constant deprecates the ``SYSKMT`` constant that was used in the obsolete
cx_Oracle driver.
"""

AUTH_MODE_SYSOPER: AuthMode = AuthMode.SYSOPER
"""
This constant is used to specify that SYSOPER access is to be acquired.

It can be used for standalone and pooled connections in python-oracledb Thin
mode, and for standalone connections in Thick mode.

This constant deprecates the ``SYSOPER`` constant that was used in the obsolete
cx_Oracle driver.
"""

AUTH_MODE_SYSRAC: AuthMode = AuthMode.SYSRAC
"""
This constant is used to specify that SYSRAC access is to be acquired.

It can be used for standalone and pooled connections in python-oracledb Thin
mode, and for standalone connections in Thick mode.

This constant deprecates the ``SYSRAC`` constant that was used in the obsolete
cx_Oracle driver.
"""


# database shutdown modes
DBSHUTDOWN_ABORT: int = constants.DBSHUTDOWN_ABORT
"""
This constant is used to specify that the caller should not wait for current
processing to complete or for users to disconnect from the database. This
should only be used in unusual circumstances since database recovery may be
necessary upon next startup.
"""

DBSHUTDOWN_FINAL: int = constants.DBSHUTDOWN_FINAL
"""
This constant is used to specify that the instance can be truly halted. This
should only be done after the database has been shutdown with one of the other
modes (except abort) and the database has been closed and dismounted using the
appropriate SQL commands.
"""

DBSHUTDOWN_IMMEDIATE: int = constants.DBSHUTDOWN_IMMEDIATE
"""
This constant is used to specify that all uncommitted transactions should be
rolled back and any connected users should be disconnected.
"""

DBSHUTDOWN_TRANSACTIONAL: int = constants.DBSHUTDOWN_TRANSACTIONAL
"""
This constant is used to specify that further connections to the database
should be prohibited and no new transactions should be allowed. It then waits
for all active transactions to complete.
"""

DBSHUTDOWN_TRANSACTIONAL_LOCAL: int = constants.DBSHUTDOWN_TRANSACTIONAL_LOCAL
"""
This constant is used to specify that further connections to the database
should be prohibited and no new transactions should be allowed. It then waits
for only local active transactions to complete.
"""


# database types
DB_TYPE_BFILE: DbType = base_impl.DB_TYPE_BFILE
"""
Describes columns, attributes or array elements in a database that are of type
BFILE. It will compare equal to the DB API type :data:`BINARY`.
"""

DB_TYPE_BINARY_DOUBLE: DbType = base_impl.DB_TYPE_BINARY_DOUBLE
"""
Describes columns, attributes or array elements in a database that are of type
BINARY_DOUBLE. It will compare equal to the DB API type :data:`NUMBER`.
"""

DB_TYPE_BINARY_FLOAT: DbType = base_impl.DB_TYPE_BINARY_FLOAT
"""
Describes columns, attributes or array elements in a database that are of type
BINARY_FLOAT. It will compare equal to the DB API type :data:`NUMBER`.
"""

DB_TYPE_BINARY_INTEGER: DbType = base_impl.DB_TYPE_BINARY_INTEGER
"""
Describes attributes or array elements in a database that are of type
BINARY_INTEGER. It will compare equal to the DB API type :data:`NUMBER`.
"""

DB_TYPE_BLOB: DbType = base_impl.DB_TYPE_BLOB
"""
Describes columns, attributes or array elements in a database that are of type
BLOB. It will compare equal to the DB API type :data:`BINARY`.
"""

DB_TYPE_BOOLEAN: DbType = base_impl.DB_TYPE_BOOLEAN
"""
Describes attributes or array elements in a database that are of type BOOLEAN.
It is only available in Oracle 12.1 and higher and only within PL/SQL.
"""

DB_TYPE_CHAR: DbType = base_impl.DB_TYPE_CHAR
"""
Describes columns, attributes or array elements in a database that are of type
CHAR. It will compare equal to the DB API type :data:`STRING`.

Note that these are fixed length string values and behave differently from
VARCHAR2.
"""

DB_TYPE_CLOB: DbType = base_impl.DB_TYPE_CLOB
"""
Describes columns, attributes or array elements in a database that are of type
CLOB. It will compare equal to the DB API type :data:`STRING`.
"""

DB_TYPE_CURSOR: DbType = base_impl.DB_TYPE_CURSOR
"""
Describes columns in a database that are of type CURSOR. In PL/SQL, these are
known as REF CURSOR.
"""

DB_TYPE_DATE: DbType = base_impl.DB_TYPE_DATE
"""
Describes columns, attributes or array elements in a database that are of type
DATE. It will compare equal to the DB API type :data:`DATETIME`.
"""

DB_TYPE_INTERVAL_DS: DbType = base_impl.DB_TYPE_INTERVAL_DS
"""
Describes columns, attributes or array elements in a database that are of type
INTERVAL DAY TO SECOND.
"""

DB_TYPE_INTERVAL_YM: DbType = base_impl.DB_TYPE_INTERVAL_YM
"""
Describes columns, attributes or array elements in a database that are of type
INTERVAL YEAR TO MONTH.
"""

DB_TYPE_JSON: DbType = base_impl.DB_TYPE_JSON
"""
Describes columns in a database that are of type JSON (with Oracle Database 21
or later).
"""

DB_TYPE_LONG: DbType = base_impl.DB_TYPE_LONG
"""
Describes columns, attributes or array elements in a database that are of type
LONG. It will compare equal to the DB API type :data:`STRING`.
"""

DB_TYPE_LONG_NVARCHAR: DbType = base_impl.DB_TYPE_LONG_NVARCHAR
"""
This constant can be used in output type handlers when fetching NCLOB columns
as a string.  (Note a type handler is not needed if
:data:`oracledb.defaults.fetch_lobs <Defaults.fetch_lobs>`, or the equivalent
execution parameter, is set to *False*).  For IN binds, this constant can be
used to create a bind variable in :meth:`Cursor.var()` or via
:meth:`Cursor.setinputsizes()`.  The ``DB_TYPE_LONG_NVARCHAR`` value won't be
shown in query metadata since it is not a database type.

It will compare equal to the DB API type :data:`STRING`.
"""

DB_TYPE_LONG_RAW: DbType = base_impl.DB_TYPE_LONG_RAW
"""
Describes columns, attributes or array elements in a database that are of type
LONG RAW. It will compare equal to the DB API type :data:`BINARY`.
"""

DB_TYPE_NCHAR: DbType = base_impl.DB_TYPE_NCHAR
"""
Describes columns, attributes or array elements in a database that are of type
NCHAR. It will compare equal to the DB API type :data:`STRING`.

Note that these are fixed length string values and behave differently from
NVARCHAR2.
"""

DB_TYPE_NCLOB: DbType = base_impl.DB_TYPE_NCLOB
"""
Describes columns, attributes or array elements in a database that are of type
NCLOB. It will compare equal to the DB API type :data:`STRING`.
"""

DB_TYPE_NUMBER: DbType = base_impl.DB_TYPE_NUMBER
"""
Describes columns, attributes or array elements in a database that are of type
NUMBER. It will compare equal to the DB API type :data:`NUMBER`.
"""

DB_TYPE_NVARCHAR: DbType = base_impl.DB_TYPE_NVARCHAR
"""
Describes columns, attributes or array elements in a database that are of type
NVARCHAR2. It will compare equal to the DB API type :data:`STRING`.
"""

DB_TYPE_OBJECT: DbType = base_impl.DB_TYPE_OBJECT
"""
Describes columns, attributes or array elements in a database that are an
instance of a named SQL or PL/SQL type.
"""

DB_TYPE_RAW: DbType = base_impl.DB_TYPE_RAW
"""
Describes columns, attributes or array elements in a database that are of type
RAW. It will compare equal to the DB API type :data:`BINARY`.
"""

DB_TYPE_ROWID: DbType = base_impl.DB_TYPE_ROWID
"""
Describes columns, attributes or array elements in a database that are of type
ROWID or UROWID. It will compare equal to the DB API type :data:`ROWID`.
"""

DB_TYPE_TIMESTAMP: DbType = base_impl.DB_TYPE_TIMESTAMP
"""
Describes columns, attributes or array elements in a database that are of type
TIMESTAMP. It will compare equal to the DB API type :data:`DATETIME`.
"""

DB_TYPE_TIMESTAMP_LTZ: DbType = base_impl.DB_TYPE_TIMESTAMP_LTZ
"""
Describes columns, attributes or array elements in a database that are of type
TIMESTAMP WITH LOCAL TIME ZONE. It will compare equal to the DB API type
:data:`DATETIME`.
"""

DB_TYPE_TIMESTAMP_TZ: DbType = base_impl.DB_TYPE_TIMESTAMP_TZ
"""
Describes columns, attributes or array elements in a database that are of type
TIMESTAMP WITH TIME ZONE. It will compare equal to the DB API type
:data:`DATETIME`.
"""

DB_TYPE_UNKNOWN: DbType = base_impl.DB_TYPE_UNKNOWN
"""
Describes columns, attributes or array elements in a database that are of an
unknown type.
"""

DB_TYPE_UROWID: DbType = base_impl.DB_TYPE_UROWID
"""
Describes columns, attributes or array elements in a database that are of type
UROWID. It will compare equal to the DB API type :data:`ROWID`.
"""

DB_TYPE_VARCHAR: DbType = base_impl.DB_TYPE_VARCHAR
"""
Describes columns, attributes or array elements in a database that are of type
VARCHAR2. It will compare equal to the DB API type :data:`STRING`.
"""

DB_TYPE_VECTOR: DbType = base_impl.DB_TYPE_VECTOR
"""
Describes columns, attributes or array elements in a database that are of type
VECTOR (with Oracle Database 23 or later).
"""

DB_TYPE_XMLTYPE: DbType = base_impl.DB_TYPE_XMLTYPE
"""
Describes columns, attributes or array elements in a database that are of type
SYS.XMLTYPE.
"""


# AQ dequeue modes
DEQ_BROWSE: int = constants.DEQ_BROWSE
"""
This constant is used to specify that dequeue should read the message without
acquiring any lock on the message (equivalent to a select statement).
"""

DEQ_LOCKED: int = constants.DEQ_LOCKED
"""
This constant is used to specify that dequeue should read and obtain a write
lock on the message for the duration of the transaction (equivalent to a select
for update statement).
"""

DEQ_REMOVE: int = constants.DEQ_REMOVE
"""
This constant is used to specify that dequeue should read the message and
update or delete it. This is the default value.
"""

DEQ_REMOVE_NODATA: int = constants.DEQ_REMOVE_NODATA
"""
This constant is used to specify that dequeue should confirm receipt of the
message but not deliver the actual message content.
"""


# AQ dequeue navigation modes
DEQ_FIRST_MSG: int = constants.DEQ_FIRST_MSG
"""
This constant is used to specify that dequeue should retrieve the first
available message that matches the search criteria. This resets the
position to the beginning of the queue.
"""

DEQ_NEXT_MSG: int = constants.DEQ_NEXT_MSG
"""
This constant is used to specify that dequeue should retrieve the next
available message that matches the search criteria. If the previous message
belongs to a message group, AQ retrieves the next available message that
matches the search criteria and belongs to the message group. This is the
default.
"""

DEQ_NEXT_TRANSACTION: int = constants.DEQ_NEXT_TRANSACTION
"""
This constant is used to specify that dequeue should skip the remainder of the
transaction group and retrieve the first message of the next transaction group.
This option can only be used if message grouping is enabled for the current
queue.
"""


# AQ dequeue visibility modes
DEQ_IMMEDIATE: int = constants.DEQ_IMMEDIATE
"""
This constant is used to specify that dequeue should perform its work as part
of an independent transaction.
"""

DEQ_ON_COMMIT: int = constants.DEQ_ON_COMMIT
"""
This constant is used to specify that dequeue should be part of the current
transaction. This is the default value.
"""


# AQ dequeue wait modes
DEQ_NO_WAIT: int = constants.DEQ_NO_WAIT
"""
This constant is used to specify that dequeue not wait for messages to be
available for dequeuing.
"""

DEQ_WAIT_FOREVER: int = constants.DEQ_WAIT_FOREVER
"""
This constant is used to specify that dequeue should wait forever for messages
to be available for dequeuing. This is the default value.
"""


# AQ enqueue visibility modes
ENQ_IMMEDIATE: int = constants.ENQ_IMMEDIATE
"""
This constant is used to specify that enqueue should perform its work as
part of an independent transaction.

The use of this constant with bulk enqueuing is only supported in
python-oracledb Thick mode.
"""

ENQ_ON_COMMIT: int = constants.ENQ_ON_COMMIT
"""
This constant is used to specify that enqueue should be part of the current
transaction. This is the default value.
"""


# event types
EVENT_AQ: int = constants.EVENT_AQ
"""
This constant is used to specify that one or more messages are available for
dequeuing on the queue specified when the subscription was created.
"""

EVENT_DEREG: int = constants.EVENT_DEREG
"""
This constant is used to specify that the subscription has been deregistered
and no further notifications will be sent.
"""

EVENT_NONE: int = constants.EVENT_NONE
"""
This constant is used to specify no information is available about the event.
"""

EVENT_OBJCHANGE: int = constants.EVENT_OBJCHANGE
"""
This constant is used to specify that a database change has taken place on a
table registered with the :meth:`Subscription.registerquery()` method.
"""

EVENT_QUERYCHANGE: int = constants.EVENT_QUERYCHANGE
"""
This constant is used to specify that the result set of a query registered with
the :meth:`Subscription.registerquery()` method has been changed.
"""

EVENT_SHUTDOWN: int = constants.EVENT_SHUTDOWN
"""
This constant is used to specify that the instance is in the process of being
shut down.
"""

EVENT_SHUTDOWN_ANY: int = constants.EVENT_SHUTDOWN_ANY
"""
This constant is used to specify that any instance (when running RAC) is in the
process of being shut down.
"""

EVENT_STARTUP: int = constants.EVENT_STARTUP
"""
This constant is used to specify that the instance is in the process of being
started up.
"""


# AQ delivery modes
MSG_BUFFERED: int = constants.MSG_BUFFERED
"""
This constant is used to specify that enqueue or dequeue operations should
enqueue or dequeue buffered messages, respectively. For multi-consumer queues,
a `subscriber <https://www.oracle.com/pls/topic/lookup?ctx=dblatest
&id=GUID-5FB46C6A-BB22-4CDE-B7D6-E242DC8808D8>`__ with buffered delivery mode
needs to be created prior to enqueuing buffered messages.

This mode is not supported for bulk array operations in python-oracledb Thick
mode, and for JSON payloads.
"""

MSG_PERSISTENT: int = constants.MSG_PERSISTENT
"""
This constant is used to specify that enqueue/dequeue operations should enqueue
or dequeue persistent messages. This is the default value.
"""

MSG_PERSISTENT_OR_BUFFERED: int = constants.MSG_PERSISTENT_OR_BUFFERED
"""
This constant is used to specify that dequeue operations should dequeue either
persistent or buffered messages.
"""


# AQ message states
MSG_EXPIRED: int = constants.MSG_EXPIRED
"""
This constant is used to specify that the message has been moved to the
exception queue.
"""

MSG_PROCESSED: int = constants.MSG_PROCESSED
"""
This constant is used to specify that the message has been processed and has
been retained.
"""

MSG_READY: int = constants.MSG_READY
"""
This constant is used to specify that the message is ready to be processed.
"""

MSG_WAITING: int = constants.MSG_WAITING
"""
This constant is used to specify that the message delay has not yet been
reached.
"""


# other AQ constants
MSG_NO_DELAY: int = constants.MSG_NO_DELAY
"""
This constant is a possible value for the :attr:`~MessageProperties.delay`
attribute of the message properties object passed as the ``msgproperties``
parameter to the :meth:`Queue.deqone()` or :meth:`Queue.deqmany()` and
:meth:`Queue.enqone()` or :meth:`Queue.enqmany()` methods. It specifies that
no delay should be imposed and the message should be immediately available for
dequeuing. This is also the default value.
"""

MSG_NO_EXPIRATION: int = constants.MSG_NO_EXPIRATION
"""
This constant is a possible value for the :attr:`~MessageProperties.expiration`
attribute of the message properties object passed as the ``msgproperties``
parameter to the :meth:`Queue.deqone()` or :meth:`Queue.deqmany()` and
:meth:`Queue.enqone()` or :meth:`Queue.enqmany()` methods. It specifies that
the message never expires. This is also the default value.
"""


# operation codes (CQN)
OPCODE_ALLOPS: int = constants.OPCODE_ALLOPS
"""
This constant is used to specify that messages should be sent for all
operations.
"""

OPCODE_ALLROWS: int = constants.OPCODE_ALLROWS
"""
This constant is used to specify that the table or query has been completely
invalidated.
"""

OPCODE_ALTER: int = constants.OPCODE_ALTER
"""
This constant is used to specify that messages should be sent when a registered
table has been altered in some fashion by DDL, or that the message identifies a
table that has been altered.
"""

OPCODE_DELETE: int = constants.OPCODE_DELETE
"""
This constant is used to specify that messages should be sent when data is
deleted, or that the message identifies a row that has been deleted.
"""

OPCODE_DROP: int = constants.OPCODE_DROP
"""
This constant is used to specify that messages should be sent when a registered
table has been dropped, or that the message identifies a table that has been
dropped.
"""

OPCODE_INSERT: int = constants.OPCODE_INSERT
"""
This constant is used to specify that messages should be sent when data is
inserted, or that the message identifies a row that has been inserted.
"""

OPCODE_UPDATE: int = constants.OPCODE_UPDATE
"""
This constant is used to specify that messages should be sent when data is
updated, or that the message identifies a row that has been updated.
"""


# pipeline operation types
PIPELINE_OP_TYPE_CALL_FUNC: PipelineOpType = PipelineOpType.CALL_FUNC
"""
This constant identifies the type of operation as the calling of a stored
function.
"""

PIPELINE_OP_TYPE_CALL_PROC: PipelineOpType = PipelineOpType.CALL_PROC
"""
This constant identifies the type of operation as the calling of a stored
procedure.
"""

PIPELINE_OP_TYPE_COMMIT: PipelineOpType = PipelineOpType.COMMIT
"""
This constant identifies the type of operation as the performing of a commit.
"""

PIPELINE_OP_TYPE_EXECUTE: PipelineOpType = PipelineOpType.EXECUTE
"""
This constant identifies the type of operation as the executing of a statement.
"""

PIPELINE_OP_TYPE_EXECUTE_MANY: PipelineOpType = PipelineOpType.EXECUTE_MANY
"""
This constant identifies the type of operations as the executing of a statement
multiple times.
"""

PIPELINE_OP_TYPE_FETCH_ALL: PipelineOpType = PipelineOpType.FETCH_ALL
"""
This constant identifies the type of operation as the executing of a query and
returning all of the rows from the result set.
"""

PIPELINE_OP_TYPE_FETCH_MANY: PipelineOpType = PipelineOpType.FETCH_MANY
"""
This constant identifies the type of operation as the executing of a query and
returning up to the specified number of rows from the result set.
"""

PIPELINE_OP_TYPE_FETCH_ONE: PipelineOpType = PipelineOpType.FETCH_ONE
"""
This constant identifies the type of operation as the executing of a query and
returning the first row of the result set.
"""


# connection pool "get" modes
POOL_GETMODE_FORCEGET: PoolGetMode = PoolGetMode.FORCEGET
"""
This constant is used to specify that a new connection should be created and
returned by :meth:`ConnectionPool.acquire()` if there are no free connections
available in the pool and the pool is already at its maximum size.

When a connection acquired in this mode is eventually released back to the
pool, it will be dropped and not added to the pool if the pool is still at its
maximum size.

This constant deprecates the ``SPOOL_ATTRVAL_FORCEGET`` constant that was used
in the obsolete cx_Oracle driver.
"""

POOL_GETMODE_NOWAIT: PoolGetMode = PoolGetMode.NOWAIT
"""
This constant is used to specify that an exception should be raised by
:meth:`ConnectionPool.acquire()` when all currently created connections are
already in use and so :meth:`~ConnectionPool.acquire()` cannot immediately
return a connection. Note the exception may occur even if the pool is smaller
than its maximum size.

This constant deprecates the ``SPOOL_ATTRVAL_NOWAIT`` constant that was used in
the obsolete cx_Oracle driver, and was the default ``getmode`` value.
"""

POOL_GETMODE_TIMEDWAIT: PoolGetMode = PoolGetMode.TIMEDWAIT
"""
This constant is used to specify that :meth:`ConnectionPool.acquire()` should
wait for a period of time (defined by the ``wait_timeout`` parameter) for a
connection to become available before returning with an error.

This constant deprecates the ``SPOOL_ATTRVAL_TIMEDWAIT`` constant that was used
in the obsolete cx_Oracle driver.
"""

POOL_GETMODE_WAIT: PoolGetMode = PoolGetMode.WAIT
"""
This constant is used to specify that :meth:`ConnectionPool.acquire()` should
wait until a connection is available if there are currently no free connections
available in the pool.  This is the default value.

This constant deprecates the ``SPOOL_ATTRVAL_WAIT`` constant that was used in
the obsolete cx_Oracle driver.
"""


# connection pool purity
PURITY_DEFAULT: Purity = Purity.DEFAULT
"""
This constant is used to specify that the purity of the session is the default
value identified by Oracle (see Oracle's documentation for more information).
This is the default value.

This constant deprecates the ``ATTR_PURITY_DEFAULT`` constant that was used in
the obsolete cx_Oracle driver, and was the default ``purity`` value.
"""

PURITY_NEW: Purity = Purity.NEW
"""
This constant is used to specify that the session acquired from the pool should
be new and not have any prior session state.

This constant deprecates the ``ATTR_PURITY_NEW`` constant that was used in the
obsolete cx_Oracle driver.
"""

PURITY_SELF: Purity = Purity.SELF
"""
This constant is used to specify that the session acquired from the pool need
not be new and may have prior session state.

This constant deprecates the ``ATTR_PURITY_SELF`` constant that was used in the
obsolete cx_Oracle driver.
"""


# subscription grouping classes
SUBSCR_GROUPING_CLASS_NONE: int = constants.SUBSCR_GROUPING_CLASS_NONE
"""
This constant is used to specify that no grouping should take place.
"""

SUBSCR_GROUPING_CLASS_TIME: int = constants.SUBSCR_GROUPING_CLASS_TIME
"""
This constant is used to specify that events are to be grouped by the period of
time in which they are received.
"""


# subscription grouping types
SUBSCR_GROUPING_TYPE_SUMMARY: int = constants.SUBSCR_GROUPING_TYPE_SUMMARY
"""
This constant is used to specify that when events are grouped a summary of the
events should be sent instead of the individual events. This is the default
value.
"""

SUBSCR_GROUPING_TYPE_LAST: int = constants.SUBSCR_GROUPING_TYPE_LAST
"""
This constant is used to specify that when events are grouped the last event
that makes up the group should be sent instead of the individual events.
"""


# subscription namespaces
SUBSCR_NAMESPACE_AQ: int = constants.SUBSCR_NAMESPACE_AQ
"""
This constant is used to specify that notifications should be sent when a queue
has messages available to dequeue.
"""

SUBSCR_NAMESPACE_DBCHANGE: int = constants.SUBSCR_NAMESPACE_DBCHANGE
"""
This constant is used to specify that database change notification or query
change notification messages are to be sent. This is the default value.
"""


# subscription protocols
SUBSCR_PROTO_CALLBACK: int = constants.SUBSCR_PROTO_CALLBACK
"""
This constant is used to specify that notifications will be sent to the
callback routine identified when the subscription was created. It is the
default value and the only value currently supported.
"""

SUBSCR_PROTO_HTTP: int = constants.SUBSCR_PROTO_HTTP
"""
This constant is used to specify that notifications will be sent to an HTTP
URL when a message is generated. This value is currently not supported.
"""

SUBSCR_PROTO_MAIL: int = constants.SUBSCR_PROTO_MAIL
"""
This constant is used to specify that notifications will be sent to an e-mail
address when a message is generated. This value is currently not supported.
"""

SUBSCR_PROTO_SERVER: int = constants.SUBSCR_PROTO_SERVER
"""
This constant is used to specify that notifications will be sent to a PL/SQL
procedure when a message is generated. This value is currently not supported.
"""


# subscription quality of service
SUBSCR_QOS_BEST_EFFORT: int = constants.SUBSCR_QOS_BEST_EFFORT
"""
This constant is used to specify that best effort filtering for query result
set changes is acceptable. False positive notifications may be received. This
behaviour may be suitable for caching applications.
"""

SUBSCR_QOS_DEFAULT: int = constants.SUBSCR_QOS_DEFAULT
"""
This constant is used to specify that the default behavior for subscriptions
should be used.
"""

SUBSCR_QOS_DEREG_NFY: int = constants.SUBSCR_QOS_DEREG_NFY
"""
This constant is used to specify that the subscription should be automatically
unregistered after the first notification is received.
"""

SUBSCR_QOS_QUERY: int = constants.SUBSCR_QOS_QUERY
"""
This constant is used to specify that notifications should be sent if the
result set of the registered query changes. By default, no false positive
notifications will be generated.
"""

SUBSCR_QOS_RELIABLE: int = constants.SUBSCR_QOS_RELIABLE
"""
This constant is used to specify that notifications should not be lost in the
event of database failure.
"""

SUBSCR_QOS_ROWIDS: int = constants.SUBSCR_QOS_ROWIDS
"""
This constant is used to specify that the rowids of the inserted, updated or
deleted rows should be included in the message objects that are sent.
"""


# flags for tpc_begin()
TPC_BEGIN_JOIN: int = base_impl.TPC_TXN_FLAGS_JOIN
"""
This constant is used to join an existing TPC transaction.
"""

TPC_BEGIN_NEW: int = base_impl.TPC_TXN_FLAGS_NEW
"""
This constant is used to create a new TPC transaction.
"""

TPC_BEGIN_PROMOTE: int = base_impl.TPC_TXN_FLAGS_PROMOTE
"""
This constant is used to promote a local transaction to a TPC transaction.
"""

TPC_BEGIN_RESUME: int = base_impl.TPC_TXN_FLAGS_RESUME
"""
This constant is used to resume an existing TPC transaction.
"""


# flags for tpc_end()
TPC_END_NORMAL: int = constants.TPC_END_NORMAL
"""
This constant is used to end TPC transaction participation normally.
"""

TPC_END_SUSPEND: int = constants.TPC_END_SUSPEND
"""
This constant is used to suspend a TPC transaction.
"""


# vector formats
VECTOR_FORMAT_BINARY: VectorFormat = VectorFormat.BINARY
"""
This constant is used to represent the storage format of VECTOR columns using
8-bit unsigned integers.
"""

VECTOR_FORMAT_FLOAT32: VectorFormat = VectorFormat.FLOAT32
"""
This constant is used to represent the storage format of VECTOR columns using
32-bit floating point numbers.
"""

VECTOR_FORMAT_FLOAT64: VectorFormat = VectorFormat.FLOAT64
"""
This constant is used to represent the storage format of VECTOR columns using
64-bit floating point numbers.
"""

VECTOR_FORMAT_INT8: VectorFormat = VectorFormat.INT8
"""
This constant is used to represent the storage format of VECTOR columns using
8-bit signed integers.
"""


from .connection import (  # noqa: E402
    AsyncConnection as AsyncConnection,
    connect as connect,
    connect_async as connect_async,
    Connection as Connection,
)

from .cursor import (  # noqa: E402
    AsyncCursor as AsyncCursor,
    Cursor as Cursor,
)

from .pool import (  # noqa: E402
    AsyncConnectionPool as AsyncConnectionPool,
    ConnectionPool as ConnectionPool,
    create_pool as create_pool,
    create_pool_async as create_pool_async,
    get_pool as get_pool,
)

from .subscr import (  # noqa: E402
    Subscription as Subscription,
    Message as Message,
    MessageQuery as MessageQuery,
    MessageRow as MessageRow,
    MessageTable as MessageTable,
)

from .aq import (  # noqa: E402
    Queue as Queue,
    AsyncQueue as AsyncQueue,
    DeqOptions as DeqOptions,
    EnqOptions as EnqOptions,
    MessageProperties as MessageProperties,
)

from .connect_params import ConnectParams as ConnectParams  # noqa: E402

from .pool_params import PoolParams as PoolParams  # noqa: E402

from . import builtin_hooks  # noqa: E402

IntervalYM = collections.namedtuple("IntervalYM", ["years", "months"])


class JsonId(bytes):
    pass


# initialize implementations
package = sys.modules[__name__]
base_impl.init_base_impl(package)
thick_impl.init_thick_impl(package)
thin_impl.init_thin_impl(package)
del package

# remove unnecessary symbols
del (
    aq,  # noqa
    base_impl,  # noqa
    builtin_hooks,  # noqa
    connect_params,  # noqa
    connection,  # noqa
    constants,  # noqa
    constructors,  # noqa
    cursor,  # noqa
    dbobject,  # noqa
    driver_mode,  # noqa
    dsn,  # noqa
    errors,  # noqa
    exceptions,  # noqa
    fetch_info,  # noqa
    future,  # noqa
    lob,  # noqa
    pipeline,  # noqa
    pool,  # noqa
    pool_params,  # noqa
    sparse_vector,  # noqa
    soda,  # noqa
    subscr,  # noqa
    sys,  # noqa
    thick_impl,  # noqa
    thin_impl,  # noqa
    utils,  # noqa
    var,  # noqa
    warnings,  # noqa
)

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

# aliases for authentication modes (for backwards compatibility)
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
