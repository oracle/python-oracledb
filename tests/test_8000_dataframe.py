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
import numpy
import pandas
import pyarrow
import test_env

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

QUERY_SQL = """
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
    order by id
"""


class TestCase(test_env.BaseTestCase):

    def __convert_date(self, value):
        """
        Converts a date to the format required by Arrow.
        """
        return (value - datetime.datetime(1970, 1, 1)).total_seconds()

    def __convert_to_array(self, data, typ):
        """
        Convert raw data to an Arrow array using pyarrow.
        """
        if isinstance(typ, pyarrow.Decimal128Type):
            data = [
                decimal.Decimal(str(value)) if value is not None else value
                for value in data
            ]
        elif isinstance(typ, pyarrow.TimestampType):
            if typ.unit == "s":
                data = [
                    self.__convert_date(
                        datetime.datetime(v.year, v.month, v.day)
                    )
                    for v in data
                ]
            else:
                data = [self.__convert_date(value) * 1000000 for value in data]
        mask = [value is None for value in data]
        return pyarrow.array(data, typ, mask=mask)

    def __convert_to_df(self, data):
        """
        Converts the data set to a Pandas data frame for comparison to what is
        returned from the database.
        """
        data_by_col = [[row[i] for row in data] for i in range(len(data[0]))]
        fetch_decimals = oracledb.defaults.fetch_decimals
        types = [
            pyarrow.decimal128(9) if fetch_decimals else pyarrow.int64(),
            pyarrow.string(),
            pyarrow.string(),
            pyarrow.string(),
            pyarrow.string(),
            pyarrow.timestamp("s"),
            pyarrow.decimal128(9, 2) if fetch_decimals else pyarrow.float64(),
            pyarrow.decimal128(3) if fetch_decimals else pyarrow.int64(),
            pyarrow.timestamp("us"),
        ]
        arrays = [
            self.__convert_to_array(d, t) for d, t in zip(data_by_col, types)
        ]
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

    def __convert_df_value(self, df_val):
        """
        This method converts a dataframe cell value to use with assertEqual()
        For e.g. NaN and np.array cannot be compared directly. Values are
        converted according to the following rules:
         - NaN -> None
         - np.array -> np.array.tolist() (Python list)
        """
        if isinstance(df_val, numpy.ndarray):
            return df_val.tolist()
        elif pandas.isna(df_val):
            return None
        elif isinstance(df_val, dict):
            return {k: self.__convert_df_value(v) for k, v in df_val.items()}
        else:
            return df_val

    def __get_data_from_df(self, df):
        """
        Returns data from the data frame in a normalized fashion suitable for
        comparison. In particular, NaN values cannot be compared to one another
        so they are converted to the value None for comparison purposes.
        """
        return [
            tuple(self.__convert_df_value(v) for v in row)
            for row in df.itertuples(index=False, name=None)
        ]

    def __populate_table(self, data):
        """
        Populate the test table with the given data.
        """
        self.cursor.execute("delete from TestDataframe")
        types = [None] * len(data[0])
        types[8] = oracledb.DB_TYPE_TIMESTAMP
        self.cursor.setinputsizes(*types)
        self.cursor.executemany(
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
        self.conn.commit()

    def __test_df_interop(self, data):
        """
        Tests interoperability with external data frames using the data set
        provided.
        """
        self.__populate_table(data)
        ora_df = self.conn.fetch_df_all(QUERY_SQL)
        self.__validate_df(ora_df, data)

    def __test_df_batches_interop(self, data, batch_size, num_batches):
        """
        Tests interoperability with external data frames using the data set
        provided.
        """
        self.__populate_table(data)
        batches = list(self.conn.fetch_df_batches(QUERY_SQL, size=batch_size))
        self.assertEqual(len(batches), num_batches)
        if num_batches == 1:
            self.__validate_df(batches[0], data)
        else:
            offset = 0
            for batch in batches:
                self.__validate_df(batch, data[offset : offset + batch_size])
                offset += batch_size

    def __validate_df(self, ora_df, data):
        """
        Validates the data frame by converting it to Pandas and comparing it
        with the original data set that was used.
        """
        raw_df = self.__convert_to_df(data)
        raw_data = self.__get_data_from_df(raw_df)
        fetched_df = pyarrow.table(ora_df).to_pandas()
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, raw_data)

    def test_8000(self):
        "8000 - test basic fetch of data frame"
        self.__populate_table(DATASET_1)
        ora_df = self.conn.fetch_df_all(QUERY_SQL)
        self.assertEqual(ora_df.num_rows(), len(DATASET_1))
        self.assertEqual(ora_df.num_columns(), len(DATASET_1[0]))

    def test_8001(self):
        "8001 - test conversion to external dataframe"
        self.__test_df_interop(DATASET_1)

    def test_8002(self):
        "8001 - test null and negative values"
        self.__test_df_interop(DATASET_2)

    def test_8003(self):
        "8002 - test with fetch_decimals"
        with test_env.DefaultsContextManager("fetch_decimals", True):
            self.__test_df_interop(DATASET_1)

    def test_8004(self):
        "8003 - test null and negative values with fetch_decimals"
        with test_env.DefaultsContextManager("fetch_decimals", True):
            self.__test_df_interop(DATASET_2)

    def test_8005(self):
        "8005 - test null and values with leading zeros"
        self.__test_df_interop(DATASET_3)

    def test_8006(self):
        "8005 - test null and values with leading zeros with fetch_decimals"
        with test_env.DefaultsContextManager("fetch_decimals", True):
            self.__test_df_interop(DATASET_3)

    def test_8007(self):
        "8007 - duplicate values in the rows"
        self.__test_df_interop(DATASET_4)

    def test_8008(self):
        "8008 - batches without specification of size"
        self.__test_df_batches_interop(
            DATASET_4, batch_size=None, num_batches=1
        )

    def test_8009(self):
        "8009 - batches with specification of size"
        self.__test_df_batches_interop(DATASET_4, batch_size=5, num_batches=2)

    def test_8010(self):
        "8010 - verify passing Arrow arrays twice works"
        self.__populate_table(DATASET_1)
        ora_df = self.conn.fetch_df_all(QUERY_SQL)
        self.__validate_df(ora_df, DATASET_1)
        self.__validate_df(ora_df, DATASET_1)

    def test_8011(self):
        "8011 - verify empty data set"
        self.__populate_table(DATASET_1)
        statement = "select * from TestDataFrame where Id = 4"
        ora_df = self.conn.fetch_df_all(statement)
        self.assertEqual(ora_df.num_rows(), 0)

    def test_8012(self):
        "8012 - verify empty data set with batches"
        self.__populate_table(DATASET_1)
        statement = "select * from TestDataFrame where Id = 4"
        for ora_df in self.conn.fetch_df_batches(statement):
            self.assertEqual(ora_df.num_rows(), 0)

    def test_8013(self):
        "8013 - negative checks on attributes"
        self.__populate_table(DATASET_1)
        ora_df = self.conn.fetch_df_all(QUERY_SQL)
        with self.assertRaises(IndexError):
            ora_df.get_column(121)
        with self.assertRaises(IndexError):
            ora_df.get_column(-1)
        with self.assertRaises(KeyError):
            ora_df.get_column_by_name("missing_column")

    def test_8014(self):
        "8014 - check unsupported error"
        statement = "select cursor(select user from dual) from dual"
        with self.assertRaisesFullCode("DPY-3030"):
            self.conn.fetch_df_all(statement)

    def test_8015(self):
        "8015 - batches with specification of size matching number of rows"
        self.__test_df_batches_interop(
            DATASET_2, batch_size=len(DATASET_2), num_batches=1
        )

    def test_8016(self):
        "8016 - verify get_column() returns the correct value"
        self.__populate_table(DATASET_1)
        ora_df = self.conn.fetch_df_all(QUERY_SQL)
        array = pyarrow.array(ora_df.get_column(1))
        self.assertEqual(array.to_pylist(), ["John", "Big"])

    def test_8017(self):
        "8017 - batches with size that has duplicate rows across batches"
        self.__test_df_batches_interop(DATASET_4, batch_size=3, num_batches=2)

    def test_8018(self):
        "8018 - fetch_decimals without precision and scale specified"
        data = [(1.0,)]
        with test_env.DefaultsContextManager("fetch_decimals", True):
            ora_df = self.conn.fetch_df_all("select 1.0 from dual")
            fetched_tab = pyarrow.Table.from_arrays(
                ora_df.column_arrays(), names=ora_df.column_names()
            )
            fetched_df = fetched_tab.to_pandas()
            fetched_data = self.__get_data_from_df(fetched_df)
            self.assertEqual(fetched_data, data)

    def test_8019(self):
        "8019 - fetch clob"
        data = [("test_8023",)]
        ora_df = self.conn.fetch_df_all(
            "select to_clob('test_8023') from dual"
        )
        fetched_df = pyarrow.table(ora_df).to_pandas()
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, data)

    def test_8020(self):
        "8020 - fetch blob"
        data = [(b"test_8024",)]
        ora_df = self.conn.fetch_df_all(
            "select to_blob(utl_raw.cast_to_raw('test_8024')) from dual"
        )
        fetched_df = pyarrow.table(ora_df).to_pandas()
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, data)

    def test_8021(self):
        "8021 - fetch raw"
        data = [(b"test_8025",)]
        ora_df = self.conn.fetch_df_all(
            "select utl_raw.cast_to_raw('test_8025') from dual"
        )
        fetched_df = pyarrow.table(ora_df).to_pandas()
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, data)

    @test_env.skip_unless_native_boolean_supported()
    def test_8022(self):
        "8022 - fetch boolean"
        data = [(True,), (False,), (False,), (True,), (True,)]
        ora_df = self.conn.fetch_df_all(
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
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, data)

    def test_8023(self):
        "8023 - fetch data with multiple rows containing null values"
        ora_df = self.conn.fetch_df_all(
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
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, data)

    @test_env.skip_unless_vectors_supported()
    def test_8024(self):
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
        ora_df = self.conn.fetch_df_all(
            """
            SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT32)
            union all
            SELECT TO_VECTOR('[34.6, 77.8, 55.9]', 3, FLOAT32)
            """
        )
        self.assertEqual(ora_df.num_rows(), 2)
        self.assertEqual(ora_df.num_columns(), 1)
        fetched_df = pyarrow.table(ora_df).to_pandas()
        self.assertEqual(data, self.__get_data_from_df(fetched_df))

    @test_env.skip_unless_vectors_supported()
    def test_8025(self):
        "8025 - fetch float64 vector"
        data = [
            ([34.6, 77.8],),
            ([34.6, 77.8, 55.9],),
        ]
        ora_df = self.conn.fetch_df_all(
            """
            SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT64)
            union all
            SELECT TO_VECTOR('[34.6, 77.8, 55.9]', 3, FLOAT64)
            """
        )
        self.assertEqual(ora_df.num_rows(), 2)
        self.assertEqual(ora_df.num_columns(), 1)
        fetched_df = pyarrow.table(ora_df).to_pandas()
        self.assertEqual(data, self.__get_data_from_df(fetched_df))

    @test_env.skip_unless_vectors_supported()
    def test_8026(self):
        "8026 - fetch int8 vector"
        data = [
            ([34, -77],),
            ([34, 77, 55],),
        ]
        ora_df = self.conn.fetch_df_all(
            """
            SELECT TO_VECTOR('[34, -77]', 2, INT8)
            union all
            SELECT TO_VECTOR('[34, 77, 55]', 3, INT8)
            """
        )
        self.assertEqual(ora_df.num_rows(), 2)
        self.assertEqual(ora_df.num_columns(), 1)
        fetched_df = pyarrow.table(ora_df).to_pandas()
        self.assertEqual(data, self.__get_data_from_df(fetched_df))

    @test_env.skip_unless_vectors_supported()
    def test_8027(self):
        "8027 - fetch binary vector"
        data = [
            ([3, 2, 3],),
            ([3, 2],),
        ]
        ora_df = self.conn.fetch_df_all(
            """
            SELECT TO_VECTOR('[3, 2, 3]', 24, BINARY)
            union all
            SELECT TO_VECTOR('[3, 2]', 16, BINARY)
            """
        )
        self.assertEqual(ora_df.num_rows(), 2)
        self.assertEqual(ora_df.num_columns(), 1)
        fetched_df = pyarrow.table(ora_df).to_pandas()
        self.assertEqual(data, self.__get_data_from_df(fetched_df))

    @test_env.skip_unless_vectors_supported()
    def test_8028(self):
        "8028 - fetch float32 vectors with None"
        data = [
            (array.array("f", [34.6, 77.8]).tolist(),),
            (array.array("f", [34.6, 77.8, 55.9]).tolist(),),
            (None,),
        ]
        ora_df = self.conn.fetch_df_all(
            """
            SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT32)
            union all
            SELECT TO_VECTOR('[34.6, 77.8, 55.9]', 3, FLOAT32)
            union all
            select NULL
            """
        )
        self.assertEqual(ora_df.num_rows(), 3)
        self.assertEqual(ora_df.num_columns(), 1)
        fetched_df = pyarrow.table(ora_df).to_pandas()
        self.assertEqual(data, self.__get_data_from_df(fetched_df))

    @test_env.skip_unless_vectors_supported()
    def test_8029(self):
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
        ora_df = self.conn.fetch_df_all(
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
        self.assertEqual(ora_df.num_rows(), 12)
        self.assertEqual(ora_df.num_columns(), 1)
        fetched_df = pyarrow.table(ora_df).to_pandas()
        self.assertEqual(data, self.__get_data_from_df(fetched_df))

    @test_env.skip_unless_sparse_vectors_supported()
    def test_8030(self):
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
        ora_df = self.conn.fetch_df_all(
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
        self.assertEqual(ora_df.num_rows(), 2)
        self.assertEqual(ora_df.num_columns(), 1)
        fetched_df = pyarrow.table(ora_df).to_pandas()
        self.assertEqual(data, self.__get_data_from_df(fetched_df))

    @test_env.skip_unless_sparse_vectors_supported()
    def test_8031(self):
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
        ora_df = self.conn.fetch_df_all(
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
        self.assertEqual(ora_df.num_rows(), 2)
        self.assertEqual(ora_df.num_columns(), 1)
        fetched_df = pyarrow.table(ora_df).to_pandas()
        self.assertEqual(data, self.__get_data_from_df(fetched_df))

    @test_env.skip_unless_vectors_supported()
    def test_8032(self):
        "8032 - DPY-3031 - Unsupported flexible vector formats"
        with self.assertRaisesFullCode("DPY-3031"):
            self.conn.fetch_df_all(
                """
                SELECT TO_VECTOR('[44, 55, 89]', 3, INT8) as flex_col
                union all
                SELECT TO_VECTOR('[34.6, 77.8, 55.9]', 3, FLOAT32) as flex_col
                """
            )

    @test_env.skip_unless_sparse_vectors_supported()
    def test_8033(self):
        "8033 - DPY-4007 -fetch sparse vectors with flexible dimensions"
        with self.assertRaisesFullCode("DPY-2065"):
            self.conn.fetch_df_all(
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

    def test_8034(self):
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
        self.__populate_table(dataset)

        # Use numeric expression involving a column
        statement = "select CreditScore/4 from TestDataFrame order by Id"
        ora_df = self.conn.fetch_df_all(statement)
        fetched_df = pyarrow.table(ora_df).to_pandas()
        self.assertEqual(data, self.__get_data_from_df(fetched_df))


if __name__ == "__main__":
    test_env.run_test_cases()
