# -----------------------------------------------------------------------------
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
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
5500 - Module for testing pools with asyncio
"""

import asyncio

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


async def _connect_and_drop(pool):
    async with pool.acquire() as conn:
        cursor = conn.cursor()
        await cursor.execute("select count(*) from TestNumbers")
        (count,) = await cursor.fetchone()
        assert count == 10


async def _connect_and_generate_error(test_env, pool):
    async with pool.acquire() as conn:
        cursor = conn.cursor()
        with test_env.assert_raises_full_code("ORA-01476"):
            await cursor.execute("select 1 / 0 from dual")


async def _verify_connection(
    connection, expected_user, expected_proxy_user=None
):
    cursor = connection.cursor()
    await cursor.execute(
        """
        select
            sys_context('userenv', 'session_user'),
            sys_context('userenv', 'proxy_user')
        from dual
        """
    )
    actual_user, actual_proxy_user = await cursor.fetchone()
    assert actual_user == expected_user.upper()
    if expected_proxy_user is not None:
        expected_proxy_user = expected_proxy_user.upper()
    assert actual_proxy_user == expected_proxy_user
    await connection.close()


async def _verify_create_arg(test_env, arg_name, arg_value, sql):
    args = {}
    args[arg_name] = arg_value
    pool = test_env.get_pool_async(**args)
    async with pool.acquire() as conn:
        cursor = conn.cursor()
        await cursor.execute(sql)
        (fetched_value,) = await cursor.fetchone()
        assert fetched_value == arg_value
    await pool.close()


async def test_5500(test_env):
    "5500 - test getting default pool parameters"
    pool = test_env.get_pool_async()
    try:
        assert pool.busy == 0
        assert pool.dsn == test_env.connect_string
        assert pool.getmode == oracledb.POOL_GETMODE_WAIT
        assert pool.homogeneous
        assert pool.increment == 1
        assert pool.max == 2
        assert pool.max_lifetime_session == 0
        assert pool.min == 1
        assert pool.ping_interval == 60
        assert pool.stmtcachesize == oracledb.defaults.stmtcachesize
        assert pool.thin
        assert pool.timeout == 0
        assert pool.username == test_env.main_user
    finally:
        await pool.close(force=True)


async def test_5501(test_env):
    "5501 - test setting pool attributes"
    pool = test_env.get_pool_async()
    test_values = [
        ((11, 2), "ping_interval", 30),
        ((11, 2), "stmtcachesize", 100),
        ((11, 2), "timeout", 10),
        ((12, 2), "getmode", oracledb.POOL_GETMODE_TIMEDWAIT),
        ((12, 1), "max_lifetime_session", 3),
    ]
    try:
        for version, attr_name, value in test_values:
            setattr(pool, attr_name, value)
            assert getattr(pool, attr_name) == value
            pytest.raises(TypeError, setattr, pool, attr_name, "invalid value")
    finally:
        await pool.close(force=True)


async def test_5502(test_env):
    "5502 - connection rolls back before released back to the pool"
    pool = test_env.get_pool_async()
    conn = await pool.acquire()
    cursor = conn.cursor()
    await cursor.execute("truncate table TestTempTable")
    await cursor.execute("insert into TestTempTable (IntCol) values (1)")
    cursor.close()
    await pool.release(conn)
    pool = test_env.get_pool_async()
    conn = await pool.acquire()
    cursor = conn.cursor()
    await cursor.execute("select count(*) from TestTempTable")
    (count,) = await cursor.fetchone()
    assert count == 0
    await conn.close()


async def test_5503(test_env):
    "5503 - test session pool with multiple coroutines"
    pool = test_env.get_pool_async(min=5, max=20, increment=2)
    try:
        coroutines = [_connect_and_drop(pool) for i in range(20)]
        await asyncio.gather(*coroutines)
    finally:
        await pool.close(force=True)


async def test_5504(test_env):
    "5504 - test session pool with multiple coroutines (with errors)"
    pool = test_env.get_pool_async(min=5, max=20, increment=2)
    try:
        coroutines = [
            _connect_and_generate_error(test_env, pool) for i in range(20)
        ]
        await asyncio.gather(*coroutines)
    finally:
        await pool.close(force=True)


async def test_5505(skip_if_drcp, test_env):
    "5505 - test session pool with various types of purity"
    pool = test_env.get_pool_async(min=1, max=8, increment=1)

    # get connection and set the action
    action = "TEST_ACTION"
    conn = await pool.acquire()
    conn.action = action
    cursor = conn.cursor()
    await cursor.execute("select 1 from dual")
    cursor.close()
    await pool.release(conn)
    assert pool.opened == 1, "opened (1)"

    # verify that the connection still has the action set on it
    conn = await pool.acquire()
    cursor = conn.cursor()
    await cursor.execute("select sys_context('userenv', 'action') from dual")
    (result,) = await cursor.fetchone()
    assert result == action
    cursor.close()
    await pool.release(conn)
    assert pool.opened == 1, "opened (2)"

    # get a new connection with new purity (should not have state)
    conn = await pool.acquire(purity=oracledb.PURITY_NEW)
    cursor = conn.cursor()
    await cursor.execute("select sys_context('userenv', 'action') from dual")
    (result,) = await cursor.fetchone()
    assert result is None
    cursor.close()
    await pool.release(conn)


async def test_5506(test_env):
    "5506 - test dropping/closing a connection from the pool"
    pool = test_env.get_pool_async(min=1, max=5, increment=2)
    try:
        conns1 = [await pool.acquire() for _ in range(2)]
        conns2 = [await oracledb.connect_async(pool=pool) for _ in range(3)]
        assert pool.busy == 5
        assert pool.opened == 5

        for conn in conns1:
            await pool.drop(conn)
        assert pool.busy == 3
        assert pool.opened == 3

        for conn in conns2:
            await conn.close()
        assert pool.busy == 0
        assert pool.opened == 3
    finally:
        await pool.close(force=True)


async def test_5507(test_env):
    "5507 - test to ensure pure connections are being created correctly"
    pool = test_env.get_pool_async(min=1, max=2, increment=1)
    try:
        conn1 = await pool.acquire()
        conn2 = await pool.acquire()
        assert pool.opened == 2, "opened (1)"
        await pool.release(conn1)
        await pool.release(conn2)
        conn3 = await pool.acquire(purity=oracledb.PURITY_NEW)
        assert pool.opened == 2, "opened (2)"
        await pool.release(conn3)
    finally:
        await pool.close(force=True)


async def test_5508(test_env):
    "5508 - test closing a pool normally with no connections checked out"
    pool = test_env.get_pool_async(min=1, max=8, increment=1)
    await pool.close()


async def test_5509(test_env):
    "5509 - test closing a pool normally with connections checked out"
    pool = test_env.get_pool_async(min=1, max=8, increment=1)
    closed = False
    try:
        async with pool.acquire():
            with test_env.assert_raises_full_code("DPY-1005"):
                await pool.close()
                closed = True
    finally:
        if not closed:
            await pool.close(force=True)


async def test_5510(test_env):
    "5510 - test closing a pool forcibly"
    pool = test_env.get_pool_async(min=1, max=8, increment=1)
    async with pool.acquire():
        await pool.close(force=True)


async def test_5511(test_env):
    "5511 - using the pool after it is closed raises an exception"
    pool = test_env.get_pool_async(min=1, max=8, increment=1)
    await pool.close()
    with test_env.assert_raises_full_code("DPY-1002"):
        await pool.acquire()


async def test_5512(test_env):
    "5512 - using the pool beyond max limit raises an error"
    pool = test_env.get_pool_async(min=1, max=2, increment=1)
    try:
        async with pool.acquire(), pool.acquire():
            pool.getmode = oracledb.POOL_GETMODE_NOWAIT
            with test_env.assert_raises_full_code("DPY-4005"):
                await pool.acquire()
    finally:
        await pool.close(force=True)


async def test_5513(test_env):
    "5513 - callable session callback is executed for new connections"

    class Counter:
        num_calls = 0

        @classmethod
        async def session_callback(cls, conn, requested_tag):
            cls.num_calls += 1

    pool = test_env.get_pool_async(
        min=1,
        max=2,
        increment=1,
        session_callback=Counter.session_callback,
    )
    try:
        async with pool.acquire(), pool.acquire():
            pass
        async with pool.acquire(), pool.acquire():
            pass
        assert Counter.num_calls == 2
    finally:
        await pool.close(force=True)


async def test_5514(skip_if_drcp, test_env):
    "5514 - drop the pooled connection on receiving dead connection error"
    admin_conn = await test_env.get_admin_connection_async()
    pool = test_env.get_pool_async(min=2, max=2, increment=2)
    try:

        # acquire connections from the pool and kill all the sessions
        with admin_conn.cursor() as admin_cursor:
            for conn in [await pool.acquire() for i in range(2)]:
                sid, serial = conn.session_id, conn.serial_num
                sql = f"alter system kill session '{sid},{serial}'"
                await admin_cursor.execute(sql)
                await conn.close()
        assert pool.opened == 2

        # when try to re-use the killed sessions error will be raised;
        # release all such connections
        for conn in [await pool.acquire() for i in range(2)]:
            with conn.cursor() as cursor:
                with test_env.assert_raises_full_code("DPY-4011"):
                    await cursor.execute("select user from dual")
            await conn.close()

        # if a free connection is available, it can be used; otherwise a
        # new connection will be created
        for conn in [await pool.acquire() for i in range(2)]:
            with conn.cursor() as cursor:
                await cursor.execute("select user from dual")
                (user,) = await cursor.fetchone()
                assert user == test_env.main_user.upper()
            await conn.close()
        assert pool.opened == 2
    finally:
        await pool.close(force=True)


async def test_5515(test_env):
    "5515 - acquire a connection from an empty pool (min=0)"
    pool = test_env.get_pool_async(min=0, max=2, increment=2)
    try:
        async with pool.acquire() as conn:
            with conn.cursor() as cursor:
                await cursor.execute("select user from dual")
                (result,) = await cursor.fetchone()
                assert result == test_env.main_user.upper()
    finally:
        await pool.close(force=True)


async def test_5516(test_env):
    "5516 - get different object types from different connections"
    pool = test_env.get_pool_async(min=1, max=2, increment=1)
    try:
        async with pool.acquire() as conn:
            typ = await conn.gettype("UDT_SUBOBJECT")
            assert typ.name == "UDT_SUBOBJECT"
        async with pool.acquire() as conn:
            typ = await conn.gettype("UDT_OBJECTARRAY")
            assert typ.name == "UDT_OBJECTARRAY"
    finally:
        await pool.close(force=True)


async def test_5517(test_env):
    "5517 - test creating a pool using a proxy user"
    user_str = f"{test_env.main_user}[{test_env.proxy_user}]"
    pool = test_env.get_pool_async(user=user_str)
    try:
        await _verify_connection(
            await pool.acquire(),
            test_env.proxy_user,
            test_env.main_user,
        )
    finally:
        await pool.close(force=True)


async def test_5518(skip_if_drcp, test_env):
    "5518 - test acquiring conn from pool in LIFO order"
    pool = test_env.get_pool_async(min=5, max=10, increment=1)
    try:
        sql = "select sys_context('userenv', 'sid') from dual"
        conns = [await pool.acquire() for i in range(3)]
        sids = []
        for conn in conns:
            with conn.cursor() as cursor:
                await cursor.execute(sql)
                (sid,) = await cursor.fetchone()
                sids.append(sid)
        await conns[1].close()
        await conns[2].close()
        await conns[0].close()

        async with pool.acquire() as conn:
            with conn.cursor() as cursor:
                await cursor.execute(sql)
                (sid,) = await cursor.fetchone()
                assert sid == sids[0], "not LIFO"
    finally:
        await pool.close(force=True)


async def test_5519(test_env):
    "5519 - verify that dynamic pool cannot have an increment of zero"
    pool = test_env.get_pool_async(min=1, max=3, increment=0)
    try:
        assert pool.increment == 1
        async with pool.acquire(), pool.acquire():
            pass
    finally:
        await pool.close(force=True)


async def test_5520(test_env):
    "5520 - verify that static pool can have an increment of zero"
    pool = test_env.get_pool_async(min=1, max=1, increment=0)
    try:
        assert pool.increment == 0
        async with pool.acquire():
            pass
    finally:
        await pool.close(force=True)


async def test_5521(test_env):
    "5521 - verify that connection with different cclass is reused"
    cclass = "cclass2431"
    pool = test_env.get_pool_async(min=1, max=1)
    # ignore the first acquire which, depending on the speed with which the
    # minimum connections are created, may create a connection that is
    # discarded; instead, use the second acquire which should remain in the
    # pool
    try:
        async with pool.acquire(cclass=cclass) as conn:
            pass
        async with pool.acquire(cclass=cclass) as conn:
            sid_serial = (conn.session_id, conn.serial_num)
        async with pool.acquire(cclass=cclass) as conn:
            next_sid_serial = (conn.session_id, conn.serial_num)
            assert next_sid_serial == sid_serial
        assert pool.opened == 1
    finally:
        await pool.close(force=True)


async def test_5522(test_env):
    "5522 - test creating a pool invalid params"
    with test_env.assert_raises_full_code("DPY-2027"):
        oracledb.create_pool_async(params="bad params")


async def test_5523(test_env):
    "5523 - test releasing and dropping an invalid connection"
    pool = test_env.get_pool_async()
    try:
        with pytest.raises(TypeError):
            await pool.release("invalid connection")
        with pytest.raises(TypeError):
            await pool.drop("invalid connection")
    finally:
        await pool.close(force=True)


async def test_5524(test_env):
    "5524 - test creating a pool with invalid pool_class"
    with test_env.assert_raises_full_code("DPY-2026"):
        oracledb.create_pool_async(pool_class=int)


async def test_5525(test_env):
    "5525 - test creating a pool with a subclassed connection type"

    class MyConnection(oracledb.AsyncConnection):
        pass

    pool = test_env.get_pool_async(connectiontype=MyConnection)
    async with pool.acquire() as conn:
        assert isinstance(conn, MyConnection)


async def test_5526(test_env):
    "5526 - test creating a pool with a subclassed pool type"

    class MyPool(oracledb.AsyncConnectionPool):
        pass

    pool = test_env.get_pool_async(pool_class=MyPool)
    try:
        assert isinstance(pool, MyPool)
    finally:
        await pool.close(force=True)


async def test_5527(test_env):
    "5527 - test connectiontype with an invalid connection class"
    with test_env.assert_raises_full_code("DPY-2023"):
        test_env.get_pool_async(connectiontype=oracledb.Connection)
    with test_env.assert_raises_full_code("DPY-2023"):
        test_env.get_pool_async(connectiontype=int)


async def test_5528(skip_unless_pool_timed_wait_supported, test_env):
    "5528 - ensure that timed wait times out with appropriate exception"
    pool = test_env.get_pool_async(
        getmode=oracledb.POOL_GETMODE_TIMEDWAIT, min=0, wait_timeout=1
    )
    with test_env.assert_raises_full_code("DPY-4005"):
        await pool.acquire()


async def test_5529(test_env):
    "5529 - ensure call timeout is reset on connections returned by pool"
    pool = test_env.get_pool_async(ping_timeout=1000, ping_interval=0)
    async with pool.acquire() as conn:
        assert conn.call_timeout == 0
    async with pool.acquire() as conn:
        assert conn.call_timeout == 0


async def test_5530(test_env):
    "5530 - test passing program when creating a pool"
    sql = (
        "select program from v$session "
        "where sid = sys_context('userenv', 'sid')"
    )
    await _verify_create_arg(test_env, "program", "newprogram", sql)


async def test_5531(test_env):
    "5531 - test passing machine when creating a pool"
    sql = (
        "select machine from v$session "
        "where sid = sys_context('userenv', 'sid')"
    )
    await _verify_create_arg(test_env, "machine", "newmachine", sql)


async def test_5532(test_env):
    "5532 - test passing terminal when creating a pool"
    sql = (
        "select terminal from v$session "
        "where sid = sys_context('userenv', 'sid')"
    )
    await _verify_create_arg(test_env, "terminal", "newterminal", sql)


async def test_5533(test_env):
    "5533 - test passing osuser when creating a pool"
    sql = (
        "select osuser from v$session "
        "where sid = sys_context('userenv', 'sid')"
    )
    await _verify_create_arg(test_env, "osuser", "newosuser", sql)


async def test_5534(test_env):
    "5534 - test passing driver_name when creating a pool"
    sql = (
        "select distinct client_driver from v$session_connect_info "
        "where sid = sys_context('userenv', 'sid')"
    )
    await _verify_create_arg(test_env, "driver_name", "newdriver", sql)


async def test_5535(test_env):
    "5535 - test register_parameter with pooled connection"
    sdu = 4096
    params = test_env.get_pool_params()
    protocol = "proto-test"
    orig_connect_string = test_env.connect_string
    connect_string = f"{protocol}://{orig_connect_string}"

    def hook(passed_protocol, passed_protocol_arg, passed_params):
        assert passed_protocol == protocol
        assert passed_protocol_arg == orig_connect_string
        passed_params.parse_connect_string(passed_protocol_arg)
        passed_params.set(sdu=sdu)

    try:
        oracledb.register_protocol(protocol, hook)
        pool = oracledb.create_pool_async(dsn=connect_string, params=params)
        assert params.sdu == sdu
        async with pool.acquire():
            pass
        await pool.close()
    finally:
        oracledb.register_protocol(protocol, None)


async def test_5536(test_env):
    "5536 - test create_pool() with edition"
    edition = test_env.edition_name
    pool = test_env.get_pool_async(edition=edition)
    async with pool.acquire() as conn:
        assert conn.edition == edition
    await pool.close()


async def test_5537(test_env):
    "5537 - test create_pool() and get_pool() with alias"
    alias = "pool_alias_5537"
    pool = test_env.get_pool_async(pool_alias=alias)
    assert pool is oracledb.get_pool(alias)
    await pool.close()


async def test_5538(test_env):
    "5538 - test create_pool() twice with the same alias"
    alias = "pool_alias_5538"
    pool = test_env.get_pool_async(pool_alias=alias)
    with test_env.assert_raises_full_code("DPY-2055"):
        test_env.get_pool_async(pool_alias=alias)
    await pool.close()
    assert oracledb.get_pool(alias) is None


async def test_5539(test_env):
    "5539 - test acquire() with pool alias and stmtcachesize"
    alias = "pool_5539"
    stmtcachesize = 35
    test_env.get_pool_async(pool_alias=alias, stmtcachesize=stmtcachesize)
    async with oracledb.connect_async(pool_alias=alias) as conn:
        assert conn.stmtcachesize == stmtcachesize
    await oracledb.get_pool(alias).close()


async def test_5540(test_env):
    "5540 - test pool alias is case sensitive"
    alias = "pool_5540"
    test_env.get_pool_async(pool_alias=alias)
    assert oracledb.get_pool(alias.upper()) is None
    with test_env.assert_raises_full_code("DPY-2054"):
        await test_env.get_connection_async(pool_alias=alias.upper())
    await oracledb.get_pool(alias).close()


async def test_5541(test_env):
    "5541 - test pool alias with invalid types"
    aliases = [5, set(), dict(), bytearray(1)]
    for alias in aliases:
        with pytest.raises(TypeError):
            test_env.get_pool_async(pool_alias=alias)


async def test_5542(test_env):
    "5542 - test creation of pool with min > max"
    with test_env.assert_raises_full_code("DPY-2064"):
        test_env.get_pool_async(min=3, max=2)


async def test_5543(skip_if_drcp, test_env):
    "5543 - ping pooled connection on receiving dead connection error"
    admin_conn = await test_env.get_admin_connection_async()
    pool = test_env.get_pool_async(min=1, max=1, ping_interval=0)

    # kill connection in pool
    with admin_conn.cursor() as admin_cursor:
        async with pool.acquire() as conn:
            sid, serial = (conn.session_id, conn.serial_num)
            sql = f"alter system kill session '{sid},{serial}'"
            await admin_cursor.execute(sql)

    # acquire connection which should succeed without failure
    async with pool.acquire() as conn:
        with conn.cursor() as cursor:
            await cursor.execute("select user from dual")
            (user,) = await cursor.fetchone()
            assert user == test_env.main_user.upper()


async def test_5544(test_env):
    "5544 - connection to database with bad password"
    pool = test_env.get_pool_async(password=test_env.main_password + "X")
    with test_env.assert_raises_full_code("ORA-01017"):
        await pool.acquire()
