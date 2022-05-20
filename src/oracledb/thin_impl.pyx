#------------------------------------------------------------------------------
# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
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
from libc.stdint cimport UINT8_MAX, UINT16_MAX, UINT32_MAX, UINT64_MAX
from libc.string cimport memcpy, memset
from cpython cimport array

import array
import collections
import datetime
import decimal
import getpass
import hashlib
import os
import socket
import re
import secrets
import ssl
import subprocess
import sys
import threading
import time

try:
    import certifi
except ImportError:
    certifi = None
macos_certs = None

cydatetime.import_datetime()

from . import __version__ as VERSION

from . import constants, errors, exceptions
from .defaults import defaults

from .base_impl cimport get_exception_class, NUM_TYPE_FLOAT
from .base_impl cimport NUM_TYPE_INT, NUM_TYPE_DECIMAL, NUM_TYPE_STR
from .base_impl cimport BaseConnImpl, BaseCursorImpl, BaseVarImpl, DbType
from .base_impl cimport BaseLobImpl, BasePoolImpl, FetchInfo
from .base_impl cimport Address, AddressList, Description, DescriptionList
from .base_impl cimport ConnectParamsImpl, PoolParamsImpl
from .base_impl import DB_TYPE_BLOB, DB_TYPE_CLOB, DB_TYPE_NCLOB
from .lob import LOB
from .var import Var

ctypedef unsigned char char_type

include "impl/thin/constants.pxi"
include "impl/thin/utils.pyx"
include "impl/thin/crypto.pyx"
include "impl/thin/capabilities.pyx"
include "impl/thin/buffer.pyx"
include "impl/thin/network_services.pyx"
include "impl/thin/data_types.pyx"
include "impl/thin/messages.pyx"
include "impl/thin/protocol.pyx"
include "impl/thin/connection.pyx"
include "impl/thin/statement.pyx"
include "impl/thin/cursor.pyx"
include "impl/thin/var.pyx"
include "impl/thin/lob.pyx"
include "impl/thin/pool.pyx"
include "impl/thin/conversions.pyx"
