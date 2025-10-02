# -----------------------------------------------------------------------------
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
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
6700 - Module for testing the JSON data type extension in Oracle DB version 23.
"""

import json

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(test_env):
    if not test_env.has_client_and_server_version(23):
        pytest.skip("no native JSON extensions support")


def _test_fetch_json(cursor, value, table_name="TestJson"):
    """
    Tests fetching JSON encoded by the database.
    """
    cursor.execute(f"delete from {table_name}")
    cursor.execute(
        f"insert into {table_name} values (1, :1)", [json.dumps(value)]
    )
    cursor.execute(f"select JsonCol from {table_name}")
    (fetched_value,) = cursor.fetchone()
    assert fetched_value == value


def _test_round_trip_json(cursor, value):
    """
    Tests fetching JSON encoded by the driver.
    """
    cursor.execute("delete from TestJson")
    cursor.setinputsizes(oracledb.DB_TYPE_JSON)
    cursor.execute("insert into TestJson values (1, :1)", [value])
    cursor.execute("select JsonCol from TestJson")
    (fetched_value,) = cursor.fetchone()
    assert fetched_value == value


def test_6700(cursor):
    "6700 - fetch JSON with a field name greater than 255 bytes"
    fname_long = "A" * 256
    value = {}
    value[fname_long] = 6700
    _test_fetch_json(cursor, value)


def test_6701(cursor):
    "6701 - fetch JSON with field names greater and less than 255 bytes"
    fname_short = "short_name"
    fname_long = "A" * 256
    value = {}
    value[fname_short] = "Short name"
    value[fname_long] = 6701
    _test_fetch_json(cursor, value)


def test_6702(cursor):
    "6702 - fetch JSON with many field names greater than 255 bytes"
    value = {}
    for i in range(26):
        for j in range(26):
            fname = chr(i + ord("A")) + chr(j + ord("A")) + "X" * 254
            value[fname] = 12.25
    _test_fetch_json(cursor, value)


def test_6703(cursor):
    "6703 - fetch JSON with many field names (large and small)"
    value = {}
    for i in range(26):
        for j in range(26):
            short_name = chr(i + ord("A")) + chr(j + ord("A"))
            value[short_name] = 6.75
            long_name = short_name + "X" * 254
            value[long_name] = 12.25
    _test_fetch_json(cursor, value)


def test_6704(cursor):
    "6704 - fetch JSON with many field names (one large and many small)"
    value = {}
    long_name = "B" * 256
    value[long_name] = 6704
    for i in range(26):
        for j in range(26):
            short_name = chr(i + ord("A")) + chr(j + ord("A"))
            value[short_name] = 8.625
    _test_fetch_json(cursor, value)


def test_6705(cursor):
    "6705 - round trip JSON with a field name greater than 255 bytes"
    fname_long = "A" * 256
    value = {}
    value[fname_long] = 6705
    _test_round_trip_json(cursor, value)


def test_6706(cursor):
    "6706 - round trip JSON with field names (small and large)"
    fname_short = "short_name"
    fname_long = "A" * 256
    value = {}
    value[fname_short] = "Short name"
    value[fname_long] = 6706
    _test_round_trip_json(cursor, value)


def test_6707(cursor):
    "6707 - round trip JSON with many field names greater than 255 bytes"
    value = {}
    for i in range(26):
        for j in range(26):
            fname = chr(i + ord("A")) + chr(j + ord("A")) + "X" * 254
            value[fname] = 12.25
    _test_round_trip_json(cursor, value)


def test_6708(cursor):
    "6708 - round trip JSON with many field names (large and small)"
    value = {}
    for i in range(26):
        for j in range(26):
            short_name = chr(i + ord("A")) + chr(j + ord("A"))
            value[short_name] = 6.75
            long_name = short_name + "X" * 254
            value[long_name] = 12.25
    _test_round_trip_json(cursor, value)


def test_6709(cursor):
    "6709 - round trip JSON with many field names (1 large and many small)"
    value = {}
    long_name = "B" * 256
    value[long_name] = 6704
    for i in range(26):
        for j in range(26):
            short_name = chr(i + ord("A")) + chr(j + ord("A"))
            value[short_name] = 8.625
    _test_round_trip_json(cursor, value)


def test_6710(cursor):
    "6710 - fetch JSON with relative offsets"
    value = {}
    fname_long = "C" * 256
    value[fname_long] = 6710
    value["num_list"] = [1.5, 2.25, 3.75, 5.5]
    value["str_list"] = ["string 1", "string 2"]
    _test_fetch_json(cursor, value, "TestCompressedJson")


def test_6711(cursor):
    "6711 - fetch JSON with relative offsets and shared fields and values"
    value = []
    for i in range(15):
        value.append(dict(a=6711, b="String Value"))
    _test_fetch_json(cursor, value, "TestCompressedJson")


def test_6712(cursor):
    "6712 - fetch JSON with relative offsets and shared fields, not values"
    value = []
    for i in range(15):
        value.append(dict(a=6711 + i, b=f"String Value {i}"))
    _test_fetch_json(cursor, value, "TestCompressedJson")
