# -----------------------------------------------------------------------------
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
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
4400 - Module for testing TPC (two-phase commit) transactions.
"""

import oracledb
import pytest


def test_4400(conn, cursor):
    "4400 - test begin, prepare, roll back global transaction"
    cursor.execute("truncate table TestTempTable")
    xid = conn.xid(3900, b"txn3900", b"branchId")
    conn.tpc_begin(xid)
    assert not conn.tpc_prepare()
    conn.tpc_begin(xid)
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'tesName')
        """
    )
    assert conn.tpc_prepare()
    conn.tpc_rollback()
    cursor.execute("select count(*) from TestTempTable")
    (count,) = cursor.fetchone()
    assert count == 0


def test_4401(conn, cursor):
    "4401 - test begin, prepare, commit global transaction"
    cursor.execute("truncate table TestTempTable")
    xid = conn.xid(3901, "txn3901", "branchId")
    conn.tpc_begin(xid)
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'tesName')
        """
    )
    assert conn.tpc_prepare()
    conn.tpc_commit()
    cursor.execute("select IntCol, StringCol1 from TestTempTable")
    assert cursor.fetchall() == [(1, "tesName")]


def test_4402(conn, cursor):
    "4402 - test multiple global transactions on the same connection"
    cursor.execute("truncate table TestTempTable")
    xid1 = conn.xid(3902, "txn3902", "branch1")
    xid2 = conn.xid(3902, b"txn3902", b"branch2")
    conn.tpc_begin(xid1)
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'tesName')
        """
    )
    conn.tpc_end()
    conn.tpc_begin(xid2)
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (2, 'tesName')
        """
    )
    conn.tpc_end()
    needs_commit1 = conn.tpc_prepare(xid1)
    needs_commit2 = conn.tpc_prepare(xid2)
    if needs_commit1:
        conn.tpc_commit(xid1)
    if needs_commit2:
        conn.tpc_commit(xid2)
    cursor.execute(
        "select IntCol, StringCol1 from TestTempTable order by IntCol"
    )
    expected_rows = [(1, "tesName"), (2, "tesName")]
    assert cursor.fetchall() == expected_rows


def test_4403(conn, cursor, test_env):
    "4403 - test rollback with parameter xid"
    cursor.execute("truncate table TestTempTable")
    xid1 = conn.xid(3901, b"txn3901", b"branch1")
    xid2 = conn.xid(3902, "txn3902", "branch2")
    for count, xid in enumerate([xid1, xid2]):
        conn.tpc_begin(xid)
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:id, 'tesName')
            """,
            id=count,
        )
        conn.tpc_end()
    conn.tpc_rollback(xid1)

    with test_env.assert_raises_full_code("ORA-24756"):
        conn.tpc_prepare(xid1)
    needs_commit = conn.tpc_prepare(xid2)
    if needs_commit:
        conn.tpc_commit(xid2)
    cursor.execute(
        "select IntCol, StringCol1 from TestTempTable order by IntCol"
    )
    assert cursor.fetchall() == [(1, "tesName")]


def test_4404(conn, cursor):
    "4404 - test resuming a transaction"
    cursor.execute("truncate table TestTempTable")
    xid1 = conn.xid(3939, "txn3939", "branch39")
    xid2 = conn.xid(3940, "txn3940", "branch40")
    values = [[xid1, (1, "User Info")], [xid2, (2, "Other User Info")]]
    for xid, data in values:
        conn.tpc_begin(xid)
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            data,
        )
        conn.tpc_end()
    for xid, data in values:
        conn.tpc_begin(xid, oracledb.TPC_BEGIN_RESUME)
        cursor.execute("select IntCol, StringCol1 from TestTempTable")
        (res,) = cursor.fetchall()
        assert res == data
        conn.tpc_rollback(xid)


def test_4405(conn, cursor, test_env):
    "4405 - test promoting a local transaction to a tpc transaction"
    cursor.execute("truncate table TestTempTable")
    xid = conn.xid(3941, "txn3941", "branch41")
    values = (1, "String 1")
    cursor.execute(
        "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)",
        values,
    )
    with test_env.assert_raises_full_code("ORA-24776"):
        conn.tpc_begin(xid)
    conn.tpc_begin(xid, oracledb.TPC_BEGIN_PROMOTE)
    cursor.execute("select IntCol, StringCol1 from TestTempTable")
    (res,) = cursor.fetchall()
    assert res == values
    conn.tpc_rollback(xid)


def test_4406(conn, cursor, test_env):
    "4406 - test ending a transaction with parameter xid"
    cursor.execute("truncate table TestTempTable")
    xid1 = conn.xid(4406, "txn4406a", "branch3")
    xid2 = conn.xid(4406, b"txn4406b", b"branch4")
    conn.tpc_begin(xid1)
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'test4406a')
        """
    )
    conn.tpc_begin(xid2)
    with test_env.assert_raises_full_code("ORA-24758"):
        conn.tpc_end(xid1)
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (2, 'test4406b')
        """
    )
    conn.tpc_end(xid2)
    with test_env.assert_raises_full_code("ORA-25352"):
        conn.tpc_end(xid1)
    conn.tpc_rollback(xid1)
    conn.tpc_rollback(xid2)


def test_4407(conn, cursor):
    "4407 - test tpc_recover()"
    cursor.execute("truncate table TestTempTable")
    n_xids = 10
    for i in range(n_xids):
        xid = conn.xid(4407 + i, f"txn4407{i}", f"branch{i}")
        conn.tpc_begin(xid)
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, 'test4407')
            """,
            [i + 1],
        )
        conn.tpc_prepare(xid)
    recovers = conn.tpc_recover()
    assert len(recovers) == n_xids

    cursor.execute("select * from DBA_PENDING_TRANSACTIONS")
    assert cursor.fetchall() == recovers

    for xid in recovers:
        if xid.format_id % 2 == 0:
            conn.tpc_commit(xid)
    recovers = conn.tpc_recover()
    assert len(recovers) == n_xids // 2

    for xid in recovers:
        conn.tpc_rollback(xid)
    recovers = conn.tpc_recover()
    assert len(recovers) == 0


def test_4408(conn, cursor):
    "4408 - test tpc_recover() with read-only transaction"
    cursor.execute("truncate table TestTempTable")
    for i in range(4):
        xid = conn.xid(4408 + i, f"txn4408{i}", f"branch{i}")
        conn.tpc_begin(xid)
        cursor.execute("select * from TestTempTable")
        conn.tpc_prepare(xid)
    recovers = conn.tpc_recover()
    assert len(recovers) == 0


def test_4409(conn, cursor):
    "4409 - test tpc_commit() with one_phase parameter"
    cursor.execute("truncate table TestTempTable")
    xid = conn.xid(4409, "txn4409", "branch1")
    conn.tpc_begin(xid)
    values = (1, "test4409")
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        values,
    )
    cursor.execute("select IntCol, StringCol1 from TestTempTable")
    conn.tpc_commit(xid, one_phase=True)
    assert cursor.fetchall() == [values]


def test_4410(conn, cursor, test_env):
    "4410 - test negative cases for tpc_commit()"
    cursor.execute("truncate table TestTempTable")
    xid = conn.xid(4410, "txn4410", "branch1")
    conn.tpc_begin(xid)
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'test4410')
        """
    )
    pytest.raises(TypeError, conn.tpc_commit, "invalid xid")
    conn.tpc_prepare(xid)
    with test_env.assert_raises_full_code("ORA-02053"):
        conn.tpc_commit(xid, one_phase=True)
    with test_env.assert_raises_full_code("ORA-24756"):
        conn.tpc_commit(xid)


def test_4411(conn, cursor, test_env):
    "4411 - test starting an already created transaction"
    cursor.execute("truncate table TestTempTable")
    xid = conn.xid(4411, "txn4411", "branch1")
    conn.tpc_begin(xid)
    with test_env.assert_raises_full_code("ORA-24757"):
        conn.tpc_begin(xid, oracledb.TPC_BEGIN_NEW)
    with test_env.assert_raises_full_code("ORA-24797"):
        conn.tpc_begin(xid, oracledb.TPC_BEGIN_PROMOTE)
    conn.tpc_end()
    for flag in [oracledb.TPC_BEGIN_NEW, oracledb.TPC_BEGIN_PROMOTE]:
        with test_env.assert_raises_full_code("ORA-24757"):
            conn.tpc_begin(xid, flag)
    conn.tpc_rollback(xid)


def test_4412(conn, cursor, test_env):
    "4412 - test resuming a prepared transaction"
    cursor.execute("truncate table TestTempTable")
    xid = conn.xid(4412, "txn4412", "branch1")
    conn.tpc_begin(xid)
    conn.tpc_prepare(xid)
    with test_env.assert_raises_full_code("ORA-24756"):
        conn.tpc_begin(xid, oracledb.TPC_BEGIN_RESUME)


def test_4413(conn, cursor, test_env):
    "4413 - test tpc_begin and tpc_end with invalid parameters"
    cursor.execute("truncate table TestTempTable")
    xid = conn.xid(4413, "txn4413", "branch1")
    test_values = [
        (conn.tpc_begin, "DPY-2050"),
        (conn.tpc_end, "DPY-2051"),
    ]
    for tpc_function, error_code in test_values:
        pytest.raises(TypeError, tpc_function, "invalid xid")
        with test_env.assert_raises_full_code(error_code):
            tpc_function(xid, "invalid flag")
        with test_env.assert_raises_full_code(error_code):
            tpc_function(xid, 70)


def test_4414(conn, cursor, test_env):
    "4414 - test commiting transaction without tpc_commit"
    xid = conn.xid(4414, "txn4409", "branch1")
    conn.tpc_begin(xid)
    with test_env.assert_raises_full_code("ORA-02089"):
        cursor.execute("truncate table TestTempTable")


def test_4415(conn, cursor, test_env):
    "4415 - test tpc_commit when a commit is not needed"
    xid = conn.xid(4416, "txn4416", "branch1")
    conn.tpc_begin(xid)
    cursor.execute("select * from TestTempTable")
    conn.tpc_end(xid)
    conn.tpc_prepare(xid)
    with test_env.assert_raises_full_code("ORA-24756"):
        conn.tpc_commit(xid)


def test_4416(conn, cursor):
    "4416 - test transaction_in_progress"
    cursor.execute("truncate table TestTempTable")
    xid = conn.xid(4415, "txn4415", "branch1")
    assert not conn.transaction_in_progress

    conn.tpc_begin(xid)
    assert conn.transaction_in_progress
    cursor.execute("insert into TestTempTable (IntCol) values (2)")

    conn.tpc_end(xid)
    assert not conn.transaction_in_progress

    conn.tpc_prepare(xid)
    assert not conn.transaction_in_progress

    conn.tpc_commit(xid)
    assert not conn.transaction_in_progress
