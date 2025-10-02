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
Module for testing DataFrame ingestion
"""

import datetime
import decimal

import pyarrow
import pytest

SPARSE_VECTOR_FIELDS_FLOAT32 = [
    ("num_dimensions", pyarrow.int64()),
    ("indices", pyarrow.list_(pyarrow.uint32())),
    ("values", pyarrow.list_(pyarrow.float32())),
]

SPARSE_VECTOR_FIELDS_FLOAT64 = [
    ("num_dimensions", pyarrow.int64()),
    ("indices", pyarrow.list_(pyarrow.uint32())),
    ("values", pyarrow.list_(pyarrow.float64())),
]

SPARSE_VECTOR_FIELDS_INT8 = [
    ("num_dimensions", pyarrow.int64()),
    ("indices", pyarrow.list_(pyarrow.uint32())),
    ("values", pyarrow.list_(pyarrow.int8())),
]


@pytest.fixture
def empty_tab(cursor):
    cursor.execute("delete from TestDataFrame")


def test_8900(conn, cursor, empty_tab):
    "8900 - test basic ingestion of data frame"
    arrays = [
        pyarrow.array([1, 2, 3], pyarrow.int64()),
        pyarrow.array(["John", "Jane", "Bob"], pyarrow.large_string()),
        pyarrow.array([1000.50, 2000.75, 3000.25], pyarrow.float64()),
        pyarrow.array(
            [
                datetime.datetime(2020, 1, 1),
                datetime.datetime(2021, 2, 2),
                datetime.datetime(2022, 3, 3),
            ],
            pyarrow.timestamp("s"),
        ),
    ]
    names = ["Id", "FirstName", "Salary", "DateOfBirth"]
    df = pyarrow.table(arrays, names)
    cursor.executemany(
        """
        insert into TestDataFrame
        (Id, FirstName, Salary, DateOfBirth)
        values (:1, :2, :3, :4)
        """,
        df,
    )
    conn.commit()
    odf = conn.fetch_df_all(
        """
        select
            Id as "Id",
            FirstName as "FirstName",
            Salary as "Salary",
            DateOfBirth as "DateOfBirth"
        from TestDataFrame
        order by Id
        """
    )
    fetched_df = pyarrow.table(odf)
    assert fetched_df.equals(df)


def test_8901(conn, cursor, empty_tab):
    "8901 - test ingestion with null values"
    arrays = [
        pyarrow.array([1, 2, 3], pyarrow.int64()),
        pyarrow.array(["John", None, "Bob"], pyarrow.large_string()),
        pyarrow.array([None, 2000.75, 3000.25], pyarrow.float64()),
        pyarrow.array(
            [
                datetime.datetime(2020, 1, 1),
                None,
                datetime.datetime(2022, 3, 3),
            ],
            pyarrow.timestamp("s"),
        ),
    ]
    names = ["Id", "FirstName", "Salary", "DateOfBirth"]
    df = pyarrow.table(arrays, names)
    cursor.executemany(
        """
        insert into TestDataFrame
        (Id, FirstName, Salary, DateOfBirth)
        values (:1, :2, :3, :4)
        """,
        df,
    )
    conn.commit()
    odf = conn.fetch_df_all(
        """
        select
            Id as "Id",
            FirstName as "FirstName",
            Salary as "Salary",
            DateOfBirth as "DateOfBirth"
        from TestDataFrame
        order by Id
        """
    )
    fetched_df = pyarrow.table(odf)
    assert fetched_df.equals(df)


def test_8902(conn, cursor, empty_tab):
    "8902 - test ingestion with single column"
    arrays = [pyarrow.array([1, 2, 3], pyarrow.int64())]
    names = ["Id"]
    df = pyarrow.table(arrays, names)
    cursor.executemany("insert into TestDataFrame (Id) values (:1)", df)
    conn.commit()
    odf = conn.fetch_df_all(
        """
        select Id as "Id"
        from TestDataFrame
        order by Id
        """
    )
    fetched_df = pyarrow.table(odf)
    assert fetched_df.equals(df)


def test_8903(conn, cursor, empty_tab):
    "8903 - test ingestion with large data types"
    long_str = "X" * 32_768
    long_raw = b"Y" * 32_768
    arrays = [
        pyarrow.array([1], pyarrow.int64()),
        pyarrow.array([long_str], pyarrow.large_string()),
        pyarrow.array([long_raw], pyarrow.large_binary()),
    ]
    names = ["Id", "LongData", "LongRawData"]
    df = pyarrow.table(arrays, names)
    cursor.executemany(
        """
        insert into TestDataFrame (Id, LongData, LongRawData)
        values (:1, :2, :3)
        """,
        df,
    )
    conn.commit()
    odf = conn.fetch_df_all(
        """
        select
            Id as "Id",
            LongData as "LongData",
            LongRawData as "LongRawData"
        from TestDataFrame
        order by Id
        """
    )
    fetched_df = pyarrow.table(odf)
    assert fetched_df.equals(df)


def test_8904(conn, cursor, empty_tab):
    "8904 - test ingestion with decimal values"
    arrays = [
        pyarrow.array(
            [
                decimal.Decimal("1"),
                decimal.Decimal("2"),
                decimal.Decimal("3"),
            ],
            pyarrow.decimal128(9, 0),
        ),
        pyarrow.array(
            [
                decimal.Decimal("1234567890.1234"),
                decimal.Decimal("-9876543210.9876"),
                decimal.Decimal("0.0001"),
            ],
            pyarrow.decimal128(15, 4),
        ),
    ]
    names = ["Id", "DecimalData"]
    df = pyarrow.table(arrays, names)
    cursor.executemany(
        """
        insert into TestDataFrame
        (Id, DecimalData)
        values (:1, :2)
        """,
        df,
    )
    conn.commit()
    odf = conn.fetch_df_all(
        """
        select
            Id as "Id",
            DecimalData as "DecimalData"
        from TestDataFrame
        order by Id
        """,
        fetch_decimals=True,
    )
    fetched_df = pyarrow.table(odf)
    assert fetched_df.equals(df)


def test_8905(skip_unless_native_boolean_supported, conn, cursor):
    "8905 - test ingestion with boolean values"
    arrays = [
        pyarrow.array([1, 2, 3], pyarrow.int64()),
        pyarrow.array([True, False, True], pyarrow.bool_()),
        pyarrow.array([False, True, None], pyarrow.bool_()),
    ]
    names = ["IntCol", "BooleanCol1", "BooleanCol2"]
    df = pyarrow.table(arrays, names)
    cursor.execute("truncate table TestBooleans")
    cursor.executemany(
        """
        insert into TestBooleans
        (IntCol, BooleanCol1, BooleanCol2)
        values (:1, :2, :3)
        """,
        df,
    )
    conn.commit()
    odf = conn.fetch_df_all(
        """
        select
            IntCol as "IntCol",
            BooleanCol1 as "BooleanCol1",
            BooleanCol2 as "BooleanCol2"
        from TestBooleans
        order by IntCol
        """
    )
    fetched_df = pyarrow.table(odf)
    assert fetched_df.equals(df)


def test_8906(conn, cursor, empty_tab):
    "8906 - test ingestion with timestamp values"
    arrays = [
        pyarrow.array([1, 2, 3], pyarrow.int64()),
        pyarrow.array(
            [
                datetime.datetime(2020, 1, 1, 0, 0, 0),
                datetime.datetime(2021, 2, 2, 12, 34, 56),
                datetime.datetime(2022, 3, 3, 23, 59, 59),
            ],
            pyarrow.timestamp("us"),
        ),
    ]
    names = ["Id", "LastUpdated"]
    df = pyarrow.table(arrays, names)
    cursor.executemany(
        """
        insert into TestDataFrame
        (Id, LastUpdated)
        values (:1, :2)
        """,
        df,
    )
    conn.commit()
    odf = conn.fetch_df_all(
        """
        select
            Id as "Id",
            LastUpdated as "LastUpdated"
        from TestDataFrame
        order by Id
        """
    )
    fetched_df = pyarrow.table(odf)
    assert fetched_df.equals(df)


def test_8907(cursor, test_env):
    "8907 - test ingestion with mismatched column count"
    arrays = [
        pyarrow.array([1, 2, 3], pyarrow.int64()),
        pyarrow.array(["John", "Jane", "Bob"], pyarrow.large_string()),
    ]
    names = ["ID", "NAME"]
    df = pyarrow.table(arrays, names)
    with test_env.assert_raises_full_code("DPY-4009", "ORA-01008"):
        cursor.executemany(
            """
            insert into TestDataFrame (Id, FirstName, Salary)
            values (:1, :2, :3)
            """,
            df,
        )


def test_8908(cursor, test_env):
    "8908 - test ingestion with invalid data type"
    arrays = [
        pyarrow.array([1, 2, 3], pyarrow.int64()),
        pyarrow.array(
            [["a", "b"], ["c"], ["d", "e", "f"]],
            pyarrow.list_(pyarrow.large_string()),
        ),
    ]
    names = ["Id", "FirstName"]
    df = pyarrow.table(arrays, names)
    with test_env.assert_raises_full_code("DPY-3033"):
        cursor.executemany(
            """
            insert into TestDataFrame (Id, FirstName)
            values (:1, :2)
            """,
            df,
        )


def test_8909(cursor, test_env):
    "8909 - test execute() with DataFrame"
    arrays = [
        pyarrow.array([1, 2, 3], pyarrow.int64()),
        pyarrow.array(["John", "Jane", "Sue"], pyarrow.large_string()),
    ]
    names = ["Id", "FirstName"]
    df = pyarrow.table(arrays, names)
    with test_env.assert_raises_full_code("DPY-2003"):
        cursor.execute(
            """
            insert into TestDataFrame (Id, FirstName)
            values (:1, :2)
            """,
            df,
        )


def test_8910(conn, cursor):
    "8910 - test consecutive executemany() calls with same dataframe"
    arrays = [
        pyarrow.array([1, 2, 3], pyarrow.int64()),
        pyarrow.array(["John", "Jane", "Bob"], pyarrow.large_string()),
        pyarrow.array([1000.50, 2000.75, 3000.25], pyarrow.float64()),
    ]
    names = ["Id", "FirstName", "Salary"]
    df = pyarrow.table(arrays, names)
    for i in range(3):
        cursor.execute("delete from TestDataFrame")
        cursor.executemany(
            """
            insert into TestDataFrame (Id, FirstName, Salary)
            values (:1, :2, :3)
            """,
            df,
        )
        conn.commit()
        odf = conn.fetch_df_all(
            """
            select
                Id as "Id",
                FirstName as "FirstName",
                Salary as "Salary"
            from TestDataFrame
            order by Id
            """
        )
        fetched_df = pyarrow.table(odf)
        assert fetched_df.equals(df)


def test_8911(conn, cursor, empty_tab):
    "8911 - test nulls/None for all datatypes"
    arrays = [
        pyarrow.array([1], pyarrow.int64()),
        pyarrow.array([None], pyarrow.float32()),
        pyarrow.array([None], pyarrow.float64()),
        pyarrow.array([None], pyarrow.large_string()),
        pyarrow.array([None], pyarrow.timestamp("s")),
        pyarrow.array([None], pyarrow.large_binary()),
    ]
    names = [
        "Id",
        "FloatData",
        "DoubleData",
        "FirstName",
        "DateOfBirth",
        "RawData",
    ]
    df = pyarrow.table(arrays, names)
    bind_names = ",".join(names)
    bind_values = ",".join(f":{i + 1}" for i in range(len(names)))
    cursor.executemany(
        f"""
        insert into TestDataFrame ({bind_names})
        values ({bind_values})
        """,
        df,
    )
    conn.commit()
    query_values = ",".join(f'{name} as "{name}"' for name in names)
    odf = conn.fetch_df_all(
        f"""
        select {query_values}
        from TestDataFrame
        order by Id
        """
    )
    fetched_df = pyarrow.table(odf)
    assert fetched_df.equals(df)


def test_8912(conn, cursor, empty_tab):
    "8912 - test LOB sizes around 32K boundary using DataFrame ingestion"
    test_sizes = [32766, 32767, 32768, 32769, 32770]
    arrays = [
        pyarrow.array(range(1, len(test_sizes) + 1), pyarrow.int64()),
        pyarrow.array(["X" * s for s in test_sizes], pyarrow.large_string()),
        pyarrow.array([b"Y" * s for s in test_sizes], pyarrow.large_binary()),
    ]
    names = ["Id", "LongData", "LongRawData"]
    df = pyarrow.table(arrays, names)
    cursor.executemany(
        """
        insert into TestDataFrame (Id, LongData, LongRawData)
        values (:1, :2, :3)
        """,
        df,
    )
    conn.commit()
    odf = conn.fetch_df_all(
        """
        select
            Id as "Id",
            LongData as "LongData",
            LongRawData as "LongRawData"
        from TestDataFrame
        order by Id
        """
    )
    fetched_df = pyarrow.table(odf)
    assert fetched_df.equals(df)


def test_8913(conn, cursor, empty_tab, test_env):
    "8913 - test ingestion with mixed characters using DataFrame"
    if test_env.charset != "AL32UTF8":
        pytest.skip("Database character set must be AL32UTF8")

    test_data = [
        "ASCII: Hello World",  # Pure ASCII
        "Latin: café España",  # Latin-1 Supplement
        "Cyrillic: русский текст",  # Actual Cyrillic
        "Chinese: 中文测试",  # Actual Chinese
        "Emoji: 👍😊❤️",  # Emojis
        "Special: ~!@#$%^&*()_+{}|:\"<>?`-=[]\\;',./",  # ASCII symbols
        "Mixed: 你好, world! café? 123@# русский 👍",  # Mixed characters
    ]
    arrays = [
        pyarrow.array(range(1, len(test_data) + 1), pyarrow.int64()),
        pyarrow.array(test_data, pyarrow.large_string()),
    ]
    names = ["Id", "FirstName"]
    df = pyarrow.table(arrays, names)
    cursor.executemany(
        """
        insert into TestDataFrame (Id, FirstName)
        values (:1, :2)
        """,
        df,
    )
    conn.commit()
    odf = conn.fetch_df_all(
        """
        select
            Id as "Id",
            FirstName as "FirstName"
        from TestDataFrame
        order by Id
        """
    )
    fetched_df = pyarrow.table(odf)
    assert fetched_df.equals(df)


def test_8914(conn, cursor, empty_tab):
    "8914 - test various numeric values"
    test_data = [
        decimal.Decimal(0),
        decimal.Decimal(1),
        decimal.Decimal(-1),
        decimal.Decimal("99999999999.9999"),
        decimal.Decimal("-99999999999.9999"),
        decimal.Decimal("10000000000.0001"),
        decimal.Decimal("-10000000000.0001"),
        decimal.Decimal(".0001"),
        decimal.Decimal("-.0001"),
        decimal.Decimal(".9"),
        decimal.Decimal("-.9"),
        decimal.Decimal(".09"),
        decimal.Decimal("-.09"),
        decimal.Decimal(".009"),
        decimal.Decimal("-.009"),
    ]
    ids = [decimal.Decimal(i) for i in range(len(test_data))]
    arrays = [
        pyarrow.array(ids, pyarrow.decimal128(9, 0)),
        pyarrow.array(test_data, pyarrow.decimal128(15, 4)),
    ]
    names = ["Id", "DecimalData"]
    df = pyarrow.table(arrays, names)
    cursor.executemany(
        """
        insert into TestDataFrame (Id, DecimalData)
        values (:1, :2)
        """,
        df,
    )
    conn.commit()
    odf = conn.fetch_df_all(
        """
        select
            Id as "Id",
            DecimalData as "DecimalData"
        from TestDataFrame
        order by Id
        """,
        fetch_decimals=True,
    )
    fetched_df = pyarrow.table(odf)
    assert fetched_df.equals(df)


def test_8915(conn, cursor, empty_tab):
    "8915 - test various timestamp values"
    test_data = [
        datetime.datetime(2056, 2, 29),
        datetime.datetime(2020, 2, 29),
        datetime.datetime(1900, 1, 1),
        datetime.datetime(2000, 1, 1),
        datetime.datetime(1970, 1, 1),
        datetime.datetime(2020, 2, 29, 23, 59, 59, 123456),
        datetime.datetime(2023, 12, 31, 23, 59, 59, 567890),
        datetime.datetime(2024, 1, 1, 0, 0, 0, 789012),
    ]
    ids = list(range(len(test_data)))
    arrays = [
        pyarrow.array(ids, pyarrow.int64()),
        pyarrow.array(test_data, pyarrow.timestamp("us")),
    ]
    names = ["Id", "LastUpdated"]
    df = pyarrow.table(arrays, names)
    cursor.executemany(
        """
        insert into TestDataFrame (Id, LastUpdated)
        values (:1, :2)
        """,
        df,
    )
    conn.commit()
    odf = conn.fetch_df_all(
        """
        select
            Id as "Id",
            LastUpdated as "LastUpdated"
        from TestDataFrame
        order by Id
        """
    )
    fetched_df = pyarrow.table(odf)
    assert fetched_df.equals(df)


def test_8916(conn, cursor, empty_tab):
    "8916 - test insertion with large data volumes"
    num_rows = 10_000
    ids = list(range(1, num_rows + 1))
    names = [f"Employee-{i}" for i in ids]
    salaries = [i * 100.25 for i in ids]
    arrays = [
        pyarrow.array(ids, pyarrow.int64()),
        pyarrow.array(names, pyarrow.large_string()),
        pyarrow.array(salaries, pyarrow.float64()),
    ]
    names = ["Id", "FirstName", "Salary"]
    df = pyarrow.table(arrays, names)
    cursor.executemany(
        """
        insert into TestDataFrame (Id, FirstName, Salary)
        values (:1, :2, :3)
        """,
        df,
    )
    conn.commit()
    odf = conn.fetch_df_all(
        """
        select
            Id as "Id",
            FirstName as "FirstName",
            Salary as "Salary"
        from TestDataFrame
        order by Id
        """
    )
    fetched_df = pyarrow.table(odf)
    assert fetched_df.equals(df)


def test_8917(skip_unless_sparse_vectors_supported, conn, cursor):
    "8917 - test ingestion of sparse vectors"
    arrays = [
        pyarrow.array([1, 2, 3], pyarrow.int64()),
        pyarrow.array(
            [
                None,
                dict(num_dimensions=16, indices=[1, 3], values=[1, -1]),
                dict(num_dimensions=16, indices=[5, 10], values=[2, -2]),
            ],
            pyarrow.struct(SPARSE_VECTOR_FIELDS_INT8),
        ),
        pyarrow.array(
            [
                dict(num_dimensions=16, indices=[1, 3], values=[1.1, -1.1]),
                None,
                dict(num_dimensions=16, indices=[5, 10], values=[2.2, -2.2]),
            ],
            pyarrow.struct(SPARSE_VECTOR_FIELDS_FLOAT32),
        ),
        pyarrow.array(
            [
                dict(num_dimensions=16, indices=[1, 3], values=[1.25, -1.25]),
                dict(num_dimensions=16, indices=[5, 10], values=[2.5, -2.5]),
                None,
            ],
            pyarrow.struct(SPARSE_VECTOR_FIELDS_FLOAT64),
        ),
    ]
    names = [
        "IntCol",
        "SparseVector8Col",
        "SparseVector32Col",
        "SparseVector64Col",
    ]
    df = pyarrow.table(arrays, names)
    cursor.execute("delete from TestSparseVectors")
    column_names = ",".join(names)
    bind_names = ",".join(f":{i + 1}" for i in range(len(names)))
    cursor.executemany(
        f"""
        insert into TestSparseVectors ({column_names})
        values ({bind_names})
        """,
        df,
    )
    conn.commit()
    query_names = ",".join(f'{name} as "{name}"' for name in names)
    odf = conn.fetch_df_all(
        f"""
        select {query_names}
        from TestSparseVectors
        order by IntCol
        """
    )
    fetched_df = pyarrow.table(odf)
    assert fetched_df.equals(df)


def test_8918(skip_unless_vectors_supported, conn, cursor):
    "8918 - test ingestion of dense vectors"
    arrays = [
        pyarrow.array([1, 2, 3], pyarrow.int64()),
        pyarrow.array(
            [
                None,
                [
                    -127,
                    -100,
                    -5,
                    -1,
                    0,
                    0,
                    0,
                    0,
                    1,
                    5,
                    7,
                    25,
                    13,
                    0,
                    10,
                    127,
                ],
                [
                    -25,
                    25,
                    -15,
                    15,
                    -5,
                    5,
                    0,
                    0,
                    -127,
                    127,
                    -25,
                    25,
                    -105,
                    105,
                    -1,
                    1,
                ],
            ],
            pyarrow.list_(pyarrow.int8()),
        ),
        pyarrow.array(
            [
                None,
                [
                    -12.5,
                    -578.625,
                    -100.25,
                    -87.5,
                    0,
                    25,
                    0,
                    0,
                    1,
                    1.25,
                    1.75,
                    2.5,
                    1.75,
                    0,
                    5889.125,
                    6500.375,
                ],
                [
                    -25.5,
                    25.5,
                    -15.25,
                    15.25,
                    -5.3,
                    5.3,
                    0,
                    0,
                    -127.8,
                    127.8,
                    -15.222,
                    15.222,
                    -105.333,
                    105.333,
                    -1,
                    1,
                ],
            ],
            pyarrow.list_(pyarrow.float32()),
        ),
        pyarrow.array(
            [
                None,
                [
                    -22.5,
                    -278.625,
                    -200.25,
                    -77.5,
                    0,
                    35,
                    0,
                    0,
                    1,
                    8.25,
                    9.75,
                    3.5,
                    4.75,
                    0,
                    6889.125,
                    7500.375,
                ],
                [
                    -35.5,
                    35.5,
                    -25.25,
                    25.25,
                    -8.3,
                    8.3,
                    0,
                    0,
                    -227.8,
                    227.8,
                    -215.222,
                    415.222,
                    -505.333,
                    605.333,
                    -1,
                    1,
                ],
            ],
            pyarrow.list_(pyarrow.float64()),
        ),
    ]
    names = [
        "IntCol",
        "Vector8Col",
        "Vector32Col",
        "Vector64Col",
    ]
    df = pyarrow.table(arrays, names)
    cursor.execute("delete from TestVectors")
    column_names = ",".join(names)
    bind_names = ",".join(f":{i + 1}" for i in range(len(names)))
    cursor.executemany(
        f"""
        insert into TestVectors ({column_names})
        values ({bind_names})
        """,
        df,
    )
    conn.commit()
    query_names = ",".join(f'{name} as "{name}"' for name in names)
    odf = conn.fetch_df_all(
        f"""
        select {query_names}
        from TestVectors
        order by IntCol
        """
    )
    fetched_df = pyarrow.table(odf)
    assert fetched_df.equals(df)


@pytest.mark.parametrize(
    "values, dtype",
    [
        ([-(2**7), 0, 2**7 - 1], pyarrow.int8()),
        ([-(2**15), 0, 2**15 - 1], pyarrow.int16()),
        ([-(2**31), 0, 2**31 - 1], pyarrow.int32()),
        ([-(2**63), 0, 2**63 - 1], pyarrow.int64()),
        ([0, 2**7, 2**8 - 1], pyarrow.uint8()),
        ([0, 2**15, 2**16 - 1], pyarrow.uint16()),
        ([0, 2**31, 2**32 - 1], pyarrow.uint32()),
        ([0, 2**63, 2**64 - 1], pyarrow.uint64()),
    ],
)
def test_8919(values, dtype, conn, cursor, empty_tab):
    "8919 - test ingestion with various integer data types"
    names = ["Id", "LongIntegerData"]
    arrays = [
        pyarrow.array([1, 2, 3], pyarrow.int8()),
        pyarrow.array(values, dtype),
    ]
    df = pyarrow.table(arrays, names)
    cursor.executemany(
        """
        insert into TestDataFrame (Id, LongIntegerData)
        values (:1, :2)
        """,
        df,
    )
    conn.commit()
    cursor.execute(
        """
        select to_char(LongIntegerData)
        from TestDataFrame
        order by Id
        """
    )
    fetched_values = [int(s) for s, in cursor]
    assert fetched_values == values


@pytest.mark.parametrize(
    "values, dtype",
    [
        (
            [
                datetime.datetime(1915, 9, 11),
                None,
                datetime.datetime(2045, 2, 28),
            ],
            pyarrow.date32(),
        ),
        (
            [
                datetime.datetime(1905, 3, 30),
                None,
                datetime.datetime(2060, 10, 5),
            ],
            pyarrow.date64(),
        ),
    ],
)
def test_8920(values, dtype, conn, cursor, empty_tab):
    "8920 - test ingestion with alternative date types"
    names = ["Id", "DateOfBirth"]
    arrays = [
        pyarrow.array([1, 2, 3], pyarrow.int8()),
        pyarrow.array(values, dtype),
    ]
    df = pyarrow.table(arrays, names)
    cursor.executemany(
        """
        insert into TestDataFrame (Id, DateOfBirth)
        values (:1, :2)
        """,
        df,
    )
    conn.commit()
    cursor.execute(
        """
        select DateOfBirth
        from TestDataFrame
        order by Id
        """
    )
    fetched_values = [d for d, in cursor]
    assert fetched_values == values


@pytest.mark.parametrize("batch_size", [1, 5, 99, 199, 200])
def test_8921(batch_size, conn, cursor, empty_tab, round_trip_checker):
    "8921 - test ingestion with various batch sizes"
    names = ["Id", "FirstName"]
    rows = [(i + 1, f"Name {i + 1}") for i in range(200)]
    arrays = [
        pyarrow.array([i for i, _ in rows], pyarrow.int16()),
        pyarrow.array([s for _, s in rows], pyarrow.large_string()),
    ]
    df = pyarrow.table(arrays, names)
    cursor.executemany(
        "insert into TestDataFrame (Id, FirstName) values (:1, :2)",
        df,
        batch_size=batch_size,
    )
    expected_round_trips = len(rows) // batch_size
    if len(rows) % batch_size:
        expected_round_trips += 1
    assert round_trip_checker.get_value() == expected_round_trips
    conn.commit()
    cursor.execute("select Id, FirstName from TestDataFrame order by Id")
    assert cursor.fetchall() == rows


@pytest.mark.parametrize("batch_size", [1, 5, 99, 199, 200])
def test_8922(batch_size, conn, cursor, empty_tab, round_trip_checker):
    "8922 - test ingestion of multi chunk data frames with various batch sizes"
    names = ["Id", "FirstName"]
    rows = [(i + 1, f"Name {i + 1}") for i in range(200)]
    int_arrays = [
        pyarrow.array([i for i, _ in rows[:25]], pyarrow.int16()),
        pyarrow.array([i for i, _ in rows[25:59]], pyarrow.int16()),
        pyarrow.array([i for i, _ in rows[59:75]], pyarrow.int16()),
        pyarrow.array([i for i, _ in rows[75:190]], pyarrow.int16()),
        pyarrow.array([i for i, _ in rows[190:]], pyarrow.int16()),
    ]
    str_arrays = [
        pyarrow.array([s for _, s in rows[:25]], pyarrow.large_string()),
        pyarrow.array([s for _, s in rows[25:59]], pyarrow.large_string()),
        pyarrow.array([s for _, s in rows[59:75]], pyarrow.large_string()),
        pyarrow.array([s for _, s in rows[75:190]], pyarrow.large_string()),
        pyarrow.array([s for _, s in rows[190:]], pyarrow.large_string()),
    ]
    chunked_arrays = [
        pyarrow.chunked_array(int_arrays),
        pyarrow.chunked_array(str_arrays),
    ]
    df = pyarrow.table(chunked_arrays, names)
    cursor.executemany(
        "insert into TestDataFrame (Id, FirstName) values (:1, :2)",
        df,
        batch_size=batch_size,
    )
    num_round_trips = 0
    for array in int_arrays:
        num_round_trips += len(array) // batch_size
        if len(array) % batch_size:
            num_round_trips += 1
    assert round_trip_checker.get_value() == num_round_trips
    conn.commit()
    cursor.execute("select Id, FirstName from TestDataFrame order by Id")
    assert cursor.fetchall() == rows
