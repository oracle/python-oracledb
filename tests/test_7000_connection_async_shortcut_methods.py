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
7000 - Module for testing async connections shortcut methods
"""

import decimal

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


async def test_7000(async_conn):
    "7000 - test execute() and fetchall()"
    await async_conn.execute("truncate table TestTempTable")
    await async_conn.execute(
        "insert into TestTempTable (IntCol) values (:1)", [77]
    )
    await async_conn.execute(
        "insert into TestTempTable (IntCol) values (:val)", dict(val=15)
    )
    await async_conn.commit()

    res = await async_conn.fetchall(
        "select IntCol from TestTempTable order by IntCol"
    )
    assert res == [(15,), (77,)]


async def test_7001(async_conn):
    "7001 - test executemany()"
    await async_conn.execute("truncate table TestTempTable")
    await async_conn.executemany(
        "insert into TestTempTable (IntCol) values (:1)", [(2,), (3,)]
    )
    await async_conn.executemany(
        "insert into TestTempTable (IntCol) values (:data)",
        [{"data": 4}, {"data": 5}],
    )
    await async_conn.commit()
    res = await async_conn.fetchall(
        "select IntCol from TestTempTable order by IntCol"
    )
    assert res == [(2,), (3,), (4,), (5,)]


async def test_7002(async_conn, round_trip_checker_async):
    "7002 - test fetchall() with arraysize"
    await async_conn.execute("truncate table TestTempTable")
    data = [(1,), (2,), (3,), (4,)]
    await async_conn.executemany(
        "insert into TestTempTable (IntCol) values (:value)",
        [{"value": i} for i, in data],
    )
    await async_conn.commit()

    await round_trip_checker_async.get_value_async()
    res = await async_conn.fetchall(
        "select IntCol from TestTempTable order by IntCol", arraysize=1
    )
    assert res == data
    assert await round_trip_checker_async.get_value_async() == 5

    res = await async_conn.fetchall(
        "select IntCol from TestTempTable order by IntCol",
        arraysize=len(data),
    )
    assert res == data
    assert await round_trip_checker_async.get_value_async() == 2


async def test_7003(async_conn):
    "7003 - test fetchall() with rowfactory"
    await async_conn.execute("truncate table TestTempTable")
    await async_conn.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'test_7003')
        """
    )
    await async_conn.commit()

    column_names = ["INTCOL", "STRINGCOL1"]

    def rowfactory(*row):
        return dict(zip(column_names, row))

    res = await async_conn.fetchall(
        "select IntCol, StringCol1 from TestTempTable",
        rowfactory=rowfactory,
    )
    expected_value = [{"INTCOL": 1, "STRINGCOL1": "test_7003"}]
    assert res == expected_value


async def test_7004(async_conn):
    "7004 - test fetchone()"
    await async_conn.execute("truncate table TestTempTable")
    await async_conn.executemany(
        "insert into TestTempTable (IntCol) values (:1)", [(9,), (10,)]
    )
    await async_conn.commit()

    res = await async_conn.fetchone(
        "select IntCol from TestTempTable order by IntCol"
    )
    assert res == (9,)

    res = await async_conn.fetchone("select :1 from dual", [23])
    assert res == (23,)

    res = await async_conn.fetchone("select :val from dual", {"val": 5})
    assert res == (5,)


async def test_7005(async_conn):
    "7005 - test fetchone() with rowfactory"
    await async_conn.execute("truncate table TestTempTable")
    await async_conn.executemany(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:int, :str)
        """,
        [{"int": 3, "str": "Mac"}, {"int": 4, "str": "Doc"}],
    )
    await async_conn.commit()

    column_names = ["INT", "STRING"]

    def rowfactory(*row):
        return dict(zip(column_names, row))

    res = await async_conn.fetchone(
        "select IntCol, StringCol1 from TestTempTable order by IntCol",
        rowfactory=rowfactory,
    )
    assert res == {"INT": 3, "STRING": "Mac"}


async def test_7006(async_conn):
    "7006 - test fetchmany()"
    data = [(i,) for i in range(10)]
    await async_conn.execute("truncate table TestTempTable")
    await async_conn.executemany(
        "insert into TestTempTable (IntCol) values (:1)", data
    )
    await async_conn.commit()
    res = await async_conn.fetchmany(
        "select IntCol from TestTempTable order by IntCol"
    )
    assert res == data

    res = await async_conn.fetchmany("select :1 from dual", [1099])
    assert res == [(1099,)]

    res = await async_conn.fetchmany("select :val from dual", {"val": 366})
    assert res == [(366,)]


async def test_7007(async_conn):
    "7007 - test fetchmany() with num_rows"
    data = [(i,) for i in range(10)]
    await async_conn.execute("truncate table TestTempTable")
    await async_conn.executemany(
        "insert into TestTempTable (IntCol) values (:1)", data
    )
    num_rows = 7
    res = await async_conn.fetchmany(
        "select IntCol from TestTempTable order by IntCol",
        num_rows=num_rows,
    )
    assert res == data[:num_rows]


async def test_7008(test_env):
    "7008 - test fetchmany() with rowfactory and num_rows"
    conn = await test_env.get_connection_async()
    await conn.execute("truncate table TestTempTable")
    await conn.executemany(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:int, :str)
        """,
        [{"int": 29, "str": "Feb"}, {"int": 4, "str": "Monday"}],
    )
    await conn.commit()

    column_names = ["INT", "STRING"]

    def rowfactory(*row):
        return dict(zip(column_names, row))

    res = await conn.fetchmany(
        "select IntCol, StringCol1 from TestTempTable order by IntCol",
        rowfactory=rowfactory,
    )
    expected_value = [
        {"INT": 4, "STRING": "Monday"},
        {"INT": 29, "STRING": "Feb"},
    ]
    assert res == expected_value

    res = await conn.fetchmany(
        "select IntCol, StringCol1 from TestTempTable order by IntCol",
        rowfactory=rowfactory,
        num_rows=1,
    )
    assert res == [{"INT": 4, "STRING": "Monday"}]


async def test_7009(async_conn):
    "7009 - test callfunc()"
    # parameters
    res = await async_conn.callfunc("func_Test", oracledb.NUMBER, ("Yes", 7))
    assert res == 10

    # keyword parameters
    kwargs = {"a_String": "Keyword", "a_ExtraAmount": 12}
    res = await async_conn.callfunc(
        "func_Test", oracledb.NUMBER, keyword_parameters=kwargs
    )
    assert res == 19

    # paramters and keyword parameters
    kwargs = {"a_ExtraAmount": 25}
    res = await async_conn.callfunc(
        "func_Test", oracledb.NUMBER, ["Mixed"], kwargs
    )
    assert res == 30


async def test_7010(async_conn, async_cursor):
    "7010 - test callproc() with parameters"
    var = async_cursor.var(oracledb.NUMBER)
    results = await async_conn.callproc("proc_Test", ("hi", 5, var))
    assert results == ["hi", 10, 2.0]


async def test_7011(async_conn, async_cursor):
    "7011 - test callproc() with keyword_parameters"
    in_out_value = async_cursor.var(oracledb.NUMBER)
    in_out_value.setvalue(0, 7)
    out_value = async_cursor.var(oracledb.NUMBER)
    kwargs = dict(
        a_InValue="Peace", a_InOutValue=in_out_value, a_OutValue=out_value
    )
    results = await async_conn.callproc("proc_Test", [], kwargs)
    assert results == []
    assert in_out_value.getvalue() == 35
    assert out_value.getvalue() == 5


async def test_7012(async_conn, async_cursor):
    "7012 - test callproc() with parameters and keyword_parameters"
    in_out_value = async_cursor.var(oracledb.NUMBER)
    in_out_value.setvalue(0, 8)
    out_value = async_cursor.var(oracledb.NUMBER)
    kwargs = dict(a_InOutValue=in_out_value, a_OutValue=out_value)
    results = await async_conn.callproc("proc_Test", ["Input_7712"], kwargs)
    assert results == ["Input_7712"]
    assert in_out_value.getvalue() == 80
    assert out_value.getvalue() == 10


async def test_7013(async_conn):
    "7013 - test fetchmany() num_rows with 0 and negative values"
    data = [(i,) for i in range(10)]
    await async_conn.execute("truncate table TestTempTable")
    await async_conn.executemany(
        "insert into TestTempTable (IntCol) values (:1)", data
    )
    await async_conn.commit()
    for num_rows in (0, -1, -10):
        res = await async_conn.fetchmany(
            "select IntCol from TestTempTable",
            num_rows=num_rows,
        )
        assert res == []


async def test_7014(async_conn):
    "7014 - test shortcut methods with transaction_in_progress"
    await async_conn.execute("truncate table TestTempTable")
    assert not async_conn.transaction_in_progress
    await async_conn.execute(
        "insert into TestTempTable (IntCol) values (5)",
    )
    assert async_conn.transaction_in_progress
    await async_conn.commit()
    assert not async_conn.transaction_in_progress


async def test_7015(async_conn):
    "7015 - test fetchone() with fetch_lobs=False"
    value = "test_7015"
    (result,) = await async_conn.fetchone(
        "select to_clob(:1) from dual", [value], fetch_lobs=False
    )
    assert result == value


async def test_7016(async_conn):
    "7016 - test fetchmany() with fetch_lobs=False"
    value = "test_7016"
    rows = await async_conn.fetchmany(
        "select to_clob(:1) from dual", [value], fetch_lobs=False
    )
    assert rows == [(value,)]


async def test_7017(async_conn):
    "7017 - test fetchall() with fetch_lobs=False"
    value = "test_7017"
    rows = await async_conn.fetchall(
        "select to_clob(:1) from dual", [value], fetch_lobs=False
    )
    assert rows == [(value,)]


async def test_7018(async_conn):
    "7018 - test fetchone() with fetch_decimals=True"
    value = 7018
    (result,) = await async_conn.fetchone(
        "select :1 from dual", [value], fetch_decimals=True
    )
    assert isinstance(result, decimal.Decimal)


async def test_7019(async_conn):
    "7019 - test fetchmany() with fetch_decimals=True"
    value = 7019
    rows = await async_conn.fetchmany(
        "select :1 from dual", [value], fetch_decimals=True
    )
    assert isinstance(rows[0][0], decimal.Decimal)


async def test_7020(async_conn):
    "7020 - test fetchall() with fetch_decimals=True"
    value = 7020
    rows = await async_conn.fetchall(
        "select :1 from dual", [value], fetch_decimals=True
    )
    assert isinstance(rows[0][0], decimal.Decimal)
