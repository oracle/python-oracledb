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
E1300 - Module for testing the 11g and 12c verifier types. No special
configuration is needed but a user is created and dropped.
"""

import oracledb
import pytest

USER = "ext_test_1300_user"


@pytest.fixture(scope="module")
def admin_conn(test_env):
    """
    Returns the password to use for the user that is created.
    """
    with test_env.get_admin_connection() as conn:
        yield conn


@pytest.fixture(scope="module")
def user_password(test_env):
    """
    Returns the password to use for the user that is created.
    """
    return test_env.get_random_string()


@pytest.fixture(scope="module")
def verifier_data(admin_conn, test_env, user_password):
    """
    Returns the verifier data after creating a user with the given password.
    """
    with admin_conn.cursor() as cursor:
        cursor.execute(
            "select count(*) from user$ where name = :1",
            [USER.upper()],
        )
        (count,) = cursor.fetchone()
        keyword = "create" if count == 0 else "alter"
        cursor.execute(f"{keyword} user {USER} identified by {user_password}")
        cursor.execute(
            "select spare4 from user$ where name = :1", [USER.upper()]
        )
        (verifier_data,) = cursor.fetchone()
        cursor.execute(f"drop user {USER}")
        yield verifier_data
        user = test_env.main_user
        password = test_env.main_password
        cursor.execute(f"alter user {user} identified by {password}")


@pytest.mark.parametrize("ix", [0, 1])
def test_ext_1300(ix, admin_conn, test_env, verifier_data, user_password):
    "E1300 - test with different verifiers"
    user = test_env.main_user
    verifier = verifier_data.split(";")[ix]
    sql = f"alter user {user} identified by values '{verifier}'"
    with admin_conn.cursor() as cursor:
        cursor.execute(sql)
    with oracledb.connect(
        user=user, password=user_password, dsn=test_env.connect_string
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute("select user from dual")
            (fetched_user,) = cursor.fetchone()
            assert fetched_user == user.upper()
