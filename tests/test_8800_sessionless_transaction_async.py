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
#  test_8800_sessionless_transaction_async.py
#
# Tests for async sessionless transactions using both client API and
# server-side procedures with the DBMS_TRANSACTION package.
# -----------------------------------------------------------------------------

import pytest

TRANSACTION_ID_CLIENT = b"test_8800_client"
TRANSACTION_ID_SERVER = b"test_8800_server"


@pytest.fixture(autouse=True)
def module_checks(
    anyio_backend,
    skip_unless_thin_mode,
    skip_unless_sessionless_transactions_supported,
):
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


async def test_8800(async_cursor, test_env):
    "8800 - test sessionless transaction using client API"
    await async_cursor.execute("truncate table TestTempTable")

    # create sessionless transaction in one connection
    async with test_env.get_connection_async() as conn:

        cursor = conn.cursor()

        # start sessionless transaction
        await conn.begin_sessionless_transaction(
            transaction_id=TRANSACTION_ID_CLIENT,
            timeout=15,
            defer_round_trip=True,
        )

        # insert data within transaction
        await cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (1, "row1"),
        )
        await cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (2, "row2"),
        )

        # suspend the sessionless transaction
        await conn.suspend_sessionless_transaction()

        # ensure data is not visible outside transaction
        await cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert await cursor.fetchall() == []

    # resume the transaction in another connection
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()

        await conn.resume_sessionless_transaction(
            transaction_id=TRANSACTION_ID_CLIENT,
            timeout=5,
            defer_round_trip=True,
        )

        # suspend using suspend_on_success flag with executemany
        await cursor.executemany(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            [(3, "row3")],
            suspend_on_success=True,
        )

        # ensure data is not visible as the transaction is suspended
        await cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert await cursor.fetchall() == []

        # resume the transaction and commit the changes
        await conn.resume_sessionless_transaction(
            transaction_id=TRANSACTION_ID_CLIENT
        )
        await conn.commit()

        # verify data after commit
        await cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert len(await cursor.fetchall()) == 3


async def test_8801(async_cursor, test_env):
    "8801 - test sessionless transaction using server-side procedures"
    await async_cursor.execute("truncate table TestTempTable")

    # create sessionless transaction in one connection
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
        await cursor.execute(
            _get_server_start_stmt("NEW"),
            {"transaction_id": TRANSACTION_ID_SERVER, "timeout": 5},
        )

        # insert data within transaction
        await cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (1, "row1"),
        )

        # Suspend on server
        await cursor.callproc("dbms_transaction.suspend_transaction")

        # verify data is not visible after suspend
        await cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert await cursor.fetchall() == []

    # resume the transaction in another connection
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
        await cursor.execute(
            _get_server_start_stmt("RESUME"),
            {"transaction_id": TRANSACTION_ID_SERVER, "timeout": 5},
        )
        await cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (2, "row2"),
        )
        await conn.commit()

    # verify data after commit in original connection
    await async_cursor.execute("SELECT IntCol, StringCol1 FROM TestTempTable")
    assert len(await async_cursor.fetchall()) == 2


async def test_8802(async_cursor, test_env):
    "8802 - test error conditions with server API sessionless transactions"
    await async_cursor.execute("truncate table TestTempTable")

    # start a transaction via the server; verify that suspension via the
    # client fails but suspension via the server succeeds
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
        await cursor.execute(
            _get_server_start_stmt("NEW"),
            {"transaction_id": TRANSACTION_ID_SERVER, "timeout": 5},
        )
        await cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (1, "server_row"),
        )
        with test_env.assert_raises_full_code("DPY-3034"):
            await conn.suspend_sessionless_transaction()
        await cursor.callproc("dbms_transaction.suspend_transaction")

    # resume on a second connection
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
        await cursor.execute(
            _get_server_start_stmt("RESUME"),
            {"transaction_id": TRANSACTION_ID_SERVER, "timeout": 5},
        )
        await cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (2, "server_row2"),
        )

        # resuming on a different session should fail
        async with test_env.get_connection_async() as other_conn:
            other_cursor = other_conn.cursor()
            with test_env.assert_raises_full_code("ORA-25351"):
                await other_cursor.execute(
                    _get_server_start_stmt("RESUME"),
                    {
                        "transaction_id": TRANSACTION_ID_SERVER,
                        "timeout": 2,
                    },
                )


async def test_8803(async_cursor, test_env):
    "8803 - test rollback of sessionless transaction"
    await async_cursor.execute("truncate table TestTempTable")

    # start and work with sessionless transaction
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
        await conn.begin_sessionless_transaction(
            transaction_id=b"rollback_test", timeout=15
        )
        await cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (1, "rollback_row"),
            suspend_on_success=True,
        )

    # resume in new connection and rollback
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
        await conn.resume_sessionless_transaction(
            transaction_id=b"rollback_test", timeout=5
        )
        await conn.rollback()
        await cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert await cursor.fetchall() == []


async def test_8804(async_cursor, test_env):
    "8804 - test multiple operations within same sessionless transaction"
    await async_cursor.execute("truncate table TestTempTable")

    # start transaction and perform multiple operations
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
        await conn.begin_sessionless_transaction(
            transaction_id=b"multi_ops_test", timeout=15
        )
        await cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (1, "original"),
        )
        await cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (2, "second"),
        )
        await cursor.execute(
            """
            update TestTempTable set StringCol1 = :v1 where IntCol = 1
            """,
            v1="updated",
        )
        await cursor.execute("delete from TestTempTable where IntCol = 2")
        await conn.suspend_sessionless_transaction()
        await cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert await cursor.fetchall() == []

    # resume and commit
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
        await conn.resume_sessionless_transaction(
            transaction_id=b"multi_ops_test", timeout=5
        )
        await conn.commit()
        await cursor.execute("select IntCol, StringCol1 from TestTempTable")
        assert await cursor.fetchall() == [(1, "updated")]


async def test_8805(async_cursor, test_env):
    "8805 - test concurrent sessionless transactions"
    await async_cursor.execute("truncate table TestTempTable")

    # start first sessionless transaction
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
        await conn.begin_sessionless_transaction(
            transaction_id=b"concurrent_1", timeout=15
        )
        await cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (1, "concurrent_1"),
            suspend_on_success=True,
        )

    # start second sessionless transaction in another connection
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
        await conn.begin_sessionless_transaction(
            transaction_id=b"concurrent_2", timeout=15
        )
        await cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (2, "concurrent_2"),
            suspend_on_success=True,
        )

    # resume and commit both transactions
    async with test_env.get_connection_async() as conn:
        await conn.resume_sessionless_transaction(
            transaction_id=b"concurrent_1"
        )
        await conn.commit()
        await conn.resume_sessionless_transaction(
            transaction_id=b"concurrent_2"
        )
        await conn.commit()

    # verify data from both transactions is present
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
        await cursor.execute(
            """
            select IntCol, StringCol1
            from TestTempTable
            order by IntCol
            """
        )
        expected_data = [(1, "concurrent_1"), (2, "concurrent_2")]
        assert await cursor.fetchall() == expected_data


async def test_8806(async_conn, async_cursor, test_env):
    "8806 - test sessionless transaction with large data"
    await async_cursor.execute("delete from TestAllTypes")
    await async_conn.commit()

    # start sessionless transaction and insert large data
    large_string = "X" * 250_000
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
        transaction_id = await conn.begin_sessionless_transaction()
        await cursor.execute(
            """
            insert into TestAllTypes (IntValue, ClobValue)
            values (:1, :2)
            """,
            (1, large_string),
            suspend_on_success=True,
        )

    # resume transaction and commit
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
        await conn.resume_sessionless_transaction(transaction_id)
        await conn.commit()
        await cursor.execute(
            "select ClobValue from TestAllTypes", fetch_lobs=False
        )
        (result,) = await cursor.fetchone()
        assert result == large_string


async def test_8807(async_conn, async_cursor, test_env):
    "8807 - test sessionless transaction with multiple suspends/resumes"
    await async_cursor.execute("truncate table TestTempTable")

    # define data to insert
    data = [
        (1, "first_insert"),
        (2, "second_insert"),
        (3, "third_insert"),
    ]

    # start sessionless transaction and suspend
    transaction_id = await async_conn.begin_sessionless_transaction()
    await async_cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        data[0],
        suspend_on_success=True,
    )

    # resume and insert second row
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
        await conn.resume_sessionless_transaction(transaction_id)
        await cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            data[1],
            suspend_on_success=True,
        )

    # resume and insert third row, then commit
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
        await conn.resume_sessionless_transaction(transaction_id)
        await cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            data[2],
        )
        await conn.commit()

    # verify all data is present
    await async_cursor.execute(
        """
        select IntCol, StringCol1
        from TestTempTable
        order by IntCol
        """
    )
    assert await async_cursor.fetchall() == data


async def test_8808(async_conn, async_cursor, test_env):
    "8808 - Test sessionless transaction with invalid resume attempts"
    await async_cursor.execute("truncate table TestTempTable")

    # start a sessionless transaction
    transaction_id = await async_conn.begin_sessionless_transaction()

    # try to resume with the wrong transaction id
    with test_env.assert_raises_full_code("DPY-3035"):
        await async_conn.resume_sessionless_transaction("wrong_id")

    # try to resume before suspend
    with test_env.assert_raises_full_code("DPY-3035"):
        await async_conn.resume_sessionless_transaction(transaction_id)

    # suspend and resume correctly
    await async_conn.suspend_sessionless_transaction()
    async with test_env.get_connection_async() as conn:
        await conn.resume_sessionless_transaction(transaction_id)


async def test_8809(async_conn, async_cursor):
    "8809 - test getting transaction ID of active sessionless transaction"
    transaction_id = await async_conn.begin_sessionless_transaction()
    await async_cursor.execute("select dbms_transaction.get_transaction_id()")
    (server_transaction_id,) = await async_cursor.fetchone()
    assert server_transaction_id == transaction_id.hex().upper()
    await async_conn.commit()


async def test_8810(async_conn, test_env):
    "8810 - test auto-generated transaction ID uniqueness"

    # start first transaction
    transaction_id_1 = await async_conn.begin_sessionless_transaction()
    await async_conn.suspend_sessionless_transaction()

    # start second transaction
    async with test_env.get_connection_async() as conn:
        transaction_id_2 = await conn.begin_sessionless_transaction()
        await conn.suspend_sessionless_transaction()
        assert transaction_id_1 != transaction_id_2
        await conn.resume_sessionless_transaction(transaction_id_2)
        await conn.rollback()

    # cleanup
    await async_conn.resume_sessionless_transaction(transaction_id_1)
    await async_conn.rollback()


async def test_8811(async_cursor, test_env):
    "8811 - test sessionless transactions with connection pool"
    await async_cursor.execute("truncate table TestTempTable")

    # initialization
    data = [(1, "value 1"), (2, "value 2")]
    pool = test_env.get_pool_async(min=2, max=5)

    # start transaction on first connection
    async with pool.acquire() as conn:
        cursor = conn.cursor()
        transaction_id = await conn.begin_sessionless_transaction()
        await cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            data[0],
            suspend_on_success=True,
        )

    # resume on second connection
    async with pool.acquire() as conn:
        cursor = conn.cursor()
        await conn.resume_sessionless_transaction(transaction_id)
        await cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            data[1],
        )
        await conn.commit()

    # verify data
    async with pool.acquire() as conn:
        cursor = conn.cursor()
        await cursor.execute(
            """
            select IntCol, StringCol1
            from TestTempTable
            order by IntCol
            """
        )
        assert await cursor.fetchall() == data

    await pool.close()


async def test_8812(async_conn, async_cursor, test_env):
    "8812 - Test sessionless transaction with special transaction ids"
    await async_cursor.execute("truncate table TestTempTable")

    # define data to insert
    data = [(1, "long_transaction_id"), (2, "special_chars")]

    # test with long transaction id
    long_transaction_id = b"X" * 64
    await async_conn.begin_sessionless_transaction(long_transaction_id)
    await async_cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        data[0],
        suspend_on_success=True,
    )

    # resume and commit in different connection
    async with test_env.get_connection_async() as conn:
        await conn.resume_sessionless_transaction(long_transaction_id)
        await conn.commit()

    # test with special characters in transaction id
    special_transaction_id = b"SPECIAL@#$%^&*()_+"
    await async_conn.begin_sessionless_transaction(special_transaction_id)
    await async_cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        data[1],
        suspend_on_success=True,
    )

    # resume and commit in different connection
    async with test_env.get_connection_async() as conn:
        await conn.resume_sessionless_transaction(special_transaction_id)
        await conn.commit()

    # verify both transactions committed
    await async_cursor.execute(
        """
        select IntCol, StringCol1
        from TestTempTable
        order by IntCol
        """
    )
    assert await async_cursor.fetchall() == data


async def test_8813(async_conn, test_env):
    "8813 - duplicate transaction id across different connections"
    transaction_id = "test_8813_transaction_id"
    await async_conn.begin_sessionless_transaction(transaction_id)
    async with test_env.get_connection_async() as conn:
        with test_env.assert_raises_full_code("ORA-26217"):
            await conn.begin_sessionless_transaction(transaction_id)


async def test_8814(async_conn, test_env):
    "8814 - zero timeout behaviour in resume"
    transaction_id = await async_conn.begin_sessionless_transaction()
    async with test_env.get_connection_async() as conn:
        with test_env.assert_raises_full_code("ORA-25351"):
            await conn.resume_sessionless_transaction(
                transaction_id, timeout=0
            )

    # suspend transaction on first session, and resume will now succeed
    await async_conn.suspend_sessionless_transaction()
    async with test_env.get_connection_async() as conn:
        await conn.resume_sessionless_transaction(transaction_id, timeout=0)
        await conn.rollback()


async def test_8815(async_conn, async_cursor, test_env):
    "8815 - transaction behaviour with DDL operations"

    # create temp table
    temp_table_name = "temp_test_8815"
    await async_cursor.execute(f"drop table if exists {temp_table_name}")
    await async_cursor.execute(
        f"""
        create table {temp_table_name} (
            id number,
            data varchar2(50)
        )"""
    )

    # beging sessionless transaction and perform DDL which performs an
    # implicit commit
    await async_conn.begin_sessionless_transaction()
    await async_cursor.execute(
        f"alter table {temp_table_name} add temp_col varchar2(20)"
    )

    # further DML operations are part of a local transaction
    local_data = (1, "LOCAL_TRANSACTION", "abc")
    await async_cursor.execute(
        f"insert into {temp_table_name} values (:1, :2, :3)",
        local_data,
    )

    # suspend will fail now as a local transaction is active and only
    # sessionless transactions are suspendable
    with test_env.assert_raises_full_code("DPY-3036"):
        await async_cursor.execute(
            f"""
            insert into {temp_table_name}
            values (2, 'LOCAL_TRANSACTION', 'def')
            """,
            suspend_on_success=True,
        )

    # verify data from local transaction is all that is present
    await async_cursor.execute(f"select * from {temp_table_name}")
    assert await async_cursor.fetchall() == [local_data]

    # drop temp table
    await async_cursor.execute(f"drop table {temp_table_name} purge")


async def test_8816(test_env):
    "8816 - test suspend_on_success with batch_size < total rows inserted"
    async with test_env.get_connection_async() as conn:
        cursor = conn.cursor()
        await cursor.execute("truncate table TestTempTable")
        rows = [(i + 1, f"String for row {i + 1}") for i in range(200)]
        await conn.begin_sessionless_transaction(
            transaction_id=TRANSACTION_ID_CLIENT,
            timeout=5,
            defer_round_trip=True,
        )
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        with test_env.assert_raises_full_code("DPY-3036"):
            await cursor.executemany(
                sql, rows, batch_size=75, suspend_on_success=True
            )
    async with test_env.get_connection_async() as conn:
        await conn.resume_sessionless_transaction(TRANSACTION_ID_CLIENT)
