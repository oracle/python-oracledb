# -----------------------------------------------------------------------------
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
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
5000 - Module for testing external authentication
"""

import oracledb
import pytest


@pytest.fixture(autouse=True)
def skip_if_no_external_auth(test_env):
    if not test_env.external_user:
        pytest.skip("external authentication not configured")


def _verify_connection(conn, expected_user, expected_proxy_user=None):
    with conn.cursor() as cursor:
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
        assert (
            actual_proxy_user == expected_proxy_user
            and expected_proxy_user.upper()
        )


def test_5000(test_env):
    """
    5000 - test error on creating a pool with user and password specified
    and externalauth enabled
    """
    with test_env.assert_raises_full_code("DPI-1032"):
        test_env.get_pool(
            min=1,
            max=2,
            increment=1,
            getmode=oracledb.POOL_GETMODE_WAIT,
            externalauth=True,
            homogeneous=False,
        )


def test_5001(test_env):
    """
    5001 - test error on creating a pool without password and with user
    specified and externalauth enabled
    """
    with test_env.assert_raises_full_code("DPI-1032"):
        oracledb.create_pool(
            user=test_env.main_user,
            min=1,
            max=2,
            increment=1,
            getmode=oracledb.POOL_GETMODE_WAIT,
            externalauth=True,
            homogeneous=False,
        )


def test_5002(test_env):
    """
    5002 - test error on creating a pool without user and with password
    specified and externalauth enabled
    """
    with test_env.assert_raises_full_code("DPI-1032"):
        oracledb.create_pool(
            password=test_env.main_password,
            min=1,
            max=2,
            increment=1,
            getmode=oracledb.POOL_GETMODE_WAIT,
            externalauth=True,
            homogeneous=False,
        )


def test_5003(test_env):
    """
    5003 - test creating a pool with user and password specified and
    externalauth set to False
    """
    pool = test_env.get_pool(
        min=1,
        max=2,
        increment=1,
        getmode=oracledb.POOL_GETMODE_WAIT,
        externalauth=False,
        homogeneous=False,
    )
    with pool.acquire() as conn:
        _verify_connection(conn, test_env.main_user)


def test_5004(test_env):
    """
    5004 - test error when connecting with user and password specified
    and externalauth enabled
    """
    with test_env.assert_raises_full_code("DPI-1032"):
        oracledb.connect(
            user=test_env.main_user,
            password=test_env.main_password,
            dsn=test_env.connect_string,
            externalauth=True,
        )


def test_5005(test_env):
    """
    5005 - test error when connecting without username and with password
    specified and externalauth enabled
    """
    with test_env.assert_raises_full_code("DPI-1032"):
        oracledb.connect(
            password=test_env.main_password,
            dsn=test_env.connect_string,
            externalauth=True,
        )

    # by default externalauth is False
    with test_env.assert_raises_full_code("ORA-01017"):
        oracledb.connect(
            password=test_env.main_password,
            dsn=test_env.connect_string,
        )


def test_5006(test_env):
    """
    5006 - test error when connecting without password and with user
    specified and externalauth enabled
    """
    with test_env.assert_raises_full_code("ORA-01017"):
        oracledb.connect(
            user="[invalid_user]",
            dsn=test_env.connect_string,
            externalauth=True,
        )

    # by default externalauth is False
    with test_env.assert_raises_full_code("ORA-01017"):
        oracledb.connect(user="[invalid_user]", dsn=test_env.connect_string)


def test_5007(test_env):
    "5007 - test external authentication with invalid proxy user"
    with test_env.assert_raises_full_code("DPI-1069"):
        oracledb.connect(
            user=test_env.main_user,
            dsn=test_env.connect_string,
            externalauth=True,
        )

    # by default externalauth is False
    with test_env.assert_raises_full_code("DPY-4001"):
        oracledb.connect(
            user=test_env.main_user,
            dsn=test_env.connect_string,
        )


def test_5008(test_env):
    """
    5008 - test creating a connection with user and password specified and
    externalauth set to False
    """
    conn = oracledb.connect(
        user=test_env.main_user,
        password=test_env.main_password,
        dsn=test_env.connect_string,
        externalauth=False,
    )
    _verify_connection(conn, test_env.main_user)


def test_5009(test_env):
    """
    5009 - test creating standalone connection with externalauth set to
    True explicitly
    """
    conn = oracledb.connect(dsn=test_env.connect_string, externalauth=True)
    _verify_connection(conn, test_env.external_user)


def test_5010(test_env):
    """
    5010 - test creating standalone connection with no user and password
    specified and externalauth not set
    """
    conn = oracledb.connect(dsn=test_env.connect_string)
    _verify_connection(conn, test_env.external_user)


def test_5011(test_env):
    "5011 - test creating a pool with external authentication"
    pool = oracledb.create_pool(
        dsn=test_env.connect_string,
        min=1,
        max=2,
        increment=1,
        getmode=oracledb.POOL_GETMODE_WAIT,
        externalauth=True,
        homogeneous=False,
    )
    assert pool.opened == 0
    with pool.acquire() as conn:
        _verify_connection(conn, test_env.external_user)


def test_5012(test_env):
    """
    5012 - test creating a pool without user and password specified and
    externalauth not set
    """
    pool = oracledb.create_pool(
        dsn=test_env.connect_string,
        min=1,
        max=2,
        increment=1,
        getmode=oracledb.POOL_GETMODE_WAIT,
        homogeneous=False,
    )
    with test_env.assert_raises_full_code("ORA-24415"):
        pool.acquire()


def test_5013(test_env):
    "5013 - test pool min is always 0 under external authentication"
    pool = oracledb.create_pool(
        dsn=test_env.connect_string,
        min=5,
        max=10,
        increment=3,
        getmode=oracledb.POOL_GETMODE_WAIT,
        externalauth=True,
        homogeneous=False,
    )
    assert pool.opened == 0


def test_5014(test_env):
    "5014 - test pool increment is always 1 under external authentication"
    pool = oracledb.create_pool(
        dsn=test_env.connect_string,
        min=5,
        max=10,
        increment=3,
        getmode=oracledb.POOL_GETMODE_WAIT,
        externalauth=True,
        homogeneous=False,
    )
    conn1 = pool.acquire()
    assert pool.opened == 1
    conn2 = pool.acquire()
    assert pool.opened == 2
    conn1.close()
    conn2.close()


def test_5015(test_env):
    "5015 - test external authentication with proxy"
    proxy_user = test_env.external_user
    schema_user = test_env.main_user
    conn1 = oracledb.connect(
        user=f"[{schema_user}]",
        dsn=test_env.connect_string,
        externalauth=True,
    )
    _verify_connection(conn1, schema_user, proxy_user)
    conn2 = oracledb.connect(
        user=f"[{schema_user}]", dsn=test_env.connect_string
    )
    _verify_connection(conn2, schema_user, proxy_user)


def test_5016(test_env):
    "5016 - test creating pool using external authentication with proxy"
    proxy_user = test_env.external_user
    schema_user = test_env.main_user
    pool = oracledb.create_pool(
        externalauth=True,
        homogeneous=False,
        dsn=test_env.connect_string,
        min=1,
        max=2,
        increment=1,
        getmode=oracledb.POOL_GETMODE_WAIT,
    )
    assert pool.opened == 0
    conn = pool.acquire(user=f"[{schema_user}]")
    _verify_connection(conn, schema_user, proxy_user)
