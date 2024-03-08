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
3500 - Module for testing the JSON data type.
"""

import datetime
import decimal
import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_client_version() >= (21, 0), "unsupported client"
)
@unittest.skipUnless(
    test_env.get_server_version() >= (21, 0), "unsupported server"
)
class TestCase(test_env.BaseTestCase):
    json_data = [
        True,
        False,
        "String",
        b"Some Bytes",
        {},
        {"name": None},
        {"name": "John"},
        {"age": 30},
        {"Permanent": True},
        {
            "employee": {
                "name": "John",
                "age": 30,
                "city": "Delhi",
                "Parmanent": True,
            }
        },
        {"employees": ["John", "Matthew", "James"]},
        {
            "employees": [
                {"employee1": {"name": "John", "city": "Delhi"}},
                {"employee2": {"name": "Matthew", "city": "Mumbai"}},
                {"employee3": {"name": "James", "city": "Bangalore"}},
            ]
        },
    ]

    def __bind_scalar_as_json(self, data):
        self.cursor.execute("delete from TestJson")
        out_var = self.cursor.var(oracledb.DB_TYPE_JSON, arraysize=len(data))
        self.cursor.setinputsizes(None, oracledb.DB_TYPE_JSON, out_var)
        bind_data = list(enumerate(data))
        self.cursor.executemany(
            """
            insert into TestJson values (:1, :2)
            returning JsonCol into :json_out
            """,
            bind_data,
        )
        self.conn.commit()
        self.assertEqual(out_var.values, [[value] for value in data])

    def test_3500(self):
        "3500 - insert and fetch single row with JSON"
        self.cursor.execute("delete from TestJson")
        self.cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
        self.cursor.execute(
            "insert into TestJson values (:1, :2)", [1, self.json_data]
        )
        self.cursor.execute("select JsonCol from TestJson")
        (result,) = self.cursor.fetchone()
        self.assertEqual(result, self.json_data)

    def test_3501(self):
        "3501 - inserting single rows with JSON and DML returning"
        json_val = self.json_data[11]
        self.cursor.execute("delete from TestJson")
        json_out = self.cursor.var(oracledb.DB_TYPE_JSON)
        self.cursor.setinputsizes(None, oracledb.DB_TYPE_JSON, json_out)
        self.cursor.execute(
            """
            insert into TestJson
            values (:1, :2)
            returning  JsonCol into :json_out
            """,
            [1, json_val],
        )
        self.assertEqual(json_out.getvalue(0), [json_val])

    def test_3502(self):
        "3502 - insert and fetch multiple rows with JSON"
        self.cursor.execute("delete from TestJson")
        self.cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
        data = list(enumerate(self.json_data))
        self.cursor.executemany("insert into TestJson values(:1, :2)", data)
        self.cursor.execute("select * from TestJson")
        self.assertEqual(self.cursor.fetchall(), data)

    def test_3503(self):
        "3503 - inserting multiple rows with JSON and DML returning"
        self.cursor.execute("delete from TestJson")
        int_values = [i for i in range(len(self.json_data))]
        out_int_var = self.cursor.var(int, arraysize=len(int_values))
        out_json_var = self.cursor.var(
            oracledb.DB_TYPE_JSON, arraysize=len(int_values)
        )
        self.cursor.setinputsizes(
            None, oracledb.DB_TYPE_JSON, out_int_var, out_json_var
        )
        data = list(zip(int_values, self.json_data))
        self.cursor.executemany(
            """
            insert into TestJson
            values(:int_val, :json_val)
            returning IntCol, JsonCol into :int_var, :json_var
            """,
            data,
        )
        self.assertEqual(out_int_var.values, [[v] for v in int_values])
        self.assertEqual(out_json_var.values, [[v] for v in self.json_data])

    def test_3504(self):
        "3504 - test binding boolean values as scalar JSON values"
        data = [True, False, True, True, False, True]
        self.__bind_scalar_as_json(data)

    def test_3505(self):
        "3505 - test binding strings/bytes values as scalar JSON values"
        data = [
            "String 1",
            b"A raw value",
            "A much longer string",
            b"A much longer RAW value",
            "Short string",
            b"Y",
        ]
        self.__bind_scalar_as_json(data)

    def test_3506(self):
        "3506 - test binding dates/intervals as scalar JSON values"
        data = [
            datetime.datetime.today(),
            datetime.datetime(2004, 2, 1, 3, 4, 5),
            datetime.datetime(2020, 12, 2, 13, 29, 14),
            datetime.timedelta(8.5),
            datetime.datetime(2002, 12, 13, 9, 36, 0),
            oracledb.Timestamp(2002, 12, 13, 9, 36, 0),
            datetime.datetime(2002, 12, 13),
        ]
        self.__bind_scalar_as_json(data)

    def test_3507(self):
        "3507 - test binding number in json values"
        data = [
            0,
            1,
            25.25,
            6088343244,
            -9999999999999999999,
            decimal.Decimal("0.25"),
            decimal.Decimal("10.25"),
            decimal.Decimal("319438950232418390.273596"),
        ]
        self.__bind_scalar_as_json(data)

    def test_3508(self):
        "3508 - test binding unsupported python type with JSON"
        self.cursor.execute("delete from TestJson")
        self.cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
        insert_sql = "insert into TestJson values (:1, :2)"
        with self.assertRaisesFullCode("DPY-3003"):
            self.cursor.execute(insert_sql, [1, list])

    def test_3509(self):
        "3509 - test fetching an unsupported python type with JSON"
        self.cursor.prefetchrows = 0
        self.cursor.execute(
            "select json(json_scalar(to_yminterval('8-04'))) from dual"
        )
        with self.assertRaisesFullCode("DPY-3007"):
            self.cursor.fetchone()

    def test_3510(self):
        "3510 - fetch all supported types"
        sql = """
            select json('{
                "binary_float": {"$numberFloat": 38.75},
                "binary_double": {"$numberDouble": 125.875},
                "date_no_time": {"$oracleDate": "2022-12-05"},
                "date_with_time": {"$oracleDate": "2022-12-05T15:06:05"},
                "empty_string": "",
                "explicit_long": {"$numberLong": 9223372036854775807},
                "false": false,
                "interval_ds": {"$intervalDaySecond" : "P133DT2H5M8.123S"},
                "long_integer": 12345678901234567890123456789012345,
                "null": null,
                "short_decimal": {"$numberDecimal": 18.25},
                "short_integer": {"$numberInt": 5 },
                "short_raw": {"$rawhex": "73686f72745f726177"},
                "short_string": "A short string",
                "small_integer": 1234,
                "small_float": 25.25,
                "string_uint8": "A longer string but still < 256 bytes",
                "true": true,
                "ts_no_fs": {"$oracleTimestamp": "2022-12-06T18:12:35"},
                "ts_tz": {"$oracleTimestampTZ": "2022-12-07T22:59:15.1234Z"},
                "ts_with_fs": {"$oracleTimestamp": "2022-12-06T18:12:35.123"}
            }'
            extended) from dual"""
        expected_data = dict(
            binary_float=38.75,
            binary_double=125.875,
            date_no_time=datetime.datetime(2022, 12, 5),
            date_with_time=datetime.datetime(2022, 12, 5, 15, 6, 5),
            empty_string="",
            explicit_long=9223372036854775807,
            false=False,
            interval_ds=datetime.timedelta(
                days=133, seconds=7508, microseconds=123000
            ),
            null=None,
            long_integer=12345678901234567890123456789012345,
            short_decimal=18.25,
            short_integer=5,
            short_raw=b"short_raw",
            short_string="A short string",
            small_integer=1234,
            small_float=25.25,
            string_uint8="A longer string but still < 256 bytes",
            true=True,
            ts_no_fs=datetime.datetime(2022, 12, 6, 18, 12, 35),
            ts_tz=datetime.datetime(2022, 12, 7, 22, 59, 15, 123400),
            ts_with_fs=datetime.datetime(2022, 12, 6, 18, 12, 35, 123000),
        )
        self.cursor.execute(sql)
        (actual_data,) = self.cursor.fetchone()
        self.assertEqual(actual_data, expected_data)

    def test_3511(self):
        "3511 - test inserting and updating JSON"
        self.cursor.execute("delete from TestJSON")
        self.cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
        self.cursor.executemany(
            "insert into TestJSON values (:1, :2)",
            list(enumerate(self.json_data)),
        )
        data = [({"a": i}, i) for i in range(len(self.json_data))]
        self.cursor.setinputsizes(oracledb.DB_TYPE_JSON)
        self.cursor.executemany(
            "update TestJSON set JsonCol = :1 where IntCol = :2",
            data,
        )
        self.cursor.execute(
            "select JsonCol, IntCol from TestJSON order by IntCol"
        )
        self.assertEqual(self.cursor.fetchall(), data)

    def test_3512(self):
        "3512 - test fetching json with json_query"
        self.cursor.execute("delete from TestJson")
        self.cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
        self.cursor.executemany(
            "insert into TestJSON values (:1, :2)",
            list(enumerate(self.json_data)),
        )
        cases = [(1, "$.employees.employee1.name"), (2, "$.employees")]
        for num_rows, json_query in cases:
            self.cursor.execute(
                f"""
                select json_query(JsonCol, '{json_query}')
                from TestJson
                order by IntCol
                """
            )
            result = [r for r, in self.cursor if r is not None]
            self.assertEqual(len(result), num_rows)

    def test_3513(self):
        "3513 - test fetching json with json_exists"
        self.cursor.execute("delete from TestJson")
        self.cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
        self.cursor.executemany(
            "insert into TestJSON values (:1, :2)",
            list(enumerate(self.json_data)),
        )
        cases = [(1, "$.Permanent"), (2, "$.employees")]
        for num_rows, json_query in cases:
            self.cursor.execute(
                f"""
                select count(*)
                from TestJson
                where json_exists(JsonCol, '{json_query}')
                """
            )
            (count,) = self.cursor.fetchone()
            self.assertEqual(count, num_rows)

    def test_3514(self):
        "3514 - test selecting json data"
        self.cursor.execute("delete from TestJson")
        self.cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
        self.cursor.executemany(
            "insert into TestJSON values (:1, :2)",
            list(enumerate(self.json_data)),
        )
        self.cursor.execute(
            """
            select t.JsonCol.employees
            from TestJson t
            where t.JsonCol.employees is not null
            order by t.IntCol
            """
        )
        expected_data = [
            self.json_data[-2]["employees"],
            self.json_data[-1]["employees"],
        ]
        data = [r for r, in self.cursor]
        self.assertEqual(data, expected_data)

    def test_3515(self):
        "3515 - test fetching json with json_serialize"
        self.cursor.execute("delete from TestJson")
        data = [{"a": 12.5}, {"b": True}, {"c": None}]
        expected_data = ['{"a":12.5}', '{"b":true}', '{"c":null}']
        self.cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
        self.cursor.executemany(
            "insert into TestJSON values (:1, :2)", list(enumerate(data))
        )
        self.cursor.execute(
            """
            select json_serialize(JsonCol)
            from TestJson
            order by IntCol
            """
        )
        fetched_data = [r for r, in self.cursor]
        self.assertEqual(fetched_data, expected_data)


if __name__ == "__main__":
    test_env.run_test_cases()
