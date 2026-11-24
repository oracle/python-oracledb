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
E1800 - Module for testing inband notification with asyncio. No special setup
is required but the test makes use of debugging packages that are not intended
for normal use with Oracle Database 19c.
"""

import asyncio

import pytest


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


@pytest.fixture(scope="module", autouse=True)
def use_package(test_env, server_version):
    """
    Returns whether or not the setup requires use of the package or not. The
    package must be used prior to Oracle AI Database 26ai but may not be used
    for recent versions of the database. If the package is needed, the grant is
    made for the duration of the test and revoked afterwards.
    """
    test_env.skip_unless_server_version(19)
    use_package = server_version[0] < 23
    user = test_env.main_user
    with test_env.get_admin_connection() as admin_conn:
        with admin_conn.cursor() as cursor:
            if use_package:
                cursor.execute(f"grant execute on dbms_tg_dbg to {user}")
            yield use_package
            if use_package:
                cursor.execute(f"revoke execute on dbms_tg_dbg from {user}")


async def mark_session_drainable(test_env, conn, use_package):
    """
    Marks the session as drainable so that the inband notification is sent. If
    the package is not used, a thread is used to disconnect the session
    instead.
    """
    assert conn.is_healthy()
    if use_package:
        await conn.callproc("dbms_tg_dbg.set_session_drainable")
    else:
        sid, serial = (conn.session_id, conn.serial_num)
        admin_conn = await test_env.get_admin_connection_async()
        sql = f"alter system disconnect session '{sid},{serial}' drain"
        task = asyncio.create_task(admin_conn.execute(sql))
        await asyncio.sleep(1)
        return task


async def test_ext_1800(test_env, use_package):
    "E1800 - test standalone connection is marked unhealthy"
    async with test_env.get_connection_async() as conn:
        task = await mark_session_drainable(test_env, conn, use_package)
        with conn.cursor() as cursor:
            await cursor.execute("select user from dual")
            (user,) = await cursor.fetchone()
            assert user == test_env.main_user.upper()
        assert not conn.is_healthy()
    if task is not None:
        await task


async def test_ext_1801(test_env, use_package):
    "E1801 - test pooled connection that is marked unhealthy"
    pool = test_env.get_pool_async(min=1, max=1, increment=1)
    async with pool.acquire() as conn:
        assert conn.is_healthy()
        info = (conn.session_id, conn.serial_num)
    async with pool.acquire() as conn:
        assert (conn.session_id, conn.serial_num) == info
        task = await mark_session_drainable(test_env, conn, use_package)
        with conn.cursor() as cursor:
            await cursor.execute("select user from dual")
            (user,) = await cursor.fetchone()
            assert user == test_env.main_user.upper()
        assert not conn.is_healthy()
    async with pool.acquire() as conn:
        assert conn.is_healthy()
        assert (conn.session_id, conn.serial_num) != info
    await pool.close()
    if task is not None:
        await task
