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
5400 - Module for testing the cursor execute() method with asyncio
"""

import collections

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


async def test_5400(async_cursor):
    "5400 - test executing a statement without any arguments"
    result = await async_cursor.execute("begin null; end;")
    assert result is None


async def test_5401(async_cursor, test_env):
    "5401 - test executing a None statement with bind variables"
    with test_env.assert_raises_full_code("DPY-2001"):
        await async_cursor.execute(None, x=5)


async def test_5402(async_cursor):
    "5402 - test executing a statement with args and empty keyword args"
    simple_var = async_cursor.var(oracledb.NUMBER)
    args = [simple_var]
    kwargs = {}
    result = await async_cursor.execute("begin :1 := 25; end;", args, **kwargs)
    assert result is None
    assert simple_var.getvalue() == 25


async def test_5403(async_cursor):
    "5403 - test executing a statement with keyword arguments"
    simple_var = async_cursor.var(oracledb.NUMBER)
    result = await async_cursor.execute(
        "begin :value := 5; end;", value=simple_var
    )
    assert result is None
    assert simple_var.getvalue() == 5


async def test_5404(async_cursor):
    "5404 - test executing a statement with a dictionary argument"
    simple_var = async_cursor.var(oracledb.NUMBER)
    dict_arg = dict(value=simple_var)
    result = await async_cursor.execute("begin :value := 10; end;", dict_arg)
    assert result is None
    assert simple_var.getvalue() == 10


async def test_5405(async_cursor, test_env):
    "5405 - test executing a statement with both a dict and keyword args"
    simple_var = async_cursor.var(oracledb.NUMBER)
    dict_arg = dict(value=simple_var)
    with test_env.assert_raises_full_code("DPY-2005"):
        await async_cursor.execute(
            "begin :value := 15; end;", dict_arg, value=simple_var
        )


async def test_5406(async_cursor):
    "5406 - test executing a statement and then changing the array size"
    await async_cursor.execute("select IntCol from TestNumbers")
    async_cursor.arraysize = 5
    assert len(await async_cursor.fetchall()) == 10


async def test_5407(async_cursor, test_env):
    "5407 - test that subsequent executes succeed after bad execute"
    sql = "begin raise_application_error(-20000, 'this); end;"
    with test_env.assert_raises_full_code("DPY-2041"):
        await async_cursor.execute(sql)
    await async_cursor.execute("begin null; end;")


async def test_5408(async_cursor, test_env):
    "5408 - test that subsequent fetches fail after bad execute"
    with test_env.assert_raises_full_code("ORA-00904"):
        await async_cursor.execute("select y from dual")
    with test_env.assert_raises_full_code("DPY-1003"):
        await async_cursor.fetchall()


async def test_5409(async_cursor, test_env):
    "5409 - test executing a statement with an incorrect named bind"
    sql = "select * from TestStrings where IntCol = :value"
    with test_env.assert_raises_full_code("DPY-4008", "ORA-01036"):
        await async_cursor.execute(sql, value2=3)


async def test_5410(async_cursor):
    "5410 - test executing a statement with named binds"
    await async_cursor.execute(
        """
        select *
        from TestNumbers
        where IntCol = :value1 and LongIntCol = :value2
        """,
        value1=1,
        value2=38,
    )
    assert len(await async_cursor.fetchall()) == 1


async def test_5411(async_cursor, test_env):
    "5411 - test executing a statement with an incorrect positional bind"
    sql = """
            select *
            from TestNumbers
            where IntCol = :value and LongIntCol = :value2"""
    with test_env.assert_raises_full_code("DPY-4009", "ORA-01008"):
        await async_cursor.execute(sql, [3])


async def test_5412(async_cursor):
    "5412 - test executing a statement with positional binds"
    await async_cursor.execute(
        """
        select *
        from TestNumbers
        where IntCol = :value and LongIntCol = :value2
        """,
        [1, 38],
    )
    assert len(await async_cursor.fetchall()) == 1


async def test_5413(async_cursor):
    "5413 - test executing a statement after rebinding a named bind"
    statement = "begin :value := :value2 + 5; end;"
    simple_var = async_cursor.var(oracledb.NUMBER)
    simple_var2 = async_cursor.var(oracledb.NUMBER)
    simple_var2.setvalue(0, 5)
    result = await async_cursor.execute(
        statement, value=simple_var, value2=simple_var2
    )
    assert result is None
    assert simple_var.getvalue() == 10

    simple_var = async_cursor.var(oracledb.NATIVE_FLOAT)
    simple_var2 = async_cursor.var(oracledb.NATIVE_FLOAT)
    simple_var2.setvalue(0, 10)
    result = await async_cursor.execute(
        statement, value=simple_var, value2=simple_var2
    )
    assert result is None
    assert simple_var.getvalue() == 15


async def test_5414(async_cursor):
    "5414 - test executing a PL/SQL statement with duplicate binds"
    simple_var = async_cursor.var(oracledb.NUMBER)
    simple_var.setvalue(0, 5)
    result = await async_cursor.execute(
        """
        begin
            :value := :value + 5;
        end;
        """,
        value=simple_var,
    )
    assert result is None
    assert simple_var.getvalue() == 10


async def test_5415(async_cursor):
    "5415 - test executing a PL/SQL statement with duplicate binds"
    simple_var = async_cursor.var(oracledb.NUMBER)
    simple_var.setvalue(0, 5)
    await async_cursor.execute(
        "begin :value := :value + 5; end;", [simple_var]
    )
    assert simple_var.getvalue() == 10


async def test_5416(async_cursor, test_env):
    "5416 - test executing a statement with an incorrect number of binds"
    statement = "begin :value := :value2 + 5; end;"
    var = async_cursor.var(oracledb.NUMBER)
    var.setvalue(0, 5)
    with test_env.assert_raises_full_code("DPY-4010", "ORA-01008"):
        await async_cursor.execute(statement)
    with test_env.assert_raises_full_code("DPY-4010", "ORA-01008"):
        await async_cursor.execute(statement, value=var)
    with test_env.assert_raises_full_code("DPY-4008", "ORA-01036"):
        await async_cursor.execute(
            statement, value=var, value2=var, value3=var
        )


async def test_5417(async_conn, async_cursor):
    "5417 - change in size on subsequent binds does not use optimised path"
    await async_cursor.execute("truncate table TestTempTable")
    data = [(1, "Test String #1"), (2, "ABC" * 100)]
    for row in data:
        await async_cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            row,
        )
    await async_conn.commit()
    await async_cursor.execute("select IntCol, StringCol1 from TestTempTable")
    assert await async_cursor.fetchall() == data


async def test_5418(async_conn, async_cursor):
    "5418 - test that dml can use optimised path"
    data_to_insert = [(i + 1, f"Test String #{i + 1}") for i in range(3)]
    await async_cursor.execute("truncate table TestTempTable")
    for row in data_to_insert:
        with async_conn.cursor() as cursor:
            await cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (:1, :2)
                """,
                row,
            )
    await async_conn.commit()
    await async_cursor.execute(
        "select IntCol, StringCol1 from TestTempTable order by IntCol"
    )
    assert await async_cursor.fetchall() == data_to_insert


async def test_5419(async_cursor, test_env):
    "5419 - test calling execute() with invalid parameters"
    sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
    with test_env.assert_raises_full_code("DPY-2003"):
        await async_cursor.execute(sql, "These are not valid parameters")


async def test_5420(async_cursor, test_env):
    "5420 - test calling execute() with mixed binds"
    await async_cursor.execute("truncate table TestTempTable")
    async_cursor.setinputsizes(None, None, str)
    data = dict(val1=1, val2="Test String 1")
    with test_env.assert_raises_full_code("DPY-2006"):
        await async_cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            returning StringCol1 into :out_var
            """,
            data,
        )


async def test_5421(async_cursor):
    "5421 - test binding by name with double quotes"
    data = {'"_value1"': 1, '"VaLue_2"': 2, '"3VALUE"': 3}
    await async_cursor.execute(
        'select :"_value1" + :"VaLue_2" + :"3VALUE" from dual',
        data,
    )
    (result,) = await async_cursor.fetchone()
    assert result == 6


async def test_5422(async_cursor):
    "5422 - test executing a statement with different input buffer sizes"
    sql = """
            insert into TestTempTable (IntCol, StringCol1, StringCol2)
            values (:int_col, :str_val1, :str_val2) returning IntCol
            into :ret_data"""
    values1 = {"int_col": 1, "str_val1": '{"a", "b"}', "str_val2": None}
    values2 = {"int_col": 2, "str_val1": None, "str_val2": '{"a", "b"}'}
    values3 = {"int_col": 3, "str_val1": '{"a"}', "str_val2": None}

    await async_cursor.execute("truncate table TestTempTable")
    ret_bind = async_cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=1)
    async_cursor.setinputsizes(ret_data=ret_bind)
    await async_cursor.execute(sql, values1)
    assert ret_bind.values == [["1"]]

    ret_bind = async_cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=1)
    async_cursor.setinputsizes(ret_data=ret_bind)
    await async_cursor.execute(sql, values2)
    assert ret_bind.values == [["2"]]

    ret_bind = async_cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=1)
    async_cursor.setinputsizes(ret_data=ret_bind)
    await async_cursor.execute(sql, values3)
    assert ret_bind.values == [["3"]]


async def test_5423(async_conn, async_cursor):
    "5423 - test using rowfactory"
    await async_cursor.execute("truncate table TestTempTable")
    await async_cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'Test 1')
        """
    )
    await async_conn.commit()
    await async_cursor.execute("select IntCol, StringCol1 from TestTempTable")
    column_names = [col[0] for col in async_cursor.description]

    def rowfactory(*row):
        return dict(zip(column_names, row))

    async_cursor.rowfactory = rowfactory
    assert async_cursor.rowfactory == rowfactory
    assert await async_cursor.fetchall() == [
        {"INTCOL": 1, "STRINGCOL1": "Test 1"}
    ]


async def test_5424(async_conn, async_cursor):
    "5424 - test executing same query after setting rowfactory"
    await async_cursor.execute("truncate table TestTempTable")
    data = [(1, "Test 1"), (2, "Test 2")]
    await async_cursor.executemany(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        data,
    )
    await async_conn.commit()
    await async_cursor.execute("select IntCol, StringCol1 from TestTempTable")
    column_names = [col[0] for col in async_cursor.description]
    async_cursor.rowfactory = lambda *row: dict(zip(column_names, row))
    results1 = await async_cursor.fetchall()
    await async_cursor.execute("select IntCol, StringCol1 from TestTempTable")
    results2 = await async_cursor.fetchall()
    assert results1 == results2


async def test_5425(async_conn, async_cursor):
    "5425 - test executing different query after setting rowfactory"
    await async_cursor.execute("truncate table TestTempTable")
    data = [(1, "Test 1"), (2, "Test 2")]
    await async_cursor.executemany(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        data,
    )
    await async_conn.commit()
    await async_cursor.execute("select IntCol, StringCol1 from TestTempTable")
    column_names = [col[0] for col in async_cursor.description]
    async_cursor.rowfactory = lambda *row: dict(zip(column_names, row))
    await async_cursor.execute(
        """
        select IntCol, StringCol
        from TestSTrings
        where IntCol between 1 and 3 order by IntCol
        """
    )
    expected_data = [(1, "String 1"), (2, "String 2"), (3, "String 3")]
    assert await async_cursor.fetchall() == expected_data


async def test_5426(async_conn):
    "5426 - test setting rowfactory on a REF cursor"
    with async_conn.cursor() as cursor:
        sql_function = "pkg_TestRefCursors.TestReturnCursor"
        ref_cursor = await cursor.callfunc(
            sql_function, oracledb.DB_TYPE_CURSOR, [2]
        )
        column_names = [col[0] for col in ref_cursor.description]
        ref_cursor.rowfactory = lambda *row: dict(zip(column_names, row))
        expected_value = [
            {"INTCOL": 1, "STRINGCOL": "String 1"},
            {"INTCOL": 2, "STRINGCOL": "String 2"},
        ]
        assert await ref_cursor.fetchall() == expected_value


async def test_5427(async_cursor):
    "5427 - test using a subclassed string as bind parameter keys"

    class my_str(str):
        pass

    await async_cursor.execute("truncate table TestTempTable")
    keys = {my_str("str_val"): oracledb.DB_TYPE_VARCHAR}
    async_cursor.setinputsizes(**keys)
    values = {
        my_str("int_val"): 5427,
        my_str("str_val"): "5427 - String Value",
    }
    await async_cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:int_val, :str_val)
        """,
        values,
    )
    await async_cursor.execute("select IntCol, StringCol1 from TestTempTable")
    assert await async_cursor.fetchall() == [(5427, "5427 - String Value")]


async def test_5428(async_cursor):
    "5428 - test using a sequence of parameters other than a list or tuple"

    class MySeq(collections.abc.Sequence):
        def __init__(self, *data):
            self.data = data

        def __len__(self):
            return len(self.data)

        def __getitem__(self, index):
            return self.data[index]

    values_to_insert = [MySeq(1, "String 1"), MySeq(2, "String 2")]
    expected_data = [tuple(value) for value in values_to_insert]
    await async_cursor.execute("truncate table TestTempTable")
    await async_cursor.executemany(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:int_val, :str_val)
        """,
        values_to_insert,
    )
    await async_cursor.execute(
        """
        select IntCol, StringCol1
        from TestTempTable
        order by IntCol
        """
    )
    assert await async_cursor.fetchall() == expected_data


async def test_5429(async_cursor):
    "5429 - test an output type handler with prefetch > arraysize"

    def type_handler(cursor, metadata):
        return cursor.var(metadata.type_code, arraysize=cursor.arraysize)

    async_cursor.arraysize = 2
    async_cursor.prefetchrows = 3
    async_cursor.outputtypehandler = type_handler
    await async_cursor.execute("select level from dual connect by level <= 5")
    assert await async_cursor.fetchall() == [(1,), (2,), (3,), (4,), (5,)]


async def test_5430(async_cursor, test_env):
    "5430 - test setinputsizes() but without binding"
    async_cursor.setinputsizes(None, int)
    sql = "select :1, : 2 from dual"

    with test_env.assert_raises_full_code("ORA-01008", "DPY-4010"):
        await async_cursor.execute(sql, [])


async def test_5431(async_conn, async_cursor, test_env):
    "5431 - test getting FetchInfo attributes"
    type_obj = await async_conn.gettype("UDT_OBJECT")
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
        await async_cursor.execute(sql)
        (fetch_info,) = async_cursor.description
        assert isinstance(fetch_info, oracledb.FetchInfo)
        assert fetch_info.display_size == display_size
        assert fetch_info.internal_size == internal_size
        if test_env.has_server_version(18):
            assert fetch_info.is_json == is_json
        assert fetch_info.name == name
        assert fetch_info.null_ok == null_ok
        assert fetch_info.precision == precision
        assert fetch_info.scale == scale
        assert fetch_info.type == typ
        assert fetch_info.type_code == type_code


async def test_5432(async_cursor):
    "5432 - test FetchInfo repr() and str()"
    await async_cursor.execute("select IntCol from TestObjects")
    (fetch_info,) = async_cursor.description
    expected = "('INTCOL', <DbType DB_TYPE_NUMBER>, 10, None, 9, 0, False)"
    assert str(fetch_info) == expected
    assert repr(fetch_info) == expected


async def test_5433(async_cursor):
    "5433 - test slicing FetchInfo"
    await async_cursor.execute("select IntCol from TestObjects")
    (fetch_info,) = async_cursor.description
    assert fetch_info[1:3] == (oracledb.DB_TYPE_NUMBER, 10)


async def test_5434(async_conn, test_env):
    "5434 - test async context manager"
    expected_value = test_env.main_user.upper()
    with async_conn.cursor() as cursor:
        await cursor.execute("select user from dual")
        assert await cursor.fetchone() == (expected_value,)
    async with async_conn.cursor() as cursor:
        await cursor.execute("select user from dual")
        assert await cursor.fetchone() == (expected_value,)


async def test_5435(async_cursor):
    "5435 - test metadata requiring multiple packets"
    values = [f"Test value 5435 - {i}" for i in range(1, 301)]
    columns = ", ".join(f"'{v}'" for v in values)
    query = f"select {columns} from dual"
    await async_cursor.execute(query)
    row = await async_cursor.fetchone()
    assert row == tuple(values)


async def test_5436(async_cursor, test_env):
    "5436 - test raising no_data_found in PL/SQL"
    with test_env.assert_raises_full_code("ORA-01403"):
        await async_cursor.execute("begin raise no_data_found; end;")


async def test_5437(async_cursor, test_env):
    "5437 - test executing an empty statement"
    with test_env.assert_raises_full_code("DPY-2066"):
        await async_cursor.execute("")
    with test_env.assert_raises_full_code("DPY-2066"):
        await async_cursor.execute("  ")
