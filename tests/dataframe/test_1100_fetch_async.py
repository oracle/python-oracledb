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
Module for testing fetching dataframes using asyncio.
"""

import array
import datetime
import decimal

import oracledb
import pyarrow
import pytest

# basic
DATASET_1 = [
    (
        1,
        "John",
        "Doe",
        "San Francisco",
        "USA",
        datetime.date(1955, 7, 1),  # summer(before 1970)
        12132.40,
        400,
        datetime.datetime.now(),
    ),
    (
        2,
        "Big",
        "Hero",
        "San Fransokyo",
        "Japansa",
        datetime.date(1955, 1, 1),  # winter(before 1970)
        234234.32,
        400,
        datetime.datetime.now(),
    ),
]

# None, -ve
DATASET_2 = [
    (
        1,
        "John",
        "Doe",
        "San Francisco",
        "USA",
        datetime.date(2000, 7, 1),  # summer(between)
        None,
        400,
        datetime.datetime.now(),
    ),
    (
        2,
        "Big",
        "Hero",
        "San Fransokyo",
        None,
        datetime.date(2000, 1, 1),  # winter(between)
        -12312.1,
        0,
        datetime.datetime.now(),
    ),
    (
        3,
        "Johns",
        "Does",
        "San Franciscos",
        "USAs",
        datetime.date(2040, 7, 1),  # summer(after)
        None,
        500,
        datetime.datetime.now(),
    ),
    (
        4,
        "Bigs",
        "Heros",
        "San Fransokyos",
        None,
        datetime.date(2040, 1, 1),  # winter(after)
        -12312.1,
        0,
        datetime.datetime.now(),
    ),
]

# None, +/- 0.XXX
DATASET_3 = [
    (
        1,
        "John",
        "Doe",
        "San Francisco",
        "USA",
        datetime.date(1989, 8, 22),
        None,
        400,
        datetime.datetime.now(),
    ),
    (
        2,
        "Big",
        "Hero",
        "San Fransokyo",
        None,
        datetime.date(1988, 8, 22),
        0.12,
        0,
        datetime.datetime.now(),
    ),
    (
        3,
        "John",
        "Doe",
        "San Francisco",
        "USA",
        datetime.date(1989, 8, 22),
        None,
        400,
        datetime.datetime.now(),
    ),
    (
        4,
        "Big",
        "Hero",
        "San Fransokyo",
        None,
        datetime.date(1988, 8, 22),
        -0.01,
        0,
        datetime.datetime.now(),
    ),
]

# Duplicates
DATASET_4 = [
    (
        1,
        "John",
        "Doe",
        "San Francisco",
        "USA",
        datetime.date(1989, 8, 22),
        -0.01,
        0,
        datetime.datetime.now(),
    ),
    (
        2,
        "John",
        "Doe",
        "San Francisco",
        "USA",
        datetime.date(1988, 8, 22),
        -0.01,
        0,
        datetime.datetime.now(),
    ),
    (
        3,
        "John",
        "Doe",
        "San Francisco",
        "USA",
        datetime.date(1988, 8, 22),
        -0.01,
        0,
        datetime.datetime.now(),
    ),
    (
        4,
        "John",
        "Doe",
        "San Francisco",
        "USA",
        datetime.date(1988, 8, 22),
        -0.01,
        0,
        datetime.datetime.now(),
    ),
    (
        5,
        "John",
        "Doe",
        "San Francisco",
        "USA",
        datetime.date(1988, 8, 22),
        -0.01,
        0,
        datetime.datetime.now(),
    ),
    (
        6,
        "John",
        "Doe",
        "San Francisco",
        "USA",
        datetime.date(1988, 8, 22),
        -0.01,
        0,
        datetime.datetime.now(),
    ),
]

QUERY_SQL_WITH_WHERE_CLAUSE = """
    select
        Id,
        FirstName,
        LastName,
        City,
        Country,
        DateOfBirth,
        Salary,
        CreditScore,
        LastUpdated
    from TestDataFrame
    {where_clause}
    order by id
"""

QUERY_SQL = QUERY_SQL_WITH_WHERE_CLAUSE.format(where_clause="")


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


def _convert_date(typ, value):
    """
    Converts a date to the format required by Arrow.
    """
    if value is not None:
        if typ.unit == "s":
            value = datetime.datetime(value.year, value.month, value.day)
        ts = (value - datetime.datetime(1970, 1, 1)).total_seconds()
        if typ.unit != "s":
            ts *= 1_000_000
        return ts


def _convert_to_array(data, typ):
    """
    Convert raw data to an Arrow array using pyarrow.
    """
    if isinstance(typ, pyarrow.Decimal128Type):
        data = [
            decimal.Decimal(str(value)) if value is not None else value
            for value in data
        ]
    elif isinstance(typ, pyarrow.TimestampType):
        data = [_convert_date(typ, v) for v in data]
    mask = [value is None for value in data]
    return pyarrow.array(data, typ, mask=mask)


def _convert_to_df(data):
    """
    Converts the data set to a Pandas data frame for comparison to what is
    returned from the database.
    """
    data_by_col = [[row[i] for row in data] for i in range(len(data[0]))]
    fetch_decimals = oracledb.defaults.fetch_decimals
    types = [
        pyarrow.decimal128(9) if fetch_decimals else pyarrow.int64(),
        pyarrow.large_string(),
        pyarrow.large_string(),
        pyarrow.large_string(),
        pyarrow.large_string(),
        pyarrow.timestamp("s"),
        pyarrow.decimal128(9, 2) if fetch_decimals else pyarrow.float64(),
        pyarrow.decimal128(3) if fetch_decimals else pyarrow.int64(),
        pyarrow.timestamp("us"),
    ]
    arrays = [_convert_to_array(d, t) for d, t in zip(data_by_col, types)]
    names = [
        "ID",
        "FIRSTNAME",
        "LASTNAME",
        "CITY",
        "COUNTRY",
        "DATEOFBIRTH",
        "SALARY",
        "CREDITSCORE",
        "LASTUPDATED",
    ]
    pa_tab = pyarrow.Table.from_arrays(arrays, names=names)
    pa_tab.validate(full=True)
    return pa_tab.to_pandas()


async def _populate_table(cursor, data):
    """
    Populate the test table with the given data.
    """
    await cursor.execute("delete from TestDataframe")
    types = [None] * len(data[0])
    types[8] = oracledb.DB_TYPE_TIMESTAMP
    cursor.setinputsizes(*types)
    await cursor.executemany(
        """
        insert into TestDataframe (
            Id, FirstName, LastName, City, Country,
            DateOfBirth, Salary, CreditScore, LastUpdated
        ) values (
            :id, :first_name, :last_name, :city, :country,
            :dob, :salary, :credit_score, :last_updated
        )
        """,
        data,
    )
    await cursor.connection.commit()


async def _test_df_interop(test_env, cursor, data):
    """
    Tests interoperability with external data frames using the data set
    provided.
    """
    await _populate_table(cursor, data)
    ora_df = await cursor.connection.fetch_df_all(QUERY_SQL)
    _validate_df(ora_df, data, test_env)


async def _test_df_batches_interop(
    test_env, cursor, data, batch_size, num_batches
):
    """
    Tests interoperability with external data frames using the data set
    provided.
    """
    await _populate_table(cursor, data)
    batches = [
        df
        async for df in cursor.connection.fetch_df_batches(
            QUERY_SQL, size=batch_size
        )
    ]
    assert len(batches) == num_batches
    if num_batches == 1:
        _validate_df(batches[0], data, test_env)
    else:
        offset = 0
        for batch in batches:
            _validate_df(batch, data[offset : offset + batch_size], test_env)
            offset += batch_size


def _validate_df(ora_df, data, test_env):
    """
    Validates the data frame by converting it to Pandas and comparing it
    with the original data set that was used.
    """
    raw_df = _convert_to_df(data)
    raw_data = test_env.get_data_from_df(raw_df)
    fetched_df = pyarrow.table(ora_df).to_pandas()
    fetched_data = test_env.get_data_from_df(fetched_df)
    assert fetched_data == raw_data


async def test_dataframe_1100(async_conn, async_cursor):
    "1100 - test basic fetch of data frame"
    await _populate_table(async_cursor, DATASET_1)
    ora_df = await async_conn.fetch_df_all(QUERY_SQL)
    assert ora_df.num_rows() == len(DATASET_1)
    assert ora_df.num_columns() == len(DATASET_1[0])


async def test_dataframe_1101(async_cursor, test_env):
    "1101 - test conversion to external dataframe"
    await _test_df_interop(test_env, async_cursor, DATASET_1)


async def test_dataframe_1102(async_cursor, test_env):
    "1101 - test null and negative values"
    await _test_df_interop(test_env, async_cursor, DATASET_2)


async def test_dataframe_1103(async_cursor, test_env):
    "1102 - test with fetch_decimals"
    with test_env.defaults_context_manager("fetch_decimals", True):
        await _test_df_interop(test_env, async_cursor, DATASET_1)


async def test_dataframe_1104(async_cursor, test_env):
    "1103 - test null and negative values with fetch_decimals"
    with test_env.defaults_context_manager("fetch_decimals", True):
        await _test_df_interop(test_env, async_cursor, DATASET_2)


async def test_dataframe_1105(async_cursor, test_env):
    "1105 - test null and values with leading zeros"
    await _test_df_interop(test_env, async_cursor, DATASET_3)


async def test_dataframe_1106(async_cursor, test_env):
    "1105 - test null and values with leading zeros with fetch_decimals"
    with test_env.defaults_context_manager("fetch_decimals", True):
        await _test_df_interop(test_env, async_cursor, DATASET_3)


async def test_dataframe_1107(async_cursor, test_env):
    "1107 - duplicate values in the rows"
    await _test_df_interop(test_env, async_cursor, DATASET_4)


async def test_dataframe_1108(async_cursor, test_env):
    "1108 - batches without specification of size"
    await _test_df_batches_interop(
        test_env, async_cursor, DATASET_4, batch_size=None, num_batches=1
    )


async def test_dataframe_1109(async_cursor, test_env):
    "1109 - batches with specification of size"
    await _test_df_batches_interop(
        test_env, async_cursor, DATASET_4, batch_size=5, num_batches=2
    )


async def test_dataframe_1110(async_conn, async_cursor, test_env):
    "1110 - verify passing Arrow arrays twice works"
    await _populate_table(async_cursor, DATASET_1)
    ora_df = await async_conn.fetch_df_all(QUERY_SQL)
    _validate_df(ora_df, DATASET_1, test_env)
    _validate_df(ora_df, DATASET_1, test_env)


async def test_dataframe_1111(async_conn, async_cursor):
    "1111 - verify empty data set"
    await _populate_table(async_cursor, DATASET_1)
    statement = "select * from TestDataFrame where Id = 4"
    ora_df = await async_conn.fetch_df_all(statement)
    assert ora_df.num_rows() == 0


async def test_dataframe_1112(async_conn, async_cursor):
    "1112 - verify empty data set with batches"
    await _populate_table(async_cursor, DATASET_1)
    statement = "select * from TestDataFrame where Id = 4"
    async for ora_df in async_conn.fetch_df_batches(statement):
        assert ora_df.num_rows() == 0


async def test_dataframe_1113(async_conn, async_cursor):
    "1113 - negative checks on attributes"
    await _populate_table(async_cursor, DATASET_1)
    ora_df = await async_conn.fetch_df_all(QUERY_SQL)
    with pytest.raises(IndexError):
        ora_df.get_column(121)
    with pytest.raises(IndexError):
        ora_df.get_column(-1)
    with pytest.raises(KeyError):
        ora_df.get_column_by_name("missing_column")


async def test_dataframe_1114(async_conn, test_env):
    "1114 - check unsupported error"
    statement = "select cursor(select user from dual) from dual"
    with test_env.assert_raises_full_code("DPY-3030"):
        await async_conn.fetch_df_all(statement)


async def test_dataframe_1115(async_cursor, test_env):
    "1115 - batches with specification of size matching number of rows"
    await _test_df_batches_interop(
        test_env,
        async_cursor,
        DATASET_2,
        batch_size=len(DATASET_2),
        num_batches=1,
    )


async def test_dataframe_1116(async_cursor, test_env):
    "1116 - batches with size that has duplicate rows across batches"
    await _test_df_batches_interop(
        test_env, async_cursor, DATASET_4, batch_size=3, num_batches=2
    )


async def test_dataframe_1117(async_conn, test_env):
    "1117 - fetch_decimals without precision and scale specified"
    data = [(1.0,)]
    with test_env.defaults_context_manager("fetch_decimals", True):
        ora_df = await async_conn.fetch_df_all("select 1.0 from dual")
        fetched_df = pyarrow.table(ora_df).to_pandas()
        fetched_data = test_env.get_data_from_df(fetched_df)
        assert fetched_data == data


async def test_dataframe_1118(async_conn, test_env):
    "1118 - fetch clob"
    data = [("test_1123",)]
    ora_df = await async_conn.fetch_df_all(
        "select to_clob('test_1123') from dual"
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    fetched_data = test_env.get_data_from_df(fetched_df)
    assert fetched_data == data


async def test_dataframe_1119(async_conn, test_env):
    "1119 - fetch blob"
    data = [(b"test_1124",)]
    ora_df = await async_conn.fetch_df_all(
        "select to_blob(utl_raw.cast_to_raw('test_1124')) from dual"
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    fetched_data = test_env.get_data_from_df(fetched_df)
    assert fetched_data == data


async def test_dataframe_1120(
    skip_unless_native_boolean_supported, async_conn, test_env
):
    "1120 - fetch boolean"
    data = [(True,), (False,), (False,), (True,), (True,)]
    ora_df = await async_conn.fetch_df_all("""
        select true
        union all
        select false
        union all
        select false
        union all
        select true
        union all
        select true
        """)
    fetched_df = pyarrow.table(ora_df).to_pandas()
    fetched_data = test_env.get_data_from_df(fetched_df)
    assert fetched_data == data


async def test_dataframe_1121(
    skip_unless_vectors_supported, async_conn, test_env
):
    "1121 - fetch float32 vector"
    data = [
        (array.array("f", [34.6, 77.8]).tolist(),),
        (array.array("f", [34.6, 77.8, 55.9]).tolist(),),
    ]
    ora_df = await async_conn.fetch_df_all("""
        SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT32)
        union all
        SELECT TO_VECTOR('[34.6, 77.8, 55.9]', 3, FLOAT32)
        """)
    assert ora_df.num_rows() == 2
    assert ora_df.num_columns() == 1
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


async def test_dataframe_1122(
    skip_unless_sparse_vectors_supported, async_conn, test_env
):
    "1122 - fetch float64 sparse vectors"
    data = [
        (
            {
                "num_dimensions": 8,
                "indices": [0, 7],
                "values": [34.6, 77.8],
            },
        ),
        (
            {
                "num_dimensions": 8,
                "indices": [0, 7],
                "values": [34.6, 9.1],
            },
        ),
    ]
    ora_df = await async_conn.fetch_df_all("""
        SELECT TO_VECTOR(
            TO_VECTOR('[34.6, 0, 0, 0, 0, 0, 0, 77.8]', 8, FLOAT64),
            8,
            FLOAT64,
            SPARSE
            )
        union all
        SELECT TO_VECTOR(
            TO_VECTOR('[34.6, 0, 0, 0, 0, 0, 0, 9.1]', 8, FLOAT64),
            8,
            FLOAT64,
            SPARSE
            )
        """)
    assert ora_df.num_rows() == 2
    assert ora_df.num_columns() == 1
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


async def test_dataframe_1123(async_conn, test_env):
    "1123 - fetch data with multiple rows containing null values"
    ora_df = await async_conn.fetch_df_all("""
        select to_date('2025-06-12', 'YYYY-MM-DD') as data from dual
        union all
        select to_date(null) as data from dual
        union all
        select to_date(null) as data from dual
        union all
        select to_date(null) as data from dual
        union all
        select to_date('2025-06-11', 'YYYY-MM-DD') as data from dual
        union all
        select to_date(null) as data from dual
        union all
        select to_date(null) as data from dual
        union all
        select to_date(null) as data from dual
        union all
        select to_date(null) as data from dual
        """)
    data = [
        (datetime.datetime(2025, 6, 12),),
        (None,),
        (None,),
        (None,),
        (datetime.datetime(2025, 6, 11),),
        (None,),
        (None,),
        (None,),
        (None,),
    ]
    fetched_df = pyarrow.table(ora_df).to_pandas()
    fetched_data = test_env.get_data_from_df(fetched_df)
    assert fetched_data == data


async def test_dataframe_1124(async_conn, async_cursor):
    "1124 - test metadata of all data types"
    now = datetime.datetime.now()
    data = [
        ("NUMBERVALUE", 5, pyarrow.float64()),
        ("STRINGVALUE", "String Val", pyarrow.large_string()),
        ("FIXEDCHARVALUE", "Fixed Char", pyarrow.large_string()),
        ("NSTRINGVALUE", "NString Val", pyarrow.large_string()),
        ("NFIXEDCHARVALUE", "NFixedChar", pyarrow.large_string()),
        ("RAWVALUE", b"Raw Data", pyarrow.large_binary()),
        ("INTVALUE", 25_387_923, pyarrow.float64()),
        ("SMALLINTVALUE", 127, pyarrow.float64()),
        ("REALVALUE", 125.25, pyarrow.float64()),
        ("DECIMALVALUE", 91.1025, pyarrow.float64()),
        ("DOUBLEPRECISIONVALUE", 87.625, pyarrow.float64()),
        ("FLOATVALUE", 125.375, pyarrow.float64()),
        ("BINARYFLOATVALUE", -25, pyarrow.float32()),
        ("BINARYDOUBLEVALUE", -175.5, pyarrow.float64()),
        ("DATEVALUE", now, pyarrow.timestamp("s")),
        ("TIMESTAMPVALUE", now, pyarrow.timestamp("us")),
        ("TIMESTAMPTZVALUE", now, pyarrow.timestamp("us")),
        ("TIMESTAMPLTZVALUE", now, pyarrow.timestamp("us")),
        ("CLOBVALUE", "CLOB Value", pyarrow.large_string()),
        ("NCLOBVALUE", "NCLOB Value", pyarrow.large_string()),
        ("BLOBVALUE", b"BLOB Value", pyarrow.large_binary()),
    ]
    await async_cursor.execute("delete from TestAllTypes")
    column_names = ",".join(n for n, v, t in data)
    bind_values = ",".join(f":{i + 1}" for i in range(len(data)))
    data_to_insert = tuple(v for n, v, t in data)
    await async_cursor.execute(
        f"""
        insert into TestAllTypes ({column_names})
        values ({bind_values})
        """,
        data_to_insert,
    )
    await async_conn.commit()
    sql = f"select {column_names} from TestAllTypes"
    ora_df = await async_conn.fetch_df_all(sql)
    expected_types = [t for n, v, t in data]
    actual_types = [pyarrow.array(a).type for a in ora_df.column_arrays()]
    assert actual_types == expected_types


async def test_dataframe_1125(async_conn, async_cursor, test_env):
    "1125 - test metadata of all data types with fetch_decimals = True"
    now = datetime.datetime.now()
    data = [
        ("NUMBERVALUE", 5, pyarrow.float64()),
        ("STRINGVALUE", "String Val", pyarrow.large_string()),
        ("FIXEDCHARVALUE", "Fixed Char", pyarrow.large_string()),
        ("NSTRINGVALUE", "NString Val", pyarrow.large_string()),
        ("NFIXEDCHARVALUE", "NFixedChar", pyarrow.large_string()),
        ("RAWVALUE", b"Raw Data", pyarrow.large_binary()),
        ("INTVALUE", 25_387_923, pyarrow.decimal128(38, 0)),
        ("SMALLINTVALUE", 127, pyarrow.decimal128(38, 0)),
        ("REALVALUE", 125.25, pyarrow.float64()),
        ("DECIMALVALUE", 91.1025, pyarrow.decimal128(20, 6)),
        ("DOUBLEPRECISIONVALUE", 87.625, pyarrow.float64()),
        ("FLOATVALUE", 125.375, pyarrow.float64()),
        ("BINARYFLOATVALUE", -25, pyarrow.float32()),
        ("BINARYDOUBLEVALUE", -175.5, pyarrow.float64()),
        ("DATEVALUE", now, pyarrow.timestamp("s")),
        ("TIMESTAMPVALUE", now, pyarrow.timestamp("us")),
        ("TIMESTAMPTZVALUE", now, pyarrow.timestamp("us")),
        ("TIMESTAMPLTZVALUE", now, pyarrow.timestamp("us")),
        ("CLOBVALUE", "CLOB Value", pyarrow.large_string()),
        ("NCLOBVALUE", "NCLOB Value", pyarrow.large_string()),
        ("BLOBVALUE", b"BLOB Value", pyarrow.large_binary()),
    ]
    await async_cursor.execute("delete from TestAllTypes")
    column_names = ",".join(n for n, v, t in data)
    bind_values = ",".join(f":{i + 1}" for i in range(len(data)))
    data_to_insert = tuple(v for n, v, t in data)
    await async_cursor.execute(
        f"""
        insert into TestAllTypes ({column_names})
        values ({bind_values})
        """,
        data_to_insert,
    )
    await async_conn.commit()
    with test_env.defaults_context_manager("fetch_decimals", True):
        sql = f"select {column_names} from TestAllTypes"
        ora_df = await async_conn.fetch_df_all(sql)
        expected_types = [t for n, v, t in data]
        actual_types = [pyarrow.array(a).type for a in ora_df.column_arrays()]
        assert actual_types == expected_types


async def test_dataframe_1126(
    skip_unless_native_boolean_supported, async_cursor
):
    "1126 - test metadata with boolean type"
    await async_cursor.execute("delete from TestBooleans")
    data = [(1, True, False, None), (2, False, True, True)]
    await async_cursor.executemany(
        """
        insert into TestBooleans
        (IntCol, BooleanCol1, BooleanCol2, BooleanCol3)
        values (:1, :2, :3, :4)
        """,
        data,
    )
    await async_cursor.connection.commit()

    sql = "select * from TestBooleans order by IntCol"
    ora_df = await async_cursor.connection.fetch_df_all(sql)
    expected_types = [
        pyarrow.int64(),
        pyarrow.bool_(),
        pyarrow.bool_(),
        pyarrow.bool_(),
    ]
    actual_types = [pyarrow.array(a).type for a in ora_df.column_arrays()]
    assert actual_types == expected_types


async def test_dataframe_1127(async_conn, async_cursor, test_env):
    "1127 - test NULL rows with all null values"
    data = [
        (1, None, None, None, None, None, None, None, None),
        (2, None, None, None, None, None, None, None, None),
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1128(async_conn, async_cursor):
    "1128 - test repeated pyarrow table construction"
    data = [
        (
            1,
            "John",
            "Doe",
            "SF",
            "USA",
            datetime.date(1990, 1, 1),
            5000.50,
            100,
            datetime.datetime.now(),
        )
    ]
    await _populate_table(async_cursor, data)
    ora_df = await async_conn.fetch_df_all(QUERY_SQL)
    table1 = pyarrow.table(ora_df)
    table2 = pyarrow.table(ora_df)
    assert table1.schema == table2.schema
    assert table1.to_pydict() == table2.to_pydict()


async def test_dataframe_1129(async_conn, async_cursor, test_env):
    "1129 - test dataframe query with multiple bind variables"
    await _populate_table(async_cursor, DATASET_2)
    statement = QUERY_SQL_WITH_WHERE_CLAUSE.format(
        where_clause="where Id between :min_id and :max_id"
    )
    ora_df = await async_conn.fetch_df_all(
        statement, {"min_id": 2, "max_id": 3}
    )
    assert ora_df.num_rows() == 2

    expected_data = [row for row in DATASET_2 if row[0] in (2, 3)]
    raw_df = _convert_to_df(expected_data)
    raw_data = test_env.get_data_from_df(raw_df)
    fetched_df = pyarrow.table(ora_df).to_pandas()
    fetched_data = test_env.get_data_from_df(fetched_df)
    assert fetched_data == raw_data


async def test_dataframe_1130(async_conn, test_env):
    "1130 - test error handling with invalid SQL in fetch_df_batches()"
    with test_env.assert_raises_full_code("ORA-00942"):
        async for batch in async_conn.fetch_df_batches(
            "select * from NonExistentTable"
        ):
            pass


async def test_dataframe_1131(async_cursor, test_env):
    "1131 - test partial batch (last batch smaller than batch size)"
    test_data = [
        (
            i,
            f"Name{i}",
            f"Last{i}",
            "City",
            "Country",
            datetime.date(2000, 1, 1),
            i * 100,
            i % 800,
            datetime.datetime.now(),
        )
        for i in range(1, 8)  # 7 rows
    ]
    await _test_df_batches_interop(
        test_env, async_cursor, test_data, batch_size=3, num_batches=3
    )


async def test_dataframe_1132(async_conn, async_cursor):
    "1132 - test with date functions"
    await _populate_table(async_cursor, DATASET_1)
    ora_df = await async_conn.fetch_df_all("""
        select
            Id,
            extract(year from DateOfBirth) as birth_year,
            to_char(DateOfBirth, 'YYYY-MM') as birth_month
        from TestDataFrame
        order by Id
        """)
    assert ora_df.num_rows() == len(DATASET_1)
    year_col = ora_df.get_column_by_name("BIRTH_YEAR")
    array = pyarrow.array(year_col)
    assert array.to_pylist() == [1955, 1955]


async def test_dataframe_1133(async_conn, async_cursor):
    "1133 - test column access by index bounds"
    await _populate_table(async_cursor, DATASET_1)
    ora_df = await async_conn.fetch_df_all(QUERY_SQL)
    with pytest.raises(IndexError):
        ora_df.get_column(ora_df.num_columns())


async def test_dataframe_1134(async_cursor, test_env):
    "1134 - test with different batch sizes"
    await _test_df_batches_interop(
        test_env, async_cursor, DATASET_4, batch_size=1, num_batches=6
    )
    await _test_df_batches_interop(
        test_env, async_cursor, DATASET_4, batch_size=2, num_batches=3
    )


async def test_dataframe_1135(async_cursor, test_env):
    "1135 - test with very large batch size"
    await _test_df_batches_interop(
        test_env, async_cursor, DATASET_1, batch_size=1000, num_batches=1
    )


async def test_dataframe_1136(async_conn, test_env):
    "1136 - test error handling with invalid SQL"
    with test_env.assert_raises_full_code("ORA-00942"):
        await async_conn.fetch_df_all("select * from NonExistentTable")


async def test_dataframe_1137(async_conn, async_cursor, test_env):
    "1137 - test error handling with invalid bind variable"
    await _populate_table(async_cursor, DATASET_1)
    with test_env.assert_raises_full_code("DPY-4010", "ORA-01008"):
        await async_conn.fetch_df_all(
            "select * from TestDataFrame where Id = :missing_bind"
        )


async def test_dataframe_1138(async_conn, async_cursor, test_env):
    "1138 - test with single row result"
    await _populate_table(async_cursor, DATASET_1)
    statement = QUERY_SQL_WITH_WHERE_CLAUSE.format(where_clause="where Id = 1")
    ora_df = await async_conn.fetch_df_all(statement)
    assert ora_df.num_rows() == 1
    _validate_df(ora_df, [DATASET_1[0]], test_env)


async def test_dataframe_1139(async_conn, async_cursor, test_env):
    "1139 - test with calculated columns"
    await _populate_table(async_cursor, DATASET_1)
    now = datetime.datetime.now().replace(microsecond=0)
    ora_df = await async_conn.fetch_df_all(
        """
        select
            Id,
            FirstName || ' ' || LastName as full_name,
            Salary * 12 as annual_salary,
            :now as current_date
        from TestDataFrame
        order by Id
        """,
        [now],
    )
    assert ora_df.num_rows() == len(DATASET_1)
    assert ora_df.num_columns() == 4

    expected_data = []
    for row in DATASET_1:
        expected_row = (
            row[0],  # Id
            f"{row[1]} {row[2]}",  # full_name
            float(str(row[6] * 12)),  # annual_salary
            now,
        )
        expected_data.append(expected_row)
    fetched_df = pyarrow.table(ora_df).to_pandas()
    fetched_data = test_env.get_data_from_df(fetched_df)
    assert fetched_data == expected_data


async def test_dataframe_1140(async_conn, async_cursor, test_env):
    "1140 - test fetch_df_batches with bind variables"
    batch_size = 2
    await _populate_table(async_cursor, DATASET_4)
    where_clause = "where Id >= :min_id"
    sql = QUERY_SQL_WITH_WHERE_CLAUSE.format(where_clause=where_clause)
    expected_data = [row for row in DATASET_4 if row[0] >= 3]
    offset = 0
    async for batch in async_conn.fetch_df_batches(
        sql, {"min_id": 3}, size=batch_size
    ):
        _validate_df(
            batch, expected_data[offset : offset + batch_size], test_env
        )
        offset += batch_size


async def test_dataframe_1141(async_conn, async_cursor, test_env):
    "1141 - test with large data"
    data = [
        (1, "A" * 41_000, b"Very long description " * 5_000),
        (2, "B" * 35_000, b"Another long text " * 10_000),
        (3, "C" * 72_000, b"Even longer content " * 20_000),
    ]

    await async_cursor.execute("delete from TestDataFrame")
    await async_cursor.executemany(
        """
        insert into TestDataFrame
        (Id, LongData, LongRawData)
        values (:1, :2, :3)
        """,
        data,
    )
    await async_conn.commit()

    ora_df = await async_conn.fetch_df_all("""
        select Id, LongData, LongRawData
        from TestDataFrame
        order by Id
        """)
    fetched_df = pyarrow.table(ora_df).to_pandas()
    fetched_data = test_env.get_data_from_df(fetched_df)
    assert fetched_data == data


async def test_dataframe_1142(async_conn, async_cursor):
    "1142 - test fetching from an empty table with fetch_df_batches"
    await async_cursor.execute("delete from TestDataFrame")
    batches = [
        b async for b in async_conn.fetch_df_batches(QUERY_SQL, size=10)
    ]
    assert len(batches) == 1
    assert batches[0].num_rows() == 0


async def test_dataframe_1143(async_conn, async_cursor, test_env):
    "1143 - fetch clob in batches"
    await async_cursor.execute("delete from TestDataFrame")
    test_string = "A" * 10000
    data = [(test_string,)] * 3
    await async_cursor.executemany(
        """
        insert into TestDataFrame (LongData)
        values (:1)
        """,
        data,
    )
    await async_conn.commit()

    offset = 0
    batch_size = 2
    sql = "select LongData from TestDataFrame"
    async for batch in async_conn.fetch_df_batches(sql, size=batch_size):
        fetched_df = pyarrow.table(batch).to_pandas()
        fetched_data = test_env.get_data_from_df(fetched_df)
        assert fetched_data == data[offset : offset + batch_size]
        offset += batch_size


async def test_dataframe_1144(async_conn, async_cursor, test_env):
    "1144 - fetch blob in batches"
    await async_cursor.execute("delete from TestDataFrame")
    test_string = b"B" * 10000
    data = [(test_string,)] * 4
    await async_cursor.executemany(
        """
        insert into TestDataFrame (LongRawData)
        values (:1)
        """,
        data,
    )
    await async_conn.commit()

    offset = 0
    batch_size = 3
    sql = "select LongRawData from TestDataFrame"
    async for batch in async_conn.fetch_df_batches(sql, size=batch_size):
        fetched_df = pyarrow.table(batch).to_pandas()
        fetched_data = test_env.get_data_from_df(fetched_df)
        assert fetched_data == data[offset : offset + batch_size]
        offset += batch_size


async def test_dataframe_1145(async_conn, async_cursor, test_env):
    "1145 - test with empty strings"
    data = [
        (
            1,
            "",
            "",
            "City",
            "Country",
            datetime.datetime(2000, 1, 1),
            1000.0,
            100,
            datetime.datetime.now(),
        ),
        (
            2,
            "First",
            "Last",
            "",
            "",
            datetime.datetime(2000, 1, 1),
            2000.0,
            200,
            datetime.datetime.now(),
        ),
    ]
    await _populate_table(async_cursor, data)
    expected_data = [
        tuple(None if v == "" else v for v in row) for row in data
    ]
    ora_df = await async_conn.fetch_df_all(QUERY_SQL)
    fetched_df = pyarrow.table(ora_df).to_pandas()
    fetched_data = test_env.get_data_from_df(fetched_df)
    assert fetched_data == expected_data


async def test_dataframe_1146(async_cursor, test_env):
    "1146 - test with unicode characters"
    data = [
        (
            1,
            "Jöhn",
            "Döe",
            "München",
            "Deutschland",
            datetime.date(1980, 5, 15),
            5000,
            300,
            datetime.datetime.now(),
        ),
        (
            2,
            "?",
            "?",
            "??",
            "??",
            datetime.date(1990, 8, 20),
            8000,
            400,
            datetime.datetime.now(),
        ),
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1147(async_cursor, test_env):
    "1147 - test with very old dates"
    data = [
        (
            1,
            "Ancient",
            "One",
            "Babylon",
            "Mesopotamia",
            datetime.date(1, 1, 1),
            0,
            0,
            datetime.datetime.now(),
        ),
        (
            2,
            "Medieval",
            "Person",
            "London",
            "England",
            datetime.date(1200, 6, 15),
            10,
            50,
            datetime.datetime.now(),
        ),
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1148(async_cursor, test_env):
    "1148 - test with future dates"
    data = [
        (
            1,
            "Future",
            "Person",
            "Mars",
            "Solar System",
            datetime.date(3000, 1, 1),
            100000,
            900,
            datetime.datetime.now(),
        ),
        (
            2,
            "Distant",
            "Future",
            "Andromeda",
            "Galaxy",
            datetime.date(9999, 12, 31),
            999999,
            999,
            datetime.datetime.now(),
        ),
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1149(async_cursor, test_env):
    "1149 - test with exactly arraysize rows"
    test_date = datetime.date(2000, 1, 1)
    now = datetime.datetime.now()
    data = [
        (
            i,
            f"Name{i}",
            f"Last{i}",
            "City",
            "Country",
            test_date,
            i * 100,
            i % 800,
            now,
        )
        for i in range(1, async_cursor.arraysize + 1)
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1150(async_cursor, test_env):
    "1150 - test with arraysize+1 rows"
    test_date = datetime.date(2000, 1, 1)
    now = datetime.datetime.now()
    data = [
        (
            i,
            f"Name{i}",
            f"Last{i}",
            "City",
            "Country",
            test_date,
            i * 100,
            i % 800,
            now,
        )
        for i in range(1, async_cursor.arraysize + 2)
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1151(async_cursor, test_env):
    "1151 - test with odd arraysize"
    test_date = datetime.date(2000, 1, 1)
    now = datetime.datetime.now()
    data = [
        (
            i,
            f"Name{i}",
            f"Last{i}",
            "City",
            "Country",
            test_date,
            i * 100,
            i % 800,
            now,
        )
        for i in range(1, 48)
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1152(async_cursor, test_env):
    "1152 - test with single row"
    data = [
        (
            1,
            "John",
            "Doe",
            "SF",
            "USA",
            datetime.date(1990, 1, 1),
            5000,
            100,
            datetime.datetime.now(),
        )
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1153(async_cursor, test_env):
    "1153 - test multiple rows with NULL values in different columns"
    now = datetime.datetime.now()
    test_date = datetime.datetime(2000, 1, 1)
    data = [
        (1, None, "Last1", "City1", "Country1", None, None, 100, None),
        (2, "First2", None, None, "Country2", test_date, 2000, None, None),
        (3, "First3", "Last3", None, None, None, 3000, 300, now),
        (4, None, None, None, None, None, None, None, None),
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1154(async_cursor, test_env):
    "1154 - test single column with all NULL values"
    data = [
        (
            1,
            None,
            "Last1",
            "City1",
            "Country1",
            datetime.date(2000, 1, 1),
            1000,
            100,
            datetime.datetime.now(),
        ),
        (
            2,
            None,
            "Last2",
            "City2",
            "Country2",
            datetime.date(2001, 1, 1),
            2000,
            200,
            datetime.datetime.now(),
        ),
        (
            3,
            None,
            "Last3",
            "City3",
            "Country3",
            datetime.date(2002, 1, 1),
            3000,
            300,
            datetime.datetime.now(),
        ),
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1155(async_cursor, test_env):
    "1155 - test last column NULL in each row"
    data = [
        (
            1,
            "First1",
            "Last1",
            "City1",
            "Country1",
            datetime.date(2000, 1, 1),
            1000,
            100,
            None,
        ),
        (
            2,
            "First2",
            "Last2",
            "City2",
            "Country2",
            datetime.date(2001, 1, 1),
            2000,
            200,
            None,
        ),
        (
            3,
            "First3",
            "Last3",
            "City3",
            "Country3",
            datetime.date(2002, 1, 1),
            3000,
            300,
            None,
        ),
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1156(async_cursor, test_env):
    "1156 - test alternating NULL/non-NULL values in a column"
    data = [
        (
            1,
            "First1",
            None,
            "City1",
            None,
            datetime.date(2000, 1, 1),
            None,
            100,
            datetime.datetime.now(),
        ),
        (2, "First2", "Last2", None, "Country2", None, 2000, None, None),
        (
            3,
            "First3",
            None,
            "City3",
            None,
            datetime.date(2002, 1, 1),
            None,
            300,
            datetime.datetime.now(),
        ),
        (4, "First4", "Last4", None, "Country4", None, 4000, None, None),
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1157(async_cursor, test_env):
    "1157 - test all columns NULL except one"
    now = datetime.datetime.now()
    test_date = datetime.date(2001, 1, 1)
    data = [
        (1, None, None, None, None, None, None, None, now),
        (2, None, None, None, None, test_date, None, None, None),
        (3, "First3", None, None, None, None, None, None, None),
        (4, None, None, None, "Country4", None, None, None, None),
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1158(async_cursor, test_env):
    "1158 - test all date columns with all NULL values"
    data = [
        (1, "First1", "Last1", "City1", "Country1", None, 1000, 100, None),
        (2, "First2", "Last2", "City2", "Country2", None, 2000, 200, None),
        (3, "First3", "Last3", "City3", "Country3", None, 3000, 300, None),
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1159(async_cursor, test_env):
    "1159 - test NULL values in numeric columns"
    data = [
        (
            1,
            "First1",
            "Last1",
            "City1",
            "Country1",
            datetime.date(2000, 1, 1),
            None,
            100,
            datetime.datetime.now(),
        ),
        (
            2,
            "First2",
            "Last2",
            "City2",
            "Country2",
            datetime.date(2001, 1, 1),
            2000,
            None,
            datetime.datetime.now(),
        ),
        (
            3,
            "First3",
            "Last3",
            "City3",
            "Country3",
            datetime.date(2002, 1, 1),
            None,
            None,
            datetime.datetime.now(),
        ),
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1160(async_cursor, test_env):
    "1160 - test multiple consecutive NULL rows"
    data = [
        (1, None, None, None, None, None, None, None, None),
        (2, None, None, None, None, None, None, None, None),
        (3, None, None, None, None, None, None, None, None),
        (
            4,
            "First4",
            "Last4",
            "City4",
            "Country4",
            datetime.date(2000, 1, 1),
            4000,
            400,
            datetime.datetime.now(),
        ),
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1161(async_cursor, test_env):
    "1161 - test NULL rows interspersed with data rows"
    data = [
        (1, None, None, None, None, None, None, None, None),
        (
            2,
            "First2",
            "Last2",
            "City2",
            "Country2",
            datetime.date(2001, 1, 1),
            2000,
            200,
            datetime.datetime.now(),
        ),
        (3, None, None, None, None, None, None, None, None),
        (
            4,
            "First4",
            "Last4",
            "City4",
            "Country4",
            datetime.date(2003, 1, 1),
            4000,
            400,
            datetime.datetime.now(),
        ),
        (5, None, None, None, None, None, None, None, None),
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1162(async_cursor, test_env):
    "1162 - test multiple NULL rows with different NULL columns"
    data = [
        (1, None, "Last1", "City1", "Country1", None, 1000, 100, None),
        (
            2,
            "First2",
            None,
            "City2",
            "Country2",
            datetime.date(2001, 1, 1),
            None,
            200,
            None,
        ),
        (
            3,
            None,
            None,
            "City3",
            "Country3",
            None,
            None,
            300,
            datetime.datetime.now(),
        ),
        (
            4,
            "First4",
            "Last4",
            None,
            None,
            datetime.date(2003, 1, 1),
            4000,
            None,
            None,
        ),
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1163(async_cursor, test_env):
    "1163 - test NULL rows with alternating NULL patterns"
    data = [
        (
            1,
            None,
            "Last1",
            None,
            "Country1",
            None,
            1000,
            None,
            datetime.datetime.now(),
        ),
        (
            2,
            "First2",
            None,
            "City2",
            None,
            datetime.date(2001, 1, 1),
            None,
            200,
            None,
        ),
        (
            3,
            None,
            "Last3",
            None,
            "Country3",
            None,
            3000,
            None,
            datetime.datetime.now(),
        ),
        (
            4,
            "First4",
            None,
            "City4",
            None,
            datetime.date(2003, 1, 1),
            None,
            400,
            None,
        ),
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1164(async_cursor, test_env):
    "1164 - test multiple NULL rows with partial NULL groups"
    data = [
        (
            1,
            None,
            None,
            "City1",
            "Country1",
            None,
            None,
            100,
            datetime.datetime.now(),
        ),
        (
            2,
            None,
            None,
            "City2",
            "Country2",
            None,
            None,
            200,
            datetime.datetime.now(),
        ),
        (
            3,
            "First3",
            "Last3",
            None,
            None,
            datetime.date(2002, 1, 1),
            3000,
            None,
            None,
        ),
        (
            4,
            "First4",
            "Last4",
            None,
            None,
            datetime.date(2003, 1, 1),
            4000,
            None,
            None,
        ),
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1165(async_cursor, test_env):
    "1165 - test multiple NULL rows with varying NULL counts"
    data = [
        (1, None, None, None, None, None, None, None, None),
        (2, "First2", None, "City2", None, None, 2000, None, None),
        (
            3,
            None,
            "Last3",
            None,
            "Country3",
            datetime.date(2002, 1, 1),
            None,
            300,
            None,
        ),
        (
            4,
            "First4",
            "Last4",
            "City4",
            "Country4",
            None,
            4000,
            400,
            datetime.datetime.now(),
        ),
    ]
    await _test_df_interop(test_env, async_cursor, data)


async def test_dataframe_1166(async_conn, test_env):
    "1166 - test fetching large integers"
    data = (-(2**40), 2**41)
    ora_df = await async_conn.fetch_df_all(
        """
        select
            cast(:1 as number(15)),
            cast(:2 as number(15))
        from dual
        """,
        data,
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert [data] == test_env.get_data_from_df(fetched_df)


async def test_dataframe_1167(async_conn, test_env):
    "1167 - test fetching NCHAR and NVARCHAR data"
    value = "test_dataframe_1167"
    value_len = len(value)
    ora_df = await async_conn.fetch_df_all(f"""
        select
            cast('{value}' as nchar({value_len})),
            cast('{value}' as nvarchar2({value_len}))
        from dual
        """)
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert test_env.get_data_from_df(fetched_df) == [(value, value)]


async def test_dataframe_1168(async_conn, test_env):
    "1168 - test fetching JSON constrained data via Arrow backed data frame"
    expected_data = [("[1, 2, 3]", "[4, 5, 6]", b"[7, 8, 9]")]
    ora_df = await async_conn.fetch_df_all("""
        select
            JsonVarchar,
            JsonClob,
            JsonBlob
        from TestJsonCols
        where IntCol = 1""")
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert test_env.get_data_from_df(fetched_df) == expected_data


async def test_dataframe_1169(test_env, async_conn, async_cursor):
    "1169 - test fetching interval types"
    await async_cursor.execute("delete from TestAllTypes")
    data = [
        (
            1,
            datetime.timedelta(
                days=2, hours=3, minutes=48, seconds=12, microseconds=25
            ),
            oracledb.IntervalYM(years=3, months=4),
        ),
        (
            2,
            datetime.timedelta(
                days=-3, hours=-8, minutes=-3, seconds=-5, microseconds=-2500
            ),
            oracledb.IntervalYM(years=-8, months=-2),
        ),
    ]
    await async_cursor.executemany(
        """
        insert into TestAllTypes (
            NumberValue, IntervalDSValue, IntervalYMValue
        ) values (
            :1, :2, :3
        )""",
        data,
    )
    await async_conn.commit()
    ora_df = await async_conn.fetch_df_all("""
        select NumberValue, IntervalDSValue, IntervalYMValue
        from TestAllTypes
        order by NumberValue""")
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert test_env.get_data_from_df(fetched_df) == data


async def test_dataframe_1170(test_env, async_conn):
    "1170 - test fetching data that is null by describe"
    data = [(None, None), (None, None), (None, None)]
    ora_df = await async_conn.fetch_df_all(
        "select null as c1, null as c2 from dual connect by level <= 3"
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert test_env.get_data_from_df(fetched_df) == data


async def test_dataframe_1171(async_conn, async_cursor):
    "1171 - test executemany() with decimal256 data frame"
    expected_values = [
        decimal.Decimal("9007199254740993"),
        decimal.Decimal("22222222222222222222222222222222222222"),
        decimal.Decimal("88888888888888888888.888888888888888888"),
        decimal.Decimal("-0.0000000000000000000000000000000000001"),
        decimal.Decimal("0.99999999999999999999999999999999999999"),
        decimal.Decimal("1.9876543210987654321098765432109876543"),
        decimal.Decimal("9876543210987654321098765432109876543.7"),
    ]
    dtype = pyarrow.decimal256(precision=76, scale=38)
    df = pyarrow.table(
        [
            pyarrow.array(range(1, len(expected_values) + 1), pyarrow.int64()),
            pyarrow.array(expected_values, dtype),
        ],
        names=["INTCOL", "NUMBERCOL"],
    )
    await async_cursor.execute("delete from TestDataFrame")
    await async_cursor.executemany(
        """
        insert into TestDataFrame (Id, UnconstrainedNumberData)
        values (:1, :2)
        """,
        df,
    )
    await async_conn.commit()
    requested_schema = pyarrow.schema([("NUMBERCOL", dtype)])
    ora_df = await async_conn.fetch_df_all(
        """
        select UnconstrainedNumberData
        from TestDataFrame
        order by Id
        """,
        requested_schema=requested_schema,
    )
    fetched_table = pyarrow.table(ora_df)
    assert fetched_table.field("NUMBERCOL").type == dtype
    assert [v.as_py() for v in fetched_table["NUMBERCOL"]] == expected_values
