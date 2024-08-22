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
E1800 - Module for testing inband notification with asyncio. No special setup
is required but the test makes use of debugging packages that are not intended
for normal use.
"""

# -----------------------------------------------------------------------------
# priv_test_1800_inband_notif_async.py
#
# Private tests for testing inband notification with asyncio. No special setup
# is required.
# -----------------------------------------------------------------------------

import unittest

import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    requires_connection = False
    setup_completed = False

    async def __perform_setup(self):
        """
        Perform setup, if needed.
        """
        if self.__class__.setup_completed:
            return
        user = test_env.get_main_user()
        async with test_env.get_admin_connection(use_async=True) as conn:
            with conn.cursor() as cursor:
                await cursor.execute(f"grant execute on dbms_tg_dbg to {user}")
        self.__class__.setup_completed = True

    async def test_ext_1800(self):
        "E1800 - test standalone connection is marked unhealthy"
        await self.__perform_setup()
        async with test_env.get_connection_async() as conn:
            self.assertEqual(conn.is_healthy(), True)
            with conn.cursor() as cursor:
                await cursor.callproc("dbms_tg_dbg.set_session_drainable")
                await cursor.execute("select user from dual")
                (user,) = await cursor.fetchone()
                self.assertEqual(user, test_env.get_main_user().upper())
            self.assertEqual(conn.is_healthy(), False)

    async def test_ext_1801(self):
        "E1801 - test pooled connection that is marked unhealthy"
        await self.__perform_setup()
        pool = test_env.get_pool_async(min=1, max=1, increment=1)
        async with pool.acquire() as conn:
            self.assertEqual(conn.is_healthy(), True)
            with conn.cursor() as cursor:
                await cursor.callproc("dbms_tg_dbg.set_session_drainable")
                info = await self.get_sid_serial(conn)
            self.assertEqual(conn.is_healthy(), False)
            with conn.cursor() as cursor:
                await cursor.execute("select user from dual")
                (user,) = await cursor.fetchone()
                self.assertEqual(user, test_env.get_main_user().upper())
        async with pool.acquire() as conn:
            self.assertEqual(conn.is_healthy(), True)
            new_info = await self.get_sid_serial(conn)
            self.assertNotEqual(new_info, info)
        await pool.close()

    async def test_ext_1802(self):
        "E1802 - test pooled connection is dropped from pool"
        await self.__perform_setup()
        pool = test_env.get_pool_async(min=1, max=1, increment=1)
        async with pool.acquire() as conn:
            self.assertEqual(conn.is_healthy(), True)
            info = await self.get_sid_serial(conn)
        async with pool.acquire() as conn:
            new_info = await self.get_sid_serial(conn)
            self.assertEqual(new_info, info)
            with conn.cursor() as cursor:
                await cursor.callproc("dbms_tg_dbg.set_session_drainable")
        async with pool.acquire() as conn:
            self.assertEqual(conn.is_healthy(), True)
            new_info = await self.get_sid_serial(conn)
            self.assertNotEqual(new_info, info)


if __name__ == "__main__":
    test_env.run_test_cases()
