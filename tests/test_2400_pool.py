# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
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
2400 - Module for testing pools
"""

import re
import threading

import oracledb
import pytest


class CallableSessionCallback:

    def __init__(self):
        self.session_called = False

    def __call__(self, conn, requested_tag):
        self.session_called = True

        supported_formats = {
            "SIMPLE": "'YYYY-MM-DD HH24:MI'",
            "FULL": "'YYYY-MM-DD HH24:MI:SS'",
        }

        supported_time_zones = {"UTC": "'UTC'", "MST": "'-07:00'"}

        supported_keys = {
            "NLS_DATE_FORMAT": supported_formats,
            "TIME_ZONE": supported_time_zones,
        }
        if requested_tag is not None:
            state_parts = []
            for directive in requested_tag.split(";"):
                parts = directive.split("=")
                if len(parts) != 2:
                    raise ValueError("Tag must contain key=value pairs")
                key, value = parts
                value_dict = supported_keys.get(key)
                if value_dict is None:
                    raise ValueError(
                        "Tag only supports keys: %s"
                        % (", ".join(supported_keys))
                    )
                actual_value = value_dict.get(value)
                if actual_value is None:
                    raise ValueError(
                        "Key %s only supports values: %s"
                        % (key, ", ".join(value_dict))
                    )
                state_parts.append(f"{key} = {actual_value}")
            sql = f"alter session set {' '.join(state_parts)}"
            cursor = conn.cursor()
            cursor.execute(sql)
        conn.tag = requested_tag


def _connect_and_drop(pool):
    with pool.acquire() as conn:
        cursor = conn.cursor()
        cursor.execute("select count(*) from TestNumbers")
        (count,) = cursor.fetchone()
        assert count == 10


def _connect_and_generate_error(pool, test_env):
    with pool.acquire() as conn:
        cursor = conn.cursor()
        with test_env.assert_raises_full_code("ORA-01476"):
            cursor.execute("select 1 / 0 from dual")


def _perform_reconfigure_test(
    test_env,
    parameter_name,
    parameter_value,
    min=3,
    max=30,
    increment=4,
    timeout=5,
    wait_timeout=5000,
    stmtcachesize=25,
    max_lifetime_session=1000,
    max_sessions_per_shard=3,
    ping_interval=30,
    getmode=oracledb.POOL_GETMODE_WAIT,
    soda_metadata_cache=False,
):
    creation_args = dict(
        min=min,
        max=max,
        increment=increment,
        timeout=timeout,
        stmtcachesize=stmtcachesize,
        ping_interval=ping_interval,
        getmode=getmode,
    )
    if test_env.has_client_version(12, 1):
        creation_args["max_lifetime_session"] = max_lifetime_session
    if test_env.has_client_version(12, 2):
        creation_args["wait_timeout"] = wait_timeout
    if test_env.has_client_version(18, 3):
        creation_args["max_sessions_per_shard"] = max_sessions_per_shard
    if test_env.has_client_version(19, 11):
        creation_args["soda_metadata_cache"] = soda_metadata_cache

    pool = test_env.get_pool(**creation_args)
    conn = pool.acquire()

    reconfigure_args = {}
    reconfigure_args[parameter_name] = parameter_value
    pool.reconfigure(**reconfigure_args)
    conn.close()

    actual_args = {}
    for name in creation_args:
        actual_args[name] = getattr(pool, name)
    expected_args = creation_args.copy()
    expected_args.update(reconfigure_args)
    assert actual_args == expected_args


def _verify_connection(conn, expected_user, expected_proxy_user=None):
    cursor = conn.cursor()
    cursor.execute(
        """
        select
            sys_context('userenv', 'session_user'),
            sys_context('userenv', 'proxy_user')
        from dual
        """
    )
    actual_user, actual_proxy_user = cursor.fetchone()
    assert actual_user == expected_user.upper()
    if expected_proxy_user is not None:
        expected_proxy_user = expected_proxy_user.upper()
    assert actual_proxy_user == expected_proxy_user


def _verify_create_arg(test_env, arg_name, arg_value, sql):
    args = {}
    args[arg_name] = arg_value
    pool = test_env.get_pool(**args)
    with pool.acquire() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        (fetched_value,) = cursor.fetchone()
        assert fetched_value == arg_value
    pool.close()


def test_2400(test_env):
    "2400 - test getting default pool parameters"
    pool = test_env.get_pool()
    assert pool.busy == 0
    assert pool.dsn == test_env.connect_string
    assert pool.tnsentry == pool.dsn
    if test_env.has_client_version(12, 2):
        assert pool.getmode == oracledb.POOL_GETMODE_WAIT
        assert pool.getmode is oracledb.PoolGetMode.WAIT
    assert pool.homogeneous
    assert pool.increment == 1
    assert pool.max == 2
    if test_env.has_client_version(12, 1):
        assert pool.max_lifetime_session == 0
    if not pool.thin and test_env.has_client_version(18, 3):
        assert pool.max_sessions_per_shard == 0
    assert pool.min == 1
    if pool.thin:
        assert pool.name is None
    else:
        assert re.search("^OCI:SP:.+", pool.name) is not None
    assert pool.ping_interval == 60
    assert pool.stmtcachesize == oracledb.defaults.stmtcachesize
    if not pool.thin and test_env.has_client_version(19, 11):
        assert not pool.soda_metadata_cache
        assert pool.thin == (not test_env.use_thick_mode)
    assert pool.timeout == 0
    assert pool.username == test_env.main_user


def test_2401(skip_unless_thick_mode, test_env):
    "2401 - test that proxy authentication is possible"
    pool = test_env.get_pool(
        min=2, max=8, increment=3, getmode=oracledb.POOL_GETMODE_WAIT
    )
    assert pool.homogeneous, "homogeneous should be True by default"
    with test_env.assert_raises_full_code("DPI-1012"):
        pool.acquire(user="missing_proxyuser")
    pool = test_env.get_pool(
        min=2,
        max=8,
        increment=3,
        getmode=oracledb.POOL_GETMODE_WAIT,
        homogeneous=False,
    )
    assert not pool.homogeneous
    conn = pool.acquire(user=test_env.proxy_user)
    cursor = conn.cursor()
    cursor.execute("select user from dual")
    (user,) = cursor.fetchone()
    assert user == test_env.proxy_user.upper()
    conn.close()


def test_2402(test_env):
    "2402 - test setting pool attributes"
    pool = test_env.get_pool()
    test_values = [
        ((11, 2), "ping_interval", 30),
        ((11, 2), "stmtcachesize", 100),
        ((11, 2), "timeout", 10),
        ((12, 2), "getmode", oracledb.POOL_GETMODE_TIMEDWAIT),
        ((12, 1), "max_lifetime_session", 3),
    ]
    for version, attr_name, value in test_values:
        if test_env.has_client_version(*version):
            setattr(pool, attr_name, value)
            assert getattr(pool, attr_name) == value
            pytest.raises(TypeError, setattr, pool, attr_name, "invalid value")

    if not pool.thin and test_env.has_client_version(18, 3):
        assert pool.max_sessions_per_shard == 0
        pytest.raises(
            TypeError, setattr, pool, "max_sessions_per_shard", "bad_val"
        )

    if not pool.thin and test_env.has_client_version(19, 11):
        pool.soda_metadata_cache = True
        assert pool.soda_metadata_cache
        pytest.raises(TypeError, setattr, pool, "soda_metadata_cache", 22)


def test_2403(test_env):
    "2403 - connection rolls back before released back to the pool"
    pool = test_env.get_pool(getmode=oracledb.POOL_GETMODE_WAIT)
    conn = pool.acquire()
    cursor = conn.cursor()
    cursor.execute("truncate table TestTempTable")
    cursor.execute("insert into TestTempTable (IntCol) values (1)")
    cursor.close()
    pool.release(conn)
    pool = test_env.get_pool(getmode=oracledb.POOL_GETMODE_WAIT)
    conn = pool.acquire()
    cursor = conn.cursor()
    cursor.execute("select count(*) from TestTempTable")
    (count,) = cursor.fetchone()
    assert count == 0
    conn.close()


def test_2404(test_env):
    "2404 - test session pool with multiple threads"
    pool = test_env.get_pool(
        min=5, max=20, increment=2, getmode=oracledb.POOL_GETMODE_WAIT
    )
    threads = []
    for i in range(20):
        thread = threading.Thread(None, _connect_and_drop, args=(pool,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()


def test_2405(test_env):
    "2405 - test session pool with multiple threads (with errors)"
    pool = test_env.get_pool(
        min=5, max=20, increment=2, getmode=oracledb.POOL_GETMODE_WAIT
    )
    threads = []
    for i in range(20):
        thread = threading.Thread(
            None, _connect_and_generate_error, args=(pool, test_env)
        )
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()


def test_2406(skip_if_drcp, test_env):
    "2406 - test session pool with various types of purity"
    pool = test_env.get_pool(
        min=1, max=8, increment=1, getmode=oracledb.POOL_GETMODE_WAIT
    )

    # get connection and set the action
    action = "TEST_ACTION"
    conn = pool.acquire()
    conn.action = action
    cursor = conn.cursor()
    cursor.execute("select 1 from dual")
    cursor.close()
    pool.release(conn)
    assert pool.opened == 1, "opened (1)"

    # verify that the connection still has the action set on it
    conn = pool.acquire()
    cursor = conn.cursor()
    cursor.execute("select sys_context('userenv', 'action') from dual")
    (result,) = cursor.fetchone()
    assert result == action
    cursor.close()
    pool.release(conn)
    assert pool.opened == 1, "opened (2)"

    # get a new connection with new purity (should not have state)
    conn = pool.acquire(purity=oracledb.ATTR_PURITY_NEW)
    cursor = conn.cursor()
    cursor.execute("select sys_context('userenv', 'action') from dual")
    (result,) = cursor.fetchone()
    assert result is None
    cursor.close()
    pool.release(conn)


def test_2407(skip_if_drcp, skip_unless_thick_mode, test_env):
    "2407 - test heterogeneous pool with user and password specified"
    pool = test_env.get_pool(
        min=2,
        max=8,
        increment=3,
        homogeneous=False,
        getmode=oracledb.POOL_GETMODE_WAIT,
    )
    assert pool.homogeneous == 0
    conn = pool.acquire()
    _verify_connection(pool.acquire(), test_env.main_user)
    conn.close()
    conn = pool.acquire(test_env.main_user, test_env.main_password)
    _verify_connection(conn, test_env.main_user)
    conn.close()
    conn = pool.acquire(test_env.proxy_user, test_env.proxy_password)
    _verify_connection(conn, test_env.proxy_user)
    conn.close()
    user_str = f"{test_env.main_user}[{test_env.proxy_user}]"
    conn = pool.acquire(user_str, test_env.main_password)
    assert conn.username == test_env.main_user
    assert conn.proxy_user == test_env.proxy_user
    _verify_connection(conn, test_env.proxy_user, test_env.main_user)
    conn.close()


def test_2408(skip_if_drcp, skip_unless_thick_mode, test_env):
    "2408 - test heterogeneous pool without user and password specified"
    pool = test_env.get_pool(
        user="",
        password="",
        min=2,
        max=8,
        increment=3,
        getmode=oracledb.POOL_GETMODE_WAIT,
        homogeneous=False,
    )
    conn = pool.acquire(test_env.main_user, test_env.main_password)
    _verify_connection(conn, test_env.main_user)
    conn.close()
    conn = pool.acquire(test_env.proxy_user, test_env.proxy_password)
    _verify_connection(conn, test_env.proxy_user)
    conn.close()
    user_str = f"{test_env.main_user}[{test_env.proxy_user}]"
    conn = pool.acquire(user_str, test_env.main_password)
    _verify_connection(conn, test_env.proxy_user, test_env.main_user)


def test_2409(skip_unless_thick_mode, test_env):
    "2409 - test heterogeneous pool with wrong password specified"
    pool = test_env.get_pool(
        min=2,
        max=8,
        increment=3,
        getmode=oracledb.POOL_GETMODE_WAIT,
        homogeneous=False,
    )
    with test_env.assert_raises_full_code("ORA-01017"):
        pool.acquire(test_env.proxy_user, "this is the wrong password")


def test_2410(skip_unless_thick_mode, test_env):
    "2410 - test tagging a session"
    pool = test_env.get_pool(
        min=2, max=8, increment=3, getmode=oracledb.POOL_GETMODE_NOWAIT
    )
    tag_mst = "TIME_ZONE=MST"
    tag_utc = "TIME_ZONE=UTC"

    conn = pool.acquire()
    assert conn.tag is None
    pool.release(conn, tag=tag_mst)

    conn = pool.acquire()
    assert conn.tag is None
    conn.tag = tag_utc
    conn.close()

    conn = pool.acquire(tag=tag_mst)
    assert conn.tag == tag_mst
    conn.close()

    conn = pool.acquire(tag=tag_utc)
    assert conn.tag == tag_utc
    conn.close()


def test_2411(skip_unless_thick_mode, test_env):
    "2411 - test PL/SQL session callbacks"
    test_env.skip_unless_client_version(12, 2)
    callback = "pkg_SessionCallback.TheCallback"
    pool = test_env.get_pool(
        min=2,
        max=8,
        increment=3,
        session_callback=callback,
    )
    tags = [
        "NLS_DATE_FORMAT=SIMPLE",
        "NLS_DATE_FORMAT=FULL;TIME_ZONE=UTC",
        "NLS_DATE_FORMAT=FULL;TIME_ZONE=MST",
    ]
    actual_tags = [None, None, "NLS_DATE_FORMAT=FULL;TIME_ZONE=UTC"]

    # truncate PL/SQL session callback log
    conn = pool.acquire()
    cursor = conn.cursor()
    cursor.execute("truncate table PLSQLSessionCallbacks")
    conn.close()

    # request sessions with each of the first two tags
    for tag in tags[:2]:
        conn = pool.acquire(tag=tag)
        conn.close()

    # for the last tag, use the matchanytag flag
    conn = pool.acquire(tag=tags[2], matchanytag=True)
    conn.close()

    # verify the PL/SQL session callback log is accurate
    conn = pool.acquire()
    cursor = conn.cursor()
    cursor.execute(
        """
        select RequestedTag, ActualTag
        from PLSQLSessionCallbacks
        order by FixupTimestamp
        """
    )
    results = cursor.fetchall()
    expected_results = list(zip(tags, actual_tags))
    assert results == expected_results
    conn.close()


def test_2412(skip_unless_thick_mode, test_env):
    "2412 - testTagging with Invalid key"
    pool = test_env.get_pool(getmode=oracledb.POOL_GETMODE_NOWAIT)
    conn = pool.acquire()
    pytest.raises(TypeError, pool.release, conn, tag=12345)
    if test_env.has_client_version(12, 2):
        with test_env.assert_raises_full_code("ORA-24488"):
            pool.release(conn, tag="INVALID_TAG")


def test_2413(test_env):
    "2413 - test dropping/closing a connection from the pool"
    pool = test_env.get_pool(min=1, max=5, increment=2)
    conns1 = [pool.acquire() for _ in range(2)]
    conns2 = [oracledb.connect(pool=pool) for _ in range(3)]
    assert pool.busy == 5
    assert pool.opened == 5

    for conn in conns1:
        pool.drop(conn)
    assert pool.busy == 3
    assert pool.opened == 3

    for conn in conns2:
        conn.close()
    assert pool.busy == 0
    assert pool.opened == 3


def test_2414(test_env):
    "2414 - test to ensure pure connections are being created correctly"
    pool = test_env.get_pool(
        min=1, max=2, increment=1, getmode=oracledb.POOL_GETMODE_WAIT
    )
    conn1 = pool.acquire()
    conn2 = pool.acquire()
    assert pool.opened == 2, "opened (1)"
    pool.release(conn1)
    pool.release(conn2)
    conn3 = pool.acquire(purity=oracledb.ATTR_PURITY_NEW)
    assert pool.opened == 2, "opened (2)"
    pool.release(conn3)


def test_2415(skip_unless_thick_mode, test_env):
    "2415 - test the reconfigure values are changed and rest unchanged"
    _perform_reconfigure_test(test_env, "min", 5)
    _perform_reconfigure_test(test_env, "max", 20)
    _perform_reconfigure_test(test_env, "increment", 5)
    _perform_reconfigure_test(test_env, "timeout", 10)
    _perform_reconfigure_test(test_env, "stmtcachesize", 40)
    _perform_reconfigure_test(test_env, "ping_interval", 50)
    _perform_reconfigure_test(
        test_env, "getmode", oracledb.POOL_GETMODE_NOWAIT
    )
    if test_env.has_client_version(12, 1):
        _perform_reconfigure_test(test_env, "max_lifetime_session", 2000)
    if test_env.has_client_version(12, 2):
        _perform_reconfigure_test(test_env, "wait_timeout", 8000)
    if test_env.has_client_version(18, 3):
        _perform_reconfigure_test(test_env, "max_sessions_per_shard", 5)
    if test_env.has_client_version(19, 11):
        _perform_reconfigure_test(test_env, "soda_metadata_cache", True)


def test_2417(skip_unless_thick_mode, test_env):
    "2417 - test that session callbacks are being called correctly"
    callback_obj = CallableSessionCallback()

    pool = test_env.get_pool(
        min=2,
        max=5,
        increment=1,
        session_callback=callback_obj,
    )

    # new connection with a tag should invoke the session callback
    with pool.acquire(tag="NLS_DATE_FORMAT=SIMPLE") as conn:
        cursor = conn.cursor()
        cursor.execute("select to_char(2021-05-20) from dual")
        (result,) = cursor.fetchone()
        assert callback_obj.session_called

    # acquiring a connection with the same tag should not invoke the
    # session callback
    callback_obj.session_called = False
    with pool.acquire(tag="NLS_DATE_FORMAT=SIMPLE") as conn:
        cursor = conn.cursor()
        cursor.execute("select to_char(2021-05-20) from dual")
        (result,) = cursor.fetchone()
        assert not callback_obj.session_called

    # acquiring a connection with a new tag should invoke the session
    # callback
    callback_obj.session_called = False
    with pool.acquire(tag="NLS_DATE_FORMAT=FULL;TIME_ZONE=UTC") as conn:
        cursor = conn.cursor()
        cursor.execute("select to_char(current_date) from dual")
        (result,) = cursor.fetchone()
        assert callback_obj.session_called

    # acquiring a connection with a new tag and specifying that a
    # connection with any tag can be acquired should invoke the session
    # callback
    callback_obj.session_called = False
    with pool.acquire(
        tag="NLS_DATE_FORMAT=FULL;TIME_ZONE=MST", matchanytag=True
    ) as conn:
        cursor = conn.cursor()
        cursor.execute("select to_char(current_date) from dual")
        (result,) = cursor.fetchone()
        assert callback_obj.session_called

    # new connection with no tag should invoke the session callback
    callback_obj.session_called = False
    with pool.acquire() as conn:
        cursor = conn.cursor()
        cursor.execute("select to_char(current_date) from dual")
        (result,) = cursor.fetchone()
        assert callback_obj.session_called


def test_2418(test_env):
    "2418 - test closing a pool normally with no connections checked out"
    pool = test_env.get_pool(
        min=1, max=8, increment=1, getmode=oracledb.POOL_GETMODE_WAIT
    )
    pool.close()


def test_2419(test_env):
    "2419 - test closing a pool normally with connections checked out"
    pool = test_env.get_pool(
        min=1, max=8, increment=1, getmode=oracledb.POOL_GETMODE_WAIT
    )
    with pool.acquire():
        with test_env.assert_raises_full_code("DPY-1005"):
            pool.close()


def test_2420(test_env):
    "2420 - test closing a pool forcibly"
    pool = test_env.get_pool(
        min=1, max=8, increment=1, getmode=oracledb.POOL_GETMODE_WAIT
    )
    with pool.acquire():
        pool.close(force=True)


def test_2421(test_env):
    "2421 - using the pool after it is closed raises an exception"
    pool = test_env.get_pool(
        min=1, max=8, increment=1, getmode=oracledb.POOL_GETMODE_WAIT
    )
    pool.close()
    with test_env.assert_raises_full_code("DPY-1002"):
        pool.acquire()


def test_2422(test_env):
    "2422 - using the pool beyond max limit raises an error"
    if not test_env.has_client_version(19):
        pytest.skip("not supported on this client")
    pool = test_env.get_pool(
        min=1, max=2, increment=1, getmode=oracledb.POOL_GETMODE_WAIT
    )
    with pool.acquire(), pool.acquire():
        pool.getmode = oracledb.POOL_GETMODE_NOWAIT
        with test_env.assert_raises_full_code("DPY-4005"):
            pool.acquire()


def test_2423(test_env):
    "2423 - callable session callback is executed for new connections"

    class Counter:
        num_calls = 0

        @classmethod
        def session_callback(cls, conn, requested_tag):
            cls.num_calls += 1

    pool = test_env.get_pool(
        min=1,
        max=2,
        increment=1,
        session_callback=Counter.session_callback,
    )
    with pool.acquire(), pool.acquire():
        pass
    with pool.acquire(), pool.acquire():
        pass
    assert Counter.num_calls == 2


def test_2424(skip_if_drcp, admin_conn, test_env):
    "2424 - drop the pooled connection on receiving dead connection error"
    test_env.skip_unless_server_version(19)
    pool = test_env.get_pool(min=2, max=2, increment=2)

    # acquire connections from the pool and kill all the sessions
    with admin_conn.cursor() as admin_cursor:
        for conn in [pool.acquire() for i in range(2)]:
            sid, serial = test_env.get_sid_serial(conn)
            sql = f"alter system kill session '{sid},{serial}'"
            admin_cursor.execute(sql)
            conn.close()
    assert pool.opened == 2

    # when try to re-use the killed sessions error will be raised;
    # release all such connections
    for conn in [pool.acquire() for i in range(2)]:
        with conn.cursor() as cursor:
            with test_env.assert_raises_full_code("DPY-4011"):
                cursor.execute("select user from dual")
        conn.close()

    # if a free connection is available, it can be used; otherwise a new
    # connection will be created
    for conn in [pool.acquire() for i in range(2)]:
        with conn.cursor() as cursor:
            cursor.execute("select user from dual")
            (user,) = cursor.fetchone()
            assert user == test_env.main_user.upper()
        conn.close()
    assert pool.opened == 2


def test_2425(test_env):
    "2425 - acquire a connection from an empty pool (min=0)"
    pool = test_env.get_pool(min=0, max=2, increment=2)
    with pool.acquire() as conn:
        with conn.cursor() as cursor:
            cursor.execute("select user from dual")
            (result,) = cursor.fetchone()
            assert result == test_env.main_user.upper()


def test_2426(test_env):
    "2426 - get different object types from different connections"
    pool = test_env.get_pool(min=1, max=2, increment=1)
    with pool.acquire() as conn:
        typ = conn.gettype("UDT_SUBOBJECT")
        assert typ.name == "UDT_SUBOBJECT"
    with pool.acquire() as conn:
        typ = conn.gettype("UDT_OBJECTARRAY")
        assert typ.name == "UDT_OBJECTARRAY"


def test_2427(test_env):
    "2427 - test creating a pool using a proxy user"
    user_str = f"{test_env.main_user}[{test_env.proxy_user}]"
    pool = test_env.get_pool(user=user_str)
    _verify_connection(pool.acquire(), test_env.proxy_user, test_env.main_user)


def test_2428(skip_if_drcp, test_env):
    "2428 - test acquiring conn from pool in LIFO order"
    pool = test_env.get_pool(
        min=5, max=10, increment=1, getmode=oracledb.POOL_GETMODE_WAIT
    )
    sql = "select sys_context('userenv', 'sid') from dual"
    conns = [pool.acquire() for i in range(3)]
    sids = [conn.cursor().execute(sql).fetchone()[0] for conn in conns]

    conns[1].close()
    conns[2].close()
    conns[0].close()

    conn = pool.acquire()
    sid = conn.cursor().execute(sql).fetchone()[0]
    assert sid == sids[0], "not LIFO"


def test_2429(test_env):
    "2429 - verify that dynamic pool cannot have an increment of zero"
    pool = test_env.get_pool(min=1, max=3, increment=0)
    assert pool.increment == 1
    with pool.acquire(), pool.acquire():
        pass


def test_2430(test_env):
    "2430 - verify that static pool can have an increment of zero"
    pool = test_env.get_pool(min=1, max=1, increment=0)
    assert pool.increment == 0
    with pool.acquire():
        pass


def test_2431(test_env):
    "2431 - verify that connection with different cclass is reused"
    test_env.skip_unless_server_version(19)
    cclass = "cclass2431"
    pool = test_env.get_pool(min=1, max=1)
    # ignore the first acquire which, depending on the speed with which the
    # minimum connections are created, may create a connection that is
    # discarded; instead, use the second acquire which should remain in the
    # pool
    with pool.acquire(cclass=cclass) as conn:
        pass
    with pool.acquire(cclass=cclass) as conn:
        sid_serial = test_env.get_sid_serial(conn)
    with pool.acquire(cclass=cclass) as conn:
        next_sid_serial = test_env.get_sid_serial(conn)
        assert next_sid_serial == sid_serial
    assert pool.opened == 1


def test_2432(test_env):
    "2432 - test creating a pool invalid params"
    with test_env.assert_raises_full_code("DPY-2027"):
        oracledb.create_pool(params="bad params")


def test_2433(test_env):
    "2433 - test releasing and dropping an invalid connection"
    pool = test_env.get_pool()
    pytest.raises(TypeError, pool.release, ["invalid connection"])
    pytest.raises(TypeError, pool.drop, ["invalid connection"])


def test_2434(test_env):
    "2434 - test creating a pool with invalid pool_class"
    with test_env.assert_raises_full_code("DPY-2026"):
        oracledb.create_pool(pool_class=int)


def test_2435(test_env):
    "2435 - test creating a pool with a subclassed connection type"

    class MyConnection(oracledb.Connection):
        pass

    pool = test_env.get_pool(connectiontype=MyConnection)
    with pool.acquire() as conn:
        assert isinstance(conn, MyConnection)


def test_2436(test_env):
    "2436 - test creating a pool with a subclassed pool type"

    class MyPool(oracledb.ConnectionPool):
        pass

    pool = test_env.get_pool(pool_class=MyPool)
    assert isinstance(pool, MyPool)


def test_2437(test_env):
    "2437 - test connectiontype with an invalid connection class"
    with test_env.assert_raises_full_code("DPY-2023"):
        test_env.get_pool(connectiontype=oracledb.AsyncConnection)
    with test_env.assert_raises_full_code("DPY-2023"):
        test_env.get_pool(connectiontype=int)


def test_2438(skip_unless_pool_timed_wait_supported, test_env):
    "2438 - ensure that timed wait times out with appropriate exception"
    pool = test_env.get_pool(
        getmode=oracledb.POOL_GETMODE_TIMEDWAIT, min=0, wait_timeout=1
    )
    with test_env.assert_raises_full_code("DPY-4005"):
        pool.acquire()


def test_2439(skip_unless_call_timeout_supported, test_env):
    "2439 - ensure call timeout is reset on connections returned by pool"
    pool = test_env.get_pool(ping_timeout=1000, ping_interval=0)
    with pool.acquire() as conn:
        assert conn.call_timeout == 0
    with pool.acquire() as conn:
        assert conn.call_timeout == 0


def test_2440(test_env):
    "2440 - test connection with an invalid pool"
    with pytest.raises(TypeError):
        oracledb.connect(pool="not a pool object")


def test_2441(test_env):
    "2441 - test oracledb.POOL_GETMODE_FORCEGET"
    pool = test_env.get_pool(
        min=1, max=3, increment=1, getmode=oracledb.POOL_GETMODE_FORCEGET
    )
    num_conns = 10
    active_sessions = set()
    conns = [pool.acquire() for _ in range(num_conns)]
    for conn in conns:
        active_sessions.add(test_env.get_sid_serial(conn))
    assert pool.opened == num_conns
    assert pool.busy == num_conns
    assert len(active_sessions) == num_conns


def test_2442(skip_unless_thin_mode, test_env):
    "2442 - test passing program when creating a pool"
    sql = (
        "select program from v$session "
        "where sid = sys_context('userenv', 'sid')"
    )
    _verify_create_arg(test_env, "program", "newprogram", sql)


def test_2443(skip_unless_thin_mode, test_env):
    "2443 - test passing machine when creating a pool"
    sql = (
        "select machine from v$session "
        "where sid = sys_context('userenv', 'sid')"
    )
    _verify_create_arg(test_env, "machine", "newmachine", sql)


def test_2444(skip_unless_thin_mode, test_env):
    "2444 - test passing terminal when creating a pool"
    sql = (
        "select terminal from v$session "
        "where sid = sys_context('userenv', 'sid')"
    )
    _verify_create_arg(test_env, "terminal", "newterminal", sql)


def test_2445(skip_unless_thin_mode, test_env):
    "2445 - test passing osuser when creating a pool"
    sql = (
        "select osuser from v$session "
        "where sid = sys_context('userenv', 'sid')"
    )
    _verify_create_arg(test_env, "osuser", "newosuser", sql)


def test_2446(test_env):
    "2446 - test passing driver_name when creating a pool"
    sql = (
        "select distinct client_driver from v$session_connect_info "
        "where sid = sys_context('userenv', 'sid')"
    )
    _verify_create_arg(test_env, "driver_name", "newdriver", sql)


def test_2447(skip_unless_thin_mode, test_env):
    "2447 - test register_parameter with pooled connection"
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
        pool = oracledb.create_pool(dsn=connect_string, params=params)
        assert params.sdu == sdu
        with pool.acquire():
            pass
        pool.close()
    finally:
        oracledb.register_protocol(protocol, None)


def test_2448(test_env):
    "2448 - test create_pool() with edition"
    edition = test_env.edition_name
    pool = test_env.get_pool(edition=edition)
    conn = pool.acquire()
    assert conn.edition == edition


def test_2449(test_env):
    "2449 - test create_pool() and get_pool() with alias"
    alias = "pool_alias_2449"
    pool = test_env.get_pool(pool_alias=alias)
    assert pool is oracledb.get_pool(alias)
    pool.close()


def test_2450(test_env):
    "2450 - test create_pool() twice with the same alias"
    alias = "pool_alias_2450"
    pool = test_env.get_pool(pool_alias=alias)
    with test_env.assert_raises_full_code("DPY-2055"):
        test_env.get_pool(pool_alias=alias)
    pool.close()
    assert oracledb.get_pool(alias) is None


def test_2451(test_env):
    "2451 - test connect() with pool alias"
    alias = "pool_alias_2451"
    pool = test_env.get_pool(pool_alias=alias)
    with test_env.assert_raises_full_code("DPY-2014"):
        test_env.get_connection(pool=pool, pool_alias=alias)
    with oracledb.connect(pool_alias=alias) as conn:
        with conn.cursor() as cursor:
            cursor.execute("select user from dual")
            (value,) = cursor.fetchone()
            assert value == test_env.main_user.upper()
    pool.close()
    with test_env.assert_raises_full_code("DPY-2054"):
        oracledb.connect(pool_alias=alias)


def test_2452(test_env):
    "2452 - test acquire() with pool alias and stmtcachesize"
    alias = "pool_2452"
    stmtcachesize = 35
    test_env.get_pool(pool_alias=alias, stmtcachesize=stmtcachesize)
    with oracledb.connect(pool_alias=alias) as conn:
        assert conn.stmtcachesize == stmtcachesize
    oracledb.get_pool(alias).close()


def test_2453(test_env):
    "2453 - test pool alias is case sensitive"
    alias = "pool_2458"
    test_env.get_pool(pool_alias=alias)
    assert oracledb.get_pool(alias.upper()) is None
    with test_env.assert_raises_full_code("DPY-2054"):
        test_env.get_connection(pool_alias=alias.upper())
    oracledb.get_pool(alias).close()


def test_2454(test_env):
    "2454 - test pool alias with invalid types"
    aliases = [5, set(), dict(), bytearray(1)]
    for alias in aliases:
        with pytest.raises(TypeError):
            test_env.get_pool(pool_alias=alias)


def test_2455(test_env):
    "2455 - test create_pool() with parameters hook"
    pool = test_env.get_pool()
    with pool.acquire() as conn:
        orig_stmtcachesize = conn.stmtcachesize
        stmtcachesize = orig_stmtcachesize + 10
    pool.close()

    def hook(params):
        params.set(stmtcachesize=stmtcachesize)

    try:
        oracledb.register_params_hook(hook)
        pool = test_env.get_pool()
        with pool.acquire() as conn:
            assert conn.stmtcachesize == stmtcachesize
        pool.close()
    finally:
        oracledb.unregister_params_hook(hook)

    pool = test_env.get_pool()
    with pool.acquire() as conn:
        assert conn.stmtcachesize == orig_stmtcachesize
    pool.close()


def test_2456(test_env):
    "2456 - test creation of pool with min > max"
    with test_env.assert_raises_full_code("DPY-2064"):
        test_env.get_pool(min=3, max=2)


def test_2457(skip_if_drcp, test_env):
    "2457 - ping pooled connection on receiving dead connection error"
    test_env.skip_unless_server_version(18)
    admin_conn = test_env.get_admin_connection()
    pool = test_env.get_pool(min=1, max=1, ping_interval=0)

    # kill connection in pool
    with admin_conn.cursor() as admin_cursor:
        with pool.acquire() as conn:
            sid, serial = test_env.get_sid_serial(conn)
            sql = f"alter system kill session '{sid},{serial}'"
            admin_cursor.execute(sql)

    # acquire connection which should succeed without failure
    with pool.acquire() as conn:
        with conn.cursor() as cursor:
            cursor.execute("select user from dual")
            (user,) = cursor.fetchone()
            assert user == test_env.main_user.upper()


def test_2458(test_env):
    "2458 - connection to database with bad password"
    with test_env.assert_raises_full_code("ORA-01017"):
        pool = test_env.get_pool(password=test_env.main_password + "X")
        pool.acquire()
