# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
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
2900 - Module for testing Rowids
"""

import datetime
import unittest

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    def __populate_test_universal_rowids(self):
        self.cursor.execute("truncate table TestUniversalRowids")
        data = [
            (1, "ABC" * 75, datetime.datetime(2017, 4, 11)),
            (2, "DEF" * 80, datetime.datetime(2017, 4, 12)),
        ]
        self.cursor.executemany(
            "insert into TestUniversalRowids values (:1, :2, :3)",
            data,
        )
        self.conn.commit()

    def __test_select_rowids(self, table_name):
        self.cursor.execute(f"select rowid, IntCol from {table_name}")
        sql = f"select IntCol from {table_name} where rowid = :val"
        for rowid, int_val in self.cursor.fetchall():
            self.cursor.execute(sql, val=rowid)
            self.assertEqual(self.cursor.fetchall(), [(int_val,)])

    def test_2900(self):
        "2900 - test selecting all rowids from a regular table"
        self.__test_select_rowids("TestNumbers")

    def test_2901(self):
        "2901 - test selecting all rowids from an index organised table"
        self.__populate_test_universal_rowids()
        self.__test_select_rowids("TestUniversalRowids")

    def test_2902(self):
        "2902 - test inserting an invalid rowid"
        sql = "insert into TestRowids (IntCol, RowidCol) values (1, :rid)"
        with self.assertRaisesFullCode("ORA-00932"):
            self.cursor.execute(sql, rid=12345)
        with self.assertRaisesFullCode("ORA-01410"):
            self.cursor.execute(sql, rid="523lkhlf")

    def test_2903(self):
        "2903 - test selecting regular rowids stored in a urowid column"
        self.cursor.execute("truncate table TestRowids")
        self.cursor.execute(
            """
            insert into TestRowids (IntCol, UrowidCol)
            select IntCol, rowid
            from TestNumbers
            """
        )
        self.conn.commit()
        self.cursor.execute("select IntCol, UrowidCol from TestRowids")
        for int_val, rowid in self.cursor.fetchall():
            self.cursor.execute(
                "select IntCol from TestNumbers where rowid = :val",
                val=rowid,
            )
            self.assertEqual(self.cursor.fetchall(), [(int_val,)])

    def test_2904(self):
        "2904 - test selecting regular rowids stored in a rowid column"
        self.cursor.execute("truncate table TestRowids")
        self.cursor.execute(
            """
            insert into TestRowids (IntCol, RowidCol)
            select IntCol, rowid
            from TestNumbers
            """
        )
        self.conn.commit()
        self.cursor.execute("select IntCol, RowidCol from TestRowids")
        for int_val, rowid in self.cursor.fetchall():
            self.cursor.execute(
                """
                select IntCol
                from TestNumbers
                where rowid = :val
                """,
                val=rowid,
            )
            self.assertEqual(self.cursor.fetchall(), [(int_val,)])

    def test_2905(self):
        "2905 - binding and inserting a rowid"
        self.cursor.execute("truncate table TestRowids")
        insert_data = [
            (1, "String #1"),
            (2, "String #2"),
            (3, "String #3"),
            (4, "String #4"),
        ]
        self.cursor.execute("truncate table TestTempTable")
        self.cursor.executemany(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            insert_data,
        )
        self.conn.commit()
        ridvar = self.cursor.var(oracledb.ROWID)
        self.cursor.execute(
            """
            begin
                select rowid into :rid
                from TestTempTable
                where IntCol = 3;
            end;
            """,
            rid=ridvar,
        )
        self.cursor.setinputsizes(r1=oracledb.ROWID)
        self.cursor.execute(
            """
            insert into TestRowids (IntCol, RowidCol)
            values(1, :r1)
            """,
            r1=ridvar,
        )
        self.conn.commit()
        self.cursor.execute("select IntCol, RowidCol from TestRowids")
        int_val, rowid = self.cursor.fetchone()
        self.cursor.execute(
            """
            select IntCol, StringCol1 from TestTempTable
            where rowid = :val
            """,
            val=rowid,
        )
        self.assertEqual(self.cursor.fetchone(), (3, "String #3"))

    @unittest.skipIf(
        not test_env.get_is_thin(), "thick mode doesn't support DB_TYPE_UROWID"
    )
    def test_2906(self):
        "2906 - binding and inserting a rowid as urowid"
        self.cursor.execute("truncate table TestRowids")
        insert_data = [
            (1, "String #1", datetime.datetime(2017, 4, 4)),
            (2, "String #2", datetime.datetime(2017, 4, 5)),
            (3, "String #3", datetime.datetime(2017, 4, 6)),
            (4, "A" * 250, datetime.datetime(2017, 4, 7)),
        ]
        self.cursor.execute("truncate table TestUniversalRowids")
        self.cursor.executemany(
            """
            insert into TestUniversalRowids
            values (:1, :2, :3)
            """,
            insert_data,
        )
        self.conn.commit()
        ridvar = self.cursor.var(oracledb.DB_TYPE_UROWID)
        self.cursor.execute(
            """
            begin
                select rowid into :rid
                from TestUniversalRowids
                where IntCol = 3;
            end;
            """,
            rid=ridvar,
        )
        self.cursor.setinputsizes(r1=oracledb.DB_TYPE_UROWID)
        self.cursor.execute(
            """
            insert into TestRowids (IntCol, UrowidCol)
            values(1, :r1)
            """,
            r1=ridvar,
        )
        self.conn.commit()
        self.cursor.execute("select IntCol, UrowidCol from TestRowids")
        int_val, rowid = self.cursor.fetchone()
        self.cursor.execute(
            """
            select IntCol, StringCol, DateCol
            from TestUniversalRowids
            where rowid = :val
            """,
            val=rowid,
        )
        self.assertEqual(
            self.cursor.fetchone(),
            (3, "String #3", datetime.datetime(2017, 4, 6)),
        )

    def test_2907(self):
        "2907 - fetching a null rowid"
        self.cursor.execute("truncate table TestRowids")
        self.cursor.execute("insert into TestRowids (IntCol) values (1)")
        self.conn.commit()
        self.cursor.execute("select * from TestRowids")
        self.assertEqual(self.cursor.fetchone(), (1, None, None))


if __name__ == "__main__":
    test_env.run_test_cases()
