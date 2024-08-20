# -----------------------------------------------------------------------------
# Copyright (c) 2024, Oracle and/or its affiliates.
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
7600 - Module for testing async pipelining.
"""

import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):

    async def test_7600(self):
        "7600 - test execute() and fetchall()."
        pipeline = oracledb.create_pipeline()
        pipeline.add_execute("truncate table TestTempTable")
        pipeline.add_execute(
            "insert into TestTempTable (IntCol) values (:1)", [1]
        )
        pipeline.add_execute(
            "insert into TestTempTable (IntCol) values (:val)", dict(val=2)
        )
        pipeline.add_commit()
        pipeline.add_fetchall(
            "select IntCol from TestTempTable order by IntCol"
        )
        results = await self.conn.run_pipeline(pipeline)
        self.assertEqual(results[-1].rows, [(1,), (2,)])

    async def test_7601(self):
        "7601 - test executemany()"
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
        pipeline.add_fetchall(
            "select IntCol from TestTempTable order by IntCol"
        )
        results = await self.conn.run_pipeline(pipeline)
        self.assertEqual(results[-1].rows, [(2,), (3,), (4,), (5,)])

    async def test_7602(self):
        "7602 - test fetchall() with arraysize"
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
        self.assertEqual(op.arraysize, arraysize)
        arraysize = len(data)
        op = pipeline.add_fetchall(
            "select IntCol from TestTempTable order by IntCol",
            arraysize=arraysize,
        )
        self.assertEqual(op.arraysize, arraysize)
        results = await self.conn.run_pipeline(pipeline)
        self.assertEqual(results[-1].rows, data)
        self.assertEqual(results[-2].rows, data)

    async def test_7603(self):
        "7603 - test fetchall() with rowfactory"
        pipeline = oracledb.create_pipeline()
        pipeline.add_execute("truncate table TestTempTable")
        pipeline.add_execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (1, 'test_7003')
            """
        )
        pipeline.add_commit()

        def rowfactory(*row):
            column_names = ["INTCOL", "STRINGCOL1"]
            return dict(zip(column_names, row))

        pipeline.add_fetchall(
            "select IntCol, StringCol1 from TestTempTable",
            rowfactory=rowfactory,
        )
        results = await self.conn.run_pipeline(pipeline)
        expected_value = [{"INTCOL": 1, "STRINGCOL1": "test_7003"}]
        self.assertEqual(results[-1].rows, expected_value)

    async def test_7604(self):
        "7604 - test fetchone()"
        pipeline = oracledb.create_pipeline()
        pipeline.add_execute("truncate table TestTempTable")
        pipeline.add_executemany(
            "insert into TestTempTable (IntCol) values (:1)", [(9,), (10,)]
        )
        pipeline.add_commit()
        pipeline.add_fetchone(
            "select IntCol from TestTempTable order by IntCol"
        )
        pipeline.add_fetchone("select :1 from dual", [23])
        pipeline.add_fetchone("select :val from dual", {"val": 5})
        results = await self.conn.run_pipeline(pipeline)
        self.assertEqual(results[-3].rows, [(9,)])
        self.assertEqual(results[-2].rows, [(23,)])
        self.assertEqual(results[-1].rows, [(5,)])

    async def test_7605(self):
        "7605 - test fetchone() with rowfactory"
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
        self.assertEqual(op.rowfactory, rowfactory)
        results = await self.conn.run_pipeline(pipeline)
        self.assertEqual(results[-1].rows, [{"INT": 3, "STRING": "Mac"}])

    async def test_7606(self):
        "7606 - test fetchmany()"
        data = [(i,) for i in range(10)]
        pipeline = oracledb.create_pipeline()
        pipeline.add_execute("truncate table TestTempTable")
        pipeline.add_executemany(
            "insert into TestTempTable (IntCol) values (:1)", data
        )
        pipeline.add_commit()
        pipeline.add_fetchmany(
            "select IntCol from TestTempTable order by IntCol"
        )
        pipeline.add_fetchmany("select :1 from dual", [1099])
        pipeline.add_fetchmany("select :val from dual", {"val": 366})
        results = await self.conn.run_pipeline(pipeline)
        self.assertEqual(results[-3].rows, data)
        self.assertEqual(results[-2].rows, [(1099,)])
        self.assertEqual(results[-1].rows, [(366,)])

    async def test_7607(self):
        "7607 - test fetchmany() with num_rows"
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
        self.assertEqual(op.num_rows, num_rows)
        results = await self.conn.run_pipeline(pipeline)
        self.assertEqual(results[-1].rows, data[:num_rows])

    async def test_7608(self):
        "7608 - test fetchmany() with rowfactory and num_rows"
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
        self.assertEqual(op.num_rows, num_rows)
        self.assertEqual(op.rowfactory, rowfactory)
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
        self.assertEqual(op.num_rows, num_rows)
        self.assertEqual(op.rowfactory, rowfactory)
        results = await self.conn.run_pipeline(pipeline)
        self.assertEqual(results[-2].rows, expected_value)
        self.assertEqual(results[-1].rows, [{"INT": 4, "STRING": "Monday"}])

    async def test_7609(self):
        "7609 - test callfunc(), return_value and return_type"
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
        self.assertEqual(op.name, func_name)
        self.assertEqual(op.return_type, oracledb.DB_TYPE_NUMBER)
        self.assertIsNone(op.statement)
        results = await self.conn.run_pipeline(pipeline)
        self.assertEqual(results[0].return_value, 10)
        self.assertEqual(results[1].return_value, 19)
        self.assertEqual(results[2].return_value, 30)

    async def test_7610(self):
        "7610 - test callproc() with parameters"
        pipeline = oracledb.create_pipeline()
        var = self.cursor.var(oracledb.DB_TYPE_NUMBER)
        proc_name = "proc_Test"
        params = ("hi", 5, var)
        op = pipeline.add_callproc(proc_name, params)
        self.assertEqual(op.name, proc_name)
        self.assertEqual(op.parameters, params)
        self.assertIsNone(op.keyword_parameters)
        self.assertIsNone(op.statement)
        self.assertEqual(op.arraysize, 0)
        self.assertEqual(op.num_rows, 0)
        await self.conn.run_pipeline(pipeline)
        self.assertEqual(var.getvalue(), 2)

    async def test_7611(self):
        "7611 - test callproc() with keyword_parameters"
        in_out_value = self.cursor.var(oracledb.DB_TYPE_NUMBER)
        in_out_value.setvalue(0, 7)
        out_value = self.cursor.var(oracledb.DB_TYPE_NUMBER)
        params = []
        kwargs = dict(
            a_InValue="Peace", a_InOutValue=in_out_value, a_OutValue=out_value
        )
        pipeline = oracledb.create_pipeline()
        op = pipeline.add_callproc("proc_Test", params, kwargs)
        self.assertEqual(op.parameters, params)
        self.assertEqual(op.keyword_parameters, kwargs)
        await self.conn.run_pipeline(pipeline)
        self.assertEqual(in_out_value.getvalue(), 35)
        self.assertEqual(out_value.getvalue(), 5)

    async def test_7612(self):
        "7612 - test callproc() with parameters and keyword_parameters"
        in_out_value = self.cursor.var(oracledb.DB_TYPE_NUMBER)
        in_out_value.setvalue(0, 8)
        out_value = self.cursor.var(oracledb.DB_TYPE_NUMBER)
        params = ["Input_7612"]
        kwargs = dict(a_InOutValue=in_out_value, a_OutValue=out_value)
        pipeline = oracledb.create_pipeline()
        op = pipeline.add_callproc("proc_Test", params, kwargs)
        self.assertEqual(op.parameters, params)
        self.assertEqual(op.keyword_parameters, kwargs)
        await self.conn.run_pipeline(pipeline)
        self.assertEqual(in_out_value.getvalue(), 80)
        self.assertEqual(out_value.getvalue(), 10)

    async def test_7613(self):
        "7613 - test fetchmany() num_rows with 0 and negative values"
        data = [(i,) for i in range(10)]
        pipeline = oracledb.create_pipeline()
        pipeline.add_execute("truncate table TestTempTable")
        pipeline.add_executemany(
            "insert into TestTempTable (IntCol) values (:1)", data
        )
        sql = "select IntCol from TestTempTable"
        op = pipeline.add_fetchmany(sql, num_rows=0)
        self.assertEqual(op.statement, sql)
        with self.assertRaises(OverflowError):
            pipeline.add_fetchmany(sql, num_rows=-1)
        with self.assertRaises(OverflowError):
            pipeline.add_fetchmany(sql, num_rows=-10)
        results = await self.conn.run_pipeline(pipeline)
        self.assertEqual(results[-1].rows, [])

    async def test_7614(self):
        "7614 - test add_commit with transaction_in_progress"
        self.assertFalse(self.conn.transaction_in_progress)
        pipeline = oracledb.create_pipeline()
        pipeline.add_execute("truncate table TestTempTable")
        pipeline.add_execute(
            "insert into TestTempTable (IntCol) values (5)",
        )
        await self.conn.run_pipeline(pipeline)
        self.assertTrue(self.conn.transaction_in_progress)
        pipeline = oracledb.create_pipeline()
        pipeline.add_commit()
        await self.conn.run_pipeline(pipeline)
        self.assertFalse(self.conn.transaction_in_progress)

    async def test_7615(self):
        "7615 - test getting an error in the middle of pipeline"
        pipeline = oracledb.create_pipeline()
        pipeline.add_execute("truncate table TestTempTable")
        pipeline.add_execute(
            "insert into TestTempTable (IntCol) values (:1)", [5]
        )
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
        results = await self.conn.run_pipeline(
            pipeline, continue_on_error=True
        )
        expected_value = [(5,)]
        self.assertEqual(results[-3].rows, expected_value)
        self.assertEqual(results[-2].error.full_code, "ORA-00913")
        self.assertEqual(results[-1].rows, expected_value)

    async def test_7617(self):
        "7617 - test insert and update the inserted row"
        pipeline = oracledb.create_pipeline()
        pipeline.add_execute("truncate table TestTempTable")
        pipeline.add_execute("insert into TestTempTable (IntCol) values (5)")
        pipeline.add_execute(
            "update TestTempTable set IntCol=25 where IntCol=5"
        )
        pipeline.add_commit()
        pipeline.add_fetchall(
            "select IntCol from TestTempTable order by IntCol",
        )
        results = await self.conn.run_pipeline(pipeline)
        self.assertEqual(results[-1].rows, [(25,)])

    async def test_7618(self):
        "7618 - test insert and update inserted rows"
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
        results = await self.conn.run_pipeline(pipeline)
        self.assertEqual(results[-1].rows, [(i, "UPD") for i in range(100)])

    async def test_7619(self):
        "7619 - test insert many rows twice"
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
        results = await self.conn.run_pipeline(pipeline)
        self.assertEqual(results[-1].rows, values1 + values2)

    async def test_7620(self):
        "7620 - test insert and delete value"
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
        results = await self.conn.run_pipeline(pipeline)
        self.assertEqual(results[-1].rows, [])

    async def test_7621(self):
        "7621 - test PipelineOp op_type"
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
        results = await self.conn.run_pipeline(pipeline)
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
            self.assertEqual(result.operation.op_type, expected_value)

    async def test_7622(self):
        "7622 - test Pipeline, PipelineOp and PipelineOpResult repr()"
        pipeline = oracledb.create_pipeline()
        self.assertEqual(
            repr(pipeline), "<oracledb.Pipeline with 0 operations>"
        )
        op = pipeline.add_commit()
        self.assertEqual(
            repr(pipeline), "<oracledb.Pipeline with 1 operations>"
        )
        self.assertEqual(repr(op), "<oracledb.PipelineOp of type COMMIT>")
        results = await self.conn.run_pipeline(pipeline)
        self.assertEqual(
            repr(results[0]),
            "<oracledb.PipelineOpResult for operation of type COMMIT>",
        )

    async def test_7623(self):
        "7623 - test getting an error at the beginning of a pipeline"
        pipeline = oracledb.create_pipeline()
        pipeline.add_execute("truncate table NonExistentTable")
        pipeline.add_execute("truncate table TestTempTable")
        pipeline.add_execute(
            "insert into TestTempTable (IntCol) values (:1)", [5]
        )
        pipeline.add_fetchall(
            "select IntCol from TestTempTable order by IntCol",
        )
        results = await self.conn.run_pipeline(
            pipeline, continue_on_error=True
        )
        expected_value = [(5,)]
        self.assertEqual(results[0].error.full_code, "ORA-00942")
        self.assertEqual(results[-1].rows, expected_value)

    async def test_7624(self):
        "7624 - test getting an error at the end of pipeline"
        pipeline = oracledb.create_pipeline()
        pipeline.add_execute("truncate table TestTempTable")
        pipeline.add_execute(
            "insert into TestTempTable (IntCol) values (:1)", [5]
        )
        pipeline.add_fetchall(
            "select IntCol from TestTempTable order by IntCol",
        )
        pipeline.add_execute(
            "insert into TestTempTable (IntCol) values (:1)", [5]
        )
        results = await self.conn.run_pipeline(
            pipeline, continue_on_error=True
        )
        expected_value = [(5,)]
        self.assertEqual(results[-2].rows, expected_value)
        self.assertEqual(results[-1].error.full_code, "ORA-00001")

    async def test_7625(self):
        "7625 - test pipeline with clobs"
        clob = await self.conn.createlob(oracledb.DB_TYPE_CLOB, "Temp CLOB")
        pipeline = oracledb.create_pipeline()
        pipeline.add_execute("truncate table TestCLOBs")
        pipeline.add_execute(
            "insert into TestCLOBs (IntCol, CLOBCol) values (1, :1)", ["CLOB"]
        )
        pipeline.add_execute(
            "insert into TestCLOBs (IntCol, CLOBCol) values (2, :1)", [clob]
        )
        pipeline.add_fetchall(
            "select CLOBCol from TestCLOBs order by IntCol",
        )
        results = await self.conn.run_pipeline(pipeline)
        rows = results[-1].rows

        self.assertEqual(
            [await lob.read() for lob, in rows], ["CLOB", "Temp CLOB"]
        )

    async def test_7626(self):
        "7626 - test nested cursors"
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
        results = await self.conn.run_pipeline(pipeline)
        rows = results[0].rows

        async def transform_row(r):
            return tuple([await transform_fn(v) for v in r])

        async def transform_fn(v):
            if isinstance(v, oracledb.AsyncCursor):
                return [await transform_row(r) async for r in v]
            return v

        rows = [await transform_row(r) async for r in rows[0][1]]
        self.assertEqual(rows, [("Level 2 String", [("Level3 String",)])])

    async def test_7627(self):
        "7627 - test executemany with number of iterations"
        num_iterations = 4
        pipeline = oracledb.create_pipeline()
        pipeline.add_execute("truncate table TestAllTypes")
        pipeline.add_executemany(
            "insert into TestAllTypes (NumberValue) values (1)", num_iterations
        )
        pipeline.add_commit()
        pipeline.add_fetchall(
            "select NumberValue from TestAllTypes order by NumberValue",
        )
        results = await self.conn.run_pipeline(pipeline)
        expected_value = [(1,) for _ in range(num_iterations)]
        self.assertEqual(results[-1].rows, expected_value)

    async def test_7628(self):
        "7628 - test anonymous PL/SQL"
        var = self.cursor.var(int)
        pipeline = oracledb.create_pipeline()
        sql = "begin :var := :value; end;"
        pipeline.add_execute(sql, [var, 5])
        pipeline.add_execute(sql, [var, 10])
        await self.conn.run_pipeline(pipeline)
        self.assertEqual(var.getvalue(), 10)

    async def test_7629(self):
        "7629 - test executemany() with PL/SQL"
        values = [31, 6, 21, 17, 43]
        out_bind = self.cursor.var(
            oracledb.DB_TYPE_NUMBER, arraysize=len(values)
        )
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
        await self.conn.run_pipeline(pipeline)
        self.assertEqual(out_bind.values, values)


if __name__ == "__main__":
    test_env.run_test_cases()
