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
5400 - Module for testing the cursor execute() method with asyncio
"""

import collections
import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    async def test_5400(self):
        "5400 - test executing a statement without any arguments"
        result = await self.cursor.execute("begin null; end;")
        self.assertIsNone(result)

    async def test_5401(self):
        "5401 - test executing a None statement with bind variables"
        cursor = self.conn.cursor()
        with self.assertRaisesFullCode("DPY-2001"):
            await cursor.execute(None, x=5)

    async def test_5402(self):
        "5402 - test executing a statement with args and empty keyword args"
        simple_var = self.cursor.var(oracledb.NUMBER)
        args = [simple_var]
        kwargs = {}
        result = await self.cursor.execute(
            "begin :1 := 25; end;", args, **kwargs
        )
        self.assertIsNone(result)
        self.assertEqual(simple_var.getvalue(), 25)

    async def test_5403(self):
        "5403 - test executing a statement with keyword arguments"
        simple_var = self.cursor.var(oracledb.NUMBER)
        result = await self.cursor.execute(
            "begin :value := 5; end;", value=simple_var
        )
        self.assertIsNone(result)
        self.assertEqual(simple_var.getvalue(), 5)

    async def test_5404(self):
        "5404 - test executing a statement with a dictionary argument"
        simple_var = self.cursor.var(oracledb.NUMBER)
        dict_arg = dict(value=simple_var)
        result = await self.cursor.execute(
            "begin :value := 10; end;", dict_arg
        )
        self.assertIsNone(result)
        self.assertEqual(simple_var.getvalue(), 10)

    async def test_5405(self):
        "5405 - test executing a statement with both a dict and keyword args"
        simple_var = self.cursor.var(oracledb.NUMBER)
        dict_arg = dict(value=simple_var)
        with self.assertRaisesFullCode("DPY-2005"):
            await self.cursor.execute(
                "begin :value := 15; end;", dict_arg, value=simple_var
            )

    async def test_5406(self):
        "5406 - test executing a statement and then changing the array size"
        await self.cursor.execute("select IntCol from TestNumbers")
        self.cursor.arraysize = 5
        self.assertEqual(len(await self.cursor.fetchall()), 10)

    async def test_5407(self):
        "5407 - test that subsequent executes succeed after bad execute"
        sql = "begin raise_application_error(-20000, 'this); end;"
        with self.assertRaisesFullCode("DPY-2041"):
            await self.cursor.execute(sql)
        await self.cursor.execute("begin null; end;")

    async def test_5408(self):
        "5408 - test that subsequent fetches fail after bad execute"
        with self.assertRaisesFullCode("ORA-00904"):
            await self.cursor.execute("select y from dual")
        with self.assertRaisesFullCode("DPY-1003"):
            await self.cursor.fetchall()

    async def test_5409(self):
        "5409 - test executing a statement with an incorrect named bind"
        sql = "select * from TestStrings where IntCol = :value"
        with self.assertRaisesFullCode("DPY-4008", "ORA-01036"):
            await self.cursor.execute(sql, value2=3)

    async def test_5410(self):
        "5410 - test executing a statement with named binds"
        await self.cursor.execute(
            """
            select *
            from TestNumbers
            where IntCol = :value1 and LongIntCol = :value2
            """,
            value1=1,
            value2=38,
        )
        self.assertEqual(len(await self.cursor.fetchall()), 1)

    async def test_5411(self):
        "5411 - test executing a statement with an incorrect positional bind"
        sql = """
                select *
                from TestNumbers
                where IntCol = :value and LongIntCol = :value2"""
        with self.assertRaisesFullCode("DPY-4009", "ORA-01008"):
            await self.cursor.execute(sql, [3])

    async def test_5412(self):
        "5412 - test executing a statement with positional binds"
        await self.cursor.execute(
            """
            select *
            from TestNumbers
            where IntCol = :value and LongIntCol = :value2
            """,
            [1, 38],
        )
        self.assertEqual(len(await self.cursor.fetchall()), 1)

    async def test_5413(self):
        "5413 - test executing a statement after rebinding a named bind"
        statement = "begin :value := :value2 + 5; end;"
        simple_var = self.cursor.var(oracledb.NUMBER)
        simple_var2 = self.cursor.var(oracledb.NUMBER)
        simple_var2.setvalue(0, 5)
        result = await self.cursor.execute(
            statement, value=simple_var, value2=simple_var2
        )
        self.assertIsNone(result)
        self.assertEqual(simple_var.getvalue(), 10)

        simple_var = self.cursor.var(oracledb.NATIVE_FLOAT)
        simple_var2 = self.cursor.var(oracledb.NATIVE_FLOAT)
        simple_var2.setvalue(0, 10)
        result = await self.cursor.execute(
            statement, value=simple_var, value2=simple_var2
        )
        self.assertIsNone(result)
        self.assertEqual(simple_var.getvalue(), 15)

    async def test_5414(self):
        "5414 - test executing a PL/SQL statement with duplicate binds"
        simple_var = self.cursor.var(oracledb.NUMBER)
        simple_var.setvalue(0, 5)
        result = await self.cursor.execute(
            """
            begin
                :value := :value + 5;
            end;
            """,
            value=simple_var,
        )
        self.assertIsNone(result)
        self.assertEqual(simple_var.getvalue(), 10)

    async def test_5415(self):
        "5415 - test executing a PL/SQL statement with duplicate binds"
        simple_var = self.cursor.var(oracledb.NUMBER)
        simple_var.setvalue(0, 5)
        await self.cursor.execute(
            "begin :value := :value + 5; end;", [simple_var]
        )
        self.assertEqual(simple_var.getvalue(), 10)

    async def test_5416(self):
        "5416 - test executing a statement with an incorrect number of binds"
        statement = "begin :value := :value2 + 5; end;"
        var = self.cursor.var(oracledb.NUMBER)
        var.setvalue(0, 5)
        with self.assertRaisesFullCode("DPY-4010", "ORA-01008"):
            await self.cursor.execute(statement)
        with self.assertRaisesFullCode("DPY-4010", "ORA-01008"):
            await self.cursor.execute(statement, value=var)
        with self.assertRaisesFullCode("DPY-4008", "ORA-01036"):
            await self.cursor.execute(
                statement, value=var, value2=var, value3=var
            )

    async def test_5417(self):
        "5417 - change in size on subsequent binds does not use optimised path"
        await self.cursor.execute("truncate table TestTempTable")
        data = [(1, "Test String #1"), (2, "ABC" * 100)]
        for row in data:
            await self.cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (:1, :2)
                """,
                row,
            )
        await self.conn.commit()
        await self.cursor.execute(
            "select IntCol, StringCol1 from TestTempTable"
        )
        self.assertEqual(await self.cursor.fetchall(), data)

    async def test_5418(self):
        "5418 - test that dml can use optimised path"
        data_to_insert = [(i + 1, f"Test String #{i + 1}") for i in range(3)]
        await self.cursor.execute("truncate table TestTempTable")
        for row in data_to_insert:
            with self.conn.cursor() as cursor:
                await cursor.execute(
                    """
                    insert into TestTempTable (IntCol, StringCol1)
                    values (:1, :2)
                    """,
                    row,
                )
        await self.conn.commit()
        await self.cursor.execute(
            "select IntCol, StringCol1 from TestTempTable order by IntCol"
        )
        self.assertEqual(await self.cursor.fetchall(), data_to_insert)

    async def test_5419(self):
        "5419 - test calling execute() with invalid parameters"
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        with self.assertRaisesFullCode("DPY-2003"):
            await self.cursor.execute(sql, "These are not valid parameters")

    async def test_5420(self):
        "5420 - test calling execute() with mixed binds"
        await self.cursor.execute("truncate table TestTempTable")
        self.cursor.setinputsizes(None, None, str)
        data = dict(val1=1, val2="Test String 1")
        with self.assertRaisesFullCode("DPY-2006"):
            await self.cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (:1, :2)
                returning StringCol1 into :out_var
                """,
                data,
            )

    async def test_5421(self):
        "5421 - test binding by name with double quotes"
        data = {'"_value1"': 1, '"VaLue_2"': 2, '"3VALUE"': 3}
        await self.cursor.execute(
            'select :"_value1" + :"VaLue_2" + :"3VALUE" from dual',
            data,
        )
        (result,) = await self.cursor.fetchone()
        self.assertEqual(result, 6)

    async def test_5422(self):
        "5422 - test executing a statement with different input buffer sizes"
        sql = """
                insert into TestTempTable (IntCol, StringCol1, StringCol2)
                values (:int_col, :str_val1, :str_val2) returning IntCol
                into :ret_data"""
        values1 = {"int_col": 1, "str_val1": '{"a", "b"}', "str_val2": None}
        values2 = {"int_col": 2, "str_val1": None, "str_val2": '{"a", "b"}'}
        values3 = {"int_col": 3, "str_val1": '{"a"}', "str_val2": None}

        await self.cursor.execute("truncate table TestTempTable")
        ret_bind = self.cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=1)
        self.cursor.setinputsizes(ret_data=ret_bind)
        await self.cursor.execute(sql, values1)
        self.assertEqual(ret_bind.values, [["1"]])

        ret_bind = self.cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=1)
        self.cursor.setinputsizes(ret_data=ret_bind)
        await self.cursor.execute(sql, values2)
        self.assertEqual(ret_bind.values, [["2"]])

        ret_bind = self.cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=1)
        self.cursor.setinputsizes(ret_data=ret_bind)
        await self.cursor.execute(sql, values3)
        self.assertEqual(ret_bind.values, [["3"]])

    async def test_5423(self):
        "5423 - test using rowfactory"
        await self.cursor.execute("truncate table TestTempTable")
        await self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (1, 'Test 1')
            """
        )
        await self.conn.commit()
        await self.cursor.execute(
            "select IntCol, StringCol1 from TestTempTable"
        )
        column_names = [col[0] for col in self.cursor.description]

        def rowfactory(*row):
            return dict(zip(column_names, row))

        self.cursor.rowfactory = rowfactory
        self.assertEqual(self.cursor.rowfactory, rowfactory)
        self.assertEqual(
            await self.cursor.fetchall(),
            [{"INTCOL": 1, "STRINGCOL1": "Test 1"}],
        )

    async def test_5424(self):
        "5424 - test executing same query after setting rowfactory"
        await self.cursor.execute("truncate table TestTempTable")
        data = [(1, "Test 1"), (2, "Test 2")]
        await self.cursor.executemany(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            data,
        )
        await self.conn.commit()
        await self.cursor.execute(
            "select IntCol, StringCol1 from TestTempTable"
        )
        column_names = [col[0] for col in self.cursor.description]
        self.cursor.rowfactory = lambda *row: dict(zip(column_names, row))
        results1 = await self.cursor.fetchall()
        await self.cursor.execute(
            "select IntCol, StringCol1 from TestTempTable"
        )
        results2 = await self.cursor.fetchall()
        self.assertEqual(results1, results2)

    async def test_5425(self):
        "5425 - test executing different query after setting rowfactory"
        await self.cursor.execute("truncate table TestTempTable")
        data = [(1, "Test 1"), (2, "Test 2")]
        await self.cursor.executemany(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            data,
        )
        await self.conn.commit()
        await self.cursor.execute(
            "select IntCol, StringCol1 from TestTempTable"
        )
        column_names = [col[0] for col in self.cursor.description]
        self.cursor.rowfactory = lambda *row: dict(zip(column_names, row))
        await self.cursor.execute(
            """
            select IntCol, StringCol
            from TestSTrings
            where IntCol between 1 and 3 order by IntCol
            """
        )
        expected_data = [(1, "String 1"), (2, "String 2"), (3, "String 3")]
        self.assertEqual(await self.cursor.fetchall(), expected_data)

    async def test_5426(self):
        "5426 - test setting rowfactory on a REF cursor"
        with self.conn.cursor() as cursor:
            sql_function = "pkg_TestRefCursors.TestReturnCursor"
            ref_cursor = await cursor.callfunc(
                sql_function, oracledb.DB_TYPE_CURSOR, [2]
            )
            column_names = [col[0] for col in ref_cursor.description]
            ref_cursor.rowfactory = lambda *row: dict(zip(column_names, row))
            expected_value = [
                {"INTCOL": 1, "STRINGCOL": "String 1"},
                {"INTCOL": 2, "STRINGCOL": "String 2"},
            ]
            self.assertEqual(await ref_cursor.fetchall(), expected_value)

    async def test_5427(self):
        "5427 - test using a subclassed string as bind parameter keys"

        class my_str(str):
            pass

        await self.cursor.execute("truncate table TestTempTable")
        keys = {my_str("str_val"): oracledb.DB_TYPE_VARCHAR}
        self.cursor.setinputsizes(**keys)
        values = {
            my_str("int_val"): 5427,
            my_str("str_val"): "5427 - String Value",
        }
        await self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:int_val, :str_val)
            """,
            values,
        )
        await self.cursor.execute(
            "select IntCol, StringCol1 from TestTempTable"
        )
        self.assertEqual(
            await self.cursor.fetchall(), [(5427, "5427 - String Value")]
        )

    async def test_5428(self):
        "5428 - test using a sequence of parameters other than a list or tuple"

        class MySeq(collections.abc.Sequence):
            def __init__(self, *data):
                self.data = data

            def __len__(self):
                return len(self.data)

            def __getitem__(self, index):
                return self.data[index]

        values_to_insert = [MySeq(1, "String 1"), MySeq(2, "String 2")]
        expected_data = [tuple(value) for value in values_to_insert]
        await self.cursor.execute("truncate table TestTempTable")
        await self.cursor.executemany(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:int_val, :str_val)
            """,
            values_to_insert,
        )
        await self.cursor.execute(
            """
            select IntCol, StringCol1
            from TestTempTable
            order by IntCol
            """
        )
        self.assertEqual(await self.cursor.fetchall(), expected_data)

    async def test_5429(self):
        "5429 - test an output type handler with prefetch > arraysize"

        def type_handler(cursor, metadata):
            return cursor.var(metadata.type_code, arraysize=cursor.arraysize)

        self.cursor.arraysize = 2
        self.cursor.prefetchrows = 3
        self.cursor.outputtypehandler = type_handler
        await self.cursor.execute(
            "select level from dual connect by level <= 5"
        )
        self.assertEqual(
            await self.cursor.fetchall(), [(1,), (2,), (3,), (4,), (5,)]
        )

    async def test_5430(self):
        "5430 - test setinputsizes() but without binding"
        self.cursor.setinputsizes(None, int)
        sql = "select :1, : 2 from dual"

        with self.assertRaisesFullCode("ORA-01008", "DPY-4010"):
            await self.cursor.execute(sql, [])

    async def test_5431(self):
        "5431 - test getting FetchInfo attributes"
        type_obj = await self.conn.gettype("UDT_OBJECT")
        varchar_ratio, _ = await test_env.get_charset_ratios_async()
        test_values = [
            (
                "select IntCol from TestObjects",
                10,
                None,
                False,
                "INTCOL",
                False,
                9,
                0,
                oracledb.DB_TYPE_NUMBER,
                oracledb.DB_TYPE_NUMBER,
            ),
            (
                "select ObjectCol from TestObjects",
                None,
                None,
                False,
                "OBJECTCOL",
                True,
                None,
                None,
                type_obj,
                oracledb.DB_TYPE_OBJECT,
            ),
            (
                "select JsonVarchar from TestJsonCols",
                4000,
                4000 * varchar_ratio,
                True,
                "JSONVARCHAR",
                False,
                None,
                None,
                oracledb.DB_TYPE_VARCHAR,
                oracledb.DB_TYPE_VARCHAR,
            ),
            (
                "select FLOATCOL from TestNumbers",
                127,
                None,
                False,
                "FLOATCOL",
                False,
                126,
                -127,
                oracledb.DB_TYPE_NUMBER,
                oracledb.DB_TYPE_NUMBER,
            ),
        ]
        for (
            sql,
            display_size,
            internal_size,
            is_json,
            name,
            null_ok,
            precision,
            scale,
            typ,
            type_code,
        ) in test_values:
            await self.cursor.execute(sql)
            (fetch_info,) = self.cursor.description
            self.assertIsInstance(fetch_info, oracledb.FetchInfo)
            self.assertEqual(fetch_info.display_size, display_size)
            self.assertEqual(fetch_info.internal_size, internal_size)
            self.assertEqual(fetch_info.is_json, is_json)
            self.assertEqual(fetch_info.name, name)
            self.assertEqual(fetch_info.null_ok, null_ok)
            self.assertEqual(fetch_info.precision, precision)
            self.assertEqual(fetch_info.scale, scale)
            self.assertEqual(fetch_info.type, typ)
            self.assertEqual(fetch_info.type_code, type_code)

    async def test_5432(self):
        "5432 - test FetchInfo repr() and str()"
        await self.cursor.execute("select IntCol from TestObjects")
        (fetch_info,) = self.cursor.description
        self.assertEqual(
            str(fetch_info),
            "('INTCOL', <DbType DB_TYPE_NUMBER>, 10, None, 9, 0, False)",
        )
        self.assertEqual(
            repr(fetch_info),
            "('INTCOL', <DbType DB_TYPE_NUMBER>, 10, None, 9, 0, False)",
        )

    async def test_5433(self):
        "5433 - test slicing FetchInfo"
        await self.cursor.execute("select IntCol from TestObjects")
        (fetch_info,) = self.cursor.description
        self.assertEqual(fetch_info[1:3], (oracledb.DB_TYPE_NUMBER, 10))

    async def test_5434(self):
        "5434 - test async context manager"
        expected_value = test_env.get_main_user().upper()
        with self.conn.cursor() as cursor:
            await cursor.execute("select user from dual")
            self.assertEqual(await cursor.fetchone(), (expected_value,))
        async with self.conn.cursor() as cursor:
            await cursor.execute("select user from dual")
            self.assertEqual(await cursor.fetchone(), (expected_value,))

    async def test_5435(self):
        "5435 - test metadata requiring multiple packets"
        values = [f"Test value 5435 - {i}" for i in range(1, 301)]
        columns = ", ".join(f"'{v}'" for v in values)
        query = f"select {columns} from dual"
        await self.cursor.execute(query)
        row = await self.cursor.fetchone()
        self.assertEqual(row, tuple(values))

    async def test_5436(self):
        "5436 - test raising no_data_found in PL/SQL"
        with self.assertRaisesFullCode("ORA-01403"):
            await self.cursor.execute("begin raise no_data_found; end;")


if __name__ == "__main__":
    test_env.run_test_cases()
