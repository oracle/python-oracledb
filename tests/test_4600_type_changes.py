# -----------------------------------------------------------------------------
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
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
4600 - Module for testing the handling of type changes in queries.
"""

import datetime
import unittest

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    def __test_type_change(
        self,
        query_frag_1,
        query_value_1,
        query_frag_2,
        query_value_2,
        table_name="dual",
        type_handler=None,
    ):
        if test_env.get_is_implicit_pooling():
            self.skipTest("sessions can change with implicit pooling")
        orig_type_handler = self.conn.outputtypehandler
        self.conn.outputtypehandler = type_handler
        try:
            self.cursor.execute(
                f"""
                create or replace view TestTypesChanged as
                select {query_frag_1} as value
                from {table_name}
                """
            )
            self.cursor.execute("select * from TestTypesChanged")
            self.assertEqual(self.cursor.fetchall(), [(query_value_1,)])
            self.cursor.execute(
                f"""
                create or replace view TestTypesChanged as
                    select {query_frag_2} as value
                    from dual
                """
            )
            self.cursor.execute("select * from TestTypesChanged")
            self.assertEqual(self.cursor.fetchall(), [(query_value_2,)])
        finally:
            self.conn.outputtypehandler = orig_type_handler

    @unittest.skipIf(
        not test_env.get_is_thin(),
        "thick mode doesn't support this type change",
    )
    def test_4600(self):
        "4600 - test data type changing from VARCHAR to CLOB"
        self.__test_type_change(
            "cast('string_4600' as VARCHAR2(15))",
            "string_4600",
            "to_clob('clob_4600')",
            "clob_4600",
        )

    @unittest.skipIf(
        not test_env.get_is_thin(),
        "thick mode doesn't support this type change",
    )
    def test_4601(self):
        "4601 - test data type changing from CHAR to CLOB"
        self.__test_type_change(
            "cast('string_4601' as CHAR(11))",
            "string_4601",
            "to_clob('clob_4601')",
            "clob_4601",
        )

    @unittest.skipIf(
        not test_env.get_is_thin(),
        "thick mode doesn't support this type change",
    )
    def test_4602(self):
        "4602 - test data type changing from LONG to CLOB"
        self.cursor.execute("truncate table TestLongs")
        self.cursor.execute("insert into TestLongs values (1, 'string_4602')")
        self.__test_type_change(
            "LongCol",
            "string_4602",
            "to_clob('clob_4602')",
            "clob_4602",
            "TestLongs",
        )

    @unittest.skipIf(
        not test_env.get_is_thin(),
        "thick mode doesn't support this type change",
    )
    def test_4603(self):
        "4603 - test data type changing from NVARCHAR to CLOB"
        self.__test_type_change(
            "cast('string_4603' as NVARCHAR2(15))",
            "string_4603",
            "to_clob('clob_4603')",
            "clob_4603",
        )

    @unittest.skipIf(
        not test_env.get_is_thin(),
        "thick mode doesn't support this type change",
    )
    def test_4604(self):
        "4604 - test data type changing from NCHAR to CLOB"
        self.__test_type_change(
            "cast('string_4604' as NCHAR(11))",
            "string_4604",
            "to_clob('clob_4604')",
            "clob_4604",
        )

    @unittest.skipIf(
        not test_env.get_is_thin(),
        "thick mode doesn't support this type change",
    )
    def test_4605(self):
        "4605 - test data type changing from RAW to BLOB"
        self.__test_type_change(
            "utl_raw.cast_to_raw('string_4605')",
            b"string_4605",
            "to_blob(utl_raw.cast_to_raw('blob_4605'))",
            b"blob_4605",
        )

    @unittest.skipIf(
        not test_env.get_is_thin(),
        "thick mode doesn't support this type change",
    )
    def test_4606(self):
        "4606 - test data type changing from LONGRAW to BLOB"
        self.cursor.execute("truncate table TestLongRaws")
        data = [1, b"string_4606"]
        self.cursor.execute("insert into TestLongRaws values (:1, :2)", data)
        self.__test_type_change(
            "LongRawCol",
            b"string_4606",
            "to_blob(utl_raw.cast_to_raw('blob_4606'))",
            b"blob_4606",
            "TestLongRaws",
        )

    @unittest.skipIf(
        not test_env.get_is_thin(),
        "thick mode doesn't support this type change",
    )
    def test_4607(self):
        "4607 - test data type changing from VARCHAR to NCLOB"
        self.__test_type_change(
            "cast('string_4607' as VARCHAR2(15))",
            "string_4607",
            "to_nclob('nclob_4607')",
            "nclob_4607",
        )

    @unittest.skipIf(
        not test_env.get_is_thin(),
        "thick mode doesn't support this type change",
    )
    def test_4608(self):
        "4608 - test data type changing from CHAR to NCLOB"
        self.__test_type_change(
            "cast('string_4608' as CHAR(11))",
            "string_4608",
            "to_nclob('nclob_4608')",
            "nclob_4608",
        )

    @unittest.skipIf(
        not test_env.get_is_thin(),
        "thick mode doesn't support this type change",
    )
    def test_4609(self):
        "4609 - test data type changing from LONG to NCLOB"
        self.cursor.execute("truncate table TestLongs")
        self.cursor.execute("insert into TestLongs values (1, 'string_4609')")
        self.__test_type_change(
            "LongCol",
            "string_4609",
            "to_nclob('nclob_4609')",
            "nclob_4609",
            "TestLongs",
        )

    @unittest.skipIf(
        not test_env.get_is_thin(),
        "thick mode doesn't support this type change",
    )
    def test_4610(self):
        "4610 - test data type changing from NVARCHAR to NCLOB"
        self.__test_type_change(
            "cast('string_4610' as NVARCHAR2(15))",
            "string_4610",
            "to_nclob('nclob_4610')",
            "nclob_4610",
        )

    @unittest.skipIf(
        not test_env.get_is_thin(),
        "thick mode doesn't support this type change",
    )
    def test_4611(self):
        "4611 - test data type changing from NCHAR to NCLOB"
        self.__test_type_change(
            "cast('string_4611' as NCHAR(11))",
            "string_4611",
            "to_nclob('nclob_4611')",
            "nclob_4611",
        )

    def test_4612(self):
        "4612 - test data type changing from VARCHAR to NUMBER"
        self.__test_type_change(
            "cast('string_4612' as VARCHAR2(15))",
            "string_4612",
            "to_number('4612')",
            4612,
        )

    def test_4613(self):
        "4613 - test data type changing from NUMBER to VARCHAR"
        self.__test_type_change(
            "to_number('4613')",
            4613,
            "cast('string_4613' as VARCHAR2(15))",
            "string_4613",
        )

    def test_4614(self):
        "4614 - test data type changing from STRING to DATE"
        self.__test_type_change(
            "cast('string_4614' as VARCHAR2(15))",
            "string_4614",
            "to_date('04-JAN-2022')",
            datetime.datetime(2022, 1, 4, 0, 0),
        )

    def test_4615(self):
        "4615 - test data type changing from DATE to STRING"
        self.__test_type_change(
            "to_date('04-JAN-2022')",
            datetime.datetime(2022, 1, 4, 0, 0),
            "cast('string_4615' as VARCHAR2(15))",
            "string_4615",
        )

    def test_4616(self):
        "4616 - test data type changing from NUMBER to DATE"
        self.__test_type_change(
            "to_number('4616')",
            4616,
            "to_date('05-JAN-2022')",
            datetime.datetime(2022, 1, 5, 0, 0),
        )

    @unittest.skipIf(
        not test_env.get_is_thin(),
        "thick mode doesn't support this type change",
    )
    def test_4617(self):
        "4617 - test data type changing from CLOB to VARCHAR"

        def type_handler(cursor, metadata):
            if metadata.type_code is oracledb.DB_TYPE_CLOB:
                return cursor.var(
                    oracledb.DB_TYPE_VARCHAR,
                    size=32768,
                    arraysize=cursor.arraysize,
                )

        self.__test_type_change(
            "to_clob('clob_4617')",
            "clob_4617",
            "cast('string_4617' as VARCHAR2(15))",
            "string_4617",
            type_handler=type_handler,
        )

    @unittest.skipIf(
        not test_env.get_is_thin(),
        "thick mode doesn't support this type change",
    )
    def test_4618(self):
        "4618 - test data type changing from NCLOB to NVARCHAR"

        def type_handler(cursor, metadata):
            if metadata.type_code is oracledb.DB_TYPE_NCLOB:
                return cursor.var(
                    oracledb.DB_TYPE_NVARCHAR,
                    size=32768,
                    arraysize=cursor.arraysize,
                )

        self.__test_type_change(
            "to_nclob('nclob_4618')",
            "nclob_4618",
            "cast('nstring_4618' as NVARCHAR2(15))",
            "nstring_4618",
            type_handler=type_handler,
        )

    @unittest.skipIf(
        not test_env.get_is_thin(),
        "thick mode doesn't support this type change",
    )
    def test_4619(self):
        "4619 - test data type changing from CLOB to NVARCHAR"

        def type_handler(cursor, metadata):
            if metadata.type_code is oracledb.DB_TYPE_CLOB:
                return cursor.var(
                    oracledb.DB_TYPE_NVARCHAR,
                    size=32768,
                    arraysize=cursor.arraysize,
                )

        self.__test_type_change(
            "to_clob('clob_4619')",
            "clob_4619",
            "cast('string_4619' as VARCHAR2(15))",
            "string_4619",
            type_handler=type_handler,
        )

    @unittest.skipIf(
        not test_env.get_is_thin(),
        "thick mode doesn't support this type change",
    )
    def test_4620(self):
        "4620 - test data type changing from BLOB to RAW"

        def type_handler(cursor, metadata):
            if metadata.type_code is oracledb.DB_TYPE_BLOB:
                return cursor.var(
                    oracledb.DB_TYPE_RAW,
                    size=32768,
                    arraysize=cursor.arraysize,
                )

        self.__test_type_change(
            "to_blob(utl_raw.cast_to_raw('blob_4620'))",
            b"blob_4620",
            "utl_raw.cast_to_raw('string_4620')",
            b"string_4620",
            type_handler=type_handler,
        )

    @unittest.skipIf(
        not test_env.get_is_thin(),
        "thick mode doesn't support this type change",
    )
    def test_4621(self):
        "4621 - test data type changing from NVARCHAR to CLOB"
        self.__test_type_change(
            "cast('string_4621' as NVARCHAR2(15))",
            "string_4621",
            "to_clob('clob_4621')",
            "clob_4621",
        )


if __name__ == "__main__":
    test_env.run_test_cases()
