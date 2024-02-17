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
        format_string = (
            "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)"
            "(HOST=%s)(PORT=%d))(CONNECT_DATA=(SID=%s)))"
        )
        args = ("hostname", 1521, "TEST")
        result = oracledb.makedsn(*args)
        self.assertEqual(result, format_string % args)

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


if __name__ == "__main__":
    test_env.run_test_cases()
