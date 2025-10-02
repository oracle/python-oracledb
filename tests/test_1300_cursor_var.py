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
1300 - Module for testing cursor variables
"""

import oracledb


def test_1300(conn, test_env):
    "1300 - test binding in a cursor"
    ref_cursor = conn.cursor()
    assert ref_cursor.description is None
    cursor = conn.cursor()
    cursor.execute(
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
    assert ref_cursor.fetchall() == [("X",)]


def test_1301(conn, test_env):
    "1301 - test binding in a cursor from a package"
    ref_cursor = conn.cursor()
    assert ref_cursor.description is None
    cursor = conn.cursor()
    cursor.callproc("pkg_TestRefCursors.TestOutCursor", (2, ref_cursor))
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
    assert ref_cursor.fetchall() == [(1, "String 1"), (2, "String 2")]


def test_1302(conn, test_env):
    "1302 - test that binding the cursor itself is not supported"
    cursor = conn.cursor()
    sql = """
            begin
                open :pcursor for
                    select 1 from dual;
            end;"""
    with test_env.assert_raises_full_code("DPY-3009"):
        cursor.execute(sql, pcursor=cursor)


def test_1303(conn):
    "1303 - test returning a ref cursor after closing it"
    out_cursor = conn.cursor()
    sql = """
            begin
                open :pcursor for
                    select IntCol
                    from TestNumbers
                    order by IntCol;
            end;"""
    cursor = conn.cursor()
    cursor.execute(sql, pcursor=out_cursor)
    rows = out_cursor.fetchall()
    out_cursor.close()
    out_cursor = conn.cursor()
    cursor.execute(sql, pcursor=out_cursor)
    rows2 = out_cursor.fetchall()
    assert rows == rows2


def test_1304(conn):
    "1304 - test fetching a cursor"
    cursor = conn.cursor()
    cursor.execute(
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
    assert cursor.description == expected_value
    for i in range(1, 11):
        number, child_cursor = cursor.fetchone()
        assert number == i
        assert child_cursor.fetchall() == [(i + 1,)]


def test_1305(conn):
    "1305 - test that ref cursor binds cannot use optimised path"
    ref_cursor = conn.cursor()
    sql = """
            begin
                open :rcursor for
                    select IntCol, StringCol
                    from TestStrings where IntCol
                    between :start_value and :end_value;
            end;"""
    expected_value = [(2, "String 2"), (3, "String 3"), (4, "String 4")]
    cursor = conn.cursor()
    cursor.execute(sql, rcursor=ref_cursor, start_value=2, end_value=4)
    assert ref_cursor.fetchall() == expected_value
    ref_cursor.close()

    expected_value = [(5, "String 5"), (6, "String 6")]
    ref_cursor = conn.cursor()
    cursor.execute(sql, rcursor=ref_cursor, start_value=5, end_value=6)
    assert ref_cursor.fetchall() == expected_value


def test_1306(conn, round_trip_checker):
    "1306 - test round trips using a REF cursor"

    # simple DDL only requires a single round trip
    with conn.cursor() as cursor:
        cursor.execute("truncate table TestTempTable")
        assert round_trip_checker.get_value() == 1

    # array execution only requires a single round trip
    num_rows = 590
    with conn.cursor() as cursor:
        sql = "insert into TestTempTable (IntCol) values (:1)"
        data = [(n + 1,) for n in range(num_rows)]
        cursor.executemany(sql, data)
        assert round_trip_checker.get_value() == 1

    # create REF cursor and execute stored procedure
    # (array size set before procedure is called)
    with conn.cursor() as cursor:
        refcursor = conn.cursor()
        refcursor.arraysize = 150
        cursor.callproc("myrefcursorproc", [refcursor])
        refcursor.fetchall()
        assert round_trip_checker.get_value() == 5

    # create REF cursor and execute stored procedure
    # (array size set after procedure is called)
    with conn.cursor() as cursor:
        refcursor = conn.cursor()
        cursor.callproc("myrefcursorproc", [refcursor])
        refcursor.arraysize = 145
        refcursor.fetchall()
        assert round_trip_checker.get_value() == 6


def test_1307(conn):
    "1307 - test executing different SQL after getting a REF cursor"
    with conn.cursor() as cursor:
        refcursor = conn.cursor()
        cursor.callproc("myrefcursorproc", [refcursor])
        var = cursor.var(int)
        refcursor.execute("begin :1 := 15; end;", [var])
        assert var.getvalue() == 15


def test_1308(conn):
    "1308 - test calling a function that returns a REF cursor"
    with conn.cursor() as cursor:
        ref_cursor = cursor.callfunc(
            "pkg_TestRefCursors.TestReturnCursor",
            oracledb.DB_TYPE_CURSOR,
            [2],
        )
        assert ref_cursor.fetchall() == [(1, "String 1"), (2, "String 2")]


def test_1309(conn):
    "1309 - test using an output type handler with a REF cursor"

    def type_handler(cursor, metadata):
        return cursor.var(str, arraysize=cursor.arraysize)

    conn.outputtypehandler = type_handler
    var = conn.cursor().var(oracledb.DB_TYPE_CURSOR)
    string_val = "Test String - 1309"
    with conn.cursor() as cursor:
        cursor.callproc("pkg_TestRefCursors.TestLobCursor", [string_val, var])
    ref_cursor = var.getvalue()
    assert ref_cursor.fetchall() == [(string_val,)]
    assert var.getvalue() is ref_cursor


def test_1310(conn, test_env):
    "1310 - bind a REF cursor but never open it"
    cursor = conn.cursor()
    ref_cursor_var = cursor.var(oracledb.DB_TYPE_CURSOR)
    cursor.execute(
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
            ref_cursor.fetchall()


def test_1311(test_env):
    "1311 - test fetching a cursor with a custom class"

    class Counter:
        num_cursors_created = 0

        @classmethod
        def cursor_created(cls):
            cls.num_cursors_created += 1

    class MyConnection(oracledb.Connection):
        def cursor(self):
            Counter.cursor_created()
            return super().cursor()

    conn = test_env.get_connection(conn_class=MyConnection)
    cursor = conn.cursor()
    cursor.execute(
        """
        select
            cursor(select 1 from dual),
            cursor(select 2 from dual)
        from dual
        """
    )
    cursor.fetchall()
    assert Counter.num_cursors_created == 3


def test_1312(conn):
    "1312 - test that nested cursors are fetched correctly"
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
    cursor = conn.cursor()
    cursor.execute(sql)

    def transform_row(r):
        return tuple(transform_fn(v) for v in r)

    def transform_fn(v):
        if isinstance(v, oracledb.Cursor):
            return [transform_row(r) for r in v]
        return v

    rows = [transform_row(r) for r in cursor]
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


def test_1313(conn):
    "1313 - test fetching nested cursors with more columns than parent"
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
    cursor = conn.cursor()
    cursor.execute(sql)

    def transform_row(r):
        return tuple(transform_fn(v) for v in r)

    def transform_fn(v):
        if isinstance(v, oracledb.Cursor):
            return [transform_row(r) for r in v]
        return v

    rows = [transform_row(r) for r in cursor]
    expected_value = [
        (
            "Top Level String",
            [("Nested String 1", "Nested String 2", "Nested String 3")],
        )
    ]
    assert rows == expected_value


def test_1314(conn):
    "1314 - test reusing a closed ref cursor for executing different sql"
    sql = "select 13141, 'String 13141' from dual"
    ref_cursor = conn.cursor()
    ref_cursor.prefetchrows = 0
    ref_cursor.execute(sql)
    plsql = "begin pkg_TestRefCursors.TestCloseCursor(:rcursor); end;"
    cursor = conn.cursor()
    cursor.execute(plsql, rcursor=ref_cursor)
    sql = "select 13142, 'String 13142' from dual"
    ref_cursor.execute(sql)
    assert ref_cursor.fetchall() == [(13142, "String 13142")]


def test_1315(conn):
    "1315 - test reusing a closed ref cursor for executing same sql"
    sql = "select 1315, 'String 1315' from dual"
    ref_cursor = conn.cursor()
    ref_cursor.prefetchrows = 0
    ref_cursor.execute(sql)
    plsql = "begin pkg_TestRefCursors.TestCloseCursor(:rcursor); end;"
    cursor = conn.cursor()
    cursor.execute(plsql, rcursor=ref_cursor)
    ref_cursor.execute(sql)
    assert ref_cursor.fetchall() == [(1315, "String 1315")]


def test_1316(conn, test_env):
    "1316 - test using a closed ref cursor for OUT bind"
    value = "test 1316a"
    sql = """
        declare
            t_Cursor sys_refcursor;
        begin
            open t_Cursor for
                select :value
                from dual;
            :cursor := t_Cursor;
        end;
    """
    cursor = conn.cursor()
    var = cursor.var(oracledb.DB_TYPE_CURSOR)
    cursor.execute(sql, [value, var])
    ref_cursor = var.getvalue()
    assert ref_cursor.fetchall() == [(value,)]
    ref_cursor.close()
    with test_env.assert_raises_full_code("DPY-1006"):
        cursor.execute(sql, [value, var])


def test_1317(conn, cursor, test_env):
    "1317 - test binding a closed cursor"
    ref_cursor = conn.cursor()
    ref_cursor.close()
    with test_env.assert_raises_full_code("DPY-1006"):
        cursor.callfunc("pkg_testRefCursors.TestInCursor", str, [ref_cursor])


def test_1318(test_env):
    "1318 - test ref cursor doesn't work after connection is closed"
    conn = test_env.get_connection()
    cursor = conn.cursor()
    var = cursor.var(oracledb.DB_TYPE_CURSOR)
    cursor.callproc("myrefcursorproc", [var])
    conn.close()
    with test_env.assert_raises_full_code("DPY-1001"):
        ref_cursor = var.getvalue()
        ref_cursor.fetchall()


def test_1319(cursor, test_env):
    "1319 - test binding cursor that is not from the same connection"
    sql = """
        declare
            t_Cursor sys_refcursor;
        begin
            open t_Cursor for
                select 1319
                from dual;
            :cursor := t_Cursor;
        end;
    """
    ref_cursor = test_env.get_connection().cursor()
    with test_env.assert_raises_full_code("DPY-3027"):
        cursor.execute(sql, [ref_cursor])


def test_1320(conn):
    "1320 - test fetching nested cursors repeatedly"
    sql = """
        select
            s.Description,
            cursor(select 'Nested String for ' || s.Description from dual)
        from
            (
                select 'Top Level String 1' as Description
                from dual
                union all
                select 'Top Level String 2'
                from dual
                union all
                select 'Top Level String 3'
                from dual
                union all
                select 'Top Level String 4'
                from dual
                union all
                select 'Top Level String 5'
                from dual
            ) s"""

    for i in range(3):
        with conn.cursor() as cursor:
            cursor.arraysize = 10
            cursor.execute(sql)
            desc, nested1 = cursor.fetchone()
            assert desc == "Top Level String 1"
            nested_rows = nested1.fetchall()
            assert nested_rows == [("Nested String for Top Level String 1",)]
            desc, nested2 = cursor.fetchone()
            assert desc == "Top Level String 2"
            nested_rows = nested2.fetchall()
            assert nested_rows == [("Nested String for Top Level String 2",)]
