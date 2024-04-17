# -----------------------------------------------------------------------------
# Copyright (c) 2023, 2024, Oracle and/or its affiliates.
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
6600 - Module for testing oracledb.defaults
"""

import decimal
import tempfile

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    def test_6600(self):
        "6600 - test setting defaults.arraysize"
        with test_env.DefaultsContextManager("arraysize", 50):
            conn = test_env.get_connection()
            cursor = conn.cursor()
            self.assertEqual(cursor.arraysize, oracledb.defaults.arraysize)

    def test_6601(self):
        "6601 - test getting decimals with defaults.fetch_decimals=True"
        with test_env.DefaultsContextManager("fetch_decimals", True):
            self.cursor.execute("select 9 from dual")
            (result,) = self.cursor.fetchone()
            self.assertIsInstance(result, decimal.Decimal)

    def test_6602(self):
        "6602 - test getting string lob with defaults.fetch_lobs=False"
        with test_env.DefaultsContextManager("fetch_lobs", False):
            self.cursor.execute("select to_clob('Hello world') from dual")
            (result,) = self.cursor.fetchone()
            self.assertIsInstance(result, str)

    def test_6603(self):
        "6603 - test setting defaults.prefetchrows"
        with test_env.DefaultsContextManager("prefetchrows", 20):
            conn = test_env.get_connection()
            cursor = conn.cursor()
            self.assertEqual(
                cursor.prefetchrows, oracledb.defaults.prefetchrows
            )

    def test_6604(self):
        "6604 - test setting defaults.stmtcachesize (pool)"
        with test_env.DefaultsContextManager("stmtcachesize", 40):
            pool = test_env.get_pool()
            self.assertEqual(
                pool.stmtcachesize, oracledb.defaults.stmtcachesize
            )
            conn = pool.acquire()
            self.assertEqual(
                conn.stmtcachesize, oracledb.defaults.stmtcachesize
            )

    def test_6605(self):
        "6605 - test setting defaults.stmtcachesize (standalone connection)"
        with test_env.DefaultsContextManager("stmtcachesize", 50):
            conn = test_env.get_connection()
            self.assertEqual(
                conn.stmtcachesize, oracledb.defaults.stmtcachesize
            )

    def test_6606(self):
        "6606 - fetch_lobs does not affect LOBS returned as OUT binds"
        with test_env.DefaultsContextManager("fetch_lobs", False):
            var = self.cursor.var(oracledb.DB_TYPE_CLOB)
            self.cursor.execute(
                "begin :value := to_clob('test clob'); end;",
                value=var,
            )
            self.assertIsInstance(var.getvalue(), oracledb.LOB)

    def test_6607(self):
        "6607 - test setting defaults.config_dir"
        with tempfile.TemporaryDirectory() as temp_dir:
            with test_env.DefaultsContextManager("config_dir", temp_dir):
                self.assertEqual(oracledb.defaults.config_dir, temp_dir)
                params = oracledb.ConnectParams()
                self.assertEqual(params.config_dir, temp_dir)

    def test_6608(self):
        "6608 - test setting defaults.stmtcachesize (ConnectParams)"
        with test_env.DefaultsContextManager("stmtcachesize", 50):
            params = oracledb.ConnectParams()
            self.assertEqual(
                params.stmtcachesize, oracledb.defaults.stmtcachesize
            )


if __name__ == "__main__":
    test_env.run_test_cases()
