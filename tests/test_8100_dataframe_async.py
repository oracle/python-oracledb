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


@test_env.skip_unless_thin_mode()
class TestCase(test_env.BaseAsyncTestCase):

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
        await self.cursor.execute("delete from TestDataframe")
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
        await self.__populate_table(data)
        ora_df = await self.conn.fetch_df_all(QUERY_SQL)
        self.__validate_df(ora_df, data)

    async def __test_df_batches_interop(self, data, batch_size, num_batches):
        """
        Tests interoperability with external data frames using the data set
        provided.
        """
        await self.__populate_table(data)
        batches = [
            df
            async for df in self.conn.fetch_df_batches(
                QUERY_SQL, size=batch_size
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
        fetched_df = pyarrow.table(ora_df).to_pandas()
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, raw_data)

    async def test_8100(self):
        "8100 - test basic fetch of data frame"
        await self.__populate_table(DATASET_1)
        ora_df = await self.conn.fetch_df_all(QUERY_SQL)
        self.assertEqual(ora_df.num_rows(), len(DATASET_1))
        self.assertEqual(ora_df.num_columns(), len(DATASET_1[0]))

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
        await self.__populate_table(DATASET_1)
        ora_df = await self.conn.fetch_df_all(QUERY_SQL)
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
        ora_df = await self.conn.fetch_df_all(QUERY_SQL)
        with self.assertRaises(IndexError):
            ora_df.get_column(121)
        with self.assertRaises(IndexError):
            ora_df.get_column(-1)
        with self.assertRaises(KeyError):
            ora_df.get_column_by_name("missing_column")

    async def test_8114(self):
        "8114 - check unsupported error"
        statement = "select cursor(select user from dual) from dual"
        with self.assertRaisesFullCode("DPY-3030"):
            await self.conn.fetch_df_all(statement)

    async def test_8115(self):
        "8115 - batches with specification of size matching number of rows"
        await self.__test_df_batches_interop(
            DATASET_2, batch_size=len(DATASET_2), num_batches=1
        )

    async def test_8116(self):
        "8116 - batches with size that has duplicate rows across batches"
        await self.__test_df_batches_interop(
            DATASET_4, batch_size=3, num_batches=2
        )

    async def test_8117(self):
        "8117 - fetch_decimals without precision and scale specified"
        data = [(1.0,)]
        with test_env.DefaultsContextManager("fetch_decimals", True):
            ora_df = await self.conn.fetch_df_all("select 1.0 from dual")
            fetched_df = pyarrow.table(ora_df).to_pandas()
            fetched_data = self.__get_data_from_df(fetched_df)
            self.assertEqual(fetched_data, data)

    async def test_8118(self):
        "8118 - fetch clob"
        data = [("test_8023",)]
        ora_df = await self.conn.fetch_df_all(
            "select to_clob('test_8023') from dual"
        )
        fetched_df = pyarrow.table(ora_df).to_pandas()
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, data)

    async def test_8119(self):
        "8119 - fetch blob"
        data = [(b"test_8024",)]
        ora_df = await self.conn.fetch_df_all(
            "select to_blob(utl_raw.cast_to_raw('test_8024')) from dual"
        )
        fetched_df = pyarrow.table(ora_df).to_pandas()
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, data)

    @test_env.skip_unless_native_boolean_supported()
    async def test_8120(self):
        "8120 - fetch boolean"
        data = [(True,), (False,), (False,), (True,), (True,)]
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
        fetched_df = pyarrow.table(ora_df).to_pandas()
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, data)

    @test_env.skip_unless_vectors_supported()
    async def test_8121(self):
        "8121 - fetch float32 vector"
        data = [
            (array.array("f", [34.6, 77.8]).tolist(),),
            (array.array("f", [34.6, 77.8, 55.9]).tolist(),),
        ]
        ora_df = await self.conn.fetch_df_all(
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

    @test_env.skip_unless_sparse_vectors_supported()
    async def test_8122(self):
        "8122 - fetch float64 sparse vectors"
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
        fetched_df = pyarrow.table(ora_df).to_pandas()
        self.assertEqual(data, self.__get_data_from_df(fetched_df))

    async def test_8123(self):
        "8123 - fetch data with multiple rows containing null values"
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
        fetched_df = pyarrow.table(ora_df).to_pandas()
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, data)


if __name__ == "__main__":
    test_env.run_test_cases()
