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
E3000 - Tests Deep Data Security.

These tests are only run when the following entries are set in the extended
configuration file:

    deep_data_security_db_token: path to the database access token file
    deep_data_security_user_token: path to the end user token file
    deep_data_security_xs_user: the Azure/IAM user name

For details on Deep Data Security refer to
https://docs-uat.us.oracle.com/en/database/oracle/oracle-database/26/ddscg/what-is-oracle-deep-data-security.html#GUID-E239A5C4-0C0D-4FF0-98DD-2E374F79C63C
"""

import collections
import queue
import threading

import pytest
import oracledb

DeepDataSecurityConfig = collections.namedtuple(
    "DeepDataSecurityConfig", "db_token user_token xs_user"
)


@pytest.fixture(autouse=True)
def module_checks(skip_unless_deep_data_security):
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


def _assert_base_session_context(cur, expected_schema_user):
    session_xs_user, current_xs_user, current_user, session_user = (
        _get_session_context(cur)
    )
    assert session_xs_user is None
    assert current_xs_user is None
    assert current_user == expected_schema_user
    assert session_user == expected_schema_user


def _assert_context_round_trip(conn, config):
    conn.set_end_user_security_context(
        oracledb.create_end_user_security_context(
            end_user_identity=config.user_token,
            database_access_token=config.db_token,
        )
    )
    with conn.cursor() as cur:
        assert _get_xs_username(cur) == config.xs_user
        cur.execute("""
            select
                sys_context('userenv', 'current_user'),
                xs_sys_context('xs$session', 'username')
            """)
        current_user, current_xs_user = cur.fetchone()
        assert current_user == "XS$NULL"
        assert current_xs_user == config.xs_user
        _assert_secured_session_context(cur, config.xs_user)


def _assert_secured_session_context(cur, expected_xs_user):
    session_xs_user, current_xs_user, current_user, session_user = (
        _get_session_context(cur)
    )
    assert (
        session_xs_user == expected_xs_user
        or current_xs_user == expected_xs_user
    )
    assert current_user == "XS$NULL"
    assert session_user == "XS$NULL"


def _get_session_context(cur):
    cur.execute("""
        select
            xs_sys_context('xs$session', 'session_xs_user'),
            xs_sys_context('xs$session', 'current_xs_user'),
            sys_context('userenv', 'current_user'),
            sys_context('userenv', 'session_user')
        """)
    return cur.fetchone()


def _get_xs_username(cur):
    cur.execute("select xs_sys_context('xs$session', 'username')")
    (value,) = cur.fetchone()
    return value


def test_ext_3000(conn, deep_data_security_config):
    "E3000 - example: create, set and clear a security context"
    _assert_context_round_trip(conn, deep_data_security_config)


def test_ext_3001(test_env, deep_data_security_config):
    "E3001 - example: use a security context with a pooled connection"
    pool = test_env.get_pool()
    with pool.acquire() as conn:
        _assert_context_round_trip(conn, deep_data_security_config)
    pool.close()


@pytest.mark.parametrize(
    "invalidate_user_token,expected_error",
    [(True, "ORA-52601"), (False, "ORA-52602")],
)
def test_ext_3002(
    conn,
    test_env,
    deep_data_security_config,
    invalidate_user_token,
    expected_error,
):
    "E3002 - invalid token inputs are rejected on use"
    if invalidate_user_token:
        end_user_identity = "invalid_token"
        database_access_token = deep_data_security_config.db_token
    else:
        end_user_identity = deep_data_security_config.user_token
        database_access_token = "invalid_token"
    conn.set_end_user_security_context(
        oracledb.create_end_user_security_context(
            end_user_identity=end_user_identity,
            database_access_token=database_access_token,
        )
    )
    with conn.cursor() as cur:
        with test_env.assert_raises_full_code(expected_error):
            _get_xs_username(cur)


@pytest.mark.parametrize(
    "nullify_user_token,null_value",
    [(True, ""), (True, None), (False, ""), (False, None)],
)
def test_ext_3003(deep_data_security_config, nullify_user_token, null_value):
    "E3003 - create_end_user_security_context requires non-empty strings"
    if nullify_user_token:
        end_user_identity = null_value
        database_access_token = deep_data_security_config.db_token
    else:
        end_user_identity = deep_data_security_config.user_token
        database_access_token = null_value
    with pytest.raises(ValueError):
        oracledb.create_end_user_security_context(
            end_user_identity=end_user_identity,
            database_access_token=database_access_token,
        )


def test_ext_3004(deep_data_security_config):
    "E3004 - create_end_user_security_context validates argument types"
    with pytest.raises(TypeError):
        oracledb.create_end_user_security_context()
    with pytest.raises(TypeError):
        oracledb.create_end_user_security_context(
            database_access_token=deep_data_security_config.db_token
        )
    with pytest.raises(TypeError):
        oracledb.create_end_user_security_context(
            end_user_identity=deep_data_security_config.user_token
        )
    with pytest.raises(ValueError):
        oracledb.create_end_user_security_context(
            end_user_identity=123,
            database_access_token=deep_data_security_config.db_token,
        )
    with pytest.raises(ValueError):
        oracledb.create_end_user_security_context(
            end_user_identity=deep_data_security_config.user_token,
            database_access_token=123,
        )


def test_ext_3005(conn, deep_data_security_config):
    "E3005 - the same security context can be reused after clear"
    context = oracledb.create_end_user_security_context(
        end_user_identity=deep_data_security_config.user_token,
        database_access_token=deep_data_security_config.db_token,
    )
    conn.set_end_user_security_context(context)
    with conn.cursor() as cur:
        assert _get_xs_username(cur) == deep_data_security_config.xs_user
        conn.clear_end_user_security_context()
        assert _get_xs_username(cur) is None
        conn.set_end_user_security_context(context)
        assert _get_xs_username(cur) == deep_data_security_config.xs_user


def test_ext_3006(conn, deep_data_security_config):
    "E3006 - clearing the security context twice is harmless"
    conn.set_end_user_security_context(
        oracledb.create_end_user_security_context(
            end_user_identity=deep_data_security_config.user_token,
            database_access_token=deep_data_security_config.db_token,
        )
    )
    with conn.cursor() as cur:
        assert _get_xs_username(cur) == deep_data_security_config.xs_user
        conn.clear_end_user_security_context()
        conn.clear_end_user_security_context()
        assert _get_xs_username(cur) is None


def test_ext_3007(conn, deep_data_security_config):
    "E3007 - setting None clears the current security context"
    conn.set_end_user_security_context(
        oracledb.create_end_user_security_context(
            end_user_identity=deep_data_security_config.user_token,
            database_access_token=deep_data_security_config.db_token,
        )
    )
    with conn.cursor() as cur:
        assert _get_xs_username(cur) == deep_data_security_config.xs_user
        conn.set_end_user_security_context(None)
        assert _get_xs_username(cur) is None


def test_ext_3008(conn, test_env, deep_data_security_config):
    "E3008 - a connection can recover after an invalid context"
    conn.set_end_user_security_context(
        oracledb.create_end_user_security_context(
            end_user_identity="invalid_token",
            database_access_token=deep_data_security_config.db_token,
        )
    )
    with conn.cursor() as cur:
        with test_env.assert_raises_full_code("ORA-52601"):
            _get_xs_username(cur)
        conn.clear_end_user_security_context()
        assert _get_xs_username(cur) is None
        conn.set_end_user_security_context(
            oracledb.create_end_user_security_context(
                end_user_identity=deep_data_security_config.user_token,
                database_access_token=deep_data_security_config.db_token,
            )
        )
        assert _get_xs_username(cur) == deep_data_security_config.xs_user


def test_ext_3009(conn, deep_data_security_config):
    "E3009 - clear_end_user_security_context restores the base session"
    with conn.cursor() as cur:
        cur.execute("select user")
        (schema_user,) = cur.fetchone()
        _assert_base_session_context(cur, schema_user)
        conn.set_end_user_security_context(
            oracledb.create_end_user_security_context(
                end_user_identity=deep_data_security_config.user_token,
                database_access_token=deep_data_security_config.db_token,
            )
        )
        _assert_secured_session_context(cur, deep_data_security_config.xs_user)
        conn.clear_end_user_security_context()
        _assert_base_session_context(cur, schema_user)


def test_ext_3010(test_env, deep_data_security_config):
    "E3010 - pooled connection reuse starts without the prior security context"
    pool = test_env.get_pool()
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute("select user from dual")
            (schema_user,) = cur.fetchone()
            conn.set_end_user_security_context(
                oracledb.create_end_user_security_context(
                    end_user_identity=deep_data_security_config.user_token,
                    database_access_token=deep_data_security_config.db_token,
                )
            )
            _assert_secured_session_context(
                cur, deep_data_security_config.xs_user
            )
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            _assert_base_session_context(cur, schema_user)
    pool.close()


def test_ext_3011(conn, deep_data_security_config):
    "E3011 - clearing before the first round-trip drops the pending context"
    with conn.cursor() as cur:
        cur.execute("select user from dual")
        (schema_user,) = cur.fetchone()
        conn.set_end_user_security_context(
            oracledb.create_end_user_security_context(
                end_user_identity=deep_data_security_config.user_token,
                database_access_token=deep_data_security_config.db_token,
            )
        )
        conn.clear_end_user_security_context()
        _assert_base_session_context(cur, schema_user)


def test_ext_3012(conn):
    "E3012 - clear_end_user_security_context can be called before set"
    conn.clear_end_user_security_context()
    with conn.cursor() as cur:
        assert _get_xs_username(cur) is None


def test_ext_3013(conn, deep_data_security_config):
    "E3013 - set_end_user_security_context validates its arguments"
    context = oracledb.create_end_user_security_context(
        end_user_identity=deep_data_security_config.user_token,
        database_access_token=deep_data_security_config.db_token,
    )
    with pytest.raises(TypeError):
        conn.set_end_user_security_context()
    with pytest.raises(TypeError):
        conn.set_end_user_security_context(context, "extra")
    with pytest.raises(TypeError):
        conn.set_end_user_security_context("invalid")


def test_ext_3014(conn):
    "E3014 - clear_end_user_security_context validates its arguments"
    with pytest.raises(TypeError):
        conn.clear_end_user_security_context("extra")


def test_ext_3015(conn, test_env, deep_data_security_config):
    "E3015 - security context APIs fail on closed connections"
    conn.close()
    context = oracledb.create_end_user_security_context(
        end_user_identity=deep_data_security_config.user_token,
        database_access_token=deep_data_security_config.db_token,
    )
    with test_env.assert_raises_full_code("DPY-1001"):
        conn.set_end_user_security_context(context)
    with test_env.assert_raises_full_code("DPY-1001"):
        conn.clear_end_user_security_context()


def test_ext_3016(test_env, deep_data_security_config):
    "E3016 - the same configured user can be used concurrently"
    threads = []
    errors = queue.Queue()

    def thread_context_check():
        try:
            with test_env.get_connection() as conn:
                _assert_context_round_trip(conn, deep_data_security_config)
        except Exception as e:
            errors.put(e)

    for _ in range(3):
        thread = threading.Thread(target=thread_context_check)
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    if not errors.empty():
        raise errors.get()


def test_ext_3017(
    test_env,
    deep_data_security_config,
):
    "E3017 - a security context can be used with a sessionless transaction"
    context = oracledb.create_end_user_security_context(
        end_user_identity=deep_data_security_config.user_token,
        database_access_token=deep_data_security_config.db_token,
    )
    with test_env.get_connection() as conn1:
        conn1.set_end_user_security_context(context)
        transaction_id = conn1.begin_sessionless_transaction()
        with conn1.cursor() as cur:
            assert _get_xs_username(cur) == deep_data_security_config.xs_user
            _assert_secured_session_context(
                cur, deep_data_security_config.xs_user
            )
        conn1.suspend_sessionless_transaction()
    with test_env.get_connection() as conn2:
        conn2.set_end_user_security_context(context)
        conn2.resume_sessionless_transaction(transaction_id)
        with conn2.cursor() as cur:
            assert _get_xs_username(cur) == deep_data_security_config.xs_user
            _assert_secured_session_context(
                cur, deep_data_security_config.xs_user
            )
        conn2.rollback()
