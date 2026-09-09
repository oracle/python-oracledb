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
Module for testing user requested schema in fetch_df APIs
"""

import decimal
import datetime

import oracledb
import pyarrow
import pytest


@pytest.mark.parametrize(
    "dtype",
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
)
def test_dataframe_1600(dtype, conn):
    "1600 - fetch_df_all() with fixed width integer types"
    statement = "select 1 from dual"
    requested_schema = pyarrow.schema([("INT_COL", dtype)])
    ora_df = conn.fetch_df_all(statement, requested_schema=requested_schema)
    tab = pyarrow.table(ora_df)
    assert tab.field("INT_COL").type == dtype
    assert tab["INT_COL"][0].as_py() == 1


@pytest.mark.parametrize(
    "dtype",
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
)
def test_dataframe_1601(dtype, conn):
    "1601 - fetch_df_all() with duplicate fixed width integer types"
    requested_schema = pyarrow.schema([("INT_COL", dtype)])
    ora_df = conn.fetch_df_all(
        """
        select 99 from dual
        union all
        select 99 from dual
        union all
        select 99 from dual
        union all
        select 99 from dual
        union all
        select 99 from dual
        union all
        select 99 from dual
        """,
        requested_schema=requested_schema,
    )
    tab = pyarrow.table(ora_df)
    assert len(tab) == 6
    assert tab.field("INT_COL").type == dtype
    for value in tab["INT_COL"]:
        assert value.as_py() == 99


def test_dataframe_1602(conn):
    "1602 - fetch_df_all() requested_schema honored for repeated execution"
    statement = "select 1 as int_col from dual"
    ora_df = conn.fetch_df_all(statement)
    tab = pyarrow.table(ora_df)
    assert tab.field("INT_COL").type == pyarrow.float64()
    requested_schema = pyarrow.schema([("INT_COL", pyarrow.int8())])
    ora_df = conn.fetch_df_all(statement, requested_schema=requested_schema)
    tab = pyarrow.table(ora_df)
    assert tab.field("INT_COL").type == pyarrow.int8()
    ora_df = conn.fetch_df_all(statement)
    tab = pyarrow.table(ora_df)
    assert tab.field("INT_COL").type == pyarrow.float64()


@pytest.mark.parametrize(
    "dtype",
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
)
def test_dataframe_1603(dtype, conn):
    "1603 - fetch_df_batches() with fixed width integer types"
    statement = "select 1 from dual"
    requested_schema = pyarrow.schema([("INT_COL", dtype)])
    for ora_df in conn.fetch_df_batches(
        statement, requested_schema=requested_schema
    ):
        tab = pyarrow.table(ora_df)
        assert tab.field("INT_COL").type == dtype
        assert tab["INT_COL"][0].as_py() == 1


@pytest.mark.parametrize(
    "dtype",
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
)
def test_dataframe_1604(dtype, conn):
    "1604 - fetch_df_batches() with duplicate fixed width integer types"
    requested_schema = pyarrow.schema([("INT_COL", dtype)])
    for ora_df in conn.fetch_df_batches(
        """
        select 99 from dual
        union all
        select 99 from dual
        union all
        select 99 from dual
        union all
        select 99 from dual
        union all
        select 99 from dual
        union all
        select 99 from dual
        """,
        requested_schema=requested_schema,
    ):
        tab = pyarrow.table(ora_df)
        assert len(tab) == 6
        assert tab.field("INT_COL").type == dtype
        for value in tab["INT_COL"]:
            assert value.as_py() == 99


def test_dataframe_1605(conn):
    "1605 - fetch_df_batches() requested_schema honored for repeated execution"
    statement = "select 1 as int_col from dual"
    for ora_df in conn.fetch_df_batches(statement):
        tab = pyarrow.table(ora_df)
        assert tab.field("INT_COL").type == pyarrow.float64()
    requested_schema = pyarrow.schema([("INT_COL", pyarrow.int8())])
    for ora_df in conn.fetch_df_batches(
        statement, requested_schema=requested_schema
    ):
        tab = pyarrow.table(ora_df)
        assert tab.field("INT_COL").type == pyarrow.int8()
    for ora_df in conn.fetch_df_batches(statement):
        tab = pyarrow.table(ora_df)
        assert tab.field("INT_COL").type == pyarrow.float64()


@pytest.mark.parametrize(
    "dtype",
    [
        pyarrow.decimal128(precision=3, scale=2),
        pyarrow.float32(),
        pyarrow.float64(),
    ],
)
def test_dataframe_1606(dtype, conn):
    "1606 - fetch_df_all() for NUMBER"
    value = 2.75
    requested_schema = pyarrow.schema([("DECIMAL_COL", dtype)])
    statement = f"select {value} from dual"
    ora_df = conn.fetch_df_all(statement, requested_schema=requested_schema)
    tab = pyarrow.table(ora_df)
    assert tab.field("DECIMAL_COL").type == dtype
    assert tab["DECIMAL_COL"][0].as_py() == value


@pytest.mark.parametrize(
    "dtype",
    [pyarrow.float32(), pyarrow.float64()],
)
def test_dataframe_1607(dtype, conn):
    "1607 - fetch_df_all() for BINARY_DOUBLE"
    value = 123.25
    requested_schema = pyarrow.schema([("BINARY_DOUBLE_COL", dtype)])
    statement = f"select to_binary_double({value}) from dual"
    ora_df = conn.fetch_df_all(statement, requested_schema=requested_schema)
    tab = pyarrow.table(ora_df)
    assert tab.field("BINARY_DOUBLE_COL").type == dtype
    assert tab["BINARY_DOUBLE_COL"][0].as_py() == value


@pytest.mark.parametrize(
    "dtype",
    [pyarrow.float32(), pyarrow.float64()],
)
def test_dataframe_1608(dtype, conn):
    "1608 - fetch_df_all() for BINARY_FLOAT"
    value = 123.625
    requested_schema = pyarrow.schema([("BINARY_FLOAT_COL", dtype)])
    statement = f"select to_binary_float({value}) from dual"
    ora_df = conn.fetch_df_all(statement, requested_schema=requested_schema)
    tab = pyarrow.table(ora_df)
    assert tab.field("BINARY_FLOAT_COL").type == dtype
    assert tab["BINARY_FLOAT_COL"][0].as_py() == value


@pytest.mark.parametrize(
    "dtype",
    [pyarrow.binary(length=6), pyarrow.binary(), pyarrow.large_binary()],
)
def test_dataframe_1609(dtype, conn):
    "1609 - fetch_df_all() for RAW"
    value = "ABCDEF"
    requested_schema = pyarrow.schema([("RAW_COL", dtype)])
    statement = f"select utl_raw.cast_to_raw('{value}') as raw_col from dual"
    ora_df = conn.fetch_df_all(statement, requested_schema=requested_schema)
    tab = pyarrow.table(ora_df)
    assert tab.field("RAW_COL").type == dtype
    assert tab["RAW_COL"][0].as_py() == value.encode()


@pytest.mark.parametrize(
    "dtype,value_is_date",
    [
        (pyarrow.date32(), True),
        (pyarrow.date64(), True),
        (pyarrow.timestamp("s"), False),
        (pyarrow.timestamp("us"), False),
        (pyarrow.timestamp("ms"), False),
        (pyarrow.timestamp("ns"), False),
    ],
)
def test_dataframe_1610(dtype, value_is_date, conn):
    "1610 - fetch_df_all() for DATE"
    requested_schema = pyarrow.schema([("DATE_COL", dtype)])
    value = datetime.datetime(2025, 2, 18)
    statement = "select cast(:1 as date) from dual"
    ora_df = conn.fetch_df_all(
        statement, [value], requested_schema=requested_schema
    )
    tab = pyarrow.table(ora_df)
    assert tab.field("DATE_COL").type == dtype
    if value_is_date:
        value = value.date()
    assert tab["DATE_COL"][0].as_py() == value


@pytest.mark.parametrize(
    "dtype",
    [
        pyarrow.date32(),
        pyarrow.date64(),
        pyarrow.timestamp("s"),
        pyarrow.timestamp("us"),
        pyarrow.timestamp("ms"),
        pyarrow.timestamp("ns"),
    ],
)
def test_dataframe_1611(dtype, conn):
    "1611 - fetch_df_all() for TIMESTAMP"
    requested_schema = pyarrow.schema([("TIMESTAMP_COL", dtype)])
    value = datetime.datetime(1974, 4, 4, 0, 57, 54, 15079)
    var = conn.cursor().var(oracledb.DB_TYPE_TIMESTAMP)
    var.setvalue(0, value)
    statement = "select :1 from dual"
    ora_df = conn.fetch_df_all(
        statement, [var], requested_schema=requested_schema
    )
    tab = pyarrow.table(ora_df)
    assert tab.field("TIMESTAMP_COL").type == dtype
    if not isinstance(dtype, pyarrow.TimestampType):
        value = value.date()
    elif dtype.unit == "s":
        value = value.replace(microsecond=0)
    elif dtype.unit == "ms":
        value = value.replace(microsecond=(value.microsecond // 1000) * 1000)
    assert tab["TIMESTAMP_COL"][0].as_py() == value


@pytest.mark.parametrize(
    "dtype,value_is_date",
    [
        (pyarrow.date32(), True),
        (pyarrow.date64(), True),
        (pyarrow.timestamp("s"), False),
        (pyarrow.timestamp("us"), False),
        (pyarrow.timestamp("ms"), False),
        (pyarrow.timestamp("ns"), False),
    ],
)
def test_dataframe_1612(dtype, value_is_date, conn):
    "1612 - fetch_df_all() for TIMESTAMP WITH LOCAL TIME ZONE"
    requested_schema = pyarrow.schema([("TIMESTAMP_LTZ_COL", dtype)])
    value = datetime.datetime(2025, 3, 4)
    statement = "select cast(:1 as timestamp with local time zone) from dual"
    ora_df = conn.fetch_df_all(
        statement, [value], requested_schema=requested_schema
    )
    tab = pyarrow.table(ora_df)
    assert tab.field("TIMESTAMP_LTZ_COL").type == dtype
    if value_is_date:
        value = value.date()
    assert tab["TIMESTAMP_LTZ_COL"][0].as_py() == value


@pytest.mark.parametrize(
    "dtype,value_is_date",
    [
        (pyarrow.date32(), True),
        (pyarrow.date64(), True),
        (pyarrow.timestamp("s"), False),
        (pyarrow.timestamp("us"), False),
        (pyarrow.timestamp("ms"), False),
        (pyarrow.timestamp("ns"), False),
    ],
)
def test_dataframe_1613(dtype, value_is_date, conn):
    "1613 - fetch_df_all() for TIMESTAMP WITH TIME ZONE"
    requested_schema = pyarrow.schema([("TIMESTAMP_TZ_COL", dtype)])
    value = datetime.datetime(2025, 3, 4)
    statement = "select cast(:1 as timestamp with time zone) from dual"
    ora_df = conn.fetch_df_all(
        statement, [value], requested_schema=requested_schema
    )
    tab = pyarrow.table(ora_df)
    assert tab.field("TIMESTAMP_TZ_COL").type == dtype
    if value_is_date:
        value = value.date()
    assert tab["TIMESTAMP_TZ_COL"][0].as_py() == value


@pytest.mark.parametrize(
    "dtype",
    [pyarrow.binary(length=6), pyarrow.binary(), pyarrow.large_binary()],
)
def test_dataframe_1614(dtype, conn):
    "1614 - fetch_df_all() for BLOB"
    value = "GHIJKL"
    requested_schema = pyarrow.schema([("BLOB_COL", dtype)])
    statement = f"select to_blob(utl_raw.cast_to_raw('{value}')) from dual"
    ora_df = conn.fetch_df_all(statement, requested_schema=requested_schema)
    tab = pyarrow.table(ora_df)
    assert tab.field("BLOB_COL").type == dtype
    assert tab["BLOB_COL"][0].as_py() == value.encode()


@pytest.mark.parametrize(
    "db_type_name",
    ["CHAR", "NCHAR", "VARCHAR2", "NVARCHAR2"],
)
@pytest.mark.parametrize("dtype", [pyarrow.string(), pyarrow.large_string()])
def test_dataframe_1615(db_type_name, dtype, conn):
    "1615 - fetch_df_all() for string types"
    value = "test_1615"
    requested_schema = pyarrow.schema([("STRING_COL", dtype)])
    statement = f"select cast('{value}' as {db_type_name}(9)) from dual"
    ora_df = conn.fetch_df_all(statement, requested_schema=requested_schema)
    tab = pyarrow.table(ora_df)
    assert tab.field("STRING_COL").type == dtype
    assert tab["STRING_COL"][0].as_py() == value


@pytest.mark.parametrize("db_type_name", ["CLOB", "NCLOB"])
@pytest.mark.parametrize("dtype", [pyarrow.string(), pyarrow.large_string()])
def test_dataframe_1616(db_type_name, dtype, conn):
    "1616 - fetch_df_all() for CLOB types"
    value = "test_dataframe_1616"
    requested_schema = pyarrow.schema([("CLOB_COL", dtype)])
    statement = f"select to_{db_type_name.lower()}('{value}') from dual"
    ora_df = conn.fetch_df_all(statement, requested_schema=requested_schema)
    tab = pyarrow.table(ora_df)
    assert tab.field("CLOB_COL").type == dtype
    assert tab["CLOB_COL"][0].as_py() == value


@pytest.mark.parametrize(
    "dtype",
    [
        pyarrow.decimal128(precision=4, scale=2),
        pyarrow.float32(),
        pyarrow.float64(),
    ],
)
def test_dataframe_1617(dtype, conn):
    "1617 - fetch_df_all() for NUMBER duplicate values"
    value = 93.25
    requested_schema = pyarrow.schema([("DECIMAL_COL", dtype)])
    ora_df = conn.fetch_df_all(
        f"""
        select {value} from dual
        union all
        select {value} from dual
        union all
        select {value} from dual
        union all
        select {value} from dual
        union all
        select {value} from dual
        union all
        select {value} from dual
        """,
        requested_schema=requested_schema,
    )
    tab = pyarrow.table(ora_df)
    assert tab.field("DECIMAL_COL").type == dtype
    for fetched_value in tab["DECIMAL_COL"]:
        assert fetched_value.as_py() == value


@pytest.mark.parametrize(
    "dtype",
    [pyarrow.float32(), pyarrow.float64()],
)
def test_dataframe_1618(dtype, conn):
    "1618 - fetch_df_all() for BINARY_DOUBLE duplicate values"
    value = 523.75
    requested_schema = pyarrow.schema([("BINARY_DOUBLE_COL", dtype)])
    ora_df = conn.fetch_df_all(
        f"""
        select to_binary_double({value}) from dual
        union all
        select to_binary_double({value}) from dual
        union all
        select to_binary_double({value}) from dual
        union all
        select to_binary_double({value}) from dual
        union all
        select to_binary_double({value}) from dual
        union all
        select to_binary_double({value}) from dual
        """,
        requested_schema=requested_schema,
    )
    tab = pyarrow.table(ora_df)
    assert tab.field("BINARY_DOUBLE_COL").type == dtype
    for fetched_value in tab["BINARY_DOUBLE_COL"]:
        assert fetched_value.as_py() == value


@pytest.mark.parametrize(
    "dtype",
    [pyarrow.float32(), pyarrow.float64()],
)
def test_dataframe_1619(dtype, conn):
    "1619 - fetch_df_all() for BINARY_FLOAT duplicate values"
    value = 9308.125
    requested_schema = pyarrow.schema([("BINARY_FLOAT_COL", dtype)])
    ora_df = conn.fetch_df_all(
        f"""
        select to_binary_float({value}) from dual
        union all
        select to_binary_float({value}) from dual
        union all
        select to_binary_float({value}) from dual
        union all
        select to_binary_float({value}) from dual
        union all
        select to_binary_float({value}) from dual
        union all
        select to_binary_float({value}) from dual
        """,
        requested_schema=requested_schema,
    )
    tab = pyarrow.table(ora_df)
    assert tab.field("BINARY_FLOAT_COL").type == dtype
    for fetched_value in tab["BINARY_FLOAT_COL"]:
        assert fetched_value.as_py() == value


@pytest.mark.parametrize(
    "dtype",
    [pyarrow.binary(length=6), pyarrow.binary(), pyarrow.large_binary()],
)
def test_dataframe_1620(dtype, conn):
    "1620 - fetch_df_all() for RAW duplicate values"
    value = "A23456"
    requested_schema = pyarrow.schema([("RAW_COL", dtype)])
    ora_df = conn.fetch_df_all(
        f"""
        select utl_raw.cast_to_raw('{value}') from dual
        union all
        select utl_raw.cast_to_raw('{value}') from dual
        union all
        select utl_raw.cast_to_raw('{value}') from dual
        union all
        select utl_raw.cast_to_raw('{value}') from dual
        union all
        select utl_raw.cast_to_raw('{value}') from dual
        union all
        select utl_raw.cast_to_raw('{value}') from dual
        """,
        requested_schema=requested_schema,
    )
    tab = pyarrow.table(ora_df)
    assert tab.field("RAW_COL").type == dtype
    for fetched_value in tab["RAW_COL"]:
        assert fetched_value.as_py() == value.encode()


@pytest.mark.parametrize(
    "dtype,value_is_date",
    [
        (pyarrow.date32(), True),
        (pyarrow.date64(), True),
        (pyarrow.timestamp("s"), False),
        (pyarrow.timestamp("us"), False),
        (pyarrow.timestamp("ms"), False),
        (pyarrow.timestamp("ns"), False),
    ],
)
def test_dataframe_1621(dtype, value_is_date, conn):
    "1621 - fetch_df_all() for DATE duplicate values"
    requested_schema = pyarrow.schema([("DATE_COL", dtype)])
    value = datetime.datetime(2025, 3, 1)
    parameters = dict(value=value)
    ora_df = conn.fetch_df_all(
        """
        select cast(:value as date) from dual
        union all
        select cast(:value as date) from dual
        union all
        select cast(:value as date) from dual
        union all
        select cast(:value as date) from dual
        union all
        select cast(:value as date) from dual
        union all
        select cast(:value as date) from dual
        """,
        parameters,
        requested_schema=requested_schema,
    )
    tab = pyarrow.table(ora_df)
    assert tab.field("DATE_COL").type == dtype
    if value_is_date:
        value = value.date()
    for fetched_value in tab["DATE_COL"]:
        assert fetched_value.as_py() == value


@pytest.mark.parametrize(
    "dtype,value_is_date",
    [
        (pyarrow.date32(), True),
        (pyarrow.date64(), True),
        (pyarrow.timestamp("s"), False),
        (pyarrow.timestamp("us"), False),
        (pyarrow.timestamp("ms"), False),
        (pyarrow.timestamp("ns"), False),
    ],
)
def test_dataframe_1622(dtype, value_is_date, conn):
    "1622 - fetch_df_all() for TIMESTAMP duplicate values"
    requested_schema = pyarrow.schema([("TIMESTAMP_COL", dtype)])
    value = datetime.datetime(2025, 1, 14)
    parameters = dict(value=value)
    ora_df = conn.fetch_df_all(
        """
        select cast(:value as timestamp) from dual
        union all
        select cast(:value as timestamp) from dual
        union all
        select cast(:value as timestamp) from dual
        union all
        select cast(:value as timestamp) from dual
        union all
        select cast(:value as timestamp) from dual
        union all
        select cast(:value as timestamp) from dual
        """,
        parameters,
        requested_schema=requested_schema,
    )
    tab = pyarrow.table(ora_df)
    assert tab.field("TIMESTAMP_COL").type == dtype
    if value_is_date:
        value = value.date()
    for fetched_value in tab["TIMESTAMP_COL"]:
        assert fetched_value.as_py() == value


@pytest.mark.parametrize(
    "dtype,value_is_date",
    [
        (pyarrow.date32(), True),
        (pyarrow.date64(), True),
        (pyarrow.timestamp("s"), False),
        (pyarrow.timestamp("us"), False),
        (pyarrow.timestamp("ms"), False),
        (pyarrow.timestamp("ns"), False),
    ],
)
def test_dataframe_1623(dtype, value_is_date, conn):
    "1623 - fetch_df_all() for TIMESTAMP WITH LOCAL TIME ZONE duplicate values"
    requested_schema = pyarrow.schema([("TIMESTAMP_LTZ_COL", dtype)])
    value = datetime.datetime(2025, 3, 6)
    parameters = dict(value=value)
    ora_df = conn.fetch_df_all(
        """
        select cast(:value as timestamp with local time zone) from dual
        union all
        select cast(:value as timestamp with local time zone) from dual
        union all
        select cast(:value as timestamp with local time zone) from dual
        union all
        select cast(:value as timestamp with local time zone) from dual
        union all
        select cast(:value as timestamp with local time zone) from dual
        union all
        select cast(:value as timestamp with local time zone) from dual
        """,
        parameters,
        requested_schema=requested_schema,
    )
    tab = pyarrow.table(ora_df)
    assert tab.field("TIMESTAMP_LTZ_COL").type == dtype
    if value_is_date:
        value = value.date()
    for fetched_value in tab["TIMESTAMP_LTZ_COL"]:
        assert fetched_value.as_py() == value


@pytest.mark.parametrize(
    "dtype,value_is_date",
    [
        (pyarrow.date32(), True),
        (pyarrow.date64(), True),
        (pyarrow.timestamp("s"), False),
        (pyarrow.timestamp("us"), False),
        (pyarrow.timestamp("ms"), False),
        (pyarrow.timestamp("ns"), False),
    ],
)
def test_dataframe_1624(dtype, value_is_date, conn):
    "1624 - fetch_df_all() for TIMESTAMP WITH TIME ZONE duplicate values"
    requested_schema = pyarrow.schema([("TIMESTAMP_TZ_COL", dtype)])
    value = datetime.datetime(2025, 2, 28)
    parameters = dict(value=value)
    ora_df = conn.fetch_df_all(
        """
        select cast(:value as timestamp with time zone) from dual
        union all
        select cast(:value as timestamp with time zone) from dual
        union all
        select cast(:value as timestamp with time zone) from dual
        union all
        select cast(:value as timestamp with time zone) from dual
        union all
        select cast(:value as timestamp with time zone) from dual
        union all
        select cast(:value as timestamp with time zone) from dual
        """,
        parameters,
        requested_schema=requested_schema,
    )
    tab = pyarrow.table(ora_df)
    assert tab.field("TIMESTAMP_TZ_COL").type == dtype
    if value_is_date:
        value = value.date()
    for fetched_value in tab["TIMESTAMP_TZ_COL"]:
        assert fetched_value.as_py() == value


@pytest.mark.parametrize(
    "db_type_name",
    ["CHAR", "NCHAR", "VARCHAR2", "NVARCHAR2"],
)
@pytest.mark.parametrize("dtype", [pyarrow.string(), pyarrow.large_string()])
def test_dataframe_1625(db_type_name, dtype, conn):
    "1625 - fetch_df_all() for string types duplicate values"
    value = "test_1625"
    requested_schema = pyarrow.schema([("STRING_COL", dtype)])
    ora_df = conn.fetch_df_all(
        f"""
        select cast('{value}' as {db_type_name}(9)) from dual
        union all
        select cast('{value}' as {db_type_name}(9)) from dual
        union all
        select cast('{value}' as {db_type_name}(9)) from dual
        union all
        select cast('{value}' as {db_type_name}(9)) from dual
        union all
        select cast('{value}' as {db_type_name}(9)) from dual
        union all
        select cast('{value}' as {db_type_name}(9)) from dual
        """,
        requested_schema=requested_schema,
    )
    tab = pyarrow.table(ora_df)
    assert tab.field("STRING_COL").type == dtype
    for fetched_value in tab["STRING_COL"]:
        assert fetched_value.as_py() == value


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
def test_dataframe_1626(dtype, value, conn, test_env):
    "1626 - fetch_df_all() for out of range integer values"
    requested_schema = pyarrow.schema([("VALUE", dtype)])
    with test_env.assert_raises_full_code("DPY-4038"):
        conn.fetch_df_all(
            "select :1 from dual", [value], requested_schema=requested_schema
        )


@pytest.mark.parametrize("value", [b"Too short", b"Much too long"])
def test_dataframe_1627(value, conn, test_env):
    "1627 - fetch_df_all() with fixed width binary violations"
    requested_schema = pyarrow.schema([("VALUE", pyarrow.binary(length=10))])
    with test_env.assert_raises_full_code("DPY-4040"):
        conn.fetch_df_all(
            "select :1 from dual", [value], requested_schema=requested_schema
        )


@pytest.mark.parametrize("num_elements", [1, 3])
def test_dataframe_1628(num_elements, conn, test_env):
    "1628 - fetch_df_all() with wrong requested_schema size"
    elements = [(f"COL_{i}", pyarrow.string()) for i in range(num_elements)]
    requested_schema = pyarrow.schema(elements)
    with test_env.assert_raises_full_code("DPY-2069"):
        conn.fetch_df_all(
            "select user, user from dual", requested_schema=requested_schema
        )


@pytest.mark.parametrize("num_elements", [1, 3])
def test_dataframe_1629(num_elements, conn, test_env):
    "1629 - fetch_df_batches() with wrong requested_schema size"
    elements = [(f"COL_{i}", pyarrow.string()) for i in range(num_elements)]
    requested_schema = pyarrow.schema(elements)
    with test_env.assert_raises_full_code("DPY-2069"):
        list(
            conn.fetch_df_batches(
                "select user, user from dual",
                requested_schema=requested_schema,
            )
        )


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
def test_dataframe_1630(conn, value):
    "1630 - unconstrained NUMBER with decimal256"
    dtype = pyarrow.decimal256(precision=76, scale=38)
    requested_schema = pyarrow.schema([("VALUE", dtype)])
    ora_df = conn.fetch_df_all(
        "select to_number(:1) from dual",
        [value],
        requested_schema=requested_schema,
    )
    tab = pyarrow.table(ora_df)
    assert tab.field("VALUE").type == dtype
    assert [v.as_py() for v in tab["VALUE"]] == [decimal.Decimal(value)]
    for ora_df in conn.fetch_df_batches(
        "select to_number(:1) from dual",
        [value],
        requested_schema=requested_schema,
    ):
        tab = pyarrow.table(ora_df)
        assert tab.field("VALUE").type == dtype
        assert [v.as_py() for v in tab["VALUE"]] == [decimal.Decimal(value)]


def test_dataframe_1631(test_env, conn):
    "1631 - fetch_df_all() for decimal256 scale overflow"
    dtype = pyarrow.decimal256(precision=76, scale=0)
    requested_schema = pyarrow.schema([("VALUE", dtype)])
    with test_env.assert_raises_full_code("DPY-4042"):
        conn.fetch_df_all(
            "select 1e100 from dual", requested_schema=requested_schema
        )


def test_dataframe_1632(conn):
    "1632 - decimal256 with large scale"
    value = "1e-76"
    expected_values = [
        decimal.Decimal(value),
        decimal.Decimal(f"-{value}"),
    ]
    dtype = pyarrow.decimal256(precision=76, scale=76)
    requested_schema = pyarrow.schema([("VALUE", dtype)])
    ora_df = conn.fetch_df_all(
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
