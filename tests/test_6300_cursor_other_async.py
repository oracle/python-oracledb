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
6300 - Module for testing other cursor methods and attributes with asyncio.
"""

import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    async def test_6300(self):
        "6300 - test preparing a statement and executing it multiple times"
        cursor = self.conn.cursor()
        self.assertEqual(cursor.statement, None)
        statement = "begin :value := :value + 5; end;"
        cursor.prepare(statement)
        var = cursor.var(oracledb.NUMBER)
        self.assertEqual(cursor.statement, statement)
        var.setvalue(0, 2)
        await cursor.execute(None, value=var)
        self.assertEqual(var.getvalue(), 7)
        await cursor.execute(None, value=var)
        self.assertEqual(var.getvalue(), 12)
        await cursor.execute("begin :value2 := 3; end;", value2=var)
        self.assertEqual(var.getvalue(), 3)

    async def test_6301(self):
        "6301 - confirm an exception is raised after closing a cursor"
        self.cursor.close()
        with self.assertRaisesFullCode("DPY-1006"):
            await self.cursor.execute("select 1 from dual")

    async def test_6302(self):
        "6302 - test iterators"
        await self.cursor.execute(
            """
            select IntCol
            from TestNumbers
            where IntCol between 1 and 3
            order by IntCol
            """
        )
        rows = [v async for v, in self.cursor]
        self.assertEqual(rows, [1, 2, 3])

    async def test_6303(self):
        "6303 - test iterators (with intermediate execute)"
        await self.cursor.execute("truncate table TestTempTable")
        await self.cursor.execute(
            """
            select IntCol
            from TestNumbers
            where IntCol between 1 and 3
            order by IntCol
            """
        )
        test_iter = self.cursor.__aiter__()
        (value,) = await test_iter.__anext__()
        await self.cursor.execute(
            "insert into TestTempTable (IntCol) values (1)"
        )
        with self.assertRaisesFullCode("DPY-1003"):
            await test_iter.__anext__()

    async def test_6304(self):
        "6304 - test setting input sizes without any parameters"
        self.cursor.setinputsizes()
        await self.cursor.execute("select :val from dual", val="Test Value")
        self.assertEqual(await self.cursor.fetchall(), [("Test Value",)])

    async def test_6305(self):
        "6305 - test setting input sizes with an empty dictionary"
        empty_dict = {}
        self.cursor.prepare("select 236 from dual")
        self.cursor.setinputsizes(**empty_dict)
        await self.cursor.execute(None, empty_dict)
        self.assertEqual(await self.cursor.fetchall(), [(236,)])

    async def test_6306(self):
        "6306 - test setting input sizes with an empty list"
        empty_list = []
        self.cursor.prepare("select 239 from dual")
        self.cursor.setinputsizes(*empty_list)
        await self.cursor.execute(None, empty_list)
        self.assertEqual(await self.cursor.fetchall(), [(239,)])

    async def test_6307(self):
        "6307 - test setting input sizes with positional args"
        var = self.cursor.var(oracledb.STRING, 100)
        self.cursor.setinputsizes(None, 5, None, 10, None, oracledb.NUMBER)
        await self.cursor.execute(
            """
            begin
              :1 := :2 || to_char(:3) || :4 || to_char(:5) || to_char(:6);
            end;
            """,
            [var, "test_", 5, "_second_", 3, 7],
        )
        self.assertEqual(var.getvalue(), "test_5_second_37")

    async def test_6308(self):
        "6308 - test parsing query statements"
        sql = "select LongIntCol from TestNumbers where IntCol = :val"
        await self.cursor.parse(sql)
        self.assertEqual(self.cursor.statement, sql)
        self.assertEqual(
            self.cursor.description,
            [("LONGINTCOL", oracledb.DB_TYPE_NUMBER, 17, None, 16, 0, 0)],
        )

    async def test_6309(self):
        "6309 - test binding boolean data without the use of PL/SQL"
        await self.cursor.execute("truncate table TestTempTable")
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        await self.cursor.execute(sql, (False, "Value should be 0"))
        await self.cursor.execute(sql, (True, "Value should be 1"))
        await self.cursor.execute(
            "select IntCol, StringCol1 from TestTempTable order by IntCol"
        )
        expected_value = [(0, "Value should be 0"), (1, "Value should be 1")]
        self.assertEqual(await self.cursor.fetchall(), expected_value)

    async def test_6310(self):
        "6310 - test using a cursor as a context manager"
        with self.cursor as cursor:
            await cursor.execute("truncate table TestTempTable")
            await cursor.execute("select count(*) from TestTempTable")
            (count,) = await cursor.fetchone()
            self.assertEqual(count, 0)
        with self.assertRaisesFullCode("DPY-1006"):
            self.cursor.close()

    async def test_6311(self):
        "6311 - test that rowcount attribute is reset to zero on query execute"
        for num in [0, 1, 1, 0]:
            await self.cursor.execute("select * from dual where 1 = :s", [num])
            await self.cursor.fetchone()
            self.assertEqual(self.cursor.rowcount, num)

    async def test_6312(self):
        "6312 - test that an object type can be used as type in cursor.var()"
        obj_type = await self.conn.gettype("UDT_OBJECT")
        var = self.cursor.var(obj_type)
        await self.cursor.callproc(
            "pkg_TestBindObject.BindObjectOut", (28, "Bind obj out", var)
        )
        obj = var.getvalue()
        result = await self.cursor.callfunc(
            "pkg_TestBindObject.GetStringRep", str, (obj,)
        )
        exp = "udt_Object(28, 'Bind obj out', null, null, null, null, null)"
        self.assertEqual(result, exp)

    async def test_6313(self):
        "6313 - test that fetching an XMLType returns a string"
        int_val = 5
        label = "IntCol"
        expected_result = f"<{label}>{int_val}</{label}>"
        await self.cursor.execute(
            f"""
            select XMLElement("{label}", IntCol)
            from TestStrings
            where IntCol = :int_val
            """,
            int_val=int_val,
        )
        (result,) = await self.cursor.fetchone()
        self.assertEqual(result, expected_result)

    async def test_6314(self):
        "6314 - test last rowid"

        # no statement executed: no rowid
        self.assertIsNone(self.cursor.lastrowid)

        # DDL statement executed: no rowid
        await self.cursor.execute("truncate table TestTempTable")
        self.assertIsNone(self.cursor.lastrowid)

        # statement prepared: no rowid
        self.cursor.prepare("insert into TestTempTable (IntCol) values (:1)")
        self.assertIsNone(self.cursor.lastrowid)

        # multiple rows inserted: rowid of last row inserted
        rows = [(n,) for n in range(225)]
        await self.cursor.executemany(None, rows)
        rowid = self.cursor.lastrowid
        await self.cursor.execute(
            """
            select rowid
            from TestTempTable
            where IntCol = :1
            """,
            rows[-1],
        )
        row = await self.cursor.fetchone()
        self.assertEqual(row[0], rowid)

        # statement executed but no rows updated: no rowid
        await self.cursor.execute("delete from TestTempTable where 1 = 0")
        self.assertIsNone(self.cursor.lastrowid)

        # stetement executed with one row updated: rowid of updated row
        await self.cursor.execute(
            """
            update TestTempTable set StringCol1 = 'Modified'
            where IntCol = :1
            """,
            rows[-2],
        )
        rowid = self.cursor.lastrowid
        await self.cursor.execute(
            "select rowid from TestTempTable where IntCol = :1",
            rows[-2],
        )
        row = await self.cursor.fetchone()
        self.assertEqual(row[0], rowid)

        # statement executed with many rows updated: rowid of last updated row
        await self.cursor.execute(
            """
            update TestTempTable set
                StringCol1 = 'Row ' || to_char(IntCol)
            where IntCol = :1
            """,
            rows[-3],
        )
        rowid = self.cursor.lastrowid
        await self.cursor.execute(
            "select StringCol1 from TestTempTable where rowid = :1",
            [rowid],
        )
        row = await self.cursor.fetchone()
        self.assertEqual(row[0], "Row %s" % rows[-3])

    async def test_6315(self):
        "6315 - test prefetch rows"
        await self.setup_round_trip_checker()

        # perform simple query and verify only one round trip is needed
        with self.conn.cursor() as cursor:
            await cursor.execute("select sysdate from dual")
            await cursor.fetchall()
            await self.assertRoundTrips(1)

        # set prefetchrows to 1 and verify that two round trips are now needed
        with self.conn.cursor() as cursor:
            cursor.prefetchrows = 1
            self.assertEqual(cursor.prefetchrows, 1)
            await cursor.execute("select sysdate from dual")
            await cursor.fetchall()
            await self.assertRoundTrips(2)

        # simple DDL only requires a single round trip
        with self.conn.cursor() as cursor:
            await cursor.execute("truncate table TestTempTable")
            await self.assertRoundTrips(1)

        # array execution only requires a single round trip
        num_rows = 590
        with self.conn.cursor() as cursor:
            data = [(n + 1,) for n in range(num_rows)]
            await cursor.executemany(
                "insert into TestTempTable (IntCol) values (:1)",
                data,
            )
            await self.assertRoundTrips(1)

        # setting prefetch and array size to 1 requires a round-trip for each
        # row
        with self.conn.cursor() as cursor:
            cursor.arraysize = 1
            cursor.prefetchrows = 1
            self.assertEqual(cursor.prefetchrows, 1)
            await cursor.execute("select IntCol from TestTempTable")
            await cursor.fetchall()
            await self.assertRoundTrips(num_rows + 1)

        # setting prefetch and array size to 300 requires 2 round-trips
        with self.conn.cursor() as cursor:
            cursor.arraysize = 300
            cursor.prefetchrows = 300
            self.assertEqual(cursor.prefetchrows, 300)
            await cursor.execute("select IntCol from TestTempTable")
            await cursor.fetchall()
            await self.assertRoundTrips(2)

    async def test_6316(self):
        "6316 - test prefetch rows using existing cursor"
        await self.setup_round_trip_checker()

        # Set prefetch rows on an existing cursor
        num_rows = 590
        with self.conn.cursor() as cursor:
            await cursor.execute("truncate table TestTempTable")
            await self.assertRoundTrips(1)
            data = [(n + 1,) for n in range(num_rows)]
            await cursor.executemany(
                "insert into TestTempTable (IntCol) values (:1)",
                data,
            )
            await self.assertRoundTrips(1)
            cursor.prefetchrows = 30
            cursor.arraysize = 100
            await cursor.execute("select IntCol from TestTempTable")
            await cursor.fetchall()
            await self.assertRoundTrips(7)

    async def test_6317(self):
        "6317 - test parsing plsql statements"
        sql = "begin :value := 5; end;"
        await self.cursor.parse(sql)
        self.assertEqual(self.cursor.statement, sql)
        self.assertIsNone(self.cursor.description)

    async def test_6318(self):
        "6318 - test parsing ddl statements"
        sql = "truncate table TestTempTable"
        await self.cursor.parse(sql)
        self.assertEqual(self.cursor.statement, sql)
        self.assertIsNone(self.cursor.description)

    async def test_6319(self):
        "6319 - test parsing dml statements"
        sql = "insert into TestTempTable (IntCol) values (1)"
        await self.cursor.parse(sql)
        self.assertEqual(self.cursor.statement, sql)
        self.assertIsNone(self.cursor.description)

    async def test_6320(self):
        "6320 - test binding by name with leading colon"
        params = {":arg1": 5}
        await self.cursor.execute("select :arg1 from dual", params)
        (result,) = await self.cursor.fetchone()
        self.assertEqual(result, params[":arg1"])

    async def test_6321(self):
        "6321 - test binding mixed null and not null values in a PL/SQL block"
        out_vars = [self.cursor.var(str) for i in range(4)]
        await self.cursor.execute(
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

    async def test_6322(self):
        "6322 - test excluding statement from statement cache"
        num_iters = 10
        sql = "select user from dual"
        await self.setup_parse_count_checker()

        # with statement cache enabled, only one parse should take place
        for i in range(num_iters):
            with self.conn.cursor() as cursor:
                await cursor.execute(sql)
        await self.assertParseCount(1)

        # with statement cache disabled for the statement, parse count should
        # be the same as the number of iterations
        for i in range(num_iters):
            with self.conn.cursor() as cursor:
                cursor.prepare(sql, cache_statement=False)
                await cursor.execute(None)
        await self.assertParseCount(num_iters - 1)

    async def test_6323(self):
        "6323 - test repeated DDL"
        await self.cursor.execute("truncate table TestTempTable")
        await self.cursor.execute(
            "insert into TestTempTable (IntCol) values (1)"
        )
        await self.cursor.execute("truncate table TestTempTable")
        await self.cursor.execute(
            "insert into TestTempTable (IntCol) values (1)"
        )

    async def test_6324(self):
        "6324 - test executing SQL with non-ASCII characters"
        await self.cursor.execute("select 'FÖÖ' from dual")
        (result,) = await self.cursor.fetchone()
        self.assertIn(result, ("FÖÖ", "F¿¿"))

    async def test_6325(self):
        "6325 - test case sensitivity of unquoted bind names"
        await self.cursor.execute("select :test from dual", {"TEST": "a"})
        (result,) = await self.cursor.fetchone()
        self.assertEqual(result, "a")

    async def test_6326(self):
        "6326 - test case sensitivity of quoted bind names"
        with self.assertRaisesFullCode("ORA-01036", "DPY-4008"):
            await self.cursor.execute(
                'select :"test" from dual', {'"TEST"': "a"}
            )

    async def test_6327(self):
        "6327 - test using a reserved keywords as a bind name"
        sql = "select :ROWID from dual"
        with self.assertRaisesFullCode("ORA-01745"):
            await self.cursor.parse(sql)

    async def test_6328(self):
        "6328 - test array size less than prefetch rows"
        for i in range(2):
            with self.conn.cursor() as cursor:
                cursor.arraysize = 1
                await cursor.execute(
                    "select 1 from dual union select 2 from dual"
                )
                self.assertEqual(await cursor.fetchall(), [(1,), (2,)])

    async def test_6329(self):
        "6329 - test re-executing a query with blob as bytes"

        def type_handler(cursor, metadata):
            if metadata.type_code is oracledb.DB_TYPE_BLOB:
                return cursor.var(bytes, arraysize=cursor.arraysize)

        self.conn.outputtypehandler = type_handler
        blob_data = b"An arbitrary set of blob data for test case 4348"
        await self.cursor.execute("truncate table TestBLOBs")
        await self.cursor.execute(
            "insert into TestBLOBs (IntCol, BlobCol) values (1, :data)",
            [blob_data],
        )
        await self.cursor.execute("select IntCol, BlobCol from TestBLOBs")
        self.assertEqual(await self.cursor.fetchall(), [(1, blob_data)])

        await self.cursor.execute("truncate table TestBLOBs")
        await self.cursor.execute(
            "insert into TestBLOBs (IntCol, BlobCol) values (1, :data)",
            [blob_data],
        )
        await self.cursor.execute("select IntCol, BlobCol from TestBLOBs")
        self.assertEqual(await self.cursor.fetchall(), [(1, blob_data)])

    async def test_6330(self):
        "6330 - test re-executing a statement after raising an error"
        sql = "select * from TestFakeTable"
        with self.assertRaisesFullCode("ORA-00942"):
            await self.cursor.execute(sql)
        with self.assertRaisesFullCode("ORA-00942"):
            await self.cursor.execute(sql)

        sql = "insert into TestStrings (StringCol) values (NULL)"
        with self.assertRaisesFullCode("ORA-01400"):
            await self.cursor.execute(sql)
        with self.assertRaisesFullCode("ORA-01400"):
            await self.cursor.execute(sql)

    async def test_6331(self):
        "6331 - test executing a statement that raises ORA-01007"
        with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                create or replace view ora_1007 as
                    select 1 as SampleNumber, 'String' as SampleString,
                        'Another String' as AnotherString
                    from dual
                """
            )
        with self.conn.cursor() as cursor:
            await cursor.execute("select * from ora_1007")
            self.assertEqual(
                await cursor.fetchone(), (1, "String", "Another String")
            )
        with self.conn.cursor() as cursor:
            await cursor.execute(
                """
                create or replace view ora_1007 as
                    select 1 as SampleNumber,
                        'Another String' as AnotherString
                    from dual
                """
            )
        with self.conn.cursor() as cursor:
            await cursor.execute("select * from ora_1007")
            self.assertEqual(await cursor.fetchone(), (1, "Another String"))

    async def test_6332(self):
        "6332 - test updating an empty row"
        int_var = self.cursor.var(int)
        await self.cursor.execute("truncate table TestTempTable")
        await self.cursor.execute(
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

    async def test_6333(self):
        "6333 - fetch duplicate data from query in statement cache"
        sql = """
                select 'A', 'B', 'C' from dual
                union all
                select 'A', 'B', 'C' from dual
                union all
                select 'A', 'B', 'C' from dual"""
        expected_data = [("A", "B", "C")] * 3
        with self.conn.cursor() as cursor:
            cursor.prefetchrows = 0
            await cursor.execute(sql)
            self.assertEqual(await cursor.fetchall(), expected_data)
        with self.conn.cursor() as cursor:
            cursor.prefetchrows = 0
            await cursor.execute(sql)
            self.assertEqual(await cursor.fetchall(), expected_data)

    async def test_6334(self):
        "6334 - fetch duplicate data with outconverter"

        def out_converter(value):
            self.assertIs(type(value), str)
            return int(value)

        def type_handler(cursor, metadata):
            if metadata.name == "COL_3":
                return cursor.var(
                    str, arraysize=cursor.arraysize, outconverter=out_converter
                )

        self.cursor.outputtypehandler = type_handler
        await self.cursor.execute(
            """
            select 'A' as col_1, 2 as col_2, 3 as col_3 from dual
                union all
            select 'A' as col_1, 2 as col_2, 3 as col_3 from dual
                union all
            select 'A' as col_1, 2 as col_2, 3 as col_3 from dual
            """
        )
        expected_data = [("A", 2, 3)] * 3
        self.assertEqual(await self.cursor.fetchall(), expected_data)

    @unittest.skipIf(test_env.get_is_drcp(), "not supported with DRCP")
    async def test_6335(self):
        "6335 - kill connection with open cursor"
        admin_conn = await test_env.get_admin_connection_async()
        conn = await test_env.get_connection_async()
        self.assertEqual(conn.is_healthy(), True)
        sid, serial = await self.get_sid_serial(conn)
        with admin_conn.cursor() as admin_cursor:
            sql = f"alter system kill session '{sid},{serial}'"
            await admin_cursor.execute(sql)
        with self.assertRaisesFullCode("DPY-4011"):
            with conn.cursor() as cursor:
                await cursor.execute("select user from dual")
        self.assertFalse(conn.is_healthy())

    @unittest.skipIf(test_env.get_is_drcp(), "not supported with DRCP")
    async def test_6336(self):
        "6336 - kill connection in cursor context manager"
        admin_conn = await test_env.get_admin_connection_async()
        conn = await test_env.get_connection_async()
        self.assertEqual(conn.is_healthy(), True)
        sid, serial = await self.get_sid_serial(conn)
        with admin_conn.cursor() as admin_cursor:
            await admin_cursor.execute(
                f"alter system kill session '{sid},{serial}'"
            )
        with self.assertRaisesFullCode("DPY-4011"):
            with conn.cursor() as cursor:
                await cursor.execute("select user from dual")
        self.assertEqual(conn.is_healthy(), False)

    async def test_6337(self):
        "6337 - fetchmany() with and without parameters"
        sql_part = "select user from dual"
        sql = " union all ".join([sql_part] * 10)
        with self.conn.cursor() as cursor:
            cursor.arraysize = 6
            await cursor.execute(sql)
            rows = await cursor.fetchmany()
            self.assertEqual(len(rows), cursor.arraysize)
            await cursor.execute(sql)
            rows = await cursor.fetchmany(size=2)
            self.assertEqual(len(rows), 2)
            await cursor.execute(sql)

    async def test_6338(self):
        "6338 - access cursor.rowcount after closing cursor"
        with self.conn.cursor() as cursor:
            await cursor.execute("select user from dual")
            await cursor.fetchall()
            self.assertEqual(cursor.rowcount, 1)
        self.assertEqual(cursor.rowcount, -1)

    async def test_6339(self):
        "6339 - changing bind type with define needed"
        await self.cursor.execute("truncate table TestClobs")
        row_for_1 = (1, "Short value 1")
        row_for_56 = (56, "Short value 56")
        for data in (row_for_1, row_for_56):
            await self.cursor.execute(
                "insert into TestClobs (IntCol, ClobCol) values (:1, :2)",
                data,
            )
        sql = "select IntCol, ClobCol from TestClobs where IntCol = :int_col"
        with test_env.DefaultsContextManager("fetch_lobs", False):
            await self.cursor.execute(sql, int_col="1")
            self.assertEqual(await self.cursor.fetchone(), row_for_1)
            await self.cursor.execute(sql, int_col="56")
            self.assertEqual(await self.cursor.fetchone(), row_for_56)
            await self.cursor.execute(sql, int_col=1)
            self.assertEqual(await self.cursor.fetchone(), row_for_1)

    async def test_6340(self):
        "6340 - test calling cursor.parse() twice with the same statement"
        await self.cursor.execute("truncate table TestTempTable")
        data = (4363, "Value for test 4363")
        await self.cursor.execute(
            "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)",
            data,
        )
        sql = "update TestTempTable set StringCol1 = :v where IntCol = :i"
        for i in range(2):
            await self.cursor.parse(sql)
            await self.cursor.execute(sql, ("Updated value", data[0]))

    async def test_6341(self):
        "6341 - test addition of column to cached query"
        table_name = "test_4365"
        try:
            await self.cursor.execute(f"drop table {table_name}")
        except oracledb.DatabaseError:
            pass
        data = ("val 1", "val 2")
        await self.cursor.execute(
            f"create table {table_name} (col1 varchar2(10))"
        )
        await self.cursor.execute(
            f"insert into {table_name} values (:1)", [data[0]]
        )
        await self.conn.commit()
        await self.cursor.execute(f"select * from {table_name}")
        self.assertEqual(await self.cursor.fetchall(), [(data[0],)])
        await self.cursor.execute(
            f"alter table {table_name} add col2 varchar2(10)"
        )
        await self.cursor.execute(
            f"update {table_name} set col2 = :1", [data[1]]
        )
        await self.conn.commit()
        await self.cursor.execute(f"select * from {table_name}")
        self.assertEqual(await self.cursor.fetchall(), [data])

    async def test_6342(self):
        "6342 - test executemany() with PL/SQL and increasing data lengths"
        sql = "begin :1 := length(:2); end;"
        var = self.cursor.var(int, arraysize=3)
        await self.cursor.executemany(
            sql, [(var, "one"), (var, "two"), (var, "end")]
        )
        self.assertEqual(var.values, [3, 3, 3])
        await self.cursor.executemany(
            sql, [(var, "three"), (var, "four"), (var, "end")]
        )
        self.assertEqual(var.values, [5, 4, 3])
        await self.cursor.executemany(
            sql, [(var, "five"), (var, "six"), (var, "end")]
        )
        self.assertEqual(var.values, [4, 3, 3])

    async def test_6343(self):
        "6343 - test cursor.rowcount values for queries"
        max_rows = 93
        self.cursor.arraysize = 10
        await self.cursor.execute(
            "select rownum as id from dual connect by rownum <= :1",
            [max_rows],
        )
        self.assertEqual(self.cursor.rowcount, 0)
        batch_num = 1
        while True:
            rows = await self.cursor.fetchmany()
            if not rows:
                break
            expected_value = min(max_rows, batch_num * self.cursor.arraysize)
            self.assertEqual(self.cursor.rowcount, expected_value)
            batch_num += 1
        await self.cursor.fetchall()
        self.assertEqual(self.cursor.rowcount, max_rows)

    async def test_6344(self):
        "6344 - test bind order for PL/SQL"
        await self.cursor.execute("truncate table TestClobs")
        sql = """
            insert into TestClobs (IntCol, CLOBCol, ExtraNumCol1)
            values (:1, :2, :3)"""
        data = "x" * 9000
        rows = [(1, data, 5), (2, data, 6)]
        await self.cursor.execute(sql, rows[0])
        plsql = f"begin {sql}; end;"
        await self.cursor.execute(plsql, rows[1])
        await self.conn.commit()
        with test_env.DefaultsContextManager("fetch_lobs", False):
            await self.cursor.execute(
                """
                select IntCol, CLOBCol, ExtraNumCol1
                from TestCLOBs
                order by IntCol
                """
            )
            self.assertEqual(await self.cursor.fetchall(), rows)

    async def test_6345(self):
        "6345 - test rebuild of table with LOB in cached query (as string)"
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
            await self.cursor.execute(drop_sql)
        except oracledb.DatabaseError:
            pass
        with test_env.DefaultsContextManager("fetch_lobs", False):
            await self.cursor.execute(create_sql)
            await self.cursor.executemany(insert_sql, data)
            await self.cursor.execute(query_sql)
            self.assertEqual(await self.cursor.fetchall(), data)
            await self.cursor.execute(query_sql)
            self.assertEqual(await self.cursor.fetchall(), data)
            await self.cursor.execute(drop_sql)
            await self.cursor.execute(create_sql)
            await self.cursor.executemany(insert_sql, data)
            await self.cursor.execute(query_sql)
            self.assertEqual(await self.cursor.fetchall(), data)

    async def test_6346(self):
        "6346 - test rebuild of table with LOB in cached query (as LOB)"
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
            await self.cursor.execute(drop_sql)
        except oracledb.DatabaseError:
            pass
        await self.cursor.execute(create_sql)
        await self.cursor.executemany(insert_sql, data)
        await self.cursor.execute(query_sql)
        fetched_data = [(n, await c.read()) async for n, c in self.cursor]
        self.assertEqual(fetched_data, data)
        await self.cursor.execute(query_sql)
        fetched_data = [(n, await c.read()) async for n, c in self.cursor]
        self.assertEqual(fetched_data, data)
        await self.cursor.execute(drop_sql)
        await self.cursor.execute(create_sql)
        await self.cursor.executemany(insert_sql, data)
        await self.cursor.execute(query_sql)
        fetched_data = [(n, await c.read()) async for n, c in self.cursor]
        self.assertEqual(fetched_data, data)

    @unittest.skipIf(
        test_env.get_server_version() < (23, 1), "unsupported database"
    )
    async def test_6347(self):
        "6347 - fetch table with domain and annotations"
        await self.cursor.execute(
            "select * from TableWithDomainAndAnnotations"
        )
        self.assertEqual(await self.cursor.fetchall(), [(1, 25)])
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

    async def test_6348(self):
        "6348 - test fetching LOBs after an error"
        sql = """
            select
                to_clob(:val),
                1 / (dbms_lob.getlength(to_clob(:val)) - 1)
            from dual"""
        with self.assertRaisesFullCode("ORA-01476"):
            await self.cursor.execute(sql, val="a")
        await self.cursor.execute(sql, val="bb")
        lob, num_val = await self.cursor.fetchone()
        self.assertEqual(await lob.read(), "bb")
        self.assertEqual(num_val, 1)

    async def test_6349(self):
        "6349 - test parse() with autocommit enabled"
        async with test_env.get_connection_async() as conn:
            conn.autocommit = True
            cursor = conn.cursor()
            await cursor.execute("truncate table TestTempTable")
            await cursor.parse(
                "insert into TestTempTable (IntCol) values (:1)"
            )
            await cursor.execute(None, [1])

    async def test_6350(self):
        "6350 - test cursor.setinputsizes() with early failed execute"
        self.cursor.setinputsizes(a=int, b=str)
        with self.assertRaisesFullCode("DPY-2006"):
            await self.cursor.execute("select :c from dual", [5])
        value = 4368
        await self.cursor.execute("select :d from dual", [value])
        (fetched_value,) = await self.cursor.fetchone()
        self.assertEqual(fetched_value, value)

    async def test_6351(self):
        "6351 - fetch JSON columns as Python objects"
        expected_data = [
            (1, [1, 2, 3], [4, 5, 6], [7, 8, 9]),
            (2, None, None, None),
        ]
        await self.cursor.execute("select * from TestJsonCols order by IntCol")
        self.assertEqual(await self.cursor.fetchall(), expected_data)

    async def test_6352(self):
        "6352 - test fetching nested cursors repeatedly"
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
            with self.conn.cursor() as cursor:
                cursor.arraysize = 10
                await cursor.execute(sql)
                desc, nested1 = await cursor.fetchone()
                self.assertEqual(desc, "Top Level String 1")
                nested_rows = await nested1.fetchall()
                self.assertEqual(
                    nested_rows, [("Nested String for Top Level String 1",)]
                )
                desc, nested2 = await cursor.fetchone()
                self.assertEqual(desc, "Top Level String 2")
                nested_rows = await nested2.fetchall()
                self.assertEqual(
                    nested_rows, [("Nested String for Top Level String 2",)]
                )


if __name__ == "__main__":
    test_env.run_test_cases()
