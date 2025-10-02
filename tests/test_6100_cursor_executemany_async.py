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
6100 - Module for testing the cursor executemany() method
"""

import decimal

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


@pytest.fixture
async def empty_tab(async_cursor):
    await async_cursor.execute("truncate table TestTempTable")


async def test_6100(async_conn, async_cursor, empty_tab):
    "6100 - test executing a statement multiple times (named args)"
    rows = [{"value": n} for n in range(250)]
    async_cursor.arraysize = 100
    await async_cursor.executemany(
        "insert into TestTempTable (IntCol) values (:value)",
        rows,
    )
    await async_conn.commit()
    await async_cursor.execute("select count(*) from TestTempTable")
    (count,) = await async_cursor.fetchone()
    assert count == len(rows)


async def test_6101(async_conn, async_cursor, empty_tab):
    "6101 - test executing a statement multiple times (positional args)"
    rows = [[n] for n in range(230)]
    async_cursor.arraysize = 100
    await async_cursor.executemany(
        "insert into TestTempTable (IntCol) values (:1)",
        rows,
    )
    await async_conn.commit()
    await async_cursor.execute("select count(*) from TestTempTable")
    (count,) = await async_cursor.fetchone()
    assert count == len(rows)


async def test_6102(async_conn, async_cursor, empty_tab):
    "6102 - test executing a statement multiple times (with prepare)"
    rows = [[n] for n in range(225)]
    async_cursor.arraysize = 100
    async_cursor.prepare("insert into TestTempTable (IntCol) values (:1)")
    await async_cursor.executemany(None, rows)
    await async_conn.commit()
    await async_cursor.execute("select count(*) from TestTempTable")
    (count,) = await async_cursor.fetchone()
    assert count == len(rows)


async def test_6103(async_conn, async_cursor, empty_tab):
    "6103 - test executing a statement multiple times (with rebind)"
    rows = [[n] for n in range(235)]
    async_cursor.arraysize = 100
    statement = "insert into TestTempTable (IntCol) values (:1)"
    await async_cursor.executemany(statement, rows[:50])
    await async_cursor.executemany(statement, rows[50:])
    await async_conn.commit()
    await async_cursor.execute("select count(*) from TestTempTable")
    (count,) = await async_cursor.fetchone()
    assert count == len(rows)


async def test_6104(async_conn):
    "6104 - test executing multiple times (with input sizes wrong)"
    cursor = async_conn.cursor()
    cursor.setinputsizes(oracledb.NUMBER)
    data = [[decimal.Decimal("25.8")], [decimal.Decimal("30.0")]]
    await cursor.executemany("declare t number; begin t := :1; end;", data)


async def test_6105(async_cursor, empty_tab):
    "6105 - test executing multiple times (with multiple batches)"
    sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
    await async_cursor.executemany(sql, [(1, None), (2, None)])
    await async_cursor.executemany(sql, [(3, None), (4, "Testing")])


async def test_6106(async_cursor, empty_tab):
    "6106 - test executemany() with various numeric types"
    data = [
        (1, 5),
        (2, 7.0),
        (3, 6.5),
        (4, 2**65),
        (5, decimal.Decimal("24.5")),
    ]
    await async_cursor.executemany(
        "insert into TestTempTable (IntCol, NumberCol) values (:1, :2)",
        data,
    )
    await async_cursor.execute(
        "select IntCol, NumberCol from TestTempTable order by IntCol"
    )
    assert await async_cursor.fetchall() == data


async def test_6107(async_cursor, empty_tab):
    "6107 - test executing a statement multiple times (with resize)"
    rows = [
        (1, "First"),
        (2, "Second"),
        (3, "Third"),
        (4, "Fourth"),
        (5, "Fifth"),
        (6, "Sixth"),
        (7, "Seventh and the longest one"),
    ]
    await async_cursor.executemany(
        "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)",
        rows,
    )
    await async_cursor.execute(
        "select IntCol, StringCol1 from TestTempTable order by IntCol"
    )
    assert await async_cursor.fetchall() == rows


async def test_6108(async_cursor, empty_tab, test_env):
    "6108 - test executing a statement multiple times (with exception)"
    rows = [{"value": n} for n in (1, 2, 3, 2, 5)]
    statement = "insert into TestTempTable (IntCol) values (:value)"
    with test_env.assert_raises_full_code("ORA-00001"):
        await async_cursor.executemany(statement, rows)
    assert async_cursor.rowcount == 3


async def test_6109(async_cursor, test_env):
    "6109 - test calling executemany() with invalid parameters"
    sql = """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)"""
    with test_env.assert_raises_full_code("DPY-2004"):
        await async_cursor.executemany(sql, "Not valid parameters")


async def test_6110(async_cursor, empty_tab):
    "6110 - test calling executemany() without any bind parameters"
    num_rows = 5
    await async_cursor.executemany(
        """
        declare
            t_Id          number;
        begin
            select nvl(count(*), 0) + 1 into t_Id
            from TestTempTable;

            insert into TestTempTable (IntCol, StringCol1)
            values (t_Id, 'Test String ' || t_Id);
        end;
        """,
        num_rows,
    )
    assert async_cursor.rowcount == 0
    await async_cursor.execute("select count(*) from TestTempTable")
    (count,) = await async_cursor.fetchone()
    assert count == num_rows


async def test_6111(async_cursor, empty_tab):
    "6111 - test calling executemany() with binds performed earlier"
    num_rows = 9
    var = async_cursor.var(int, arraysize=num_rows)
    async_cursor.setinputsizes(var)
    await async_cursor.executemany(
        """
        declare
            t_Id          number;
        begin
            select nvl(count(*), 0) + 1 into t_Id
            from TestTempTable;

            insert into TestTempTable (IntCol, StringCol1)
            values (t_Id, 'Test String ' || t_Id);

            select sum(IntCol) into :1
            from TestTempTable;
        end;
        """,
        num_rows,
    )
    assert async_cursor.rowcount == 0
    expected_data = [1, 3, 6, 10, 15, 21, 28, 36, 45]
    assert var.values == expected_data


async def test_6112(async_cursor):
    "6112 - test executing plsql statements multiple times (with binds)"
    var = async_cursor.var(int, arraysize=5)
    async_cursor.setinputsizes(var)
    data = [[25], [30], [None], [35], [None]]
    exepected_data = [25, 30, None, 35, None]
    await async_cursor.executemany(
        "declare t number; begin t := :1; end;", data
    )
    assert var.values == exepected_data


async def test_6113(async_cursor, test_env):
    "6113 - test executemany with incorrect parameters"
    with test_env.assert_raises_full_code("DPY-2004"):
        await async_cursor.executemany("select :1 from dual", [1])


async def test_6114(async_cursor, test_env):
    "6114 - test executemany with mixed binds (pos first)"
    rows = [["test"], {"value": 1}]
    with test_env.assert_raises_full_code("DPY-2006"):
        await async_cursor.executemany("select :1 from dual", rows)


async def test_6115(async_cursor, test_env):
    "6115 - test executemany with mixed binds (name first)"
    rows = [{"value": 1}, ["test"]]
    with test_env.assert_raises_full_code("DPY-2006"):
        await async_cursor.executemany("select :value from dual", rows)


async def test_6116(async_cursor, empty_tab):
    "6116 - test executemany() with a pl/sql statement with dml returning"
    num_rows = 5
    out_var = async_cursor.var(oracledb.NUMBER, arraysize=5)
    async_cursor.setinputsizes(out_var)
    await async_cursor.executemany(
        """
        declare
            t_Id          number;
        begin
            select nvl(count(*), 0) + 1 into t_Id
            from TestTempTable;

            insert into TestTempTable (IntCol, StringCol1)
            values (t_Id, 'Test String ' || t_Id)
            returning IntCol into :out_bind;
        end;
        """,
        num_rows,
    )
    assert out_var.values == [1, 2, 3, 4, 5]


async def test_6117(async_cursor, empty_tab):
    "6117 - test executemany() with pl/sql in binds and out binds"
    values = [5, 8, 17, 24, 6]
    data = [(i, f"Test {i}") for i in values]
    out_bind = async_cursor.var(oracledb.NUMBER, arraysize=5)
    async_cursor.setinputsizes(None, None, out_bind)
    await async_cursor.executemany(
        """
        begin
            insert into TestTempTable (IntCol, StringCol1)
            values (:int_val, :str_val)
            returning IntCol into :out_bind;
        end;
        """,
        data,
    )
    assert out_bind.values == values


async def test_6118(async_cursor, empty_tab):
    "6118 - test executemany() with pl/sql outbinds"
    out_bind = async_cursor.var(oracledb.NUMBER, arraysize=5)
    async_cursor.setinputsizes(out_bind)
    await async_cursor.executemany("begin :out_var := 5; end;", 5)
    assert out_bind.values == [5, 5, 5, 5, 5]


async def test_6119(async_cursor):
    "6119 - test re-executemany() with pl/sql in binds and out binds"
    values = [5, 8, 17, 24, 6]
    data = [(i, f"Test {i}") for i in values]
    for i in range(2):
        await async_cursor.execute("truncate table TestTempTable")
        out_bind = async_cursor.var(oracledb.NUMBER, arraysize=5)
        async_cursor.setinputsizes(None, None, out_bind)
        await async_cursor.executemany(
            """
            begin
                insert into TestTempTable (IntCol, StringCol1)
                values (:int_val, :str_val)
                returning IntCol into :out_bind;
            end;
            """,
            data,
        )
        assert out_bind.values == values


async def test_6120(async_cursor):
    "6120 - test PL/SQL statement with single row bind"
    value = 4020
    var = async_cursor.var(int)
    await async_cursor.executemany("begin :1 := :2; end;", [[var, value]])
    assert var.values == [value]


async def test_6121(async_conn, async_cursor, empty_tab):
    "6121 - test deferral of type assignment"
    data = [(1, None), (2, 25)]
    await async_cursor.executemany(
        """
        insert into TestTempTable
        (IntCol, NumberCol)
        values (:1, :2)
        """,
        data,
    )
    await async_conn.commit()
    await async_cursor.execute(
        """
        select IntCol, NumberCol
        from TestTempTable
        order by IntCol
        """
    )
    assert await async_cursor.fetchall() == data


async def test_6122(async_cursor):
    "6122 - test PL/SQL with a lerge number of binds"
    parts = []
    bind_names = []
    all_bind_values = []
    out_binds = []
    for i in range(5):
        all_bind_values.append([])
    for i in range(350):
        n = len(parts) + 1
        bind_names.extend([f"v_out_{n}_0", f"a_{n}", f"b_{n}", f"c_{n}"])
        parts.append(f":v_out{n} := :a_{n} + :b_{n} + :c_{n};")
        out_binds.append(async_cursor.var(int, arraysize=len(all_bind_values)))
        for j, bind_values in enumerate(all_bind_values):
            bind_values.extend(
                [out_binds[-1], n * 1 + j, n * 2 + j, n * 3 + j]
            )
    lf = "\n"
    sql = f"begin{lf}{lf.join(parts)}{lf}end;"
    await async_cursor.executemany(sql, all_bind_values)
    init_val = 6
    for var in out_binds:
        expected_values = [
            init_val,
            init_val + 3,
            init_val + 6,
            init_val + 9,
            init_val + 12,
        ]
        assert var.values == expected_values
        init_val += 6


async def test_6123(async_conn, test_env):
    "6123 - test executing no statement"
    cursor = async_conn.cursor()
    with test_env.assert_raises_full_code("DPY-2001"):
        await cursor.executemany(None, [1, 2])


async def test_6124(async_cursor):
    "6124 - test executemany with empty parameter set"
    sql = "insert into TestTempTable values (:1)"
    await async_cursor.executemany(sql, [])


async def test_6125(async_cursor, test_env):
    "6125 - test executemany with an empty statement"
    with test_env.assert_raises_full_code("DPY-2066"):
        await async_cursor.executemany("", 5)
    with test_env.assert_raises_full_code("DPY-2066"):
        await async_cursor.executemany("  ", 5)


async def test_6126(cursor):
    "6126 - test executemany with batch size 0"
    rows = [[1], [2]]
    with pytest.raises(TypeError):
        await cursor.executemany(
            "insert into TestTempTable (IntCol) values (:1)",
            rows,
            batch_size=0,
        )


@pytest.mark.parametrize("batch_size", [1, 5, 99, 199, 200])
async def test_6127(
    batch_size, async_conn, async_cursor, empty_tab, round_trip_checker_async
):
    "6127 - test executemany with various batch sizes"
    rows = [(i + 1, f"String for row {i + 1}") for i in range(200)]
    await async_cursor.executemany(
        "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)",
        rows,
        batch_size=batch_size,
    )
    num_round_trips = len(rows) // batch_size
    if len(rows) % batch_size:
        num_round_trips += 1
    assert await round_trip_checker_async.get_value_async() == num_round_trips
    await async_conn.commit()
    await async_cursor.execute(
        "select IntCol, StringCol1 from TestTempTable order by IntCol"
    )
    assert await async_cursor.fetchall() == rows
