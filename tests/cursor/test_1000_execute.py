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
Module for testing the cursor execute() method
"""

import collections

import oracledb


def test_1000(cursor):
    "1000 - test executing a statement without any arguments"
    result = cursor.execute("begin null; end;")
    assert result is None


def test_1001(conn, test_env):
    "1001 - test executing a None statement with bind variables"
    cursor = conn.cursor()
    with test_env.assert_raises_full_code("DPY-2001"):
        cursor.execute(None, x=5)


def test_1002(cursor):
    "1002 - test executing a statement with args and empty keyword args"
    simple_var = cursor.var(oracledb.NUMBER)
    args = [simple_var]
    kwargs = {}
    result = cursor.execute("begin :1 := 25; end;", args, **kwargs)
    assert result is None
    assert simple_var.getvalue() == 25


def test_1003(cursor):
    "1003 - test executing a statement with keyword arguments"
    simple_var = cursor.var(oracledb.NUMBER)
    result = cursor.execute("begin :value := 5; end;", value=simple_var)
    assert result is None
    assert simple_var.getvalue() == 5


def test_1004(cursor):
    "1004 - test executing a statement with a dictionary argument"
    simple_var = cursor.var(oracledb.NUMBER)
    dict_arg = dict(value=simple_var)
    result = cursor.execute("begin :value := 10; end;", dict_arg)
    assert result is None
    assert simple_var.getvalue() == 10


def test_1005(cursor, test_env):
    "1005 - test executing a statement with both a dict and keyword args"
    simple_var = cursor.var(oracledb.NUMBER)
    dict_arg = dict(value=simple_var)
    with test_env.assert_raises_full_code("DPY-2005"):
        cursor.execute("begin :value := 15; end;", dict_arg, value=simple_var)


def test_1006(cursor):
    "1006 - test executing a statement and then changing the array size"
    cursor.execute("select IntCol from TestNumbers")
    cursor.arraysize = 20
    assert len(cursor.fetchall()) == 10


def test_1007(cursor, test_env):
    "1007 - test that subsequent executes succeed after bad execute"
    sql = "begin raise_application_error(-20000, 'this); end;"
    with test_env.assert_raises_full_code("DPY-2041"):
        cursor.execute(sql)
    cursor.execute("begin null; end;")


def test_1008(cursor, test_env):
    "1008 - test that subsequent fetches fail after bad execute"
    with test_env.assert_raises_full_code("ORA-00904"):
        cursor.execute("select y from dual")
    with test_env.assert_raises_full_code("DPY-1003"):
        cursor.fetchall()


def test_1009(cursor, test_env):
    "1009 - test executing a statement with an incorrect named bind"
    sql = "select * from TestStrings where IntCol = :value"
    with test_env.assert_raises_full_code("DPY-4008", "ORA-01036"):
        cursor.execute(sql, value2=3)


def test_1010(cursor):
    "1010 - test executing a statement with named binds"
    result = cursor.execute(
        """
        select *
        from TestNumbers
        where IntCol = :value1 and LongIntCol = :value2
        """,
        value1=1,
        value2=38,
    )
    assert len(result.fetchall()) == 1


def test_1011(cursor, test_env):
    "1011 - test executing a statement with an incorrect positional bind"
    sql = """
            select *
            from TestNumbers
            where IntCol = :value and LongIntCol = :value2"""
    with test_env.assert_raises_full_code("DPY-4009", "ORA-01008"):
        cursor.execute(sql, [3])


def test_1012(cursor):
    "1012 - test executing a statement with positional binds"
    result = cursor.execute(
        """
        select *
        from TestNumbers
        where IntCol = :value and LongIntCol = :value2
        """,
        [1, 38],
    )
    assert len(result.fetchall()) == 1


def test_1013(cursor):
    "1013 - test executing a statement after rebinding a named bind"
    statement = "begin :value := :value2 + 5; end;"
    simple_var = cursor.var(oracledb.NUMBER)
    simple_var2 = cursor.var(oracledb.NUMBER)
    simple_var2.setvalue(0, 5)
    result = cursor.execute(statement, value=simple_var, value2=simple_var2)
    assert result is None
    assert simple_var.getvalue() == 10

    simple_var = cursor.var(oracledb.NATIVE_FLOAT)
    simple_var2 = cursor.var(oracledb.NATIVE_FLOAT)
    simple_var2.setvalue(0, 10)
    result = cursor.execute(statement, value=simple_var, value2=simple_var2)
    assert result is None
    assert simple_var.getvalue() == 15


def test_1014(cursor):
    "1014 - test executing a PL/SQL statement with duplicate binds"
    simple_var = cursor.var(oracledb.NUMBER)
    simple_var.setvalue(0, 5)
    result = cursor.execute(
        """
        begin
            :value := :value + 5;
        end;
        """,
        value=simple_var,
    )
    assert result is None
    assert simple_var.getvalue() == 10


def test_1015(cursor):
    "1015 - test executing a PL/SQL statement with duplicate binds"
    simple_var = cursor.var(oracledb.NUMBER)
    simple_var.setvalue(0, 5)
    cursor.execute("begin :value := :value + 5; end;", [simple_var])
    assert simple_var.getvalue() == 10


def test_1016(cursor, test_env):
    "1016 - test executing a statement with an incorrect number of binds"
    statement = "begin :value := :value2 + 5; end;"
    var = cursor.var(oracledb.NUMBER)
    var.setvalue(0, 5)
    with test_env.assert_raises_full_code("DPY-4010", "ORA-01008"):
        cursor.execute(statement)
    with test_env.assert_raises_full_code("DPY-4010", "ORA-01008"):
        cursor.execute(statement, value=var)
    with test_env.assert_raises_full_code("DPY-4008", "ORA-01036"):
        cursor.execute(statement, value=var, value2=var, value3=var)


def test_1017(conn, cursor):
    "1017 - change in size on subsequent binds does not use optimised path"
    cursor.execute("truncate table TestTempTable")
    data = [(1, "Test String #1"), (2, "ABC" * 100)]
    for row in data:
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            row,
        )
    conn.commit()
    cursor.execute("select IntCol, StringCol1 from TestTempTable")
    assert cursor.fetchall() == data


def test_1018(conn, cursor):
    "1018 - test that dml can use optimised path"
    data_to_insert = [(i + 1, f"Test String #{i + 1}") for i in range(3)]
    cursor.execute("truncate table TestTempTable")
    for row in data_to_insert:
        with conn.cursor() as other_cursor:
            other_cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (:1, :2)
                """,
                row,
            )
    conn.commit()
    cursor.execute(
        "select IntCol, StringCol1 from TestTempTable order by IntCol"
    )
    assert cursor.fetchall() == data_to_insert


def test_1019(cursor, test_env):
    "1019 - test calling execute() with invalid parameters"
    sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
    with test_env.assert_raises_full_code("DPY-2003"):
        cursor.execute(sql, "These are not valid parameters")


def test_1020(cursor, test_env):
    "1020 - test calling execute() with mixed binds"
    cursor.execute("truncate table TestTempTable")
    cursor.setinputsizes(None, None, str)
    data = dict(val1=1, val2="Test String 1")
    with test_env.assert_raises_full_code("DPY-2006"):
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            returning StringCol1 into :out_var
            """,
            data,
        )


def test_1021(cursor):
    "1021 - test binding by name with double quotes"
    data = {'"_value1"': 1, '"VaLue_2"': 2, '"3VALUE"': 3}
    cursor.execute(
        'select :"_value1" + :"VaLue_2" + :"3VALUE" from dual',
        data,
    )
    (result,) = cursor.fetchone()
    assert result == 6


def test_1022(cursor):
    "1022 - test executing a statement with different input buffer sizes"
    sql = """
            insert into TestTempTable (IntCol, StringCol1, StringCol2)
            values (:int_col, :str_val1, :str_val2) returning IntCol
            into :ret_data"""
    values1 = {"int_col": 1, "str_val1": '{"a", "b"}', "str_val2": None}
    values2 = {"int_col": 2, "str_val1": None, "str_val2": '{"a", "b"}'}
    values3 = {"int_col": 3, "str_val1": '{"a"}', "str_val2": None}

    cursor.execute("truncate table TestTempTable")
    ret_bind = cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=1)
    cursor.setinputsizes(ret_data=ret_bind)
    cursor.execute(sql, values1)
    assert ret_bind.values == [["1"]]

    ret_bind = cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=1)
    cursor.setinputsizes(ret_data=ret_bind)
    cursor.execute(sql, values2)
    assert ret_bind.values == [["2"]]

    ret_bind = cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=1)
    cursor.setinputsizes(ret_data=ret_bind)
    cursor.execute(sql, values3)
    assert ret_bind.values == [["3"]]


def test_1023(conn, cursor):
    "1023 - test using rowfactory"
    cursor.execute("truncate table TestTempTable")
    cursor.execute("""
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'Test 1')
        """)
    conn.commit()
    cursor.execute("select IntCol, StringCol1 from TestTempTable")
    column_names = [col[0] for col in cursor.description]

    def rowfactory(*row):
        return dict(zip(column_names, row))

    cursor.rowfactory = rowfactory
    assert cursor.rowfactory == rowfactory
    assert cursor.fetchall() == [{"INTCOL": 1, "STRINGCOL1": "Test 1"}]


def test_1024(conn, cursor):
    "1024 - test executing same query after setting rowfactory"
    cursor.execute("truncate table TestTempTable")
    data = [(1, "Test 1"), (2, "Test 2")]
    cursor.executemany(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        data,
    )
    conn.commit()
    cursor.execute("select IntCol, StringCol1 from TestTempTable")
    column_names = [col[0] for col in cursor.description]
    cursor.rowfactory = lambda *row: dict(zip(column_names, row))
    results1 = cursor.fetchall()
    cursor.execute("select IntCol, StringCol1 from TestTempTable")
    results2 = cursor.fetchall()
    assert results1 == results2


def test_1025(conn, cursor):
    "1025 - test executing different query after setting rowfactory"
    cursor.execute("truncate table TestTempTable")
    data = [(1, "Test 1"), (2, "Test 2")]
    cursor.executemany(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        data,
    )
    conn.commit()
    cursor.execute("select IntCol, StringCol1 from TestTempTable")
    column_names = [col[0] for col in cursor.description]
    cursor.rowfactory = lambda *row: dict(zip(column_names, row))
    cursor.execute("""
        select IntCol, StringCol
        from TestSTrings
        where IntCol between 1 and 3 order by IntCol
        """)
    expected_data = [(1, "String 1"), (2, "String 2"), (3, "String 3")]
    assert cursor.fetchall() == expected_data


def test_1026(conn):
    "1026 - test setting rowfactory on a REF cursor"
    with conn.cursor() as cursor:
        sql_function = "pkg_TestRefCursors.TestReturnCursor"
        ref_cursor = cursor.callfunc(
            sql_function, oracledb.DB_TYPE_CURSOR, [2]
        )
        column_names = [col[0] for col in ref_cursor.description]
        ref_cursor.rowfactory = lambda *row: dict(zip(column_names, row))
        expected_value = [
            {"INTCOL": 1, "STRINGCOL": "String 1"},
            {"INTCOL": 2, "STRINGCOL": "String 2"},
        ]
        assert ref_cursor.fetchall() == expected_value


def test_1027(cursor):
    "1027 - test using a subclassed string as bind parameter keys"

    class my_str(str):
        pass

    cursor.execute("truncate table TestTempTable")
    keys = {my_str("str_val"): oracledb.DB_TYPE_VARCHAR}
    cursor.setinputsizes(**keys)
    values = {
        my_str("int_val"): 3927,
        my_str("str_val"): "1027 - String Value",
    }
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:int_val, :str_val)
        """,
        values,
    )
    cursor.execute("select IntCol, StringCol1 from TestTempTable")
    assert cursor.fetchall() == [(3927, "1027 - String Value")]


def test_1028(cursor):
    "1028 - test using a sequence of parameters other than a list or tuple"

    class MySeq(collections.abc.Sequence):
        def __init__(self, *data):
            self.data = data

        def __len__(self):
            return len(self.data)

        def __getitem__(self, index):
            return self.data[index]

    values_to_insert = [MySeq(1, "String 1"), MySeq(2, "String 2")]
    expected_data = [tuple(value) for value in values_to_insert]
    cursor.execute("truncate table TestTempTable")
    cursor.executemany(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:int_val, :str_val)
        """,
        values_to_insert,
    )
    cursor.execute("""
        select IntCol, StringCol1
        from TestTempTable
        order by IntCol
        """)
    assert cursor.fetchall() == expected_data


def test_1029(cursor):
    "1029 - test an output type handler with prefetch > arraysize"

    def type_handler(cursor, metadata):
        return cursor.var(metadata.type_code, arraysize=cursor.arraysize)

    cursor.arraysize = 2
    cursor.prefetchrows = 3
    cursor.outputtypehandler = type_handler
    cursor.execute("select level from dual connect by level <= 5")
    assert cursor.fetchall() == [(1,), (2,), (3,), (4,), (5,)]


def test_1030(cursor, test_env):
    "1030 - test setinputsizes() but without binding"
    cursor.setinputsizes(None, int)
    sql = "select :1, : 2 from dual"
    with test_env.assert_raises_full_code("ORA-01008", "DPY-4010"):
        cursor.execute(sql, [])


def test_1031(conn, cursor, test_env):
    "1031 - test getting FetchInfo attributes"
    type_obj = conn.gettype("UDT_OBJECT")
    varchar_ratio, _ = test_env.charset_ratios
    test_values = [
        (
            "select IntCol from TestObjects",
            10,
            None,
            False,
            "INTCOL",
            False,
            9,
            0,
            oracledb.DB_TYPE_NUMBER,
            oracledb.DB_TYPE_NUMBER,
        ),
        (
            "select ObjectCol from TestObjects",
            None,
            None,
            False,
            "OBJECTCOL",
            True,
            None,
            None,
            type_obj,
            oracledb.DB_TYPE_OBJECT,
        ),
        (
            "select JsonVarchar from TestJsonCols",
            4000,
            4000 * varchar_ratio,
            True,
            "JSONVARCHAR",
            False,
            None,
            None,
            oracledb.DB_TYPE_VARCHAR,
            oracledb.DB_TYPE_VARCHAR,
        ),
        (
            "select FLOATCOL from TestNumbers",
            127,
            None,
            False,
            "FLOATCOL",
            False,
            126,
            -127,
            oracledb.DB_TYPE_NUMBER,
            oracledb.DB_TYPE_NUMBER,
        ),
    ]
    for (
        sql,
        display_size,
        internal_size,
        is_json,
        name,
        null_ok,
        precision,
        scale,
        typ,
        type_code,
    ) in test_values:
        cursor.execute(sql)
        (fetch_info,) = cursor.description
        assert isinstance(fetch_info, oracledb.FetchInfo)
        assert fetch_info.display_size == display_size
        assert fetch_info.internal_size == internal_size
        if test_env.has_server_version(18, 0):
            assert fetch_info.is_json == is_json
        assert fetch_info.name == name
        assert fetch_info.null_ok == null_ok
        assert fetch_info.precision == precision
        assert fetch_info.scale == scale
        assert fetch_info.type == typ
        assert fetch_info.type_code == type_code
        assert fetch_info.vector_dimensions is None
        assert fetch_info.vector_format is None


def test_1032(cursor):
    "1032 - test FetchInfo repr() and str()"
    cursor.execute("select IntCol from TestObjects")
    (fetch_info,) = cursor.description
    expected = "('INTCOL', <DbType DB_TYPE_NUMBER>, 10, None, 9, 0, False)"
    assert str(fetch_info) == expected
    assert repr(fetch_info) == expected


def test_1033(cursor):
    "1033 - test slicing FetchInfo"
    cursor.execute("select IntCol from TestObjects")
    (fetch_info,) = cursor.description
    assert fetch_info[1:3] == (oracledb.DB_TYPE_NUMBER, 10)


def test_1034(cursor):
    "1034 - test rowcount is zero for PL/SQL"
    cursor.execute("begin null; end;")
    assert cursor.rowcount == 0
    cursor.execute("select user from dual")
    cursor.fetchall()
    assert cursor.rowcount == 1
    cursor.execute("begin null; end;")
    assert cursor.rowcount == 0


def test_1035(cursor, test_env):
    "1035 - test raising no_data_found in PL/SQL"
    with test_env.assert_raises_full_code("ORA-01403"):
        cursor.execute("begin raise no_data_found; end;")


def test_1036(cursor, test_env):
    "1036 - test executing an empty statement"
    with test_env.assert_raises_full_code("DPY-2066"):
        cursor.execute("")
    with test_env.assert_raises_full_code("DPY-2066"):
        cursor.execute("  ")
