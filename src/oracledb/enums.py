# -----------------------------------------------------------------------------
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
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
# enums.py
#
# Contains the enumerations of various constants used throughout the package.
# -----------------------------------------------------------------------------

import enum

from . import base_impl


class AuthMode(enum.IntFlag):
    DEFAULT = base_impl.AUTH_MODE_DEFAULT
    PRELIM = base_impl.AUTH_MODE_PRELIM
    SYSASM = base_impl.AUTH_MODE_SYSASM
    SYSBKP = base_impl.AUTH_MODE_SYSBKP
    SYSDBA = base_impl.AUTH_MODE_SYSDBA
    SYSDGD = base_impl.AUTH_MODE_SYSDGD
    SYSKMT = base_impl.AUTH_MODE_SYSKMT
    SYSOPER = base_impl.AUTH_MODE_SYSOPER
    SYSRAC = base_impl.AUTH_MODE_SYSRAC


class PipelineOpType(enum.IntFlag):
    CALL_FUNC = base_impl.PIPELINE_OP_TYPE_CALL_FUNC
    CALL_PROC = base_impl.PIPELINE_OP_TYPE_CALL_PROC
    COMMIT = base_impl.PIPELINE_OP_TYPE_COMMIT
    EXECUTE = base_impl.PIPELINE_OP_TYPE_EXECUTE
    EXECUTE_MANY = base_impl.PIPELINE_OP_TYPE_EXECUTE_MANY
    FETCH_ALL = base_impl.PIPELINE_OP_TYPE_FETCH_ALL
    FETCH_MANY = base_impl.PIPELINE_OP_TYPE_FETCH_MANY
    FETCH_ONE = base_impl.PIPELINE_OP_TYPE_FETCH_ONE


class PoolGetMode(enum.IntEnum):
    FORCEGET = base_impl.POOL_GETMODE_FORCEGET
    NOWAIT = base_impl.POOL_GETMODE_NOWAIT
    TIMEDWAIT = base_impl.POOL_GETMODE_TIMEDWAIT
    WAIT = base_impl.POOL_GETMODE_WAIT


class Purity(enum.IntEnum):
    DEFAULT = base_impl.PURITY_DEFAULT
    NEW = base_impl.PURITY_NEW
    SELF = base_impl.PURITY_SELF


class VectorFormat(enum.IntEnum):
    BINARY = base_impl.VECTOR_FORMAT_BINARY
    FLOAT32 = base_impl.VECTOR_FORMAT_FLOAT32
    FLOAT64 = base_impl.VECTOR_FORMAT_FLOAT64
    INT8 = base_impl.VECTOR_FORMAT_INT8
