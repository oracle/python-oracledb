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
E1900 - Module for testing pool strinking with asyncio. No special setup is
required but the tests here will only be run if the run_long_tests value is
enabled.
"""

import asyncio

import pytest


@pytest.fixture(autouse=True)
def module_checks(
    anyio_backend, skip_unless_thin_mode, skip_unless_run_long_tests
):
    pass


async def test_ext_1900(test_env):
    "E1900 - test pool timeout with simple acquite after waiting"
    pool = test_env.get_pool_async(min=3, max=10, increment=1, timeout=5)
    conns = [await pool.acquire() for i in range(7)]
    assert pool.opened == 7
    for conn in conns:
        await conn.close()
    await asyncio.sleep(7)
    conn = await pool.acquire()
    assert pool.opened == 3


async def test_ext_1901(test_env):
    "E1901 - test pool timeout with older connection returned first"
    pool = test_env.get_pool_async(min=2, max=5, increment=1, timeout=3)
    conns = [await pool.acquire() for i in range(3)]
    await conns[2].close()
    for i in range(10):
        async with pool.acquire() as conn:
            with conn.cursor() as cursor:
                await cursor.execute("select 1 from dual")
    await asyncio.sleep(4)
    conn = await pool.acquire()
    assert pool.opened == 3


async def test_ext_1902(test_env):
    "E1902 - test pool timeout shrinks to min on pool inactivity"
    pool = test_env.get_pool_async(min=3, max=10, increment=2, timeout=4)
    conns = [await pool.acquire() for i in range(6)]
    assert pool.opened == 6
    for conn in conns:
        await conn.close()
    await asyncio.sleep(6)
    assert pool.opened == 3


async def test_ext_1903(test_env):
    "E1902 - test pool timeout eliminates extra connections on inactivity"
    pool = test_env.get_pool_async(min=4, max=10, increment=4, timeout=3)
    conns = [await pool.acquire() for i in range(5)]
    assert pool.opened == 5
    await asyncio.sleep(2)
    assert pool.opened == 8
    await asyncio.sleep(3)
    assert pool.opened == 5
    del conns


async def test_ext_1904(test_env):
    "E1904 - test pool max_lifetime_session on release"
    pool = test_env.get_pool_async(
        min=4, max=10, increment=4, max_lifetime_session=3
    )
    conns = [await pool.acquire() for i in range(5)]
    assert pool.opened == 5
    await asyncio.sleep(2)
    assert pool.opened == 8
    await asyncio.sleep(2)
    for conn in conns:
        await conn.close()
    await asyncio.sleep(2)
    assert pool.opened == 4


async def test_ext_1905(test_env):
    "E1905 - test pool max_lifetime_session on acquire"
    pool = test_env.get_pool_async(
        min=4, max=10, increment=4, max_lifetime_session=4
    )
    conns = [await pool.acquire() for i in range(5)]
    assert pool.opened == 5
    await asyncio.sleep(2)
    assert pool.opened == 8
    for conn in conns:
        await conn.close()
    await asyncio.sleep(4)
    async with pool.acquire():
        pass
    await asyncio.sleep(2)
    assert pool.opened == 4
