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


@test_env.skip_unless_thin_mode()
class TestCase(test_env.BaseAsyncTestCase):

    def __convert_date(self, typ, value):
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
            data = [self.__convert_date(typ, v) for v in data]
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
        data = [("test_8123",)]
        ora_df = await self.conn.fetch_df_all(
            "select to_clob('test_8123') from dual"
        )
        fetched_df = pyarrow.table(ora_df).to_pandas()
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, data)

    async def test_8119(self):
        "8119 - fetch blob"
        data = [(b"test_8124",)]
        ora_df = await self.conn.fetch_df_all(
            "select to_blob(utl_raw.cast_to_raw('test_8124')) from dual"
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

    async def test_8124(self):
        "8124 - test metadata of all data types"
        now = datetime.datetime.now()
        data = [
            ("NUMBERVALUE", 5, pyarrow.float64()),
            ("STRINGVALUE", "String Val", pyarrow.string()),
            ("FIXEDCHARVALUE", "Fixed Char", pyarrow.string()),
            ("NSTRINGVALUE", "NString Val", pyarrow.string()),
            ("NFIXEDCHARVALUE", "NFixedChar", pyarrow.string()),
            ("RAWVALUE", b"Raw Data", pyarrow.binary()),
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
        await self.cursor.execute("delete from TestAllTypes")
        column_names = ",".join(n for n, v, t in data)
        bind_values = ",".join(f":{i + 1}" for i in range(len(data)))
        data_to_insert = tuple(v for n, v, t in data)
        await self.cursor.execute(
            f"""
            insert into TestAllTypes ({column_names})
            values ({bind_values})
            """,
            data_to_insert,
        )
        await self.conn.commit()
        sql = f"select {column_names} from TestAllTypes"
        ora_df = await self.conn.fetch_df_all(sql)
        expected_types = [t for n, v, t in data]
        actual_types = [pyarrow.array(a).type for a in ora_df.column_arrays()]
        self.assertEqual(actual_types, expected_types)

    async def test_8125(self):
        "8125 - test metadata of all data types with fetch_decimals = True"
        now = datetime.datetime.now()
        data = [
            ("NUMBERVALUE", 5, pyarrow.float64()),
            ("STRINGVALUE", "String Val", pyarrow.string()),
            ("FIXEDCHARVALUE", "Fixed Char", pyarrow.string()),
            ("NSTRINGVALUE", "NString Val", pyarrow.string()),
            ("NFIXEDCHARVALUE", "NFixedChar", pyarrow.string()),
            ("RAWVALUE", b"Raw Data", pyarrow.binary()),
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
        await self.cursor.execute("delete from TestAllTypes")
        column_names = ",".join(n for n, v, t in data)
        bind_values = ",".join(f":{i + 1}" for i in range(len(data)))
        data_to_insert = tuple(v for n, v, t in data)
        await self.cursor.execute(
            f"""
            insert into TestAllTypes ({column_names})
            values ({bind_values})
            """,
            data_to_insert,
        )
        await self.conn.commit()
        with test_env.DefaultsContextManager("fetch_decimals", True):
            sql = f"select {column_names} from TestAllTypes"
            ora_df = await self.conn.fetch_df_all(sql)
            expected_types = [t for n, v, t in data]
            actual_types = [
                pyarrow.array(a).type for a in ora_df.column_arrays()
            ]
            self.assertEqual(actual_types, expected_types)

    @test_env.skip_unless_native_boolean_supported()
    async def test_8126(self):
        "8126 - test metadata with boolean type"
        await self.cursor.execute("delete from TestBooleans")
        data = [(1, True, False, None), (2, False, True, True)]
        await self.cursor.executemany(
            """
            insert into TestBooleans
            (IntCol, BooleanCol1, BooleanCol2, BooleanCol3)
            values (:1, :2, :3, :4)
            """,
            data,
        )
        await self.conn.commit()

        sql = "select * from TestBooleans order by IntCol"
        ora_df = await self.conn.fetch_df_all(sql)
        expected_types = [
            pyarrow.int64(),
            pyarrow.bool_(),
            pyarrow.bool_(),
            pyarrow.bool_(),
        ]
        actual_types = [pyarrow.array(a).type for a in ora_df.column_arrays()]
        self.assertEqual(actual_types, expected_types)

    async def test_8127(self):
        "8127 - test NULL rows with all null values"
        data = [
            (1, None, None, None, None, None, None, None, None),
            (2, None, None, None, None, None, None, None, None),
        ]
        await self.__test_df_interop(data)

    async def test_8128(self):
        "8128 - test repeated pyarrow table construction"
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
        await self.__populate_table(data)
        ora_df = await self.conn.fetch_df_all(QUERY_SQL)
        table1 = pyarrow.table(ora_df)
        table2 = pyarrow.table(ora_df)
        self.assertEqual(table1.schema, table2.schema)
        self.assertEqual(table1.to_pydict(), table2.to_pydict())

    async def test_8129(self):
        "8129 - test dataframe query with multiple bind variables"
        await self.__populate_table(DATASET_2)
        statement = QUERY_SQL_WITH_WHERE_CLAUSE.format(
            where_clause="where Id between :min_id and :max_id"
        )
        ora_df = await self.conn.fetch_df_all(
            statement, {"min_id": 2, "max_id": 3}
        )
        self.assertEqual(ora_df.num_rows(), 2)

        expected_data = [row for row in DATASET_2 if row[0] in (2, 3)]
        raw_df = self.__convert_to_df(expected_data)
        raw_data = self.__get_data_from_df(raw_df)
        fetched_df = pyarrow.table(ora_df).to_pandas()
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, raw_data)

    async def test_8130(self):
        "8130 - test error handling with invalid SQL in fetch_df_batches()"
        with self.assertRaisesFullCode("ORA-00942"):
            async for batch in self.conn.fetch_df_batches(
                "select * from NonExistentTable"
            ):
                pass

    async def test_8131(self):
        "8131 - test partial batch (last batch smaller than batch size)"
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
        await self.__test_df_batches_interop(
            test_data, batch_size=3, num_batches=3
        )

    async def test_8132(self):
        "8132 - test with date functions"
        await self.__populate_table(DATASET_1)
        ora_df = await self.conn.fetch_df_all(
            """
            select
                Id,
                extract(year from DateOfBirth) as birth_year,
                to_char(DateOfBirth, 'YYYY-MM') as birth_month
            from TestDataFrame
            order by Id
            """
        )
        self.assertEqual(ora_df.num_rows(), len(DATASET_1))
        year_col = ora_df.get_column_by_name("BIRTH_YEAR")
        array = pyarrow.array(year_col)
        self.assertEqual(array.to_pylist(), [1955, 1955])

    async def test_8133(self):
        "8133 - test column access by index bounds"
        await self.__populate_table(DATASET_1)
        ora_df = await self.conn.fetch_df_all(QUERY_SQL)
        with self.assertRaises(IndexError):
            ora_df.get_column(ora_df.num_columns())

    async def test_8134(self):
        "8134 - test with different batch sizes"
        await self.__test_df_batches_interop(
            DATASET_4, batch_size=1, num_batches=6
        )
        await self.__test_df_batches_interop(
            DATASET_4, batch_size=2, num_batches=3
        )

    async def test_8135(self):
        "8135 - test with very large batch size"
        await self.__test_df_batches_interop(
            DATASET_1, batch_size=1000, num_batches=1
        )

    async def test_8136(self):
        "8136 - test error handling with invalid SQL"
        with self.assertRaisesFullCode("ORA-00942"):
            await self.conn.fetch_df_all("select * from NonExistentTable")

    async def test_8137(self):
        "8137 - test error handling with invalid bind variable"
        await self.__populate_table(DATASET_1)
        with self.assertRaisesFullCode("DPY-4010", "ORA-01008"):
            await self.conn.fetch_df_all(
                "select * from TestDataFrame where Id = :missing_bind"
            )

    async def test_8138(self):
        "8138 - test with single row result"
        await self.__populate_table(DATASET_1)
        statement = QUERY_SQL_WITH_WHERE_CLAUSE.format(
            where_clause="where Id = 1"
        )
        ora_df = await self.conn.fetch_df_all(statement)
        self.assertEqual(ora_df.num_rows(), 1)
        self.__validate_df(ora_df, [DATASET_1[0]])

    async def test_8139(self):
        "8139 - test with calculated columns"
        await self.__populate_table(DATASET_1)
        now = datetime.datetime.now().replace(microsecond=0)
        ora_df = await self.conn.fetch_df_all(
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
        self.assertEqual(ora_df.num_rows(), len(DATASET_1))
        self.assertEqual(ora_df.num_columns(), 4)

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
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, expected_data)

    async def test_8140(self):
        "8140 - test fetch_df_batches with bind variables"
        batch_size = 2
        await self.__populate_table(DATASET_4)
        where_clause = "where Id >= :min_id"
        sql = QUERY_SQL_WITH_WHERE_CLAUSE.format(where_clause=where_clause)
        expected_data = [row for row in DATASET_4 if row[0] >= 3]
        offset = 0
        async for batch in self.conn.fetch_df_batches(
            sql, {"min_id": 3}, size=batch_size
        ):
            self.__validate_df(
                batch, expected_data[offset : offset + batch_size]
            )
            offset += batch_size

    async def test_8141(self):
        "8141 - test with large data"
        data = [
            (1, "A" * 41_000, b"Very long description " * 5_000),
            (2, "B" * 35_000, b"Another long text " * 10_000),
            (3, "C" * 72_000, b"Even longer content " * 20_000),
        ]

        await self.cursor.execute("delete from TestDataFrame")
        await self.cursor.executemany(
            """
            insert into TestDataFrame
            (Id, LongData, LongRawData)
            values (:1, :2, :3)
            """,
            data,
        )
        await self.conn.commit()

        ora_df = await self.conn.fetch_df_all(
            """
            select Id, LongData, LongRawData
            from TestDataFrame
            order by Id
            """
        )
        fetched_df = pyarrow.table(ora_df).to_pandas()
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, data)

    async def test_8142(self):
        "8142 - test fetching from an empty table with fetch_df_batches"
        await self.cursor.execute("delete from TestDataFrame")
        batches = [
            b async for b in self.conn.fetch_df_batches(QUERY_SQL, size=10)
        ]
        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0].num_rows(), 0)

    async def test_8143(self):
        "8143 - fetch clob in batches"
        await self.cursor.execute("delete from TestDataFrame")
        test_string = "A" * 10000
        data = [(test_string,)] * 3
        await self.cursor.executemany(
            """
            insert into TestDataFrame (LongData)
            values (:1)
            """,
            data,
        )
        await self.conn.commit()

        offset = 0
        batch_size = 2
        sql = "select LongData from TestDataFrame"
        async for batch in self.conn.fetch_df_batches(sql, size=batch_size):
            fetched_df = pyarrow.table(batch).to_pandas()
            fetched_data = self.__get_data_from_df(fetched_df)
            self.assertEqual(fetched_data, data[offset : offset + batch_size])
            offset += batch_size

    async def test_8144(self):
        "8144 - fetch blob in batches"
        await self.cursor.execute("delete from TestDataFrame")
        test_string = b"B" * 10000
        data = [(test_string,)] * 4
        await self.cursor.executemany(
            """
            insert into TestDataFrame (LongRawData)
            values (:1)
            """,
            data,
        )
        await self.conn.commit()

        offset = 0
        batch_size = 3
        sql = "select LongRawData from TestDataFrame"
        async for batch in self.conn.fetch_df_batches(sql, size=batch_size):
            fetched_df = pyarrow.table(batch).to_pandas()
            fetched_data = self.__get_data_from_df(fetched_df)
            self.assertEqual(fetched_data, data[offset : offset + batch_size])
            offset += batch_size

    async def test_8145(self):
        "8145 - test with empty strings"
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
        await self.__populate_table(data)
        expected_data = [
            tuple(None if v == "" else v for v in row) for row in data
        ]
        ora_df = await self.conn.fetch_df_all(QUERY_SQL)
        fetched_df = pyarrow.table(ora_df).to_pandas()
        fetched_data = self.__get_data_from_df(fetched_df)
        self.assertEqual(fetched_data, expected_data)

    async def test_8146(self):
        "8146 - test with unicode characters"
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
        await self.__test_df_interop(data)

    async def test_8147(self):
        "8147 - test with very old dates"
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
        await self.__test_df_interop(data)

    async def test_8148(self):
        "8148 - test with future dates"
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
        await self.__test_df_interop(data)

    async def test_8149(self):
        "8149 - test with exactly arraysize rows"
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
            for i in range(1, self.cursor.arraysize + 1)
        ]
        await self.__test_df_interop(data)

    async def test_8150(self):
        "8150 - test with arraysize+1 rows"
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
            for i in range(1, self.cursor.arraysize + 2)
        ]
        await self.__test_df_interop(data)

    async def test_8151(self):
        "8151 - test with odd arraysize"
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
        await self.__test_df_interop(data)

    async def test_8152(self):
        "8152 - test with single row"
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
        await self.__test_df_interop(data)

    async def test_8153(self):
        "8153 - test multiple rows with NULL values in different columns"
        now = datetime.datetime.now()
        test_date = datetime.datetime(2000, 1, 1)
        data = [
            (1, None, "Last1", "City1", "Country1", None, None, 100, None),
            (2, "First2", None, None, "Country2", test_date, 2000, None, None),
            (3, "First3", "Last3", None, None, None, 3000, 300, now),
            (4, None, None, None, None, None, None, None, None),
        ]
        await self.__test_df_interop(data)

    async def test_8154(self):
        "8154 - test single column with all NULL values"
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
        await self.__test_df_interop(data)

    async def test_8155(self):
        "8155 - test last column NULL in each row"
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
        await self.__test_df_interop(data)

    async def test_8156(self):
        "8156 - test alternating NULL/non-NULL values in a column"
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
        await self.__test_df_interop(data)

    async def test_8157(self):
        "8157 - test all columns NULL except one"
        now = datetime.datetime.now()
        test_date = datetime.date(2001, 1, 1)
        data = [
            (1, None, None, None, None, None, None, None, now),
            (2, None, None, None, None, test_date, None, None, None),
            (3, "First3", None, None, None, None, None, None, None),
            (4, None, None, None, "Country4", None, None, None, None),
        ]
        await self.__test_df_interop(data)

    async def test_8158(self):
        "8158 - test all date columns with all NULL values"
        data = [
            (1, "First1", "Last1", "City1", "Country1", None, 1000, 100, None),
            (2, "First2", "Last2", "City2", "Country2", None, 2000, 200, None),
            (3, "First3", "Last3", "City3", "Country3", None, 3000, 300, None),
        ]
        await self.__test_df_interop(data)

    async def test_8159(self):
        "8159 - test NULL values in numeric columns"
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
        await self.__test_df_interop(data)

    async def test_8160(self):
        "8160 - test multiple consecutive NULL rows"
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
        await self.__test_df_interop(data)

    async def test_8161(self):
        "8161 - test NULL rows interspersed with data rows"
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
        await self.__test_df_interop(data)

    async def test_8162(self):
        "8162 - test multiple NULL rows with different NULL columns"
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
        await self.__test_df_interop(data)

    async def test_8163(self):
        "8163 - test NULL rows with alternating NULL patterns"
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
        await self.__test_df_interop(data)

    async def test_8164(self):
        "8164 - test multiple NULL rows with partial NULL groups"
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
        await self.__test_df_interop(data)

    async def test_8165(self):
        "8165 - test multiple NULL rows with varying NULL counts"
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
        await self.__test_df_interop(data)


if __name__ == "__main__":
    test_env.run_test_cases()
