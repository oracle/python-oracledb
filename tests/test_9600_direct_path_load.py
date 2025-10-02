# -----------------------------------------------------------------------------
# Copyright (c) 2025, Oracle and/or its affiliates.
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
Module for testing the Direct Path Load interface.
"""

import datetime
import decimal

import pandas
import pyarrow
import pytest

TABLE_NAME = "TestDataFrame"


@pytest.fixture(autouse=True)
def module_checks(skip_unless_thin_mode):
    pass


@pytest.fixture
def empty_tab(cursor):
    cursor.execute(f"delete from {TABLE_NAME}")
    cursor.connection.commit()


def _verify_data(conn, data, column_names):
    """
    Verifies that the data matches what is stored in the table.
    """
    select_items = ",".join(column_names)
    sql = f"select {select_items} from {TABLE_NAME} order by Id"
    with conn.cursor() as cursor:
        cursor.execute(sql)
        assert cursor.fetchall() == data


def _verify_data_frame(conn, df, column_names, test_env):
    """
    Verifies that the contents of the data frame matches what is stored in the
    table.
    """
    data = test_env.get_data_from_df(df)
    _verify_data(conn, data, column_names)


def test_9600(empty_tab, conn, test_env):
    "9600 - test basic direct path load with list of tuples"
    data = [
        (
            1,
            "Alice",
            "Smith",
            "New York",
            "USA",
            datetime.datetime(1990, 1, 15),
            50000.50,
            750,
        ),
        (
            2,
            "Bob",
            "Johnson",
            "London",
            "UK",
            datetime.datetime(1985, 6, 20),
            60000.75,
            680,
        ),
        (
            3,
            "Charlie",
            "Brown",
            "Paris",
            "France",
            datetime.datetime(1992, 3, 10),
            70000.25,
            720,
        ),
    ]
    column_names = [
        "Id",
        "FirstName",
        "LastName",
        "City",
        "Country",
        "DateOfBirth",
        "Salary",
        "CreditScore",
    ]
    conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=data,
    )
    _verify_data(conn, data, column_names)


def test_9601(empty_tab, conn, test_env):
    "9601 - test basic direct path load with dataframe"
    data = {
        "Id": [1, 2, 3, 4, 5],
        "FirstName": ["Alice", "Bob", "Charlie", "David", "Eve"],
        "LastName": ["Smith", "Johnson", "Brown", "Wilson", "Davis"],
        "City": ["New York", "London", "Paris", "Tokyo", "Sydney"],
        "Country": ["USA", "UK", "France", "Japan", "Australia"],
        "DateOfBirth": [
            datetime.datetime(1990, 1, 15),
            datetime.datetime(1985, 6, 20),
            datetime.datetime(1992, 3, 10),
            datetime.datetime(1988, 12, 1),
            datetime.datetime(1995, 5, 5),
        ],
        "Salary": [50000.50, 60000.75, 70000.25, 80000.00, 90000.50],
        "CreditScore": [750, 680, 720, 810, 690],
    }
    df = pandas.DataFrame(data)
    column_names = list(df.columns.tolist())
    conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=df,
    )
    _verify_data_frame(conn, df, column_names, test_env)


def test_9602(empty_tab, conn, test_env):
    "960f - test with empty data"
    data = []
    column_names = ["Id", "FirstName"]
    conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=data,
    )
    _verify_data(conn, data, column_names)


def test_9603(empty_tab, conn, test_env):
    "9603 - test with empty data frame"
    data = {
        "Id": [],
        "FirstName": [],
    }
    df = pandas.DataFrame(data)
    column_names = list(df.columns.tolist())
    conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=df,
    )
    _verify_data_frame(conn, df, column_names, test_env)


@pytest.mark.parametrize("batch_size", [1, 5, 99, 199, 200])
def test_9604(batch_size, conn, empty_tab, round_trip_checker, test_env):
    "9604 - test with various batch sizes"
    data = [(i + 1, f"String for row {i + 1}") for i in range(200)]
    column_names = ["Id", "FirstName"]
    conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=data,
        batch_size=batch_size,
    )
    num_round_trips = 2 + len(data) // batch_size
    if len(data) % batch_size:
        num_round_trips += 1
    assert round_trip_checker.get_value() == num_round_trips
    _verify_data(conn, data, column_names)


@pytest.mark.parametrize("batch_size", [1, 5, 99, 199, 200])
def test_9605(batch_size, conn, empty_tab, round_trip_checker, test_env):
    "9605 - test with various batch sizes with a data frame"
    names = ["Id", "FirstName"]
    rows = [(i + 1, f"Name {i + 1}") for i in range(200)]
    arrays = [
        pyarrow.array([i for i, _ in rows], pyarrow.int16()),
        pyarrow.array([s for _, s in rows], pyarrow.string()),
    ]
    df = pyarrow.table(arrays, names).to_pandas()
    conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=names,
        data=df,
        batch_size=batch_size,
    )
    num_round_trips = 2 + len(rows) // batch_size
    if len(rows) % batch_size:
        num_round_trips += 1
    assert round_trip_checker.get_value() == num_round_trips
    _verify_data_frame(conn, df, names, test_env)


def test_9606(empty_tab, disable_fetch_lobs, conn, test_env):
    "9607 - test with all basic data types"
    column_names = [
        "Id",
        "FirstName",
        "DateOfBirth",
        "LastUpdated",
        "Salary",
        "CreditScore",
        "IntegerData",
        "LongIntegerData",
        "FloatData",
        "DoubleData",
        "RawData",
        "LongData",
        "LongRawData",
    ]
    current_time = datetime.datetime.now()
    rows = [
        (
            1,
            "Test1",
            datetime.datetime(1990, 1, 1),
            current_time,
            12345.50,
            700,
            123456789,
            123456789012345,
            1.625,
            9.87654321,
            b"\x01\x02\x03\x04\x05",
            "This is a long text description",
            b"blob_data_1",
        ),
        (
            2,
            "Test2",
            datetime.datetime(1991, 2, 2),
            current_time,
            23456.75,
            750,
            987654321,
            987654321098765,
            5.5,
            1.23456789,
            b"\xff\xfe\xfd\xfc\xfb",
            "Another long description here",
            b"blob_data_2",
        ),
    ]
    conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=rows,
    )
    _verify_data(conn, rows, column_names)


def test_9607(empty_tab, disable_fetch_lobs, conn, test_env):
    "9607 - test with all basic data types with a data frame"
    current_time = datetime.datetime.now()
    column_names = [
        "Id",
        "FirstName",
        "DateOfBirth",
        "LastUpdated",
        "Salary",
        "CreditScore",
        "IntegerData",
        "LongIntegerData",
        "FloatData",
        "DoubleData",
        "RawData",
        "LongData",
        "LongRawData",
    ]
    arrays = [
        pyarrow.array([1, 2], pyarrow.int8()),
        pyarrow.array(["Test1", "Test2"], pyarrow.string()),
        pyarrow.array(
            [datetime.datetime(1990, 1, 1), datetime.datetime(1991, 2, 2)],
            pyarrow.timestamp("s"),
        ),
        pyarrow.array(
            [current_time, current_time],
            pyarrow.timestamp("us"),
        ),
        pyarrow.array([12345.50, 23456.75], pyarrow.float32()),
        pyarrow.array([700, 750], pyarrow.int16()),
        pyarrow.array([123456789, 987654321], pyarrow.uint32()),
        pyarrow.array([123456789012345, 987654321098765], pyarrow.uint64()),
        pyarrow.array([1.625, 5.675], pyarrow.float32()),
        pyarrow.array([9.87654321, 1.23456789], pyarrow.float64()),
        pyarrow.array(
            [b"\x01\x02\x03\x04\x05", b"\xff\xfe\xfd\xfc\xfb"],
            pyarrow.binary(),
        ),
        pyarrow.array(
            [
                "This is a long text description",
                "Another long description here",
            ],
            pyarrow.string(),
        ),
        pyarrow.array([b"blob_data_1", b"blob_data_2"], pyarrow.binary()),
    ]
    df = pyarrow.table(arrays, column_names).to_pandas()
    conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=df,
    )
    _verify_data_frame(conn, df, column_names, test_env)


def test_9608(empty_tab, conn, test_env):
    "9608 - test with null values"
    column_names = [
        "Id",
        "FirstName",
        "LastName",
        "City",
        "Country",
        "DateOfBirth",
        "Salary",
        "CreditScore",
    ]
    rows = [
        (
            1,
            "Alice",
            "Smith",
            "New York",
            None,
            datetime.datetime(1990, 1, 15),
            50_000.50,
            750,
        ),
        (2, None, "Johnson", None, "UK", None, None, 680),
        (3, "Charlie", None, "Paris", "France", None, 70_000.25, None),
        (
            4,
            None,
            None,
            "Tokyo",
            None,
            datetime.datetime(1995, 5, 5),
            80_000.00,
            690,
        ),
    ]
    conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=rows,
    )
    _verify_data(conn, rows, column_names)


def test_9609(empty_tab, conn, test_env):
    "9609 - test with null values using a data frame"
    data = {
        "Id": [1, 2, 3, 4],
        "FirstName": ["Alice", None, "Charlie", None],
        "LastName": ["Smith", "Johnson", None, None],
        "City": ["New York", None, "Paris", "Tokyo"],
        "Country": [None, "UK", "France", None],
        "DateOfBirth": [
            datetime.datetime(1990, 1, 15),
            None,
            None,
            datetime.datetime(1995, 5, 5),
        ],
        "Salary": [50000.50, None, 70000.25, 80000.00],
        "CreditScore": [750, 680, None, 690],
    }
    df = pandas.DataFrame(data)
    column_names = list(df.columns.tolist())
    conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=df,
    )
    _verify_data_frame(conn, df, column_names, test_env)


def test_9610(empty_tab, conn, test_env):
    "9610 - test with the wrong number of columns"
    column_names = ["Id", "FirstName", "LastName"]
    rows = [(1, "Alice"), (2, "Joe")]
    with test_env.assert_raises_full_code("DPY-4009"):
        conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name=TABLE_NAME,
            column_names=column_names,
            data=rows,
        )


def test_9611(empty_tab, conn, test_env):
    "9611 - test with the wrong number of columns using a data frame"
    column_names = ["Id", "FirstName"]
    data = {
        "Id": [1, 2],
        "FirstName": ["Alice", "Joe"],
        "LastName": ["Smith", "Johnson"],
    }
    df = pandas.DataFrame(data)
    with test_env.assert_raises_full_code("DPY-4009"):
        conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name=TABLE_NAME,
            column_names=column_names,
            data=df,
        )


def test_9612(empty_tab, conn, test_env):
    "9612 - test with decimal data"
    column_names = ["Id", "FirstName", "DecimalData"]
    rows = [
        (decimal.Decimal("1"), "Sally", decimal.Decimal("1234567.8910")),
        (decimal.Decimal("2"), "Jill", decimal.Decimal("9876543.2109")),
        (decimal.Decimal("3"), "John", decimal.Decimal("5555555.5555")),
    ]
    conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=rows,
    )
    with test_env.defaults_context_manager("fetch_decimals", True):
        _verify_data(conn, rows, column_names)


def test_9613(empty_tab, conn, test_env):
    "9613 - test with decimal data using a data frame"
    data = {
        "Id": [
            decimal.Decimal("1"),
            decimal.Decimal("2"),
            decimal.Decimal("3"),
        ],
        "FirstName": ["Sally", "Jill", "John"],
        "DecimalData": [
            decimal.Decimal("1234567.8910"),
            decimal.Decimal("9876543.2109"),
            decimal.Decimal("5555555.5555"),
        ],
    }
    df = pandas.DataFrame(data)
    column_names = list(df.columns.tolist())
    conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=df,
    )
    with test_env.defaults_context_manager("fetch_decimals", True):
        _verify_data_frame(conn, df, column_names, test_env)


def test_9614(empty_tab, conn, test_env):
    "9614 - test string data that exceeds the maximum length"
    column_names = ["Id", "FirstName"]
    rows = [(1, "Sally"), (2, "Jill" * 26)]
    with test_env.assert_raises_full_code("DPY-8000"):
        conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name=TABLE_NAME,
            column_names=column_names,
            data=rows,
        )


def test_9615(empty_tab, conn, test_env):
    "9615 - test string data that exceeds the maximum length with a data frame"
    data = {
        "Id": [1, 2, 3],
        "FirstName": ["Sally", "Jill", "John" * 26],
    }
    df = pandas.DataFrame(data)
    column_names = list(df.columns.tolist())
    with test_env.assert_raises_full_code("DPY-8000"):
        conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name=TABLE_NAME,
            column_names=column_names,
            data=df,
        )


def test_9616(conn, test_env):
    "9616 - test data that is null"
    column_names = ["IntCol", "StringCol", "RawCol", "FixedCharCol"]
    rows = [(100, "String 100", b"Raw", "Fixed"), (2, None, b"Raw", "Fixed")]
    with test_env.assert_raises_full_code("DPY-8001"):
        conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name="TestStrings",
            column_names=column_names,
            data=rows,
        )


def test_9617(conn, test_env):
    "9617 - test data that is null in a data frame"
    data = {
        "IntCol": [100, 200, 300],
        "StringCol": ["String 100", None, "String 300"],
        "RawCol": [b"Raw", b"Raw", b"Raw"],
        "FixedCharCol": ["Fixed", "Fixed", "Fixed"],
    }
    df = pandas.DataFrame(data)
    column_names = list(df.columns.tolist())
    with test_env.assert_raises_full_code("DPY-8001"):
        conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name="TestStrings",
            column_names=column_names,
            data=df,
        )


def test_9618(conn, test_env):
    "9618 - test data containing empty string"
    column_names = ["IntCol", "StringCol", "RawCol", "FixedCharCol"]
    rows = [(100, "String 100", b"Raw", "Fixed"), (2, "", b"Raw", "Fixed")]
    with test_env.assert_raises_full_code("DPY-8001"):
        conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name="TestStrings",
            column_names=column_names,
            data=rows,
        )


def test_9619(conn, test_env):
    "9619 - test data containing empty string in a data frame"
    data = {
        "IntCol": [100, 200, 300],
        "StringCol": ["String 100", "", "String 300"],
        "RawCol": [b"Raw", b"Raw", b"Raw"],
        "FixedCharCol": ["Fixed", "Fixed", "Fixed"],
    }
    df = pandas.DataFrame(data)
    column_names = list(df.columns.tolist())
    with test_env.assert_raises_full_code("DPY-8001"):
        conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name="TestStrings",
            column_names=column_names,
            data=df,
        )


def test_9620(empty_tab, conn, test_env):
    "9620 - test data is committed on success"
    column_names = ["Id", "FirstName"]
    rows = [(1, "Sally"), (2, "Jill")]
    with test_env.get_connection() as other_conn:
        other_conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name=TABLE_NAME,
            column_names=column_names,
            data=rows,
        )
    _verify_data(conn, rows, column_names)


def test_9621(empty_tab, conn, test_env):
    "9621 - test data is committed on success using a data frame"
    data = {
        "Id": [1, 2, 3],
        "FirstName": ["Sally", "Jill", "John"],
    }
    df = pandas.DataFrame(data)
    column_names = list(df.columns.tolist())
    with test_env.get_connection() as other_conn:
        other_conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name=TABLE_NAME,
            column_names=column_names,
            data=df,
        )
    _verify_data_frame(conn, df, column_names, test_env)
