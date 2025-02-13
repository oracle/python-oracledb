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
E1000 - Module for testing pool strinking. No special setup is required but the
tests here will only be run if the run_long_tests value is enabled.
"""

import time
import unittest

import test_env


@unittest.skipUnless(
    test_env.get_extended_config_bool("run_long_tests"),
    "extended configuration run_long_tests is disabled",
)
class TestCase(test_env.BaseTestCase):
    def test_ext_1000(self):
        "E1000 - test pool timeout with simple acquire after waiting"
        pool = test_env.get_pool(min=3, max=10, increment=1, timeout=5)
        conns = [pool.acquire() for i in range(7)]
        self.assertEqual(pool.opened, 7)
        for conn in conns:
            conn.close()
        time.sleep(10)
        conn = pool.acquire()
        self.assertEqual(pool.opened, 3)

    def test_ext_1001(self):
        "E1001 - test pool timeout with older connection returned first"
        pool = test_env.get_pool(min=2, max=5, increment=1, timeout=3)
        conns = [pool.acquire() for i in range(3)]
        conns[2].close()
        for i in range(10):
            with pool.acquire() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("select 1 from dual")
        time.sleep(4)
        conn = pool.acquire()
        self.assertEqual(pool.opened, 3)

    @unittest.skipUnless(test_env.get_is_thin(), "doesn't occur in thick mode")
    def test_ext_1002(self):
        "E1002 - test pool timeout shrinks to min on pool inactivity"
        pool = test_env.get_pool(min=3, max=10, increment=2, timeout=4)
        conns = [pool.acquire() for i in range(6)]
        self.assertEqual(pool.opened, 6)
        for conn in conns:
            conn.close()
        time.sleep(6)
        self.assertEqual(pool.opened, 3)

    @unittest.skipUnless(test_env.get_is_thin(), "doesn't occur in thick mode")
    def test_ext_1003(self):
        "E1003 - test pool timeout eliminates extra connections on inactivity"
        pool = test_env.get_pool(min=4, max=10, increment=4, timeout=3)
        conns = [pool.acquire() for i in range(5)]
        self.assertEqual(pool.opened, 5)
        time.sleep(2)
        self.assertEqual(pool.opened, 8)
        time.sleep(3)
        self.assertEqual(pool.opened, 5)
        del conns

    @unittest.skipUnless(test_env.get_is_thin(), "doesn't occur in thick mode")
    def test_ext_1004(self):
        "E1004 - test pool max_lifetime_session on release"
        pool = test_env.get_pool(
            min=4, max=10, increment=4, max_lifetime_session=3
        )
        conns = [pool.acquire() for i in range(5)]
        self.assertEqual(pool.opened, 5)
        time.sleep(2)
        self.assertEqual(pool.opened, 8)
        time.sleep(2)
        for conn in conns:
            conn.close()
        time.sleep(2)
        self.assertEqual(pool.opened, 4)

    @unittest.skipUnless(test_env.get_is_thin(), "doesn't occur in thick mode")
    def test_ext_1005(self):
        "E1005 - test pool max_lifetime_session on acquire"
        pool = test_env.get_pool(
            min=4, max=10, increment=4, max_lifetime_session=4
        )
        conns = [pool.acquire() for i in range(5)]
        self.assertEqual(pool.opened, 5)
        time.sleep(2)
        self.assertEqual(pool.opened, 8)
        for conn in conns:
            conn.close()
        time.sleep(4)
        with pool.acquire():
            pass
        time.sleep(2)
        self.assertEqual(pool.opened, 4)


if __name__ == "__main__":
    test_env.run_test_cases()
