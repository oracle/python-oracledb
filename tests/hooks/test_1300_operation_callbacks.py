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
Module for testing database operation callbacks
"""

import oracledb
import pytest


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


def test_hooks_1300(conn, test_env):
    "1300 - test connection callback properties"
    operation_callback = OperationRecorder()
    round_trip_callback = RoundTripRecorder()
    assert conn.operation_callback is None
    assert conn.round_trip_callback is None
    conn.operation_callback = operation_callback
    conn.round_trip_callback = round_trip_callback
    assert conn.operation_callback is operation_callback
    assert conn.round_trip_callback is round_trip_callback
    conn.operation_callback = None
    conn.round_trip_callback = None
    assert conn.operation_callback is None
    assert conn.round_trip_callback is None
    for name in ("operation_callback", "round_trip_callback"):
        with test_env.assert_raises_full_code("DPY-2070"):
            setattr(conn, name, 1)


def test_hooks_1301(cursor):
    "1301 - test operation callback arguments and successful completion"
    callback = OperationRecorder()
    cursor.connection.operation_callback = callback
    parameters = [1]
    result = cursor.execute("select :1 from dual", parameters)
    assert result is cursor
    assert len(callback.calls) == 1
    name, arguments = callback.calls[0]
    assert name == "execute"
    assert arguments["self"] is cursor
    assert arguments["statement"] == "select :1 from dual"
    assert arguments["parameters"] is parameters
    assert callback.results == [cursor]


def test_hooks_1302(cursor):
    "1302 - test operation failure is passed to completion callback"
    callback = OperationRecorder()
    cursor.connection.operation_callback = callback
    with pytest.raises(oracledb.DatabaseError) as exc_info:
        cursor.execute("select y from dual")
    assert callback.results == [exc_info.value]


def test_hooks_1303(cursor):
    "1303 - test operation callback can skip completion"
    callback = OperationRecorder(completion=None)
    cursor.connection.operation_callback = callback
    cursor.execute("select 1 from dual")
    assert len(callback.calls) == 1
    assert callback.results == []


def test_hooks_1304(cursor, test_env):
    "1304 - test operation callback must return callable or None"
    cursor.connection.operation_callback = OperationRecorder(completion=1)
    with test_env.assert_raises_full_code("DPY-2070"):
        cursor.execute("select 1 from dual")
    cursor.connection.operation_callback = None
    cursor.execute("select 1 from dual")


def test_hooks_1305(test_env):
    "1305 - test pooled connections restore pool callback defaults"
    pool_callback = OperationRecorder()
    pool = test_env.get_pool(
        min=1,
        max=1,
        operation_callback=pool_callback,
    )
    try:
        with pool.acquire() as conn:
            conn.operation_callback = OperationRecorder()
        with pool.acquire() as conn:
            assert conn.operation_callback is pool_callback
    finally:
        pool.close()


def test_hooks_1306(conn, skip_unless_thin_mode):
    "1306 - test successful Thin mode round trip callbacks"
    callback = RoundTripRecorder()
    conn.round_trip_callback = callback
    cursor = conn.cursor()
    cursor.prefetchrows = 0
    cursor.arraysize = 1
    cursor.execute(
        "select to_clob(to_char(level)) from dual connect by level <= 2"
    )
    cursor.fetchall()
    assert callback.names.count("execute") == 2
    assert "fetch" in callback.names
    assert len(callback.names) == len(callback.results)
    assert all(result is None for result in callback.results)


def test_hooks_1307(conn, skip_unless_thin_mode):
    "1307 - test failed Thin mode round trip callbacks"
    callback = RoundTripRecorder()
    conn.round_trip_callback = callback
    with pytest.raises(oracledb.DatabaseError) as exc_info:
        conn.cursor().execute("select y from dual")
    assert "execute" in callback.names
    assert any(result is exc_info.value for result in callback.results)


def test_hooks_1308(cursor):
    "1308 - test cursor callbacks do not contain duplicate nested operations"
    callback = OperationRecorder()
    cursor.connection.operation_callback = callback
    cursor.execute("select 1 from dual")
    cursor.fetchall()
    assert [name for name, _ in callback.calls] == ["execute", "fetchall"]


def test_hooks_1309(conn, skip_unless_thin_mode, test_env):
    "1309 - test round trip callback must return callable or None"
    conn.round_trip_callback = lambda name: 1
    try:
        with test_env.assert_raises_full_code("DPY-2070"):
            conn.cursor().execute("select 1 from dual")
    finally:
        conn.round_trip_callback = None


def test_hooks_1310(cursor):
    "1310 - test callproc is reported as one canonical operation"
    callback = OperationRecorder()
    cursor.connection.operation_callback = callback
    cursor.callproc("dbms_output.enable")
    assert [name for name, _ in callback.calls] == ["callproc"]


def test_hooks_1311(test_env):
    "1311 - test pool management methods do not invoke callbacks"
    callback = OperationRecorder()
    pool = test_env.get_pool(
        min=0,
        max=1,
        operation_callback=callback,
    )
    pool.close()
    assert callback.calls == []


def test_hooks_1312(test_env):
    "1312 - test callback configured with connection parameters"
    callback = OperationRecorder()
    params = test_env.get_connect_params()
    params.set(operation_callback=callback)
    with oracledb.connect(test_env.connect_string, params=params) as conn:
        assert [name for name, _ in callback.calls] == ["connect"]
        assert callback.results == [conn]
        cursor = conn.cursor()
        cursor.execute("select 1 from dual")
        assert [name for name, _ in callback.calls] == ["connect", "execute"]
        assert callback.results == [conn, cursor]


def test_hooks_1313(cursor):
    "1313 - test completion failure after successful operation"

    def complete(result):
        raise RuntimeError("completion failed")

    cursor.connection.operation_callback = lambda name, arguments: complete
    try:
        with pytest.raises(RuntimeError, match="completion failed"):
            cursor.execute("select 1 from dual")
    finally:
        cursor.connection.operation_callback = None


def test_hooks_1314(cursor):
    "1314 - test completion failure after failed operation"

    def complete(result):
        raise RuntimeError("completion failed")

    cursor.connection.operation_callback = lambda name, arguments: complete
    try:
        with pytest.raises(RuntimeError) as exc_info:
            cursor.execute("select y from dual")
        assert isinstance(exc_info.value.__context__, oracledb.DatabaseError)
    finally:
        cursor.connection.operation_callback = None


def test_hooks_1315(cursor):
    "1315 - test before callback failure prevents the operation"

    def callback(name, arguments):
        raise RuntimeError("callback failed")

    cursor.connection.operation_callback = callback
    try:
        with pytest.raises(RuntimeError, match="callback failed"):
            cursor.execute("select y from dual")
    finally:
        cursor.connection.operation_callback = None
