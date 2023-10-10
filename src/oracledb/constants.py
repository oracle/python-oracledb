# -----------------------------------------------------------------------------
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
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# constants.py
#
# Contains the constants defined by the package.
# -----------------------------------------------------------------------------

# mandated DB API constants
apilevel = "2.0"
threadsafety = 2
paramstyle = "named"

# authentication modes
AUTH_MODE_DEFAULT = 0
AUTH_MODE_PRELIM = 0x00000008
AUTH_MODE_SYSASM = 0x00008000
AUTH_MODE_SYSBKP = 0x00020000
AUTH_MODE_SYSDBA = 0x00000002
AUTH_MODE_SYSDGD = 0x00040000
AUTH_MODE_SYSKMT = 0x00080000
AUTH_MODE_SYSOPER = 0x00000004
AUTH_MODE_SYSRAC = 0x00100000

# pool "get" modes
POOL_GETMODE_WAIT = 0
POOL_GETMODE_NOWAIT = 1
POOL_GETMODE_FORCEGET = 2
POOL_GETMODE_TIMEDWAIT = 3

# purity values
PURITY_DEFAULT = 0
PURITY_NEW = 1
PURITY_SELF = 2

# AQ delivery modes
MSG_BUFFERED = 2
MSG_PERSISTENT = 1
MSG_PERSISTENT_OR_BUFFERED = 3

# AQ dequeue modes
DEQ_BROWSE = 1
DEQ_LOCKED = 2
DEQ_REMOVE = 3
DEQ_REMOVE_NODATA = 4

# AQ dequeue navigation modes
DEQ_FIRST_MSG = 1
DEQ_NEXT_MSG = 3
DEQ_NEXT_TRANSACTION = 2

# AQ dequeue visibility modes
DEQ_IMMEDIATE = 1
DEQ_ON_COMMIT = 2

# AQ dequeue wait modes
DEQ_NO_WAIT = 0
DEQ_WAIT_FOREVER = 2**32 - 1

# AQ enqueue visibility modes
ENQ_IMMEDIATE = 1
ENQ_ON_COMMIT = 2

# AQ message states
MSG_EXPIRED = 3
MSG_PROCESSED = 2
MSG_READY = 0
MSG_WAITING = 1

# AQ other constants
MSG_NO_DELAY = 0
MSG_NO_EXPIRATION = -1

# shutdown modes
DBSHUTDOWN_ABORT = 4
DBSHUTDOWN_FINAL = 5
DBSHUTDOWN_IMMEDIATE = 3
DBSHUTDOWN_TRANSACTIONAL = 1
DBSHUTDOWN_TRANSACTIONAL_LOCAL = 2

# subscription grouping classes
SUBSCR_GROUPING_CLASS_NONE = 0
SUBSCR_GROUPING_CLASS_TIME = 1

# subscription grouping types
SUBSCR_GROUPING_TYPE_SUMMARY = 1
SUBSCR_GROUPING_TYPE_LAST = 2

# subscription namespaces
SUBSCR_NAMESPACE_AQ = 1
SUBSCR_NAMESPACE_DBCHANGE = 2

# subscription protocols
SUBSCR_PROTO_HTTP = 3
SUBSCR_PROTO_MAIL = 1
SUBSCR_PROTO_CALLBACK = 0
SUBSCR_PROTO_SERVER = 2

# subscription quality of service
SUBSCR_QOS_BEST_EFFORT = 0x10
SUBSCR_QOS_DEFAULT = 0
SUBSCR_QOS_DEREG_NFY = 0x02
SUBSCR_QOS_QUERY = 0x08
SUBSCR_QOS_RELIABLE = 0x01
SUBSCR_QOS_ROWIDS = 0x04

# event types
EVENT_AQ = 100
EVENT_DEREG = 5
EVENT_NONE = 0
EVENT_OBJCHANGE = 6
EVENT_QUERYCHANGE = 7
EVENT_SHUTDOWN = 2
EVENT_SHUTDOWN_ANY = 3
EVENT_STARTUP = 1

# operation codes
OPCODE_ALLOPS = 0
OPCODE_ALLROWS = 0x01
OPCODE_ALTER = 0x10
OPCODE_DELETE = 0x08
OPCODE_DROP = 0x20
OPCODE_INSERT = 0x02
OPCODE_UPDATE = 0x04

# flags for tpc_begin()
TPC_BEGIN_JOIN = 0x00000002
TPC_BEGIN_NEW = 0x00000001
TPC_BEGIN_PROMOTE = 0x00000008
TPC_BEGIN_RESUME = 0x00000004

# flags for tpc_end()
TPC_END_NORMAL = 0
TPC_END_SUSPEND = 0x00100000

# basic configuration constants
DRIVER_NAME = "python-oracledb"
INSTALLATION_URL = (
    "https://python-oracledb.readthedocs.io/en/"
    "latest/user_guide/initialization.html"
)
ENCODING = "UTF-8"
