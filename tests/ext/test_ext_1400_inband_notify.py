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
E1400 - Module for testing inband notification. No special setup is required
but the test makes use of debugging packages that are not intended for normal
use with Oracle Database 19c.
"""

import threading
import time

import pytest


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


def mark_session_drainable(test_env, conn, use_package):
    """
    Marks the session as drainable so that the inband notification is sent. If
    the package is not used, a thread is used to disconnect the session
    instead.
    """
    assert conn.is_healthy()
    if use_package:
        conn.cursor().callproc("dbms_tg_dbg.set_session_drainable")
    else:
        sid, serial = test_env.get_sid_serial(conn)
        admin_conn = test_env.get_admin_connection()
        sql = f"alter system disconnect session '{sid},{serial}' drain"
        thread = threading.Thread(
            target=admin_conn.cursor().execute, args=(sql,)
        )
        thread.start()
        time.sleep(1)
        return thread


def test_ext_1400(test_env, use_package):
    "E1400 - test standalone connection is marked unhealthy"
    with test_env.get_connection() as conn:
        thread = mark_session_drainable(test_env, conn, use_package)
        with conn.cursor() as cursor:
            cursor.execute("select user from dual")
            (user,) = cursor.fetchone()
            assert user == test_env.main_user.upper()
        assert not conn.is_healthy()
    if thread is not None:
        thread.join()


def test_ext_1401(test_env, use_package):
    "E1401 - test pooled connection that is marked unhealthy"
    pool = test_env.get_pool(min=1, max=1, increment=1)
    with pool.acquire() as conn:
        assert conn.is_healthy()
        info = test_env.get_sid_serial(conn)
    with pool.acquire() as conn:
        assert test_env.get_sid_serial(conn) == info
        thread = mark_session_drainable(test_env, conn, use_package)
        with conn.cursor() as cursor:
            cursor.execute("select user from dual")
            (user,) = cursor.fetchone()
            assert user == test_env.main_user.upper()
    with pool.acquire() as conn:
        assert conn.is_healthy()
        new_info = test_env.get_sid_serial(conn)
        assert new_info != info
    if thread is not None:
        thread.join()
