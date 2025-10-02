# -----------------------------------------------------------------------------
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
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
3700 - Module for testing all variable types.
"""

import datetime
import decimal

import oracledb
import pytest


def _test_positive_set_and_get(
    cursor, test_env, var_type, value_to_set, expected_value, type_name=None
):
    var = cursor.var(var_type, typename=type_name)
    var.setvalue(0, value_to_set)
    result = var.getvalue()
    if isinstance(result, oracledb.LOB):
        result = result.read()
    elif isinstance(result, oracledb.DbObject):
        result = test_env.get_db_object_as_plain_object(result)
    if isinstance(expected_value, datetime.date) and not isinstance(
        expected_value, datetime.datetime
    ):
        if isinstance(result, datetime.datetime):
            result = result.date()
    assert type(result) == type(expected_value)
    assert result == expected_value


def _test_negative_set_and_get(cursor, var_type, value_to_set, type_name=None):
    var = cursor.var(var_type, typename=type_name)
    pytest.raises(
        (TypeError, oracledb.DatabaseError), var.setvalue, 0, value_to_set
    )


def test_3700(cursor, test_env):
    "3700 - setting values on variables of type DB_TYPE_NUMBER"
    _test_positive_set_and_get(cursor, test_env, int, 5, 5)
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_NUMBER, 3.5, 3.5
    )
    _test_positive_set_and_get(
        cursor,
        test_env,
        decimal.Decimal,
        decimal.Decimal("24.8"),
        decimal.Decimal("24.8"),
    )
    _test_positive_set_and_get(cursor, test_env, int, True, 1)
    _test_positive_set_and_get(cursor, test_env, int, False, 0)
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_NUMBER, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_NUMBER, "abc")


def test_3701(cursor, test_env):
    "3701 - setting values on variables of type DB_TYPE_BINARY_INTEGER"
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BINARY_INTEGER, 5, 5
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BINARY_INTEGER, 3.5, 3
    )
    _test_positive_set_and_get(
        cursor,
        test_env,
        oracledb.DB_TYPE_BINARY_INTEGER,
        decimal.Decimal("24.8"),
        24,
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BINARY_INTEGER, True, 1
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BINARY_INTEGER, False, 0
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BINARY_INTEGER, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_BINARY_INTEGER, "abc")


def test_3702(cursor, test_env):
    "3702 - setting values on variables of type DB_TYPE_VARCHAR"
    value = "A VARCHAR string"
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_VARCHAR, value, value
    )
    value = b"A raw string for VARCHAR"
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_VARCHAR, value, value.decode()
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_VARCHAR, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_VARCHAR, 5)


def test_3703(cursor, test_env):
    "3703 - setting values on variables of type DB_TYPE_NVARCHAR"
    value = "A NVARCHAR string"
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_NVARCHAR, value, value
    )
    value = b"A raw string for NVARCHAR"
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_NVARCHAR, value, value.decode()
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_NVARCHAR, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_NVARCHAR, 5)


def test_3704(cursor, test_env):
    "3704 - setting values on variables of type DB_TYPE_CHAR"
    value = "A CHAR string"
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_CHAR, value, value
    )
    value = b"A raw string for CHAR"
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_CHAR, value, value.decode()
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_CHAR, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_CHAR, 5)


def test_3705(cursor, test_env):
    "3705 - setting values on variables of type DB_TYPE_NCHAR"
    value = "A NCHAR string"
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_NCHAR, value, value
    )
    value = b"A raw string for NCHAR"
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_CHAR, value, value.decode()
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_NCHAR, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_NCHAR, 5)


def test_3706(cursor, test_env):
    "3706 - setting values on variables of type DB_TYPE_LONG"
    value = "Long Data" * 15000
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_LONG, value, value
    )
    value = b"Raw data for LONG" * 15000
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_LONG, value, value.decode()
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_LONG, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_LONG, 5)


def test_3707(cursor, test_env):
    "3707 - setting values on variables of type DB_TYPE_RAW"
    value = b"Raw Data"
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_RAW, value, value
    )
    value = "String data for RAW"
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_RAW, value, value.encode()
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_RAW, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_RAW, 5)


def test_3708(cursor, test_env):
    "3708 - setting values on variables of type DB_TYPE_LONG_RAW"
    value = b"Long Raw Data" * 15000
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_LONG_RAW, value, value
    )
    value = "String data for LONG RAW" * 15000
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_LONG_RAW, value, value.encode()
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_LONG_RAW, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_LONG_RAW, 5)


def test_3709(cursor, test_env):
    "3709 - setting values on variables of type DB_TYPE_DATE"
    value = datetime.date(2017, 5, 6)
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_DATE, value, value
    )
    value = datetime.datetime(2017, 5, 6, 9, 36, 0)
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_DATE, value, value
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_DATE, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_DATE, 5)


def test_3710(cursor, test_env):
    "3710 - setting values on variables of type DB_TYPE_TIMESTAMP"
    value = datetime.date(2017, 5, 6)
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_TIMESTAMP, value, value
    )
    value = datetime.datetime(2017, 5, 6, 9, 36, 0, 300000)
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_TIMESTAMP, value, value
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_TIMESTAMP, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_TIMESTAMP, 5)


def test_3711(cursor, test_env):
    "3711 - setting values on variables of type DB_TYPE_TIMESTAMP_TZ"
    value = datetime.date(2017, 5, 6)
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_TIMESTAMP_TZ, value, value
    )
    value = datetime.datetime(2017, 5, 6, 9, 36, 0, 300000)
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_TIMESTAMP_TZ, value, value
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_TIMESTAMP_TZ, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_TIMESTAMP_TZ, 5)


def test_3712(cursor, test_env):
    "3712 - setting values on variables of type DB_TYPE_TIMESTAMP_LTZ"
    value = datetime.date(2017, 5, 6)
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_TIMESTAMP_LTZ, value, value
    )
    value = datetime.datetime(2017, 5, 6, 9, 36, 0, 300000)
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_TIMESTAMP_LTZ, value, value
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_TIMESTAMP_LTZ, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_TIMESTAMP_LTZ, 5)


def test_3713(conn, cursor, test_env):
    "3713 - setting values on variables of type DB_TYPE_BLOB"
    value = b"Short temp BLOB value"
    temp_blob = conn.createlob(oracledb.DB_TYPE_BLOB)
    temp_blob.write(value)
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BLOB, temp_blob, value
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_CLOB, temp_blob)
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_NCLOB, temp_blob)
    value = b"Short BLOB value"
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BLOB, value, value
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BLOB, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_BLOB, 5)


def test_3714(conn, cursor, test_env):
    "3714 - setting values on variables of type DB_TYPE_CLOB"
    value = "Short temp CLOB value"
    temp_clob = conn.createlob(oracledb.DB_TYPE_CLOB)
    temp_clob.write(value)
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_CLOB, temp_clob, value
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_BLOB, temp_clob)
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_NCLOB, temp_clob)
    value = "Short CLOB value"
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_CLOB, value, value
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_CLOB, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_CLOB, 5)


def test_3715(conn, cursor, test_env):
    "3715 - setting values on variables of type DB_TYPE_NCLOB"
    value = "Short temp NCLOB value"
    temp_nclob = conn.createlob(oracledb.DB_TYPE_NCLOB)
    temp_nclob.write(value)
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_NCLOB, temp_nclob, value
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_BLOB, temp_nclob)
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_CLOB, temp_nclob)
    value = "Short NCLOB Value"
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_NCLOB, value, value
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_NCLOB, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_NCLOB, 5)


def test_3716(cursor, test_env):
    "3716 - setting values on variables of type DB_TYPE_BINARY_FLOAT"
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BINARY_FLOAT, 5, 5.0
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BINARY_FLOAT, 3.5, 3.5
    )
    _test_positive_set_and_get(
        cursor,
        test_env,
        oracledb.DB_TYPE_BINARY_FLOAT,
        decimal.Decimal("24.5"),
        24.5,
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BINARY_FLOAT, True, 1.0
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BINARY_FLOAT, False, 0.0
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BINARY_FLOAT, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_BINARY_FLOAT, "abc")


def test_3717(cursor, test_env):
    "3717 - setting values on variables of type DB_TYPE_BINARY_DOUBLE"
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BINARY_DOUBLE, 5, 5.0
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BINARY_DOUBLE, 3.5, 3.5
    )
    _test_positive_set_and_get(
        cursor,
        test_env,
        oracledb.DB_TYPE_BINARY_DOUBLE,
        decimal.Decimal("192.125"),
        192.125,
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BINARY_DOUBLE, True, 1.0
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BINARY_DOUBLE, False, 0.0
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BINARY_DOUBLE, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_BINARY_DOUBLE, "abc")


def test_3718(cursor, test_env):
    "3718 - setting values on variables of type DB_TYPE_BOOLEAN"
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BOOLEAN, 5, True
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BOOLEAN, 2.0, True
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BOOLEAN, "abc", True
    )
    _test_positive_set_and_get(
        cursor,
        test_env,
        oracledb.DB_TYPE_BOOLEAN,
        decimal.Decimal("24.8"),
        True,
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BOOLEAN, 0.0, False
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BOOLEAN, 0, False
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_BOOLEAN, None, None
    )


def test_3719(cursor, test_env):
    "3719 - setting values on variables of type DB_TYPE_INTERVAL_DS"
    value = datetime.timedelta(days=5, seconds=56000, microseconds=123780)
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_INTERVAL_DS, value, value
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_INTERVAL_DS, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_INTERVAL_DS, 5)


def test_3720(cursor, test_env):
    "3720 - setting values on variables of type DB_TYPE_ROWID"
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_ROWID, 12345)
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_ROWID, "523lkhlf")


def test_3721(conn, cursor, test_env):
    "3721 - setting values on variables of type DB_TYPE_OBJECT"
    obj_type = conn.gettype("UDT_OBJECT")
    obj = obj_type.newobject()
    plain_obj = test_env.get_db_object_as_plain_object(obj)
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_OBJECT, obj, plain_obj, "UDT_OBJECT"
    )
    _test_positive_set_and_get(cursor, test_env, obj_type, obj, plain_obj)
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_OBJECT, None, None, "UDT_OBJECT"
    )
    _test_positive_set_and_get(cursor, test_env, obj_type, None, None)
    _test_negative_set_and_get(
        cursor, oracledb.DB_TYPE_OBJECT, "abc", "UDT_OBJECT"
    )
    _test_negative_set_and_get(
        cursor, oracledb.DB_TYPE_OBJECT, obj, "UDT_OBJECTARRAY"
    )
    wrong_obj_type = conn.gettype("UDT_OBJECTARRAY")
    _test_negative_set_and_get(cursor, wrong_obj_type, obj)


def test_3722(skip_unless_native_json_supported, cursor, test_env):
    "3722 - setting values on variables of type DB_TYPE_JSON"
    json_data = [
        5,
        25.25,
        decimal.Decimal("10.25"),
        True,
        False,
        datetime.datetime(2017, 5, 6),
        datetime.datetime(2017, 5, 6, 9, 36, 0, 300000),
        datetime.timedelta(days=5, seconds=56000, microseconds=123780),
        {},
        "String",
        b"Some bytes",
        {"keyA": 1, "KeyB": "Melbourne"},
        [],
        [1, "A"],
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
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_JSON, json_data, json_data
    )
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_JSON, None, None
    )


def test_3723(cursor, test_env):
    "3723 - test setting values on variables of type DB_TYPE_CURSOR"
    _test_positive_set_and_get(
        cursor, test_env, oracledb.DB_TYPE_CURSOR, None, None
    )
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_CURSOR, 5)


def test_3724(cursor):
    "3724 - test fetching columns containing all null values"
    cursor.execute(
        """
        select null, to_char(null), to_number(null), to_date(null),
            to_timestamp(null), to_clob(null), to_blob(null)
        from dual
        """
    )
    assert cursor.fetchall() == [(None, None, None, None, None, None, None)]


def test_3725(skip_unless_thin_mode, cursor, test_env):
    "3725 - setting values on variables of type DB_TYPE_UROWID"
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_UROWID, 12345)
    _test_negative_set_and_get(cursor, oracledb.DB_TYPE_UROWID, "523lkhlf")


def test_3726(cursor):
    "3726 - getting value with an specific index"
    var = cursor.var(oracledb.DB_TYPE_NUMBER, 1000, 2)
    var.setvalue(0, 10)
    assert var.getvalue(0) == 10
    assert var.getvalue(1) is None
    pytest.raises(IndexError, var.getvalue, 4)


def test_3727(cursor):
    "3727 - getting buffer_size attribute"
    test_values = [
        (oracledb.DB_TYPE_NUMBER, 200, 22),
        (oracledb.DB_TYPE_VARCHAR, 3000, 12000),
        (oracledb.DB_TYPE_RAW, 4000, 4000),
        (oracledb.DB_TYPE_NCHAR, 1000, 4000),
        (oracledb.DB_TYPE_CHAR, 2000, 8000),
    ]
    for typ, size, buffer_size in test_values:
        var = cursor.var(typ, size)
        assert var.buffer_size == buffer_size


def test_3728(cursor):
    "3728 - getting actual elements"
    array_size = 8
    var = cursor.var(oracledb.DB_TYPE_NUMBER, arraysize=array_size)
    assert var.actual_elements == array_size
    assert var.actual_elements == var.num_elements


def test_3729(cursor):
    "3729 - test deprecated attributes"
    var = cursor.var(oracledb.DB_TYPE_NUMBER, arraysize=200)
    assert var.bufferSize == 22
    assert var.actualElements == 200
    assert var.numElements == 200


def test_3730(cursor):
    "3730 - test calling of outconverter with null values"

    def type_handler(cursor, metadata):
        return cursor.var(
            metadata.type_code,
            outconverter=lambda v: f"|{v}|" if v else "",
            convert_nulls=True,
            arraysize=cursor.arraysize,
        )

    cursor.outputtypehandler = type_handler
    cursor.execute(
        """
        select 'First - A', 'First - B'
        from dual
            union all
        select 'Second - A', null
        from dual
            union all
        select null, 'Third - B'
        from dual
        """
    )
    rows = cursor.fetchall()
    expected_rows = [
        ("|First - A|", "|First - B|"),
        ("|Second - A|", ""),
        ("", "|Third - B|"),
    ]
    assert rows == expected_rows


def test_3731(cursor):
    "3731 - test getting convert_nulls"
    for convert_nulls in [True, False]:
        simple_var = cursor.var(str, convert_nulls=convert_nulls)
        assert simple_var.convert_nulls == convert_nulls


def test_3732(conn, cursor, test_env):
    "3732 - test encoding_errors"
    if test_env.charset != "AL32UTF8":
        pytest.skip("Database character set must be AL32UTF8")
    str_value = "Я"
    replacement_char = "�"
    invalid_bytes = str_value.encode("windows-1251")
    cursor.execute("truncate table TestTempTable")
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (1, utl_raw.cast_to_varchar2(:1))
        """,
        [invalid_bytes],
    )
    conn.commit()

    for arg_name in ["encoding_errors", "encodingErrors"]:

        def type_handler(cursor, fetch_info):
            args = dict(arraysize=cursor.arraysize)
            args[arg_name] = "replace"
            return cursor.var(fetch_info.type_code, **args)

        with conn.cursor() as cursor:
            cursor.outputtypehandler = type_handler
            cursor.execute("select StringCol1 from TestTempTable")
            (fetched_value,) = cursor.fetchone()
            assert fetched_value == replacement_char
