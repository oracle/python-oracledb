# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2026, Oracle and/or its affiliates.
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

"""
1000 - Module for testing top-level module methods
"""

import datetime
import threading

import oracledb
import pytest


def test_1000():
    "1000 - test DateFromTicks()"
    today = datetime.datetime.today()
    timestamp = today.timestamp()
    date = oracledb.DateFromTicks(int(timestamp))
    assert date == today.date()


def test_1001():
    "1001 - test management of __future__ object"
    assert oracledb.__future__.dummy is None
    oracledb.__future__.dummy = "Unimportant"
    assert oracledb.__future__.dummy is None


def test_1002():
    "1002 - test TimestampFromTicks()"
    timestamp = datetime.datetime.today().timestamp()
    today = datetime.datetime.fromtimestamp(timestamp)
    date = oracledb.TimestampFromTicks(timestamp)
    assert date == today


def test_1003(test_env):
    "1003 - test unsupported time functions"
    with test_env.assert_raises_full_code("DPY-3000"):
        oracledb.Time(12, 0, 0)
    with test_env.assert_raises_full_code("DPY-3000"):
        oracledb.TimeFromTicks(100)


def test_1004():
    "1004 - test makedsn() with valid arguments"
    for name, value in [
        ("SID", "sid_1004"),
        ("SERVICE_NAME", "my_service_1004"),
    ]:
        host = "host_1004"
        port = 1004
        region = "US WEST"
        sharding_key = "ShardKey"
        super_sharding_key = "SuperShardKey"
        args = (
            host,
            port,
            value if name == "SID" else None,
            value if name == "SERVICE_NAME" else None,
            region,
            sharding_key,
            super_sharding_key,
        )
        result = oracledb.makedsn(*args)
        expected_value = (
            f"(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={host})"
            f"(PORT={port}))(CONNECT_DATA=({name}={value})"
            f"(REGION={region})(SHARDING_KEY={sharding_key})"
            f"(SUPER_SHARDING_KEY={super_sharding_key})))"
        )
        assert result == expected_value


def test_1005(test_env):
    "1005 - test makedsn() with invalid arguments"
    with test_env.assert_raises_full_code("DPY-2020"):
        oracledb.makedsn(host="(invalid)", port=1521)
    with test_env.assert_raises_full_code("DPY-2020"):
        oracledb.makedsn(host="host", port=1521, sid="(invalid)")
    with test_env.assert_raises_full_code("DPY-2020"):
        oracledb.makedsn(host="host", port=1521, service_name="(invalid)")
    with test_env.assert_raises_full_code("DPY-2020"):
        oracledb.makedsn(host="host", port=1521, region="(invalid)")
    with test_env.assert_raises_full_code("DPY-2020"):
        oracledb.makedsn(host="host", port=1521, sharding_key="(invalid)")
    with test_env.assert_raises_full_code("DPY-2020"):
        oracledb.makedsn(
            host="host", port=1521, super_sharding_key="(invalid)"
        )


def test_1006():
    "1006 - test aliases match"

    # database type aliases
    assert oracledb.BFILE is oracledb.DB_TYPE_BFILE
    assert oracledb.BLOB is oracledb.DB_TYPE_BLOB
    assert oracledb.BOOLEAN is oracledb.DB_TYPE_BOOLEAN
    assert oracledb.CLOB is oracledb.DB_TYPE_CLOB
    assert oracledb.CURSOR is oracledb.DB_TYPE_CURSOR
    assert oracledb.FIXED_CHAR is oracledb.DB_TYPE_CHAR
    assert oracledb.FIXED_NCHAR is oracledb.DB_TYPE_NCHAR
    assert oracledb.INTERVAL is oracledb.DB_TYPE_INTERVAL_DS
    assert oracledb.LONG_BINARY is oracledb.DB_TYPE_LONG_RAW
    assert oracledb.LONG_STRING is oracledb.DB_TYPE_LONG
    assert oracledb.NATIVE_INT is oracledb.DB_TYPE_BINARY_INTEGER
    assert oracledb.NATIVE_FLOAT is oracledb.DB_TYPE_BINARY_DOUBLE
    assert oracledb.NCHAR is oracledb.DB_TYPE_NVARCHAR
    assert oracledb.NCLOB is oracledb.DB_TYPE_NCLOB
    assert oracledb.OBJECT is oracledb.DB_TYPE_OBJECT
    assert oracledb.TIMESTAMP is oracledb.DB_TYPE_TIMESTAMP

    # type aliases
    assert oracledb.ObjectType is oracledb.DbObjectType
    assert oracledb.Object is oracledb.DbObject
    assert oracledb.SessionPool is oracledb.ConnectionPool

    # authentication mode aliases
    assert oracledb.DEFAULT_AUTH is oracledb.AUTH_MODE_DEFAULT
    assert oracledb.SYSASM is oracledb.AUTH_MODE_SYSASM
    assert oracledb.SYSBKP is oracledb.AUTH_MODE_SYSBKP
    assert oracledb.SYSDBA is oracledb.AUTH_MODE_SYSDBA
    assert oracledb.SYSDGD is oracledb.AUTH_MODE_SYSDGD
    assert oracledb.SYSKMT is oracledb.AUTH_MODE_SYSKMT
    assert oracledb.SYSOPER is oracledb.AUTH_MODE_SYSOPER
    assert oracledb.SYSRAC is oracledb.AUTH_MODE_SYSRAC
    assert oracledb.PRELIM_AUTH is oracledb.AUTH_MODE_PRELIM

    # pool "get" mode aliases
    assert oracledb.SPOOL_ATTRVAL_WAIT is oracledb.POOL_GETMODE_WAIT
    assert oracledb.SPOOL_ATTRVAL_NOWAIT is oracledb.POOL_GETMODE_NOWAIT
    assert oracledb.SPOOL_ATTRVAL_FORCEGET is oracledb.POOL_GETMODE_FORCEGET
    assert oracledb.SPOOL_ATTRVAL_TIMEDWAIT is oracledb.POOL_GETMODE_TIMEDWAIT

    # purity aliases
    assert oracledb.ATTR_PURITY_DEFAULT is oracledb.PURITY_DEFAULT
    assert oracledb.ATTR_PURITY_NEW is oracledb.PURITY_NEW
    assert oracledb.ATTR_PURITY_SELF is oracledb.PURITY_SELF

    # other aliases
    assert oracledb.SUBSCR_PROTO_OCI is oracledb.SUBSCR_PROTO_CALLBACK
    assert oracledb.version is oracledb.__version__


def test_1007(test_env, skip_unless_thin_mode):
    "1007 - test clientversion() fails without init_oracle_client()"
    with test_env.assert_raises_full_code("DPY-2021"):
        oracledb.clientversion()


def test_1008():
    "1008 - test enumeration aliases match"

    # authentication mode enumeration
    assert oracledb.AUTH_MODE_DEFAULT is oracledb.AuthMode.DEFAULT
    assert oracledb.AUTH_MODE_PRELIM is oracledb.AuthMode.PRELIM
    assert oracledb.AUTH_MODE_SYSASM is oracledb.AuthMode.SYSASM
    assert oracledb.AUTH_MODE_SYSBKP is oracledb.AuthMode.SYSBKP
    assert oracledb.AUTH_MODE_SYSDBA is oracledb.AuthMode.SYSDBA
    assert oracledb.AUTH_MODE_SYSDGD is oracledb.AuthMode.SYSDGD
    assert oracledb.AUTH_MODE_SYSKMT is oracledb.AuthMode.SYSKMT
    assert oracledb.AUTH_MODE_SYSOPER is oracledb.AuthMode.SYSOPER
    assert oracledb.AUTH_MODE_SYSRAC is oracledb.AuthMode.SYSRAC

    # batch operation type enumeration
    assert (
        oracledb.PIPELINE_OP_TYPE_CALL_FUNC
        is oracledb.PipelineOpType.CALL_FUNC
    )
    assert (
        oracledb.PIPELINE_OP_TYPE_CALL_PROC
        is oracledb.PipelineOpType.CALL_PROC
    )
    assert oracledb.PIPELINE_OP_TYPE_COMMIT is oracledb.PipelineOpType.COMMIT
    assert oracledb.PIPELINE_OP_TYPE_EXECUTE is oracledb.PipelineOpType.EXECUTE
    assert (
        oracledb.PIPELINE_OP_TYPE_EXECUTE_MANY
        is oracledb.PipelineOpType.EXECUTE_MANY
    )
    assert (
        oracledb.PIPELINE_OP_TYPE_FETCH_ALL
        is oracledb.PipelineOpType.FETCH_ALL
    )
    assert (
        oracledb.PIPELINE_OP_TYPE_FETCH_MANY
        is oracledb.PipelineOpType.FETCH_MANY
    )
    assert (
        oracledb.PIPELINE_OP_TYPE_FETCH_ONE
        is oracledb.PipelineOpType.FETCH_ONE
    )

    # pool "get" mode enumeration
    assert oracledb.POOL_GETMODE_FORCEGET is oracledb.PoolGetMode.FORCEGET
    assert oracledb.POOL_GETMODE_WAIT is oracledb.PoolGetMode.WAIT
    assert oracledb.POOL_GETMODE_NOWAIT is oracledb.PoolGetMode.NOWAIT
    assert oracledb.POOL_GETMODE_TIMEDWAIT is oracledb.PoolGetMode.TIMEDWAIT

    # purity enumeration
    assert oracledb.PURITY_DEFAULT is oracledb.Purity.DEFAULT
    assert oracledb.PURITY_NEW is oracledb.Purity.NEW
    assert oracledb.PURITY_SELF is oracledb.Purity.SELF

    # vector format enumeration
    assert oracledb.VECTOR_FORMAT_BINARY is oracledb.VectorFormat.BINARY
    assert oracledb.VECTOR_FORMAT_FLOAT32 is oracledb.VectorFormat.FLOAT32
    assert oracledb.VECTOR_FORMAT_FLOAT64 is oracledb.VectorFormat.FLOAT64
    assert oracledb.VECTOR_FORMAT_INT8 is oracledb.VectorFormat.INT8


def test_1009(test_env, conn):
    "1009 - test enable_thin_mode()"
    if test_env.use_thick_mode:
        with test_env.assert_raises_full_code("DPY-2053"):
            oracledb.enable_thin_mode()
    else:
        oracledb.enable_thin_mode()
        with test_env.assert_raises_full_code("DPY-2019"):
            oracledb.init_oracle_client()


def test_1010():
    "1010 - test creation and updating of secret values"
    secret = "secret_1010"
    value = oracledb.SecretValue(secret)
    assert value.value == secret
    another_secret = "secret_1010_modified"
    value.value = another_secret
    assert value.value == another_secret


def test_1011():
    "1011 - test secret values that expire are not returned"
    secret = "secret_1011"
    expires = datetime.datetime.now(
        datetime.timezone.utc
    ) - datetime.timedelta(1)
    value = oracledb.SecretValue(secret, expires=expires)
    assert value.value is None


def test_1012():
    "1012 - test secret values require a timezone-aware date"
    secret = "secret_1012"
    expires = datetime.datetime.now() - datetime.timedelta(1)
    with pytest.raises(ValueError):
        oracledb.SecretValue(secret, expires=expires)


def test_1013():
    "1013 - test secret values that have not expired are returned"
    secret = "secret_1013"
    expires = datetime.datetime.now(
        datetime.timezone.utc
    ) + datetime.timedelta(10)
    value = oracledb.SecretValue(secret, expires=expires)
    assert value.value == secret


def test_1014():
    "1014 - test storing secrets in the global cache"
    key = (1014, "key")
    secret = "secret_1014"
    assert oracledb.get_secret(key) is None
    oracledb.save_secret(key, secret)
    assert oracledb.get_secret(key).value == secret


def test_1015():
    "1015 - test storing secrets in the thread local cache"
    key = (1015, "key")
    main_secret = "secret_1015"

    def thread_fn():
        assert oracledb.get_secret(key, thread_local=True) is None
        thread_secret = "secret_1015_thread"
        oracledb.save_secret(key, thread_secret, thread_local=True)
        secret_value = oracledb.get_secret(key, thread_local=True)
        assert secret_value.value == thread_secret

    assert oracledb.get_secret(key, thread_local=True) is None
    oracledb.save_secret(key, main_secret, thread_local=True)
    secret_value = oracledb.get_secret(key, thread_local=True)
    assert secret_value.value == main_secret

    thread = threading.Thread(target=thread_fn)
    thread.start()
    thread.join()
    secret_value = oracledb.get_secret(key, thread_local=True)
    assert secret_value.value == main_secret


def test_1016():
    "1016 - test secrets that have expired are not returned"
    key = (1016, "key")
    secret = "secret_1016"
    expires = datetime.datetime.now(
        datetime.timezone.utc
    ) - datetime.timedelta(1)
    oracledb.save_secret(key, secret, expires=expires)
    assert oracledb.get_secret(key) is None


def test_1017():
    "1017 - test secrets that have not expired are returned correctly"
    key = (1017, "key")
    secret = "secret_1017"
    expires = datetime.datetime.now(
        datetime.timezone.utc
    ) + datetime.timedelta(10)
    oracledb.save_secret(key, secret, expires=expires)
    assert oracledb.get_secret(key).value == secret


def test_1018():
    "1018 - test storing a secret value of None"
    key = (1018, "key")
    assert oracledb.save_secret(key, None) is None
    assert oracledb.get_secret(key) is None
    secret = "secret_1018"
    oracledb.save_secret(key, secret)
    assert oracledb.get_secret(key).value == secret
    oracledb.save_secret(key, None)
    assert oracledb.get_secret(key) is None


def test_1019():
    "1019 - test storing a secret value containing bytes"
    key = (1019, "key")
    secret = b"secret_1019"
    oracledb.save_secret(key, secret)
    assert oracledb.get_secret(key).value_bytes == secret
