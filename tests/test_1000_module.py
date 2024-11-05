# -----------------------------------------------------------------------------
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
# -----------------------------------------------------------------------------

"""
1000 - Module for testing top-level module methods
"""

import datetime
import unittest

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    requires_connection = False

    def test_1000(self):
        "1000 - test DateFromTicks()"
        today = datetime.datetime.today()
        timestamp = today.timestamp()
        date = oracledb.DateFromTicks(int(timestamp))
        self.assertEqual(date, today.date())

    def test_1001(self):
        "1001 - test management of __future__ object"
        self.assertIsNone(oracledb.__future__.dummy)
        oracledb.__future__.dummy = "Unimportant"
        self.assertIsNone(oracledb.__future__.dummy)

    def test_1002(self):
        "1002 - test TimestampFromTicks()"
        timestamp = datetime.datetime.today().timestamp()
        today = datetime.datetime.fromtimestamp(timestamp)
        date = oracledb.TimestampFromTicks(timestamp)
        self.assertEqual(date, today)

    def test_1003(self):
        "1003 - test unsupported time functions"
        with self.assertRaisesFullCode("DPY-3000"):
            oracledb.Time(12, 0, 0)
        with self.assertRaisesFullCode("DPY-3000"):
            oracledb.TimeFromTicks(100)

    def test_1004(self):
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
            self.assertEqual(result, expected_value)

    def test_1005(self):
        "1005 - test makedsn() with invalid arguments"
        with self.assertRaisesFullCode("DPY-2020"):
            oracledb.makedsn(host="(invalid)", port=1521)
        with self.assertRaisesFullCode("DPY-2020"):
            oracledb.makedsn(host="host", port=1521, sid="(invalid)")
        with self.assertRaisesFullCode("DPY-2020"):
            oracledb.makedsn(host="host", port=1521, service_name="(invalid)")
        with self.assertRaisesFullCode("DPY-2020"):
            oracledb.makedsn(host="host", port=1521, region="(invalid)")
        with self.assertRaisesFullCode("DPY-2020"):
            oracledb.makedsn(host="host", port=1521, sharding_key="(invalid)")
        with self.assertRaisesFullCode("DPY-2020"):
            oracledb.makedsn(
                host="host", port=1521, super_sharding_key="(invalid)"
            )

    def test_1006(self):
        "1006 - test aliases match"

        # database type aliases
        self.assertIs(oracledb.BFILE, oracledb.DB_TYPE_BFILE)
        self.assertIs(oracledb.BLOB, oracledb.DB_TYPE_BLOB)
        self.assertIs(oracledb.BOOLEAN, oracledb.DB_TYPE_BOOLEAN)
        self.assertIs(oracledb.CLOB, oracledb.DB_TYPE_CLOB)
        self.assertIs(oracledb.CURSOR, oracledb.DB_TYPE_CURSOR)
        self.assertIs(oracledb.FIXED_CHAR, oracledb.DB_TYPE_CHAR)
        self.assertIs(oracledb.FIXED_NCHAR, oracledb.DB_TYPE_NCHAR)
        self.assertIs(oracledb.INTERVAL, oracledb.DB_TYPE_INTERVAL_DS)
        self.assertIs(oracledb.LONG_BINARY, oracledb.DB_TYPE_LONG_RAW)
        self.assertIs(oracledb.LONG_STRING, oracledb.DB_TYPE_LONG)
        self.assertIs(oracledb.NATIVE_INT, oracledb.DB_TYPE_BINARY_INTEGER)
        self.assertIs(oracledb.NATIVE_FLOAT, oracledb.DB_TYPE_BINARY_DOUBLE)
        self.assertIs(oracledb.NCHAR, oracledb.DB_TYPE_NVARCHAR)
        self.assertIs(oracledb.NCLOB, oracledb.DB_TYPE_NCLOB)
        self.assertIs(oracledb.OBJECT, oracledb.DB_TYPE_OBJECT)
        self.assertIs(oracledb.TIMESTAMP, oracledb.DB_TYPE_TIMESTAMP)

        # type aliases
        self.assertIs(oracledb.ObjectType, oracledb.DbObjectType)
        self.assertIs(oracledb.Object, oracledb.DbObject)
        self.assertIs(oracledb.SessionPool, oracledb.ConnectionPool)

        # authentication mode aliases
        self.assertIs(oracledb.DEFAULT_AUTH, oracledb.AUTH_MODE_DEFAULT)
        self.assertIs(oracledb.SYSASM, oracledb.AUTH_MODE_SYSASM)
        self.assertIs(oracledb.SYSBKP, oracledb.AUTH_MODE_SYSBKP)
        self.assertIs(oracledb.SYSDBA, oracledb.AUTH_MODE_SYSDBA)
        self.assertIs(oracledb.SYSDGD, oracledb.AUTH_MODE_SYSDGD)
        self.assertIs(oracledb.SYSKMT, oracledb.AUTH_MODE_SYSKMT)
        self.assertIs(oracledb.SYSOPER, oracledb.AUTH_MODE_SYSOPER)
        self.assertIs(oracledb.SYSRAC, oracledb.AUTH_MODE_SYSRAC)
        self.assertIs(oracledb.PRELIM_AUTH, oracledb.AUTH_MODE_PRELIM)

        # pool "get" mode aliases
        self.assertIs(oracledb.SPOOL_ATTRVAL_WAIT, oracledb.POOL_GETMODE_WAIT)
        self.assertIs(
            oracledb.SPOOL_ATTRVAL_NOWAIT, oracledb.POOL_GETMODE_NOWAIT
        )
        self.assertIs(
            oracledb.SPOOL_ATTRVAL_FORCEGET, oracledb.POOL_GETMODE_FORCEGET
        )
        self.assertIs(
            oracledb.SPOOL_ATTRVAL_TIMEDWAIT, oracledb.POOL_GETMODE_TIMEDWAIT
        )

        # purity aliases
        self.assertIs(oracledb.ATTR_PURITY_DEFAULT, oracledb.PURITY_DEFAULT)
        self.assertIs(oracledb.ATTR_PURITY_NEW, oracledb.PURITY_NEW)
        self.assertIs(oracledb.ATTR_PURITY_SELF, oracledb.PURITY_SELF)

        # other aliases
        self.assertIs(
            oracledb.SUBSCR_PROTO_OCI, oracledb.SUBSCR_PROTO_CALLBACK
        )
        self.assertIs(oracledb.version, oracledb.__version__)

    @unittest.skipUnless(test_env.get_is_thin(), "not relevant for thick mode")
    def test_1007(self):
        "1007 - test clientversion() fails without init_oracle_client()"
        with self.assertRaisesFullCode("DPY-2021"):
            oracledb.clientversion()

    def test_1008(self):
        "1008 - test enumeration aliases match"

        # authentication mode enumeration
        self.assertIs(oracledb.AUTH_MODE_DEFAULT, oracledb.AuthMode.DEFAULT)
        self.assertIs(oracledb.AUTH_MODE_PRELIM, oracledb.AuthMode.PRELIM)
        self.assertIs(oracledb.AUTH_MODE_SYSASM, oracledb.AuthMode.SYSASM)
        self.assertIs(oracledb.AUTH_MODE_SYSBKP, oracledb.AuthMode.SYSBKP)
        self.assertIs(oracledb.AUTH_MODE_SYSDBA, oracledb.AuthMode.SYSDBA)
        self.assertIs(oracledb.AUTH_MODE_SYSDGD, oracledb.AuthMode.SYSDGD)
        self.assertIs(oracledb.AUTH_MODE_SYSKMT, oracledb.AuthMode.SYSKMT)
        self.assertIs(oracledb.AUTH_MODE_SYSOPER, oracledb.AuthMode.SYSOPER)
        self.assertIs(oracledb.AUTH_MODE_SYSRAC, oracledb.AuthMode.SYSRAC)

        # batch operation type enumeration
        self.assertIs(
            oracledb.PIPELINE_OP_TYPE_CALL_FUNC,
            oracledb.PipelineOpType.CALL_FUNC,
        )
        self.assertIs(
            oracledb.PIPELINE_OP_TYPE_CALL_PROC,
            oracledb.PipelineOpType.CALL_PROC,
        )
        self.assertIs(
            oracledb.PIPELINE_OP_TYPE_COMMIT, oracledb.PipelineOpType.COMMIT
        )
        self.assertIs(
            oracledb.PIPELINE_OP_TYPE_EXECUTE, oracledb.PipelineOpType.EXECUTE
        )
        self.assertIs(
            oracledb.PIPELINE_OP_TYPE_EXECUTE_MANY,
            oracledb.PipelineOpType.EXECUTE_MANY,
        )
        self.assertIs(
            oracledb.PIPELINE_OP_TYPE_FETCH_ALL,
            oracledb.PipelineOpType.FETCH_ALL,
        )
        self.assertIs(
            oracledb.PIPELINE_OP_TYPE_FETCH_MANY,
            oracledb.PipelineOpType.FETCH_MANY,
        )
        self.assertIs(
            oracledb.PIPELINE_OP_TYPE_FETCH_ONE,
            oracledb.PipelineOpType.FETCH_ONE,
        )

        # pool "get" mode enumeration
        self.assertIs(
            oracledb.POOL_GETMODE_FORCEGET, oracledb.PoolGetMode.FORCEGET
        )
        self.assertIs(oracledb.POOL_GETMODE_WAIT, oracledb.PoolGetMode.WAIT)
        self.assertIs(
            oracledb.POOL_GETMODE_NOWAIT, oracledb.PoolGetMode.NOWAIT
        )
        self.assertIs(
            oracledb.POOL_GETMODE_TIMEDWAIT, oracledb.PoolGetMode.TIMEDWAIT
        )

        # purity enumeration
        self.assertIs(oracledb.PURITY_DEFAULT, oracledb.Purity.DEFAULT)
        self.assertIs(oracledb.PURITY_NEW, oracledb.Purity.NEW)
        self.assertIs(oracledb.PURITY_SELF, oracledb.Purity.SELF)

        # vector format enumeration
        self.assertIs(
            oracledb.VECTOR_FORMAT_BINARY, oracledb.VectorFormat.BINARY
        )
        self.assertIs(
            oracledb.VECTOR_FORMAT_FLOAT32, oracledb.VectorFormat.FLOAT32
        )
        self.assertIs(
            oracledb.VECTOR_FORMAT_FLOAT64, oracledb.VectorFormat.FLOAT64
        )
        self.assertIs(oracledb.VECTOR_FORMAT_INT8, oracledb.VectorFormat.INT8)

    def test_1009(self):
        "1009 - test enable_thin_mode()"
        if test_env.get_is_thin():
            oracledb.enable_thin_mode()
            with self.assertRaisesFullCode("DPY-2019"):
                oracledb.init_oracle_client()
        else:
            with self.assertRaisesFullCode("DPY-2053"):
                oracledb.enable_thin_mode()


if __name__ == "__main__":
    test_env.run_test_cases()
