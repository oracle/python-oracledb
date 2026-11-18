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
E3800 - Test async pipelining after a network disconnect.

These tests require a Thin asyncio connection to Oracle Database 23 or later
with pipelining support.
"""

import asyncio

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(
    anyio_backend, skip_unless_thin_mode, skip_unless_run_long_tests
):
    pass


async def test_ext_3800(async_tunnel, test_env):
    "E3800 - pipeline reports a connection closed during its request"
    params = test_env.get_connect_params()
    params.parse_connect_string(test_env.connect_string)
    params.set(host=async_tunnel.host, port=async_tunnel.port)
    async with oracledb.connect_async(params=params) as conn:
        pipeline = oracledb.create_pipeline()
        pipeline.add_execute("begin dbms_session.sleep(10); end;")
        for _ in range(5):
            pipeline.add_fetchone("select 1 from dual")
        task = asyncio.create_task(conn.run_pipeline(pipeline))
        await asyncio.sleep(1)
        await async_tunnel.cut()
        with test_env.assert_raises_full_code("DPY-4011"):
            await asyncio.wait_for(task, timeout=5)
