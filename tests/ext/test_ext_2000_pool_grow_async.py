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
E2000 - Module for testing pool growth with asyncio when sessions are killed.
No special setup is required but the tests here will only be run if the
run_long_tests value is enabled.
"""

# -----------------------------------------------------------------------------
# priv_test_2000_pool_grow.py
#
# Private tests for testing pool growth when sessions are killed. No special
# setup is required.
# -----------------------------------------------------------------------------

import asyncio
import unittest

import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
@unittest.skipUnless(
    test_env.get_extended_config_bool("run_long_tests"),
    "extended configuration run_long_tests is disabled",
)
class TestCase(test_env.BaseAsyncTestCase):
    requires_connection = False

    async def test_ext_2000(self):
        "E2000 - test static pool grows back to the min after sessions killed"
        pool = test_env.get_pool_async(
            min=5, max=5, increment=1, ping_interval=0
        )
        conns = [await pool.acquire() for i in range(5)]
        admin_conn = await test_env.get_admin_connection_async()
        with admin_conn.cursor() as admin_cursor:
            for conn in conns:
                sid, serial = await self.get_sid_serial(conn)
                kill_sql = f"alter system kill session '{sid},{serial}'"
                await admin_cursor.execute(kill_sql)
        await admin_conn.close()
        for conn in conns:
            await conn.close()
        conns.clear()
        conn = await pool.acquire()
        await asyncio.sleep(2)
        self.assertEqual(pool.opened, pool.min)


if __name__ == "__main__":
    test_env.run_test_cases()
