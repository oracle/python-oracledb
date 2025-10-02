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

"""
E1200 - Module for testing the use of the statement cache
"""

import random


def test_ext_1200(conn, parse_count_checker):
    "E1200 - verify statement cache is used"
    statements = [
        "select 0 from dual",
        "select 1 from dual",
        "select 2 from dual",
    ]
    conn.stmtcachesize = len(statements)
    for i in range(500):
        sql = random.choice(statements)
        with conn.cursor() as cursor:
            cursor.execute(sql)
            cursor.fetchall()
    assert parse_count_checker.get_value() == 3


def test_ext_1201(conn, parse_count_checker):
    "E1201 - verify statement cache uses LIFO"
    statements = [
        "select 0 from dual",
        "select 1 from dual",
        "select 2 from dual",
    ]
    conn.stmtcachesize = len(statements)
    for sql in statements:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            cursor.fetchall()
    with conn.cursor() as cursor:
        cursor.execute("begin null; end;")
    assert parse_count_checker.get_value() == 4
    for sql in statements[1:]:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            cursor.fetchall()
    assert parse_count_checker.get_value() == 0
    with conn.cursor() as cursor:
        cursor.execute(statements[0])
        cursor.fetchall()
    assert parse_count_checker.get_value() == 1


def test_ext_1202(conn, parse_count_checker):
    "E1202 - verify copied statement is independent of cached statement"
    sql = "select : val from dual"
    value1 = "One"
    value2 = "Four"
    value3 = "Five"
    with conn.cursor() as cursor:
        cursor.execute(sql, [value1])
        rows = cursor.fetchall()
        assert rows == [(value1,)]
    assert parse_count_checker.get_value() == 1
    with conn.cursor() as cursor:
        cursor.execute(sql, [value1])
        assert parse_count_checker.get_value() == 0
        with conn.cursor() as copyCursor:
            copyCursor.execute(sql, [value2])
            rows = copyCursor.fetchall()
            assert rows == [(value2,)]
        rows = cursor.fetchall()
        assert rows == [(value1,)]
    assert parse_count_checker.get_value() == 1
    with conn.cursor() as cursor:
        cursor.execute(sql, [value3])
        rows = cursor.fetchall()
        assert rows == [(value3,)]
    assert parse_count_checker.get_value() == 0
