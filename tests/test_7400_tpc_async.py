# -----------------------------------------------------------------------------
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
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

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


async def test_7400(async_conn, async_cursor):
    "7400 - test begin, prepare, roll back global transaction"
    await async_cursor.execute("truncate table TestTempTable")
    xid = async_conn.xid(3900, b"txn3900", b"branchId")
    await async_conn.tpc_begin(xid)
    assert not await async_conn.tpc_prepare()
    await async_conn.tpc_begin(xid)
    await async_cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'tesName')
        """
    )
    assert await async_conn.tpc_prepare()
    await async_conn.tpc_rollback()
    await async_cursor.execute("select count(*) from TestTempTable")
    (count,) = await async_cursor.fetchone()
    assert count == 0


async def test_7401(async_conn, async_cursor):
    "7401 - test begin, prepare, commit global transaction"
    await async_cursor.execute("truncate table TestTempTable")
    xid = async_conn.xid(3901, "txn3901", "branchId")
    await async_conn.tpc_begin(xid)
    await async_cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'tesName')
        """
    )
    assert await async_conn.tpc_prepare()
    await async_conn.tpc_commit()
    await async_cursor.execute("select IntCol, StringCol1 from TestTempTable")
    assert await async_cursor.fetchall() == [(1, "tesName")]


async def test_7402(async_conn, async_cursor):
    "7402 - test multiple global transactions on the same connection"
    await async_cursor.execute("truncate table TestTempTable")
    xid1 = async_conn.xid(3902, "txn3902", "branch1")
    xid2 = async_conn.xid(3902, b"txn3902", b"branch2")
    await async_conn.tpc_begin(xid1)
    await async_cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'tesName')
        """
    )
    await async_conn.tpc_end()
    await async_conn.tpc_begin(xid2)
    await async_cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (2, 'tesName')
        """
    )
    await async_conn.tpc_end()
    needs_commit1 = await async_conn.tpc_prepare(xid1)
    needs_commit2 = await async_conn.tpc_prepare(xid2)
    if needs_commit1:
        await async_conn.tpc_commit(xid1)
    if needs_commit2:
        await async_conn.tpc_commit(xid2)
    await async_cursor.execute(
        "select IntCol, StringCol1 from TestTempTable order by IntCol"
    )
    expected_rows = [(1, "tesName"), (2, "tesName")]
    assert await async_cursor.fetchall() == expected_rows


async def test_7403(async_conn, async_cursor, test_env):
    "7403 - test rollback with parameter xid"
    await async_cursor.execute("truncate table TestTempTable")
    xid1 = async_conn.xid(3901, b"txn3901", b"branch1")
    xid2 = async_conn.xid(3902, "txn3902", "branch2")
    for count, xid in enumerate([xid1, xid2]):
        await async_conn.tpc_begin(xid)
        await async_cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:id, 'tesName')
            """,
            id=count,
        )
        await async_conn.tpc_end()
    await async_conn.tpc_rollback(xid1)

    with test_env.assert_raises_full_code("ORA-24756"):
        await async_conn.tpc_prepare(xid1)
    needs_commit = await async_conn.tpc_prepare(xid2)
    if needs_commit:
        await async_conn.tpc_commit(xid2)
    await async_cursor.execute(
        "select IntCol, StringCol1 from TestTempTable order by IntCol"
    )
    assert await async_cursor.fetchall() == [(1, "tesName")]


async def test_7404(async_conn, async_cursor):
    "7404 - test resuming a transaction"
    await async_cursor.execute("truncate table TestTempTable")
    xid1 = async_conn.xid(3939, "txn3939", "branch39")
    xid2 = async_conn.xid(3940, "txn3940", "branch40")
    values = [[xid1, (1, "User Info")], [xid2, (2, "Other User Info")]]
    for xid, data in values:
        await async_conn.tpc_begin(xid)
        await async_cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            data,
        )
        await async_conn.tpc_end()
    for xid, data in values:
        await async_conn.tpc_begin(xid, oracledb.TPC_BEGIN_RESUME)
        await async_cursor.execute(
            "select IntCol, StringCol1 from TestTempTable"
        )
        (res,) = await async_cursor.fetchall()
        assert res == data
        await async_conn.tpc_rollback(xid)


async def test_7405(async_conn, async_cursor, test_env):
    "7405 - test promoting a local transaction to a tpc transaction"
    await async_cursor.execute("truncate table TestTempTable")
    xid = async_conn.xid(3941, "txn3941", "branch41")
    values = (1, "String 1")
    await async_cursor.execute(
        "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)",
        values,
    )
    with test_env.assert_raises_full_code("ORA-24776"):
        await async_conn.tpc_begin(xid)
    await async_conn.tpc_begin(xid, oracledb.TPC_BEGIN_PROMOTE)
    await async_cursor.execute("select IntCol, StringCol1 from TestTempTable")
    (res,) = await async_cursor.fetchall()
    assert res == values
    await async_conn.tpc_rollback(xid)


async def test_7406(async_conn, async_cursor, test_env):
    "7406 - test ending a transaction with parameter xid"
    await async_cursor.execute("truncate table TestTempTable")
    xid1 = async_conn.xid(7406, "txn7406a", "branch3")
    xid2 = async_conn.xid(7406, b"txn7406b", b"branch4")
    await async_conn.tpc_begin(xid1)
    await async_cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'test7406a')
        """
    )
    await async_conn.tpc_begin(xid2)
    with test_env.assert_raises_full_code("ORA-24758"):
        await async_conn.tpc_end(xid1)
    await async_cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (2, 'test7406b')
        """
    )
    await async_conn.tpc_end(xid2)
    with test_env.assert_raises_full_code("ORA-25352"):
        await async_conn.tpc_end(xid1)
    await async_conn.tpc_rollback(xid1)
    await async_conn.tpc_rollback(xid2)


async def test_7407(async_conn, async_cursor):
    "7407 - test tpc_recover()"
    await async_cursor.execute("truncate table TestTempTable")
    n_xids = 10
    for i in range(n_xids):
        xid = async_conn.xid(7407 + i, f"txn7407{i}", f"branch{i}")
        await async_conn.tpc_begin(xid)
        await async_cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, 'test7407')
            """,
            [i + 1],
        )
        await async_conn.tpc_prepare(xid)
    recovers = await async_conn.tpc_recover()
    assert len(recovers) == n_xids

    await async_cursor.execute("select * from DBA_PENDING_TRANSACTIONS")
    assert await async_cursor.fetchall() == recovers

    for xid in recovers:
        if xid.format_id % 2 == 0:
            await async_conn.tpc_commit(xid)
    recovers = await async_conn.tpc_recover()
    assert len(recovers) == n_xids // 2

    for xid in recovers:
        await async_conn.tpc_rollback(xid)
    recovers = await async_conn.tpc_recover()
    assert len(recovers) == 0


async def test_7408(async_conn, async_cursor):
    "7408 - test tpc_recover() with read-only transaction"
    await async_cursor.execute("truncate table TestTempTable")
    for i in range(4):
        xid = async_conn.xid(7408 + i, f"txn7408{i}", f"branch{i}")
        await async_conn.tpc_begin(xid)
        await async_cursor.execute("select * from TestTempTable")
        await async_conn.tpc_prepare(xid)
    recovers = await async_conn.tpc_recover()
    assert len(recovers) == 0


async def test_7409(async_conn, async_cursor):
    "7409 - test tpc_commit() with one_phase parameter"
    await async_cursor.execute("truncate table TestTempTable")
    xid = async_conn.xid(7409, "txn7409", "branch1")
    await async_conn.tpc_begin(xid)
    values = (1, "test7409")
    await async_cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        values,
    )
    await async_cursor.execute("select IntCol, StringCol1 from TestTempTable")
    await async_conn.tpc_commit(xid, one_phase=True)
    assert await async_cursor.fetchall() == [values]


async def test_7410(async_conn, async_cursor, test_env):
    "7410 - test negative cases for tpc_commit()"
    await async_cursor.execute("truncate table TestTempTable")
    xid = async_conn.xid(7410, "txn7410", "branch1")
    await async_conn.tpc_begin(xid)
    await async_cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'test7410')
        """
    )
    with pytest.raises(TypeError):
        await async_conn.tpc_commit("invalid xid")
    await async_conn.tpc_prepare(xid)
    with test_env.assert_raises_full_code("ORA-02053"):
        await async_conn.tpc_commit(xid, one_phase=True)
    with test_env.assert_raises_full_code("ORA-24756"):
        await async_conn.tpc_commit(xid)


async def test_7411(async_conn, async_cursor, test_env):
    "7411 - test starting an already created transaction"
    await async_cursor.execute("truncate table TestTempTable")
    xid = async_conn.xid(7411, "txn7411", "branch1")
    await async_conn.tpc_begin(xid)
    with test_env.assert_raises_full_code("ORA-24757"):
        await async_conn.tpc_begin(xid, oracledb.TPC_BEGIN_NEW)
    with test_env.assert_raises_full_code("ORA-24797"):
        await async_conn.tpc_begin(xid, oracledb.TPC_BEGIN_PROMOTE)
    await async_conn.tpc_end()
    for flag in [oracledb.TPC_BEGIN_NEW, oracledb.TPC_BEGIN_PROMOTE]:
        with test_env.assert_raises_full_code("ORA-24757"):
            await async_conn.tpc_begin(xid, flag)
    await async_conn.tpc_rollback(xid)


async def test_7412(async_conn, async_cursor, test_env):
    "7412 - test resuming a prepared transaction"
    await async_cursor.execute("truncate table TestTempTable")
    xid = async_conn.xid(7412, "txn7412", "branch1")
    await async_conn.tpc_begin(xid)
    await async_conn.tpc_prepare(xid)
    with test_env.assert_raises_full_code("ORA-24756"):
        await async_conn.tpc_begin(xid, oracledb.TPC_BEGIN_RESUME)


async def test_7413(async_conn, async_cursor, test_env):
    "7413 - test tpc_begin and tpc_end with invalid parameters"
    await async_cursor.execute("truncate table TestTempTable")
    xid = async_conn.xid(7413, "txn7413", "branch1")
    test_values = [
        (async_conn.tpc_begin, "DPY-2050"),
        (async_conn.tpc_end, "DPY-2051"),
    ]
    for tpc_function, error_code in test_values:
        with pytest.raises(TypeError):
            await tpc_function("invalid xid")
        with test_env.assert_raises_full_code(error_code):
            await tpc_function(xid, "invalid flag")
        with test_env.assert_raises_full_code(error_code):
            await tpc_function(xid, 70)


async def test_7414(async_conn, async_cursor, test_env):
    "7414 - test commiting transaction without tpc_commit"
    xid = async_conn.xid(7414, "txn7409", "branch1")
    await async_conn.tpc_begin(xid)
    with test_env.assert_raises_full_code("ORA-02089"):
        await async_cursor.execute("truncate table TestTempTable")


async def test_7415(async_conn, async_cursor, test_env):
    "7415 - test tpc_commit when a commit is not needed"
    xid = async_conn.xid(7416, "txn7416", "branch1")
    await async_conn.tpc_begin(xid)
    await async_cursor.execute("select * from TestTempTable")
    await async_conn.tpc_end(xid)
    await async_conn.tpc_prepare(xid)
    with test_env.assert_raises_full_code("ORA-24756"):
        await async_conn.tpc_commit(xid)


async def test_7416(async_conn, async_cursor):
    "7416 - test transaction_in_progress"
    await async_cursor.execute("truncate table TestTempTable")
    xid = async_conn.xid(7415, "txn7415", "branch1")
    assert not async_conn.transaction_in_progress

    await async_conn.tpc_begin(xid)
    assert async_conn.transaction_in_progress
    await async_cursor.execute("insert into TestTempTable (IntCol) values (2)")

    await async_conn.tpc_end(xid)
    assert not async_conn.transaction_in_progress

    await async_conn.tpc_prepare(xid)
    assert not async_conn.transaction_in_progress

    await async_conn.tpc_commit(xid)
    assert not async_conn.transaction_in_progress
