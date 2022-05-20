#------------------------------------------------------------------------------
# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
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
#------------------------------------------------------------------------------

"""
1300 - Module for testing cursor variables
"""

import oracledb
import test_env

class TestCase(test_env.BaseTestCase):

    def test_1300_bind_cursor(self):
        "1300 - test binding in a cursor"
        cursor = self.connection.cursor()
        self.assertEqual(cursor.description, None)
        self.cursor.execute("""
                begin
                    open :cursor for select 'X' StringValue from dual;
                end;""",
                cursor=cursor)
        varchar_ratio, nvarchar_ratio = test_env.get_charset_ratios()
        expected_value = [
            ('STRINGVALUE', oracledb.DB_TYPE_CHAR, 1, varchar_ratio, None,
                    None, True)
        ]
        self.assertEqual(cursor.description, expected_value)
        self.assertEqual(cursor.fetchall(), [('X',)])

    def test_1301_bind_cursor_in_package(self):
        "1301 - test binding in a cursor from a package"
        cursor = self.connection.cursor()
        self.assertEqual(cursor.description, None)
        self.cursor.callproc("pkg_TestRefCursors.TestOutCursor", (2, cursor))
        varchar_ratio, nvarchar_ratio = test_env.get_charset_ratios()
        expected_value = [
            ('INTCOL', oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
            ('STRINGCOL', oracledb.DB_TYPE_VARCHAR, 20, 20 * varchar_ratio,
                    None, None, False)
        ]
        self.assertEqual(cursor.description, expected_value)
        self.assertEqual(cursor.fetchall(), [(1, 'String 1'), (2, 'String 2')])

    def test_1302_bind_self(self):
        "1302 - test that binding the cursor itself is not supported"
        cursor = self.connection.cursor()
        sql = """
                begin
                    open :pcursor for
                        select 1 from dual;
                end;"""
        self.assertRaisesRegex(oracledb.NotSupportedError, "^DPY-3009:",
                               cursor.execute, sql, pcursor=cursor)

    def test_1303_execute_after_close(self):
        "1303 - test returning a ref cursor after closing it"
        out_cursor = self.connection.cursor()
        sql = """
                begin
                    open :pcursor for
                        select IntCol
                        from TestNumbers
                        order by IntCol;
                end;"""
        self.cursor.execute(sql, pcursor=out_cursor)
        rows = out_cursor.fetchall()
        out_cursor.close()
        out_cursor = self.connection.cursor()
        self.cursor.execute(sql, pcursor=out_cursor)
        rows2 = out_cursor.fetchall()
        self.assertEqual(rows, rows2)

    def test_1304_fetch_cursor(self):
        "1304 - test fetching a cursor"
        self.cursor.execute("""
                select IntCol, cursor(select IntCol + 1 from dual) CursorValue
                from TestNumbers
                order by IntCol""")
        expected_value = [
            ('INTCOL', oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
            ('CURSORVALUE', oracledb.DB_TYPE_CURSOR, None, None, None, None,
                    True)
        ]
        self.assertEqual(self.cursor.description, expected_value)
        for i in range(1, 11):
            number, cursor = self.cursor.fetchone()
            self.assertEqual(number, i)
            self.assertEqual(cursor.fetchall(), [(i + 1,)])

    def test_1305_ref_cursor_binds(self):
        "1305 - test that ref cursor binds cannot use optimised path"
        ref_cursor = self.connection.cursor()
        sql = """
                begin
                    open :rcursor for
                        select IntCol, StringCol
                        from TestStrings where IntCol
                        between :start_value and :end_value;
                end;"""
        self.cursor.execute(sql, rcursor=ref_cursor, start_value=2,
                            end_value=4)
        expected_value = [
            (2, 'String 2'),
            (3, 'String 3'),
            (4, 'String 4')
        ]
        rows = ref_cursor.fetchall()
        ref_cursor.close()
        self.assertEqual(rows, expected_value)
        ref_cursor = self.connection.cursor()
        self.cursor.execute(sql, rcursor=ref_cursor, start_value=5,
                            end_value=6)
        expected_value = [
            (5, 'String 5'),
            (6, 'String 6')
        ]
        rows = ref_cursor.fetchall()
        self.assertEqual(rows, expected_value)

    def test_1306_refcursor_prefetchrows(self):
        "1306 - test prefetch rows and arraysize using a refcursor"
        self.setup_round_trip_checker()

        # simple DDL only requires a single round trip
        with self.connection.cursor() as cursor:
            cursor.execute("truncate table TestTempTable")
            self.assertRoundTrips(1)

        # array execution only requires a single round trip
        num_rows = 590
        with self.connection.cursor() as cursor:
            sql = "insert into TestTempTable (IntCol) values (:1)"
            data = [(n + 1,) for n in range(num_rows)]
            cursor.executemany(sql, data)
            self.assertRoundTrips(1)

        # create refcursor and execute stored procedure
        with self.connection.cursor() as cursor:
            refcursor = self.connection.cursor()
            refcursor.prefetchrows = 150
            refcursor.arraysize = 50
            cursor.callproc("myrefcursorproc", [refcursor])
            refcursor.fetchall()
            self.assertRoundTrips(4)

    def test_1307_refcursor_execute_different_sql(self):
        "1307 - test executing different SQL after getting a REF cursor"
        with self.connection.cursor() as cursor:
            refcursor = self.connection.cursor()
            cursor.callproc("myrefcursorproc", [refcursor])
            var = cursor.var(int)
            refcursor.execute("begin :1 := 15; end;", [var])
            self.assertEqual(var.getvalue(), 15)

    def test_1308_function_with_ref_cursor_return(self):
        "1308 - test calling a function that returns a REF cursor"
        with self.connection.cursor() as cursor:
            ref_cursor = cursor.callfunc("pkg_TestRefCursors.TestReturnCursor",
                                         oracledb.DB_TYPE_CURSOR, [2])
            rows = ref_cursor.fetchall()
            self.assertEqual(rows, [(1, 'String 1'), (2, 'String 2')])

    def test_1309_output_type_handler_with_ref_cursor(self):
        "1309 - test using an output type handler with a REF cursor"
        def type_handler(cursor, name, default_type, size, precision, scale):
            return cursor.var(str, arraysize=cursor.arraysize)
        self.connection.outputtypehandler = type_handler
        var = self.cursor.var(oracledb.DB_TYPE_CURSOR)
        string_val = "Test String - 1309"
        with self.connection.cursor() as cursor:
            cursor.callproc("pkg_TestRefCursors.TestLobCursor",
                            [string_val, var])
        ref_cursor = var.getvalue()
        self.assertEqual(ref_cursor.fetchall(), [(string_val,)])

    def test_1310_unassigned_ref_cursor(self):
        "1310 - bind a REF cursor but never open it"
        ref_cursor_var = self.cursor.var(oracledb.DB_TYPE_CURSOR)
        self.cursor.execute("""
                begin
                    if false then
                        open :cursor for
                            select user
                            from dual;
                    end if;
                end;""",
                cursor=ref_cursor_var)
        ref_cursor = ref_cursor_var.getvalue()
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-4025:",
                               ref_cursor.fetchall)

    def test_1311_fetch_cursor_uses_custom_class(self):
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
        cursor.execute("""
                select
                    cursor(select 1 from dual),
                    cursor(select 2 from dual)
                from dual""")
        cursor.fetchall()
        self.assertEqual(Counter.num_cursors_created, 3)


if __name__ == "__main__":
    test_env.run_test_cases()
