# -----------------------------------------------------------------------------
# Copyright (c) 2024, Oracle and/or its affiliates.
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
7400 - Module for testing TPC (two-phase commit) transactions with asyncio.
"""

import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    async def test_7400(self):
        "7400 - test begin, prepare, roll back global transaction"
        await self.cursor.execute("truncate table TestTempTable")
        xid = self.conn.xid(3900, b"txn3900", b"branchId")
        await self.conn.tpc_begin(xid)
        self.assertEqual(await self.conn.tpc_prepare(), False)
        await self.conn.tpc_begin(xid)
        await self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (1, 'tesName')
            """
        )
        self.assertEqual(await self.conn.tpc_prepare(), True)
        await self.conn.tpc_rollback()
        await self.cursor.execute("select count(*) from TestTempTable")
        (count,) = await self.cursor.fetchone()
        self.assertEqual(count, 0)

    async def test_7401(self):
        "7401 - test begin, prepare, commit global transaction"
        await self.cursor.execute("truncate table TestTempTable")
        xid = self.conn.xid(3901, "txn3901", "branchId")
        await self.conn.tpc_begin(xid)
        await self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (1, 'tesName')
            """
        )
        self.assertEqual(await self.conn.tpc_prepare(), True)
        await self.conn.tpc_commit()
        await self.cursor.execute(
            "select IntCol, StringCol1 from TestTempTable"
        )
        self.assertEqual(await self.cursor.fetchall(), [(1, "tesName")])

    async def test_7402(self):
        "7402 - test multiple global transactions on the same connection"
        await self.cursor.execute("truncate table TestTempTable")
        xid1 = self.conn.xid(3902, "txn3902", "branch1")
        xid2 = self.conn.xid(3902, b"txn3902", b"branch2")
        await self.conn.tpc_begin(xid1)
        await self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (1, 'tesName')
            """
        )
        await self.conn.tpc_end()
        await self.conn.tpc_begin(xid2)
        await self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (2, 'tesName')
            """
        )
        await self.conn.tpc_end()
        needs_commit1 = await self.conn.tpc_prepare(xid1)
        needs_commit2 = await self.conn.tpc_prepare(xid2)
        if needs_commit1:
            await self.conn.tpc_commit(xid1)
        if needs_commit2:
            await self.conn.tpc_commit(xid2)
        await self.cursor.execute(
            "select IntCol, StringCol1 from TestTempTable order by IntCol"
        )
        expected_rows = [(1, "tesName"), (2, "tesName")]
        self.assertEqual(await self.cursor.fetchall(), expected_rows)

    async def test_7403(self):
        "7403 - test rollback with parameter xid"
        await self.cursor.execute("truncate table TestTempTable")
        xid1 = self.conn.xid(3901, b"txn3901", b"branch1")
        xid2 = self.conn.xid(3902, "txn3902", "branch2")
        for count, xid in enumerate([xid1, xid2]):
            await self.conn.tpc_begin(xid)
            await self.cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (:id, 'tesName')
                """,
                id=count,
            )
            await self.conn.tpc_end()
        await self.conn.tpc_rollback(xid1)

        with self.assertRaisesFullCode("ORA-24756"):
            await self.conn.tpc_prepare(xid1)
        needs_commit = await self.conn.tpc_prepare(xid2)
        if needs_commit:
            await self.conn.tpc_commit(xid2)
        await self.cursor.execute(
            "select IntCol, StringCol1 from TestTempTable order by IntCol"
        )
        self.assertEqual(await self.cursor.fetchall(), [(1, "tesName")])

    async def test_7404(self):
        "7404 - test resuming a transaction"
        await self.cursor.execute("truncate table TestTempTable")
        xid1 = self.conn.xid(3939, "txn3939", "branch39")
        xid2 = self.conn.xid(3940, "txn3940", "branch40")
        values = [[xid1, (1, "User Info")], [xid2, (2, "Other User Info")]]
        for xid, data in values:
            await self.conn.tpc_begin(xid)
            await self.cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (:1, :2)
                """,
                data,
            )
            await self.conn.tpc_end()
        for xid, data in values:
            await self.conn.tpc_begin(xid, oracledb.TPC_BEGIN_RESUME)
            await self.cursor.execute(
                "select IntCol, StringCol1 from TestTempTable"
            )
            (res,) = await self.cursor.fetchall()
            self.assertEqual(res, data)
            await self.conn.tpc_rollback(xid)

    async def test_7405(self):
        "7405 - test promoting a local transaction to a tpc transaction"
        await self.cursor.execute("truncate table TestTempTable")
        xid = self.conn.xid(3941, "txn3941", "branch41")
        values = (1, "String 1")
        await self.cursor.execute(
            "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)",
            values,
        )
        with self.assertRaisesFullCode("ORA-24776"):
            await self.conn.tpc_begin(xid)
        await self.conn.tpc_begin(xid, oracledb.TPC_BEGIN_PROMOTE)
        await self.cursor.execute(
            "select IntCol, StringCol1 from TestTempTable"
        )
        (res,) = await self.cursor.fetchall()
        self.assertEqual(res, values)
        await self.conn.tpc_rollback(xid)

    async def test_7406(self):
        "7406 - test ending a transaction with parameter xid"
        await self.cursor.execute("truncate table TestTempTable")
        xid1 = self.conn.xid(7406, "txn7406a", "branch3")
        xid2 = self.conn.xid(7406, b"txn7406b", b"branch4")
        await self.conn.tpc_begin(xid1)
        await self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (1, 'test7406a')
            """
        )
        await self.conn.tpc_begin(xid2)
        with self.assertRaisesFullCode("ORA-24758"):
            await self.conn.tpc_end(xid1)
        await self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (2, 'test7406b')
            """
        )
        await self.conn.tpc_end(xid2)
        with self.assertRaisesFullCode("ORA-25352"):
            await self.conn.tpc_end(xid1)
        await self.conn.tpc_rollback(xid1)
        await self.conn.tpc_rollback(xid2)

    async def test_7407(self):
        "7407 - test tpc_recover()"
        await self.cursor.execute("truncate table TestTempTable")
        n_xids = 10
        for i in range(n_xids):
            xid = self.conn.xid(7407 + i, f"txn7407{i}", f"branch{i}")
            await self.conn.tpc_begin(xid)
            await self.cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (:1, 'test7407')
                """,
                [i + 1],
            )
            await self.conn.tpc_prepare(xid)
        recovers = await self.conn.tpc_recover()
        self.assertEqual(len(recovers), n_xids)

        await self.cursor.execute("select * from DBA_PENDING_TRANSACTIONS")
        self.assertEqual(await self.cursor.fetchall(), recovers)

        for xid in recovers:
            if xid.format_id % 2 == 0:
                await self.conn.tpc_commit(xid)
        recovers = await self.conn.tpc_recover()
        self.assertEqual(len(recovers), n_xids // 2)

        for xid in recovers:
            await self.conn.tpc_rollback(xid)
        recovers = await self.conn.tpc_recover()
        self.assertEqual(len(recovers), 0)

    async def test_7408(self):
        "7408 - test tpc_recover() with read-only transaction"
        await self.cursor.execute("truncate table TestTempTable")
        for i in range(4):
            xid = self.conn.xid(7408 + i, f"txn7408{i}", f"branch{i}")
            await self.conn.tpc_begin(xid)
            await self.cursor.execute("select * from TestTempTable")
            await self.conn.tpc_prepare(xid)
        recovers = await self.conn.tpc_recover()
        self.assertEqual(len(recovers), 0)

    async def test_7409(self):
        "7409 - test tpc_commit() with one_phase parameter"
        await self.cursor.execute("truncate table TestTempTable")
        xid = self.conn.xid(7409, "txn7409", "branch1")
        await self.conn.tpc_begin(xid)
        values = (1, "test7409")
        await self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            values,
        )
        await self.cursor.execute(
            "select IntCol, StringCol1 from TestTempTable"
        )
        await self.conn.tpc_commit(xid, one_phase=True)
        self.assertEqual(await self.cursor.fetchall(), [values])

    async def test_7410(self):
        "7410 - test negative cases for tpc_commit()"
        await self.cursor.execute("truncate table TestTempTable")
        xid = self.conn.xid(7410, "txn7410", "branch1")
        await self.conn.tpc_begin(xid)
        await self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (1, 'test7410')
            """
        )
        with self.assertRaises(TypeError):
            await self.conn.tpc_commit("invalid xid")
        await self.conn.tpc_prepare(xid)
        with self.assertRaisesFullCode("ORA-02053"):
            await self.conn.tpc_commit(xid, one_phase=True)
        with self.assertRaisesFullCode("ORA-24756"):
            await self.conn.tpc_commit(xid)

    async def test_7411(self):
        "7411 - test starting an already created transaction"
        await self.cursor.execute("truncate table TestTempTable")
        xid = self.conn.xid(7411, "txn7411", "branch1")
        await self.conn.tpc_begin(xid)
        with self.assertRaisesFullCode("ORA-24757"):
            await self.conn.tpc_begin(xid, oracledb.TPC_BEGIN_NEW)
        with self.assertRaisesFullCode("ORA-24797"):
            await self.conn.tpc_begin(xid, oracledb.TPC_BEGIN_PROMOTE)
        await self.conn.tpc_end()
        for flag in [oracledb.TPC_BEGIN_NEW, oracledb.TPC_BEGIN_PROMOTE]:
            with self.assertRaisesFullCode("ORA-24757"):
                await self.conn.tpc_begin(xid, flag)
        await self.conn.tpc_rollback(xid)

    async def test_7412(self):
        "7412 - test resuming a prepared transaction"
        await self.cursor.execute("truncate table TestTempTable")
        xid = self.conn.xid(7412, "txn7412", "branch1")
        await self.conn.tpc_begin(xid)
        await self.conn.tpc_prepare(xid)
        with self.assertRaisesFullCode("ORA-24756"):
            await self.conn.tpc_begin(xid, oracledb.TPC_BEGIN_RESUME)

    async def test_7413(self):
        "7413 - test tpc_begin and tpc_end with invalid parameters"
        await self.cursor.execute("truncate table TestTempTable")
        xid = self.conn.xid(7413, "txn7413", "branch1")
        test_values = [
            (self.conn.tpc_begin, "DPY-2050"),
            (self.conn.tpc_end, "DPY-2051"),
        ]
        for tpc_function, error_code in test_values:
            with self.assertRaises(TypeError):
                await tpc_function("invalid xid")
            with self.assertRaisesFullCode(error_code):
                await tpc_function(xid, "invalid flag")
            with self.assertRaisesFullCode(error_code):
                await tpc_function(xid, 70)

    async def test_7414(self):
        "7414 - test commiting transaction without tpc_commit"
        xid = self.conn.xid(7414, "txn7409", "branch1")
        await self.conn.tpc_begin(xid)
        with self.assertRaisesFullCode("ORA-02089"):
            await self.cursor.execute("truncate table TestTempTable")

    async def test_7415(self):
        "7415 - test tpc_commit when a commit is not needed"
        xid = self.conn.xid(7416, "txn7416", "branch1")
        await self.conn.tpc_begin(xid)
        await self.cursor.execute("select * from TestTempTable")
        await self.conn.tpc_end(xid)
        await self.conn.tpc_prepare(xid)
        with self.assertRaisesFullCode("ORA-24756"):
            await self.conn.tpc_commit(xid)

    async def test_7416(self):
        "7416 - test transaction_in_progress"
        await self.cursor.execute("truncate table TestTempTable")
        xid = self.conn.xid(7415, "txn7415", "branch1")
        self.assertFalse(self.conn.transaction_in_progress)

        await self.conn.tpc_begin(xid)
        self.assertTrue(self.conn.transaction_in_progress)
        await self.cursor.execute(
            "insert into TestTempTable (IntCol) values (2)"
        )

        await self.conn.tpc_end(xid)
        self.assertFalse(self.conn.transaction_in_progress)

        await self.conn.tpc_prepare(xid)
        self.assertFalse(self.conn.transaction_in_progress)

        await self.conn.tpc_commit(xid)
        self.assertFalse(self.conn.transaction_in_progress)


if __name__ == "__main__":
    test_env.run_test_cases()
