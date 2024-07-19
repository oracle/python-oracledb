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
2600 - Module for testing timestamp variables
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
            date_interval = datetime.timedelta(days=i)
            date_value = base_date + date_interval
            str_value = str(i * 50)
            fsecond = int(str_value + "0" * (6 - len(str_value)))
            date_col = datetime.datetime(
                date_value.year,
                date_value.month,
                date_value.day,
                date_value.hour,
                date_value.minute,
                i * 2,
                fsecond,
            )
            if i % 2:
                date_interval = datetime.timedelta(days=i + 1)
                date_value = base_date + date_interval
                str_value = str(i * 125)
                fsecond = int(str_value + "0" * (6 - len(str_value)))
                nullable_col = datetime.datetime(
                    date_value.year,
                    date_value.month,
                    date_value.day,
                    date_value.hour,
                    date_value.minute,
                    i * 3,
                    fsecond,
                )
            else:
                nullable_col = None
            precision_col = datetime.datetime(2009, 12, 14)
            data_tuple = (i, date_col, nullable_col, precision_col)
            self.raw_data.append(data_tuple)
            self.data_by_key[i] = data_tuple

    def test_2600(self):
        "2600 - test binding in a timestamp"
        self.cursor.setinputsizes(value=oracledb.DB_TYPE_TIMESTAMP)
        self.cursor.execute(
            "select * from TestTimestamps where TimestampCol = :value",
            value=datetime.datetime(2002, 12, 14, 0, 0, 10, 250000),
        )
        self.assertEqual(self.cursor.fetchall(), [self.data_by_key[5]])

    def test_2601(self):
        "2601 - test binding in a null"
        self.cursor.setinputsizes(value=oracledb.DB_TYPE_TIMESTAMP)
        self.cursor.execute(
            "select * from TestTimestamps where TimestampCol = :value",
            value=None,
        )
        self.assertEqual(self.cursor.fetchall(), [])

    def test_2602(self):
        "2602 - test binding out with set input sizes defined"
        bind_vars = self.cursor.setinputsizes(value=oracledb.DB_TYPE_TIMESTAMP)
        self.cursor.execute(
            """
            begin
                :value := to_timestamp('20021209', 'YYYYMMDD');
            end;
            """
        )
        self.assertEqual(
            bind_vars["value"].getvalue(), datetime.datetime(2002, 12, 9)
        )

    def test_2603(self):
        "2603 - test binding in/out with set input sizes defined"
        bind_vars = self.cursor.setinputsizes(value=oracledb.DB_TYPE_TIMESTAMP)
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

    def test_2604(self):
        "2604 - test binding out with cursor.var() method"
        var = self.cursor.var(oracledb.DB_TYPE_TIMESTAMP)
        self.cursor.execute(
            """
            begin
                :value := to_date('20021231 12:31:00',
                    'YYYYMMDD HH24:MI:SS');
            end;
            """,
            value=var,
        )
        self.assertEqual(
            var.getvalue(), datetime.datetime(2002, 12, 31, 12, 31, 0)
        )

    def test_2605(self):
        "2605 - test binding in/out with cursor.var() method"
        var = self.cursor.var(oracledb.DB_TYPE_TIMESTAMP)
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

    def test_2606(self):
        "2606 - test cursor description is accurate"
        self.cursor.execute("select * from TestTimestamps")
        expected_value = [
            ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
            (
                "TIMESTAMPCOL",
                oracledb.DB_TYPE_TIMESTAMP,
                23,
                None,
                0,
                6,
                False,
            ),
            ("NULLABLECOL", oracledb.DB_TYPE_TIMESTAMP, 23, None, 0, 6, True),
            (
                "TIMESTAMPPRECISIONCOL",
                oracledb.DB_TYPE_TIMESTAMP,
                23,
                None,
                0,
                4,
                True,
            ),
        ]
        self.assertEqual(self.cursor.description, expected_value)

    def test_2607(self):
        "2607 - test that fetching all of the data returns the correct results"
        self.cursor.execute("select * From TestTimestamps order by IntCol")
        self.assertEqual(self.cursor.fetchall(), self.raw_data)
        self.assertEqual(self.cursor.fetchall(), [])

    def test_2608(self):
        "2608 - test that fetching data in chunks returns the correct results"
        self.cursor.execute("select * From TestTimestamps order by IntCol")
        self.assertEqual(self.cursor.fetchmany(3), self.raw_data[0:3])
        self.assertEqual(self.cursor.fetchmany(2), self.raw_data[3:5])
        self.assertEqual(self.cursor.fetchmany(4), self.raw_data[5:9])
        self.assertEqual(self.cursor.fetchmany(3), self.raw_data[9:])
        self.assertEqual(self.cursor.fetchmany(3), [])

    def test_2609(self):
        "2609 - test that fetching a single row returns the correct results"
        self.cursor.execute(
            """
            select *
            from TestTimestamps
            where IntCol in (3, 4)
            order by IntCol
            """
        )
        self.assertEqual(self.cursor.fetchone(), self.data_by_key[3])
        self.assertEqual(self.cursor.fetchone(), self.data_by_key[4])
        self.assertIsNone(self.cursor.fetchone())

    def test_2610(self):
        "2610 - test binding a timestamp with zero fractional seconds"
        self.cursor.setinputsizes(value=oracledb.DB_TYPE_TIMESTAMP)
        self.cursor.execute(
            """
            select *
            from TestTimestamps
            where trunc(TimestampCol) = :value
            """,
            value=datetime.datetime(2002, 12, 14),
        )
        self.assertEqual(self.cursor.fetchall(), [self.data_by_key[5]])


if __name__ == "__main__":
    test_env.run_test_cases()
