# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
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
1600 - Module for testing DML returning clauses
"""

import datetime

import oracledb
import pytest


def test_1600(cursor):
    "1600 - test insert (single row) with DML returning"
    cursor.execute("truncate table TestTempTable")
    int_val = 5
    str_val = "A test string"
    int_var = cursor.var(oracledb.NUMBER)
    str_var = cursor.var(str)
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:int_val, :str_val)
        returning IntCol, StringCol1 into :int_var, :str_var
        """,
        int_val=int_val,
        str_val=str_val,
        int_var=int_var,
        str_var=str_var,
    )
    assert int_var.values == [[int_val]]
    assert str_var.values == [[str_val]]


def test_1601(cursor):
    "1601 - test insert (multiple rows) with DML returning"
    cursor.execute("truncate table TestTempTable")
    int_values = [5, 8, 17, 24, 6]
    str_values = ["Test 5", "Test 8", "Test 17", "Test 24", "Test 6"]
    int_var = cursor.var(oracledb.NUMBER, arraysize=len(int_values))
    str_var = cursor.var(str, arraysize=len(int_values))
    cursor.setinputsizes(None, None, int_var, str_var)
    data = list(zip(int_values, str_values))
    cursor.executemany(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:int_val, :str_val)
        returning IntCol, StringCol1 into :int_var, :str_var
        """,
        data,
    )
    assert int_var.values == [[v] for v in int_values]
    assert str_var.values == [[v] for v in str_values]


def test_1602(cursor, test_env):
    "1602 - test insert with DML returning into too small a variable"
    cursor.execute("truncate table TestTempTable")
    int_val = 6
    str_val = "A different test string"
    int_var = cursor.var(oracledb.NUMBER)
    str_var = cursor.var(str, 2)
    parameters = dict(
        int_val=int_val, str_val=str_val, int_var=int_var, str_var=str_var
    )
    with test_env.assert_raises_full_code("DPY-4002", "DPI-1037"):
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:int_val, :str_val)
            returning IntCol, StringCol1 into :int_var, :str_var
            """,
            parameters,
        )


def test_1603(cursor):
    "1603 - test update single row with DML returning"
    int_val = 7
    str_val = "The updated value of the string"
    cursor.execute("truncate table TestTempTable")
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        (int_val, "The initial value of the string"),
    )
    int_var = cursor.var(oracledb.NUMBER)
    str_var = cursor.var(str)
    cursor.execute(
        """
        update TestTempTable set
            StringCol1 = :str_val
        where IntCol = :int_val
        returning IntCol, StringCol1 into :int_var, :str_var
        """,
        int_val=int_val,
        str_val=str_val,
        int_var=int_var,
        str_var=str_var,
    )
    assert int_var.values == [[int_val]]
    assert str_var.values == [[str_val]]


def test_1604(cursor):
    "1604 - test update no rows with DML returning"
    int_val = 8
    str_val = "The updated value of the string"
    cursor.execute("truncate table TestTempTable")
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        (int_val, "The initial value of the string"),
    )
    int_var = cursor.var(oracledb.NUMBER)
    str_var = cursor.var(str)
    cursor.execute(
        """
        update TestTempTable set
            StringCol1 = :str_val
        where IntCol = :int_val
        returning IntCol, StringCol1 into :int_var, :str_var
        """,
        int_val=int_val + 1,
        str_val=str_val,
        int_var=int_var,
        str_var=str_var,
    )
    assert int_var.values == [[]]
    assert str_var.values == [[]]
    assert int_var.getvalue() == []
    assert str_var.getvalue() == []


def test_1605(cursor):
    "1605 - test update multiple rows with DML returning"
    cursor.execute("truncate table TestTempTable")
    for i in (8, 9, 10):
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1) values (:1, :2)
            """,
            (i, f"The initial value of string {i}"),
        )
    int_var = cursor.var(oracledb.NUMBER)
    str_var = cursor.var(str)
    cursor.execute(
        """
        update TestTempTable set
            IntCol = IntCol + 15,
            StringCol1 = 'The final value of string ' || to_char(IntCol)
        returning IntCol, StringCol1 into :int_var, :str_var
        """,
        int_var=int_var,
        str_var=str_var,
    )
    assert cursor.rowcount == 3
    assert int_var.values == [[23, 24, 25]]
    expected_values = [
        [
            "The final value of string 8",
            "The final value of string 9",
            "The final value of string 10",
        ]
    ]
    assert str_var.values == expected_values


def test_1606(cursor):
    "1606 - test update multiple rows with DML returning (executemany)"
    data = [(i, f"The initial value of string {i}") for i in range(1, 11)]
    cursor.execute("truncate table TestTempTable")
    cursor.executemany(
        "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)",
        data,
    )
    int_var = cursor.var(oracledb.NUMBER, arraysize=3)
    str_var = cursor.var(str, arraysize=3)
    cursor.setinputsizes(None, int_var, str_var)
    cursor.executemany(
        """
        update TestTempTable set
            IntCol = IntCol + 25,
            StringCol1 = 'Updated value of string ' || to_char(IntCol)
        where IntCol < :inVal
        returning IntCol, StringCol1 into :int_var, :str_var
        """,
        [[3], [8], [11]],
    )
    expected_values = [[26, 27], [28, 29, 30, 31, 32], [33, 34, 35]]
    assert int_var.values == expected_values
    expected_values = [
        ["Updated value of string 1", "Updated value of string 2"],
        [
            "Updated value of string 3",
            "Updated value of string 4",
            "Updated value of string 5",
            "Updated value of string 6",
            "Updated value of string 7",
        ],
        [
            "Updated value of string 8",
            "Updated value of string 9",
            "Updated value of string 10",
        ],
    ]
    assert str_var.values == expected_values


def test_1607(conn, cursor):
    "1607 - test inserting an object with DML returning"
    type_obj = conn.gettype("UDT_OBJECT")
    string_value = "The string that will be verified"
    obj = type_obj.newobject()
    obj.STRINGVALUE = string_value
    out_var = cursor.var(oracledb.DB_TYPE_OBJECT, typename="UDT_OBJECT")
    cursor.execute(
        """
        insert into TestObjects (IntCol, ObjectCol)
        values (4, :obj)returning ObjectCol into :outObj
        """,
        obj=obj,
        outObj=out_var,
    )
    (result,) = out_var.getvalue()
    assert result.STRINGVALUE == string_value
    conn.rollback()


def test_1608(cursor):
    "1608 - test inserting a row and returning a rowid"
    cursor.execute("truncate table TestTempTable")
    var = cursor.var(oracledb.ROWID)
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (278, 'String 278')
        returning rowid into :1
        """,
        [var],
    )
    (rowid,) = var.getvalue()
    cursor.execute(
        """
        select IntCol, StringCol1
        from TestTempTable
        where rowid = :1
        """,
        [rowid],
    )
    assert cursor.fetchall() == [(278, "String 278")]


def test_1609(conn, cursor):
    "1609 - test inserting with a REF cursor and returning a rowid"
    cursor.execute("truncate table TestTempTable")
    var = cursor.var(oracledb.ROWID)
    in_cursor = conn.cursor()
    in_cursor.execute(
        """
        select StringCol
        from TestStrings
        where IntCol >= 5
        order by IntCol
        """
    )
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (187, pkg_TestRefCursors.TestInCursor(:1))
        returning rowid into :2
        """,
        (in_cursor, var),
    )
    (rowid,) = var.getvalue()
    cursor.execute(
        """
        select IntCol, StringCol1
        from TestTempTable
        where rowid = :1
        """,
        [rowid],
    )
    assert cursor.fetchall() == [(187, "String 7 (Modified)")]


def test_1610(cursor):
    "1610 - test delete returning decreasing number of rows"
    data = [(i, f"Test String {i}") for i in range(1, 11)]
    cursor.execute("truncate table TestTempTable")
    cursor.executemany(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        data,
    )
    results = []
    int_var = cursor.var(int)
    cursor.setinputsizes(None, int_var)
    for int_val in (5, 8, 10):
        cursor.execute(
            """
            delete from TestTempTable
            where IntCol < :1
            returning IntCol into :2
            """,
            [int_val],
        )
        results.append(int_var.getvalue())
    assert results == [[1, 2, 3, 4], [5, 6, 7], [8, 9]]


def test_1611(cursor):
    "1611 - test delete returning no rows after returning many rows"
    data = [(i, f"Test String {i}") for i in range(1, 11)]
    cursor.execute("truncate table TestTempTable")
    cursor.executemany(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        data,
    )
    int_var = cursor.var(int)
    cursor.execute(
        """
        delete from TestTempTable
        where IntCol < :1
        returning IntCol into :2
        """,
        [5, int_var],
    )
    assert int_var.getvalue() == [1, 2, 3, 4]
    cursor.execute(None, [4, int_var])
    assert int_var.getvalue() == []


def test_1612(cursor, test_env):
    "1612 - test DML returning when an error occurs"
    cursor.execute("truncate table TestTempTable")
    int_val = 7
    str_val = "A" * 401
    int_var = cursor.var(oracledb.NUMBER)
    str_var = cursor.var(str)
    sql = """
            insert into TestTempTable (IntCol, StringCol1)
            values (:int_val, :str_val)
            returning IntCol, StringCol1 into :int_var, :str_var"""
    parameters = dict(
        int_val=int_val, str_val=str_val, int_var=int_var, str_var=str_var
    )
    with test_env.assert_raises_full_code("ORA-12899"):
        cursor.execute(sql, parameters)


def test_1613(cursor):
    "1613 - test DML returning with no input variables, multiple iters"
    cursor.execute("truncate table TestTempTable")
    sql = """
            insert into TestTempTable (IntCol)
            values ((select count(*) + 1 from TestTempTable))
            returning IntCol into :1"""
    var = cursor.var(int)
    cursor.execute(sql, [var])
    assert var.getvalue() == [1]
    cursor.execute(sql, [var])
    assert var.getvalue() == [2]


def test_1614(cursor):
    "1614 - test DML returning with a quoted bind name"
    sql = """
            insert into TestTempTable (IntCol, StringCol1)
            values (:int_val, :str_val)
            returning IntCol, StringCol1 into :"_val1" , :"VaL_2" """
    cursor.parse(sql)
    expected_bind_names = ["INT_VAL", "STR_VAL", "_val1", "VaL_2"]
    assert cursor.bindnames() == expected_bind_names


def test_1615(cursor, test_env):
    "1615 - test DML returning with an invalid bind name"
    sql = """
            insert into TestTempTable (IntCol)
            values (:int_val)
            returning IntCol, StringCol1 into :ROWID"""
    with test_env.assert_raises_full_code("ORA-01745"):
        cursor.parse(sql)


def test_1616(cursor):
    "1616 - test DML returning with a non-ascii bind name"
    sql = """
            insert into TestTempTable (IntCol)
            values (:int_val)
            returning IntCol, StringCol1 into :méil"""
    cursor.prepare(sql)
    assert cursor.bindnames() == ["INT_VAL", "MÉIL"]


def test_1617(conn, cursor):
    "1617 - test DML returning with input bind variable data"
    cursor.execute("truncate table TestTempTable")
    out_var = cursor.var(int)
    cursor.execute(
        """
        insert into TestTempTable (IntCol)
        values (:int_val)
        returning IntCol + :add_val into :out_val
        """,
        int_val=5,
        add_val=18,
        out_val=out_var,
    )
    conn.commit()
    assert out_var.getvalue() == [23]


def test_1618(conn, cursor):
    "1618 - test DML returning with LOBs and an output converter"
    cursor.execute("delete from TestCLOBs")
    out_var = cursor.var(
        oracledb.DB_TYPE_CLOB, outconverter=lambda value: value.read()
    )
    lob_value = "A short CLOB - 1618"
    cursor.execute(
        """
        insert into TestCLOBs (IntCol, ClobCol)
        values (1, :in_val)
        returning CLOBCol into :out_val
        """,
        in_val=lob_value,
        out_val=out_var,
    )
    conn.commit()
    assert out_var.getvalue() == [lob_value]


def test_1619(conn, cursor):
    "1619 - test DML returning with CLOB converted to LONG"
    cursor.execute("delete from TestCLOBs")
    out_var = cursor.var(oracledb.DB_TYPE_LONG)
    lob_value = "A short CLOB - 1619"
    cursor.execute(
        """
        insert into TestCLOBs
        (IntCol, ClobCol)
        values (1, :in_val)
        returning CLOBCol into :out_val
        """,
        in_val=lob_value,
        out_val=out_var,
    )
    conn.commit()
    assert out_var.getvalue() == [lob_value]


def test_1620(cursor):
    "1620 - test dml returning with an index organized table"
    cursor.execute("truncate table TestUniversalRowids")
    rowid_var = cursor.var(oracledb.ROWID)
    data = (1, "ABC", datetime.datetime(2017, 4, 11), rowid_var)
    sql = """
            insert into TestUniversalRowids values (:1, :2, :3)
            returning rowid into :4"""
    cursor.execute(sql, data)
    (rowid_value,) = rowid_var.getvalue()
    cursor.execute(
        """
        select *
        from TestUniversalRowids
        where rowid = :1
        """,
        [rowid_value],
    )
    (row,) = cursor.fetchall()
    assert row == data[:3]


def test_1621(cursor):
    "1621 - test plsql returning rowids with index organized table"
    cursor.execute("truncate table TestUniversalRowids")
    rowid_var = cursor.var(oracledb.ROWID)
    data = (1, "ABC", datetime.datetime(2017, 4, 11), rowid_var)
    cursor.execute(
        """
        begin
            insert into TestUniversalRowids values (:1, :2, :3)
            returning rowid into :4;
        end;
        """,
        data,
    )
    rowid_value = rowid_var.values[0]
    cursor.execute(
        """
        select *
        from TestUniversalRowids
        where rowid = :1
        """,
        [rowid_value],
    )
    (row,) = cursor.fetchall()
    assert row == data[:3]


def test_1622(cursor):
    "1622 - parse DML returning with no spaces"
    cursor.execute("truncate table TestTempTable")
    sql = (
        "insert into TestTempTable (IntCol) values (:in_val)"
        "returning(IntCol)into :out_val"
    )
    out_val = cursor.var(int, arraysize=5)
    cursor.execute(sql, in_val=25, out_val=out_val)
    assert out_val.getvalue() == [25]


def test_1623(skip_unless_thin_mode, cursor, test_env):
    "1623 - execute DML returning with duplicated binds"
    cursor.execute("truncate table TestTempTable")
    str_val = cursor.var(str)
    str_val.setvalue(0, "Test Data")
    sql = """
        insert into TestTempTable (IntCol, StringCol1)
        values (:id_val, :str_val || ' (Additional String)')
        returning StringCol1 into :str_val
    """
    with test_env.assert_raises_full_code("DPY-2048"):
        cursor.execute(sql, id_val=1, str_val=str_val)


def test_1624(cursor):
    "1624 - use bind variable in new statement after RETURNING statement"
    cursor.execute("truncate table TestTempTable")
    sql = (
        "insert into TestTempTable (IntCol) values (:in_val)"
        "returning IntCol + 15 into :out_val"
    )
    out_val = cursor.var(int, arraysize=5)
    cursor.execute(sql, in_val=25, out_val=out_val)
    assert out_val.getvalue() == [40]
    sql = "begin :out_val := :in_val + 35; end;"
    cursor.execute(sql, in_val=35, out_val=out_val)
    assert out_val.getvalue() == 70


def test_1625(conn, cursor):
    "1625 - test DML returning with multiple LOBs returned"
    lob_data = [
        "Short CLOB - 1625a",
        "Short CLOB - 1625b",
        "Short CLOB - 1625c",
        "Short CLOB - 1625d",
    ]
    all_data = [(i + 1, d) for i, d in enumerate(lob_data)]
    cursor.execute("delete from TestCLOBs")
    cursor.executemany(
        "insert into TestCLOBs (IntCol, ClobCol) values (:1, :2)", all_data
    )
    ret_val = cursor.var(oracledb.DB_TYPE_CLOB)
    cursor.execute(
        """
        update TestCLOBs set
            ExtraNumCol1 = 1
        where ExtraNumCol1 is null
        returning ClobCol into :ret_val
        """,
        [ret_val],
    )
    conn.commit()
    ret_lob_data = [v.read() for v in ret_val.getvalue()]
    ret_lob_data.sort()
    assert ret_lob_data == lob_data


# blocked by bug 37741324 in thick mode
def test_1626(skip_unless_thin_mode, conn, cursor, test_env):
    "1626 - test DML returning with multiple DbObjects returned"
    if not test_env.has_server_version(21):
        pytest.skip("awaiting fix for bug 37756810")
    arrays = [
        (1626, 1627, 1628),
        (1629, 1630, 1631),
        (1632, 1633, 1634),
        (1635, 1636, 1637),
    ]
    all_data = [(i + 4, v[0], v[1], v[2]) for i, v in enumerate(arrays)]
    cursor.execute("delete from TestObjects where IntCol > 3")
    cursor.executemany(
        """
        insert into TestObjects (IntCol, ArrayCol)
        values (:1, udt_Array(:1, :2, :3))
        """,
        all_data,
    )
    typ = conn.gettype("UDT_ARRAY")
    ret_val = cursor.var(typ)
    cursor.execute(
        """
        update TestObjects set
            ObjectCol = null
        where IntCol > 3
        returning ArrayCol into :ret_val
        """,
        [ret_val],
    )
    conn.commit()
    ret_obj_data = [tuple(v) for v in ret_val.getvalue()]
    ret_obj_data.sort()
    assert ret_obj_data == arrays
