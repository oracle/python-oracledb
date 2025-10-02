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
Module for testing the Direct Path Load interface with asyncio.
"""

import datetime
import decimal

import pandas
import pyarrow
import pytest

TABLE_NAME = "TestDataFrame"


@pytest.fixture(autouse=True)
async def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


@pytest.fixture
async def empty_tab(async_cursor):
    await async_cursor.execute(f"delete from {TABLE_NAME}")
    await async_cursor.connection.commit()


async def _verify_data(conn, data, column_names):
    """
    Verifies that the data matches what is stored in the table.
    """
    select_items = ",".join(column_names)
    sql = f"select {select_items} from {TABLE_NAME} order by Id"
    with conn.cursor() as cursor:
        await cursor.execute(sql)
        assert await cursor.fetchall() == data


async def _verify_data_frame(conn, df, column_names, test_env):
    """
    Verifies that the contents of the data frame matches what is stored in the
    table.
    """
    data = test_env.get_data_from_df(df)
    await _verify_data(conn, data, column_names)


async def test_9700(empty_tab, async_conn, test_env):
    "9700 - test basic direct path load with list of tuples"
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
    await async_conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=data,
    )
    await _verify_data(async_conn, data, column_names)


async def test_9701(empty_tab, async_conn, test_env):
    "9701 - test basic direct path load with Pandas dataframe"
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
    await async_conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=df,
    )
    await _verify_data_frame(async_conn, df, column_names, test_env)


async def test_9702(empty_tab, async_conn, test_env):
    "9702 - test with empty data"
    data = []
    column_names = ["Id", "FirstName"]
    await async_conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=data,
    )
    await _verify_data(async_conn, data, column_names)


async def test_9703(empty_tab, async_conn, test_env):
    "9703 - test with empty data frame"
    data = {
        "Id": [],
        "FirstName": [],
    }
    df = pandas.DataFrame(data)
    column_names = list(df.columns.tolist())
    await async_conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=df,
    )
    await _verify_data_frame(async_conn, df, column_names, test_env)


@pytest.mark.parametrize("batch_size", [1, 5, 99, 199, 200])
async def test_9704(
    batch_size, async_conn, empty_tab, round_trip_checker_async, test_env
):
    "9704 - test with various batch sizes"
    data = [(i + 1, f"String for row {i + 1}") for i in range(200)]
    column_names = ["Id", "FirstName"]
    await async_conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=data,
        batch_size=batch_size,
    )
    num_round_trips = 2 + len(data) // batch_size
    if len(data) % batch_size:
        num_round_trips += 1
    assert await round_trip_checker_async.get_value_async() == num_round_trips
    await _verify_data(async_conn, data, column_names)


@pytest.mark.parametrize("batch_size", [1, 5, 99, 199, 200])
async def test_9705(
    batch_size, async_conn, empty_tab, round_trip_checker_async, test_env
):
    "9705 - test with various batch sizes with a data frame"
    names = ["Id", "FirstName"]
    rows = [(i + 1, f"Name {i + 1}") for i in range(200)]
    arrays = [
        pyarrow.array([i for i, _ in rows], pyarrow.int16()),
        pyarrow.array([s for _, s in rows], pyarrow.string()),
    ]
    df = pyarrow.table(arrays, names).to_pandas()
    await async_conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=names,
        data=df,
        batch_size=batch_size,
    )
    num_round_trips = 2 + len(rows) // batch_size
    if len(rows) % batch_size:
        num_round_trips += 1
    assert await round_trip_checker_async.get_value_async() == num_round_trips
    await _verify_data_frame(async_conn, df, names, test_env)


async def test_9706(empty_tab, disable_fetch_lobs, async_conn, test_env):
    "9707 - test with all basic data types"
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
    await async_conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=rows,
    )
    await _verify_data(async_conn, rows, column_names)


async def test_9707(empty_tab, disable_fetch_lobs, async_conn, test_env):
    "9707 - test with all basic data types with a data frame"
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
    await async_conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=df,
    )
    await _verify_data_frame(async_conn, df, column_names, test_env)


async def test_9708(empty_tab, async_conn, test_env):
    "9708 - test with null values"
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
    await async_conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=rows,
    )
    await _verify_data(async_conn, rows, column_names)


async def test_9709(empty_tab, async_conn, test_env):
    "9709 - test with null values using a data frame"
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
    await async_conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=df,
    )
    await _verify_data_frame(async_conn, df, column_names, test_env)


async def test_9710(empty_tab, async_conn, test_env):
    "9710 - test with the wrong number of columns"
    column_names = ["Id", "FirstName", "LastName"]
    rows = [(1, "Alice"), (2, "Joe")]
    with test_env.assert_raises_full_code("DPY-4009"):
        await async_conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name=TABLE_NAME,
            column_names=column_names,
            data=rows,
        )


async def test_9711(empty_tab, async_conn, test_env):
    "9711 - test with the wrong number of columns using a data frame"
    column_names = ["Id", "FirstName"]
    data = {
        "Id": [1, 2],
        "FirstName": ["Alice", "Joe"],
        "LastName": ["Smith", "Johnson"],
    }
    df = pandas.DataFrame(data)
    with test_env.assert_raises_full_code("DPY-4009"):
        await async_conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name=TABLE_NAME,
            column_names=column_names,
            data=df,
        )


async def test_9712(empty_tab, async_conn, test_env):
    "9712 - test with decimal data"
    column_names = ["Id", "FirstName", "DecimalData"]
    rows = [
        (decimal.Decimal("1"), "Sally", decimal.Decimal("1234567.8910")),
        (decimal.Decimal("2"), "Jill", decimal.Decimal("9876543.2109")),
        (decimal.Decimal("3"), "John", decimal.Decimal("5555555.5555")),
    ]
    await async_conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=rows,
    )
    with test_env.defaults_context_manager("fetch_decimals", True):
        await _verify_data(async_conn, rows, column_names)


async def test_9713(empty_tab, async_conn, test_env):
    "9713 - test with decimal data using a data frame"
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
    await async_conn.direct_path_load(
        schema_name=test_env.main_user,
        table_name=TABLE_NAME,
        column_names=column_names,
        data=df,
    )
    with test_env.defaults_context_manager("fetch_decimals", True):
        await _verify_data_frame(async_conn, df, column_names, test_env)


async def test_9714(empty_tab, async_conn, test_env):
    "9714 - test string data that exceeds the maximum length"
    column_names = ["Id", "FirstName"]
    rows = [(1, "Sally"), (2, "Jill" * 26)]
    with test_env.assert_raises_full_code("DPY-8000"):
        await async_conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name=TABLE_NAME,
            column_names=column_names,
            data=rows,
        )


async def test_9715(empty_tab, async_conn, test_env):
    "9715 - test string data that exceeds the maximum length with a data frame"
    data = {
        "Id": [1, 2, 3],
        "FirstName": ["Sally", "Jill", "John" * 26],
    }
    df = pandas.DataFrame(data)
    column_names = list(df.columns.tolist())
    with test_env.assert_raises_full_code("DPY-8000"):
        await async_conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name=TABLE_NAME,
            column_names=column_names,
            data=df,
        )


async def test_9716(async_conn, test_env):
    "9716 - test data that is null"
    column_names = ["IntCol", "StringCol", "RawCol", "FixedCharCol"]
    rows = [(100, "String 100", b"Raw", "Fixed"), (2, None, b"Raw", "Fixed")]
    with test_env.assert_raises_full_code("DPY-8001"):
        await async_conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name="TestStrings",
            column_names=column_names,
            data=rows,
        )


async def test_9717(async_conn, test_env):
    "9717 - test data that is null in a data frame"
    data = {
        "IntCol": [100, 200, 300],
        "StringCol": ["String 100", None, "String 300"],
        "RawCol": [b"Raw", b"Raw", b"Raw"],
        "FixedCharCol": ["Fixed", "Fixed", "Fixed"],
    }
    df = pandas.DataFrame(data)
    column_names = list(df.columns.tolist())
    with test_env.assert_raises_full_code("DPY-8001"):
        await async_conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name="TestStrings",
            column_names=column_names,
            data=df,
        )


async def test_9718(async_conn, test_env):
    "9718 - test data containing empty string"
    column_names = ["IntCol", "StringCol", "RawCol", "FixedCharCol"]
    rows = [(100, "String 100", b"Raw", "Fixed"), (2, "", b"Raw", "Fixed")]
    with test_env.assert_raises_full_code("DPY-8001"):
        await async_conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name="TestStrings",
            column_names=column_names,
            data=rows,
        )


async def test_9719(async_conn, test_env):
    "9719 - test data containing empty string in a data frame"
    data = {
        "IntCol": [100, 200, 300],
        "StringCol": ["String 100", "", "String 300"],
        "RawCol": [b"Raw", b"Raw", b"Raw"],
        "FixedCharCol": ["Fixed", "Fixed", "Fixed"],
    }
    df = pandas.DataFrame(data)
    column_names = list(df.columns.tolist())
    with test_env.assert_raises_full_code("DPY-8001"):
        await async_conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name="TestStrings",
            column_names=column_names,
            data=df,
        )


async def test_9720(empty_tab, async_conn, test_env):
    "9720 - test data is committed on success"
    column_names = ["Id", "FirstName"]
    rows = [(1, "Sally"), (2, "Jill")]
    async with test_env.get_connection_async() as other_conn:
        await other_conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name=TABLE_NAME,
            column_names=column_names,
            data=rows,
        )
    await _verify_data(async_conn, rows, column_names)


async def test_9721(empty_tab, async_conn, test_env):
    "9721 - test data is committed on success using a data frame"
    data = {
        "Id": [1, 2, 3],
        "FirstName": ["Sally", "Jill", "John"],
    }
    df = pandas.DataFrame(data)
    column_names = list(df.columns.tolist())
    async with test_env.get_connection_async() as other_conn:
        await other_conn.direct_path_load(
            schema_name=test_env.main_user,
            table_name=TABLE_NAME,
            column_names=column_names,
            data=df,
        )
    await _verify_data_frame(async_conn, df, column_names, test_env)
