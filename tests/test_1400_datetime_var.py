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
1400 - Module for testing date/time variables
"""

import datetime

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.raw_data = []
        self.data_by_key = {}
        for i in range(1, 11):
            base_date = datetime.datetime(2002, 12, 9)
            date_interval = datetime.timedelta(
                days=i, hours=i * 2, minutes=i * 24
            )
            date_col = base_date + date_interval
            if i % 2:
                date_interval = datetime.timedelta(
                    days=i * 2, hours=i * 3, minutes=i * 36
                )
                nullable_col = base_date + date_interval
            else:
                nullable_col = None
            data_tuple = (i, date_col, nullable_col)
            self.raw_data.append(data_tuple)
            self.data_by_key[i] = data_tuple

    def test_1400(self):
        "1400 - test binding in a date"
        self.cursor.execute(
            "select * from TestDates where DateCol = :value",
            value=datetime.datetime(2002, 12, 13, 9, 36, 0),
        )
        self.assertEqual(self.cursor.fetchall(), [self.data_by_key[4]])

    def test_1401(self):
        "1401 - test binding in a datetime.datetime value"
        self.cursor.execute(
            "select * from TestDates where DateCol = :value",
            value=datetime.datetime(2002, 12, 13, 9, 36, 0),
        )
        self.assertEqual(self.cursor.fetchall(), [self.data_by_key[4]])

    def test_1402(self):
        "1402 - test binding date in a datetime variable"
        var = self.cursor.var(oracledb.DATETIME)
        date_val = datetime.date.today()
        var.setvalue(0, date_val)
        self.cursor.execute("select :1 from dual", [var])
        (result,) = self.cursor.fetchone()
        self.assertEqual(result.date(), date_val)

    def test_1403(self):
        "1403 - test binding in a date after setting input sizes to a string"
        self.cursor.setinputsizes(value=15)
        self.cursor.execute(
            "select * from TestDates where DateCol = :value",
            value=datetime.datetime(2002, 12, 14, 12, 0, 0),
        )
        self.assertEqual(self.cursor.fetchall(), [self.data_by_key[5]])

    def test_1404(self):
        "1404 - test binding in a null"
        self.cursor.setinputsizes(value=oracledb.DATETIME)
        self.cursor.execute(
            "select * from TestDates where DateCol = :value",
            value=None,
        )
        self.assertEqual(self.cursor.fetchall(), [])

    def test_1405(self):
        "1405 - test binding in a date array"
        array = [r[1] for r in self.raw_data]
        return_value = self.cursor.callfunc(
            "pkg_TestDateArrays.TestInArrays",
            oracledb.DB_TYPE_NUMBER,
            [5, datetime.date(2002, 12, 12), array],
        )
        self.assertEqual(return_value, 35.5)
        array += array[:5]
        return_value = self.cursor.callfunc(
            "pkg_TestDateArrays.TestInArrays",
            oracledb.DB_TYPE_NUMBER,
            [7, datetime.date(2002, 12, 13), array],
        )
        self.assertEqual(return_value, 24.0)

    def test_1406(self):
        "1406 - test binding in a date array (with setinputsizes)"
        return_value = self.cursor.var(oracledb.NUMBER)
        self.cursor.setinputsizes(array=[oracledb.DATETIME, 10])
        array = [r[1] for r in self.raw_data]
        self.cursor.execute(
            """
            begin
                :return_value := pkg_TestDateArrays.TestInArrays(
                    :start_value, :base_date, :array);
            end;
            """,
            return_value=return_value,
            start_value=6,
            base_date=oracledb.Date(2002, 12, 13),
            array=array,
        )
        self.assertEqual(return_value.getvalue(), 26.5)

    def test_1407(self):
        "1407 - test binding in a date array (with arrayvar)"
        return_value = self.cursor.var(oracledb.NUMBER)
        array = self.cursor.arrayvar(oracledb.DATETIME, 10, 20)
        array.setvalue(0, [r[1] for r in self.raw_data])
        self.cursor.execute(
            """
            begin
                :return_value := pkg_TestDateArrays.TestInArrays(
                    :start_value, :base_date, :array);
            end;
            """,
            return_value=return_value,
            start_value=7,
            base_date=oracledb.Date(2002, 12, 14),
            array=array,
        )
        self.assertEqual(return_value.getvalue(), 17.5)

    def test_1408(self):
        "1408 - test binding in/out a date array (with arrayvar)"
        array = self.cursor.arrayvar(oracledb.DATETIME, 10, 100)
        original_data = [r[1] for r in self.raw_data]
        array.setvalue(0, original_data)
        self.cursor.execute(
            """
            begin
                pkg_TestDateArrays.TestInOutArrays(:num_elems, :array);
            end;
            """,
            num_elems=5,
            array=array,
        )
        expected_value = [
            datetime.datetime(2002, 12, 17, 2, 24, 0),
            datetime.datetime(2002, 12, 18, 4, 48, 0),
            datetime.datetime(2002, 12, 19, 7, 12, 0),
            datetime.datetime(2002, 12, 20, 9, 36, 0),
            datetime.datetime(2002, 12, 21, 12, 0, 0),
        ] + original_data[5:]
        self.assertEqual(array.getvalue(), expected_value)

    def test_1409(self):
        "1409 - test binding out a date array (with arrayvar)"
        array = self.cursor.arrayvar(oracledb.DATETIME, 6, 100)
        self.cursor.execute(
            """
            begin
                pkg_TestDateArrays.TestOutArrays(:num_elems, :array);
            end;
            """,
            num_elems=6,
            array=array,
        )
        expected_value = [
            datetime.datetime(2002, 12, 13, 4, 48, 0),
            datetime.datetime(2002, 12, 14, 9, 36, 0),
            datetime.datetime(2002, 12, 15, 14, 24, 0),
            datetime.datetime(2002, 12, 16, 19, 12, 0),
            datetime.datetime(2002, 12, 18, 0, 0, 0),
            datetime.datetime(2002, 12, 19, 4, 48, 0),
        ]
        self.assertEqual(array.getvalue(), expected_value)

    def test_1410(self):
        "1410 - test binding out with set input sizes defined"
        bind_vars = self.cursor.setinputsizes(value=oracledb.DATETIME)
        self.cursor.execute(
            """
            begin
                :value := to_date(20021209, 'YYYYMMDD');
            end;
            """
        )
        self.assertEqual(
            bind_vars["value"].getvalue(), datetime.datetime(2002, 12, 9)
        )

    def test_1411(self):
        "1411 - test binding in/out with set input sizes defined"
        bind_vars = self.cursor.setinputsizes(value=oracledb.DATETIME)
        self.cursor.execute(
            """
            begin
                :value := :value + 5.25;
            end;
            """,
            value=datetime.datetime(2002, 12, 12, 10, 0, 0),
        )
        self.assertEqual(
            bind_vars["value"].getvalue(),
            datetime.datetime(2002, 12, 17, 16, 0, 0),
        )

    def test_1412(self):
        "1412 - test binding out with cursor.var() method"
        var = self.cursor.var(oracledb.DATETIME)
        self.cursor.execute(
            """
            begin
                :value := to_date('20021231 12:31:00', 'YYYYMMDD HH24:MI:SS');
            end;
            """,
            value=var,
        )
        self.assertEqual(
            var.getvalue(), datetime.datetime(2002, 12, 31, 12, 31, 0)
        )

    def test_1413(self):
        "1413 - test binding in/out with cursor.var() method"
        var = self.cursor.var(oracledb.DATETIME)
        var.setvalue(0, datetime.datetime(2002, 12, 9, 6, 0, 0))
        self.cursor.execute(
            """
            begin
                :value := :value + 5.25;
            end;
            """,
            value=var,
        )
        self.assertEqual(
            var.getvalue(), datetime.datetime(2002, 12, 14, 12, 0, 0)
        )

    def test_1414(self):
        "1414 - test cursor description is accurate"
        self.cursor.execute("select * from TestDates")
        expected_value = [
            ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
            ("DATECOL", oracledb.DB_TYPE_DATE, 23, None, None, None, False),
            ("NULLABLECOL", oracledb.DB_TYPE_DATE, 23, None, None, None, True),
        ]
        self.assertEqual(self.cursor.description, expected_value)

    def test_1415(self):
        "1415 - test that fetching all of the data returns the correct results"
        self.cursor.execute("select * From TestDates order by IntCol")
        self.assertEqual(self.cursor.fetchall(), self.raw_data)
        self.assertEqual(self.cursor.fetchall(), [])

    def test_1416(self):
        "1416 - test that fetching data in chunks returns the correct results"
        self.cursor.execute("select * From TestDates order by IntCol")
        self.assertEqual(self.cursor.fetchmany(3), self.raw_data[0:3])
        self.assertEqual(self.cursor.fetchmany(2), self.raw_data[3:5])
        self.assertEqual(self.cursor.fetchmany(4), self.raw_data[5:9])
        self.assertEqual(self.cursor.fetchmany(3), self.raw_data[9:])
        self.assertEqual(self.cursor.fetchmany(3), [])

    def test_1417(self):
        "1417 - test that fetching a single row returns the correct results"
        self.cursor.execute(
            """
            select *
            from TestDates
            where IntCol in (3, 4)
            order by IntCol
            """
        )
        self.assertEqual(self.cursor.fetchone(), self.data_by_key[3])
        self.assertEqual(self.cursor.fetchone(), self.data_by_key[4])
        self.assertIsNone(self.cursor.fetchone())

    def test_1418(self):
        "1418 - test fetching a date with year < 0"
        with self.assertRaises(ValueError):
            self.cursor.execute(
                "select to_date('-4712-01-01', 'SYYYY-MM-DD') from dual"
            )
            self.cursor.fetchone()


if __name__ == "__main__":
    test_env.run_test_cases()
