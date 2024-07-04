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
E1700 - Module for testing the generation of warnings with asyncio. No special
setup is required but sys privilege is required in order to create and drop
users.
"""

import asyncio
import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    profile_name = "profile_priv_test_1700"
    user_name = "user_priv_test_1700"
    requires_connection = False
    setup_completed = False

    async def __perform_setup(self):
        """
        Perform the setup, if necessary.
        """
        if self.__class__.setup_completed:
            return
        conn = await test_env.get_admin_connection_async()
        password = test_env.get_main_password()
        cursor = conn.cursor()
        await cursor.execute(
            f"""
            declare
                e_user_missing exception;
                pragma exception_init(e_user_missing, -1918);
            begin
                execute immediate('drop user {self.user_name} cascade');
            exception
            when e_user_missing then
                null;
            end;
            """
        )
        await cursor.execute(
            f"""
            declare
                e_user_missing exception;
                pragma exception_init(e_user_missing, -2380);
            begin
                execute immediate('drop profile {self.profile_name}');
            exception
            when e_user_missing then
                null;
            end;
            """
        )
        await cursor.execute(
            f"create user {self.user_name} identified by {password}"
        )
        await cursor.execute(f"grant create session to {self.user_name}")
        await cursor.execute(
            f"""
            create profile {self.profile_name} limit
            password_life_time 1 / 24 / 60 / 60
            password_grace_time 7
            """
        )
        await cursor.execute(
            f"alter user {self.user_name} profile {self.profile_name}"
        )
        await asyncio.sleep(2)
        self.__class__.setup_completed = True

    async def test_ext_1700(self):
        "E1700 - test standalone connection generates a warning"
        await self.__perform_setup()
        password = test_env.get_main_password()
        async with oracledb.connect_async(
            user=self.user_name,
            password=password,
            dsn=test_env.get_connect_string(),
        ) as conn:
            self.assertIn(conn.warning.full_code, ["ORA-28002", "ORA-28098"])

    async def test_ext_1701(self):
        "E1701 - test pooled connection generates a warning (min 0)"
        await self.__perform_setup()
        password = test_env.get_main_password()
        pool = oracledb.create_pool_async(
            user=self.user_name,
            password=password,
            dsn=test_env.get_connect_string(),
            min=0,
            max=5,
            increment=1,
        )
        async with pool.acquire() as conn:
            self.assertIn(conn.warning.full_code, ["ORA-28002", "ORA-28098"])
        async with pool.acquire() as conn:
            self.assertIsNone(conn.warning)
        await pool.close(0)

    async def test_ext_1702(self):
        "E1702 - test pooled connection generates a warning (min 1)"
        await self.__perform_setup()
        password = test_env.get_main_password()
        pool = oracledb.create_pool_async(
            user=self.user_name,
            password=password,
            dsn=test_env.get_connect_string(),
            min=1,
            max=5,
            increment=1,
        )
        async with pool.acquire() as conn:
            self.assertIn(conn.warning.full_code, ["ORA-28002", "ORA-28098"])
        async with pool.acquire() as conn:
            self.assertIsNone(conn.warning)
        await pool.close(0)


if __name__ == "__main__":
    test_env.run_test_cases()
