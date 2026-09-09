# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2026, Oracle and/or its affiliates.
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
Module for testing the cursor executemany() method
"""

import decimal

import oracledb
import pytest


@pytest.fixture
def empty_tab(cursor):
    cursor.execute("truncate table TestTempTable")


def test_cursor_1200(conn, cursor, empty_tab):
    "1200 - test executing a statement multiple times (named args)"
    rows = [{"value": n} for n in range(250)]
    cursor.arraysize = 100
    cursor.executemany(
        "insert into TestTempTable (IntCol) values (:value)",
        rows,
    )
    conn.commit()
    cursor.execute("select count(*) from TestTempTable")
    (count,) = cursor.fetchone()
    assert count == len(rows)


def test_cursor_1201(conn, cursor, empty_tab):
    "1201 - test executing a statement multiple times (positional args)"
    rows = [[n] for n in range(230)]
    cursor.arraysize = 100
    cursor.executemany(
        "insert into TestTempTable (IntCol) values (:1)",
        rows,
    )
    conn.commit()
    cursor.execute("select count(*) from TestTempTable")
    (count,) = cursor.fetchone()
    assert count == len(rows)


def test_cursor_1202(conn, cursor, empty_tab):
    "1202 - test executing a statement multiple times (with prepare)"
    rows = [[n] for n in range(225)]
    cursor.arraysize = 100
    cursor.prepare("insert into TestTempTable (IntCol) values (:1)")
    cursor.executemany(None, rows)
    conn.commit()
    cursor.execute("select count(*) from TestTempTable")
    (count,) = cursor.fetchone()
    assert count == len(rows)


def test_cursor_1203(conn, cursor, empty_tab):
    "1203 - test executing a statement multiple times (with rebind)"
    rows = [[n] for n in range(235)]
    cursor.arraysize = 100
    statement = "insert into TestTempTable (IntCol) values (:1)"
    cursor.executemany(statement, rows[:50])
    cursor.executemany(statement, rows[50:])
    conn.commit()
    cursor.execute("select count(*) from TestTempTable")
    (count,) = cursor.fetchone()
    assert count == len(rows)


def test_cursor_1204(conn):
    "1204 - test executing multiple times (with input sizes wrong)"
    cursor = conn.cursor()
    cursor.setinputsizes(oracledb.NUMBER)
    data = [[decimal.Decimal("25.8")], [decimal.Decimal("30.0")]]
    cursor.executemany("declare t number; begin t := :1; end;", data)


def test_cursor_1205(cursor, empty_tab):
    "1205 - test executing multiple times (with multiple batches)"
    sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
    cursor.executemany(sql, [(1, None), (2, None)])
    cursor.executemany(sql, [(3, None), (4, "Testing")])


def test_cursor_1206(cursor, empty_tab):
    "1206 - test executemany() with various numeric types"
    data = [
        (1, 5),
        (2, 7.0),
        (3, 6.5),
        (4, 2**65),
        (5, decimal.Decimal("24.5")),
    ]
    cursor.executemany(
        "insert into TestTempTable (IntCol, NumberCol) values (:1, :2)",
        data,
    )
    cursor.execute(
        "select IntCol, NumberCol from TestTempTable order by IntCol"
    )
    assert cursor.fetchall() == data


def test_cursor_1207(cursor, empty_tab):
    "1207 - test executing a statement multiple times (with resize)"
    rows = [
        (1, "First"),
        (2, "Second"),
        (3, "Third"),
        (4, "Fourth"),
        (5, "Fifth"),
        (6, "Sixth"),
        (7, "Seventh and the longest one"),
    ]
    cursor.executemany(
        "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)",
        rows,
    )
    cursor.execute(
        "select IntCol, StringCol1 from TestTempTable order by IntCol"
    )
    assert cursor.fetchall() == rows


def test_cursor_1208(cursor, empty_tab, test_env):
    "1208 - test executing a statement multiple times (with exception)"
    rows = [{"value": n} for n in (1, 2, 3, 2, 5)]
    statement = "insert into TestTempTable (IntCol) values (:value)"
    with test_env.assert_raises_full_code("ORA-00001"):
        cursor.executemany(statement, rows)
    assert cursor.rowcount == 3


def test_cursor_1209(cursor, test_env):
    "1209 - test calling executemany() with invalid parameters"
    sql = """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)"""
    with test_env.assert_raises_full_code("DPY-2004"):
        cursor.executemany(sql, "These are not valid parameters")


def test_cursor_1210(cursor, empty_tab):
    "1210 - test calling executemany() without any bind parameters"
    num_rows = 5
    cursor.executemany(
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
    assert cursor.rowcount == 0
    cursor.execute("select count(*) from TestTempTable")
    (count,) = cursor.fetchone()
    assert count == num_rows


def test_cursor_1211(cursor, empty_tab):
    "1211 - test calling executemany() with binds performed earlier"
    num_rows = 9
    var = cursor.var(int, arraysize=num_rows)
    cursor.setinputsizes(var)
    cursor.executemany(
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
    assert cursor.rowcount == 0
    expected_data = [1, 3, 6, 10, 15, 21, 28, 36, 45]
    assert var.values == expected_data


def test_cursor_1212(cursor):
    "1212 - test executing plsql statements multiple times (with binds)"
    var = cursor.var(int, arraysize=5)
    cursor.setinputsizes(var)
    data = [[25], [30], [None], [35], [None]]
    exepected_data = [25, 30, None, 35, None]
    cursor.executemany("declare t number; begin t := :1; end;", data)
    assert var.values == exepected_data


def test_cursor_1213(cursor, test_env):
    "1213 - test executemany with incorrect parameters"
    with test_env.assert_raises_full_code("DPY-2004"):
        cursor.executemany("select :1 from dual", [1])


def test_cursor_1214(cursor, test_env):
    "1214 - test executemany with mixed binds (pos first)"
    rows = [["test"], {"value": 1}]
    with test_env.assert_raises_full_code("DPY-2006"):
        cursor.executemany("select :1 from dual", rows)


def test_cursor_1215(cursor, test_env):
    "1215 - test executemany with mixed binds (name first)"
    rows = [{"value": 1}, ["test"]]
    with test_env.assert_raises_full_code("DPY-2006"):
        cursor.executemany("select :value from dual", rows)


def test_cursor_1216(cursor, empty_tab):
    "1216 - test executemany() with a pl/sql statement with dml returning"
    num_rows = 5
    out_var = cursor.var(oracledb.NUMBER, arraysize=5)
    cursor.setinputsizes(out_var)
    cursor.executemany(
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


def test_cursor_1217(cursor, empty_tab):
    "1217 - test executemany() with pl/sql in binds and out binds"
    values = [5, 8, 17, 24, 6]
    data = [(i, f"Test {i}") for i in values]
    out_bind = cursor.var(oracledb.NUMBER, arraysize=5)
    cursor.setinputsizes(None, None, out_bind)
    cursor.executemany(
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


def test_cursor_1218(cursor, empty_tab):
    "1218 - test executemany() with pl/sql outbinds"
    out_bind = cursor.var(oracledb.NUMBER, arraysize=5)
    cursor.setinputsizes(out_bind)
    cursor.executemany("begin :out_var := 5; end;", 5)
    assert out_bind.values == [5, 5, 5, 5, 5]


def test_cursor_1219(cursor):
    "1219 - test re-executemany() with pl/sql in binds and out binds"
    values = [5, 8, 17, 24, 6]
    data = [(i, f"Test {i}") for i in values]
    for i in range(2):
        cursor.execute("truncate table TestTempTable")
        out_bind = cursor.var(oracledb.NUMBER, arraysize=len(values))
        cursor.setinputsizes(None, None, out_bind)
        cursor.executemany(
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


def test_cursor_1220(cursor):
    "1220 - test PL/SQL statement with single row bind"
    value = 4020
    var = cursor.var(int)
    cursor.executemany("begin :1 := :2; end;", [[var, value]])
    assert var.values == [value]


def test_cursor_1221(conn, cursor, empty_tab):
    "1221 - test deferral of type assignment"
    data = [(1, None), (2, 25)]
    cursor.executemany(
        """
        insert into TestTempTable
        (IntCol, NumberCol)
        values (:1, :2)
        """,
        data,
    )
    conn.commit()
    cursor.execute("""
        select IntCol, NumberCol
        from TestTempTable
        order by IntCol
        """)
    assert cursor.fetchall() == data


def test_cursor_1222(cursor):
    "1222 - test PL/SQL with a lerge number of binds"
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
        out_binds.append(cursor.var(int, arraysize=len(all_bind_values)))
        for j, bind_values in enumerate(all_bind_values):
            bind_values.extend(
                [out_binds[-1], n * 1 + j, n * 2 + j, n * 3 + j]
            )
    lf = "\n"
    sql = f"begin{lf}{lf.join(parts)}{lf}end;"
    cursor.executemany(sql, all_bind_values)
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


def test_cursor_1223(cursor, test_env):
    "3901 - test executing a None statement"
    with test_env.assert_raises_full_code("DPY-2001"):
        cursor.executemany(None, [(1,), (2,)])


def test_cursor_1224(cursor):
    """
    4024 - test executemany with number of iterations
    (previous bind values)
    """
    data = [(2,), (3,), (4,)]
    for num_iterations in range(1, len(data) + 1):
        cursor.execute("truncate table TestLongs")
        cursor.executemany("insert into TestLongs (IntCol) values (:1)", data)
        cursor.executemany(None, num_iterations)
        cursor.execute("select IntCol from TestLongs")
        expected_value = data + data[:num_iterations]
        assert cursor.fetchall() == expected_value


def test_cursor_1225(cursor):
    "1225 - test executemany with empty lists and number of iterations"
    values = [[] for _ in range(5)]
    for num_iterations in (4, 6):
        cursor.execute("truncate table TestLongs")
        cursor.executemany(
            "insert into TestLongs (IntCol) values (67)",
            values,
        )
        cursor.executemany(None, num_iterations)
        cursor.execute("select IntCol from TestLongs")
        expected_value = [(67,)] * (len(values) + num_iterations)
        assert cursor.fetchall() == expected_value


def test_cursor_1226(cursor):
    "1226 - test executemany error offset returned correctly"
    data = [(i,) for i in range(1, 11)]
    with pytest.raises(oracledb.Error) as excinfo:
        cursor.executemany(
            """
            declare
                t_Value     number;
            begin
                t_Value := 10 / (4 - :1);
            end;
            """,
            data,
        )
    (error_obj,) = excinfo.value.args
    assert error_obj.offset == 3


def test_cursor_1227(cursor, empty_tab, test_env):
    "1227 - test executemany with number of iterations too small"
    data = [[1], [2], [3]]
    cursor.executemany(
        """
        declare
            t_Value         number;
        begin
            t_Value := :1;
        end;
        """,
        data,
    )
    cursor.executemany(None, 2)
    with test_env.assert_raises_full_code("DPY-2016"):
        cursor.executemany(None, 4)


def test_cursor_1228(cursor):
    "1228 - test executemany with empty parameter set"
    cursor.executemany("insert into TestTempTable values (:1)", [])


def test_cursor_1229(cursor, test_env):
    "1229 - test executemany with an empty statement"
    with test_env.assert_raises_full_code("DPY-2066"):
        cursor.executemany("", 5)
    with test_env.assert_raises_full_code("DPY-2066"):
        cursor.executemany("  ", 5)


def test_cursor_1230(cursor):
    "1230 - test executemany with batch size 0"
    rows = [[1], [2]]
    with pytest.raises(TypeError):
        cursor.executemany(
            "insert into TestTempTable (IntCol) values (:1)",
            rows,
            batch_size=0,
        )


@pytest.mark.parametrize("batch_size", [1, 5, 99, 199, 200])
def test_cursor_1231(batch_size, conn, cursor, empty_tab, round_trip_checker):
    "1231 - test executemany with various batch sizes"
    rows = [(i + 1, f"String for row {i + 1}") for i in range(200)]
    cursor.executemany(
        "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)",
        rows,
        batch_size=batch_size,
    )
    expected_round_trips = len(rows) // batch_size
    if len(rows) % batch_size:
        expected_round_trips += 1
    assert round_trip_checker.get_value() == expected_round_trips
    conn.commit()
    cursor.execute(
        "select IntCol, StringCol1 from TestTempTable order by IntCol"
    )
    assert cursor.fetchall() == rows


def test_cursor_1232(conn, cursor, empty_tab):
    "1232 - test consecutive executemany() with all values null in first call"
    rows = [(i + 1, None) for i in range(10)] + [
        (i + 11, (i + 11) * 0.25) for i in range(10)
    ]
    pos = 0
    while pos < len(rows):
        cursor.executemany(
            "insert into TestTempTable (IntCol, NumberCol) values (:1, :2)",
            rows[pos : pos + 4],
        )
        pos += 4
    conn.commit()
    cursor.execute(
        "select IntCol, NumberCol from TestTempTable order by IntCol"
    )
    assert cursor.fetchall() == rows


def test_cursor_1233(conn, cursor, empty_tab):
    "1233 - test batched executemany() with all values null in first chunks"
    rows = [(i + 1, None) for i in range(10)] + [
        (i + 11, (i + 11) * 0.25) for i in range(10)
    ]
    cursor.executemany(
        "insert into TestTempTable (IntCol, NumberCol) values (:1, :2)",
        rows,
        batch_size=4,
    )
    conn.commit()
    cursor.execute(
        "select IntCol, NumberCol from TestTempTable order by IntCol"
    )
    assert cursor.fetchall() == rows


def test_cursor_1234(conn, cursor):
    "1234 - test executemany() with PL/SQL in/out variables"
    typ = conn.gettype("PKG_TESTRECORDS.UDT_RECORDARRAY")
    obj = typ.newobject()
    data = [((i + 1) * 10, f"String {(i + 1) * 10}") for i in range(4)]
    input_data = [(n, s, obj) for n, s in data]
    cursor.executemany(
        "begin pkg_TestRecords.TestInOutArrays(:1, :2, :3); end;", input_data
    )
    output_data = [(e.NUMBERVALUE, e.STRINGVALUE) for e in obj.aslist()]
    assert output_data == data
