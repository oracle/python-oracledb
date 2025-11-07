# -----------------------------------------------------------------------------
# Copyright (c) 2025, Oracle and/or its affiliates.
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
8600 - Module for testing scrollable cursors with asyncio
"""

import pytest


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode, test_env):
    test_env.skip_unless_server_version(12, 2)


async def test_8600(async_conn):
    "8600 - test creating a scrollable cursor"
    cursor = async_conn.cursor()
    assert not cursor.scrollable
    cursor = async_conn.cursor(True)
    assert cursor.scrollable
    cursor = async_conn.cursor(scrollable=True)
    assert cursor.scrollable
    cursor.scrollable = False
    assert not cursor.scrollable


async def test_8601(async_conn, test_env):
    "8601 - test scrolling absolute yields an exception (after result set)"
    cursor = async_conn.cursor(scrollable=True)
    await cursor.execute("select NumberCol from TestNumbers order by IntCol")
    with test_env.assert_raises_full_code("DPY-2063"):
        await cursor.scroll(12, "absolute")


async def test_8602(async_conn):
    "8602 - test scrolling absolute (when in buffers)"
    cursor = async_conn.cursor(scrollable=True)
    cursor.prefetchrows = 0
    await cursor.execute("select NumberCol from TestNumbers order by IntCol")
    await cursor.fetchmany()
    assert (
        cursor.arraysize > 1
    ), "array size must exceed 1 for this test to work correctly"
    await cursor.scroll(1, mode="absolute")
    (value,) = await cursor.fetchone()
    assert value == 1.25
    assert cursor.rowcount == 1


async def test_8603(async_conn):
    "8603 - test scrolling absolute (when not in buffers)"
    cursor = async_conn.cursor(scrollable=True)
    await cursor.execute("select NumberCol from TestNumbers order by IntCol")
    await cursor.scroll(6, mode="absolute")
    (value,) = await cursor.fetchone()
    assert value == 7.5
    assert cursor.rowcount == 6


async def test_8604(async_conn):
    "8604 - test scrolling to first row in result set (in buffers)"
    cursor = async_conn.cursor(scrollable=True)
    cursor.prefetchrows = 0
    await cursor.execute("select NumberCol from TestNumbers order by IntCol")
    await cursor.fetchmany()
    await cursor.scroll(mode="first")
    (value,) = await cursor.fetchone()
    assert value == 1.25
    assert cursor.rowcount == 1


async def test_8605(async_conn):
    "8605 - test scrolling to first row in result set (not in buffers)"
    cursor = async_conn.cursor(scrollable=True)
    cursor.prefetchrows = 0
    await cursor.execute("select NumberCol from TestNumbers order by IntCol")
    await cursor.fetchmany()
    await cursor.fetchmany()
    await cursor.scroll(mode="first")
    (value,) = await cursor.fetchone()
    assert value == 1.25
    assert cursor.rowcount == 1


async def test_8606(async_conn):
    "8606 - test scrolling to last row in result set"
    cursor = async_conn.cursor(scrollable=True)
    await cursor.execute("select NumberCol from TestNumbers order by IntCol")
    await cursor.scroll(mode="last")
    (value,) = await cursor.fetchone()
    assert value == 12.5
    assert cursor.rowcount == 10


async def test_8607(async_conn, test_env):
    "8607 - test scrolling relative yields an exception (after result set)"
    cursor = async_conn.cursor(scrollable=True)
    await cursor.execute("select NumberCol from TestNumbers order by IntCol")
    with test_env.assert_raises_full_code("DPY-2063"):
        await cursor.scroll(15)


async def test_8608(async_conn, test_env):
    "8608 - test scrolling relative yields exception (before result set)"
    cursor = async_conn.cursor(scrollable=True)
    await cursor.execute("select NumberCol from TestNumbers order by IntCol")
    with test_env.assert_raises_full_code("DPY-2063"):
        await cursor.scroll(-5)


async def test_8609(async_conn):
    "8609 - test scrolling relative (when in buffers)"
    cursor = async_conn.cursor(scrollable=True)
    cursor.prefetchrows = 0
    await cursor.execute("select NumberCol from TestNumbers order by IntCol")
    await cursor.fetchmany()
    message = "array size must exceed 1 for this test to work correctly"
    assert cursor.arraysize > 1, message
    await cursor.scroll(2 - cursor.rowcount)
    (value,) = await cursor.fetchone()
    assert value == 2.5
    assert cursor.rowcount == 2


async def test_8610(async_conn):
    "8610 - test scrolling relative (when not in buffers)"
    cursor = async_conn.cursor(scrollable=True)
    await cursor.execute("select NumberCol from TestNumbers order by IntCol")
    await cursor.fetchmany()
    await cursor.fetchmany()
    message = "array size must exceed 1 for this test to work correctly"
    assert cursor.arraysize > 1, message
    await cursor.scroll(3 - cursor.rowcount)
    (value,) = await cursor.fetchone()
    assert value == 3.75
    assert cursor.rowcount == 3


async def test_8611(async_conn, async_cursor, test_env):
    "8611 - test scrolling when there are no rows"
    await async_cursor.execute("truncate table TestTempTable")
    cursor = async_conn.cursor(scrollable=True)
    await cursor.execute("select * from TestTempTable")
    await cursor.scroll(mode="last")
    assert await cursor.fetchall() == []
    await cursor.scroll(mode="first")
    assert await cursor.fetchall() == []
    with test_env.assert_raises_full_code("DPY-2063"):
        await cursor.scroll(1, mode="absolute")


async def test_8612(async_conn, async_cursor):
    "8612 - test scrolling with differing array and fetch array sizes"
    await async_cursor.execute("truncate table TestTempTable")
    for i in range(30):
        await async_cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, null)
            """,
            [i + 1],
        )
    for arraysize in range(1, 6):
        cursor = async_conn.cursor(scrollable=True)
        cursor.arraysize = arraysize
        await cursor.execute(
            "select IntCol from TestTempTable order by IntCol"
        )
        for num_rows in range(1, arraysize + 1):
            await cursor.scroll(15, "absolute")
            rows = await cursor.fetchmany(num_rows)
            assert rows[0][0] == 15
            assert cursor.rowcount == 15 + num_rows - 1
            await cursor.scroll(9)
            rows = await cursor.fetchmany(num_rows)
            num_rows_fetched = len(rows)
            assert rows[0][0] == 15 + num_rows + 8
            assert cursor.rowcount == 15 + num_rows + num_rows_fetched + 7
            await cursor.scroll(-12)
            rows = await cursor.fetchmany(num_rows)
            count = 15 + num_rows + num_rows_fetched - 5
            assert rows[0][0] == count
            count = 15 + num_rows + num_rows_fetched + num_rows - 6
            assert cursor.rowcount == count


async def test_8613(async_conn, test_env):
    "8613 - test calling scroll() with invalid mode"
    cursor = async_conn.cursor(scrollable=True)
    await cursor.execute("select NumberCol from TestNumbers order by IntCol")
    await cursor.fetchmany()
    with test_env.assert_raises_full_code("DPY-2009"):
        await cursor.scroll(mode="middle")


async def test_8614(async_conn):
    "8614 - test scroll after fetching all rows"
    cursor = async_conn.cursor(scrollable=True)
    cursor.arraysize = 5
    cursor.prefetchrows = 0
    await cursor.execute("select NumberCol from TestNumbers order by IntCol")
    await cursor.fetchall()
    await cursor.scroll(5, mode="absolute")
    (value,) = await cursor.fetchone()
    assert value == 6.25
    assert cursor.rowcount == 5


async def test_8615(async_conn):
    "8615 - test parse() on a scrollable cursor"
    cursor = async_conn.cursor(scrollable=True)
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
    await cursor.parse(statement)
    await cursor.execute(statement)
    (fetched_value,) = await cursor.fetchone()
    assert fetched_value == 1
    await cursor.scroll(mode="last")
    (fetched_value,) = await cursor.fetchone()
    assert fetched_value == 5


async def test_8616(async_conn):
    "8616 - test scroll operation with bind values"
    cursor = async_conn.cursor(scrollable=True)
    base_value = 4215
    await cursor.execute(
        """
        select :base_value + 1 from dual
        union all
        select :base_value + 2 from dual
        union all
        select :base_value + 3 from dual
        """,
        dict(base_value=base_value),
    )
    await cursor.scroll(mode="last")
    (fetched_value,) = await cursor.fetchone()
    assert fetched_value == base_value + 3


async def test_8617(async_conn, test_env):
    "8717 - test calling scroll() on a non-scrollable cursor"
    cursor = async_conn.cursor()
    await cursor.execute("select NumberCol from TestNumbers order by IntCol")
    with test_env.assert_raises_full_code("DPY-2068"):
        await cursor.scroll(mode="first")
