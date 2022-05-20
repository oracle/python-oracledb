#------------------------------------------------------------------------------
# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
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
#------------------------------------------------------------------------------

"""
2900 - Module for testing Rowids
"""

import datetime

import oracledb
import test_env

class TestCase(test_env.BaseTestCase):

    def __populate_test_universal_rowids(self):
        self.cursor.execute("truncate table TestUniversalRowids")
        data = [
            (1, "ABC" * 75, datetime.datetime(2017, 4, 11)),
            (2, "DEF" * 80, datetime.datetime(2017, 4, 12))
        ]
        self.cursor.executemany("""
                    insert into TestUniversalRowids
                    values (:1, :2, :3)""", data)
        self.connection.commit()

    def __test_select_rowids(self, table_name):
        self.cursor.execute(f"select rowid, IntCol from {table_name}")
        sql = f"select IntCol from {table_name} where rowid = :val"
        for rowid, int_val in self.cursor.fetchall():
            self.cursor.execute(sql, val=rowid)
            self.assertEqual(self.cursor.fetchall(), [(int_val,)])

    def test_2900_select_rowids_regular(self):
        "2900 - test selecting all rowids from a regular table"
        self.__test_select_rowids("TestNumbers")

    def test_2901_select_rowids_index_organised(self):
        "2901 - test selecting all rowids from an index organised table"
        self.__populate_test_universal_rowids()
        self.__test_select_rowids("TestUniversalRowids")

    def test_2902_insert_invalid_rowid(self):
        "2902 - test inserting an invalid rowid"
        sql = "insert into TestRowids (IntCol, RowidCol) values (1, :rid)"
        self.assertRaisesRegex(oracledb.DatabaseError, "^ORA-00932:",
                               self.cursor.execute, sql, rid=12345)
        self.assertRaisesRegex(oracledb.DatabaseError, "^ORA-01410:",
                               self.cursor.execute, sql, rid="523lkhlf")

    def test_2903_select_rowids_as_urowids(self):
        "2903 - test selecting regular rowids stored in a urowid column"
        self.cursor.execute("truncate table TestRowids")
        self.cursor.execute("""
                insert into TestRowids (IntCol, UrowidCol)
                select IntCol, rowid from TestNumbers""")
        self.connection.commit()
        self.cursor.execute("select IntCol, UrowidCol from TestRowids")
        for int_val, rowid in self.cursor.fetchall():
            self.cursor.execute("""
                    select IntCol
                    from TestNumbers
                    where rowid = :val""",
                    val=rowid)
            self.assertEqual(self.cursor.fetchall(), [(int_val,)])

if __name__ == "__main__":
    test_env.run_test_cases()
