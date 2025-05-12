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

import datetime
import decimal
import unittest

import oracledb

try:
    import pyarrow
    import pandas

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
        datetime.date(1989, 8, 22),
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
        datetime.date(1988, 8, 22),
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
                    datetime.datetime(v.year, v.month, v.day).timestamp()
                    for v in data
                ]
            else:
                data = [value.timestamp() * 1000000 for value in data]
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

    def __get_data_from_df(self, df):
        """
        Returns data from the data frame in a normalized fashion suitable for
        comparison. In particular, NaN values cannot be compared to one another
        so they are converted to the value None for comparison purposes.
        """
        return [
            tuple(None if pandas.isna(v) else v for v in row)
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
        self.assertEqual(col.null_count, 1)

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

    @unittest.skipUnless(
        test_env.get_server_version() >= (23, 1), "unsupported server"
    )
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


if __name__ == "__main__":
    test_env.run_test_cases()
