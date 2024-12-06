# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
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
4300 - Module for testing other cursor methods and attributes.
"""

import decimal
import unittest

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    def test_4300(self):
        "4300 - test preparing a statement and executing it multiple times"
        cursor = self.conn.cursor()
        self.assertEqual(cursor.statement, None)
        statement = "begin :value := :value + 5; end;"
        cursor.prepare(statement)
        var = cursor.var(oracledb.NUMBER)
        self.assertEqual(cursor.statement, statement)
        var.setvalue(0, 2)
        cursor.execute(None, value=var)
        self.assertEqual(var.getvalue(), 7)
        cursor.execute(None, value=var)
        self.assertEqual(var.getvalue(), 12)
        cursor.execute("begin :value2 := 3; end;", value2=var)
        self.assertEqual(var.getvalue(), 3)

    def test_4301(self):
        "4301 - confirm an exception is raised after closing a cursor"
        self.cursor.close()
        with self.assertRaisesFullCode("DPY-1006"):
            self.cursor.execute("select 1 from dual")

    def test_4302(self):
        "4302 - test iterators"
        self.cursor.execute(
            """
            select IntCol
            from TestNumbers
            where IntCol between 1 and 3
            order by IntCol
            """
        )
        rows = [v for v, in self.cursor]
        self.assertEqual(rows, [1, 2, 3])

    def test_4303(self):
        "4303 - test iterators (with intermediate execute)"
        self.cursor.execute("truncate table TestTempTable")
        self.cursor.execute(
            """
            select IntCol
            from TestNumbers
            where IntCol between 1 and 3
            order by IntCol
            """
        )
        test_iter = iter(self.cursor)
        (value,) = next(test_iter)
        self.cursor.execute("insert into TestTempTable (IntCol) values (1)")
        with self.assertRaisesFullCode("DPY-1003"):
            next(test_iter)

    def test_4304(self):
        "4304 - test that bindnames() works correctly."
        cursor = self.conn.cursor()
        with self.assertRaisesFullCode("DPY-2002"):
            cursor.bindnames()
        cursor.prepare("begin null; end;")
        self.assertEqual(cursor.bindnames(), [])
        cursor.prepare("begin :retval := :inval + 5; end;")
        self.assertEqual(cursor.bindnames(), ["RETVAL", "INVAL"])
        cursor.prepare("begin :retval := :a * :a + :b * :b; end;")
        self.assertEqual(cursor.bindnames(), ["RETVAL", "A", "B"])
        cursor.prepare(
            """
            begin
                :a := :b + :c + :d + :e + :f + :g + :h + :i + :j + :k + :l;
            end;
            """
        )
        names = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]
        self.assertEqual(cursor.bindnames(), names)
        cursor.prepare("select :a * :a + :b * :b from dual")
        self.assertEqual(cursor.bindnames(), ["A", "B"])
        cursor.prepare("select :value1 + :VaLue_2 from dual")
        self.assertEqual(cursor.bindnames(), ["VALUE1", "VALUE_2"])
        cursor.prepare("select :élevé, :fenêtre from dual")
        self.assertEqual(cursor.bindnames(), ["ÉLEVÉ", "FENÊTRE"])

    def test_4305(self):
        "4305 - test cursor.setinputsizes() with invalid parameters"
        val = decimal.Decimal(5)
        with self.assertRaisesFullCode("DPY-2005"):
            self.cursor.setinputsizes(val, x=val)
        with self.assertRaisesFullCode("DPY-2007"):
            self.cursor.setinputsizes(val)

    def test_4306(self):
        "4306 - test setting input sizes without any parameters"
        self.cursor.setinputsizes()
        self.cursor.execute("select :val from dual", val="Test Value")
        self.assertEqual(self.cursor.fetchall(), [("Test Value",)])

    def test_4307(self):
        "4307 - test setting input sizes with an empty dictionary"
        empty_dict = {}
        self.cursor.prepare("select 236 from dual")
        self.cursor.setinputsizes(**empty_dict)
        self.cursor.execute(None, empty_dict)
        self.assertEqual(self.cursor.fetchall(), [(236,)])

    def test_4308(self):
        "4308 - test setting input sizes with an empty list"
        empty_list = []
        self.cursor.prepare("select 239 from dual")
        self.cursor.setinputsizes(*empty_list)
        self.cursor.execute(None, empty_list)
        self.assertEqual(self.cursor.fetchall(), [(239,)])

    def test_4309(self):
        "4309 - test setting input sizes with positional args"
        var = self.cursor.var(oracledb.STRING, 100)
        self.cursor.setinputsizes(None, 5, None, 10, None, oracledb.NUMBER)
        self.cursor.execute(
            """
            begin
              :1 := :2 || to_char(:3) || :4 || to_char(:5) || to_char(:6);
            end;
            """,
            [var, "test_", 5, "_second_", 3, 7],
        )
        self.assertEqual(var.getvalue(), "test_5_second_37")

    def test_4310(self):
        "4310 - test Cursor repr()"
        expected_value = f"<oracledb.Cursor on {self.conn}>"
        self.assertEqual(str(self.cursor), expected_value)
        self.assertEqual(repr(self.cursor), expected_value)

    def test_4311(self):
        "4311 - test parsing query statements"
        sql = "select LongIntCol from TestNumbers where IntCol = :val"
        self.cursor.parse(sql)
        self.assertEqual(self.cursor.statement, sql)
        self.assertEqual(
            self.cursor.description,
            [("LONGINTCOL", oracledb.DB_TYPE_NUMBER, 17, None, 16, 0, 0)],
        )

    def test_4312(self):
        "4312 - test cursor.setoutputsize() does not fail (but does nothing)"
        self.cursor.setoutputsize(100, 2)

    def test_4313(self):
        "4313 - test cursor.var() with invalid parameters"
        with self.assertRaisesFullCode("DPY-2007"):
            self.cursor.var(5)

    def test_4314(self):
        "4314 - test cursor.arrayvar() with invalid parameters"
        with self.assertRaisesFullCode("DPY-2007"):
            self.cursor.arrayvar(5, 1)

    def test_4315(self):
        "4315 - test binding boolean data without the use of PL/SQL"
        self.cursor.execute("truncate table TestTempTable")
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        self.cursor.execute(sql, (False, "Value should be 0"))
        self.cursor.execute(sql, (True, "Value should be 1"))
        self.cursor.execute(
            "select IntCol, StringCol1 from TestTempTable order by IntCol"
        )
        expected_value = [(0, "Value should be 0"), (1, "Value should be 1")]
        self.assertEqual(self.cursor.fetchall(), expected_value)

    def test_4316(self):
        "4316 - test using a cursor as a context manager"
        with self.cursor as cursor:
            cursor.execute("truncate table TestTempTable")
            cursor.execute("select count(*) from TestTempTable")
            (count,) = cursor.fetchone()
            self.assertEqual(count, 0)
        with self.assertRaisesFullCode("DPY-1006"):
            self.cursor.close()

    def test_4317(self):
        "4317 - test that rowcount attribute is reset to zero on query execute"
        for num in [0, 1, 1, 0]:
            self.cursor.execute("select * from dual where 1 = :s", [num])
            self.cursor.fetchone()
            self.assertEqual(self.cursor.rowcount, num)

    def test_4318(self):
        "4318 - test that the typename attribute can be passed a value of None"
        value_to_set = 5
        var = self.cursor.var(int, typename=None)
        var.setvalue(0, value_to_set)
        self.assertEqual(var.getvalue(), value_to_set)

    def test_4319(self):
        "4319 - test that an object type can be used as type in cursor.var()"
        obj_type = self.conn.gettype("UDT_OBJECT")
        var = self.cursor.var(obj_type)
        self.cursor.callproc(
            "pkg_TestBindObject.BindObjectOut", (28, "Bind obj out", var)
        )
        obj = var.getvalue()
        result = self.cursor.callfunc(
            "pkg_TestBindObject.GetStringRep", str, (obj,)
        )
        exp = "udt_Object(28, 'Bind obj out', null, null, null, null, null)"
        self.assertEqual(result, exp)

    def test_4320(self):
        "4320 - test that fetching an XMLType returns a string"
        int_val = 5
        label = "IntCol"
        expected_result = f"<{label}>{int_val}</{label}>"
        self.cursor.execute(
            f"""
            select XMLElement("{label}", IntCol)
            from TestStrings
            where IntCol = :int_val
            """,
            int_val=int_val,
        )
        (result,) = self.cursor.fetchone()
        self.assertEqual(result, expected_result)

    def test_4321(self):
        "4321 - test last rowid"

        # no statement executed: no rowid
        self.assertIsNone(self.cursor.lastrowid)

        # DDL statement executed: no rowid
        self.cursor.execute("truncate table TestTempTable")
        self.assertIsNone(self.cursor.lastrowid)

        # statement prepared: no rowid
        self.cursor.prepare("insert into TestTempTable (IntCol) values (:1)")
        self.assertIsNone(self.cursor.lastrowid)

        # multiple rows inserted: rowid of last row inserted
        rows = [(n,) for n in range(225)]
        self.cursor.executemany(None, rows)
        rowid = self.cursor.lastrowid
        self.cursor.execute(
            """
            select rowid
            from TestTempTable
            where IntCol = :1
            """,
            rows[-1],
        )
        self.assertEqual(self.cursor.fetchone()[0], rowid)

        # statement executed but no rows updated: no rowid
        self.cursor.execute("delete from TestTempTable where 1 = 0")
        self.assertIsNone(self.cursor.lastrowid)

        # stetement executed with one row updated: rowid of updated row
        self.cursor.execute(
            """
            update TestTempTable set StringCol1 = 'Modified'
            where IntCol = :1
            """,
            rows[-2],
        )
        rowid = self.cursor.lastrowid
        self.cursor.execute(
            "select rowid from TestTempTable where IntCol = :1",
            rows[-2],
        )
        self.assertEqual(self.cursor.fetchone()[0], rowid)

        # statement executed with many rows updated: rowid of last updated row
        self.cursor.execute(
            """
            update TestTempTable set
                StringCol1 = 'Row ' || to_char(IntCol)
            where IntCol = :1
            """,
            rows[-3],
        )
        rowid = self.cursor.lastrowid
        self.cursor.execute(
            "select StringCol1 from TestTempTable where rowid = :1",
            [rowid],
        )
        self.assertEqual(self.cursor.fetchone()[0], "Row %s" % rows[-3])

    def test_4322(self):
        "4322 - test prefetch rows"
        self.setup_round_trip_checker()

        # perform simple query and verify only one round trip is needed
        with self.conn.cursor() as cursor:
            cursor.execute("select sysdate from dual").fetchall()
            self.assertRoundTrips(1)

        # set prefetchrows to 1 and verify that two round trips are now needed
        with self.conn.cursor() as cursor:
            cursor.prefetchrows = 1
            self.assertEqual(cursor.prefetchrows, 1)
            cursor.execute("select sysdate from dual").fetchall()
            self.assertRoundTrips(2)

        # simple DDL only requires a single round trip
        with self.conn.cursor() as cursor:
            cursor.execute("truncate table TestTempTable")
            self.assertRoundTrips(1)

        # array execution only requires a single round trip
        num_rows = 590
        with self.conn.cursor() as cursor:
            data = [(n + 1,) for n in range(num_rows)]
            cursor.executemany(
                "insert into TestTempTable (IntCol) values (:1)",
                data,
            )
            self.assertRoundTrips(1)

        # setting prefetch and array size to 1 requires a round-trip for each
        # row
        with self.conn.cursor() as cursor:
            cursor.arraysize = 1
            cursor.prefetchrows = 1
            self.assertEqual(cursor.prefetchrows, 1)
            cursor.execute("select IntCol from TestTempTable").fetchall()
            self.assertRoundTrips(num_rows + 1)

        # setting prefetch and array size to 300 requires 2 round-trips
        with self.conn.cursor() as cursor:
            cursor.arraysize = 300
            cursor.prefetchrows = 300
            self.assertEqual(cursor.prefetchrows, 300)
            cursor.execute("select IntCol from TestTempTable").fetchall()
            self.assertRoundTrips(2)

    def test_4323(self):
        "4323 - test prefetch rows using existing cursor"
        self.setup_round_trip_checker()

        # Set prefetch rows on an existing cursor
        num_rows = 590
        with self.conn.cursor() as cursor:
            cursor.execute("truncate table TestTempTable")
            self.assertRoundTrips(1)
            data = [(n + 1,) for n in range(num_rows)]
            cursor.executemany(
                "insert into TestTempTable (IntCol) values (:1)",
                data,
            )
            self.assertRoundTrips(1)
            cursor.prefetchrows = 30
            cursor.arraysize = 100
            cursor.execute("select IntCol from TestTempTable").fetchall()
            self.assertRoundTrips(7)

    def test_4324(self):
        "4324 - test parsing plsql statements"
        sql = "begin :value := 5; end;"
        self.cursor.parse(sql)
        self.assertEqual(self.cursor.statement, sql)
        self.assertIsNone(self.cursor.description)

    def test_4325(self):
        "4325 - test parsing ddl statements"
        sql = "truncate table TestTempTable"
        self.cursor.parse(sql)
        self.assertEqual(self.cursor.statement, sql)
        self.assertIsNone(self.cursor.description)

    def test_4326(self):
        "4326 - test parsing dml statements"
        sql = "insert into TestTempTable (IntCol) values (1)"
        self.cursor.parse(sql)
        self.assertEqual(self.cursor.statement, sql)
        self.assertIsNone(self.cursor.description)

    def test_4327(self):
        "4327 - test to verify encodingErrors is deprecated"
        errors = "strict"
        with self.assertRaisesFullCode("DPY-2014"):
            self.cursor.var(
                oracledb.NUMBER, encoding_errors=errors, encodingErrors=errors
            )

    def test_4328(self):
        "4328 - test arrays of arrays not supported"
        simple_var = self.cursor.arrayvar(oracledb.NUMBER, 3)
        with self.assertRaisesFullCode("DPY-3005"):
            simple_var.setvalue(1, [1, 2, 3])

    def test_4329(self):
        "4329 - test cursor.setinputsizes() with invalid list parameters"
        with self.assertRaisesFullCode("DPY-2011"):
            self.cursor.setinputsizes([int, 2, 10])

    def test_4330(self):
        "4330 - test unsupported python type on cursor"
        with self.assertRaisesFullCode("DPY-3003"):
            self.cursor.var(list)

    def test_4331(self):
        "4331 - test binding by name with leading colon"
        params = {":arg1": 5}
        self.cursor.execute("select :arg1 from dual", params)
        (result,) = self.cursor.fetchone()
        self.assertEqual(result, params[":arg1"])

    def test_4332(self):
        "4332 - test binding mixed null and not null values in a PL/SQL block"
        out_vars = [self.cursor.var(str) for i in range(4)]
        self.cursor.execute(
            """
            begin
                :1 := null;
                :2 := 'Value 1';
                :3 := null;
                :4 := 'Value 2';
            end;
            """,
            out_vars,
        )
        values = [var.getvalue() for var in out_vars]
        self.assertEqual(values, [None, "Value 1", None, "Value 2"])

    def test_4333(self):
        "4333 - test excluding statement from statement cache"
        num_iters = 10
        sql = "select user from dual"
        self.setup_parse_count_checker()

        # with statement cache enabled, only one parse should take place
        for i in range(num_iters):
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
        self.assertParseCount(1)

        # with statement cache disabled for the statement, parse count should
        # be the same as the number of iterations
        for i in range(num_iters):
            with self.conn.cursor() as cursor:
                cursor.prepare(sql, cache_statement=False)
                cursor.execute(None)
        self.assertParseCount(num_iters - 1)

    def test_4334(self):
        "4334 - test repeated DDL"
        self.cursor.execute("truncate table TestTempTable")
        self.cursor.execute("insert into TestTempTable (IntCol) values (1)")
        self.cursor.execute("truncate table TestTempTable")
        self.cursor.execute("insert into TestTempTable (IntCol) values (1)")

    def test_4335(self):
        "4335 - test executing SQL with non-ASCII characters"
        self.cursor.execute("select 'FÖÖ' from dual")
        (result,) = self.cursor.fetchone()
        self.assertIn(result, ("FÖÖ", "F¿¿"))

    def test_4336(self):
        "4336 - test case sensitivity of unquoted bind names"
        self.cursor.execute("select :test from dual", {"TEST": "a"})
        (result,) = self.cursor.fetchone()
        self.assertEqual(result, "a")

    def test_4337(self):
        "4337 - test case sensitivity of quoted bind names"
        with self.assertRaisesFullCode("ORA-01036", "DPY-4008"):
            self.cursor.execute('select :"test" from dual', {'"TEST"': "a"})

    def test_4338(self):
        "4338 - test using a reserved keywords as a bind name"
        sql = "select :ROWID from dual"
        with self.assertRaisesFullCode("ORA-01745"):
            self.cursor.parse(sql)

    def test_4339(self):
        "4339 - test array size less than prefetch rows"
        for i in range(2):
            with self.conn.cursor() as cursor:
                cursor.arraysize = 1
                cursor.execute("select 1 from dual union select 2 from dual")
                self.assertEqual(cursor.fetchall(), [(1,), (2,)])

    def test_4340(self):
        "4340 - test re-executing a query with blob as bytes"

        def type_handler(cursor, metadata):
            if metadata.type_code is oracledb.DB_TYPE_BLOB:
                return cursor.var(bytes, arraysize=cursor.arraysize)

        self.conn.outputtypehandler = type_handler
        blob_data = b"An arbitrary set of blob data for test case 4348"
        self.cursor.execute("delete from TestBLOBs")
        self.cursor.execute(
            "insert into TestBLOBs (IntCol, BlobCol) values (1, :data)",
            [blob_data],
        )
        self.cursor.execute("select IntCol, BlobCol from TestBLOBs")
        self.assertEqual(self.cursor.fetchall(), [(1, blob_data)])

        self.cursor.execute("delete from TestBLOBs")
        self.cursor.execute(
            "insert into TestBLOBs (IntCol, BlobCol) values (1, :data)",
            [blob_data],
        )
        self.cursor.execute("select IntCol, BlobCol from TestBLOBs")
        self.assertEqual(self.cursor.fetchall(), [(1, blob_data)])

    def test_4341(self):
        "4341 - test re-executing a statement after raising an error"
        sql = "select * from TestFakeTable"
        with self.assertRaisesFullCode("ORA-00942"):
            self.cursor.execute(sql)
        with self.assertRaisesFullCode("ORA-00942"):
            self.cursor.execute(sql)

        sql = "insert into TestStrings (StringCol) values (NULL)"
        with self.assertRaisesFullCode("ORA-01400"):
            self.cursor.execute(sql)
        with self.assertRaisesFullCode("ORA-01400"):
            self.cursor.execute(sql)

    def test_4342(self):
        "4342 - test executing a statement that raises ORA-01007"
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                create or replace view ora_1007 as
                    select 1 as SampleNumber, 'String' as SampleString,
                        'Another String' as AnotherString
                    from dual
                """
            )
        with self.conn.cursor() as cursor:
            cursor.execute("select * from ora_1007")
            self.assertEqual(
                cursor.fetchone(), (1, "String", "Another String")
            )
        with self.conn.cursor() as cursor:
            cursor.execute(
                """
                create or replace view ora_1007 as
                    select 1 as SampleNumber,
                        'Another String' as AnotherString
                    from dual
                """
            )
        with self.conn.cursor() as cursor:
            cursor.execute("select * from ora_1007")
            self.assertEqual(cursor.fetchone(), (1, "Another String"))

    def test_4343(self):
        "4343 - test updating an empty row"
        int_var = self.cursor.var(int)
        self.cursor.execute("truncate table TestTempTable")
        self.cursor.execute(
            """
            begin
                update TestTempTable set IntCol = :1
                where StringCol1 = :2
                returning IntCol into :3;
            end;
            """,
            [1, "test string 4352", int_var],
        )
        self.assertEqual(int_var.values, [None])

    def test_4344(self):
        "4344 - fetch duplicate data from query in statement cache"
        sql = """
                select 'A', 'B', 'C' from dual
                union all
                select 'A', 'B', 'C' from dual
                union all
                select 'A', 'B', 'C' from dual"""
        expected_data = [("A", "B", "C")] * 3
        with self.conn.cursor() as cursor:
            cursor.prefetchrows = 0
            cursor.execute(sql)
            self.assertEqual(cursor.fetchall(), expected_data)
        with self.conn.cursor() as cursor:
            cursor.prefetchrows = 0
            cursor.execute(sql)
            self.assertEqual(cursor.fetchall(), expected_data)

    def test_4345(self):
        "4345 - fetch duplicate data with outconverter"

        def out_converter(value):
            self.assertIs(type(value), str)
            return int(value)

        def type_handler(cursor, metadata):
            if metadata.name == "COL_3":
                return cursor.var(
                    str, arraysize=cursor.arraysize, outconverter=out_converter
                )

        self.cursor.outputtypehandler = type_handler
        self.cursor.execute(
            """
            select 'A' as col_1, 2 as col_2, 3 as col_3 from dual
                union all
            select 'A' as col_1, 2 as col_2, 3 as col_3 from dual
                union all
            select 'A' as col_1, 2 as col_2, 3 as col_3 from dual
            """
        )
        expected_data = [("A", 2, 3)] * 3
        self.assertEqual(self.cursor.fetchall(), expected_data)

    def test_4346(self):
        "4346 - test setinputsizes() with defaults specified"
        self.cursor.setinputsizes(None, str)
        self.assertIsNone(self.cursor.bindvars[0])
        self.assertIsInstance(self.cursor.bindvars[1], oracledb.Var)
        self.cursor.setinputsizes(a=None, b=str)
        self.assertIsNone(self.cursor.bindvars.get("a"))
        self.assertIsInstance(self.cursor.bindvars["b"], oracledb.Var)

    @unittest.skipIf(test_env.get_is_drcp(), "not supported with DRCP")
    def test_4347(self):
        "4547 - kill connection with open cursor"
        admin_conn = test_env.get_admin_connection()
        conn = test_env.get_connection()
        self.assertEqual(conn.is_healthy(), True)
        sid, serial = self.get_sid_serial(conn)
        with admin_conn.cursor() as admin_cursor:
            sql = f"alter system kill session '{sid},{serial}'"
            admin_cursor.execute(sql)
        with self.assertRaisesFullCode("DPY-4011"):
            with conn.cursor() as cursor:
                cursor.execute("select user from dual")
        self.assertFalse(conn.is_healthy())

    @unittest.skipIf(test_env.get_is_drcp(), "not supported with DRCP")
    def test_4348(self):
        "4348 - kill connection in cursor context manager"
        admin_conn = test_env.get_admin_connection()
        conn = test_env.get_connection()
        self.assertEqual(conn.is_healthy(), True)
        sid, serial = self.get_sid_serial(conn)
        with admin_conn.cursor() as admin_cursor:
            admin_cursor.execute(f"alter system kill session '{sid},{serial}'")
        with self.assertRaisesFullCode("DPY-4011"):
            with conn.cursor() as cursor:
                cursor.execute("select user from dual")
        self.assertEqual(conn.is_healthy(), False)

    def test_4349(self):
        "4349 - fetchmany() with and without parameters"
        sql_part = "select user from dual"
        sql = " union all ".join([sql_part] * 10)
        with self.conn.cursor() as cursor:
            cursor.arraysize = 6
            cursor.execute(sql)
            rows = cursor.fetchmany()
            self.assertEqual(len(rows), cursor.arraysize)
            cursor.execute(sql)
            rows = cursor.fetchmany(size=2)
            self.assertEqual(len(rows), 2)
            cursor.execute(sql)
            rows = cursor.fetchmany(numRows=4)
            self.assertEqual(len(rows), 4)
            cursor.execute(sql)
            with self.assertRaisesFullCode("DPY-2014"):
                cursor.fetchmany(size=2, numRows=4)

    def test_4350(self):
        "4350 - access cursor.rowcount after closing cursor"
        with self.conn.cursor() as cursor:
            cursor.execute("select user from dual")
            cursor.fetchall()
            self.assertEqual(cursor.rowcount, 1)
        self.assertEqual(cursor.rowcount, -1)

    def test_4351(self):
        "4351 - changing bind type with define needed"
        self.cursor.execute("delete from TestClobs")
        row_for_1 = (1, "Short value 1")
        row_for_56 = (56, "Short value 56")
        for data in (row_for_1, row_for_56):
            self.cursor.execute(
                "insert into TestClobs (IntCol, ClobCol) values (:1, :2)",
                data,
            )
        sql = "select IntCol, ClobCol from TestClobs where IntCol = :int_col"
        with test_env.DefaultsContextManager("fetch_lobs", False):
            self.cursor.execute(sql, int_col="1")
            self.assertEqual(self.cursor.fetchone(), row_for_1)
            self.cursor.execute(sql, int_col="56")
            self.assertEqual(self.cursor.fetchone(), row_for_56)
            self.cursor.execute(sql, int_col=1)
            self.assertEqual(self.cursor.fetchone(), row_for_1)

    def test_4352(self):
        "4352 - test calling cursor.parse() twice with the same statement"
        self.cursor.execute("truncate table TestTempTable")
        data = (4363, "Value for test 4363")
        self.cursor.execute(
            "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)",
            data,
        )
        sql = "update TestTempTable set StringCol1 = :v where IntCol = :i"
        for i in range(2):
            self.cursor.parse(sql)
            self.cursor.execute(sql, ("Updated value", data[0]))

    def test_4353(self):
        "4353 - test addition of column to cached query"
        table_name = "test_4365"
        try:
            self.cursor.execute(f"drop table {table_name}")
        except oracledb.DatabaseError:
            pass
        data = ("val 1", "val 2")
        self.cursor.execute(f"create table {table_name} (col1 varchar2(10))")
        self.cursor.execute(f"insert into {table_name} values (:1)", [data[0]])
        self.conn.commit()
        self.cursor.execute(f"select * from {table_name}")
        self.assertEqual(self.cursor.fetchall(), [(data[0],)])
        self.cursor.execute(f"alter table {table_name} add col2 varchar2(10)")
        self.cursor.execute(f"update {table_name} set col2 = :1", [data[1]])
        self.conn.commit()
        self.cursor.execute(f"select * from {table_name}")
        self.assertEqual(self.cursor.fetchall(), [data])

    def test_4354(self):
        "4354 - test population of array var with too many elements"
        var = self.cursor.arrayvar(int, 3)
        with self.assertRaisesFullCode("DPY-2016"):
            var.setvalue(0, [1, 2, 3, 4])

    def test_4355(self):
        "4355 - test executemany() with PL/SQL and increasing data lengths"
        sql = "begin :1 := length(:2); end;"
        var = self.cursor.var(int, arraysize=3)
        self.cursor.executemany(
            sql, [(var, "one"), (var, "two"), (var, "end")]
        )
        self.assertEqual(var.values, [3, 3, 3])
        self.cursor.executemany(
            sql, [(var, "three"), (var, "four"), (var, "end")]
        )
        self.assertEqual(var.values, [5, 4, 3])
        self.cursor.executemany(
            sql, [(var, "five"), (var, "six"), (var, "end")]
        )
        self.assertEqual(var.values, [4, 3, 3])

    def test_4356(self):
        "4356 - test cursor.rowcount values for queries"
        max_rows = 93
        self.cursor.arraysize = 10
        self.cursor.execute(
            "select rownum as id from dual connect by rownum <= :1",
            [max_rows],
        )
        self.assertEqual(self.cursor.rowcount, 0)
        batch_num = 1
        while True:
            rows = self.cursor.fetchmany()
            if not rows:
                break
            expected_value = min(max_rows, batch_num * self.cursor.arraysize)
            self.assertEqual(self.cursor.rowcount, expected_value)
            batch_num += 1
        self.cursor.fetchall()
        self.assertEqual(self.cursor.rowcount, max_rows)

    def test_4357(self):
        "4357 - test bind order for PL/SQL"
        self.cursor.execute("delete from TestClobs")
        sql = """
            insert into TestClobs (IntCol, CLOBCol, ExtraNumCol1)
            values (:1, :2, :3)"""
        data = "x" * 9000
        rows = [(1, data, 5), (2, data, 6)]
        self.cursor.execute(sql, rows[0])
        plsql = f"begin {sql}; end;"
        self.cursor.execute(plsql, rows[1])
        self.conn.commit()
        with test_env.DefaultsContextManager("fetch_lobs", False):
            self.cursor.execute(
                """
                select IntCol, CLOBCol, ExtraNumCol1
                from TestCLOBs
                order by IntCol
                """
            )
            self.assertEqual(self.cursor.fetchall(), rows)

    def test_4358(self):
        "4358 - test rebuild of table with LOB in cached query (as string)"
        table_name = "test_4370"
        drop_sql = f"drop table {table_name} purge"
        create_sql = f"""
            create table {table_name} (
                Col1 number(9) not null,
                Col2 clob not null
            )"""
        insert_sql = f"insert into {table_name} values (:1, :2)"
        query_sql = f"select * from {table_name} order by Col1"
        data = [(1, "CLOB value 1"), (2, "CLOB value 2")]
        try:
            self.cursor.execute(drop_sql)
        except oracledb.DatabaseError:
            pass
        with test_env.DefaultsContextManager("fetch_lobs", False):
            self.cursor.execute(create_sql)
            self.cursor.executemany(insert_sql, data)
            self.cursor.execute(query_sql)
            self.assertEqual(self.cursor.fetchall(), data)
            self.cursor.execute(query_sql)
            self.assertEqual(self.cursor.fetchall(), data)
            self.cursor.execute(drop_sql)
            self.cursor.execute(create_sql)
            self.cursor.executemany(insert_sql, data)
            self.cursor.execute(query_sql)
            self.assertEqual(self.cursor.fetchall(), data)

    def test_4359(self):
        "4359 - test rebuild of table with LOB in cached query (as LOB)"
        table_name = "test_4371"
        drop_sql = f"drop table {table_name} purge"
        create_sql = f"""
            create table {table_name} (
                Col1 number(9) not null,
                Col2 clob not null)"""
        insert_sql = f"insert into {table_name} values (:1, :2)"
        query_sql = f"select * from {table_name} order by Col1"
        data = [(1, "CLOB value 1"), (2, "CLOB value 2")]
        try:
            self.cursor.execute(drop_sql)
        except oracledb.DatabaseError:
            pass
        self.cursor.execute(create_sql)
        self.cursor.executemany(insert_sql, data)
        self.cursor.execute(query_sql)
        fetched_data = [(n, c.read()) for n, c in self.cursor]
        self.assertEqual(fetched_data, data)
        self.cursor.execute(query_sql)
        fetched_data = [(n, c.read()) for n, c in self.cursor]
        self.assertEqual(fetched_data, data)
        self.cursor.execute(drop_sql)
        self.cursor.execute(create_sql)
        self.cursor.executemany(insert_sql, data)
        self.cursor.execute(query_sql)
        fetched_data = [(n, c.read()) for n, c in self.cursor]
        self.assertEqual(fetched_data, data)

    @unittest.skipIf(
        test_env.get_server_version() <= (12, 2), "unsupported database"
    )
    @unittest.skipIf(
        test_env.get_client_version() <= (12, 2), "unsupported database"
    )
    def test_4360(self):
        "4360 - fetch JSON columns as Python objects"
        expected_data = [
            (1, [1, 2, 3], [4, 5, 6], [7, 8, 9]),
            (2, None, None, None),
        ]
        self.cursor.execute("select * from TestJsonCols order by IntCol")
        self.assertEqual(self.cursor.fetchall(), expected_data)

    @unittest.skipIf(
        test_env.get_server_version() < (23, 1), "unsupported database"
    )
    @unittest.skipIf(
        test_env.get_client_version() < (23, 1), "unsupported client"
    )
    def test_4361(self):
        "4361 - fetch table with domain and annotations"
        self.cursor.execute("select * from TableWithDomainAndAnnotations")
        self.assertEqual(self.cursor.fetchall(), [(1, 25)])
        column_1 = self.cursor.description[0]
        self.assertIsNone(column_1.domain_schema)
        self.assertIsNone(column_1.domain_name)
        self.assertIsNone(column_1.annotations)
        column_2 = self.cursor.description[1]
        self.assertEqual(
            column_2.domain_schema, test_env.get_main_user().upper()
        )
        self.assertEqual(column_2.domain_name, "SIMPLEDOMAIN")
        expected_annotations = {
            "ANNO_1": "first annotation",
            "ANNO_2": "second annotation",
            "ANNO_3": "",
        }
        self.assertEqual(column_2.annotations, expected_annotations)

    def test_4362(self):
        "4362 - test getting statement after it was executed"
        cursor = self.conn.cursor()
        sql = "select 1 from dual"
        cursor.execute(sql)
        self.assertEqual(cursor.statement, sql)

    def test_4363(self):
        "4363 - test getting cursor fetchvars"
        cursor = self.conn.cursor()
        self.assertIsNone(cursor.fetchvars)

        cursor.execute("truncate table TestTempTable")
        cursor.execute(
            "insert into TestTempTable (IntCol, StringCol1) values (1, '12')",
        )
        cursor.execute("select IntCol, StringCol1 from TestTempTable")
        cursor.fetchall()
        self.assertEqual(len(cursor.fetchvars), 2)
        self.assertEqual(cursor.fetchvars[0].getvalue(), 1)
        self.assertEqual(cursor.fetchvars[1].getvalue(), "12")

    def test_4364(self):
        "4364 - test fetchmany() with non-default cursor.arraysize"
        self.cursor.arraysize = 20
        values = [(i,) for i in range(30)]
        self.cursor.execute("truncate table TestTempTable")
        self.cursor.executemany(
            "insert into TestTempTable (IntCol) values (:1)", values
        )
        self.cursor.execute("select IntCol from TestTempTable order by IntCol")
        # fetch first 20 elements
        fetched_values = self.cursor.fetchmany()
        self.assertEqual(fetched_values, values[: self.cursor.arraysize])

        # fetch missing elements
        fetched_values = self.cursor.fetchmany()
        self.assertEqual(fetched_values, values[self.cursor.arraysize :])

    def test_4365(self):
        "4365 - negative tests for cursor.arraysize"
        with self.assertRaisesFullCode("DPY-2045"):
            self.cursor.arraysize = 0
        with self.assertRaisesFullCode("DPY-2045"):
            self.cursor.arraysize = -1
        with self.assertRaisesFullCode("DPY-2045"):
            self.cursor.arraysize = "not valid"

    def test_4366(self):
        "4366 - test fetching LOBs after an error"
        sql = """
            select
                to_clob(:val),
                1 / (dbms_lob.getlength(to_clob(:val)) - 1)
            from dual"""
        with self.assertRaisesFullCode("ORA-01476"):
            self.cursor.execute(sql, val="a")
            self.cursor.fetchall()
        self.cursor.execute(sql, val="bb")
        lob, num_val = self.cursor.fetchone()
        self.assertEqual(lob.read(), "bb")
        self.assertEqual(num_val, 1)

    def test_4367(self):
        "4367 - test parse() with autocommit enabled"
        conn = test_env.get_connection()
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("truncate table TestTempTable")
        cursor.parse("insert into TestTempTable (IntCol) values (:1)")
        cursor.execute(None, [1])

    def test_4368(self):
        "4368 - test cursor.setinputsizes() with early failed execute"
        self.cursor.setinputsizes(a=int, b=str)
        with self.assertRaisesFullCode("DPY-2006"):
            self.cursor.execute("select :c from dual", [5])
        value = 4368
        self.cursor.execute("select :d from dual", [value])
        (fetched_value,) = self.cursor.fetchone()
        self.assertEqual(fetched_value, value)


if __name__ == "__main__":
    test_env.run_test_cases()
