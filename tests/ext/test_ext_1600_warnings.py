# -----------------------------------------------------------------------------
# Copyright (c) 2024, Oracle and/or its affiliates.
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
import test_env


class TestCase(test_env.BaseTestCase):
    profile_name = "profile_ext_test_1600"
    user_name = "user_ext_test_1600"
    requires_connection = False

    @classmethod
    def setUpClass(cls):
        conn = test_env.get_admin_connection()
        password = test_env.get_main_password()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            declare
                e_user_missing exception;
                pragma exception_init(e_user_missing, -1918);
            begin
                execute immediate('drop user {cls.user_name} cascade');
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
                execute immediate('drop profile {cls.profile_name}');
            exception
            when e_user_missing then
                null;
            end;
            """
        )
        cursor.execute(f"create user {cls.user_name} identified by {password}")
        cursor.execute(f"grant create session to {cls.user_name}")
        cursor.execute(
            f"""
            create profile {cls.profile_name} limit
            password_life_time 1 / 24 / 60 / 60
            password_grace_time 7
            """
        )
        cursor.execute(
            f"alter user {cls.user_name} profile {cls.profile_name}"
        )
        time.sleep(2)

    @classmethod
    def tearDownClass(cls):
        conn = test_env.get_admin_connection()
        cursor = conn.cursor()
        cursor.execute(f"drop user {cls.user_name} cascade")
        cursor.execute(f"drop profile {cls.profile_name}")

    def test_ext_1600(self):
        "E1600 - test standalone connection generates a warning"
        password = test_env.get_main_password()
        with oracledb.connect(
            user=self.user_name,
            password=password,
            dsn=test_env.get_connect_string(),
        ) as conn:
            self.assertIn(conn.warning.full_code, ["ORA-28002", "ORA-28098"])

    def test_ext_1601_pooled_conn_warning_min_0(self):
        "E1601 - test pooled connection generates a warning (min 0)"
        password = test_env.get_main_password()
        pool = oracledb.create_pool(
            user=self.user_name,
            password=password,
            dsn=test_env.get_connect_string(),
            min=0,
            max=5,
            increment=1,
        )
        with pool.acquire() as conn:
            self.assertIn(conn.warning.full_code, ["ORA-28002", "ORA-28098"])
        with pool.acquire() as conn:
            self.assertIsNone(conn.warning)
        pool.close(0)

    def test_ext_1602_pooled_conn_warning_min_1(self):
        "E1602 - test pooled connection generates a warning (min 1)"
        password = test_env.get_main_password()
        pool = oracledb.create_pool(
            user=self.user_name,
            password=password,
            dsn=test_env.get_connect_string(),
            min=1,
            max=5,
            increment=1,
        )
        with pool.acquire() as conn:
            self.assertIn(conn.warning.full_code, ["ORA-28002", "ORA-28098"])
        with pool.acquire() as conn:
            self.assertIsNone(conn.warning)
        pool.close(0)


if __name__ == "__main__":
    test_env.run_test_cases()
