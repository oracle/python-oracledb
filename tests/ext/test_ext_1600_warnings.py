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
E1600 - Module for testing the generation of warnings. No special setup is
required but sys privilege is required in order to create and drop users.
"""

import time

import oracledb
import pytest

PROFILE_NAME = "profile_ext_test_1600"
USER_NAME = "user_ext_test_1600"


@pytest.fixture(scope="module", autouse=True)
def setup_user(test_env):
    password = test_env.main_password
    with test_env.get_admin_connection() as admin_conn:
        cursor = admin_conn.cursor()
        cursor.execute(
            f"""
            declare
                e_user_missing exception;
                pragma exception_init(e_user_missing, -1918);
            begin
                execute immediate('drop user {USER_NAME} cascade');
            exception
            when e_user_missing then
                null;
            end;
            """
        )
        cursor.execute(
            f"""
            declare
                e_user_missing exception;
                pragma exception_init(e_user_missing, -2380);
            begin
                execute immediate('drop profile {PROFILE_NAME}');
            exception
            when e_user_missing then
                null;
            end;
            """
        )
        cursor.execute(f"create user {USER_NAME} identified by {password}")
        cursor.execute(f"grant create session to {USER_NAME}")
        cursor.execute(
            f"""
            create profile {PROFILE_NAME} limit
            password_life_time 1 / 24 / 60 / 60
            password_grace_time 7
            """
        )
        cursor.execute(f"alter user {USER_NAME} profile {PROFILE_NAME}")
        time.sleep(2)
        yield
        cursor.execute(f"drop user {USER_NAME} cascade")
        cursor.execute(f"drop profile {PROFILE_NAME}")


def test_ext_1600(test_env):
    "E1600 - test standalone connection generates a warning"
    with oracledb.connect(
        user=USER_NAME,
        password=test_env.main_password,
        dsn=test_env.connect_string,
    ) as conn:
        assert conn.warning.full_code in ["ORA-28002", "ORA-28098"]


def test_ext_1601_pooled_conn_warning_min_0(test_env):
    "E1601 - test pooled connection generates a warning (min 0)"
    pool = oracledb.create_pool(
        user=USER_NAME,
        password=test_env.main_password,
        dsn=test_env.connect_string,
        min=0,
        max=5,
        increment=1,
    )
    with pool.acquire() as conn:
        assert conn.warning.full_code in ["ORA-28002", "ORA-28098"]
    with pool.acquire() as conn:
        assert conn.warning is None
    pool.close(0)


def test_ext_1602_pooled_conn_warning_min_1(test_env):
    "E1602 - test pooled connection generates a warning (min 1)"
    pool = oracledb.create_pool(
        user=USER_NAME,
        password=test_env.main_password,
        dsn=test_env.connect_string,
        min=1,
        max=5,
        increment=1,
    )
    with pool.acquire() as conn:
        assert conn.warning.full_code in ["ORA-28002", "ORA-28098"]
    with pool.acquire() as conn:
        assert conn.warning is None
    pool.close(0)
