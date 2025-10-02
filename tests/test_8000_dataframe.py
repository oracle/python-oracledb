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
Module for testing dataframes
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


def _populate_table(cursor, data):
    """
    Populate the test table with the given data.
    """
    cursor.execute("delete from TestDataframe")
    types = [None] * len(data[0])
    types[8] = oracledb.DB_TYPE_TIMESTAMP
    cursor.setinputsizes(*types)
    cursor.executemany(
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
    cursor.connection.commit()


def _test_df_interop(test_env, cursor, data):
    """
    Tests interoperability with external data frames using the data set
    provided.
    """
    _populate_table(cursor, data)
    ora_df = cursor.connection.fetch_df_all(QUERY_SQL)
    _validate_df(ora_df, data, test_env)


def _test_df_batches_interop(test_env, cursor, data, batch_size, num_batches):
    """
    Tests interoperability with external data frames using the data set
    provided.
    """
    _populate_table(cursor, data)
    conn = cursor.connection
    batches = list(conn.fetch_df_batches(QUERY_SQL, size=batch_size))
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


def test_8000(conn, cursor):
    "8000 - test basic fetch of data frame"
    _populate_table(cursor, DATASET_1)
    ora_df = conn.fetch_df_all(QUERY_SQL)
    assert ora_df.num_rows() == len(DATASET_1)
    assert ora_df.num_columns() == len(DATASET_1[0])


def test_8001(cursor, test_env):
    "8001 - test conversion to external dataframe"
    _test_df_interop(test_env, cursor, DATASET_1)


def test_8002(cursor, test_env):
    "8001 - test null and negative values"
    _test_df_interop(test_env, cursor, DATASET_2)


def test_8003(cursor, test_env):
    "8002 - test with fetch_decimals"
    with test_env.defaults_context_manager("fetch_decimals", True):
        _test_df_interop(test_env, cursor, DATASET_1)


def test_8004(cursor, test_env):
    "8003 - test null and negative values with fetch_decimals"
    with test_env.defaults_context_manager("fetch_decimals", True):
        _test_df_interop(test_env, cursor, DATASET_2)


def test_8005(cursor, test_env):
    "8005 - test null and values with leading zeros"
    _test_df_interop(test_env, cursor, DATASET_3)


def test_8006(cursor, test_env):
    "8005 - test null and values with leading zeros with fetch_decimals"
    with test_env.defaults_context_manager("fetch_decimals", True):
        _test_df_interop(test_env, cursor, DATASET_3)


def test_8007(cursor, test_env):
    "8007 - duplicate values in the rows"
    _test_df_interop(test_env, cursor, DATASET_4)


def test_8008(cursor, test_env):
    "8008 - batches without specification of size"
    _test_df_batches_interop(
        test_env, cursor, DATASET_4, batch_size=None, num_batches=1
    )


def test_8009(cursor, test_env):
    "8009 - batches with specification of size"
    _test_df_batches_interop(
        test_env, cursor, DATASET_4, batch_size=5, num_batches=2
    )


def test_8010(conn, cursor, test_env):
    "8010 - verify passing Arrow arrays twice works"
    _populate_table(cursor, DATASET_1)
    ora_df = conn.fetch_df_all(QUERY_SQL)
    _validate_df(ora_df, DATASET_1, test_env)
    _validate_df(ora_df, DATASET_1, test_env)


def test_8011(conn, cursor):
    "8011 - verify empty data set"
    _populate_table(cursor, DATASET_1)
    statement = "select * from TestDataFrame where Id = 4"
    ora_df = conn.fetch_df_all(statement)
    assert ora_df.num_rows() == 0


def test_8012(conn, cursor):
    "8012 - verify empty data set with batches"
    _populate_table(cursor, DATASET_1)
    statement = "select * from TestDataFrame where Id = 4"
    for ora_df in conn.fetch_df_batches(statement):
        assert ora_df.num_rows() == 0


def test_8013(conn, cursor):
    "8013 - negative checks on attributes"
    _populate_table(cursor, DATASET_1)
    ora_df = conn.fetch_df_all(QUERY_SQL)
    with pytest.raises(IndexError):
        ora_df.get_column(121)
    with pytest.raises(IndexError):
        ora_df.get_column(-1)
    with pytest.raises(KeyError):
        ora_df.get_column_by_name("missing_column")


def test_8014(conn, test_env):
    "8014 - check unsupported error"
    statement = "select cursor(select user from dual) from dual"
    with test_env.assert_raises_full_code("DPY-3030"):
        conn.fetch_df_all(statement)


def test_8015(cursor, test_env):
    "8015 - batches with specification of size matching number of rows"
    _test_df_batches_interop(
        test_env, cursor, DATASET_2, batch_size=len(DATASET_2), num_batches=1
    )


def test_8016(conn, cursor):
    "8016 - verify get_column() returns the correct value"
    _populate_table(cursor, DATASET_1)
    ora_df = conn.fetch_df_all(QUERY_SQL)
    array = pyarrow.array(ora_df.get_column(1))
    assert array.to_pylist() == ["John", "Big"]


def test_8017(cursor, test_env):
    "8017 - batches with size that has duplicate rows across batches"
    _test_df_batches_interop(
        test_env, cursor, DATASET_4, batch_size=3, num_batches=2
    )


def test_8018(conn, test_env):
    "8018 - fetch_decimals without precision and scale specified"
    data = [(1.0,)]
    with test_env.defaults_context_manager("fetch_decimals", True):
        ora_df = conn.fetch_df_all("select 1.0 from dual")
        fetched_tab = pyarrow.Table.from_arrays(
            ora_df.column_arrays(), names=ora_df.column_names()
        )
        fetched_df = fetched_tab.to_pandas()
        fetched_data = test_env.get_data_from_df(fetched_df)
        assert fetched_data == data


def test_8019(conn, test_env):
    "8019 - fetch clob"
    data = [("test_8023",)]
    ora_df = conn.fetch_df_all("select to_clob('test_8023') from dual")
    fetched_df = pyarrow.table(ora_df).to_pandas()
    fetched_data = test_env.get_data_from_df(fetched_df)
    assert fetched_data == data


def test_8020(conn, test_env):
    "8020 - fetch blob"
    data = [(b"test_8024",)]
    ora_df = conn.fetch_df_all(
        "select to_blob(utl_raw.cast_to_raw('test_8024')) from dual"
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    fetched_data = test_env.get_data_from_df(fetched_df)
    assert fetched_data == data


def test_8021(conn, test_env):
    "8021 - fetch raw"
    data = [(b"test_8025",)]
    ora_df = conn.fetch_df_all(
        "select utl_raw.cast_to_raw('test_8025') from dual"
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    fetched_data = test_env.get_data_from_df(fetched_df)
    assert fetched_data == data


def test_8022(skip_unless_native_boolean_supported, conn, test_env):
    "8022 - fetch boolean"
    data = [(True,), (False,), (False,), (True,), (True,)]
    ora_df = conn.fetch_df_all(
        """
        select true
        union all
        select false
        union all
        select false
        union all
        select true
        union all
        select true
        """
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    fetched_data = test_env.get_data_from_df(fetched_df)
    assert fetched_data == data


def test_8023(conn, test_env):
    "8023 - fetch data with multiple rows containing null values"
    ora_df = conn.fetch_df_all(
        """
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
        """
    )
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


def test_8024(skip_unless_vectors_supported, conn, test_env):
    "8024 - fetch float32 vector"

    # float32 is a special case while comparing dataframe values
    # Converting Dataframe cell value of type numpy.ndarray[float32]
    # using .tolist() converts each value to Python float. Python
    # float uses 64-bit precision causing mismatches in assertEqual.
    # As a workaround we use array.array('f', src).tolist() on the
    # source data
    data = [
        (array.array("f", [34.6, 77.8]).tolist(),),
        (array.array("f", [34.6, 77.8, 55.9]).tolist(),),
    ]
    ora_df = conn.fetch_df_all(
        """
        SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT32)
        union all
        SELECT TO_VECTOR('[34.6, 77.8, 55.9]', 3, FLOAT32)
        """
    )
    assert ora_df.num_rows() == 2
    assert ora_df.num_columns() == 1
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


def test_8025(skip_unless_vectors_supported, conn, test_env):
    "8025 - fetch float64 vector"
    data = [
        ([34.6, 77.8],),
        ([34.6, 77.8, 55.9],),
    ]
    ora_df = conn.fetch_df_all(
        """
        SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT64)
        union all
        SELECT TO_VECTOR('[34.6, 77.8, 55.9]', 3, FLOAT64)
        """
    )
    assert ora_df.num_rows() == 2
    assert ora_df.num_columns() == 1
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


def test_8026(skip_unless_vectors_supported, conn, test_env):
    "8026 - fetch int8 vector"
    data = [
        ([34, -77],),
        ([34, 77, 55],),
    ]
    ora_df = conn.fetch_df_all(
        """
        SELECT TO_VECTOR('[34, -77]', 2, INT8)
        union all
        SELECT TO_VECTOR('[34, 77, 55]', 3, INT8)
        """
    )
    assert ora_df.num_rows() == 2
    assert ora_df.num_columns() == 1
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


def test_8027(skip_unless_vectors_supported, conn, test_env):
    "8027 - fetch binary vector"
    data = [
        ([3, 2, 3],),
        ([3, 2],),
    ]
    ora_df = conn.fetch_df_all(
        """
        SELECT TO_VECTOR('[3, 2, 3]', 24, BINARY)
        union all
        SELECT TO_VECTOR('[3, 2]', 16, BINARY)
        """
    )
    assert ora_df.num_rows() == 2
    assert ora_df.num_columns() == 1
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


def test_8028(skip_unless_vectors_supported, conn, test_env):
    "8028 - fetch float32 vectors with None"
    data = [
        (array.array("f", [34.6, 77.8]).tolist(),),
        (array.array("f", [34.6, 77.8, 55.9]).tolist(),),
        (None,),
    ]
    ora_df = conn.fetch_df_all(
        """
        SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT32)
        union all
        SELECT TO_VECTOR('[34.6, 77.8, 55.9]', 3, FLOAT32)
        union all
        select NULL
        """
    )
    assert ora_df.num_rows() == 3
    assert ora_df.num_columns() == 1
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


def test_8029(skip_unless_vectors_supported, conn, test_env):
    "8029 - fetch duplicate float64 vectors"
    data = [
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
        ([34.6, 77.8],),
    ]
    ora_df = conn.fetch_df_all(
        """
        SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT64)
        union all
        SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT64)
        union all
        SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT64)
        union all
        SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT64)
        union all
        SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT64)
        union all
        SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT64)
        union all
        SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT64)
        union all
        SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT64)
        union all
        SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT64)
        union all
        SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT64)
        union all
        SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT64)
        union all
        SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT64)
        """
    )
    assert ora_df.num_rows() == 12
    assert ora_df.num_columns() == 1
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


def test_8030(skip_unless_sparse_vectors_supported, conn, test_env):
    "8030 - fetch float32 sparse vectors"
    data = [
        (
            {
                "num_dimensions": 8,
                "indices": [0, 7],
                "values": array.array("f", [34.6, 77.8]).tolist(),
            },
        ),
        (
            {
                "num_dimensions": 8,
                "indices": [0, 7],
                "values": array.array("f", [34.6, 9.1]).tolist(),
            },
        ),
    ]
    ora_df = conn.fetch_df_all(
        """
        SELECT TO_VECTOR(
            TO_VECTOR('[34.6, 0, 0, 0, 0, 0, 0, 77.8]', 8, FLOAT32),
            8,
            FLOAT32,
            SPARSE
            )
        union all
        SELECT TO_VECTOR(
            TO_VECTOR('[34.6, 0, 0, 0, 0, 0, 0, 9.1]', 8, FLOAT32),
            8,
            FLOAT32,
            SPARSE
            )
        """
    )
    assert ora_df.num_rows() == 2
    assert ora_df.num_columns() == 1
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


def test_8031(skip_unless_sparse_vectors_supported, conn, test_env):
    "8031 - fetch float64 sparse vectors"
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
    ora_df = conn.fetch_df_all(
        """
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
        """
    )
    assert ora_df.num_rows() == 2
    assert ora_df.num_columns() == 1
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


def test_8032(skip_unless_vectors_supported, conn, test_env):
    "8032 - DPY-3031 - Unsupported flexible vector formats"
    with test_env.assert_raises_full_code("DPY-3031"):
        conn.fetch_df_all(
            """
            SELECT TO_VECTOR('[44, 55, 89]', 3, INT8) as flex_col
            union all
            SELECT TO_VECTOR('[34.6, 77.8, 55.9]', 3, FLOAT32) as flex_col
            """
        )


def test_8033(skip_unless_sparse_vectors_supported, conn, test_env):
    "8033 - DPY-4007 -fetch sparse vectors with flexible dimensions"
    with test_env.assert_raises_full_code("DPY-2065"):
        conn.fetch_df_all(
            """
            SELECT TO_VECTOR(
                TO_VECTOR('[34.6, 0, 0, 0, 0, 0, 77.8]', 7, FLOAT64),
                7,
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
            """
        )


def test_8034(conn, cursor, test_env):
    "8034 - test expressions on numeric columns"
    # fill only the numeric column - credit score
    dataset = [
        (1, None, None, None, None, None, None, 225, None),
        (2, None, None, None, None, None, None, 365, None),
    ]

    data = [
        (56.25,),
        (91.25,),
    ]
    _populate_table(cursor, dataset)

    # Use numeric expression involving a column
    statement = "select CreditScore/4 from TestDataFrame order by Id"
    ora_df = conn.fetch_df_all(statement)
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert data == test_env.get_data_from_df(fetched_df)


def test_8035(conn, cursor):
    "8035 - test metadata of all data types"
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
    cursor.execute("delete from TestAllTypes")
    column_names = ",".join(n for n, v, t in data)
    bind_values = ",".join(f":{i + 1}" for i in range(len(data)))
    data_to_insert = tuple(v for n, v, t in data)
    cursor.execute(
        f"""
        insert into TestAllTypes ({column_names})
        values ({bind_values})
        """,
        data_to_insert,
    )
    conn.commit()
    sql = f"select {column_names} from TestAllTypes"
    ora_df = conn.fetch_df_all(sql)
    expected_types = [t for n, v, t in data]
    actual_types = [pyarrow.array(a).type for a in ora_df.column_arrays()]
    assert actual_types == expected_types


def test_8036(conn, cursor, test_env):
    "8036 - test metadata of all data types with fetch_decimals = True"
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
    cursor.execute("delete from TestAllTypes")
    column_names = ",".join(n for n, v, t in data)
    bind_values = ",".join(f":{i + 1}" for i in range(len(data)))
    data_to_insert = tuple(v for n, v, t in data)
    cursor.execute(
        f"""
        insert into TestAllTypes ({column_names})
        values ({bind_values})
        """,
        data_to_insert,
    )
    conn.commit()
    with test_env.defaults_context_manager("fetch_decimals", True):
        sql = f"select {column_names} from TestAllTypes"
        ora_df = conn.fetch_df_all(sql)
        expected_types = [t for n, v, t in data]
        actual_types = [pyarrow.array(a).type for a in ora_df.column_arrays()]
        assert actual_types == expected_types


def test_8037(skip_unless_native_boolean_supported, conn, cursor):
    "8037 - test metadata with boolean type"
    cursor.execute("delete from TestBooleans")
    data = [(1, True, False, None), (2, False, True, True)]
    cursor.executemany(
        """
        insert into TestBooleans
        (IntCol, BooleanCol1, BooleanCol2, BooleanCol3)
        values (:1, :2, :3, :4)
        """,
        data,
    )
    conn.commit()

    sql = "select * from TestBooleans order by IntCol"
    ora_df = conn.fetch_df_all(sql)
    expected_types = [
        pyarrow.int64(),
        pyarrow.bool_(),
        pyarrow.bool_(),
        pyarrow.bool_(),
    ]
    actual_types = [pyarrow.array(a).type for a in ora_df.column_arrays()]
    assert actual_types == expected_types


def test_8038(cursor, test_env):
    "8038 - test NULL rows with all null values"
    data = [
        (1, None, None, None, None, None, None, None, None),
        (2, None, None, None, None, None, None, None, None),
    ]
    _test_df_interop(test_env, cursor, data)


def test_8039(conn, cursor):
    "8039 - test repeated pyarrow table construction"
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
    _populate_table(cursor, data)
    ora_df = conn.fetch_df_all(QUERY_SQL)
    table1 = pyarrow.table(ora_df)
    table2 = pyarrow.table(ora_df)
    assert table1.schema == table2.schema
    assert table1.to_pydict() == table2.to_pydict()


def test_8040(conn, cursor, test_env):
    "8040 - test dataframe query with multiple bind variables"
    _populate_table(cursor, DATASET_2)
    statement = QUERY_SQL_WITH_WHERE_CLAUSE.format(
        where_clause="where Id between :min_id and :max_id"
    )
    ora_df = conn.fetch_df_all(statement, {"min_id": 2, "max_id": 3})
    assert ora_df.num_rows() == 2

    expected_data = [row for row in DATASET_2 if row[0] in (2, 3)]
    raw_df = _convert_to_df(expected_data)
    raw_data = test_env.get_data_from_df(raw_df)
    fetched_df = pyarrow.table(ora_df).to_pandas()
    fetched_data = test_env.get_data_from_df(fetched_df)
    assert fetched_data == raw_data


def test_8041(conn, test_env):
    "8041 - test error handling with invalid SQL in fetch_df_batches()"
    with test_env.assert_raises_full_code("ORA-00942"):
        for batch in conn.fetch_df_batches("select * from NonExistentTable"):
            pass


def test_8042(cursor, test_env):
    "8042 - test partial batch (last batch smaller than batch size)"
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
    _test_df_batches_interop(
        test_env, cursor, test_data, batch_size=3, num_batches=3
    )


def test_8043(conn, cursor):
    "8043 - test with date functions"
    _populate_table(cursor, DATASET_1)
    ora_df = conn.fetch_df_all(
        """
        select
            Id,
            extract(year from DateOfBirth) as birth_year,
            to_char(DateOfBirth, 'YYYY-MM') as birth_month
        from TestDataFrame
        order by Id
        """
    )
    assert ora_df.num_rows() == len(DATASET_1)
    year_col = ora_df.get_column_by_name("BIRTH_YEAR")
    array = pyarrow.array(year_col)
    assert array.to_pylist() == [1955, 1955]


def test_8044(conn, cursor):
    "8044 - test column access by index bounds"
    _populate_table(cursor, DATASET_1)
    ora_df = conn.fetch_df_all(QUERY_SQL)
    with pytest.raises(IndexError):
        ora_df.get_column(ora_df.num_columns())


def test_8045(cursor, test_env):
    "8045 - test with different batch sizes"
    _test_df_batches_interop(
        test_env, cursor, DATASET_4, batch_size=1, num_batches=6
    )
    _test_df_batches_interop(
        test_env, cursor, DATASET_4, batch_size=2, num_batches=3
    )


def test_8046(cursor, test_env):
    "8046 - test with very large batch size"
    _test_df_batches_interop(
        test_env, cursor, DATASET_1, batch_size=1000, num_batches=1
    )


def test_8047(conn, test_env):
    "8047 - test error handling with invalid SQL"
    with test_env.assert_raises_full_code("ORA-00942"):
        conn.fetch_df_all("select * from NonExistentTable")


def test_8048(conn, cursor, test_env):
    "8048 - test error handling with invalid bind variable"
    _populate_table(cursor, DATASET_1)
    with test_env.assert_raises_full_code("DPY-4010", "ORA-01008"):
        conn.fetch_df_all(
            "select * from TestDataFrame where Id = :missing_bind"
        )


def test_8049(conn, cursor, test_env):
    "8049 - test with single row result"
    _populate_table(cursor, DATASET_1)
    statement = QUERY_SQL_WITH_WHERE_CLAUSE.format(where_clause="where Id = 1")
    ora_df = conn.fetch_df_all(statement)
    assert ora_df.num_rows() == 1
    _validate_df(ora_df, [DATASET_1[0]], test_env)


def test_8050(conn, cursor, test_env):
    "8050 - test with calculated columns"
    _populate_table(cursor, DATASET_1)
    now = datetime.datetime.now().replace(microsecond=0)
    ora_df = conn.fetch_df_all(
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


def test_8051(conn, cursor, test_env):
    "8051 - test fetch_df_batches with bind variables"
    batch_size = 2
    _populate_table(cursor, DATASET_4)
    where_clause = "where Id >= :min_id"
    sql = QUERY_SQL_WITH_WHERE_CLAUSE.format(where_clause=where_clause)
    batches = conn.fetch_df_batches(sql, {"min_id": 3}, size=batch_size)
    expected_data = [row for row in DATASET_4 if row[0] >= 3]
    offset = 0
    for batch in batches:
        _validate_df(
            batch, expected_data[offset : offset + batch_size], test_env
        )
        offset += batch_size


def test_8052(conn, cursor, test_env):
    "8052 - test with large data"
    data = [
        (1, "A" * 41_000, b"Very long description " * 5_000),
        (2, "B" * 35_000, b"Another long text " * 10_000),
        (3, "C" * 72_000, b"Even longer content " * 20_000),
    ]

    cursor.execute("delete from TestDataFrame")
    cursor.executemany(
        """
        insert into TestDataFrame
        (Id, LongData, LongRawData)
        values (:1, :2, :3)
        """,
        data,
    )
    conn.commit()

    ora_df = conn.fetch_df_all(
        """
        select Id, LongData, LongRawData
        from TestDataFrame
        order by Id
        """
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    fetched_data = test_env.get_data_from_df(fetched_df)
    assert fetched_data == data


def test_8053(conn, cursor):
    "8053 - test fetching from an empty table with fetch_df_batches"
    cursor.execute("delete from TestDataFrame")
    batches = list(conn.fetch_df_batches(QUERY_SQL, size=10))
    assert len(batches) == 1
    assert batches[0].num_rows() == 0


def test_8054(conn, cursor, test_env):
    "8054 - fetch clob in batches"
    cursor.execute("delete from TestDataFrame")
    test_string = "A" * 10000
    data = [(test_string,)] * 3
    cursor.executemany(
        """
        insert into TestDataFrame (LongData)
        values (:1)
        """,
        data,
    )
    conn.commit()

    offset = 0
    batch_size = 2
    sql = "select LongData from TestDataFrame"
    for batch in conn.fetch_df_batches(sql, size=batch_size):
        fetched_df = pyarrow.table(batch).to_pandas()
        fetched_data = test_env.get_data_from_df(fetched_df)
        assert fetched_data == data[offset : offset + batch_size]
        offset += batch_size


def test_8055(conn, cursor, test_env):
    "8055 - fetch blob in batches"
    cursor.execute("delete from TestDataFrame")
    test_string = b"B" * 10000
    data = [(test_string,)] * 4
    cursor.executemany(
        """
        insert into TestDataFrame (LongRawData)
        values (:1)
        """,
        data,
    )
    conn.commit()

    offset = 0
    batch_size = 3
    sql = "select LongRawData from TestDataFrame"
    for batch in conn.fetch_df_batches(sql, size=batch_size):
        fetched_df = pyarrow.table(batch).to_pandas()
        fetched_data = test_env.get_data_from_df(fetched_df)
        assert fetched_data == data[offset : offset + batch_size]
        offset += batch_size


def test_8056(conn, cursor, test_env):
    "8056 - test with empty strings"
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
    _populate_table(cursor, data)
    expected_data = [
        tuple(None if v == "" else v for v in row) for row in data
    ]
    ora_df = conn.fetch_df_all(QUERY_SQL)
    fetched_df = pyarrow.table(ora_df).to_pandas()
    fetched_data = test_env.get_data_from_df(fetched_df)
    assert fetched_data == expected_data


def test_8057(cursor, test_env):
    "8057 - test with unicode characters"
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
    _test_df_interop(test_env, cursor, data)


def test_8058(cursor, test_env):
    "8072 - test with very old dates"
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
    _test_df_interop(test_env, cursor, data)


def test_8059(cursor, test_env):
    "8059 - test with future dates"
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
    _test_df_interop(test_env, cursor, data)


def test_8060(cursor, test_env):
    "8060 - test with exactly arraysize rows"
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
        for i in range(1, cursor.arraysize + 1)
    ]
    _test_df_interop(test_env, cursor, data)


def test_8061(cursor, test_env):
    "8061 - test with arraysize+1 rows"
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
        for i in range(1, cursor.arraysize + 2)
    ]
    _test_df_interop(test_env, cursor, data)


def test_8062(cursor, test_env):
    "8062 - test with odd arraysize"
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
    _test_df_interop(test_env, cursor, data)


def test_8063(cursor, test_env):
    "8063 - test with single row"
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
    _test_df_interop(test_env, cursor, data)


def test_8064(cursor, test_env):
    "8064 - test multiple rows with NULL values in different columns"
    now = datetime.datetime.now()
    test_date = datetime.datetime(2000, 1, 1)
    data = [
        (1, None, "Last1", "City1", "Country1", None, None, 100, None),
        (2, "First2", None, None, "Country2", test_date, 2000, None, None),
        (3, "First3", "Last3", None, None, None, 3000, 300, now),
        (4, None, None, None, None, None, None, None, None),
    ]
    _test_df_interop(test_env, cursor, data)


def test_8065(cursor, test_env):
    "8065 - test single column with all NULL values"
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
    _test_df_interop(test_env, cursor, data)


def test_8066(cursor, test_env):
    "8066 - test last column NULL in each row"
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
    _test_df_interop(test_env, cursor, data)


def test_8067(cursor, test_env):
    "8067 - test alternating NULL/non-NULL values in a column"
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
    _test_df_interop(test_env, cursor, data)


def test_8068(cursor, test_env):
    "8068 - test all columns NULL except one"
    now = datetime.datetime.now()
    test_date = datetime.date(2001, 1, 1)
    data = [
        (1, None, None, None, None, None, None, None, now),
        (2, None, None, None, None, test_date, None, None, None),
        (3, "First3", None, None, None, None, None, None, None),
        (4, None, None, None, "Country4", None, None, None, None),
    ]
    _test_df_interop(test_env, cursor, data)


def test_8069(cursor, test_env):
    "8069 - test all date columns with all NULL values"
    data = [
        (1, "First1", "Last1", "City1", "Country1", None, 1000, 100, None),
        (2, "First2", "Last2", "City2", "Country2", None, 2000, 200, None),
        (3, "First3", "Last3", "City3", "Country3", None, 3000, 300, None),
    ]
    _test_df_interop(test_env, cursor, data)


def test_8070(cursor, test_env):
    "8070 - test NULL values in numeric columns"
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
    _test_df_interop(test_env, cursor, data)


def test_8071(cursor, test_env):
    "8071 - test multiple consecutive NULL rows"
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
    _test_df_interop(test_env, cursor, data)


def test_8072(cursor, test_env):
    "8072 - test NULL rows interspersed with data rows"
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
    _test_df_interop(test_env, cursor, data)


def test_8073(cursor, test_env):
    "8073 - test multiple NULL rows with different NULL columns"
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
    _test_df_interop(test_env, cursor, data)


def test_8074(cursor, test_env):
    "8074 - test NULL rows with alternating NULL patterns"
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
    _test_df_interop(test_env, cursor, data)


def test_8075(cursor, test_env):
    "8075 - test multiple NULL rows with partial NULL groups"
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
    _test_df_interop(test_env, cursor, data)


def test_8076(cursor, test_env):
    "8076 - test multiple NULL rows with varying NULL counts"
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
    _test_df_interop(test_env, cursor, data)


def test_8077(conn, test_env):
    "8077 - test fetching large integers"
    data = (-(2**40), 2**41)
    ora_df = conn.fetch_df_all(
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


def test_8078(conn, test_env):
    "8078 - test fetching NCHAR and NVARCHAR data"
    value = "test_8078"
    value_len = len(value)
    ora_df = conn.fetch_df_all(
        f"""
        select
            cast('{value}' as nchar({value_len})),
            cast('{value}' as nvarchar2({value_len}))
        from dual
        """
    )
    fetched_df = pyarrow.table(ora_df).to_pandas()
    assert test_env.get_data_from_df(fetched_df) == [(value, value)]
