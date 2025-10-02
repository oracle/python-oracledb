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
5800 - Module for testing cursor variables with asyncio
"""

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


async def test_5800(async_conn, async_cursor, test_env):
    "5800 - test binding in a cursor"
    ref_cursor = async_conn.cursor()
    assert ref_cursor.description is None
    await async_cursor.execute(
        """
        begin
            open :cursor for select 'X' StringValue from dual;
        end;
        """,
        cursor=ref_cursor,
    )
    varchar_ratio, _ = test_env.charset_ratios
    expected_value = [
        (
            "STRINGVALUE",
            oracledb.DB_TYPE_CHAR,
            1,
            varchar_ratio,
            None,
            None,
            True,
        )
    ]
    assert ref_cursor.description == expected_value
    assert await ref_cursor.fetchall() == [("X",)]


async def test_5801(async_conn, async_cursor, test_env):
    "5801 - test binding in a cursor from a package"
    ref_cursor = async_conn.cursor()
    assert ref_cursor.description is None
    await async_cursor.callproc(
        "pkg_TestRefCursors.TestOutCursor", (2, ref_cursor)
    )
    varchar_ratio, _ = test_env.charset_ratios
    expected_value = [
        ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
        (
            "STRINGCOL",
            oracledb.DB_TYPE_VARCHAR,
            20,
            20 * varchar_ratio,
            None,
            None,
            False,
        ),
    ]
    assert ref_cursor.description == expected_value
    assert await ref_cursor.fetchall() == [(1, "String 1"), (2, "String 2")]


async def test_5802(async_cursor, test_env):
    "5802 - test that binding the cursor itself is not supported"
    sql = """
            begin
                open :pcursor for
                    select 1 from dual;
            end;"""
    with test_env.assert_raises_full_code("DPY-3009"):
        await async_cursor.execute(sql, pcursor=async_cursor)


async def test_5803(async_conn, async_cursor):
    "5803 - test returning a ref cursor after closing it"
    out_cursor = async_conn.cursor()
    sql = """
            begin
                open :pcursor for
                    select IntCol
                    from TestNumbers
                    order by IntCol;
            end;"""
    await async_cursor.execute(sql, pcursor=out_cursor)
    rows = await out_cursor.fetchall()
    out_cursor.close()
    out_cursor = async_conn.cursor()
    await async_cursor.execute(sql, pcursor=out_cursor)
    rows2 = await out_cursor.fetchall()
    assert rows == rows2


async def test_5804(async_cursor):
    "5804 - test fetching a cursor"
    await async_cursor.execute(
        """
        select IntCol, cursor(select IntCol + 1 from dual) CursorValue
        from TestNumbers
        order by IntCol
        """
    )
    expected_value = [
        ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
        (
            "CURSORVALUE",
            oracledb.DB_TYPE_CURSOR,
            None,
            None,
            None,
            None,
            True,
        ),
    ]
    assert async_cursor.description == expected_value
    for i in range(1, 11):
        number, cursor = await async_cursor.fetchone()
        assert number == i
        assert await cursor.fetchall() == [(i + 1,)]


async def test_5805(async_conn, async_cursor):
    "5805 - test that ref cursor binds cannot use optimised path"
    ref_cursor = async_conn.cursor()
    sql = """
            begin
                open :rcursor for
                    select IntCol, StringCol
                    from TestStrings where IntCol
                    between :start_value and :end_value;
            end;"""
    expected_value = [(2, "String 2"), (3, "String 3"), (4, "String 4")]
    await async_cursor.execute(
        sql, rcursor=ref_cursor, start_value=2, end_value=4
    )
    assert await ref_cursor.fetchall() == expected_value
    ref_cursor.close()

    expected_value = [(5, "String 5"), (6, "String 6")]
    ref_cursor = async_conn.cursor()
    await async_cursor.execute(
        sql, rcursor=ref_cursor, start_value=5, end_value=6
    )
    assert await ref_cursor.fetchall() == expected_value


async def test_5806(async_conn, round_trip_checker_async):
    "5806 - test round trips using a REF cursor"

    # simple DDL only requires a single round trip
    with async_conn.cursor() as cursor:
        await cursor.execute("truncate table TestTempTable")
        assert await round_trip_checker_async.get_value_async() == 1

    # array execution only requires a single round trip
    num_rows = 590
    with async_conn.cursor() as cursor:
        sql = "insert into TestTempTable (IntCol) values (:1)"
        data = [(n + 1,) for n in range(num_rows)]
        await cursor.executemany(sql, data)
        assert await round_trip_checker_async.get_value_async() == 1

    # create REF cursor and execute stored procedure
    # (array size set before procedure is called)
    with async_conn.cursor() as cursor:
        refcursor = async_conn.cursor()
        refcursor.arraysize = 150
        await cursor.callproc("myrefcursorproc", [refcursor])
        await refcursor.fetchall()
        assert await round_trip_checker_async.get_value_async() == 5

    # create REF cursor and execute stored procedure
    # (array size set after procedure is called)
    with async_conn.cursor() as cursor:
        refcursor = async_conn.cursor()
        await cursor.callproc("myrefcursorproc", [refcursor])
        refcursor.arraysize = 145
        await refcursor.fetchall()
        assert await round_trip_checker_async.get_value_async() == 6


async def test_5807(async_conn):
    "5807 - test executing different SQL after getting a REF cursor"
    with async_conn.cursor() as cursor:
        refcursor = async_conn.cursor()
        await cursor.callproc("myrefcursorproc", [refcursor])
        var = cursor.var(int)
        await refcursor.execute("begin :1 := 15; end;", [var])
        assert var.getvalue() == 15


async def test_5808(async_conn):
    "5808 - test calling a function that returns a REF cursor"
    with async_conn.cursor() as cursor:
        ref_cursor = await cursor.callfunc(
            "pkg_TestRefCursors.TestReturnCursor",
            oracledb.DB_TYPE_CURSOR,
            [2],
        )
        assert await ref_cursor.fetchall() == [
            (1, "String 1"),
            (2, "String 2"),
        ]


async def test_5809(async_conn, async_cursor):
    "5809 - test using an output type handler with a REF cursor"

    def type_handler(cursor, metadata):
        return cursor.var(str, arraysize=cursor.arraysize)

    async_conn.outputtypehandler = type_handler
    var = async_cursor.var(oracledb.DB_TYPE_CURSOR)
    string_val = "Test String - 5809"
    with async_conn.cursor() as cursor:
        await cursor.callproc(
            "pkg_TestRefCursors.TestLobCursor", [string_val, var]
        )
    ref_cursor = var.getvalue()
    assert await ref_cursor.fetchall() == [(string_val,)]


async def test_5810(async_cursor, test_env):
    "5810 - bind a REF cursor but never open it"
    ref_cursor_var = async_cursor.var(oracledb.DB_TYPE_CURSOR)
    await async_cursor.execute(
        """
        begin
            if false then
                open :cursor for
                    select user
                    from dual;
            end if;
        end;
        """,
        cursor=ref_cursor_var,
    )
    ref_cursor = ref_cursor_var.getvalue()
    if ref_cursor is not None:
        with test_env.assert_raises_full_code("DPY-4025"):
            await ref_cursor.fetchall()


async def test_5811(test_env):
    "5811 - test fetching a cursor with a custom class"

    class Counter:
        num_cursors_created = 0

        @classmethod
        def cursor_created(cls):
            cls.num_cursors_created += 1

    class MyConnection(oracledb.AsyncConnection):
        def cursor(self):
            Counter.cursor_created()
            return super().cursor()

    conn = await test_env.get_connection_async(conn_class=MyConnection)
    cursor = conn.cursor()
    await cursor.execute(
        """
        select
            cursor(select 1 from dual),
            cursor(select 2 from dual)
        from dual
        """
    )
    await cursor.fetchall()
    assert Counter.num_cursors_created == 3


async def test_5812(async_cursor):
    "5812 - test that nested cursors are fetched correctly"
    sql = """
        select
        'Level 1 String',
        cursor(
            select
            'Level 2 String',
            cursor(
                select
                'Level 3 String',
                cursor(
                    select 1, 'Level 4 String A' from dual
                    union all
                    select 2, 'Level 4 String B' from dual
                    union all
                    select 3, 'Level 4 String C' from dual
                ) as nc3
                from dual
            ) as nc2
            from dual
        ) as nc1
        from dual"""
    await async_cursor.execute(sql)

    async def transform_row(r):
        return tuple([await transform_fn(v) for v in r])

    async def transform_fn(v):
        if isinstance(v, oracledb.AsyncCursor):
            return [await transform_row(r) async for r in v]
        return v

    rows = [await transform_row(r) async for r in async_cursor]
    expected_value = [
        (
            "Level 1 String",
            [
                (
                    "Level 2 String",
                    [
                        (
                            "Level 3 String",
                            [
                                (1, "Level 4 String A"),
                                (2, "Level 4 String B"),
                                (3, "Level 4 String C"),
                            ],
                        ),
                    ],
                ),
            ],
        )
    ]
    assert rows == expected_value


async def test_5813(async_cursor):
    "5813 - test fetching nested cursors with more columns than parent"
    sql = """
        select
            'Top Level String',
            cursor(
                select
                    'Nested String 1',
                    'Nested String 2',
                    'Nested String 3'
                from dual
            )
        from dual"""
    await async_cursor.execute(sql)

    async def transform_row(r):
        return tuple([await transform_fn(v) for v in r])

    async def transform_fn(v):
        if isinstance(v, oracledb.AsyncCursor):
            return [await transform_row(r) async for r in v]
        return v

    rows = [await transform_row(r) async for r in async_cursor]
    expected_value = [
        (
            "Top Level String",
            [("Nested String 1", "Nested String 2", "Nested String 3")],
        )
    ]
    assert rows == expected_value


async def test_5814(async_conn, async_cursor):
    "5814 - test reusing a closed ref cursor for executing different sql"
    sql = "select 58141, 'String 58141' from dual"
    ref_cursor = async_conn.cursor()
    ref_cursor.prefetchrows = 0
    await ref_cursor.execute(sql)
    plsql = "begin pkg_TestRefCursors.TestCloseCursor(:rcursor); end;"
    await async_cursor.execute(plsql, rcursor=ref_cursor)
    sql = "select 58142, 'String 58142' from dual"
    await ref_cursor.execute(sql)
    assert await ref_cursor.fetchall() == [
        (58142, "String 58142"),
    ]


async def test_5815(async_conn, async_cursor):
    "5815 - test reusing a closed ref cursor for executing same sql"
    sql = "select 5815, 'String 5815' from dual"
    ref_cursor = async_conn.cursor()
    ref_cursor.prefetchrows = 0
    await ref_cursor.execute(sql)
    plsql = "begin pkg_TestRefCursors.TestCloseCursor(:rcursor); end;"
    await async_cursor.execute(plsql, rcursor=ref_cursor)
    await ref_cursor.execute(sql)
    assert await ref_cursor.fetchall() == [
        (5815, "String 5815"),
    ]
