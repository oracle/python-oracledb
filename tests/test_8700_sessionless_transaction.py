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

# -----------------------------------------------------------------------------
#  test_8700_sessionless_transaction.py
#
# Tests for sessionless transactions using both client API and server-side
# procedures with DBMS_TRANSACTION package.
# -----------------------------------------------------------------------------

import pytest

TRANSACTION_ID_CLIENT = b"test_8700_client"
TRANSACTION_ID_SERVER = b"test_8700_server"


@pytest.fixture(autouse=True)
def module_checks(skip_unless_sessionless_transactions_supported):
    pass


def _get_server_start_stmt(mode):
    "Generate server-side transaction start statement"
    return f"""
    DECLARE
        transaction_id RAW(128);
    BEGIN
        transaction_id := DBMS_TRANSACTION.START_TRANSACTION(
            :transaction_id,
            DBMS_TRANSACTION.TRANSACTION_TYPE_SESSIONLESS,
            :timeout,
            DBMS_TRANSACTION.TRANSACTION_{mode}
        );
    END;"""


def test_8700(cursor, test_env):
    "8700 - test sessionless transaction using client API"
    cursor.execute("truncate table TestTempTable")

    # create sessionless transaction in one connection
    with test_env.get_connection() as conn:

        cursor = conn.cursor()

        # start sessionless transaction
        conn.begin_sessionless_transaction(
            transaction_id=TRANSACTION_ID_CLIENT,
            timeout=15,
            defer_round_trip=True,
        )

        # insert data within transaction
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (1, "row1"),
        )
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (2, "row2"),
        )

        # suspend the sessionless transaction
        conn.suspend_sessionless_transaction()

        # ensure data is not visible outside transaction
        cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert cursor.fetchall() == []

    # resume the transaction in another connection
    with test_env.get_connection() as conn:
        cursor = conn.cursor()

        conn.resume_sessionless_transaction(
            transaction_id=TRANSACTION_ID_CLIENT,
            timeout=5,
            defer_round_trip=True,
        )

        # suspend using suspend_on_success flag with executemany
        cursor.executemany(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            [(3, "row3")],
            suspend_on_success=True,
        )

        # ensure data is not visible as the transaction is suspended
        cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert cursor.fetchall() == []

        # resume the transaction and commit the changes
        conn.resume_sessionless_transaction(
            transaction_id=TRANSACTION_ID_CLIENT
        )
        conn.commit()

        # verify data after commit
        cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert len(cursor.fetchall()) == 3


def test_8701(conn, test_env):
    "8701 - test sessionless transaction using server-side procedures"
    base_cursor = conn.cursor()
    base_cursor.execute("truncate table TestTempTable")

    # create sessionless transaction in one connection
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            _get_server_start_stmt("NEW"),
            {"transaction_id": TRANSACTION_ID_SERVER, "timeout": 5},
        )

        # insert data within transaction
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (1, "row1"),
        )

        # Suspend on server
        cursor.callproc("dbms_transaction.suspend_transaction")

        # verify data is not visible after suspend
        cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert cursor.fetchall() == []

    # resume the transaction in another connection
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            _get_server_start_stmt("RESUME"),
            {"transaction_id": TRANSACTION_ID_SERVER, "timeout": 5},
        )
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (2, "row2"),
        )
        conn.commit()

    # verify data after commit in original connection
    base_cursor.execute("SELECT IntCol, StringCol1 FROM TestTempTable")
    assert len(base_cursor.fetchall()) == 2


def test_8702(cursor, test_env):
    "8702 - test error conditions with server API sessionless transactions"
    cursor.execute("truncate table TestTempTable")

    # start a transaction via the server; verify that suspension via the
    # client fails but suspension via the server succeeds
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            _get_server_start_stmt("NEW"),
            {"transaction_id": TRANSACTION_ID_SERVER, "timeout": 5},
        )
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (1, "server_row"),
        )
        with test_env.assert_raises_full_code("DPY-3034"):
            conn.suspend_sessionless_transaction()
        cursor.callproc("dbms_transaction.suspend_transaction")

    # resume on a second connection
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            _get_server_start_stmt("RESUME"),
            {"transaction_id": TRANSACTION_ID_SERVER, "timeout": 5},
        )
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (2, "server_row2"),
        )

        # resuming on a different session should fail
        with test_env.get_connection() as other_conn:
            other_cursor = other_conn.cursor()
            with test_env.assert_raises_full_code("ORA-25351"):
                other_cursor.execute(
                    _get_server_start_stmt("RESUME"),
                    {
                        "transaction_id": TRANSACTION_ID_SERVER,
                        "timeout": 2,
                    },
                )


def test_8703(cursor, test_env):
    "8703 - test rollback of sessionless transaction"
    cursor.execute("truncate table TestTempTable")

    # start and work with sessionless transaction
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        conn.begin_sessionless_transaction(
            transaction_id=b"rollback_test", timeout=15
        )
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (1, "rollback_row"),
            suspend_on_success=True,
        )

    # resume in new connection and rollback
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        conn.resume_sessionless_transaction(
            transaction_id=b"rollback_test", timeout=5
        )
        conn.rollback()
        cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert cursor.fetchall() == []


def test_8704(cursor, test_env):
    "8704 - test multiple operations within same sessionless transaction"
    cursor.execute("truncate table TestTempTable")

    # start transaction and perform multiple operations
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        conn.begin_sessionless_transaction(
            transaction_id=b"multi_ops_test", timeout=15
        )
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (1, "original"),
        )
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (2, "second"),
        )
        cursor.execute(
            """
            update TestTempTable set StringCol1 = :v1 where IntCol = 1
            """,
            v1="updated",
        )
        cursor.execute("delete from TestTempTable where IntCol = 2")
        conn.suspend_sessionless_transaction()
        cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert cursor.fetchall() == []

    # resume and commit
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        conn.resume_sessionless_transaction(
            transaction_id=b"multi_ops_test", timeout=5
        )
        conn.commit()
        cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert cursor.fetchall() == [(1, "updated")]


def test_8705(cursor, test_env):
    "8705 - test concurrent sessionless transactions"
    cursor.execute("truncate table TestTempTable")

    # start first sessionless transaction
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        conn.begin_sessionless_transaction(
            transaction_id=b"concurrent_1", timeout=15
        )
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (1, "concurrent_1"),
            suspend_on_success=True,
        )

    # start second sessionless transaction in another connection
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        conn.begin_sessionless_transaction(
            transaction_id=b"concurrent_2", timeout=15
        )
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (2, "concurrent_2"),
            suspend_on_success=True,
        )

    # resume and commit both transactions
    with test_env.get_connection() as conn:
        conn.resume_sessionless_transaction(transaction_id=b"concurrent_1")
        conn.commit()
        conn.resume_sessionless_transaction(transaction_id=b"concurrent_2")
        conn.commit()

    # verify data from both transactions is present
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            select IntCol, StringCol1
            from TestTempTable
            order by IntCol
            """
        )
        expected_data = [(1, "concurrent_1"), (2, "concurrent_2")]
        assert cursor.fetchall() == expected_data


def test_8706(conn, cursor, test_env):
    "8706 - test sessionless transaction with large data"
    cursor.execute("delete from TestAllTypes")
    conn.commit()

    # start sessionless transaction and insert large data
    large_string = "X" * 250_000
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        transaction_id = conn.begin_sessionless_transaction()
        cursor.execute(
            """
            insert into TestAllTypes (IntValue, ClobValue)
            values (:1, :2)
            """,
            (1, large_string),
            suspend_on_success=True,
        )

    # resume transaction and commit
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        conn.resume_sessionless_transaction(transaction_id)
        conn.commit()
        cursor.execute("select ClobValue from TestAllTypes", fetch_lobs=False)
        (result,) = cursor.fetchone()
        assert result == large_string


def test_8707(conn, test_env):
    "8707 - test sessionless transaction with multiple suspends/resumes"
    base_cursor = conn.cursor()
    base_cursor.execute("truncate table TestTempTable")

    # define data to insert
    data = [
        (1, "first_insert"),
        (2, "second_insert"),
        (3, "third_insert"),
    ]

    # start sessionless transaction and suspend
    transaction_id = conn.begin_sessionless_transaction()
    base_cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        data[0],
        suspend_on_success=True,
    )

    # resume and insert second row
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        conn.resume_sessionless_transaction(transaction_id)
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            data[1],
            suspend_on_success=True,
        )

    # resume and insert third row, then commit
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        conn.resume_sessionless_transaction(transaction_id)
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            data[2],
        )
        conn.commit()

    # verify all data is present
    base_cursor.execute(
        """
        select IntCol, StringCol1
        from TestTempTable
        order by IntCol
        """
    )
    assert base_cursor.fetchall() == data


def test_8708(conn, cursor, test_env):
    "8708 - Test sessionless transaction with invalid resume attempts"
    cursor.execute("truncate table TestTempTable")

    # start a sessionless transaction
    transaction_id = conn.begin_sessionless_transaction()

    # try to resume with the wrong transaction id
    if conn.thin:
        with test_env.assert_raises_full_code("DPY-3035"):
            conn.resume_sessionless_transaction("wrong_id")

    # try to resume before suspend
    if conn.thin:
        with test_env.assert_raises_full_code("DPY-3035"):
            conn.resume_sessionless_transaction(transaction_id)

    # suspend and resume correctly
    conn.suspend_sessionless_transaction()
    with test_env.get_connection() as other_conn:
        other_conn.resume_sessionless_transaction(transaction_id)


def test_8709(conn, cursor):
    "8709 - test getting transaction ID of active sessionless transaction"
    transaction_id = conn.begin_sessionless_transaction()
    cursor.execute("select dbms_transaction.get_transaction_id()")
    (server_transaction_id,) = cursor.fetchone()
    assert server_transaction_id == transaction_id.hex().upper()
    conn.commit()


def test_8710(conn, test_env):
    "8710 - test auto-generated transaction ID uniqueness"

    # start first transaction
    transaction_id_1 = conn.begin_sessionless_transaction()
    conn.suspend_sessionless_transaction()

    # start second transaction
    with test_env.get_connection() as other_conn:
        transaction_id_2 = other_conn.begin_sessionless_transaction()
        other_conn.suspend_sessionless_transaction()
        assert transaction_id_1 != transaction_id_2
        other_conn.resume_sessionless_transaction(transaction_id_2)
        other_conn.rollback()

    # cleanup
    conn.resume_sessionless_transaction(transaction_id_1)
    conn.rollback()


def test_8711(cursor, test_env):
    "8711 - test sessionless transactions with connection pool"
    cursor.execute("truncate table TestTempTable")

    # initialization
    data = [(1, "value 1"), (2, "value 2")]
    pool = test_env.get_pool(min=2, max=5)

    # start transaction on first connection
    with pool.acquire() as conn:
        cursor = conn.cursor()
        transaction_id = conn.begin_sessionless_transaction()
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            data[0],
            suspend_on_success=True,
        )

    # resume on second connection
    with pool.acquire() as conn:
        cursor = conn.cursor()
        conn.resume_sessionless_transaction(transaction_id)
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            data[1],
        )
        conn.commit()

    # verify data
    with pool.acquire() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            select IntCol, StringCol1
            from TestTempTable
            order by IntCol
            """
        )
        assert cursor.fetchall() == data

    pool.close()


def test_8712(conn, cursor, test_env):
    "8712 - Test sessionless transaction with special transaction ids"
    cursor.execute("truncate table TestTempTable")

    # define data to insert
    data = [(1, "long_transaction_id"), (2, "special_chars")]

    # test with long transaction id
    long_transaction_id = b"X" * 64
    conn.begin_sessionless_transaction(long_transaction_id)
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        data[0],
        suspend_on_success=True,
    )

    # resume and commit in different connection
    with test_env.get_connection() as other_conn:
        other_conn.resume_sessionless_transaction(long_transaction_id)
        other_conn.commit()

    # test with special characters in transaction id
    special_transaction_id = b"SPECIAL@#$%^&*()_+"
    conn.begin_sessionless_transaction(special_transaction_id)
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        data[1],
        suspend_on_success=True,
    )

    # resume and commit in different connection
    with test_env.get_connection() as other_conn:
        other_conn.resume_sessionless_transaction(special_transaction_id)
        other_conn.commit()

    # verify both transactions committed
    cursor.execute(
        """
        select IntCol, StringCol1
        from TestTempTable
        order by IntCol
        """
    )
    assert cursor.fetchall() == data


def test_8713(conn, test_env):
    "8713 - duplicate transaction id across different connections"
    transaction_id = "test_8713_transaction_id"
    conn.begin_sessionless_transaction(transaction_id)
    with test_env.get_connection() as conn:
        with test_env.assert_raises_full_code("ORA-26217"):
            conn.begin_sessionless_transaction(transaction_id)


def test_8714(conn, test_env):
    "8714 - zero timeout behaviour in resume"
    transaction_id = conn.begin_sessionless_transaction()
    with test_env.get_connection() as other_conn:
        with test_env.assert_raises_full_code("ORA-25351"):
            other_conn.resume_sessionless_transaction(
                transaction_id, timeout=0
            )

    # suspend transaction on first session, and resume will now succeed
    conn.suspend_sessionless_transaction()
    with test_env.get_connection() as conn:
        conn.resume_sessionless_transaction(transaction_id, timeout=0)
        conn.rollback()


def test_8715(conn, cursor, test_env):
    "8715 - transaction behaviour with DDL operations"

    # create temp table
    temp_table_name = "temp_test_8715"
    cursor.execute(f"drop table if exists {temp_table_name}")
    cursor.execute(
        f"""
        create table {temp_table_name} (
            id number,
            data varchar2(50)
        )"""
    )

    # beging sessionless transaction and perform DDL which performs an
    # implicit commit
    conn.begin_sessionless_transaction()
    cursor.execute(f"alter table {temp_table_name} add temp_col varchar2(20)")

    # further DML operations are part of a local transaction
    local_data = (1, "LOCAL_TRANSACTION", "abc")
    cursor.execute(
        f"insert into {temp_table_name} values (:1, :2, :3)",
        local_data,
    )

    # suspend will fail now as a local transaction is active and only
    # sessionless transactions are suspendable
    with test_env.assert_raises_full_code("DPY-3036"):
        cursor.execute(
            f"""
            insert into {temp_table_name}
            values (2, 'LOCAL_TRANSACTION', 'def')
            """,
            suspend_on_success=True,
        )

    # verify data from local transaction is all that is present
    cursor.execute(f"select * from {temp_table_name}")
    assert cursor.fetchall() == [local_data]

    # drop temp table
    cursor.execute(f"drop table {temp_table_name} purge")


def test_8716(test_env):
    "8716 - test suspend_on_success with batch_size < total rows inserted"
    with test_env.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("truncate table TestTempTable")
        rows = [(i + 1, f"String for row {i + 1}") for i in range(200)]
        conn.begin_sessionless_transaction(
            transaction_id=TRANSACTION_ID_CLIENT,
            timeout=5,
            defer_round_trip=True,
        )
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        with test_env.assert_raises_full_code("DPY-3036"):
            cursor.executemany(
                sql, rows, batch_size=75, suspend_on_success=True
            )
    with test_env.get_connection() as conn:
        conn.resume_sessionless_transaction(TRANSACTION_ID_CLIENT)
