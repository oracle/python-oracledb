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
3900 - Module for testing the cursor execute() method
"""

import collections

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    def test_3900(self):
        "3900 - test executing a statement without any arguments"
        result = self.cursor.execute("begin null; end;")
        self.assertIsNone(result)

    def test_3901(self):
        "3901 - test executing a None statement with bind variables"
        cursor = self.conn.cursor()
        with self.assertRaisesFullCode("DPY-2001"):
            cursor.execute(None, x=5)

    def test_3902(self):
        "3902 - test executing a statement with args and empty keyword args"
        simple_var = self.cursor.var(oracledb.NUMBER)
        args = [simple_var]
        kwargs = {}
        result = self.cursor.execute("begin :1 := 25; end;", args, **kwargs)
        self.assertIsNone(result)
        self.assertEqual(simple_var.getvalue(), 25)

    def test_3903(self):
        "3903 - test executing a statement with keyword arguments"
        simple_var = self.cursor.var(oracledb.NUMBER)
        result = self.cursor.execute(
            "begin :value := 5; end;", value=simple_var
        )
        self.assertIsNone(result)
        self.assertEqual(simple_var.getvalue(), 5)

    def test_3904(self):
        "3904 - test executing a statement with a dictionary argument"
        simple_var = self.cursor.var(oracledb.NUMBER)
        dict_arg = dict(value=simple_var)
        result = self.cursor.execute("begin :value := 10; end;", dict_arg)
        self.assertIsNone(result)
        self.assertEqual(simple_var.getvalue(), 10)

    def test_3905(self):
        "3905 - test executing a statement with both a dict and keyword args"
        simple_var = self.cursor.var(oracledb.NUMBER)
        dict_arg = dict(value=simple_var)
        with self.assertRaisesFullCode("DPY-2005"):
            self.cursor.execute(
                "begin :value := 15; end;", dict_arg, value=simple_var
            )

    def test_3906(self):
        "3906 - test executing a statement and then changing the array size"
        self.cursor.execute("select IntCol from TestNumbers")
        self.cursor.arraysize = 20
        self.assertEqual(len(self.cursor.fetchall()), 10)

    def test_3907(self):
        "3907 - test that subsequent executes succeed after bad execute"
        sql = "begin raise_application_error(-20000, 'this); end;"
        with self.assertRaisesFullCode("DPY-2041"):
            self.cursor.execute(sql)
        self.cursor.execute("begin null; end;")

    def test_3908(self):
        "3908 - test that subsequent fetches fail after bad execute"
        with self.assertRaisesFullCode("ORA-00904"):
            self.cursor.execute("select y from dual")
        with self.assertRaisesFullCode("DPY-1003"):
            self.cursor.fetchall()

    def test_3909(self):
        "3909 - test executing a statement with an incorrect named bind"
        sql = "select * from TestStrings where IntCol = :value"
        with self.assertRaisesFullCode("DPY-4008", "ORA-01036"):
            self.cursor.execute(sql, value2=3)

    def test_3910(self):
        "3910 - test executing a statement with named binds"
        result = self.cursor.execute(
            """
            select *
            from TestNumbers
            where IntCol = :value1 and LongIntCol = :value2
            """,
            value1=1,
            value2=38,
        )
        self.assertEqual(len(result.fetchall()), 1)

    def test_3911(self):
        "3911 - test executing a statement with an incorrect positional bind"
        sql = """
                select *
                from TestNumbers
                where IntCol = :value and LongIntCol = :value2"""
        with self.assertRaisesFullCode("DPY-4009", "ORA-01008"):
            self.cursor.execute(sql, [3])

    def test_3912(self):
        "3912 - test executing a statement with positional binds"
        result = self.cursor.execute(
            """
            select *
            from TestNumbers
            where IntCol = :value and LongIntCol = :value2
            """,
            [1, 38],
        )
        self.assertEqual(len(result.fetchall()), 1)

    def test_3913(self):
        "3913 - test executing a statement after rebinding a named bind"
        statement = "begin :value := :value2 + 5; end;"
        simple_var = self.cursor.var(oracledb.NUMBER)
        simple_var2 = self.cursor.var(oracledb.NUMBER)
        simple_var2.setvalue(0, 5)
        result = self.cursor.execute(
            statement, value=simple_var, value2=simple_var2
        )
        self.assertIsNone(result)
        self.assertEqual(simple_var.getvalue(), 10)

        simple_var = self.cursor.var(oracledb.NATIVE_FLOAT)
        simple_var2 = self.cursor.var(oracledb.NATIVE_FLOAT)
        simple_var2.setvalue(0, 10)
        result = self.cursor.execute(
            statement, value=simple_var, value2=simple_var2
        )
        self.assertIsNone(result)
        self.assertEqual(simple_var.getvalue(), 15)

    def test_3914(self):
        "3914 - test executing a PL/SQL statement with duplicate binds"
        simple_var = self.cursor.var(oracledb.NUMBER)
        simple_var.setvalue(0, 5)
        result = self.cursor.execute(
            """
            begin
                :value := :value + 5;
            end;
            """,
            value=simple_var,
        )
        self.assertIsNone(result)
        self.assertEqual(simple_var.getvalue(), 10)

    def test_3915(self):
        "3915 - test executing a PL/SQL statement with duplicate binds"
        simple_var = self.cursor.var(oracledb.NUMBER)
        simple_var.setvalue(0, 5)
        self.cursor.execute("begin :value := :value + 5; end;", [simple_var])
        self.assertEqual(simple_var.getvalue(), 10)

    def test_3916(self):
        "3916 - test executing a statement with an incorrect number of binds"
        statement = "begin :value := :value2 + 5; end;"
        var = self.cursor.var(oracledb.NUMBER)
        var.setvalue(0, 5)
        with self.assertRaisesFullCode("DPY-4010", "ORA-01008"):
            self.cursor.execute(statement)
        with self.assertRaisesFullCode("DPY-4010", "ORA-01008"):
            self.cursor.execute(statement, value=var)
        with self.assertRaisesFullCode("DPY-4008", "ORA-01036"):
            self.cursor.execute(statement, value=var, value2=var, value3=var)

    def test_3917(self):
        "3917 - change in size on subsequent binds does not use optimised path"
        self.cursor.execute("truncate table TestTempTable")
        data = [(1, "Test String #1"), (2, "ABC" * 100)]
        for row in data:
            self.cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (:1, :2)
                """,
                row,
            )
        self.conn.commit()
        self.cursor.execute("select IntCol, StringCol1 from TestTempTable")
        self.assertEqual(self.cursor.fetchall(), data)

    def test_3918(self):
        "3918 - test that dml can use optimised path"
        data_to_insert = [(i + 1, f"Test String #{i + 1}") for i in range(3)]
        self.cursor.execute("truncate table TestTempTable")
        for row in data_to_insert:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    insert into TestTempTable (IntCol, StringCol1)
                    values (:1, :2)
                    """,
                    row,
                )
        self.conn.commit()
        self.cursor.execute(
            "select IntCol, StringCol1 from TestTempTable order by IntCol"
        )
        self.assertEqual(self.cursor.fetchall(), data_to_insert)

    def test_3919(self):
        "3919 - test calling execute() with invalid parameters"
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        with self.assertRaisesFullCode("DPY-2003"):
            self.cursor.execute(sql, "These are not valid parameters")

    def test_3920(self):
        "3920 - test calling execute() with mixed binds"
        self.cursor.execute("truncate table TestTempTable")
        self.cursor.setinputsizes(None, None, str)
        data = dict(val1=1, val2="Test String 1")
        with self.assertRaisesFullCode("DPY-2006"):
            self.cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (:1, :2)
                returning StringCol1 into :out_var
                """,
                data,
            )

    def test_3921(self):
        "3921 - test binding by name with double quotes"
        data = {'"_value1"': 1, '"VaLue_2"': 2, '"3VALUE"': 3}
        self.cursor.execute(
            'select :"_value1" + :"VaLue_2" + :"3VALUE" from dual',
            data,
        )
        (result,) = self.cursor.fetchone()
        self.assertEqual(result, 6)

    def test_3922(self):
        "3922 - test executing a statement with different input buffer sizes"
        sql = """
                insert into TestTempTable (IntCol, StringCol1, StringCol2)
                values (:int_col, :str_val1, :str_val2) returning IntCol
                into :ret_data"""
        values1 = {"int_col": 1, "str_val1": '{"a", "b"}', "str_val2": None}
        values2 = {"int_col": 2, "str_val1": None, "str_val2": '{"a", "b"}'}
        values3 = {"int_col": 3, "str_val1": '{"a"}', "str_val2": None}

        self.cursor.execute("truncate table TestTempTable")
        ret_bind = self.cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=1)
        self.cursor.setinputsizes(ret_data=ret_bind)
        self.cursor.execute(sql, values1)
        self.assertEqual(ret_bind.values, [["1"]])

        ret_bind = self.cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=1)
        self.cursor.setinputsizes(ret_data=ret_bind)
        self.cursor.execute(sql, values2)
        self.assertEqual(ret_bind.values, [["2"]])

        ret_bind = self.cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=1)
        self.cursor.setinputsizes(ret_data=ret_bind)
        self.cursor.execute(sql, values3)
        self.assertEqual(ret_bind.values, [["3"]])

    def test_3923(self):
        "3923 - test using rowfactory"
        self.cursor.execute("truncate table TestTempTable")
        self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (1, 'Test 1')
            """
        )
        self.conn.commit()
        self.cursor.execute("select IntCol, StringCol1 from TestTempTable")
        column_names = [col[0] for col in self.cursor.description]

        def rowfactory(*row):
            return dict(zip(column_names, row))

        self.cursor.rowfactory = rowfactory
        self.assertEqual(self.cursor.rowfactory, rowfactory)
        self.assertEqual(
            self.cursor.fetchall(), [{"INTCOL": 1, "STRINGCOL1": "Test 1"}]
        )

    def test_3924(self):
        "3924 - test executing same query after setting rowfactory"
        self.cursor.execute("truncate table TestTempTable")
        data = [(1, "Test 1"), (2, "Test 2")]
        self.cursor.executemany(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            data,
        )
        self.conn.commit()
        self.cursor.execute("select IntCol, StringCol1 from TestTempTable")
        column_names = [col[0] for col in self.cursor.description]
        self.cursor.rowfactory = lambda *row: dict(zip(column_names, row))
        results1 = self.cursor.fetchall()
        self.cursor.execute("select IntCol, StringCol1 from TestTempTable")
        results2 = self.cursor.fetchall()
        self.assertEqual(results1, results2)

    def test_3925(self):
        "3925 - test executing different query after setting rowfactory"
        self.cursor.execute("truncate table TestTempTable")
        data = [(1, "Test 1"), (2, "Test 2")]
        self.cursor.executemany(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            data,
        )
        self.conn.commit()
        self.cursor.execute("select IntCol, StringCol1 from TestTempTable")
        column_names = [col[0] for col in self.cursor.description]
        self.cursor.rowfactory = lambda *row: dict(zip(column_names, row))
        self.cursor.execute(
            """
            select IntCol, StringCol
            from TestSTrings
            where IntCol between 1 and 3 order by IntCol
            """
        )
        expected_data = [(1, "String 1"), (2, "String 2"), (3, "String 3")]
        self.assertEqual(self.cursor.fetchall(), expected_data)

    def test_3926(self):
        "3926 - test setting rowfactory on a REF cursor"
        with self.conn.cursor() as cursor:
            sql_function = "pkg_TestRefCursors.TestReturnCursor"
            ref_cursor = cursor.callfunc(
                sql_function, oracledb.DB_TYPE_CURSOR, [2]
            )
            column_names = [col[0] for col in ref_cursor.description]
            ref_cursor.rowfactory = lambda *row: dict(zip(column_names, row))
            expected_value = [
                {"INTCOL": 1, "STRINGCOL": "String 1"},
                {"INTCOL": 2, "STRINGCOL": "String 2"},
            ]
            self.assertEqual(ref_cursor.fetchall(), expected_value)

    def test_3927(self):
        "3927 - test using a subclassed string as bind parameter keys"

        class my_str(str):
            pass

        self.cursor.execute("truncate table TestTempTable")
        keys = {my_str("str_val"): oracledb.DB_TYPE_VARCHAR}
        self.cursor.setinputsizes(**keys)
        values = {
            my_str("int_val"): 3927,
            my_str("str_val"): "3927 - String Value",
        }
        self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:int_val, :str_val)
            """,
            values,
        )
        self.cursor.execute("select IntCol, StringCol1 from TestTempTable")
        self.assertEqual(
            self.cursor.fetchall(), [(3927, "3927 - String Value")]
        )

    def test_3928(self):
        "3928 - test using a sequence of parameters other than a list or tuple"

        class MySeq(collections.abc.Sequence):
            def __init__(self, *data):
                self.data = data

            def __len__(self):
                return len(self.data)

            def __getitem__(self, index):
                return self.data[index]

        values_to_insert = [MySeq(1, "String 1"), MySeq(2, "String 2")]
        expected_data = [tuple(value) for value in values_to_insert]
        self.cursor.execute("truncate table TestTempTable")
        self.cursor.executemany(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:int_val, :str_val)
            """,
            values_to_insert,
        )
        self.cursor.execute(
            """
            select IntCol, StringCol1
            from TestTempTable
            order by IntCol
            """
        )
        self.assertEqual(self.cursor.fetchall(), expected_data)

    def test_3929(self):
        "3929 - test an output type handler with prefetch > arraysize"

        def type_handler(cursor, metadata):
            return cursor.var(metadata.type_code, arraysize=cursor.arraysize)

        self.cursor.arraysize = 2
        self.cursor.prefetchrows = 3
        self.cursor.outputtypehandler = type_handler
        self.cursor.execute("select level from dual connect by level <= 5")
        self.assertEqual(
            self.cursor.fetchall(), [(1,), (2,), (3,), (4,), (5,)]
        )

    def test_3930(self):
        "3930 - test setinputsizes() but without binding"
        self.cursor.setinputsizes(None, int)
        sql = "select :1, : 2 from dual"
        with self.assertRaisesFullCode("ORA-01008", "DPY-4010"):
            self.cursor.execute(sql, [])

    def test_3931(self):
        "3931 - test getting FetchInfo attributes"
        type_obj = self.conn.gettype("UDT_OBJECT")
        varchar_ratio, _ = test_env.get_charset_ratios()
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
            self.cursor.execute(sql)
            (fetch_info,) = self.cursor.description
            self.assertIsInstance(fetch_info, oracledb.FetchInfo)
            self.assertEqual(fetch_info.display_size, display_size)
            self.assertEqual(fetch_info.internal_size, internal_size)
            if test_env.get_server_version() > (12, 2):
                self.assertEqual(fetch_info.is_json, is_json)
            self.assertEqual(fetch_info.name, name)
            self.assertEqual(fetch_info.null_ok, null_ok)
            self.assertEqual(fetch_info.precision, precision)
            self.assertEqual(fetch_info.scale, scale)
            self.assertEqual(fetch_info.type, typ)
            self.assertEqual(fetch_info.type_code, type_code)
            self.assertIsNone(fetch_info.vector_dimensions)
            self.assertIsNone(fetch_info.vector_format)

    def test_3932(self):
        "3932 - test FetchInfo repr() and str()"
        self.cursor.execute("select IntCol from TestObjects")
        (fetch_info,) = self.cursor.description
        self.assertEqual(
            str(fetch_info),
            "('INTCOL', <DbType DB_TYPE_NUMBER>, 10, None, 9, 0, False)",
        )
        self.assertEqual(
            repr(fetch_info),
            "('INTCOL', <DbType DB_TYPE_NUMBER>, 10, None, 9, 0, False)",
        )

    def test_3933(self):
        "3933 - test slicing FetchInfo"
        self.cursor.execute("select IntCol from TestObjects")
        (fetch_info,) = self.cursor.description
        self.assertEqual(fetch_info[1:3], (oracledb.DB_TYPE_NUMBER, 10))

    def test_3934(self):
        "3934 - test rowcount is zero for PL/SQL"
        self.cursor.execute("begin null; end;")
        self.assertEqual(self.cursor.rowcount, 0)
        self.cursor.execute("select user from dual")
        self.cursor.fetchall()
        self.assertEqual(self.cursor.rowcount, 1)
        self.cursor.execute("begin null; end;")
        self.assertEqual(self.cursor.rowcount, 0)

    def test_3935(self):
        "3935 - test raising no_data_found in PL/SQL"
        with self.assertRaisesFullCode("ORA-01403"):
            self.cursor.execute("begin raise no_data_found; end;")


if __name__ == "__main__":
    test_env.run_test_cases()
