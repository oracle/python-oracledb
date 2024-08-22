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
E1400 - Module for testing inband notification. No special setup is required
but the test makes use of debugging packages that are not intended for normal
use.
"""

import test_env


class TestCase(test_env.BaseTestCase):
    requires_connection = False

    @classmethod
    def setUpClass(cls):
        cls.admin_conn = test_env.get_admin_connection()
        user = test_env.get_main_user()
        with cls.admin_conn.cursor() as cursor:
            cursor.execute(f"grant execute on dbms_tg_dbg to {user}")

    @classmethod
    def tearDownClass(cls):
        user = test_env.get_main_user()
        with cls.admin_conn.cursor() as cursor:
            cursor.execute(f"revoke execute on dbms_tg_dbg from {user}")

    def test_ext_1400(self):
        "E1400 - test standalone connection is marked unhealthy"
        conn = test_env.get_connection()
        self.assertEqual(conn.is_healthy(), True)
        with conn.cursor() as cursor:
            cursor.callproc("dbms_tg_dbg.set_session_drainable")
            cursor.execute("select user from dual")
            (user,) = cursor.fetchone()
            self.assertEqual(user, test_env.get_main_user().upper())
        self.assertEqual(conn.is_healthy(), False)

    def test_ext_1401(self):
        "E1401 - test pooled connection that is marked unhealthy"
        pool = test_env.get_pool(min=1, max=1, increment=1)
        with pool.acquire() as conn:
            self.assertEqual(conn.is_healthy(), True)
            with conn.cursor() as cursor:
                cursor.callproc("dbms_tg_dbg.set_session_drainable")
                info = self.get_sid_serial(conn)
            self.assertEqual(conn.is_healthy(), False)
            with conn.cursor() as cursor:
                cursor.execute("select user from dual")
                (user,) = cursor.fetchone()
                self.assertEqual(user, test_env.get_main_user().upper())
        with pool.acquire() as conn:
            self.assertEqual(conn.is_healthy(), True)
            new_info = self.get_sid_serial(conn)
            self.assertNotEqual(new_info, info)

    def test_ext_1402(self):
        "E1402 - test pooled connection is dropped from pool"
        pool = test_env.get_pool(min=1, max=1, increment=1)
        with pool.acquire() as conn:
            self.assertEqual(conn.is_healthy(), True)
            info = self.get_sid_serial(conn)
        with pool.acquire() as conn:
            new_info = self.get_sid_serial(conn)
            self.assertEqual(new_info, info)
            with conn.cursor() as cursor:
                cursor.callproc("dbms_tg_dbg.set_session_drainable")
        with pool.acquire() as conn:
            self.assertEqual(conn.is_healthy(), True)
            new_info = self.get_sid_serial(conn)
            self.assertNotEqual(new_info, info)


if __name__ == "__main__":
    test_env.run_test_cases()
