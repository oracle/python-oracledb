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
2200 - Module for testing number variables
"""

import decimal
import unittest

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    def output_type_handler_binary_int(self, cursor, metadata):
        return cursor.var(
            oracledb.DB_TYPE_BINARY_INTEGER, arraysize=cursor.arraysize
        )

    def output_type_handler_decimal(self, cursor, metadata):
        if metadata.type_code is oracledb.DB_TYPE_NUMBER:
            return cursor.var(
                str,
                255,
                outconverter=decimal.Decimal,
                arraysize=cursor.arraysize,
            )

    def output_type_handler_str(self, cursor, metadata):
        return cursor.var(str, 255, arraysize=cursor.arraysize)

    def setUp(self):
        super().setUp()
        self.raw_data = []
        self.data_by_key = {}
        for i in range(1, 11):
            number_col = i + i * 0.25
            float_col = i + i * 0.75
            unconstrained_col = i**3 + i * 0.5
            if i % 2:
                nullable_col = 143**i
            else:
                nullable_col = None
            data_tuple = (
                i,
                38**i,
                number_col,
                float_col,
                unconstrained_col,
                nullable_col,
            )
            self.raw_data.append(data_tuple)
            self.data_by_key[i] = data_tuple

    @unittest.skipIf(
        test_env.get_client_version() < (12, 1), "not supported on this client"
    )
    def test_2200(self):
        "2200 - test binding in a boolean"
        result = self.cursor.callfunc(
            "pkg_TestBooleans.GetStringRep", str, [True]
        )
        self.assertEqual(result, "TRUE")

    def test_2201(self):
        "2201 - test binding in a boolean as a number"
        var = self.cursor.var(oracledb.NUMBER)
        var.setvalue(0, True)
        self.cursor.execute("select :1 from dual", [var])
        (result,) = self.cursor.fetchone()
        self.assertEqual(result, 1)
        var.setvalue(0, False)
        self.cursor.execute("select :1 from dual", [var])
        (result,) = self.cursor.fetchone()
        self.assertEqual(result, 0)

    def test_2202(self):
        "2202 - test binding in a decimal.Decimal"
        self.cursor.execute(
            """
            select *
            from TestNumbers
            where NumberCol - :value1 - :value2 = trunc(NumberCol)
            """,
            value1=decimal.Decimal("0.20"),
            value2=decimal.Decimal("0.05"),
        )
        expected_data = [
            self.data_by_key[1],
            self.data_by_key[5],
            self.data_by_key[9],
        ]
        self.assertEqual(self.cursor.fetchall(), expected_data)

    def test_2203(self):
        "2203 - test binding in a float"
        self.cursor.execute(
            """
            select *
            from TestNumbers
            where NumberCol - :value = trunc(NumberCol)
            """,
            value=0.25,
        )
        expected_data = [
            self.data_by_key[1],
            self.data_by_key[5],
            self.data_by_key[9],
        ]
        self.assertEqual(self.cursor.fetchall(), expected_data)

    def test_2204(self):
        "2204 - test binding in an integer"
        self.cursor.execute(
            "select * from TestNumbers where IntCol = :value",
            value=2,
        )
        self.assertEqual(self.cursor.fetchall(), [self.data_by_key[2]])

    def test_2205(self):
        "2205 - test binding in a large long integer as Oracle number"
        in_val = 6088343244
        value_var = self.cursor.var(oracledb.NUMBER)
        value_var.setvalue(0, in_val)
        self.cursor.execute(
            """
            begin
                :value := :value + 5;
            end;
            """,
            value=value_var,
        )
        self.assertEqual(value_var.getvalue(), in_val + 5)

    def test_2206(self):
        "2206 - test binding in a large long integer as Python integer"
        long_value = -9999999999999999999
        self.cursor.execute("select :value from dual", value=long_value)
        (result,) = self.cursor.fetchone()
        self.assertEqual(result, long_value)

    def test_2207(self):
        "2207 - test binding in an integer after setting input sizes to string"
        self.cursor.setinputsizes(value=15)
        self.cursor.execute(
            "select * from TestNumbers where IntCol = :value",
            value=3,
        )
        self.assertEqual(self.cursor.fetchall(), [self.data_by_key[3]])

    def test_2208(self):
        "2208 - test binding in a decimal after setting input sizes to number"
        cursor = self.conn.cursor()
        value = decimal.Decimal("319438950232418390.273596")
        cursor.setinputsizes(value=oracledb.NUMBER)
        cursor.outputtypehandler = self.output_type_handler_decimal
        cursor.execute("select :value from dual", value=value)
        (out_value,) = cursor.fetchone()
        self.assertEqual(out_value, value)

    def test_2209(self):
        "2209 - test binding in a null"
        self.cursor.execute(
            "select * from TestNumbers where IntCol = :value",
            value=None,
        )
        self.assertEqual(self.cursor.fetchall(), [])

    def test_2210(self):
        "2210 - test binding in a number array"
        return_value = self.cursor.var(oracledb.NUMBER)
        array = [r[2] for r in self.raw_data]
        statement = """
                begin
                    :return_value := pkg_TestNumberArrays.TestInArrays(
                        :start_value, :array);
                end;"""
        self.cursor.execute(
            statement, return_value=return_value, start_value=5, array=array
        )
        self.assertEqual(return_value.getvalue(), 73.75)
        array = list(range(15))
        self.cursor.execute(statement, start_value=10, array=array)
        self.assertEqual(return_value.getvalue(), 115.0)

    def test_2211(self):
        "2211 - test binding in a number array (with setinputsizes)"
        return_value = self.cursor.var(oracledb.NUMBER)
        self.cursor.setinputsizes(array=[oracledb.NUMBER, 10])
        array = [r[2] for r in self.raw_data]
        self.cursor.execute(
            """
            begin
                :return_value := pkg_TestNumberArrays.TestInArrays(
                    :start_value, :array);
            end;
            """,
            return_value=return_value,
            start_value=6,
            array=array,
        )
        self.assertEqual(return_value.getvalue(), 74.75)

    def test_2212(self):
        "2212 - test binding in a number array (with arrayvar)"
        return_value = self.cursor.var(oracledb.NUMBER)
        array = self.cursor.arrayvar(
            oracledb.NUMBER, [r[2] for r in self.raw_data]
        )
        self.cursor.execute(
            """
            begin
                :return_value := pkg_TestNumberArrays.TestInArrays(
                    :integer_value, :array);
            end;
            """,
            return_value=return_value,
            integer_value=7,
            array=array,
        )
        self.assertEqual(return_value.getvalue(), 75.75)

    def test_2213(self):
        "2213 - test binding in a zero length number array (with arrayvar)"
        return_value = self.cursor.var(oracledb.NUMBER)
        array = self.cursor.arrayvar(oracledb.NUMBER, 0)
        self.cursor.execute(
            """
            begin
                :return_value := pkg_TestNumberArrays.TestInArrays(
                    :integer_value, :array);
            end;
            """,
            return_value=return_value,
            integer_value=8,
            array=array,
        )
        self.assertEqual(return_value.getvalue(), 8.0)
        self.assertEqual(array.getvalue(), [])

    def test_2214(self):
        "2214 - test binding in/out a number array (with arrayvar)"
        array = self.cursor.arrayvar(oracledb.NUMBER, 10)
        original_data = [r[2] for r in self.raw_data]
        expected_data = [
            original_data[i - 1] * 10 for i in range(1, 6)
        ] + original_data[5:]
        array.setvalue(0, original_data)
        self.cursor.execute(
            """
            begin
                pkg_TestNumberArrays.TestInOutArrays(:num_elems, :array);
            end;
            """,
            num_elems=5,
            array=array,
        )
        self.assertEqual(array.getvalue(), expected_data)

    def test_2215(self):
        "2215 - test binding out a Number array (with arrayvar)"
        array = self.cursor.arrayvar(oracledb.NUMBER, 6)
        expected_data = [i * 100 for i in range(1, 7)]
        self.cursor.execute(
            """
            begin
                pkg_TestNumberArrays.TestOutArrays(:num_elems, :array);
            end;
            """,
            num_elems=6,
            array=array,
        )
        self.assertEqual(array.getvalue(), expected_data)

    def test_2216(self):
        "2216 - test binding out with set input sizes defined"
        bind_vars = self.cursor.setinputsizes(value=oracledb.NUMBER)
        self.cursor.execute(
            """
            begin
                :value := 5;
            end;
            """
        )
        self.assertEqual(bind_vars["value"].getvalue(), 5)

    def test_2217(self):
        "2217 - test binding in/out with set input sizes defined"
        bind_vars = self.cursor.setinputsizes(value=oracledb.NUMBER)
        self.cursor.execute(
            """
            begin
                :value := :value + 5;
            end;
            """,
            value=1.25,
        )
        self.assertEqual(bind_vars["value"].getvalue(), 6.25)

    def test_2218(self):
        "2218 - test binding out with cursor.var() method"
        var = self.cursor.var(oracledb.NUMBER)
        self.cursor.execute(
            """
            begin
                :value := 5;
            end;
            """,
            value=var,
        )
        self.assertEqual(var.getvalue(), 5)

    def test_2219(self):
        "2219 - test binding in/out with cursor.var() method"
        var = self.cursor.var(oracledb.NUMBER)
        var.setvalue(0, 2.25)
        self.cursor.execute(
            """
            begin
                :value := :value + 5;
            end;
            """,
            value=var,
        )
        self.assertEqual(var.getvalue(), 7.25)

    def test_2220(self):
        "2220 - test cursor description is accurate"
        self.cursor.execute("select * from TestNumbers")
        expected_value = [
            ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
            ("LONGINTCOL", oracledb.DB_TYPE_NUMBER, 17, None, 16, 0, False),
            ("NUMBERCOL", oracledb.DB_TYPE_NUMBER, 13, None, 9, 2, False),
            ("FLOATCOL", oracledb.DB_TYPE_NUMBER, 127, None, 126, -127, False),
            (
                "UNCONSTRAINEDCOL",
                oracledb.DB_TYPE_NUMBER,
                127,
                None,
                0,
                -127,
                False,
            ),
            ("NULLABLECOL", oracledb.DB_TYPE_NUMBER, 39, None, 38, 0, True),
        ]
        self.assertEqual(self.cursor.description, expected_value)

    def test_2221(self):
        "2221 - test that fetching all of the data returns the correct results"
        self.cursor.execute("select * From TestNumbers order by IntCol")
        self.assertEqual(self.cursor.fetchall(), self.raw_data)
        self.assertEqual(self.cursor.fetchall(), [])

    def test_2222(self):
        "2222 - test that fetching data in chunks returns the correct results"
        self.cursor.execute("select * From TestNumbers order by IntCol")
        self.assertEqual(self.cursor.fetchmany(3), self.raw_data[0:3])
        self.assertEqual(self.cursor.fetchmany(2), self.raw_data[3:5])
        self.assertEqual(self.cursor.fetchmany(4), self.raw_data[5:9])
        self.assertEqual(self.cursor.fetchmany(3), self.raw_data[9:])
        self.assertEqual(self.cursor.fetchmany(3), [])

    def test_2223(self):
        "2223 - test that fetching a single row returns the correct results"
        self.cursor.execute(
            """
            select *
            from TestNumbers
            where IntCol in (3, 4)
            order by IntCol
            """
        )
        self.assertEqual(self.cursor.fetchone(), self.data_by_key[3])
        self.assertEqual(self.cursor.fetchone(), self.data_by_key[4])
        self.assertIsNone(self.cursor.fetchone())

    def test_2224(self):
        "2224 - test that fetching a long integer returns such in Python"
        self.cursor.execute(
            """
            select NullableCol
            from TestNumbers
            where IntCol = 9
            """
        )
        (col,) = self.cursor.fetchone()
        self.assertEqual(col, 25004854810776297743)

    def test_2225(self):
        "2225 - test fetching a floating point number returns such in Python"
        self.cursor.execute("select 1.25 from dual")
        (result,) = self.cursor.fetchone()
        self.assertEqual(result, 1.25)

    def test_2226(self):
        "2226 - test that fetching an integer returns such in Python"
        self.cursor.execute("select 148 from dual")
        (result,) = self.cursor.fetchone()
        self.assertEqual(result, 148)
        self.assertIsInstance(result, int, "integer not returned")

    def test_2227(self):
        "2227 - test that acceptable boundary numbers are handled properly"
        in_values = [
            decimal.Decimal("9.99999999999999e+125"),
            decimal.Decimal("-9.99999999999999e+125"),
            0.0,
            1e-130,
            -1e-130,
        ]
        out_values = [
            int("9" * 15 + "0" * 111),
            -int("9" * 15 + "0" * 111),
            0,
            1e-130,
            -1e-130,
        ]
        for in_value, out_value in zip(in_values, out_values):
            self.cursor.execute("select :1 from dual", [in_value])
            (result,) = self.cursor.fetchone()
            self.assertEqual(result, out_value)

    def test_2228(self):
        "2228 - test that unacceptable boundary numbers are rejected"
        test_values = [
            (1e126, "DPY-4003"),
            (-1e126, "DPY-4003"),
            (float("inf"), "DPY-4004"),
            (float("-inf"), "DPY-4004"),
            (float("NaN"), "DPY-4004"),
            (decimal.Decimal("1e126"), "DPY-4003"),
            (decimal.Decimal("-1e126"), "DPY-4003"),
            (decimal.Decimal("inf"), "DPY-4004"),
            (decimal.Decimal("-inf"), "DPY-4004"),
            (decimal.Decimal("NaN"), "DPY-4004"),
        ]
        for value, error in test_values:
            with self.assertRaisesFullCode(error):
                self.cursor.execute("select :1 from dual", [value])

    def test_2229(self):
        "2229 - test that fetching the result of division returns a float"
        self.cursor.execute(
            """
            select IntCol / 7
            from TestNumbers
            where IntCol = 1
            """
        )
        (result,) = self.cursor.fetchone()
        self.assertEqual(result, 1.0 / 7.0)
        self.assertIsInstance(result, float, "float not returned")

    def test_2230(self):
        "2230 - test that string format is returned properly"
        var = self.cursor.var(oracledb.NUMBER)
        self.assertIs(var.type, oracledb.DB_TYPE_NUMBER)
        self.assertEqual(
            str(var), "<oracledb.Var of type DB_TYPE_NUMBER with value None>"
        )
        var.setvalue(0, 4.5)
        self.assertEqual(
            str(var), "<oracledb.Var of type DB_TYPE_NUMBER with value 4.5>"
        )

    def test_2231(self):
        "2231 - test that binding binary double is possible"
        statement = "select :1 from dual"
        self.cursor.setinputsizes(oracledb.DB_TYPE_BINARY_DOUBLE)
        self.cursor.execute(statement, (5,))
        self.assertEqual(
            self.cursor.bindvars[0].type, oracledb.DB_TYPE_BINARY_DOUBLE
        )
        (value,) = self.cursor.fetchone()
        self.assertEqual(value, 5)

        self.cursor.execute(statement, (1.5,))
        self.assertEqual(
            self.cursor.bindvars[0].type, oracledb.DB_TYPE_BINARY_DOUBLE
        )
        (value,) = self.cursor.fetchone()
        self.assertEqual(value, 1.5)

        self.cursor.execute(statement, [decimal.Decimal("NaN")])
        self.assertEqual(
            self.cursor.bindvars[0].type, oracledb.DB_TYPE_BINARY_DOUBLE
        )
        (value,) = self.cursor.fetchone()
        self.assertEqual(str(value), str(float("NaN")))

    def test_2232(self):
        "2232 - test fetching numbers as binary integers"
        self.cursor.outputtypehandler = self.output_type_handler_binary_int
        for value in (1, 2**31, 2**63 - 1, -1, -(2**31), -(2**63) + 1):
            self.cursor.execute("select :1 from dual", [str(value)])
            (fetched_value,) = self.cursor.fetchone()
            self.assertEqual(value, fetched_value)

    def test_2233(self):
        "2233 - test binding native integer as an out bind"
        simple_var = self.cursor.var(oracledb.DB_TYPE_BINARY_INTEGER)
        self.cursor.execute("begin :value := 2.9; end;", [simple_var])
        self.assertEqual(simple_var.getvalue(), 2)

        simple_var = self.cursor.var(oracledb.DB_TYPE_BINARY_INTEGER)
        self.cursor.execute("begin :value := 1.5; end;", [simple_var])
        self.assertEqual(simple_var.getvalue(), 1)

    def test_2234(self):
        "2234 - test binding in a native integer"
        statement = "begin :value := :value + 2.5; end;"
        simple_var = self.cursor.var(oracledb.DB_TYPE_BINARY_INTEGER)
        simple_var.setvalue(0, 0)
        self.cursor.execute(statement, [simple_var])
        self.assertEqual(simple_var.getvalue(), 2)

        simple_var.setvalue(0, -5)
        self.cursor.execute(statement, [simple_var])
        self.assertEqual(simple_var.getvalue(), -2)

    def test_2235(self):
        "2235 - test setting decimal value for binary int"
        simple_var = self.cursor.var(oracledb.DB_TYPE_BINARY_INTEGER)
        simple_var.setvalue(0, 2.5)
        self.cursor.execute("begin :value := :value + 2.5; end;", [simple_var])
        self.assertEqual(simple_var.getvalue(), 4)

    def test_2236(self):
        "2236 - bind a large value to binary int"
        simple_var = self.cursor.var(oracledb.DB_TYPE_BINARY_INTEGER)
        self.cursor.execute(
            "begin :value := POWER(2, 31) - 1; end;", [simple_var]
        )
        self.assertEqual(simple_var.getvalue(), 2**31 - 1)

        self.cursor.execute(
            "begin :value := POWER(-2, 31) - 1; end;", [simple_var]
        )
        self.assertEqual(simple_var.getvalue(), -(2**31) - 1)

    def test_2237(self):
        "2237 - fetch a number with oracledb.defaults.fetch_lobs = False"
        with test_env.DefaultsContextManager("fetch_lobs", False):
            self.cursor.execute("select 1 from dual")
            (result,) = self.cursor.fetchone()
            self.assertIsInstance(result, int)

    def test_2238(self):
        "2238 - fetch a small constant with a decimal point"
        self.cursor.outputtypehandler = self.output_type_handler_str
        self.cursor.execute("select 3 / 2 from dual")
        (result,) = self.cursor.fetchone()
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "1")
        self.assertEqual(result[2], "5")


if __name__ == "__main__":
    test_env.run_test_cases()
