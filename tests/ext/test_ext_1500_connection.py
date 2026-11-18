# -----------------------------------------------------------------------------
# Copyright (c) 2026, Oracle and/or its affiliates.
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
E1500 - Tests connection behavior after a network disconnect.

Requires a Thin connection. The tunnel fixture requires run_long_tests
to be enabled in the extended test configuration.
"""

import oracledb


def test_ext_1500(tunnel, test_env, skip_unless_thin_mode):
    "E1500 - setting call_timeout after connection loss raises DPY-1001"
    params = test_env.get_connect_params()
    params.parse_connect_string(test_env.connect_string)
    params.set(host=tunnel.host, port=tunnel.port)

    with oracledb.connect(params=params) as conn:
        conn.call_timeout = 5000
        assert conn.call_timeout == 5000
        conn.ping()

        tunnel.cut()
        with test_env.assert_raises_full_code("DPY-4011"):
            conn.cursor().execute("select 1 from dual")
        assert not conn.is_healthy()
        assert conn.call_timeout == 5000
        with test_env.assert_raises_full_code("DPY-1001"):
            conn.call_timeout = 0
