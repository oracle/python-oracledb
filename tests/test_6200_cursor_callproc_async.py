# -----------------------------------------------------------------------------
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
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
6200 - Module for testing the methods for calling stored procedures and
functions (callproc() and callfunc()) with asyncio
"""

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


async def test_6200(async_cursor):
    "6200 - test executing a stored procedure"
    var = async_cursor.var(oracledb.NUMBER)
    results = await async_cursor.callproc("proc_Test", ("hi", 5, var))
    assert results == ["hi", 10, 2.0]


async def test_6201(async_cursor):
    "6201 - test executing a stored procedure with all args keyword args"
    inout_value = async_cursor.var(oracledb.NUMBER)
    inout_value.setvalue(0, 5)
    out_value = async_cursor.var(oracledb.NUMBER)
    kwargs = dict(
        a_InOutValue=inout_value, a_InValue="hi", a_OutValue=out_value
    )
    results = await async_cursor.callproc("proc_Test", [], kwargs)
    assert results == []
    assert inout_value.getvalue() == 10
    assert out_value.getvalue() == 2.0


async def test_6202(async_cursor):
    "6202 - test executing a stored procedure with last arg as keyword arg"
    out_value = async_cursor.var(oracledb.NUMBER)
    kwargs = dict(a_OutValue=out_value)
    results = await async_cursor.callproc("proc_Test", ("hi", 5), kwargs)
    assert results == ["hi", 10]
    assert out_value.getvalue() == 2.0


async def test_6203(async_cursor, test_env):
    "6203 - test executing a stored procedure, repeated keyword arg"
    kwargs = dict(a_InValue="hi", a_OutValue=async_cursor.var(oracledb.NUMBER))
    with test_env.assert_raises_full_code("ORA-06550"):
        await async_cursor.callproc("proc_Test", ("hi", 5), kwargs)


async def test_6204(async_cursor):
    "6204 - test executing a stored procedure without any arguments"
    results = await async_cursor.callproc("proc_TestNoArgs")
    assert results == []


async def test_6205(async_cursor):
    "6205 - test executing a stored function"
    results = await async_cursor.callfunc(
        "func_Test", oracledb.NUMBER, ("hi", 5)
    )
    assert results == 7


async def test_6206(async_cursor):
    "6206 - test executing a stored function without any arguments"
    results = await async_cursor.callfunc("func_TestNoArgs", oracledb.NUMBER)
    assert results == 712


async def test_6207(async_cursor, test_env):
    "6207 - test executing a stored function with wrong parameters"
    func_name = "func_Test"
    with test_env.assert_raises_full_code("DPY-2007"):
        await async_cursor.callfunc(oracledb.NUMBER, func_name, ("hi", 5))
    with test_env.assert_raises_full_code("ORA-06550"):
        await async_cursor.callfunc(func_name, oracledb.NUMBER, ("hi", 5, 7))
    with test_env.assert_raises_full_code("DPY-2012"):
        await async_cursor.callfunc(func_name, oracledb.NUMBER, "hi", 7)
    with test_env.assert_raises_full_code("ORA-06502"):
        await async_cursor.callfunc(func_name, oracledb.NUMBER, [5, "hi"])
    with test_env.assert_raises_full_code("ORA-06550"):
        await async_cursor.callfunc(func_name, oracledb.NUMBER)
    with test_env.assert_raises_full_code("DPY-2012"):
        await async_cursor.callfunc(func_name, oracledb.NUMBER, 5)


async def test_6208(async_cursor, test_env):
    "6208 - test error for keyword args with invalid type"
    kwargs = [5]
    with test_env.assert_raises_full_code("DPY-2013"):
        await async_cursor.callproc("proc_Test", [], kwargs)
    with test_env.assert_raises_full_code("DPY-2013"):
        await async_cursor.callfunc("func_Test", oracledb.NUMBER, [], kwargs)


async def test_6209(async_cursor):
    "6209 - test calling a procedure with a string > 32767 characters"
    data = "6209" * 16000
    size_var = async_cursor.var(int)
    await async_cursor.callproc("pkg_TestLobs.GetSize", [data, size_var])
    assert size_var.getvalue() == len(data)


async def test_6210(async_cursor):
    "6210 - test calling a procedure with raw data > 32767 bytes"
    data = b"6210" * 16250
    size_var = async_cursor.var(int)
    await async_cursor.callproc("pkg_TestLobs.GetSize", [data, size_var])
    assert size_var.getvalue() == len(data)
