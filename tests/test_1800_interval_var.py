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
1800 - Module for testing interval variables
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
            delta = datetime.timedelta(
                days=i, hours=i, minutes=i * 2, seconds=i * 3
            )
            if i % 2 == 0:
                nullable_delta = None
            else:
                nullable_delta = datetime.timedelta(
                    days=i + 5,
                    hours=i + 2,
                    minutes=i * 2 + 5,
                    seconds=i * 3 + 5,
                )
            precision_col = datetime.timedelta(
                days=8,
                hours=5,
                minutes=15,
                seconds=0,
            )
            precision_scale_col = datetime.timedelta(
                days=10,
                hours=12,
                minutes=15,
                seconds=15,
            )
            data_tuple = (
                i,
                delta,
                nullable_delta,
                precision_col,
                precision_scale_col,
            )
            self.raw_data.append(data_tuple)
            self.data_by_key[i] = data_tuple

    def test_1800(self):
        "1800 - test binding in an interval"
        self.cursor.setinputsizes(value=oracledb.DB_TYPE_INTERVAL_DS)
        value = datetime.timedelta(days=5, hours=5, minutes=10, seconds=15)
        self.cursor.execute(
            "select * from TestIntervals where IntervalCol = :value",
            value=value,
        )
        self.assertEqual(self.cursor.fetchall(), [self.data_by_key[5]])

    def test_1801(self):
        "1801 - test binding in a null"
        self.cursor.setinputsizes(value=oracledb.DB_TYPE_INTERVAL_DS)
        self.cursor.execute(
            "select * from TestIntervals where IntervalCol = :value",
            value=None,
        )
        self.assertEqual(self.cursor.fetchall(), [])

    def test_1802(self):
        "1802 - test binding out with set input sizes defined"
        bind_vars = self.cursor.setinputsizes(
            value=oracledb.DB_TYPE_INTERVAL_DS
        )
        self.cursor.execute(
            """
            begin
                :value := to_dsinterval('8 09:24:18.123789');
            end;
            """
        )
        expected_value = datetime.timedelta(
            days=8, hours=9, minutes=24, seconds=18, microseconds=123789
        )
        self.assertEqual(bind_vars["value"].getvalue(), expected_value)

    def test_1803(self):
        "1803 - test binding in/out with set input sizes defined"
        bind_vars = self.cursor.setinputsizes(
            value=oracledb.DB_TYPE_INTERVAL_DS
        )
        self.cursor.execute(
            """
            begin
                :value := :value + to_dsinterval('5 08:30:00');
            end;
            """,
            value=datetime.timedelta(days=5, hours=2, minutes=15),
        )
        expected_value = datetime.timedelta(days=10, hours=10, minutes=45)
        self.assertEqual(bind_vars["value"].getvalue(), expected_value)

    def test_1804(self):
        "1804 - test binding in/out with set input sizes defined"
        bind_vars = self.cursor.setinputsizes(
            value=oracledb.DB_TYPE_INTERVAL_DS
        )
        self.cursor.execute(
            """
            begin
                :value := :value + to_dsinterval('5 08:30:00');
            end;
            """,
            value=datetime.timedelta(days=5, seconds=12.123789),
        )
        expected_value = datetime.timedelta(
            days=10, hours=8, minutes=30, seconds=12, microseconds=123789
        )
        self.assertEqual(bind_vars["value"].getvalue(), expected_value)

    def test_1805(self):
        "1805 - test binding out with cursor.var() method"
        var = self.cursor.var(oracledb.DB_TYPE_INTERVAL_DS)
        self.cursor.execute(
            """
            begin
                :value := to_dsinterval('15 18:35:45.586');
            end;
            """,
            value=var,
        )
        expected_value = datetime.timedelta(
            days=15, hours=18, minutes=35, seconds=45, milliseconds=586
        )
        self.assertEqual(var.getvalue(), expected_value)

    def test_1806(self):
        "1806 - test binding in/out with cursor.var() method"
        var = self.cursor.var(oracledb.DB_TYPE_INTERVAL_DS)
        var.setvalue(0, datetime.timedelta(days=1, minutes=50))
        self.cursor.execute(
            """
            begin
                :value := :value + to_dsinterval('8 05:15:00');
            end;
            """,
            value=var,
        )
        expected_value = datetime.timedelta(days=9, hours=6, minutes=5)
        self.assertEqual(var.getvalue(), expected_value)

    def test_1807(self):
        "1807 - test cursor description is accurate"
        self.cursor.execute("select * from TestIntervals")
        expected_value = [
            ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
            (
                "INTERVALCOL",
                oracledb.DB_TYPE_INTERVAL_DS,
                None,
                None,
                2,
                6,
                False,
            ),
            (
                "NULLABLECOL",
                oracledb.DB_TYPE_INTERVAL_DS,
                None,
                None,
                2,
                6,
                True,
            ),
            (
                "INTERVALPRECISIONCOL",
                oracledb.DB_TYPE_INTERVAL_DS,
                None,
                None,
                7,
                6,
                True,
            ),
            (
                "INTERVALPRECISIONSCALECOL",
                oracledb.DB_TYPE_INTERVAL_DS,
                None,
                None,
                8,
                9,
                True,
            ),
        ]
        self.assertEqual(self.cursor.description, expected_value)

    def test_1808(self):
        "1808 - test that fetching all of the data returns the correct results"
        self.cursor.execute("select * From TestIntervals order by IntCol")
        self.assertEqual(self.cursor.fetchall(), self.raw_data)
        self.assertEqual(self.cursor.fetchall(), [])

    def test_1809(self):
        "1809 - test that fetching data in chunks returns the correct results"
        self.cursor.execute("select * From TestIntervals order by IntCol")
        self.assertEqual(self.cursor.fetchmany(3), self.raw_data[0:3])
        self.assertEqual(self.cursor.fetchmany(2), self.raw_data[3:5])
        self.assertEqual(self.cursor.fetchmany(4), self.raw_data[5:9])
        self.assertEqual(self.cursor.fetchmany(3), self.raw_data[9:])
        self.assertEqual(self.cursor.fetchmany(3), [])

    def test_1810(self):
        "1810 - test that fetching a single row returns the correct results"
        self.cursor.execute(
            """
            select *
            from TestIntervals
            where IntCol in (3, 4)
            order by IntCol
            """
        )
        self.assertEqual(self.cursor.fetchone(), self.data_by_key[3])
        self.assertEqual(self.cursor.fetchone(), self.data_by_key[4])
        self.assertIsNone(self.cursor.fetchone())

    def test_1811(self):
        "1811 - test binding and fetching a negative interval"
        value = datetime.timedelta(days=-1, seconds=86314, microseconds=431152)
        self.cursor.execute("select :1 from dual", [value])
        (result,) = self.cursor.fetchone()
        self.assertEqual(result, value)


if __name__ == "__main__":
    test_env.run_test_cases()
