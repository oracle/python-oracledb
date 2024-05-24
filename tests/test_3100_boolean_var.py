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
3100 - Module for testing boolean variables
"""

import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_client_version() >= (12, 1), "unsupported client"
)
@unittest.skipUnless(
    test_env.get_server_version() >= (12, 1), "unsupported server"
)
class TestCase(test_env.BaseTestCase):
    def __test_bind_value_as_boolean(self, value):
        expected_result = str(bool(value)).upper()
        var = self.cursor.var(bool)
        var.setvalue(0, value)
        result = self.cursor.callfunc(
            "pkg_TestBooleans.GetStringRep", str, [var]
        )
        self.assertEqual(result, expected_result)

    def test_3100(self):
        "3100 - test binding in a False value"
        result = self.cursor.callfunc(
            "pkg_TestBooleans.GetStringRep", str, [False]
        )
        self.assertEqual(result, "FALSE")

    def test_3101(self):
        "3101 - test binding in a float as a boolean"
        self.__test_bind_value_as_boolean(0.0)
        self.__test_bind_value_as_boolean(1.0)

    def test_3102(self):
        "3102 - test binding in an integer as a boolean"
        self.__test_bind_value_as_boolean(0)
        self.__test_bind_value_as_boolean(1)

    def test_3103(self):
        "3103 - test binding in a null value"
        self.cursor.setinputsizes(None, bool)
        result = self.cursor.callfunc(
            "pkg_TestBooleans.GetStringRep", str, [None]
        )
        self.assertEqual(result, "NULL")

    def test_3104(self):
        "3104 - test binding out a boolean value (False)"
        result = self.cursor.callfunc(
            "pkg_TestBooleans.IsLessThan10", oracledb.DB_TYPE_BOOLEAN, [15]
        )
        self.assertFalse(result)

    def test_3105(self):
        "3105 - test binding out a boolean value (True)"
        result = self.cursor.callfunc(
            "pkg_TestBooleans.IsLessThan10", bool, [5]
        )
        self.assertTrue(result)

    def test_3106(self):
        "3106 - test binding in a string as a boolean"
        self.__test_bind_value_as_boolean("")
        self.__test_bind_value_as_boolean("0")

    def test_3107(self):
        "3107 - test binding in a True value"
        result = self.cursor.callfunc(
            "pkg_TestBooleans.GetStringRep", str, [True]
        )
        self.assertEqual(result, "TRUE")

    def test_3108(self):
        "3108 - test binding out a boolean value (None)"
        result = self.cursor.callfunc(
            "pkg_TestBooleans.TestOutValueNull", bool
        )
        self.assertIsNone(result)

    @unittest.skipUnless(
        test_env.get_client_version() >= (23, 1), "unsupported client"
    )
    @unittest.skipUnless(
        test_env.get_server_version() >= (23, 1), "unsupported server"
    )
    def test_3109(self):
        "3109 - test binding and fetching boolean with 23ai"
        for value in (True, False):
            with self.subTest(value=value):
                self.cursor.execute("select not :1 from dual", [value])
                (fetched_value,) = self.cursor.fetchone()
                self.assertIsInstance(fetched_value, bool)
                self.assertEqual(fetched_value, not value)

    @unittest.skipUnless(
        test_env.get_client_version() >= (23, 1), "unsupported client"
    )
    @unittest.skipUnless(
        test_env.get_server_version() >= (23, 1), "unsupported server"
    )
    def test_3110(self):
        "3110 - test binding and fetching string literals that represent True"
        self.cursor.execute("truncate table TestBooleans")
        true_values = ["true", "yes", "on", "1", "t", "y"]
        self.cursor.executemany(
            "insert into TestBooleans values (:1, :2, :3)",
            [(i, v, v) for i, v in enumerate(true_values)],
        )
        self.cursor.execute(
            "select BooleanCol1, BooleanCol2 from TestBooleans order by IntCol"
        )
        expected_values = [(True, True) for _ in true_values]
        self.assertEqual(self.cursor.fetchall(), expected_values)

    @unittest.skipUnless(
        test_env.get_client_version() >= (23, 1), "unsupported client"
    )
    @unittest.skipUnless(
        test_env.get_server_version() >= (23, 1), "unsupported server"
    )
    def test_3111(self):
        "3111 - test binding and fetching string literals that represent False"
        self.cursor.execute("truncate table TestBooleans")
        false_values = ["false", "no", "off", "0", "f", "n"]
        self.cursor.executemany(
            "insert into TestBooleans values (:1, :2, :3)",
            [(i, v, v) for i, v in enumerate(false_values)],
        )
        self.cursor.execute(
            "select BooleanCol1, BooleanCol2 from TestBooleans order by IntCol"
        )
        expected_value = [(False, False) for _ in range(len(false_values))]
        self.assertEqual(self.cursor.fetchall(), expected_value)


if __name__ == "__main__":
    test_env.run_test_cases()
