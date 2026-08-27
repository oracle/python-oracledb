# -----------------------------------------------------------------------------
# Copyright (c) 2024, 2026, Oracle and/or its affiliates.
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
Module for testing async pipelining.
"""

import datetime
import decimal

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


async def test_1200(async_conn):
    "1200 - test execute() and fetchall()."
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_execute("insert into TestTempTable (IntCol) values (:1)", [1])
    pipeline.add_execute(
        "insert into TestTempTable (IntCol) values (:val)", dict(val=2)
    )
    pipeline.add_commit()
    pipeline.add_fetchall("select IntCol from TestTempTable order by IntCol")
    results = await async_conn.run_pipeline(pipeline)
    assert results[-1].rows == [(1,), (2,)]


async def test_1201(async_conn):
    "1201 - test executemany()"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_executemany(
        "insert into TestTempTable (IntCol) values (:1)", [(2,), (3,)]
    )
    pipeline.add_executemany(
        "insert into TestTempTable (IntCol) values (:data)",
        [{"data": 4}, {"data": 5}],
    )
    pipeline.add_commit()
    pipeline.add_fetchall("select IntCol from TestTempTable order by IntCol")
    results = await async_conn.run_pipeline(pipeline)
    assert results[-1].rows == [(2,), (3,), (4,), (5,)]


async def test_1202(async_conn):
    "1202 - test fetchall() with arraysize"
    data = [(1,), (2,), (3,), (4,)]
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_executemany(
        "insert into TestTempTable (IntCol) values (:value)",
        [{"value": i} for i, in data],
    )
    pipeline.add_commit()
    arraysize = 1
    op = pipeline.add_fetchall(
        "select IntCol from TestTempTable order by IntCol",
        arraysize=arraysize,
    )
    assert op.arraysize == arraysize
    arraysize = len(data)
    op = pipeline.add_fetchall(
        "select IntCol from TestTempTable order by IntCol",
        arraysize=arraysize,
    )
    assert op.arraysize == arraysize
    results = await async_conn.run_pipeline(pipeline)
    assert results[-1].rows == data
    assert results[-2].rows == data


async def test_1203(async_conn):
    "1203 - test fetchall() with rowfactory"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_execute("""
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'test_7003')
        """)
    pipeline.add_commit()

    def rowfactory(*row):
        column_names = ["INTCOL", "STRINGCOL1"]
        return dict(zip(column_names, row))

    pipeline.add_fetchall(
        "select IntCol, StringCol1 from TestTempTable",
        rowfactory=rowfactory,
    )
    results = await async_conn.run_pipeline(pipeline)
    expected_value = [{"INTCOL": 1, "STRINGCOL1": "test_7003"}]
    assert results[-1].rows == expected_value


async def test_1204(async_conn):
    "1204 - test fetchone()"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_executemany(
        "insert into TestTempTable (IntCol) values (:1)", [(9,), (10,)]
    )
    pipeline.add_commit()
    pipeline.add_fetchone("select IntCol from TestTempTable order by IntCol")
    pipeline.add_fetchone("select :1 from dual", [23])
    pipeline.add_fetchone("select :val from dual", {"val": 5})
    results = await async_conn.run_pipeline(pipeline)
    assert results[-3].rows == [(9,)]
    assert results[-2].rows == [(23,)]
    assert results[-1].rows == [(5,)]


async def test_1205(async_conn):
    "1205 - test fetchone() with rowfactory"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_executemany(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:int, :str)
        """,
        [{"int": 3, "str": "Mac"}, {"int": 4, "str": "Doc"}],
    )
    pipeline.add_commit()

    def rowfactory(*row):
        column_names = ["INT", "STRING"]
        return dict(zip(column_names, row))

    op = pipeline.add_fetchone(
        "select IntCol, StringCol1 from TestTempTable order by IntCol",
        rowfactory=rowfactory,
    )
    assert op.rowfactory == rowfactory
    results = await async_conn.run_pipeline(pipeline)
    assert results[-1].rows == [{"INT": 3, "STRING": "Mac"}]


async def test_1206(async_conn):
    "1206 - test fetchmany()"
    data = [(i,) for i in range(10)]
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_executemany(
        "insert into TestTempTable (IntCol) values (:1)", data
    )
    pipeline.add_commit()
    pipeline.add_fetchmany("select IntCol from TestTempTable order by IntCol")
    pipeline.add_fetchmany("select :1 from dual", [1099])
    pipeline.add_fetchmany("select :val from dual", {"val": 366})
    results = await async_conn.run_pipeline(pipeline)
    assert results[-3].rows == data
    assert results[-2].rows == [(1099,)]
    assert results[-1].rows == [(366,)]


async def test_1207(async_conn):
    "1207 - test fetchmany() with num_rows"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    data = [(i,) for i in range(10)]
    pipeline.add_executemany(
        "insert into TestTempTable (IntCol) values (:1)", data
    )
    pipeline.add_commit()
    num_rows = 7
    op = pipeline.add_fetchmany(
        "select IntCol from TestTempTable order by IntCol",
        num_rows=num_rows,
    )
    assert op.num_rows == num_rows
    results = await async_conn.run_pipeline(pipeline)
    assert results[-1].rows == data[:num_rows]


async def test_1208(async_conn):
    "1208 - test fetchmany() with rowfactory and num_rows"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_executemany(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:int, :str)
        """,
        [{"int": 29, "str": "Feb"}, {"int": 4, "str": "Monday"}],
    )
    pipeline.add_commit()

    def rowfactory(*row):
        column_names = ["INT", "STRING"]
        return dict(zip(column_names, row))

    num_rows = 2
    op = pipeline.add_fetchmany(
        "select IntCol, StringCol1 from TestTempTable order by IntCol",
        num_rows=num_rows,
        rowfactory=rowfactory,
    )
    assert op.num_rows == num_rows
    assert op.rowfactory == rowfactory
    expected_value = [
        {"INT": 4, "STRING": "Monday"},
        {"INT": 29, "STRING": "Feb"},
    ]
    num_rows = 1
    op = pipeline.add_fetchmany(
        "select IntCol, StringCol1 from TestTempTable order by IntCol",
        rowfactory=rowfactory,
        num_rows=num_rows,
    )
    assert op.num_rows == num_rows
    assert op.rowfactory == rowfactory
    results = await async_conn.run_pipeline(pipeline)
    assert results[-2].rows == expected_value
    assert results[-1].rows == [{"INT": 4, "STRING": "Monday"}]


async def test_1209(async_conn):
    "1209 - test callfunc(), return_value and return_type"
    pipeline = oracledb.create_pipeline()
    pipeline.add_callfunc("func_Test", oracledb.DB_TYPE_NUMBER, ("Yes", 7))
    kwargs = {"a_String": "Keyword", "a_ExtraAmount": 12}
    pipeline.add_callfunc(
        "func_Test", oracledb.DB_TYPE_NUMBER, keyword_parameters=kwargs
    )

    # paramters and keyword parameters
    kwargs = {"a_ExtraAmount": 25}
    func_name = "func_Test"
    op = pipeline.add_callfunc(
        func_name, oracledb.DB_TYPE_NUMBER, ["Mixed"], kwargs
    )
    assert op.name == func_name
    assert op.return_type == oracledb.DB_TYPE_NUMBER
    assert op.statement is None
    results = await async_conn.run_pipeline(pipeline)
    assert results[0].return_value == 10
    assert results[1].return_value == 19
    assert results[2].return_value == 30


async def test_1210(async_conn, async_cursor):
    "1210 - test callproc() with parameters"
    pipeline = oracledb.create_pipeline()
    var = async_cursor.var(oracledb.DB_TYPE_NUMBER)
    proc_name = "proc_Test"
    params = ("hi", 5, var)
    op = pipeline.add_callproc(proc_name, params)
    assert op.name == proc_name
    assert op.parameters == params
    assert op.keyword_parameters is None
    assert op.statement is None
    assert op.arraysize == 0
    assert op.num_rows == 0
    await async_conn.run_pipeline(pipeline)
    assert var.getvalue() == 2


async def test_1211(async_conn, async_cursor):
    "1211 - test callproc() with keyword_parameters"
    in_out_value = async_cursor.var(oracledb.DB_TYPE_NUMBER)
    in_out_value.setvalue(0, 7)
    out_value = async_cursor.var(oracledb.DB_TYPE_NUMBER)
    params = []
    kwargs = dict(
        a_InValue="Peace", a_InOutValue=in_out_value, a_OutValue=out_value
    )
    pipeline = oracledb.create_pipeline()
    op = pipeline.add_callproc("proc_Test", params, kwargs)
    assert op.parameters == params
    assert op.keyword_parameters == kwargs
    await async_conn.run_pipeline(pipeline)
    assert in_out_value.getvalue() == 35
    assert out_value.getvalue() == 5


async def test_1212(async_conn, async_cursor):
    "1212 - test callproc() with parameters and keyword_parameters"
    in_out_value = async_cursor.var(oracledb.DB_TYPE_NUMBER)
    in_out_value.setvalue(0, 8)
    out_value = async_cursor.var(oracledb.DB_TYPE_NUMBER)
    params = ["Input_7612"]
    kwargs = dict(a_InOutValue=in_out_value, a_OutValue=out_value)
    pipeline = oracledb.create_pipeline()
    op = pipeline.add_callproc("proc_Test", params, kwargs)
    assert op.parameters == params
    assert op.keyword_parameters == kwargs
    await async_conn.run_pipeline(pipeline)
    assert in_out_value.getvalue() == 80
    assert out_value.getvalue() == 10


async def test_1213(async_conn):
    "1213 - test fetchmany() num_rows with 0 and negative values"
    data = [(i,) for i in range(10)]
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_executemany(
        "insert into TestTempTable (IntCol) values (:1)", data
    )
    sql = "select IntCol from TestTempTable"
    op = pipeline.add_fetchmany(sql, num_rows=0)
    assert op.statement == sql
    with pytest.raises(OverflowError):
        pipeline.add_fetchmany(sql, num_rows=-1)
    with pytest.raises(OverflowError):
        pipeline.add_fetchmany(sql, num_rows=-10)
    results = await async_conn.run_pipeline(pipeline)
    assert results[-1].rows == []


async def test_1214(async_conn):
    "1214 - test add_commit with transaction_in_progress"
    assert not async_conn.transaction_in_progress
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_execute(
        "insert into TestTempTable (IntCol) values (5)",
    )
    await async_conn.run_pipeline(pipeline)
    assert async_conn.transaction_in_progress
    pipeline = oracledb.create_pipeline()
    pipeline.add_commit()
    await async_conn.run_pipeline(pipeline)
    assert not async_conn.transaction_in_progress


async def test_1215(async_conn):
    "1215 - test getting an error in the middle of pipeline"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_execute("insert into TestTempTable (IntCol) values (:1)", [5])
    pipeline.add_commit()
    pipeline.add_fetchall(
        "select IntCol from TestTempTable order by IntCol",
    )
    pipeline.add_execute(
        "insert into TestTempTable (IntCol) values (9, 'too many values')"
    )
    pipeline.add_fetchall(
        "select IntCol from TestTempTable order by IntCol",
    )
    results = await async_conn.run_pipeline(pipeline, continue_on_error=True)
    expected_value = [(5,)]
    assert results[-3].rows == expected_value
    assert results[-2].error.full_code == "ORA-00913"
    assert results[-1].rows == expected_value


async def test_1217(async_conn):
    "1217 - test insert and update the inserted row"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_execute("insert into TestTempTable (IntCol) values (5)")
    pipeline.add_execute("update TestTempTable set IntCol=25 where IntCol=5")
    pipeline.add_commit()
    pipeline.add_fetchall(
        "select IntCol from TestTempTable order by IntCol",
    )
    results = await async_conn.run_pipeline(pipeline)
    assert results[-1].rows == [(25,)]


async def test_1218(async_conn):
    "1218 - test insert and update inserted rows"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_executemany(
        "insert into TestTempTable (IntCol) values (:1)",
        [(i,) for i in range(100)],
    )
    pipeline.add_execute("update TestTempTable set StringCol1 = 'UPD'")
    pipeline.add_commit()
    pipeline.add_fetchall(
        "select IntCol, StringCol1 from TestTempTable order by IntCol",
    )
    results = await async_conn.run_pipeline(pipeline)
    assert results[-1].rows == [(i, "UPD") for i in range(100)]


async def test_1219(async_conn):
    "1219 - test insert many rows twice"
    values1 = [(i,) for i in range(100)]
    values2 = [(i,) for i in range(200, 205)]
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    sql = "insert into TestTempTable (IntCol) values (:1)"
    pipeline.add_executemany(sql, values1)
    pipeline.add_executemany(sql, values2)
    pipeline.add_commit()
    pipeline.add_fetchall(
        "select IntCol from TestTempTable order by IntCol",
    )
    results = await async_conn.run_pipeline(pipeline)
    assert results[-1].rows == values1 + values2


async def test_1220(async_conn):
    "1220 - test insert and delete value"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_executemany(
        "insert into TestTempTable (IntCol) values (:1)",
        [(i,) for i in range(100)],
    )
    pipeline.add_execute("delete TestTempTable")
    pipeline.add_commit()
    pipeline.add_fetchall(
        "select IntCol from TestTempTable order by IntCol",
    )
    results = await async_conn.run_pipeline(pipeline)
    assert results[-1].rows == []


async def test_1221(async_conn):
    "1221 - test PipelineOp op_type"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_executemany(
        "insert into TestTempTable (IntCol) values (:1)",
        [(1,), (2,)],
    )
    pipeline.add_commit()
    sql = "select IntCol from TestTempTable"
    pipeline.add_fetchone(sql)
    pipeline.add_fetchall(sql)
    pipeline.add_fetchmany(sql)
    pipeline.add_callproc("proc_Test", ("hi", 5, 2))
    pipeline.add_callfunc("func_Test", oracledb.DB_TYPE_NUMBER, ("Yes", 7))
    results = await async_conn.run_pipeline(pipeline)
    expected_values = [
        oracledb.PIPELINE_OP_TYPE_EXECUTE,
        oracledb.PIPELINE_OP_TYPE_EXECUTE_MANY,
        oracledb.PIPELINE_OP_TYPE_COMMIT,
        oracledb.PIPELINE_OP_TYPE_FETCH_ONE,
        oracledb.PIPELINE_OP_TYPE_FETCH_ALL,
        oracledb.PIPELINE_OP_TYPE_FETCH_MANY,
        oracledb.PIPELINE_OP_TYPE_CALL_PROC,
        oracledb.PIPELINE_OP_TYPE_CALL_FUNC,
    ]
    for result, expected_value in zip(results, expected_values):
        assert result.operation.op_type == expected_value


async def test_1222(async_conn):
    "1222 - test Pipeline, PipelineOp and PipelineOpResult repr()"
    pipeline = oracledb.create_pipeline()
    assert repr(pipeline) == "<oracledb.Pipeline with 0 operations>"
    op = pipeline.add_commit()
    assert repr(pipeline) == "<oracledb.Pipeline with 1 operations>"
    assert repr(op) == "<oracledb.PipelineOp of type COMMIT>"
    results = await async_conn.run_pipeline(pipeline)
    assert (
        repr(results[0])
        == "<oracledb.PipelineOpResult for operation of type COMMIT>"
    )


async def test_1223(async_conn):
    "1223 - test getting an error at the beginning of a pipeline"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table NonExistentTable")
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_execute("insert into TestTempTable (IntCol) values (:1)", [5])
    pipeline.add_fetchall(
        "select IntCol from TestTempTable order by IntCol",
    )
    results = await async_conn.run_pipeline(pipeline, continue_on_error=True)
    expected_value = [(5,)]
    assert results[0].error.full_code == "ORA-00942"
    assert results[-1].rows == expected_value


async def test_1224(async_conn):
    "1224 - test getting an error at the end of pipeline"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_execute("insert into TestTempTable (IntCol) values (:1)", [5])
    pipeline.add_fetchall(
        "select IntCol from TestTempTable order by IntCol",
    )
    pipeline.add_execute("insert into TestTempTable (IntCol) values (:1)", [5])
    results = await async_conn.run_pipeline(pipeline, continue_on_error=True)
    expected_value = [(5,)]
    assert results[-2].rows == expected_value
    assert results[-1].error.full_code == "ORA-00001"


async def test_1225(async_conn):
    "1225 - test pipeline with clobs"
    clob = await async_conn.createlob(oracledb.DB_TYPE_CLOB, "Temp CLOB")
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("delete from TestCLOBs")
    pipeline.add_execute(
        "insert into TestCLOBs (IntCol, CLOBCol) values (1, :1)", ["CLOB"]
    )
    pipeline.add_execute(
        "insert into TestCLOBs (IntCol, CLOBCol) values (2, :1)", [clob]
    )
    pipeline.add_fetchall(
        "select CLOBCol from TestCLOBs order by IntCol",
    )
    results = await async_conn.run_pipeline(pipeline)
    rows = results[-1].rows

    assert [await lob.read() for lob, in rows] == ["CLOB", "Temp CLOB"]


async def test_1226(async_conn):
    "1226 - test nested cursors"
    sql = """
        select 'Level 1 String',
            cursor(
                select 'Level 2 String',
                    cursor(
                        select 'Level3 String' from dual
                    ) from dual
            ) from dual
    """
    pipeline = oracledb.create_pipeline()
    pipeline.add_fetchone(sql)
    pipeline.add_fetchone("select user from dual")
    results = await async_conn.run_pipeline(pipeline)
    rows = results[0].rows

    async def transform_row(r):
        return tuple([await transform_fn(v) for v in r])

    async def transform_fn(v):
        if isinstance(v, oracledb.AsyncCursor):
            return [await transform_row(r) async for r in v]
        return v

    rows = [await transform_row(r) async for r in rows[0][1]]
    assert rows == [("Level 2 String", [("Level3 String",)])]


async def test_1227(async_conn):
    "1227 - test executemany with number of iterations"
    num_iterations = 4
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("delete from TestAllTypes")
    pipeline.add_executemany(
        "insert into TestAllTypes (NumberValue) values (1)", num_iterations
    )
    pipeline.add_commit()
    pipeline.add_fetchall(
        "select NumberValue from TestAllTypes order by NumberValue",
    )
    results = await async_conn.run_pipeline(pipeline)
    expected_value = [(1,) for _ in range(num_iterations)]
    assert results[-1].rows == expected_value


async def test_1228(async_conn, async_cursor):
    "1228 - test anonymous PL/SQL"
    var = async_cursor.var(int)
    pipeline = oracledb.create_pipeline()
    sql = "begin :var := :value; end;"
    pipeline.add_execute(sql, [var, 5])
    pipeline.add_execute(sql, [var, 10])
    pipeline.add_execute(sql, [var, 15])
    await async_conn.run_pipeline(pipeline)
    assert var.getvalue() == 15


async def test_1229(async_conn, async_cursor):
    "1229 - test executemany() with PL/SQL"
    values = [31, 6, 21, 17, 43]
    out_bind = async_cursor.var(oracledb.DB_TYPE_NUMBER, arraysize=len(values))
    data = [(i, f"Test {i}", out_bind) for i in values]
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_executemany(
        """
        begin
            insert into TestTempTable (IntCol, StringCol1)
            values (:int_val, :str_val)
            returning IntCol into :out_bind;
        end;
        """,
        data,
    )
    pipeline.add_commit()
    await async_conn.run_pipeline(pipeline)
    assert out_bind.values == values


async def test_1230(disable_fetch_lobs, async_conn):
    "1230 - test fetch_lobs with add_fetchone()"
    clob_value = "CLOB Data 7630"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("delete from TestCLOBs")
    pipeline.add_execute(
        "insert into TestCLOBs (IntCol, CLOBCol) values (1, :1)",
        [clob_value],
    )
    pipeline.add_fetchone("select CLOBCol from TestCLOBs order by IntCol")
    pipeline.add_fetchone(
        "select CLOBCol from TestCLOBs order by IntCol", fetch_lobs=False
    )
    res = await async_conn.run_pipeline(pipeline)
    assert [res[-2].rows] == [[(clob_value,)]]
    assert [res[-1].rows] == [[(clob_value,)]]


async def test_1231(async_conn):
    "1231 - test pipeline with lobs > 32K"
    blob_1_data = b"T" * 33000
    blob_2_data = b"B" * 33000
    blob = await async_conn.createlob(oracledb.DB_TYPE_BLOB, blob_1_data)
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("delete from TestBLOBs")
    pipeline.add_execute(
        "insert into TestBLOBs (IntCol, BLOBCol) values (1, :1)", [blob]
    )
    pipeline.add_execute(
        "insert into TestBLOBs (IntCol, BLOBCol) values (2, :1)",
        [blob_2_data],
    )
    pipeline.add_fetchall(
        "select BLOBCol from TestBLOBs order by IntCol",
    )
    res = await async_conn.run_pipeline(pipeline)
    expected_value = [blob_1_data, blob_2_data]
    fetched_value = [await lob.read() for lob, in res[-1].rows]
    assert fetched_value == expected_value


async def test_1232(async_conn):
    "1232 - test ref cursor"
    ref_cursor1 = async_conn.cursor()
    ref_cursor2 = async_conn.cursor()
    sql = """
            begin
                open :pcursor for
                    select IntCol
                    from TestNumbers
                    order by IntCol;
            end;"""
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute(sql, [ref_cursor1])
    pipeline.add_execute(sql, [ref_cursor2])
    await async_conn.run_pipeline(pipeline)
    assert await ref_cursor1.fetchall() == await ref_cursor2.fetchall()


async def test_1233(async_conn):
    "1233 - test add_callproc() with ref cursor"
    values = [(2, None, None, None), (3, None, None, None)]
    ref_cursor = async_conn.cursor()
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_executemany(
        "insert into TestTempTable values (:1, :2, :3, :4)", values
    )
    pipeline.add_callproc("myrefcursorproc", [ref_cursor])
    await async_conn.run_pipeline(pipeline)
    assert await ref_cursor.fetchall() == values


async def test_1234(async_conn):
    "1234 - test empty pipeline"
    pipeline = oracledb.create_pipeline()
    results = await async_conn.run_pipeline(pipeline)
    assert results == []


async def test_1235(async_conn):
    "1235 - test alter session"
    sql = """
        select value FROM nls_session_parameters
        WHERE parameter = 'NLS_DATE_FORMAT'
    """
    (default_date_format,) = await async_conn.fetchone(sql)
    date = datetime.datetime(2000, 12, 15, 7, 3)
    pipeline = oracledb.create_pipeline()
    pipeline.add_fetchone("select to_char(:1) from dual", [date])
    pipeline.add_execute(
        "alter session set NLS_DATE_FORMAT='YYYY-MM-DD HH24:MI'"
    )
    pipeline.add_fetchone("select to_char(:1) from dual", [date])
    pipeline.add_execute(
        f"alter session set NLS_DATE_FORMAT='{default_date_format}'"
    )
    pipeline.add_fetchone("select to_char(:1) from dual", [date])
    pipeline.add_fetchone(sql)
    results = await async_conn.run_pipeline(pipeline)
    assert results[2].rows == [("2000-12-15 07:03",)]
    assert results[4].rows == results[0].rows
    assert results[-1].rows == [(default_date_format,)]


async def test_1236(async_conn):
    "1236 - test connection inputtypehandler"

    def input_type_handler(cursor, value, num_elements):
        if isinstance(value, str):
            return cursor.var(
                oracledb.DB_TYPE_NUMBER,
                arraysize=num_elements,
                inconverter=lambda x: int(x),
            )

    async_conn.inputtypehandler = input_type_handler
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_execute(
        "insert into TestTempTable (IntCol) values (:1)", ["12"]
    )
    pipeline.add_commit()
    pipeline.add_fetchall("select IntCol from TestTempTable")
    results = await async_conn.run_pipeline(pipeline)
    assert results[-1].rows == [(12,)]


async def test_1237(async_conn, test_env):
    "1237 - test fetch_decimals with add_fetchone()"
    value = 7637
    with test_env.defaults_context_manager("fetch_decimals", True):
        pipeline = oracledb.create_pipeline()
        pipeline.add_execute("truncate table TestTempTable")
        pipeline.add_execute(
            "insert into TestTempTable (IntCol) values (:1)", [value]
        )
        pipeline.add_fetchone("select IntCol from TestTempTable")
        pipeline.add_fetchone(
            "select IntCol from TestTempTable", fetch_decimals=False
        )
    res = await async_conn.run_pipeline(pipeline)
    assert isinstance(res[-2].rows[0][0], decimal.Decimal)
    assert isinstance(res[-1].rows[0][0], int)


async def test_1238(async_conn, test_env):
    "1238 - test oracledb.defaults.arraysize"
    arraysize = 1
    with test_env.defaults_context_manager("arraysize", arraysize):
        data = [(1,), (2,), (3,), (4,)]
        pipeline = oracledb.create_pipeline()
        pipeline.add_execute("truncate table TestTempTable")
        pipeline.add_executemany(
            "insert into TestTempTable (IntCol) values (:value)",
            [{"value": i} for i, in data],
        )
        pipeline.add_commit()
        op = pipeline.add_fetchall(
            "select IntCol from TestTempTable order by IntCol",
        )
        assert op.arraysize == arraysize
        new_arraysize = 4
        oracledb.defaults.arraysize = new_arraysize
        op = pipeline.add_fetchall(
            "select IntCol from TestTempTable order by IntCol",
        )
        assert op.arraysize == new_arraysize
        results = await async_conn.run_pipeline(pipeline)
        assert results[-1].rows == data
        assert results[-2].rows == data


async def test_1239(test_env):
    "1239 - test autocommit"
    conn1 = await test_env.get_connection_async()
    conn1.autocommit = True
    conn2 = await test_env.get_connection_async()

    pipeline1 = oracledb.create_pipeline()
    pipeline1.add_execute("truncate table TestTempTable")
    pipeline1.add_execute("insert into TestTempTable (IntCol) values (1)")

    pipeline2 = oracledb.create_pipeline()
    pipeline2.add_execute("insert into TestTempTable (IntCol) values (2)")
    pipeline2.add_commit()
    pipeline2.add_fetchall("select IntCol from TestTempTable order by IntCol")

    await conn1.run_pipeline(pipeline1)
    results = await conn2.run_pipeline(pipeline2)
    assert results[-1].rows == [(1,), (2,)]


async def test_1240(async_conn, async_cursor):
    "1240 - test DML returning"
    out_value = async_cursor.var(str, arraysize=2)
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_execute("""
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'Value for first row')
        """)
    pipeline.add_execute("""
        insert into TestTempTable (IntCol, StringCol1)
        values (2, 'Value for second row')
        """)
    pipeline.add_execute(
        """
        update TestTempTable set
            StringCol1 = StringCol1 || ' (Modified)'
        returning StringCol1 into :1
        """,
        [out_value],
    )
    pipeline.add_execute("update TestTempTable set StringCol1 = 'Fixed'")
    pipeline.add_commit()
    pipeline.add_fetchall(
        "select IntCol, StringCol1 from TestTempTable order by IntCol"
    )
    results = await async_conn.run_pipeline(pipeline)
    expected_data = [(1, "Fixed"), (2, "Fixed")]
    assert results[-1].rows == expected_data
    assert out_value.getvalue() == [
        "Value for first row (Modified)",
        "Value for second row (Modified)",
    ]


async def test_1241(async_conn):
    "1241 - test the columns attribute on results"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_execute("""
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'Value for first row')
        """)
    pipeline.add_commit()
    pipeline.add_fetchone("select IntCol, StringCol1 from TestTempTable")
    results = await async_conn.run_pipeline(pipeline)
    assert results[0].columns is None
    assert results[1].columns is None
    assert results[2].columns is None
    names = [i.name for i in results[3].columns]
    assert names == ["INTCOL", "STRINGCOL1"]


async def test_1242(async_conn):
    "1242 - test the columns attribute on single operation"
    pipeline = oracledb.create_pipeline()
    pipeline.add_fetchone("select user from dual")
    results = await async_conn.run_pipeline(pipeline)
    names = [i.name for i in results[0].columns]
    assert names == ["USER"]


async def test_1243(async_conn, async_cursor, test_env):
    "1243 - test DML returning with error - pipeline error"
    out_value = async_cursor.var(oracledb.DB_TYPE_RAW)
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'Value for first row')
        returning StringCol1 into :1
        """,
        [out_value],
    )
    pipeline.add_commit()
    pipeline.add_fetchone("select user from dual")
    with test_env.assert_raises_full_code("ORA-01465"):
        await async_conn.run_pipeline(pipeline)
    await async_cursor.execute("select user from dual")
    (fetched_value,) = await async_cursor.fetchone()
    assert fetched_value == test_env.main_user.upper()


async def test_1244(async_conn, async_cursor, test_env):
    "1244 - test DML returning with error - pipeline continue"
    out_value = async_cursor.var(oracledb.DB_TYPE_RAW)
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("truncate table TestTempTable")
    pipeline.add_execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (1, 'Value for first row')
        returning StringCol1 into :1
        """,
        [out_value],
    )
    pipeline.add_commit()
    pipeline.add_fetchone("select user from dual")
    results = await async_conn.run_pipeline(pipeline, continue_on_error=True)
    assert results[1].error.full_code == "ORA-01465"
    user = test_env.main_user.upper()
    assert results[3].rows == [(user,)]
    await async_cursor.execute("select user from dual")
    (fetched_value,) = await async_cursor.fetchone()
    assert fetched_value == test_env.main_user.upper()


async def test_1245(async_conn, test_env):
    "1245 - test fetch_decimals with add_fetchmany()"
    value = 7645
    with test_env.defaults_context_manager("fetch_decimals", True):
        pipeline = oracledb.create_pipeline()
        pipeline.add_execute("truncate table TestTempTable")
        pipeline.add_execute(
            "insert into TestTempTable (IntCol) values (:1)", [value]
        )
        pipeline.add_fetchmany("select IntCol from TestTempTable")
        pipeline.add_fetchmany(
            "select IntCol from TestTempTable", fetch_decimals=False
        )
    res = await async_conn.run_pipeline(pipeline)
    assert isinstance(res[-2].rows[0][0], decimal.Decimal)
    assert isinstance(res[-1].rows[0][0], int)


async def test_1246(async_conn, test_env):
    "1246 - test fetch_decimals with add_fetchall()"
    value = 7646
    with test_env.defaults_context_manager("fetch_decimals", True):
        pipeline = oracledb.create_pipeline()
        pipeline.add_execute("truncate table TestTempTable")
        pipeline.add_execute(
            "insert into TestTempTable (IntCol) values (:1)", [value]
        )
        pipeline.add_fetchall("select IntCol from TestTempTable")
        pipeline.add_fetchall(
            "select IntCol from TestTempTable", fetch_decimals=False
        )
    res = await async_conn.run_pipeline(pipeline)
    assert isinstance(res[-2].rows[0][0], decimal.Decimal)
    assert isinstance(res[-1].rows[0][0], int)


async def test_1247(async_conn, test_env):
    "1247 - test fetch_lobs with add_fetchmany()"
    clob_1_value = "CLOB Data 7647 - One"
    clob_2_value = "CLOB Data 7647 - Two"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("delete from TestCLOBs")
    pipeline.add_execute(
        "insert into TestCLOBs (IntCol, CLOBCol) values (1, :1)",
        [clob_1_value],
    )
    clob = await async_conn.createlob(oracledb.DB_TYPE_CLOB, clob_2_value)
    pipeline.add_execute(
        "insert into TestCLOBs (IntCol, CLOBCol) values (2, :1)", [clob]
    )
    with test_env.defaults_context_manager("fetch_lobs", False):
        pipeline.add_fetchmany(
            "select CLOBCol from TestCLOBs order by IntCol",
        )
    pipeline.add_fetchmany(
        "select CLOBCol from TestCLOBs order by IntCol", fetch_lobs=False
    )

    res = await async_conn.run_pipeline(pipeline)
    assert [res[-1].rows] == [[(clob_1_value,), (clob_2_value,)]]
    assert [res[-2].rows] == [[(clob_1_value,), (clob_2_value,)]]


async def test_1248(async_conn, test_env):
    "1248 - test fetch_lobs with add_fetchall()"
    clob_1_value = "CLOB Data 7648 - One"
    clob_2_value = "CLOB Data 7648 - Two"
    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("delete from TestCLOBs")
    pipeline.add_execute(
        "insert into TestCLOBs (IntCol, CLOBCol) values (1, :1)",
        [clob_1_value],
    )
    clob = await async_conn.createlob(oracledb.DB_TYPE_CLOB, clob_2_value)
    pipeline.add_execute(
        "insert into TestCLOBs (IntCol, CLOBCol) values (2, :1)", [clob]
    )
    with test_env.defaults_context_manager("fetch_lobs", False):
        pipeline.add_fetchall(
            "select CLOBCol from TestCLOBs order by IntCol",
        )
    pipeline.add_fetchall(
        "select CLOBCol from TestCLOBs order by IntCol", fetch_lobs=False
    )

    res = await async_conn.run_pipeline(pipeline)
    assert [res[-1].rows] == [[(clob_1_value,), (clob_2_value,)]]
    assert [res[-2].rows] == [[(clob_1_value,), (clob_2_value,)]]


async def test_1249(async_conn, test_env):
    "1249 - test PL/SQL returning LOB data from a function"
    clob_format = "Sample data for test 7649 - {}"
    num_values = [5, 38, 1549]
    pipeline = oracledb.create_pipeline()
    for num in num_values:
        pipeline.add_callfunc(
            "pkg_TestLOBs.GetLOB",
            return_type=oracledb.DB_TYPE_CLOB,
            parameters=[num, clob_format],
        )
    res = await async_conn.run_pipeline(pipeline)
    for result, num in zip(res, num_values):
        expected_value = clob_format.replace("{}", str(num))
        assert await result.return_value.read() == expected_value
