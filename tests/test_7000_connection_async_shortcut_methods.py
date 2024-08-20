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
7000 - Module for testing async connections shortcut methods
"""

import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    async def test_7000(self):
        "7000 - test execute() and fetchall()"
        await self.conn.execute("truncate table TestTempTable")
        await self.conn.execute(
            "insert into TestTempTable (IntCol) values (:1)", [77]
        )
        await self.conn.execute(
            "insert into TestTempTable (IntCol) values (:val)", dict(val=15)
        )
        await self.conn.commit()

        res = await self.conn.fetchall(
            "select IntCol from TestTempTable order by IntCol"
        )
        self.assertEqual(res, [(15,), (77,)])

    async def test_7001(self):
        "7001 - test executemany()"
        await self.conn.execute("truncate table TestTempTable")
        await self.conn.executemany(
            "insert into TestTempTable (IntCol) values (:1)", [(2,), (3,)]
        )
        await self.conn.executemany(
            "insert into TestTempTable (IntCol) values (:data)",
            [{"data": 4}, {"data": 5}],
        )
        await self.conn.commit()
        res = await self.conn.fetchall(
            "select IntCol from TestTempTable order by IntCol"
        )
        self.assertEqual(res, [(2,), (3,), (4,), (5,)])

    async def test_7002(self):
        "7002 - test fetchall() with arraysize"
        await self.conn.execute("truncate table TestTempTable")
        data = [(1,), (2,), (3,), (4,)]
        await self.conn.executemany(
            "insert into TestTempTable (IntCol) values (:value)",
            [{"value": i} for i, in data],
        )
        await self.conn.commit()

        await self.setup_round_trip_checker()
        res = await self.conn.fetchall(
            "select IntCol from TestTempTable order by IntCol", arraysize=1
        )
        self.assertEqual(res, data)
        await self.assertRoundTrips(5)

        res = await self.conn.fetchall(
            "select IntCol from TestTempTable order by IntCol",
            arraysize=len(data),
        )
        self.assertEqual(res, data)
        await self.assertRoundTrips(2)

    async def test_7003(self):
        "7003 - test fetchall() with rowfactory"
        await self.conn.execute("truncate table TestTempTable")
        await self.conn.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (1, 'test_7003')
            """
        )
        await self.conn.commit()

        column_names = ["INTCOL", "STRINGCOL1"]

        def rowfactory(*row):
            return dict(zip(column_names, row))

        res = await self.conn.fetchall(
            "select IntCol, StringCol1 from TestTempTable",
            rowfactory=rowfactory,
        )
        expected_value = [{"INTCOL": 1, "STRINGCOL1": "test_7003"}]
        self.assertEqual(res, expected_value)

    async def test_7004(self):
        "7004 - test fetchone()"
        await self.conn.execute("truncate table TestTempTable")
        await self.conn.executemany(
            "insert into TestTempTable (IntCol) values (:1)", [(9,), (10,)]
        )
        await self.conn.commit()

        res = await self.conn.fetchone(
            "select IntCol from TestTempTable order by IntCol"
        )
        self.assertEqual(res, (9,))

        res = await self.conn.fetchone("select :1 from dual", [23])
        self.assertEqual(res, (23,))

        res = await self.conn.fetchone("select :val from dual", {"val": 5})
        self.assertEqual(res, (5,))

    async def test_7005(self):
        "7005 - test fetchone() with rowfactory"
        await self.conn.execute("truncate table TestTempTable")
        await self.conn.executemany(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:int, :str)
            """,
            [{"int": 3, "str": "Mac"}, {"int": 4, "str": "Doc"}],
        )
        await self.conn.commit()

        column_names = ["INT", "STRING"]

        def rowfactory(*row):
            return dict(zip(column_names, row))

        res = await self.conn.fetchone(
            "select IntCol, StringCol1 from TestTempTable order by IntCol",
            rowfactory=rowfactory,
        )
        self.assertEqual(res, {"INT": 3, "STRING": "Mac"})

    async def test_7006(self):
        "7006 - test fetchmany()"
        data = [(i,) for i in range(10)]
        await self.conn.execute("truncate table TestTempTable")
        await self.conn.executemany(
            "insert into TestTempTable (IntCol) values (:1)", data
        )
        await self.conn.commit()
        res = await self.conn.fetchmany(
            "select IntCol from TestTempTable order by IntCol"
        )
        self.assertEqual(res, data)

        res = await self.conn.fetchmany("select :1 from dual", [1099])
        self.assertEqual(res, [(1099,)])

        res = await self.conn.fetchmany("select :val from dual", {"val": 366})
        self.assertEqual(res, [(366,)])

    async def test_7007(self):
        "7007 - test fetchmany() with num_rows"
        data = [(i,) for i in range(10)]
        await self.conn.execute("truncate table TestTempTable")
        await self.conn.executemany(
            "insert into TestTempTable (IntCol) values (:1)", data
        )
        num_rows = 7
        res = await self.conn.fetchmany(
            "select IntCol from TestTempTable order by IntCol",
            num_rows=num_rows,
        )
        self.assertEqual(res, data[:num_rows])

    async def test_7008(self):
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
        self.assertEqual(res, expected_value)

        res = await conn.fetchmany(
            "select IntCol, StringCol1 from TestTempTable order by IntCol",
            rowfactory=rowfactory,
            num_rows=1,
        )
        self.assertEqual(res, [{"INT": 4, "STRING": "Monday"}])

    async def test_7009(self):
        "7009 - test callfunc()"
        # parameters
        res = await self.conn.callfunc(
            "func_Test", oracledb.NUMBER, ("Yes", 7)
        )
        self.assertEqual(res, 10)

        # keyword parameters
        kwargs = {"a_String": "Keyword", "a_ExtraAmount": 12}
        res = await self.conn.callfunc(
            "func_Test", oracledb.NUMBER, keyword_parameters=kwargs
        )
        self.assertEqual(res, 19)

        # paramters and keyword parameters
        kwargs = {"a_ExtraAmount": 25}
        res = await self.conn.callfunc(
            "func_Test", oracledb.NUMBER, ["Mixed"], kwargs
        )
        self.assertEqual(res, 30)

    async def test_7010(self):
        "7010 - test callproc() with parameters"
        var = self.cursor.var(oracledb.NUMBER)
        results = await self.conn.callproc("proc_Test", ("hi", 5, var))
        self.assertEqual(results, ["hi", 10, 2.0])

    async def test_7011(self):
        "7011 - test callproc() with keyword_parameters"
        in_out_value = self.cursor.var(oracledb.NUMBER)
        in_out_value.setvalue(0, 7)
        out_value = self.cursor.var(oracledb.NUMBER)
        kwargs = dict(
            a_InValue="Peace", a_InOutValue=in_out_value, a_OutValue=out_value
        )
        results = await self.conn.callproc("proc_Test", [], kwargs)
        self.assertEqual(results, [])
        self.assertEqual(in_out_value.getvalue(), 35)
        self.assertEqual(out_value.getvalue(), 5)

    async def test_7012(self):
        "7012 - test callproc() with parameters and keyword_parameters"
        in_out_value = self.cursor.var(oracledb.NUMBER)
        in_out_value.setvalue(0, 8)
        out_value = self.cursor.var(oracledb.NUMBER)
        kwargs = dict(a_InOutValue=in_out_value, a_OutValue=out_value)
        results = await self.conn.callproc("proc_Test", ["Input_7712"], kwargs)
        self.assertEqual(results, ["Input_7712"])
        self.assertEqual(in_out_value.getvalue(), 80)
        self.assertEqual(out_value.getvalue(), 10)

    async def test_7013(self):
        "7013 - test fetchmany() num_rows with 0 and negative values"
        data = [(i,) for i in range(10)]
        await self.conn.execute("truncate table TestTempTable")
        await self.conn.executemany(
            "insert into TestTempTable (IntCol) values (:1)", data
        )
        await self.conn.commit()
        for num_rows in (0, -1, -10):
            res = await self.conn.fetchmany(
                "select IntCol from TestTempTable",
                num_rows=num_rows,
            )
            self.assertEqual(res, [])

    async def test_7014(self):
        "7014 - test shortcut methods with transaction_in_progress"
        await self.conn.execute("truncate table TestTempTable")
        self.assertFalse(self.conn.transaction_in_progress)
        await self.conn.execute(
            "insert into TestTempTable (IntCol) values (5)",
        )
        self.assertTrue(self.conn.transaction_in_progress)
        await self.conn.commit()
        self.assertFalse(self.conn.transaction_in_progress)


if __name__ == "__main__":
    test_env.run_test_cases()
