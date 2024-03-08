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
5800 - Module for testing cursor variables with asyncio
"""

import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    async def test_5800(self):
        "5800 - test binding in a cursor"
        cursor = self.conn.cursor()
        self.assertIsNone(cursor.description)
        await self.cursor.execute(
            """
            begin
                open :cursor for select 'X' StringValue from dual;
            end;
            """,
            cursor=cursor,
        )
        varchar_ratio, _ = await test_env.get_charset_ratios_async()
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
        self.assertEqual(cursor.description, expected_value)
        self.assertEqual(await cursor.fetchall(), [("X",)])

    async def test_5801(self):
        "5801 - test binding in a cursor from a package"
        cursor = self.conn.cursor()
        self.assertIsNone(cursor.description)
        await self.cursor.callproc(
            "pkg_TestRefCursors.TestOutCursor", (2, cursor)
        )
        varchar_ratio, _ = await test_env.get_charset_ratios_async()
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
        self.assertEqual(cursor.description, expected_value)
        self.assertEqual(
            await cursor.fetchall(), [(1, "String 1"), (2, "String 2")]
        )

    async def test_5802(self):
        "5802 - test that binding the cursor itself is not supported"
        cursor = self.conn.cursor()
        sql = """
                begin
                    open :pcursor for
                        select 1 from dual;
                end;"""
        with self.assertRaisesFullCode("DPY-3009"):
            await cursor.execute(sql, pcursor=cursor)

    async def test_5803(self):
        "5803 - test returning a ref cursor after closing it"
        out_cursor = self.conn.cursor()
        sql = """
                begin
                    open :pcursor for
                        select IntCol
                        from TestNumbers
                        order by IntCol;
                end;"""
        await self.cursor.execute(sql, pcursor=out_cursor)
        rows = await out_cursor.fetchall()
        out_cursor.close()
        out_cursor = self.conn.cursor()
        await self.cursor.execute(sql, pcursor=out_cursor)
        rows2 = await out_cursor.fetchall()
        self.assertEqual(rows, rows2)

    async def test_5804(self):
        "5804 - test fetching a cursor"
        await self.cursor.execute(
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
        self.assertEqual(self.cursor.description, expected_value)
        for i in range(1, 11):
            number, cursor = await self.cursor.fetchone()
            self.assertEqual(number, i)
            self.assertEqual(await cursor.fetchall(), [(i + 1,)])

    async def test_5805(self):
        "5805 - test that ref cursor binds cannot use optimised path"
        ref_cursor = self.conn.cursor()
        sql = """
                begin
                    open :rcursor for
                        select IntCol, StringCol
                        from TestStrings where IntCol
                        between :start_value and :end_value;
                end;"""
        expected_value = [(2, "String 2"), (3, "String 3"), (4, "String 4")]
        await self.cursor.execute(
            sql, rcursor=ref_cursor, start_value=2, end_value=4
        )
        self.assertEqual(await ref_cursor.fetchall(), expected_value)
        ref_cursor.close()

        expected_value = [(5, "String 5"), (6, "String 6")]
        ref_cursor = self.conn.cursor()
        await self.cursor.execute(
            sql, rcursor=ref_cursor, start_value=5, end_value=6
        )
        self.assertEqual(await ref_cursor.fetchall(), expected_value)

    async def test_5806(self):
        "5806 - test round trips using a REF cursor"
        await self.setup_round_trip_checker()

        # simple DDL only requires a single round trip
        with self.conn.cursor() as cursor:
            await cursor.execute("truncate table TestTempTable")
            await self.assertRoundTrips(1)

        # array execution only requires a single round trip
        num_rows = 590
        with self.conn.cursor() as cursor:
            sql = "insert into TestTempTable (IntCol) values (:1)"
            data = [(n + 1,) for n in range(num_rows)]
            await cursor.executemany(sql, data)
            await self.assertRoundTrips(1)

        # create REF cursor and execute stored procedure
        # (array size set before procedure is called)
        with self.conn.cursor() as cursor:
            refcursor = self.conn.cursor()
            refcursor.arraysize = 150
            await cursor.callproc("myrefcursorproc", [refcursor])
            await refcursor.fetchall()
            await self.assertRoundTrips(5)

        # create REF cursor and execute stored procedure
        # (array size set after procedure is called)
        with self.conn.cursor() as cursor:
            refcursor = self.conn.cursor()
            await cursor.callproc("myrefcursorproc", [refcursor])
            refcursor.arraysize = 145
            await refcursor.fetchall()
            await self.assertRoundTrips(6)

    async def test_5807(self):
        "5807 - test executing different SQL after getting a REF cursor"
        with self.conn.cursor() as cursor:
            refcursor = self.conn.cursor()
            await cursor.callproc("myrefcursorproc", [refcursor])
            var = cursor.var(int)
            await refcursor.execute("begin :1 := 15; end;", [var])
            self.assertEqual(var.getvalue(), 15)

    async def test_5808(self):
        "5808 - test calling a function that returns a REF cursor"
        with self.conn.cursor() as cursor:
            ref_cursor = await cursor.callfunc(
                "pkg_TestRefCursors.TestReturnCursor",
                oracledb.DB_TYPE_CURSOR,
                [2],
            )
            self.assertEqual(
                await ref_cursor.fetchall(), [(1, "String 1"), (2, "String 2")]
            )

    async def test_5809(self):
        "5809 - test using an output type handler with a REF cursor"

        def type_handler(cursor, metadata):
            return cursor.var(str, arraysize=cursor.arraysize)

        self.conn.outputtypehandler = type_handler
        var = self.cursor.var(oracledb.DB_TYPE_CURSOR)
        string_val = "Test String - 5809"
        with self.conn.cursor() as cursor:
            await cursor.callproc(
                "pkg_TestRefCursors.TestLobCursor", [string_val, var]
            )
        ref_cursor = var.getvalue()
        self.assertEqual(await ref_cursor.fetchall(), [(string_val,)])

    async def test_5810(self):
        "5810 - bind a REF cursor but never open it"
        ref_cursor_var = self.cursor.var(oracledb.DB_TYPE_CURSOR)
        await self.cursor.execute(
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
            with self.assertRaisesFullCode("DPY-4025"):
                await ref_cursor.fetchall()

    async def test_5811(self):
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
        self.assertEqual(Counter.num_cursors_created, 3)

    async def test_5812(self):
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
        await self.cursor.execute(sql)

        async def transform_row(r):
            return tuple([await transform_fn(v) for v in r])

        async def transform_fn(v):
            if isinstance(v, oracledb.AsyncCursor):
                return [await transform_row(r) async for r in v]
            return v

        rows = [await transform_row(r) async for r in self.cursor]
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
        self.assertEqual(rows, expected_value)

    async def test_5813(self):
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
        await self.cursor.execute(sql)

        async def transform_row(r):
            return tuple([await transform_fn(v) for v in r])

        async def transform_fn(v):
            if isinstance(v, oracledb.AsyncCursor):
                return [await transform_row(r) async for r in v]
            return v

        rows = [await transform_row(r) async for r in self.cursor]
        expected_value = [
            (
                "Top Level String",
                [("Nested String 1", "Nested String 2", "Nested String 3")],
            )
        ]
        self.assertEqual(rows, expected_value)

    async def test_5814(self):
        "5814 - test reusing a closed ref cursor for executing different sql"
        sql = "select 58141, 'String 58141' from dual"
        ref_cursor = self.conn.cursor()
        ref_cursor.prefetchrows = 0
        await ref_cursor.execute(sql)
        plsql = "begin pkg_TestRefCursors.TestCloseCursor(:rcursor); end;"
        await self.cursor.execute(plsql, rcursor=ref_cursor)
        sql = "select 58142, 'String 58142' from dual"
        await ref_cursor.execute(sql)
        self.assertEqual(
            await ref_cursor.fetchall(),
            [
                (58142, "String 58142"),
            ],
        )

    async def test_5815(self):
        "5815 - test reusing a closed ref cursor for executing same sql"
        sql = "select 5815, 'String 5815' from dual"
        ref_cursor = self.conn.cursor()
        ref_cursor.prefetchrows = 0
        await ref_cursor.execute(sql)
        plsql = "begin pkg_TestRefCursors.TestCloseCursor(:rcursor); end;"
        await self.cursor.execute(plsql, rcursor=ref_cursor)
        await ref_cursor.execute(sql)
        self.assertEqual(
            await ref_cursor.fetchall(),
            [
                (5815, "String 5815"),
            ],
        )


if __name__ == "__main__":
    test_env.run_test_cases()
