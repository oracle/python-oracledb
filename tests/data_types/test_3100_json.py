# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2026, Oracle and/or its affiliates.
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
Module for testing the JSON data type.
"""

import datetime
import decimal

import oracledb
import pytest


@pytest.fixture(autouse=True)
def skip_tests(skip_unless_native_json_supported):
    """
    Skip all tests in the file unless native JSON is supported.
    """


@pytest.fixture(scope="module")
def json_data():
    """
    Returns the data used for the tests in this module.
    """
    return [
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


def _bind_scalar_as_json(cursor, data):
    cursor.execute("delete from TestJson")
    out_var = cursor.var(oracledb.DB_TYPE_JSON, arraysize=len(data))
    cursor.setinputsizes(None, oracledb.DB_TYPE_JSON, out_var)
    bind_data = list(enumerate(data))
    cursor.executemany(
        """
        insert into TestJson values (:1, :2)
        returning JsonCol into :json_out
        """,
        bind_data,
    )
    cursor.connection.commit()
    assert out_var.values == [[value] for value in data]


def test_data_types_3100(cursor, json_data):
    "3100 - insert and fetch single row with JSON"
    cursor.execute("delete from TestJson")
    cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
    cursor.execute("insert into TestJson values (:1, :2)", [1, json_data])
    cursor.execute("select JsonCol from TestJson")
    (result,) = cursor.fetchone()
    assert result == json_data


def test_data_types_3101(cursor, json_data):
    "3101 - inserting single rows with JSON and DML returning"
    json_val = json_data[11]
    cursor.execute("delete from TestJson")
    json_out = cursor.var(oracledb.DB_TYPE_JSON)
    cursor.setinputsizes(None, oracledb.DB_TYPE_JSON, json_out)
    cursor.execute(
        """
        insert into TestJson
        values (:1, :2)
        returning  JsonCol into :json_out
        """,
        [1, json_val],
    )
    assert json_out.getvalue(0) == [json_val]


def test_data_types_3102(cursor, json_data):
    "3102 - insert and fetch multiple rows with JSON"
    cursor.execute("delete from TestJson")
    cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
    data = list(enumerate(json_data))
    cursor.executemany("insert into TestJson values(:1, :2)", data)
    cursor.execute("select * from TestJson")
    assert cursor.fetchall() == data


def test_data_types_3103(cursor, json_data):
    "3103 - inserting multiple rows with JSON and DML returning"
    cursor.execute("delete from TestJson")
    int_values = [i for i in range(len(json_data))]
    out_int_var = cursor.var(int, arraysize=len(int_values))
    out_json_var = cursor.var(oracledb.DB_TYPE_JSON, arraysize=len(int_values))
    cursor.setinputsizes(
        None, oracledb.DB_TYPE_JSON, out_int_var, out_json_var
    )
    data = list(zip(int_values, json_data))
    cursor.executemany(
        """
        insert into TestJson
        values(:int_val, :json_val)
        returning IntCol, JsonCol into :int_var, :json_var
        """,
        data,
    )
    assert out_int_var.values == [[v] for v in int_values]
    assert out_json_var.values == [[v] for v in json_data]


def test_data_types_3104(cursor):
    "3104 - test binding boolean values as scalar JSON values"
    data = [True, False, True, True, False, True]
    _bind_scalar_as_json(cursor, data)


def test_data_types_3105(cursor):
    "3105 - test binding strings/bytes values as scalar JSON values"
    data = [
        "String 1",
        b"A raw value",
        "A much longer string",
        b"A much longer RAW value",
        "Short string",
        b"Y",
    ]
    _bind_scalar_as_json(cursor, data)


def test_data_types_3106(cursor):
    "3106 - test binding dates/intervals as scalar JSON values"
    data = [
        datetime.datetime.today(),
        datetime.datetime(2004, 2, 1, 3, 4, 5),
        datetime.datetime(2020, 12, 2, 13, 29, 14),
        datetime.timedelta(8.5),
        datetime.datetime(2002, 12, 13, 9, 36, 0),
        oracledb.Timestamp(2002, 12, 13, 9, 36, 0),
        datetime.datetime(2002, 12, 13),
    ]
    _bind_scalar_as_json(cursor, data)


def test_data_types_3107(cursor):
    "3107 - test binding number in json values"
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
    _bind_scalar_as_json(cursor, data)


def test_data_types_3108(cursor, test_env):
    "3108 - test binding unsupported python type with JSON"
    cursor.execute("delete from TestJson")
    cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
    insert_sql = "insert into TestJson values (:1, :2)"
    with test_env.assert_raises_full_code("DPY-3003"):
        cursor.execute(insert_sql, [1, list])


def test_data_types_3109(cursor, test_env):
    "3109 - test fetching an unsupported python type with JSON"
    cursor.prefetchrows = 0
    cursor.execute("select json(json_scalar(to_yminterval('8-04'))) from dual")
    with test_env.assert_raises_full_code("DPY-3007"):
        cursor.fetchone()


def test_data_types_3110(cursor):
    "3110 - fetch all supported types"
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
    cursor.execute(sql)
    (actual_data,) = cursor.fetchone()
    assert actual_data == expected_data


def test_data_types_3111(cursor, json_data):
    "3111 - test inserting and updating JSON"
    cursor.execute("delete from TestJSON")
    cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
    cursor.executemany(
        "insert into TestJSON values (:1, :2)",
        list(enumerate(json_data)),
    )
    data = [({"a": i}, i) for i in range(len(json_data))]
    cursor.setinputsizes(oracledb.DB_TYPE_JSON)
    cursor.executemany(
        "update TestJSON set JsonCol = :1 where IntCol = :2",
        data,
    )
    cursor.execute("select JsonCol, IntCol from TestJSON order by IntCol")
    assert cursor.fetchall() == data


def test_data_types_3112(cursor, json_data):
    "3112 - test fetching json with json_query"
    cursor.execute("delete from TestJson")
    cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
    cursor.executemany(
        "insert into TestJSON values (:1, :2)",
        list(enumerate(json_data)),
    )
    cases = [(1, "$.employees.employee1.name"), (2, "$.employees")]
    for num_rows, json_query in cases:
        cursor.execute(f"""
            select json_query(JsonCol, '{json_query}')
            from TestJson
            order by IntCol
            """)
        result = [r for r, in cursor if r is not None]
        assert len(result) == num_rows


def test_data_types_3113(cursor, json_data):
    "3113 - test fetching json with json_exists"
    cursor.execute("delete from TestJson")
    cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
    cursor.executemany(
        "insert into TestJSON values (:1, :2)",
        list(enumerate(json_data)),
    )
    cases = [(1, "$.Permanent"), (2, "$.employees")]
    for num_rows, json_query in cases:
        cursor.execute(f"""
            select count(*)
            from TestJson
            where json_exists(JsonCol, '{json_query}')
            """)
        (count,) = cursor.fetchone()
        assert count == num_rows


def test_data_types_3114(cursor, json_data):
    "3114 - test selecting json data"
    cursor.execute("delete from TestJson")
    cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
    cursor.executemany(
        "insert into TestJSON values (:1, :2)",
        list(enumerate(json_data)),
    )
    cursor.execute("""
        select t.JsonCol.employees
        from TestJson t
        where t.JsonCol.employees is not null
        order by t.IntCol
        """)
    expected_data = [
        json_data[-2]["employees"],
        json_data[-1]["employees"],
    ]
    data = [r for r, in cursor]
    assert data == expected_data


def test_data_types_3115(cursor):
    "3115 - test fetching json with json_serialize"
    cursor.execute("delete from TestJson")
    data = [{"a": 12.5}, {"b": True}, {"c": None}]
    expected_data = ['{"a":12.5}', '{"b":true}', '{"c":null}']
    cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
    cursor.executemany(
        "insert into TestJSON values (:1, :2)", list(enumerate(data))
    )
    cursor.execute("""
        select json_serialize(JsonCol)
        from TestJson
        order by IntCol
        """)
    fetched_data = [r for r, in cursor]
    assert fetched_data == expected_data


def test_data_types_3116(conn, test_env):
    "3116 - test decoding invalid OSON"
    value_to_encode = dict(key_1="test_3116a", key_2="test_3116b")
    encoded_bytes = conn.encode_oson(value_to_encode)
    modified_bytes = bytearray(encoded_bytes)
    modified_bytes[15] = 0xFF
    with test_env.assert_raises_full_code("DPY-5006"):
        conn.decode_oson(bytes(modified_bytes))
