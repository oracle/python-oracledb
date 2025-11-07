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
Module for testing user requested schema in fetch_df APIs
"""

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
def test_9300(dtype, conn):
    "9300 - fetch_df_all() with fixed width integer types"
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
def test_9301(dtype, conn):
    "9301 - fetch_df_all() with duplicate fixed width integer types"
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


def test_9302(conn):
    "9302 - fetch_df_all() requested_schema honored for repeated execution"
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
def test_9303(dtype, conn):
    "9303 - fetch_df_batches() with fixed width integer types"
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
def test_9304(dtype, conn):
    "9304 - fetch_df_batches() with duplicate fixed width integer types"
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


def test_9305(conn):
    "9305 - fetch_df_batches() requested_schema honored for repeated execution"
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
def test_9306(dtype, conn):
    "9306 - fetch_df_all() for NUMBER"
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
def test_9307(dtype, conn):
    "9307 - fetch_df_all() for BINARY_DOUBLE"
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
def test_9308(dtype, conn):
    "9308 - fetch_df_all() for BINARY_FLOAT"
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
def test_9309(dtype, conn):
    "9309 - fetch_df_all() for RAW"
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
def test_9310(dtype, value_is_date, conn):
    "9310 - fetch_df_all() for DATE"
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
def test_9311(dtype, conn):
    "9311 - fetch_df_all() for TIMESTAMP"
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
def test_9312(dtype, value_is_date, conn):
    "9312 - fetch_df_all() for TIMESTAMP WITH LOCAL TIME ZONE"
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
def test_9313(dtype, value_is_date, conn):
    "9313 - fetch_df_all() for TIMESTAMP WITH TIME ZONE"
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
def test_9314(dtype, conn):
    "9314 - fetch_df_all() for BLOB"
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
def test_9315(db_type_name, dtype, conn):
    "9315 - fetch_df_all() for string types"
    value = "test_9315"
    requested_schema = pyarrow.schema([("STRING_COL", dtype)])
    statement = f"select cast('{value}' as {db_type_name}(9)) from dual"
    ora_df = conn.fetch_df_all(statement, requested_schema=requested_schema)
    tab = pyarrow.table(ora_df)
    assert tab.field("STRING_COL").type == dtype
    assert tab["STRING_COL"][0].as_py() == value


@pytest.mark.parametrize("db_type_name", ["CLOB", "NCLOB"])
@pytest.mark.parametrize("dtype", [pyarrow.string(), pyarrow.large_string()])
def test_9316(db_type_name, dtype, conn):
    "9316 - fetch_df_all() for CLOB types"
    value = "test_9316"
    requested_schema = pyarrow.schema([("CLOB_COL", dtype)])
    statement = f"select to_{db_type_name.lower()}('{value}') from dual"
    ora_df = conn.fetch_df_all(statement, requested_schema=requested_schema)
    tab = pyarrow.table(ora_df)
    assert tab.field("CLOB_COL").type == dtype
    assert tab["CLOB_COL"][0].as_py() == value


@pytest.mark.parametrize(
    "dtype",
    [
        pyarrow.decimal128(precision=3, scale=2),
        pyarrow.float32(),
        pyarrow.float64(),
    ],
)
def test_9317(dtype, conn):
    "9317 - fetch_df_all() for NUMBER duplicate values"
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
def test_9318(dtype, conn):
    "9318 - fetch_df_all() for BINARY_DOUBLE duplicate values"
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
def test_9319(dtype, conn):
    "9319 - fetch_df_all() for BINARY_FLOAT duplicate values"
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
def test_9320(dtype, conn):
    "9320 - fetch_df_all() for RAW duplicate values"
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
def test_9321(dtype, value_is_date, conn):
    "9321 - fetch_df_all() for DATE duplicate values"
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
def test_9322(dtype, value_is_date, conn):
    "9322 - fetch_df_all() for TIMESTAMP duplicate values"
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
def test_9323(dtype, value_is_date, conn):
    "9323 - fetch_df_all() for TIMESTAMP WITH LOCAL TIME ZONE duplicate values"
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
def test_9324(dtype, value_is_date, conn):
    "9324 - fetch_df_all() for TIMESTAMP WITH TIME ZONE duplicate values"
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
def test_9325(db_type_name, dtype, conn):
    "9325 - fetch_df_all() for string types duplicate values"
    value = "test_9325"
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
def test_9326(dtype, value, conn, test_env):
    "9326 - fetch_df_all() for out of range integer values"
    requested_schema = pyarrow.schema([("VALUE", dtype)])
    with test_env.assert_raises_full_code("DPY-4038"):
        conn.fetch_df_all(
            "select :1 from dual", [value], requested_schema=requested_schema
        )


@pytest.mark.parametrize("value", [b"Too short", b"Much too long"])
def test_9327(value, conn, test_env):
    "9327 - fetch_df_all() with fixed width binary violations"
    requested_schema = pyarrow.schema([("VALUE", pyarrow.binary(length=10))])
    with test_env.assert_raises_full_code("DPY-4040"):
        conn.fetch_df_all(
            "select :1 from dual", [value], requested_schema=requested_schema
        )


@pytest.mark.parametrize("num_elements", [1, 3])
def test_9328(num_elements, conn, test_env):
    "9328 - fetch_df_all() with wrong requested_schema size"
    elements = [(f"COL_{i}", pyarrow.string()) for i in range(num_elements)]
    requested_schema = pyarrow.schema(elements)
    with test_env.assert_raises_full_code("DPY-2069"):
        conn.fetch_df_all(
            "select user, user from dual", requested_schema=requested_schema
        )


@pytest.mark.parametrize("num_elements", [1, 3])
def test_9329(num_elements, conn, test_env):
    "9329 - fetch_df_batches() with wrong requested_schema size"
    elements = [(f"COL_{i}", pyarrow.string()) for i in range(num_elements)]
    requested_schema = pyarrow.schema(elements)
    with test_env.assert_raises_full_code("DPY-2069"):
        list(
            conn.fetch_df_batches(
                "select user, user from dual",
                requested_schema=requested_schema,
            )
        )
