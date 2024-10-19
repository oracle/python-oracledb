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
import os
import tempfile

import oracledb
import test_env
import unittest


class TestCase(test_env.BaseTestCase):
    def __verify_network_name_attr(self, name):
        """
        Verify that a default attribute is handled properly in both valid
        and invalid cases.
        """
        for value, ok in [
            ("valid_value", True),
            ("'contains_quotes'", False),
            ('"contains_double_quotes"', False),
            ("contains_opening_paren (", False),
            ("contains_closing_paren )", False),
            ("contains_equals =", False),
            ("contains_trailing_slash\\", False),
        ]:
            args = {}
            args[name] = value
            if ok:
                with test_env.DefaultsContextManager(name, value):
                    cp = oracledb.ConnectParams(**args)
                    self.assertEqual(getattr(cp, name), value)
            else:
                with self.assertRaisesFullCode("DPY-3029"):
                    with test_env.DefaultsContextManager(name, value):
                        pass

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
        new_stmtcachesize = 15
        with test_env.DefaultsContextManager("stmtcachesize", 40):
            pool = test_env.get_pool()
            self.assertEqual(
                pool.stmtcachesize, oracledb.defaults.stmtcachesize
            )
            conn = pool.acquire()
            self.assertEqual(
                conn.stmtcachesize, oracledb.defaults.stmtcachesize
            )
            pool = test_env.get_pool(stmtcachesize=new_stmtcachesize)
            self.assertEqual(pool.stmtcachesize, new_stmtcachesize)
            conn = pool.acquire()
            self.assertEqual(conn.stmtcachesize, new_stmtcachesize)

    def test_6605(self):
        "6605 - test setting defaults.stmtcachesize (standalone connection)"
        new_stmtcachesize = 25
        with test_env.DefaultsContextManager("stmtcachesize", 50):
            conn = test_env.get_connection()
            self.assertEqual(
                conn.stmtcachesize, oracledb.defaults.stmtcachesize
            )
            conn = test_env.get_connection(stmtcachesize=new_stmtcachesize)
            self.assertEqual(conn.stmtcachesize, new_stmtcachesize)

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
            new_temp_dir = os.path.join(temp_dir, "subdir")
            with test_env.DefaultsContextManager("config_dir", temp_dir):
                self.assertEqual(oracledb.defaults.config_dir, temp_dir)
                params = oracledb.ConnectParams()
                self.assertEqual(params.config_dir, temp_dir)
                params = oracledb.ConnectParams(config_dir=new_temp_dir)
                self.assertEqual(params.config_dir, new_temp_dir)

    def test_6608(self):
        "6608 - test setting defaults.stmtcachesize (ConnectParams)"
        new_stmtcachesize = 35
        with test_env.DefaultsContextManager("stmtcachesize", 60):
            params = oracledb.ConnectParams()
            self.assertEqual(
                params.stmtcachesize, oracledb.defaults.stmtcachesize
            )
            params = oracledb.ConnectParams(stmtcachesize=new_stmtcachesize)
            self.assertEqual(params.stmtcachesize, new_stmtcachesize)

    def test_6609(self):
        "6609 - test defaults.stmtcachesize persists after setting it again"
        value = 50
        new_value = 29
        with test_env.DefaultsContextManager("stmtcachesize", value):
            pool = test_env.get_pool()
            pooled_conn = pool.acquire()
            params = oracledb.ConnectParams()
            standalone_conn = test_env.get_connection()
            with test_env.DefaultsContextManager("stmtcachesize", new_value):
                self.assertEqual(pool.stmtcachesize, value)
                self.assertEqual(pooled_conn.stmtcachesize, value)
                self.assertEqual(params.stmtcachesize, value)
                self.assertEqual(standalone_conn.stmtcachesize, value)
                pool = test_env.get_pool()
                pooled_conn = pool.acquire()
                params = oracledb.ConnectParams()
                standalone_conn = test_env.get_connection()
                self.assertEqual(pool.stmtcachesize, new_value)
                self.assertEqual(pooled_conn.stmtcachesize, new_value)
                self.assertEqual(params.stmtcachesize, new_value)
                self.assertEqual(standalone_conn.stmtcachesize, new_value)

    def test_6610(self):
        "6610 - test setting defaults.terminal"
        with test_env.DefaultsContextManager("terminal", "newterminal"):
            params = oracledb.ConnectParams()
            self.assertEqual(params.terminal, oracledb.defaults.terminal)

    def test_6611(self):
        "6611 - test setting defaults.driver_name"
        with test_env.DefaultsContextManager("driver_name", "newdriver"):
            params = oracledb.ConnectParams()
            self.assertEqual(params.driver_name, oracledb.defaults.driver_name)

    def test_6612(self):
        "6612 - test setting defaults.program attribute"
        self.__verify_network_name_attr("program")

    def test_6613(self):
        "6613 - test setting defaults.machine attribute"
        self.__verify_network_name_attr("machine")

    def test_6614(self):
        "6614 - test setting defaults.osuser attribute"
        self.__verify_network_name_attr("osuser")

    @unittest.skipUnless(
        test_env.get_is_thin(),
        "thick mode doesn't support program yet",
    )
    def test_6615(self):
        "6615 - test program with two pools"
        default_value = "defaultprogram"
        new_value = "newprogram"
        verify_sql = (
            "select program from v$session "
            "where sid = sys_context('userenv', 'sid')"
        )
        with test_env.DefaultsContextManager("program", default_value):

            # create pool using default value
            pool = test_env.get_pool()
            with pool.acquire() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(verify_sql)
                    (fetched_value,) = cursor.fetchone()
                    self.assertEqual(fetched_value, default_value)
            pool.close()

            # create pool using new value
            pool = test_env.get_pool(program=new_value)
            with pool.acquire() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(verify_sql)
                    (fetched_value,) = cursor.fetchone()
                    self.assertEqual(fetched_value, new_value)
            pool.close()


if __name__ == "__main__":
    test_env.run_test_cases()
