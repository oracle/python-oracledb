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
E1500 - Module for testing pool growth when sessions are killed. No special
setup is required but the tests here will only be run if the run_long_tests
value is enabled.
"""

import time


def test_ext_1500(skip_unless_run_long_tests, test_env):
    "E1500 - test static pool grows back to the min after sessions killed"
    test_env.skip_unless_client_version(19)
    pool = test_env.get_pool(min=5, max=5, increment=1, ping_interval=0)
    conns = [pool.acquire() for i in range(5)]
    with test_env.get_admin_connection() as admin_conn:
        with admin_conn.cursor() as admin_cursor:
            for conn in conns:
                sid, serial = test_env.get_sid_serial(conn)
                kill_sql = f"alter system kill session '{sid},{serial}'"
                admin_cursor.execute(kill_sql)
    conns.clear()
    conn = pool.acquire()
    time.sleep(2)
    assert pool.opened == pool.min
