# -----------------------------------------------------------------------------
# Copyright (c) 2026, Oracle and/or its affiliates.
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
E3100 - Tests Deep Data Security with asyncio.

These tests are only run when the following entries are set in the extended
configuration file:

    deep_data_security_db_token: path to the database access token file
    deep_data_security_user_token: path to the end user token file
    deep_data_security_xs_user: the Azure/IAM user name

For details on Deep Data Security refer to
https://docs-uat.us.oracle.com/en/database/oracle/oracle-database/26/ddscg/what-is-oracle-deep-data-security.html#GUID-E239A5C4-0C0D-4FF0-98DD-2E374F79C63C
"""

import asyncio
import collections

import pytest
import oracledb

DeepDataSecurityConfig = collections.namedtuple(
    "DeepDataSecurityConfig", "db_token user_token xs_user"
)


@pytest.fixture(autouse=True)
def module_checks(skip_unless_deep_data_security, anyio_backend):
    pass


@pytest.fixture(scope="module")
def deep_data_security_config(skip_unless_deep_data_security, extended_config):
    return DeepDataSecurityConfig(
        db_token=extended_config.get_file_value("deep_data_security_db_token"),
        user_token=extended_config.get_file_value(
            "deep_data_security_user_token"
        ),
        xs_user=extended_config.get_str_value("deep_data_security_xs_user"),
    )


async def _assert_base_session_context(cur, expected_schema_user):
    session_xs_user, current_xs_user, current_user, session_user = (
        await _get_session_context(cur)
    )
    assert session_xs_user is None
    assert current_xs_user is None
    assert current_user == expected_schema_user
    assert session_user == expected_schema_user


async def _assert_context_round_trip(conn, config):
    conn.set_end_user_security_context(
        oracledb.create_end_user_security_context(
            end_user_identity=config.user_token,
            database_access_token=config.db_token,
        )
    )
    with conn.cursor() as cur:
        assert await _get_xs_username(cur) == config.xs_user
        await cur.execute("""
            select
                sys_context('userenv', 'current_user'),
                xs_sys_context('xs$session', 'username')
            """)
        current_user, current_xs_user = await cur.fetchone()
        assert current_user == "XS$NULL"
        assert current_xs_user == config.xs_user
        await _assert_secured_session_context(cur, config.xs_user)


async def _assert_secured_session_context(cur, expected_xs_user):
    session_xs_user, current_xs_user, current_user, session_user = (
        await _get_session_context(cur)
    )
    assert (
        session_xs_user == expected_xs_user
        or current_xs_user == expected_xs_user
    )
    assert current_user == "XS$NULL"
    assert session_user == "XS$NULL"


async def _get_session_context(cur):
    await cur.execute("""
        select
            xs_sys_context('xs$session', 'session_xs_user'),
            xs_sys_context('xs$session', 'current_xs_user'),
            sys_context('userenv', 'current_user'),
            sys_context('userenv', 'session_user')
        """)
    return await cur.fetchone()


async def _get_xs_username(cur):
    await cur.execute("select xs_sys_context('xs$session', 'username')")
    (value,) = await cur.fetchone()
    return value


def _thread_context_check(test_env, errors, config):
    try:
        with test_env.get_connection() as conn:
            _assert_context_round_trip(conn, config)
    except Exception as e:
        errors.put(e)


async def test_ext_3100(async_conn, deep_data_security_config):
    "E3100 - example: create, set and clear a security context"
    await _assert_context_round_trip(async_conn, deep_data_security_config)


async def test_ext_3101(test_env, deep_data_security_config):
    "E3101 - example: use a security context with a pooled connection"
    pool = test_env.get_pool_async()
    async with pool.acquire() as conn:
        await _assert_context_round_trip(conn, deep_data_security_config)
    await pool.close()


@pytest.mark.parametrize(
    "invalidate_user_token,expected_error",
    [(True, "ORA-52601"), (False, "ORA-52602")],
)
async def test_ext_3102(
    async_conn,
    test_env,
    deep_data_security_config,
    invalidate_user_token,
    expected_error,
):
    "E3102 - invalid token inputs are rejected on use"
    if invalidate_user_token:
        end_user_identity = "invalid_token"
        database_access_token = deep_data_security_config.db_token
    else:
        end_user_identity = deep_data_security_config.user_token
        database_access_token = "invalid_token"
    async_conn.set_end_user_security_context(
        oracledb.create_end_user_security_context(
            end_user_identity=end_user_identity,
            database_access_token=database_access_token,
        )
    )
    with async_conn.cursor() as cur:
        with test_env.assert_raises_full_code(expected_error):
            await _get_xs_username(cur)


async def test_ext_3103(async_conn, deep_data_security_config):
    "E3103 - the same security context can be reused after clear"
    context = oracledb.create_end_user_security_context(
        end_user_identity=deep_data_security_config.user_token,
        database_access_token=deep_data_security_config.db_token,
    )
    async_conn.set_end_user_security_context(context)
    with async_conn.cursor() as cur:
        assert await _get_xs_username(cur) == deep_data_security_config.xs_user
        async_conn.clear_end_user_security_context()
        assert await _get_xs_username(cur) is None
        async_conn.set_end_user_security_context(context)
        assert await _get_xs_username(cur) == deep_data_security_config.xs_user


async def test_ext_3104(async_conn, deep_data_security_config):
    "E3104 - clearing the security context twice is harmless"
    async_conn.set_end_user_security_context(
        oracledb.create_end_user_security_context(
            end_user_identity=deep_data_security_config.user_token,
            database_access_token=deep_data_security_config.db_token,
        )
    )
    with async_conn.cursor() as cur:
        assert await _get_xs_username(cur) == deep_data_security_config.xs_user
        async_conn.clear_end_user_security_context()
        async_conn.clear_end_user_security_context()
        assert await _get_xs_username(cur) is None


async def test_ext_3105(async_conn, test_env, deep_data_security_config):
    "E3105 - a connection can recover after an invalid context"
    async_conn.set_end_user_security_context(
        oracledb.create_end_user_security_context(
            end_user_identity="invalid_token",
            database_access_token=deep_data_security_config.db_token,
        )
    )
    with async_conn.cursor() as cur:
        with test_env.assert_raises_full_code("ORA-52601"):
            await _get_xs_username(cur)
        async_conn.clear_end_user_security_context()
        assert await _get_xs_username(cur) is None
        async_conn.set_end_user_security_context(
            oracledb.create_end_user_security_context(
                end_user_identity=deep_data_security_config.user_token,
                database_access_token=deep_data_security_config.db_token,
            )
        )
        assert await _get_xs_username(cur) == deep_data_security_config.xs_user


async def test_ext_3106(async_conn, deep_data_security_config):
    "E3106 - clear_end_user_security_context restores the base session"
    with async_conn.cursor() as cur:
        await cur.execute("select user")
        (schema_user,) = await cur.fetchone()
        await _assert_base_session_context(cur, schema_user)
        async_conn.set_end_user_security_context(
            oracledb.create_end_user_security_context(
                end_user_identity=deep_data_security_config.user_token,
                database_access_token=deep_data_security_config.db_token,
            )
        )
        await _assert_secured_session_context(
            cur, deep_data_security_config.xs_user
        )
        async_conn.clear_end_user_security_context()
        await _assert_base_session_context(cur, schema_user)


async def test_ext_3107(test_env, deep_data_security_config):
    "E3107 - pooled connection reuse starts without the prior security context"
    pool = test_env.get_pool_async()
    async with pool.acquire() as conn:
        with conn.cursor() as cur:
            await cur.execute("select user from dual")
            (schema_user,) = await cur.fetchone()
            conn.set_end_user_security_context(
                oracledb.create_end_user_security_context(
                    end_user_identity=deep_data_security_config.user_token,
                    database_access_token=deep_data_security_config.db_token,
                )
            )
            await _assert_secured_session_context(
                cur, deep_data_security_config.xs_user
            )
    async with pool.acquire() as conn:
        with conn.cursor() as cur:
            await _assert_base_session_context(cur, schema_user)
    await pool.close()


async def test_ext_3108(async_conn, deep_data_security_config):
    "E3108 - clearing before the first round-trip drops the pending context"
    with async_conn.cursor() as cur:
        await cur.execute("select user from dual")
        (schema_user,) = await cur.fetchone()
        async_conn.set_end_user_security_context(
            oracledb.create_end_user_security_context(
                end_user_identity=deep_data_security_config.user_token,
                database_access_token=deep_data_security_config.db_token,
            )
        )
        async_conn.clear_end_user_security_context()
        await _assert_base_session_context(cur, schema_user)


async def test_ext_3109(async_conn):
    "E3109 - clear_end_user_security_context can be called before set"
    async_conn.clear_end_user_security_context()
    with async_conn.cursor() as cur:
        assert await _get_xs_username(cur) is None


async def test_ext_3110(async_conn, deep_data_security_config):
    "E3110 - set_end_user_security_context validates its arguments"
    context = oracledb.create_end_user_security_context(
        end_user_identity=deep_data_security_config.user_token,
        database_access_token=deep_data_security_config.db_token,
    )
    with pytest.raises(TypeError):
        async_conn.set_end_user_security_context()
    with pytest.raises(TypeError):
        async_conn.set_end_user_security_context(context, "extra")
    with pytest.raises(TypeError):
        async_conn.set_end_user_security_context("invalid")


async def test_ext_3111(async_conn):
    "E3111 - clear_end_user_security_context validates its arguments"
    with pytest.raises(TypeError):
        async_conn.clear_end_user_security_context("extra")


async def test_ext_3112(async_conn, test_env, deep_data_security_config):
    "E3112 - security context APIs fail on closed connections"
    await async_conn.close()
    context = oracledb.create_end_user_security_context(
        end_user_identity=deep_data_security_config.user_token,
        database_access_token=deep_data_security_config.db_token,
    )
    with test_env.assert_raises_full_code("DPY-1001"):
        async_conn.set_end_user_security_context(context)
    with test_env.assert_raises_full_code("DPY-1001"):
        async_conn.clear_end_user_security_context()


async def test_ext_3113(test_env, deep_data_security_config):
    "E3113 - the same configured user can be used concurrently"

    async def context_check():
        async with test_env.get_connection_async() as conn:
            await _assert_context_round_trip(conn, deep_data_security_config)

    await asyncio.gather(context_check(), context_check(), context_check())


async def test_ext_3114(
    test_env,
    deep_data_security_config,
):
    "E3114 - a security context can be used with a sessionless transaction"
    context = oracledb.create_end_user_security_context(
        end_user_identity=deep_data_security_config.user_token,
        database_access_token=deep_data_security_config.db_token,
    )
    async with test_env.get_connection_async() as conn1:
        conn1.set_end_user_security_context(context)
        transaction_id = await conn1.begin_sessionless_transaction()
        with conn1.cursor() as cur:
            assert (
                await _get_xs_username(cur)
                == deep_data_security_config.xs_user
            )
            await _assert_secured_session_context(
                cur, deep_data_security_config.xs_user
            )
        await conn1.suspend_sessionless_transaction()
    async with test_env.get_connection_async() as conn2:
        conn2.set_end_user_security_context(context)
        await conn2.resume_sessionless_transaction(transaction_id)
        with conn2.cursor() as cur:
            assert (
                await _get_xs_username(cur)
                == deep_data_security_config.xs_user
            )
            await _assert_secured_session_context(
                cur, deep_data_security_config.xs_user
            )
        await conn2.rollback()
