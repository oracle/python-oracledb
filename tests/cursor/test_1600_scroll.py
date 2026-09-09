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
Module for testing scrollable cursors
"""


def test_cursor_1600(conn):
    "1600 - test creating a scrollable cursor"
    cursor = conn.cursor()
    assert not cursor.scrollable
    cursor = conn.cursor(True)
    assert cursor.scrollable
    cursor = conn.cursor(scrollable=True)
    assert cursor.scrollable
    cursor.scrollable = False
    assert not cursor.scrollable


def test_cursor_1601(conn, test_env):
    "1601 - test scrolling absolute yields an exception (after result set)"
    test_env.skip_unless_server_version(12, 2)
    cursor = conn.cursor(scrollable=True)
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    with test_env.assert_raises_full_code("DPY-2063"):
        cursor.scroll(12, "absolute")


def test_cursor_1602(conn):
    "1602 - test scrolling absolute (when in buffers)"
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


def test_cursor_1603(conn, test_env):
    "1603 - test scrolling absolute (when not in buffers)"
    test_env.skip_unless_server_version(12, 2)
    cursor = conn.cursor(scrollable=True)
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    cursor.scroll(6, mode="absolute")
    (value,) = cursor.fetchone()
    assert value == 7.5
    assert cursor.rowcount == 6


def test_cursor_1604(conn):
    "1604 - test scrolling to first row in result set (in buffers)"
    cursor = conn.cursor(scrollable=True)
    cursor.prefetchrows = 0
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    cursor.fetchmany()
    cursor.scroll(mode="first")
    (value,) = cursor.fetchone()
    assert value == 1.25
    assert cursor.rowcount == 1


def test_cursor_1605(conn):
    "1605 - test scrolling to first row in result set (not in buffers)"
    cursor = conn.cursor(scrollable=True)
    cursor.prefetchrows = 0
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    cursor.fetchmany()
    cursor.fetchmany()
    cursor.scroll(mode="first")
    (value,) = cursor.fetchone()
    assert value == 1.25
    assert cursor.rowcount == 1


def test_cursor_1606(conn):
    "1606 - test scrolling to last row in result set"
    cursor = conn.cursor(scrollable=True)
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    cursor.scroll(mode="last")
    (value,) = cursor.fetchone()
    assert value == 12.5
    assert cursor.rowcount == 10


def test_cursor_1607(conn, test_env):
    "1607 - test scrolling relative yields an exception (after result set)"
    test_env.skip_unless_server_version(12, 2)
    cursor = conn.cursor(scrollable=True)
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    with test_env.assert_raises_full_code("DPY-2063"):
        cursor.scroll(15)


def test_cursor_1608(conn, test_env):
    "1608 - test scrolling relative yields exception (before result set)"
    cursor = conn.cursor(scrollable=True)
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    with test_env.assert_raises_full_code("DPY-2063"):
        cursor.scroll(-5)


def test_cursor_1609(conn):
    "1609 - test scrolling relative (when in buffers)"
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


def test_cursor_1610(conn):
    "1610 - test scrolling relative (when not in buffers)"
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


def test_cursor_1611(conn, cursor, test_env):
    "1611 - test scrolling when there are no rows"
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


def test_cursor_1612(conn, cursor, test_env):
    "1612 - test scrolling with differing array and fetch array sizes"
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


def test_cursor_1613(conn, test_env):
    "1613 - test calling scroll() with invalid mode"
    cursor = conn.cursor(scrollable=True)
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    cursor.fetchmany()
    with test_env.assert_raises_full_code("DPY-2009"):
        cursor.scroll(mode="middle")


def test_cursor_1614(conn):
    "1614 - test scroll after fetching all rows"
    cursor = conn.cursor(scrollable=True)
    cursor.arraysize = 5
    cursor.prefetchrows = 0
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    cursor.fetchall()
    cursor.scroll(5, mode="absolute")
    (value,) = cursor.fetchone()
    assert value == 6.25
    assert cursor.rowcount == 5


def test_cursor_1615(conn):
    "1615 - test parse() on a scrollable cursor"
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


def test_cursor_1616(conn):
    "1616 - test scroll operation with bind values"
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


def test_cursor_1617(conn, test_env):
    "1617 - test calling scroll() on a non-scrollable cursor"
    cursor = conn.cursor()
    cursor.execute("select NumberCol from TestNumbers order by IntCol")
    with test_env.assert_raises_full_code("DPY-2068"):
        cursor.scroll(mode="first")
