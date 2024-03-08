# -----------------------------------------------------------------------------
# Copyright (c) 2023, 2024, Oracle and/or its affiliates.
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
import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    async def test_6100(self):
        "6100 - test executing a statement multiple times (named args)"
        await self.cursor.execute("truncate table TestTempTable")
        rows = [{"value": n} for n in range(250)]
        self.cursor.arraysize = 100
        await self.cursor.executemany(
            "insert into TestTempTable (IntCol) values (:value)",
            rows,
        )
        await self.conn.commit()
        await self.cursor.execute("select count(*) from TestTempTable")
        (count,) = await self.cursor.fetchone()
        self.assertEqual(count, len(rows))

    async def test_6101(self):
        "6101 - test executing a statement multiple times (positional args)"
        await self.cursor.execute("truncate table TestTempTable")
        rows = [[n] for n in range(230)]
        self.cursor.arraysize = 100
        await self.cursor.executemany(
            "insert into TestTempTable (IntCol) values (:1)",
            rows,
        )
        await self.conn.commit()
        await self.cursor.execute("select count(*) from TestTempTable")
        (count,) = await self.cursor.fetchone()
        self.assertEqual(count, len(rows))

    async def test_6102(self):
        "6102 - test executing a statement multiple times (with prepare)"
        await self.cursor.execute("truncate table TestTempTable")
        rows = [[n] for n in range(225)]
        self.cursor.arraysize = 100
        self.cursor.prepare("insert into TestTempTable (IntCol) values (:1)")
        await self.cursor.executemany(None, rows)
        await self.conn.commit()
        await self.cursor.execute("select count(*) from TestTempTable")
        (count,) = await self.cursor.fetchone()
        self.assertEqual(count, len(rows))

    async def test_6103(self):
        "6103 - test executing a statement multiple times (with rebind)"
        await self.cursor.execute("truncate table TestTempTable")
        rows = [[n] for n in range(235)]
        self.cursor.arraysize = 100
        statement = "insert into TestTempTable (IntCol) values (:1)"
        await self.cursor.executemany(statement, rows[:50])
        await self.cursor.executemany(statement, rows[50:])
        await self.conn.commit()
        await self.cursor.execute("select count(*) from TestTempTable")
        (count,) = await self.cursor.fetchone()
        self.assertEqual(count, len(rows))

    async def test_6104(self):
        "6104 - test executing multiple times (with input sizes wrong)"
        cursor = self.conn.cursor()
        cursor.setinputsizes(oracledb.NUMBER)
        data = [[decimal.Decimal("25.8")], [decimal.Decimal("30.0")]]
        await cursor.executemany("declare t number; begin t := :1; end;", data)

    async def test_6105(self):
        "6105 - test executing multiple times (with multiple batches)"
        await self.cursor.execute("truncate table TestTempTable")
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        await self.cursor.executemany(sql, [(1, None), (2, None)])
        await self.cursor.executemany(sql, [(3, None), (4, "Testing")])

    async def test_6106(self):
        "6106 - test executemany() with various numeric types"
        await self.cursor.execute("truncate table TestTempTable")
        data = [
            (1, 5),
            (2, 7.0),
            (3, 6.5),
            (4, 2**65),
            (5, decimal.Decimal("24.5")),
        ]
        await self.cursor.executemany(
            "insert into TestTempTable (IntCol, NumberCol) values (:1, :2)",
            data,
        )
        await self.cursor.execute(
            "select IntCol, NumberCol from TestTempTable order by IntCol"
        )
        self.assertEqual(await self.cursor.fetchall(), data)

    async def test_6107(self):
        "6107 - test executing a statement multiple times (with resize)"
        await self.cursor.execute("truncate table TestTempTable")
        rows = [
            (1, "First"),
            (2, "Second"),
            (3, "Third"),
            (4, "Fourth"),
            (5, "Fifth"),
            (6, "Sixth"),
            (7, "Seventh and the longest one"),
        ]
        await self.cursor.executemany(
            "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)",
            rows,
        )
        await self.cursor.execute(
            "select IntCol, StringCol1 from TestTempTable order by IntCol"
        )
        self.assertEqual(await self.cursor.fetchall(), rows)

    async def test_6108(self):
        "6108 - test executing a statement multiple times (with exception)"
        await self.cursor.execute("truncate table TestTempTable")
        rows = [{"value": n} for n in (1, 2, 3, 2, 5)]
        statement = "insert into TestTempTable (IntCol) values (:value)"
        with self.assertRaisesFullCode("ORA-00001"):
            await self.cursor.executemany(statement, rows)
        self.assertEqual(self.cursor.rowcount, 3)

    async def test_6109(self):
        "6109 - test calling executemany() with invalid parameters"
        sql = """
                insert into TestTempTable (IntCol, StringCol1)
                values (:1, :2)"""
        with self.assertRaisesFullCode("DPY-2004"):
            await self.cursor.executemany(sql, "Not valid parameters")

    async def test_6110(self):
        "6110 - test calling executemany() without any bind parameters"
        num_rows = 5
        await self.cursor.execute("truncate table TestTempTable")
        await self.cursor.executemany(
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
        self.assertEqual(self.cursor.rowcount, 0)
        await self.cursor.execute("select count(*) from TestTempTable")
        (count,) = await self.cursor.fetchone()
        self.assertEqual(count, num_rows)

    async def test_6111(self):
        "6111 - test calling executemany() with binds performed earlier"
        num_rows = 9
        await self.cursor.execute("truncate table TestTempTable")
        var = self.cursor.var(int, arraysize=num_rows)
        self.cursor.setinputsizes(var)
        await self.cursor.executemany(
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
        self.assertEqual(self.cursor.rowcount, 0)
        expected_data = [1, 3, 6, 10, 15, 21, 28, 36, 45]
        self.assertEqual(var.values, expected_data)

    async def test_6112(self):
        "6112 - test executing plsql statements multiple times (with binds)"
        var = self.cursor.var(int, arraysize=5)
        self.cursor.setinputsizes(var)
        data = [[25], [30], [None], [35], [None]]
        exepected_data = [25, 30, None, 35, None]
        await self.cursor.executemany(
            "declare t number; begin t := :1; end;", data
        )
        self.assertEqual(var.values, exepected_data)

    async def test_6113(self):
        "6113 - test executemany with incorrect parameters"
        with self.assertRaisesFullCode("DPY-2004"):
            await self.cursor.executemany("select :1 from dual", [1])

    async def test_6114(self):
        "6114 - test executemany with mixed binds (pos first)"
        rows = [["test"], {"value": 1}]
        with self.assertRaisesFullCode("DPY-2006"):
            await self.cursor.executemany("select :1 from dual", rows)

    async def test_6115(self):
        "6115 - test executemany with mixed binds (name first)"
        rows = [{"value": 1}, ["test"]]
        with self.assertRaisesFullCode("DPY-2006"):
            await self.cursor.executemany("select :value from dual", rows)

    async def test_6116(self):
        "6116 - test executemany() with a pl/sql statement with dml returning"
        num_rows = 5
        await self.cursor.execute("truncate table TestTempTable")
        out_var = self.cursor.var(oracledb.NUMBER, arraysize=5)
        self.cursor.setinputsizes(out_var)
        await self.cursor.executemany(
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
        self.assertEqual(out_var.values, [1, 2, 3, 4, 5])

    async def test_6117(self):
        "6117 - test executemany() with pl/sql in binds and out binds"
        await self.cursor.execute("truncate table TestTempTable")
        values = [5, 8, 17, 24, 6]
        data = [(i, f"Test {i}") for i in values]
        out_bind = self.cursor.var(oracledb.NUMBER, arraysize=5)
        self.cursor.setinputsizes(None, None, out_bind)
        await self.cursor.executemany(
            """
            begin
                insert into TestTempTable (IntCol, StringCol1)
                values (:int_val, :str_val)
                returning IntCol into :out_bind;
            end;
            """,
            data,
        )
        self.assertEqual(out_bind.values, values)

    async def test_6118(self):
        "6118 - test executemany() with pl/sql outbinds"
        await self.cursor.execute("truncate table TestTempTable")
        out_bind = self.cursor.var(oracledb.NUMBER, arraysize=5)
        self.cursor.setinputsizes(out_bind)
        await self.cursor.executemany("begin :out_var := 5; end;", 5)
        self.assertEqual(out_bind.values, [5, 5, 5, 5, 5])

    async def test_6119(self):
        "6119 - test re-executemany() with pl/sql in binds and out binds"
        values = [5, 8, 17, 24, 6]
        data = [(i, f"Test {i}") for i in values]
        for i in range(2):
            await self.cursor.execute("truncate table TestTempTable")
            out_bind = self.cursor.var(oracledb.NUMBER, arraysize=5)
            self.cursor.setinputsizes(None, None, out_bind)
            await self.cursor.executemany(
                """
                begin
                    insert into TestTempTable (IntCol, StringCol1)
                    values (:int_val, :str_val)
                    returning IntCol into :out_bind;
                end;
                """,
                data,
            )
            self.assertEqual(out_bind.values, values)

    async def test_6120(self):
        "6120 - test PL/SQL statement with single row bind"
        value = 4020
        var = self.cursor.var(int)
        await self.cursor.executemany("begin :1 := :2; end;", [[var, value]])
        self.assertEqual(var.values, [value])

    async def test_6121(self):
        "6121 - test deferral of type assignment"
        await self.cursor.execute("truncate table TestTempTable")
        data = [(1, None), (2, 25)]
        await self.cursor.executemany(
            """
            insert into TestTempTable
            (IntCol, NumberCol)
            values (:1, :2)
            """,
            data,
        )
        await self.conn.commit()
        await self.cursor.execute(
            """
            select IntCol, NumberCol
            from TestTempTable
            order by IntCol
            """
        )
        self.assertEqual(await self.cursor.fetchall(), data)

    async def test_6122(self):
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
            out_binds.append(
                self.cursor.var(int, arraysize=len(all_bind_values))
            )
            for j, bind_values in enumerate(all_bind_values):
                bind_values.extend(
                    [out_binds[-1], n * 1 + j, n * 2 + j, n * 3 + j]
                )
        lf = "\n"
        sql = f"begin{lf}{lf.join(parts)}{lf}end;"
        await self.cursor.executemany(sql, all_bind_values)
        init_val = 6
        for var in out_binds:
            expected_values = [
                init_val,
                init_val + 3,
                init_val + 6,
                init_val + 9,
                init_val + 12,
            ]
            self.assertEqual(var.values, expected_values)
            init_val += 6

    async def test_6123(self):
        "6123 - test executing no statement"
        cursor = self.conn.cursor()
        with self.assertRaisesFullCode("DPY-2001"):
            await cursor.executemany(None, [1, 2])


if __name__ == "__main__":
    test_env.run_test_cases()
