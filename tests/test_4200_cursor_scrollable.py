# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
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
4200 - Module for testing scrollable cursors
"""


def test_4200(conn):
    "4200 - test creating a scrollable cursor"
    cursor = conn.cursor()
    assert not cursor.scrollable
    cursor = conn.cursor(True)
    assert cursor.scrollable
    cursor = conn.cursor(scrollable=True)
    assert cursor.scrollable
    cursor.scrollable = False
    assert not cursor.scrollable


def test_4201(conn, test_env):
    "4201 - test scrolling absolute yields an exception (after result set)"
    test_env.skip_unless_server_version(12, 2)
    cursor = conn.cursor(scrollable=True)
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    with test_env.assert_raises_full_code("DPY-2063"):
        cursor.scroll(12, "absolute")


def test_4202(conn):
    "4202 - test scrolling absolute (when in buffers)"
    cursor = conn.cursor(scrollable=True)
    cursor.prefetchrows = 0
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    cursor.fetchmany()
    assert (
        cursor.arraysize > 1
    ), "array size must exceed 1 for this test to work correctly"
    cursor.scroll(1, mode="absolute")
    (value,) = cursor.fetchone()
    assert value == 1.25
    assert cursor.rowcount == 1


def test_4203(conn, test_env):
    "4203 - test scrolling absolute (when not in buffers)"
    test_env.skip_unless_server_version(12, 2)
    cursor = conn.cursor(scrollable=True)
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    cursor.scroll(6, mode="absolute")
    (value,) = cursor.fetchone()
    assert value == 7.5
    assert cursor.rowcount == 6


def test_4204(conn):
    "4204 - test scrolling to first row in result set (in buffers)"
    cursor = conn.cursor(scrollable=True)
    cursor.prefetchrows = 0
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    cursor.fetchmany()
    cursor.scroll(mode="first")
    (value,) = cursor.fetchone()
    assert value == 1.25
    assert cursor.rowcount == 1


def test_4205(conn):
    "4205 - test scrolling to first row in result set (not in buffers)"
    cursor = conn.cursor(scrollable=True)
    cursor.prefetchrows = 0
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    cursor.fetchmany()
    cursor.fetchmany()
    cursor.scroll(mode="first")
    (value,) = cursor.fetchone()
    assert value == 1.25
    assert cursor.rowcount == 1


def test_4206(conn):
    "4206 - test scrolling to last row in result set"
    cursor = conn.cursor(scrollable=True)
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    cursor.scroll(mode="last")
    (value,) = cursor.fetchone()
    assert value == 12.5
    assert cursor.rowcount == 10


def test_4207(conn, test_env):
    "4207 - test scrolling relative yields an exception (after result set)"
    test_env.skip_unless_server_version(12, 2)
    cursor = conn.cursor(scrollable=True)
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    with test_env.assert_raises_full_code("DPY-2063"):
        cursor.scroll(15)


def test_4208(conn, test_env):
    "4208 - test scrolling relative yields exception (before result set)"
    cursor = conn.cursor(scrollable=True)
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    with test_env.assert_raises_full_code("DPY-2063"):
        cursor.scroll(-5)


def test_4209(conn):
    "4209 - test scrolling relative (when in buffers)"
    cursor = conn.cursor(scrollable=True)
    cursor.prefetchrows = 0
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    cursor.fetchmany()
    message = "array size must exceed 1 for this test to work correctly"
    assert cursor.arraysize > 1, message
    cursor.scroll(2 - cursor.rowcount)
    (value,) = cursor.fetchone()
    assert value == 2.5
    assert cursor.rowcount == 2


def test_4210(conn):
    "4210 - test scrolling relative (when not in buffers)"
    cursor = conn.cursor(scrollable=True)
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    cursor.fetchmany()
    cursor.fetchmany()
    message = "array size must exceed 1 for this test to work correctly"
    assert cursor.arraysize > 1, message
    cursor.scroll(3 - cursor.rowcount)
    (value,) = cursor.fetchone()
    assert value == 3.75
    assert cursor.rowcount == 3


def test_4211(conn, cursor, test_env):
    "4211 - test scrolling when there are no rows"
    test_env.skip_unless_server_version(12, 2)
    cursor.execute("truncate table TestTempTable")
    cursor = conn.cursor(scrollable=True)
    cursor.execute("select * from TestTempTable")
    cursor.scroll(mode="last")
    assert cursor.fetchall() == []
    cursor.scroll(mode="first")
    assert cursor.fetchall() == []
    with test_env.assert_raises_full_code("DPY-2063"):
        cursor.scroll(1, mode="absolute")


def test_4212(conn, cursor, test_env):
    "4212 - test scrolling with differing array and fetch array sizes"
    test_env.skip_unless_server_version(12, 2)
    cursor.execute("truncate table TestTempTable")
    for i in range(30):
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, null)
            """,
            [i + 1],
        )
    conn.commit()
    for arraysize in range(1, 6):
        cursor = conn.cursor(scrollable=True)
        cursor.arraysize = arraysize
        cursor.execute("select IntCol from TestTempTable order by IntCol")
        for num_rows in range(1, arraysize + 1):
            cursor.scroll(15, "absolute")
            rows = cursor.fetchmany(num_rows)
            assert rows[0][0] == 15
            assert cursor.rowcount == 15 + num_rows - 1
            cursor.scroll(9)
            rows = cursor.fetchmany(num_rows)
            num_rows_fetched = len(rows)
            assert rows[0][0] == 15 + num_rows + 8
            assert cursor.rowcount == 15 + num_rows + num_rows_fetched + 7
            cursor.scroll(-12)
            rows = cursor.fetchmany(num_rows)
            count = 15 + num_rows + num_rows_fetched - 5
            assert rows[0][0] == count
            count = 15 + num_rows + num_rows_fetched + num_rows - 6
            assert cursor.rowcount == count


def test_4213(conn, test_env):
    "4213 - test calling scroll() with invalid mode"
    cursor = conn.cursor(scrollable=True)
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    cursor.fetchmany()
    with test_env.assert_raises_full_code("DPY-2009"):
        cursor.scroll(mode="middle")


def test_4214(conn):
    "4214 - test scroll after fetching all rows"
    cursor = conn.cursor(scrollable=True)
    cursor.arraysize = 5
    cursor.prefetchrows = 0
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    cursor.fetchall()
    cursor.scroll(5, mode="absolute")
    (value,) = cursor.fetchone()
    assert value == 6.25
    assert cursor.rowcount == 5


def test_4215(conn):
    "4215 - test parse() on a scrollable cursor"
    cursor = conn.cursor(scrollable=True)
    statement = """
        select 1 from dual
        union all
        select 2 from dual
        union all
        select 3 from dual
        union all
        select 4 from dual
        union all
        select 5 from dual
    """
    cursor.parse(statement)
    cursor.execute(statement)
    (fetched_value,) = cursor.fetchone()
    assert fetched_value == 1
    cursor.scroll(mode="last")
    (fetched_value,) = cursor.fetchone()
    assert fetched_value == 5


def test_4216(conn):
    "4216 - test scroll operation with bind values"
    cursor = conn.cursor(scrollable=True)
    base_value = 4215
    cursor.execute(
        """
        select :base_value + 1 from dual
        union all
        select :base_value + 2 from dual
        union all
        select :base_value + 3 from dual
        """,
        dict(base_value=base_value),
    )
    cursor.scroll(mode="last")
    (fetched_value,) = cursor.fetchone()
    assert fetched_value == base_value + 3


def test_4217(conn, test_env):
    "4217 - test calling scroll() on a non-scrollable cursor"
    cursor = conn.cursor()
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    with test_env.assert_raises_full_code("DPY-2068"):
        cursor.scroll(mode="first")
