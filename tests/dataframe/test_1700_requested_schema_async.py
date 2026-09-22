# -----------------------------------------------------------------------------
# Copyright (c) 2025, 2026, Oracle and/or its affiliates.
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
Module for testing user requested schema in fetch_df APIs using asyncio.
"""

import decimal
import datetime
import itertools

import pyarrow
import pytest


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


@pytest.mark.parametrize(
    "expr,dtype,value",
    [
        (":1", pyarrow.decimal128(precision=3, scale=2), 2.75),
        (":1", pyarrow.decimal256(precision=4, scale=2), 12.25),
    ]
    + list(
        itertools.product(
            [":1"],
            [
                pyarrow.int8(),
                pyarrow.int16(),
                pyarrow.int32(),
                pyarrow.int64(),
                pyarrow.uint8(),
                pyarrow.uint16(),
                pyarrow.uint32(),
                pyarrow.uint64(),
            ],
            [99],
        )
    )
    + list(
        itertools.product(
            [
                "cast(:1 as number)",
                "cast(:1 as binary_float)",
                "cast(:1 as binary_double)",
            ],
            [pyarrow.float32(), pyarrow.float64()],
            [26.25],
        )
    )
    + list(
        itertools.product(
            [":1", "to_blob(:1)"],
            [
                pyarrow.binary(length=6),
                pyarrow.binary(),
                pyarrow.large_binary(),
            ],
            [b"ABCDEF"],
        )
    )
    + list(
        itertools.product(
            [
                "cast(:1 as date)",
                "cast(:1 as timestamp)",
                "cast(:1 as timestamp with local time zone)",
                "cast(:1 as timestamp with time zone)",
            ],
            [pyarrow.date32(), pyarrow.date64()],
            [datetime.date(2026, 9, 22)],
        )
    )
    + list(
        itertools.product(
            [
                "cast(:1 as date)",
                "cast(:1 as timestamp)",
                "cast(:1 as timestamp with local time zone)",
                "cast(:1 as timestamp with time zone)",
            ],
            [
                pyarrow.timestamp("s"),
                pyarrow.timestamp("us"),
                pyarrow.timestamp("ms"),
                pyarrow.timestamp("ns"),
            ],
            [datetime.datetime(2026, 9, 22)],
        )
    )
    + list(
        itertools.product(
            [
                "cast(:1 as char(9))",
                "cast(:1 as nchar(9))",
                "cast(:1 as varchar2(9))",
                "cast(:1 as nvarchar2(9))",
                "to_clob(:1)",
                "to_nclob(:1)",
            ],
            [pyarrow.string(), pyarrow.large_string()],
            ["ABCDEFGHI"],
        )
    ),
)
async def test_dataframe_1700(test_env, async_conn, expr, dtype, value):
    "1700 - duplicate value handling for all types"
    num_rows = 6
    statement = f"""
        select {expr} as value
        from dual
        connect by level <= {num_rows}"""
    requested_schema = pyarrow.schema([("VALUE", dtype)])
    ora_df = await async_conn.fetch_df_all(
        statement,
        [value],
        requested_schema=requested_schema,
    )
    tab = pyarrow.table(ora_df)
    df = tab.to_pandas()
    assert tab.field("VALUE").type == dtype
    assert test_env.get_data_from_df(df) == [(value,)] * num_rows
    batch_size = 3
    async for ora_df in async_conn.fetch_df_batches(
        statement, [value], size=batch_size, requested_schema=requested_schema
    ):
        tab = pyarrow.table(ora_df)
        df = tab.to_pandas()
        assert tab.field("VALUE").type == dtype
        assert test_env.get_data_from_df(df) == [(value,)] * batch_size


async def test_dataframe_1702(async_conn):
    "1702 - fetch_df_all() requested_schema honored for repeated execution"
    statement = "select 1 as int_col from dual"
    ora_df = await async_conn.fetch_df_all(statement)
    tab = pyarrow.table(ora_df)
    assert tab.field("INT_COL").type == pyarrow.float64()
    requested_schema = pyarrow.schema([("INT_COL", pyarrow.int8())])
    ora_df = await async_conn.fetch_df_all(
        statement, requested_schema=requested_schema
    )
    tab = pyarrow.table(ora_df)
    assert tab.field("INT_COL").type == pyarrow.int8()
    ora_df = await async_conn.fetch_df_all(statement)
    tab = pyarrow.table(ora_df)
    assert tab.field("INT_COL").type == pyarrow.float64()


async def test_dataframe_1705(async_conn):
    "1705 - fetch_df_batches() requested_schema honored for repeated execution"
    statement = "select 1 as int_col from dual"
    async for ora_df in async_conn.fetch_df_batches(statement):
        tab = pyarrow.table(ora_df)
        assert tab.field("INT_COL").type == pyarrow.float64()
    requested_schema = pyarrow.schema([("INT_COL", pyarrow.int8())])
    async for ora_df in async_conn.fetch_df_batches(
        statement, requested_schema=requested_schema
    ):
        tab = pyarrow.table(ora_df)
        assert tab.field("INT_COL").type == pyarrow.int8()
    async for ora_df in async_conn.fetch_df_batches(statement):
        tab = pyarrow.table(ora_df)
        assert tab.field("INT_COL").type == pyarrow.float64()


@pytest.mark.parametrize(
    "dtype,value",
    [
        (pyarrow.int8(), -129),
        (pyarrow.int8(), 128),
        (pyarrow.int16(), -32769),
        (pyarrow.int16(), 32768),
        (pyarrow.int32(), -2147483649),
        (pyarrow.int32(), 2147483648),
        (pyarrow.uint8(), -1),
        (pyarrow.uint8(), 256),
        (pyarrow.uint16(), -1),
        (pyarrow.uint16(), 65536),
        (pyarrow.uint32(), -1),
        (pyarrow.uint32(), 4294967296),
    ],
)
async def test_dataframe_1726(dtype, value, async_conn, test_env):
    "1726 - fetch_df_all() for out of range integer values"
    requested_schema = pyarrow.schema([("VALUE", dtype)])
    with test_env.assert_raises_full_code("DPY-4038"):
        await async_conn.fetch_df_all(
            "select :1 from dual", [value], requested_schema=requested_schema
        )


@pytest.mark.parametrize("value", [b"Too short", b"Much too long"])
async def test_dataframe_1727(value, async_conn, test_env):
    "1727 - fetch_df_all() with fixed width binary violations"
    requested_schema = pyarrow.schema([("VALUE", pyarrow.binary(length=10))])
    with test_env.assert_raises_full_code("DPY-4040"):
        await async_conn.fetch_df_all(
            "select :1 from dual", [value], requested_schema=requested_schema
        )


@pytest.mark.parametrize("num_elements", [1, 3])
async def test_dataframe_1728(num_elements, async_conn, test_env):
    "1728 - fetch_df_all() with wrong requested_schema size"
    elements = [(f"COL_{i}", pyarrow.string()) for i in range(num_elements)]
    requested_schema = pyarrow.schema(elements)
    with test_env.assert_raises_full_code("DPY-2069"):
        await async_conn.fetch_df_all(
            "select user, user from dual", requested_schema=requested_schema
        )


@pytest.mark.parametrize("num_elements", [1, 3])
async def test_dataframe_1729(num_elements, async_conn, test_env):
    "1729 - fetch_df_batches() with wrong requested_schema size"
    elements = [(f"COL_{i}", pyarrow.string()) for i in range(num_elements)]
    requested_schema = pyarrow.schema(elements)
    with test_env.assert_raises_full_code("DPY-2069"):
        async for df in async_conn.fetch_df_batches(
            "select user, user from dual", requested_schema=requested_schema
        ):
            pass


@pytest.mark.parametrize(
    "value",
    [
        "9007199254740993",
        "22222222222222222222222222222222222222",
        "88888888888888888888.888888888888888888",
        "-0.0000000000000000000000000000000000001",
        "0.99999999999999999999999999999999999999",
        "1.9876543210987654321098765432109876543",
        "9876543210987654321098765432109876543.7",
    ],
)
async def test_dataframe_1730(async_conn, value):
    "1730 - fetch_df_all() for unconstrained NUMBER with decimal256"
    dtype = pyarrow.decimal256(precision=76, scale=38)
    requested_schema = pyarrow.schema([("VALUE", dtype)])
    ora_df = await async_conn.fetch_df_all(
        "select to_number(:1) from dual",
        [value],
        requested_schema=requested_schema,
    )
    tab = pyarrow.table(ora_df)
    assert tab.field("VALUE").type == dtype
    assert [v.as_py() for v in tab["VALUE"]] == [decimal.Decimal(value)]
    async for ora_df in async_conn.fetch_df_batches(
        "select to_number(:1) from dual",
        [value],
        requested_schema=requested_schema,
    ):
        tab = pyarrow.table(ora_df)
        assert tab.field("VALUE").type == dtype
        assert [v.as_py() for v in tab["VALUE"]] == [decimal.Decimal(value)]


async def test_dataframe_1731(test_env, async_conn):
    "1731 - fetch_df_all() for decimal256 scale overflow"
    dtype = pyarrow.decimal256(precision=76, scale=0)
    requested_schema = pyarrow.schema([("VALUE", dtype)])
    with test_env.assert_raises_full_code("DPY-4042"):
        await async_conn.fetch_df_all(
            "select 1e100 from dual", requested_schema=requested_schema
        )


async def test_dataframe_1732(async_conn):
    "1732 - decimal256 with large scale"
    value = "1e-76"
    expected_values = [
        decimal.Decimal(value),
        decimal.Decimal(f"-{value}"),
    ]
    dtype = pyarrow.decimal256(precision=76, scale=76)
    requested_schema = pyarrow.schema([("VALUE", dtype)])
    ora_df = await async_conn.fetch_df_all(
        """
        select to_number(:1) from dual
        union all
        select to_number(:2) from dual
        """,
        [value, f"-{value}"],
        requested_schema=requested_schema,
    )
    tab = pyarrow.table(ora_df)
    assert tab.field("VALUE").type == dtype
    assert [v.as_py() for v in tab["VALUE"]] == expected_values
