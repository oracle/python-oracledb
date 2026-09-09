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
Module for testing database operation callbacks with asyncio
"""

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


class OperationRecorder:

    def __init__(self, completion=True):
        self.calls = []
        self.completion = completion
        self.results = []

    def __call__(self, name, arguments):
        self.calls.append((name, arguments))
        if self.completion is True:
            return self.results.append
        return self.completion


class RoundTripRecorder:

    def __init__(self):
        self.names = []
        self.results = []

    def __call__(self, name):
        self.names.append(name)
        return self.results.append


async def test_hooks_1400(async_conn, test_env):
    "1400 - test asynchronous connection callback properties"
    operation_callback = OperationRecorder()
    round_trip_callback = RoundTripRecorder()
    assert async_conn.operation_callback is None
    assert async_conn.round_trip_callback is None
    async_conn.operation_callback = operation_callback
    async_conn.round_trip_callback = round_trip_callback
    assert async_conn.operation_callback is operation_callback
    assert async_conn.round_trip_callback is round_trip_callback
    async_conn.operation_callback = None
    async_conn.round_trip_callback = None
    assert async_conn.operation_callback is None
    assert async_conn.round_trip_callback is None
    for name in ("operation_callback", "round_trip_callback"):
        with test_env.assert_raises_full_code("DPY-2070"):
            setattr(async_conn, name, 1)


async def test_hooks_1401(async_cursor):
    "1401 - test asynchronous callback arguments and successful completion"
    callback = OperationRecorder()
    async_cursor.connection.operation_callback = callback
    parameters = [1]
    result = await async_cursor.execute("select :1 from dual", parameters)
    assert result is async_cursor
    assert len(callback.calls) == 1
    name, arguments = callback.calls[0]
    assert name == "execute"
    assert arguments["self"] is async_cursor
    assert arguments["statement"] == "select :1 from dual"
    assert arguments["parameters"] is parameters
    assert callback.results == [async_cursor]


async def test_hooks_1402(async_cursor):
    "1402 - test asynchronous operation failure callback"
    callback = OperationRecorder()
    async_cursor.connection.operation_callback = callback
    with pytest.raises(oracledb.DatabaseError) as exc_info:
        await async_cursor.execute("select y from dual")
    assert callback.results == [exc_info.value]


async def test_hooks_1403(async_cursor):
    "1403 - test asynchronous callback can skip completion"
    callback = OperationRecorder(completion=None)
    async_cursor.connection.operation_callback = callback
    await async_cursor.execute("select 1 from dual")
    assert len(callback.calls) == 1
    assert callback.results == []


async def test_hooks_1404(async_cursor, test_env):
    "1404 - test asynchronous callback must return callable or None"
    async_cursor.connection.operation_callback = OperationRecorder(
        completion=1
    )
    with test_env.assert_raises_full_code("DPY-2070"):
        await async_cursor.execute("select 1 from dual")
    async_cursor.connection.operation_callback = None
    await async_cursor.execute("select 1 from dual")


async def test_hooks_1405(test_env):
    "1405 - test asynchronous pools restore callback defaults"
    pool_callback = OperationRecorder()
    pool = test_env.get_pool_async(
        min=1,
        max=1,
        operation_callback=pool_callback,
    )
    try:
        async with pool.acquire() as conn:
            conn.operation_callback = OperationRecorder()
        async with pool.acquire() as conn:
            assert conn.operation_callback is pool_callback
    finally:
        await pool.close()


async def test_hooks_1406(async_conn):
    "1406 - test successful asynchronous round trip callbacks"
    callback = RoundTripRecorder()
    async_conn.round_trip_callback = callback
    cursor = async_conn.cursor()
    cursor.prefetchrows = 0
    cursor.arraysize = 1
    await cursor.execute(
        "select to_clob(to_char(level)) from dual connect by level <= 2"
    )
    await cursor.fetchall()
    assert callback.names.count("execute") == 2
    assert "fetch" in callback.names
    assert len(callback.names) == len(callback.results)
    assert all(result is None for result in callback.results)


async def test_hooks_1407(async_conn):
    "1407 - test failed asynchronous round trip callbacks"
    callback = RoundTripRecorder()
    async_conn.round_trip_callback = callback
    with pytest.raises(oracledb.DatabaseError) as exc_info:
        await async_conn.cursor().execute("select y from dual")
    assert "execute" in callback.names
    assert any(result is exc_info.value for result in callback.results)


async def test_hooks_1408(async_cursor):
    "1408 - test asynchronous callbacks have no duplicate operations"
    callback = OperationRecorder()
    async_cursor.connection.operation_callback = callback
    await async_cursor.execute("select 1 from dual")
    await async_cursor.fetchall()
    assert [name for name, _ in callback.calls] == ["execute", "fetchall"]


async def test_hooks_1409(async_conn, test_env):
    "1409 - test asynchronous round trip completion must be callable"
    async_conn.round_trip_callback = lambda name: 1
    try:
        with test_env.assert_raises_full_code("DPY-2070"):
            await async_conn.cursor().execute("select 1 from dual")
    finally:
        async_conn.round_trip_callback = None


async def test_hooks_1410(async_cursor):
    "1410 - test asynchronous callproc is one canonical operation"
    callback = OperationRecorder()
    async_cursor.connection.operation_callback = callback
    await async_cursor.callproc("dbms_output.enable")
    assert [name for name, _ in callback.calls] == ["callproc"]


async def test_hooks_1411(test_env):
    "1411 - test asynchronous pool methods do not invoke callbacks"
    callback = OperationRecorder()
    pool = test_env.get_pool_async(
        min=0,
        max=1,
        operation_callback=callback,
    )
    await pool.close()
    assert callback.calls == []


async def test_hooks_1412(test_env):
    "1412 - test callback configured with async connection parameters"
    callback = OperationRecorder()
    params = test_env.get_connect_params()
    params.set(operation_callback=callback)
    async with oracledb.connect_async(
        test_env.connect_string,
        params=params,
    ) as conn:
        assert [name for name, _ in callback.calls] == ["connect"]
        assert callback.results == [conn]
        cursor = conn.cursor()
        await cursor.execute("select 1 from dual")
        assert [name for name, _ in callback.calls] == ["connect", "execute"]
        assert callback.results == [conn, cursor]


async def test_hooks_1413(async_cursor):
    "1413 - test asynchronous completion failure after success"

    def complete(result):
        raise RuntimeError("completion failed")

    async_cursor.connection.operation_callback = lambda name, args: complete
    try:
        with pytest.raises(RuntimeError, match="completion failed"):
            await async_cursor.execute("select 1 from dual")
    finally:
        async_cursor.connection.operation_callback = None


async def test_hooks_1414(async_cursor):
    "1414 - test asynchronous completion failure after operation failure"

    def complete(result):
        raise RuntimeError("completion failed")

    async_cursor.connection.operation_callback = lambda name, args: complete
    try:
        with pytest.raises(RuntimeError) as exc_info:
            await async_cursor.execute("select y from dual")
        assert isinstance(exc_info.value.__context__, oracledb.DatabaseError)
    finally:
        async_cursor.connection.operation_callback = None


async def test_hooks_1415(async_cursor):
    "1415 - test asynchronous before callback failure"

    def callback(name, arguments):
        raise RuntimeError("callback failed")

    async_cursor.connection.operation_callback = callback
    try:
        with pytest.raises(RuntimeError, match="callback failed"):
            await async_cursor.execute("select y from dual")
    finally:
        async_cursor.connection.operation_callback = None


async def test_hooks_1416(async_conn):
    "1416 - test connection helpers use canonical cursor callbacks"
    callback = OperationRecorder()
    async_conn.operation_callback = callback
    await async_conn.execute("select 1 from dual")
    assert [name for name, _ in callback.calls] == ["execute"]


async def test_hooks_1417(async_conn):
    "1417 - test a pipeline is reported as one operation"
    callback = OperationRecorder()
    async_conn.operation_callback = callback
    pipeline = oracledb.create_pipeline()
    pipeline.add_fetchall("select 1 from dual")
    await async_conn.run_pipeline(pipeline)
    assert [name for name, _ in callback.calls] == ["run_pipeline"]
