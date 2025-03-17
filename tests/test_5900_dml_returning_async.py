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
5900 - Module for testing DML returning clauses with asyncio
"""

import datetime
import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    async def test_5900(self):
        "5900 - test insert (single row) with DML returning"
        await self.cursor.execute("truncate table TestTempTable")
        int_val = 5
        str_val = "A test string"
        int_var = self.cursor.var(oracledb.NUMBER)
        str_var = self.cursor.var(str)
        await self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:int_val, :str_val)
            returning IntCol, StringCol1 into :int_var, :str_var
            """,
            int_val=int_val,
            str_val=str_val,
            int_var=int_var,
            str_var=str_var,
        )
        self.assertEqual(int_var.values, [[int_val]])
        self.assertEqual(str_var.values, [[str_val]])

    async def test_5901(self):
        "5901 - test insert (multiple rows) with DML returning"
        await self.cursor.execute("truncate table TestTempTable")
        int_values = [5, 8, 17, 24, 6]
        str_values = ["Test 5", "Test 8", "Test 17", "Test 24", "Test 6"]
        int_var = self.cursor.var(oracledb.NUMBER, arraysize=len(int_values))
        str_var = self.cursor.var(str, arraysize=len(int_values))
        self.cursor.setinputsizes(None, None, int_var, str_var)
        data = list(zip(int_values, str_values))
        await self.cursor.executemany(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:int_val, :str_val)
            returning IntCol, StringCol1 into :int_var, :str_var
            """,
            data,
        )
        self.assertEqual(int_var.values, [[v] for v in int_values])
        self.assertEqual(str_var.values, [[v] for v in str_values])

    async def test_5902(self):
        "5902 - test insert with DML returning into too small a variable"
        await self.cursor.execute("truncate table TestTempTable")
        int_val = 6
        str_val = "A different test string"
        int_var = self.cursor.var(oracledb.NUMBER)
        str_var = self.cursor.var(str, 2)
        parameters = dict(
            int_val=int_val, str_val=str_val, int_var=int_var, str_var=str_var
        )
        with self.assertRaisesFullCode("DPY-4002", "DPI-1037"):
            await self.cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (:int_val, :str_val)
                returning IntCol, StringCol1 into :int_var, :str_var
                """,
                parameters,
            )

    async def test_5903(self):
        "5903 - test update single row with DML returning"
        int_val = 7
        str_val = "The updated value of the string"
        await self.cursor.execute("truncate table TestTempTable")
        await self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (int_val, "The initial value of the string"),
        )
        int_var = self.cursor.var(oracledb.NUMBER)
        str_var = self.cursor.var(str)
        await self.cursor.execute(
            """
            update TestTempTable set
                StringCol1 = :str_val
            where IntCol = :int_val
            returning IntCol, StringCol1 into :int_var, :str_var
            """,
            int_val=int_val,
            str_val=str_val,
            int_var=int_var,
            str_var=str_var,
        )
        self.assertEqual(int_var.values, [[int_val]])
        self.assertEqual(str_var.values, [[str_val]])

    async def test_5904(self):
        "5904 - test update no rows with DML returning"
        int_val = 8
        str_val = "The updated value of the string"
        await self.cursor.execute("truncate table TestTempTable")
        await self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (int_val, "The initial value of the string"),
        )
        int_var = self.cursor.var(oracledb.NUMBER)
        str_var = self.cursor.var(str)
        await self.cursor.execute(
            """
            update TestTempTable set
                StringCol1 = :str_val
            where IntCol = :int_val
            returning IntCol, StringCol1 into :int_var, :str_var
            """,
            int_val=int_val + 1,
            str_val=str_val,
            int_var=int_var,
            str_var=str_var,
        )
        self.assertEqual(int_var.values, [[]])
        self.assertEqual(str_var.values, [[]])
        self.assertEqual(int_var.getvalue(), [])
        self.assertEqual(str_var.getvalue(), [])

    async def test_5905(self):
        "5905 - test update multiple rows with DML returning"
        await self.cursor.execute("truncate table TestTempTable")
        for i in (8, 9, 10):
            await self.cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1) values (:1, :2)
                """,
                (i, f"The initial value of string {i}"),
            )
        int_var = self.cursor.var(oracledb.NUMBER)
        str_var = self.cursor.var(str)
        await self.cursor.execute(
            """
            update TestTempTable set
                IntCol = IntCol + 15,
                StringCol1 = 'The final value of string ' || to_char(IntCol)
            returning IntCol, StringCol1 into :int_var, :str_var
            """,
            int_var=int_var,
            str_var=str_var,
        )
        self.assertEqual(self.cursor.rowcount, 3)
        self.assertEqual(int_var.values, [[23, 24, 25]])
        expected_values = [
            [
                "The final value of string 8",
                "The final value of string 9",
                "The final value of string 10",
            ]
        ]
        self.assertEqual(str_var.values, expected_values)

    async def test_5906(self):
        "5906 - test update multiple rows with DML returning (executemany)"
        data = [(i, f"The initial value of string {i}") for i in range(1, 11)]
        await self.cursor.execute("truncate table TestTempTable")
        await self.cursor.executemany(
            "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)",
            data,
        )
        int_var = self.cursor.var(oracledb.NUMBER, arraysize=3)
        str_var = self.cursor.var(str, arraysize=3)
        self.cursor.setinputsizes(None, int_var, str_var)
        await self.cursor.executemany(
            """
            update TestTempTable set
                IntCol = IntCol + 25,
                StringCol1 = 'Updated value of string ' || to_char(IntCol)
            where IntCol < :inVal
            returning IntCol, StringCol1 into :int_var, :str_var
            """,
            [[3], [8], [11]],
        )
        expected_values = [[26, 27], [28, 29, 30, 31, 32], [33, 34, 35]]
        self.assertEqual(int_var.values, expected_values)
        expected_values = [
            ["Updated value of string 1", "Updated value of string 2"],
            [
                "Updated value of string 3",
                "Updated value of string 4",
                "Updated value of string 5",
                "Updated value of string 6",
                "Updated value of string 7",
            ],
            [
                "Updated value of string 8",
                "Updated value of string 9",
                "Updated value of string 10",
            ],
        ]
        self.assertEqual(str_var.values, expected_values)

    async def test_5907(self):
        "5907 - test inserting an object with DML returning"
        type_obj = await self.conn.gettype("UDT_OBJECT")
        string_value = "The string that will be verified"
        obj = type_obj.newobject()
        obj.STRINGVALUE = string_value
        out_var = self.cursor.var(type_obj)
        await self.cursor.execute(
            """
            insert into TestObjects (IntCol, ObjectCol)
            values (4, :obj)returning ObjectCol into :outObj
            """,
            obj=obj,
            outObj=out_var,
        )
        (result,) = out_var.getvalue()
        self.assertEqual(result.STRINGVALUE, string_value)
        await self.conn.rollback()

    async def test_5908(self):
        "5908 - test inserting a row and returning a rowid"
        await self.cursor.execute("truncate table TestTempTable")
        var = self.cursor.var(oracledb.ROWID)
        await self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (278, 'String 278')
            returning rowid into :1
            """,
            [var],
        )
        (rowid,) = var.getvalue()
        await self.cursor.execute(
            """
            select IntCol, StringCol1
            from TestTempTable
            where rowid = :1
            """,
            [rowid],
        )
        self.assertEqual(await self.cursor.fetchall(), [(278, "String 278")])

    async def test_5909(self):
        "5909 - test inserting with a REF cursor and returning a rowid"
        await self.cursor.execute("truncate table TestTempTable")
        var = self.cursor.var(oracledb.ROWID)
        in_cursor = self.conn.cursor()
        await in_cursor.execute(
            """
            select StringCol
            from TestStrings
            where IntCol >= 5
            order by IntCol
            """
        )
        await self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (187, pkg_TestRefCursors.TestInCursor(:1))
            returning rowid into :2
            """,
            (in_cursor, var),
        )
        (rowid,) = var.getvalue()
        await self.cursor.execute(
            """
            select IntCol, StringCol1
            from TestTempTable
            where rowid = :1
            """,
            [rowid],
        )
        self.assertEqual(
            await self.cursor.fetchall(), [(187, "String 7 (Modified)")]
        )

    async def test_5910(self):
        "5910 - test delete returning decreasing number of rows"
        data = [(i, f"Test String {i}") for i in range(1, 11)]
        await self.cursor.execute("truncate table TestTempTable")
        await self.cursor.executemany(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            data,
        )
        results = []
        int_var = self.cursor.var(int)
        self.cursor.setinputsizes(None, int_var)
        for int_val in (5, 8, 10):
            await self.cursor.execute(
                """
                delete from TestTempTable
                where IntCol < :1
                returning IntCol into :2
                """,
                [int_val],
            )
            results.append(int_var.getvalue())
        self.assertEqual(results, [[1, 2, 3, 4], [5, 6, 7], [8, 9]])

    async def test_5911(self):
        "5911 - test delete returning no rows after returning many rows"
        data = [(i, f"Test String {i}") for i in range(1, 11)]
        await self.cursor.execute("truncate table TestTempTable")
        await self.cursor.executemany(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            data,
        )
        int_var = self.cursor.var(int)
        await self.cursor.execute(
            """
            delete from TestTempTable
            where IntCol < :1
            returning IntCol into :2
            """,
            [5, int_var],
        )
        self.assertEqual(int_var.getvalue(), [1, 2, 3, 4])
        await self.cursor.execute(None, [4, int_var])
        self.assertEqual(int_var.getvalue(), [])

    async def test_5912(self):
        "5912 - test DML returning when an error occurs"
        await self.cursor.execute("truncate table TestTempTable")
        int_val = 7
        str_val = "A" * 401
        int_var = self.cursor.var(oracledb.NUMBER)
        str_var = self.cursor.var(str)
        sql = """
                insert into TestTempTable (IntCol, StringCol1)
                values (:int_val, :str_val)
                returning IntCol, StringCol1 into :int_var, :str_var"""
        parameters = dict(
            int_val=int_val, str_val=str_val, int_var=int_var, str_var=str_var
        )
        with self.assertRaisesFullCode("ORA-12899"):
            await self.cursor.execute(sql, parameters)

    async def test_5913(self):
        "5913 - test DML returning with no input variables, multiple iters"
        await self.cursor.execute("truncate table TestTempTable")
        sql = """
                insert into TestTempTable (IntCol)
                values ((select count(*) + 1 from TestTempTable))
                returning IntCol into :1"""
        var = self.cursor.var(int)
        await self.cursor.execute(sql, [var])
        self.assertEqual(var.getvalue(), [1])
        await self.cursor.execute(sql, [var])
        self.assertEqual(var.getvalue(), [2])

    async def test_5914(self):
        "5914 - test DML returning with a quoted bind name"
        sql = """
                insert into TestTempTable (IntCol, StringCol1)
                values (:int_val, :str_val)
                returning IntCol, StringCol1 into :"_val1" , :"VaL_2" """
        await self.cursor.parse(sql)
        expected_bind_names = ["INT_VAL", "STR_VAL", "_val1", "VaL_2"]
        self.assertEqual(self.cursor.bindnames(), expected_bind_names)

    async def test_5915(self):
        "5915 - test DML returning with an invalid bind name"
        sql = """
                insert into TestTempTable (IntCol)
                values (:int_val)
                returning IntCol, StringCol1 into :ROWID"""
        with self.assertRaisesFullCode("ORA-01745"):
            await self.cursor.parse(sql)

    async def test_5916(self):
        "5916 - test DML returning with input bind variable data"
        await self.cursor.execute("truncate table TestTempTable")
        out_var = self.cursor.var(int)
        await self.cursor.execute(
            """
            insert into TestTempTable (IntCol)
            values (:int_val)
            returning IntCol + :add_val into :out_val
            """,
            int_val=5,
            add_val=18,
            out_val=out_var,
        )
        await self.conn.commit()
        self.assertEqual(out_var.getvalue(), [23])

    async def test_5917(self):
        "5917 - test DML returning with LOBs and an output converter"
        await self.cursor.execute("truncate table TestCLOBs")
        out_var = self.cursor.var(
            oracledb.DB_TYPE_CLOB, outconverter=lambda value: value.read()
        )
        lob_value = "A short CLOB - 1618"
        await self.cursor.execute(
            """
            insert into TestCLOBs (IntCol, ClobCol)
            values (1, :in_val)
            returning CLOBCol into :out_val
            """,
            in_val=lob_value,
            out_val=out_var,
        )
        await self.conn.commit()
        self.assertEqual(out_var.getvalue(), [lob_value])

    async def test_5918(self):
        "5918 - test DML returning with CLOB converted to LONG"
        await self.cursor.execute("truncate table TestCLOBs")
        out_var = self.cursor.var(oracledb.DB_TYPE_LONG)
        lob_value = "A short CLOB - 1619"
        await self.cursor.execute(
            """
            insert into TestCLOBs
            (IntCol, ClobCol)
            values (1, :in_val)
            returning CLOBCol into :out_val
            """,
            in_val=lob_value,
            out_val=out_var,
        )
        await self.conn.commit()
        self.assertEqual(out_var.getvalue(), [lob_value])

    async def test_5919(self):
        "5919 - test dml returning with an index organized table"
        await self.cursor.execute("truncate table TestUniversalRowids")
        rowid_var = self.cursor.var(oracledb.ROWID)
        data = (1, "ABC", datetime.datetime(2017, 4, 11), rowid_var)
        sql = """
                insert into TestUniversalRowids values (:1, :2, :3)
                returning rowid into :4"""
        await self.cursor.execute(sql, data)
        (rowid_value,) = rowid_var.getvalue()
        await self.cursor.execute(
            """
            select *
            from TestUniversalRowids
            where rowid = :1
            """,
            [rowid_value],
        )
        (row,) = await self.cursor.fetchall()
        self.assertEqual(row, data[:3])

    async def test_5920(self):
        "5920 - test plsql returning rowids with index organized table"
        await self.cursor.execute("truncate table TestUniversalRowids")
        rowid_var = self.cursor.var(oracledb.ROWID)
        data = (1, "ABC", datetime.datetime(2017, 4, 11), rowid_var)
        await self.cursor.execute(
            """
            begin
                insert into TestUniversalRowids values (:1, :2, :3)
                returning rowid into :4;
            end;
            """,
            data,
        )
        rowid_value = rowid_var.values[0]
        await self.cursor.execute(
            """
            select *
            from TestUniversalRowids
            where rowid = :1
            """,
            [rowid_value],
        )
        (row,) = await self.cursor.fetchall()
        self.assertEqual(row, data[:3])

    async def test_5921(self):
        "5921 - parse DML returning with no spaces"
        await self.cursor.execute("truncate table TestTempTable")
        sql = (
            "insert into TestTempTable (IntCol) values (:in_val)"
            "returning(IntCol)into :out_val"
        )
        out_val = self.cursor.var(int, arraysize=5)
        await self.cursor.execute(sql, in_val=25, out_val=out_val)
        self.assertEqual(out_val.getvalue(), [25])

    async def test_5922(self):
        "5922 - use bind variable in new statement after RETURNING statement"
        await self.cursor.execute("truncate table TestTempTable")
        sql = (
            "insert into TestTempTable (IntCol) values (:in_val)"
            "returning IntCol + 15 into :out_val"
        )
        out_val = self.cursor.var(int, arraysize=5)
        await self.cursor.execute(sql, in_val=25, out_val=out_val)
        self.assertEqual(out_val.getvalue(), [40])
        sql = "begin :out_val := :in_val + 35; end;"
        await self.cursor.execute(sql, in_val=35, out_val=out_val)
        self.assertEqual(out_val.getvalue(), 70)


if __name__ == "__main__":
    test_env.run_test_cases()
