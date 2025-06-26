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
Module for testing dataframes using asyncio.
"""

import array
import datetime
import decimal
import unittest

import oracledb

try:
    import numpy
    import pandas
    import pyarrow

    HAS_INTEROP = True
except ImportError:
    HAS_INTEROP = False

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


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):

    def __check_interop(self):
        """
        Checks to see if the pyarrow and pandas modules are available.
        """
        if not HAS_INTEROP:
            self.skipTest("missing pandas or pyarrow modules")

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

    async def __populate_table(self, data):
        """
        Populate the test table with the given data.
        """
        await self.cursor.execute("truncate table TestDataframe")
        types = [None] * len(data[0])
        types[8] = oracledb.DB_TYPE_TIMESTAMP
        self.cursor.setinputsizes(*types)
        await self.cursor.executemany(
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
        await self.conn.commit()

    async def __test_df_interop(self, data):
        """
        Tests interoperability with external data frames using the data set
        provided.
        """
        self.__check_interop()
        await self.__populate_table(data)
        statement = "select * from TestDataFrame order by Id"
        ora_df = await self.conn.fetch_df_all(statement)
        self.__validate_df(ora_df, data)

    async def __test_df_batches_interop(self, data, batch_size, num_batches):
        """
        Tests interoperability with external data frames using the data set
        provided.
        """
        self.__check_interop()
        await self.__populate_table(data)
        statement = "select * from TestDataFrame order by Id"
        batches = [
            df
            async for df in self.conn.fetch_df_batches(
                statement, size=batch_size
            )
        ]
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
        fetched_tab = pyarrow.Table.from_arrays(
            ora_df.column_arrays(), names=ora_df.column_names()
        )
        fetched_df = fetched_tab.to_pandas()
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, raw_data)

    async def test_8100(self):
        "8100 - test basic fetch of data frame"
        await self.__populate_table(DATASET_1)
        statement = "select * from TestDataFrame order by Id"
        ora_df = await self.conn.fetch_df_all(statement)
        self.assertEqual(ora_df.num_rows(), len(DATASET_1))
        self.assertEqual(ora_df.num_columns(), len(DATASET_1[0]))
        metadata = dict(
            num_columns=ora_df.num_columns(),
            num_rows=ora_df.num_rows(),
            num_chunks=1,
        )
        self.assertEqual(ora_df.metadata, metadata)

    async def test_8101(self):
        "8101 - test conversion to external dataframe"
        await self.__test_df_interop(DATASET_1)

    async def test_8102(self):
        "8101 - test null and negative values"
        await self.__test_df_interop(DATASET_2)

    async def test_8103(self):
        "8102 - test with fetch_decimals"
        with test_env.DefaultsContextManager("fetch_decimals", True):
            await self.__test_df_interop(DATASET_1)

    async def test_8104(self):
        "8103 - test null and negative values with fetch_decimals"
        with test_env.DefaultsContextManager("fetch_decimals", True):
            await self.__test_df_interop(DATASET_2)

    async def test_8105(self):
        "8105 - test null and values with leading zeros"
        await self.__test_df_interop(DATASET_3)

    async def test_8106(self):
        "8105 - test null and values with leading zeros with fetch_decimals"
        with test_env.DefaultsContextManager("fetch_decimals", True):
            await self.__test_df_interop(DATASET_3)

    async def test_8107(self):
        "8107 - duplicate values in the rows"
        await self.__test_df_interop(DATASET_4)

    async def test_8108(self):
        "8108 - batches without specification of size"
        await self.__test_df_batches_interop(
            DATASET_4, batch_size=None, num_batches=1
        )

    async def test_8109(self):
        "8109 - batches with specification of size"
        await self.__test_df_batches_interop(
            DATASET_4, batch_size=5, num_batches=2
        )

    async def test_8110(self):
        "8110 - verify passing Arrow arrays twice works"
        self.__check_interop()
        await self.__populate_table(DATASET_1)
        statement = "select * from TestDataFrame order by Id"
        ora_df = await self.conn.fetch_df_all(statement)
        self.__validate_df(ora_df, DATASET_1)
        self.__validate_df(ora_df, DATASET_1)

    async def test_8111(self):
        "8111 - verify empty data set"
        await self.__populate_table(DATASET_1)
        statement = "select * from TestDataFrame where Id = 4"
        ora_df = await self.conn.fetch_df_all(statement)
        self.assertEqual(ora_df.num_rows(), 0)

    async def test_8112(self):
        "8112 - verify empty data set with batches"
        await self.__populate_table(DATASET_1)
        statement = "select * from TestDataFrame where Id = 4"
        async for ora_df in self.conn.fetch_df_batches(statement):
            self.assertEqual(ora_df.num_rows(), 0)

    async def test_8113(self):
        "8113 - negative checks on attributes"
        await self.__populate_table(DATASET_1)
        statement = "select * from TestDataFrame order by Id"
        ora_df = await self.conn.fetch_df_all(statement)
        with self.assertRaises(IndexError):
            ora_df.get_column(121)
        with self.assertRaises(IndexError):
            ora_df.get_column(-1)
        with self.assertRaises(KeyError):
            ora_df.get_column_by_name("missing_column")

    async def test_8114(self):
        "8114 - check size and null count with no nulls"
        await self.__populate_table(DATASET_1)
        statement = "select * from TestDataFrame order by Id"
        ora_df = await self.conn.fetch_df_all(statement)
        col = ora_df.get_column(0)
        self.assertEqual(col.size(), len(DATASET_1))
        self.assertEqual(col.null_count, 0)

    async def test_8115(self):
        "8115 - check size and null count with nulls present"
        await self.__populate_table(DATASET_2)
        statement = "select * from TestDataFrame order by Id"
        ora_df = await self.conn.fetch_df_all(statement)
        col = ora_df.get_column_by_name("SALARY")
        self.assertEqual(col.size(), len(DATASET_2))
        self.assertEqual(col.null_count, 2)

    async def test_8116(self):
        "8116 - check unsupported error"
        statement = "select cursor(select user from dual) from dual"
        with self.assertRaisesFullCode("DPY-3030"):
            await self.conn.fetch_df_all(statement)

    async def test_8117(self):
        "8117 - batches with specification of size matching number of rows"
        await self.__test_df_batches_interop(
            DATASET_2, batch_size=len(DATASET_2), num_batches=1
        )

    async def test_8118(self):
        "8118 - batches with size that has duplicate rows across batches"
        await self.__test_df_batches_interop(
            DATASET_4, batch_size=3, num_batches=2
        )

    async def test_8119(self):
        "8119 - fetch_decimals without precision and scale specified"
        data = [(1.0,)]
        self.__check_interop()
        with test_env.DefaultsContextManager("fetch_decimals", True):
            ora_df = await self.conn.fetch_df_all("select 1.0 from dual")
            fetched_tab = pyarrow.Table.from_arrays(
                ora_df.column_arrays(), names=ora_df.column_names()
            )
            fetched_df = fetched_tab.to_pandas()
            fetched_data = self.__get_data_from_df(fetched_df)
            self.assertEqual(fetched_data, data)

    async def test_8120(self):
        "8120 - fetch clob"
        data = [("test_8023",)]
        self.__check_interop()
        ora_df = await self.conn.fetch_df_all(
            "select to_clob('test_8023') from dual"
        )
        fetched_tab = pyarrow.Table.from_arrays(
            ora_df.column_arrays(), names=ora_df.column_names()
        )
        fetched_df = fetched_tab.to_pandas()
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, data)

    async def test_8121(self):
        "8121 - fetch blob"
        data = [(b"test_8024",)]
        self.__check_interop()
        ora_df = await self.conn.fetch_df_all(
            "select to_blob(utl_raw.cast_to_raw('test_8024')) from dual"
        )
        fetched_tab = pyarrow.Table.from_arrays(
            ora_df.column_arrays(), names=ora_df.column_names()
        )
        fetched_df = fetched_tab.to_pandas()
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, data)

    @unittest.skipUnless(test_env.has_server_version(23), "unsupported server")
    async def test_8122(self):
        "8122 - fetch boolean"
        data = [(True,), (False,), (False,), (True,), (True,)]
        self.__check_interop()
        ora_df = await self.conn.fetch_df_all(
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
        fetched_tab = pyarrow.Table.from_arrays(
            ora_df.column_arrays(), names=ora_df.column_names()
        )
        fetched_df = fetched_tab.to_pandas()
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, data)

    @unittest.skipUnless(
        test_env.has_client_version(23, 4), "unsupported client"
    )
    @unittest.skipUnless(
        test_env.has_server_version(23, 4), "unsupported server"
    )
    async def test_8123(self):
        "8123 - fetch float32 vector"
        data = [
            (array.array("f", [34.6, 77.8]).tolist(),),
            (array.array("f", [34.6, 77.8, 55.9]).tolist(),),
        ]
        self.__check_interop()
        ora_df = await self.conn.fetch_df_all(
            """
            SELECT TO_VECTOR('[34.6, 77.8]', 2, FLOAT32)
            union all
            SELECT TO_VECTOR('[34.6, 77.8, 55.9]', 3, FLOAT32)
            """
        )
        self.assertEqual(ora_df.num_rows(), 2)
        self.assertEqual(ora_df.num_columns(), 1)
        ora_col = ora_df.get_column(0)
        self.assertEqual(ora_col.null_count, 0)
        fetched_tab = pyarrow.Table.from_arrays(
            ora_df.column_arrays(), names=ora_df.column_names()
        )

        # number of children for a nested list = 1
        self.assertEqual(fetched_tab.schema.types[0].num_fields, 1)
        fetched_df = fetched_tab.to_pandas()
        self.assertEqual(data, self.__get_data_from_df(fetched_df))

    @unittest.skipUnless(
        test_env.has_client_version(23, 7), "unsupported client"
    )
    @unittest.skipUnless(
        test_env.has_server_version(23, 7), "unsupported server"
    )
    async def test_8124(self):
        "8124 - fetch float64 sparse vectors"
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
        self.__check_interop()
        ora_df = await self.conn.fetch_df_all(
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
        ora_col = ora_df.get_column(0)
        self.assertEqual(ora_col.null_count, 0)
        fetched_tab = pyarrow.Table.from_arrays(
            ora_df.column_arrays(), names=ora_df.column_names()
        )
        # number of children for a struct = 3 (num_dimensions, indices, values)
        self.assertEqual(fetched_tab.schema.types[0].num_fields, 3)
        fetched_df = fetched_tab.to_pandas()
        self.assertEqual(data, self.__get_data_from_df(fetched_df))

    async def test_8125(self):
        "8125 - fetch data with multiple rows containing null values"
        self.__check_interop()
        ora_df = await self.conn.fetch_df_all(
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
        fetched_tab = pyarrow.Table.from_arrays(
            ora_df.column_arrays(), names=ora_df.column_names()
        )
        fetched_df = fetched_tab.to_pandas()
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, data)

    async def test_8126(self):
        "8126 - verify dtype for all Arrow types"
        query = """
            select
                cast(1 as number(10)) as col_int64,
                cast(1.23 as binary_double) as col_double,
                cast(7.14 as binary_float) as col_float,
                cast('abcd' as varchar2(10)) as col_string,
                cast('efgh' as nvarchar2(6)) as col_nstring,
                cast('ijkl' as char(4)) as col_char,
                cast('mnop' as nchar(4)) as col_nchar,
                cast(systimestamp as timestamp(0)) as col_ts_sec,
                cast(systimestamp as timestamp(3)) as col_ts_ms,
                cast(systimestamp as timestamp(6)) as col_ts_us,
                cast(systimestamp as timestamp(9)) as col_ts_ns,
                to_clob('abc') as col_large_string,
                to_nclob('def') as col_large_nstring,
                utl_raw.cast_to_raw('abc2') as col_binary,
                to_blob(utl_raw.cast_to_raw('abc3')) as col_large_binary
            from dual
        """
        decimal_query = (
            "select cast(123.45 as decimal(10, 2)) as col_decimal128 from dual"
        )

        # determine dtype kind enumeration
        ora_df = await self.conn.fetch_df_all("select user from dual")
        col = ora_df.get_column(0)
        dtype_kind = type(col.dtype[0])

        expected_dtypes = {
            "COL_INT64": (dtype_kind.INT, 64, "l", "="),
            "COL_DOUBLE": (dtype_kind.FLOAT, 64, "g", "="),
            "COL_FLOAT": (dtype_kind.FLOAT, 64, "g", "="),
            "COL_STRING": (dtype_kind.STRING, 8, "u", "="),
            "COL_NSTRING": (dtype_kind.STRING, 8, "u", "="),
            "COL_CHAR": (dtype_kind.STRING, 8, "u", "="),
            "COL_NCHAR": (dtype_kind.STRING, 8, "u", "="),
            "COL_TS_SEC": (dtype_kind.DATETIME, 64, "tss:", "="),
            "COL_TS_MS": (dtype_kind.DATETIME, 64, "tsm:", "="),
            "COL_TS_US": (dtype_kind.DATETIME, 64, "tsu:", "="),
            "COL_TS_NS": (dtype_kind.DATETIME, 64, "tsn:", "="),
            "COL_LARGE_STRING": (dtype_kind.STRING, 8, "U", "="),
            "COL_LARGE_NSTRING": (dtype_kind.STRING, 8, "U", "="),
            "COL_BINARY": (dtype_kind.STRING, 8, "z", "="),
            "COL_LARGE_BINARY": (dtype_kind.STRING, 8, "Z", "="),
            "COL_DECIMAL128": (dtype_kind.DECIMAL, 128, "d:10.2", "="),
        }

        # check query without fetch_decimals enabled
        ora_df = await self.conn.fetch_df_all(query)
        for i, name in enumerate(ora_df.column_names()):
            col = ora_df.get_column(i)
            self.assertEqual(col.dtype, expected_dtypes[name])

        # check query with fetch_decimals enabled
        with test_env.DefaultsContextManager("fetch_decimals", True):
            ora_df = await self.conn.fetch_df_all(decimal_query)
            col = ora_df.get_column(0)
            self.assertEqual(col.dtype, expected_dtypes["COL_DECIMAL128"])


if __name__ == "__main__":
    test_env.run_test_cases()
