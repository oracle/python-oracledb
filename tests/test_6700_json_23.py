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
6700 - Module for testing the JSON data type extension in Oracle Database 23ai.
"""

import json
import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_client_version() >= (23, 0), "unsupported client"
)
@unittest.skipUnless(
    test_env.get_server_version() >= (23, 0), "unsupported server"
)
class TestCase(test_env.BaseTestCase):
    def __test_fetch_json(self, value, table_name="TestJson"):
        """
        Tests fetching JSON encoded by the database.
        """
        self.cursor.execute(f"delete from {table_name}")
        self.cursor.execute(
            f"insert into {table_name} values (1, :1)", [json.dumps(value)]
        )
        self.cursor.execute(f"select JsonCol from {table_name}")
        (fetched_value,) = self.cursor.fetchone()
        self.assertEqual(fetched_value, value)

    def __test_round_trip_json(self, value):
        """
        Tests fetching JSON encoded by the driver.
        """
        self.cursor.execute("delete from TestJson")
        self.cursor.setinputsizes(oracledb.DB_TYPE_JSON)
        self.cursor.execute("insert into TestJson values (1, :1)", [value])
        self.cursor.execute("select JsonCol from TestJson")
        (fetched_value,) = self.cursor.fetchone()
        self.assertEqual(fetched_value, value)

    def test_6700(self):
        "6700 - fetch JSON with a field name greater than 255 bytes"
        fname_long = "A" * 256
        value = {}
        value[fname_long] = 6700
        self.__test_fetch_json(value)

    def test_6701(self):
        "6701 - fetch JSON with field names greater and less than 255 bytes"
        fname_short = "short_name"
        fname_long = "A" * 256
        value = {}
        value[fname_short] = "Short name"
        value[fname_long] = 6701
        self.__test_fetch_json(value)

    def test_6702(self):
        "6702 - fetch JSON with many field names greater than 255 bytes"
        value = {}
        for i in range(26):
            for j in range(26):
                fname = chr(i + ord("A")) + chr(j + ord("A")) + "X" * 254
                value[fname] = 12.25
        self.__test_fetch_json(value)

    def test_6703(self):
        "6703 - fetch JSON with many field names (large and small)"
        value = {}
        for i in range(26):
            for j in range(26):
                short_name = chr(i + ord("A")) + chr(j + ord("A"))
                value[short_name] = 6.75
                long_name = short_name + "X" * 254
                value[long_name] = 12.25
        self.__test_fetch_json(value)

    def test_6704(self):
        "6704 - fetch JSON with many field names (one large and many small)"
        value = {}
        long_name = "B" * 256
        value[long_name] = 6704
        for i in range(26):
            for j in range(26):
                short_name = chr(i + ord("A")) + chr(j + ord("A"))
                value[short_name] = 8.625
        self.__test_fetch_json(value)

    def test_6705(self):
        "6705 - round trip JSON with a field name greater than 255 bytes"
        fname_long = "A" * 256
        value = {}
        value[fname_long] = 6705
        self.__test_round_trip_json(value)

    def test_6706(self):
        "6706 - round trip JSON with field names (small and large)"
        fname_short = "short_name"
        fname_long = "A" * 256
        value = {}
        value[fname_short] = "Short name"
        value[fname_long] = 6706
        self.__test_round_trip_json(value)

    def test_6707(self):
        "6707 - round trip JSON with many field names greater than 255 bytes"
        value = {}
        for i in range(26):
            for j in range(26):
                fname = chr(i + ord("A")) + chr(j + ord("A")) + "X" * 254
                value[fname] = 12.25
        self.__test_round_trip_json(value)

    def test_6708(self):
        "6708 - round trip JSON with many field names (large and small)"
        value = {}
        for i in range(26):
            for j in range(26):
                short_name = chr(i + ord("A")) + chr(j + ord("A"))
                value[short_name] = 6.75
                long_name = short_name + "X" * 254
                value[long_name] = 12.25
        self.__test_round_trip_json(value)

    def test_6709(self):
        "6709 - round trip JSON with many field names (1 large and many small)"
        value = {}
        long_name = "B" * 256
        value[long_name] = 6704
        for i in range(26):
            for j in range(26):
                short_name = chr(i + ord("A")) + chr(j + ord("A"))
                value[short_name] = 8.625
        self.__test_round_trip_json(value)

    def test_6710(self):
        "6710 - fetch JSON with relative offsets"
        value = {}
        fname_long = "C" * 256
        value[fname_long] = 6710
        value["num_list"] = [1.5, 2.25, 3.75, 5.5]
        value["str_list"] = ["string 1", "string 2"]
        self.__test_fetch_json(value, "TestCompressedJson")

    def test_6711(self):
        "6711 - fetch JSON with relative offsets and shared fields and values"
        value = []
        for i in range(15):
            value.append(dict(a=6711, b="String Value"))
        self.__test_fetch_json(value, "TestCompressedJson")

    def test_6712(self):
        "6712 - fetch JSON with relative offsets and shared fields, not values"
        value = []
        for i in range(15):
            value.append(dict(a=6711 + i, b=f"String Value {i}"))
        self.__test_fetch_json(value, "TestCompressedJson")


if __name__ == "__main__":
    test_env.run_test_cases()
