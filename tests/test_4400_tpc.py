#------------------------------------------------------------------------------
# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
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
4400 - Module for testing TPC (two-phase commit) transactions.
"""

import unittest

import oracledb
import test_env

@unittest.skipIf(test_env.get_is_thin(),
                 "thin mode doesn't support two-phase commit yet")
class TestCase(test_env.BaseTestCase):

    def test_4400_tpc_with_rolback(self):
        "4400 - test begin, prepare, roll back global transaction"
        self.cursor.execute("truncate table TestTempTable")
        xid = self.connection.xid(3900, "txn3900", "branchId")
        self.connection.tpc_begin(xid)
        self.assertEqual(self.connection.tpc_prepare(), False)
        self.connection.tpc_begin(xid)
        self.cursor.execute("""
                insert into TestTempTable (IntCol, StringCol1)
                values (1, 'tesName')""")
        self.assertEqual(self.connection.tpc_prepare(), True)
        self.connection.tpc_rollback()
        self.cursor.execute("select count(*) from TestTempTable")
        count, = self.cursor.fetchone()
        self.assertEqual(count, 0)

    def test_4401_tpc_with_commit(self):
        "4401 - test begin, prepare, commit global transaction"
        self.cursor.execute("truncate table TestTempTable")
        xid = self.connection.xid(3901, "txn3901", "branchId")
        self.connection.tpc_begin(xid)
        self.cursor.execute("""
                insert into TestTempTable (IntCol, StringCol1)
                values (1, 'tesName')""")
        self.assertEqual(self.connection.tpc_prepare(), True)
        self.connection.tpc_commit()
        self.cursor.execute("select IntCol, StringCol1 from TestTempTable")
        self.assertEqual(self.cursor.fetchall(), [(1, 'tesName')])

    def test_4402_tpc_multiple_transactions(self):
        "4402 - test multiple global transactions on the same connection"
        self.cursor.execute("truncate table TestTempTable")
        xid1 = self.connection.xid(3902, "txn3902", "branch1")
        xid2 = self.connection.xid(3902, "txn3902", "branch2")
        self.connection.tpc_begin(xid1)
        self.cursor.execute("""
                insert into TestTempTable (IntCol, StringCol1)
                values (1, 'tesName')""")
        self.connection.tpc_end()
        self.connection.tpc_begin(xid2)
        self.cursor.execute("""
                insert into TestTempTable (IntCol, StringCol1)
                values (2, 'tesName')""")
        self.connection.tpc_end()
        needs_commit1 = self.connection.tpc_prepare(xid1)
        needs_commit2 = self.connection.tpc_prepare(xid2)
        if needs_commit1:
            self.connection.tpc_commit(xid1)
        if needs_commit2:
            self.connection.tpc_commit(xid2)
        self.cursor.execute("""
                select IntCol, StringCol1
                from TestTempTable
                order by IntCol""")
        expected_rows = [(1, 'tesName'), (2, 'tesName')]
        self.assertEqual(self.cursor.fetchall(), expected_rows)

if __name__ == "__main__":
    test_env.run_test_cases()
