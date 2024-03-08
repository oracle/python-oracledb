# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
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
4000 - Module for testing the cursor executemany() method
"""

import decimal

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    def test_4000(self):
        "4000 - test executing a statement multiple times (named args)"
        self.cursor.execute("truncate table TestTempTable")
        rows = [{"value": n} for n in range(250)]
        self.cursor.arraysize = 100
        self.cursor.executemany(
            "insert into TestTempTable (IntCol) values (:value)",
            rows,
        )
        self.conn.commit()
        self.cursor.execute("select count(*) from TestTempTable")
        (count,) = self.cursor.fetchone()
        self.assertEqual(count, len(rows))

    def test_4001(self):
        "4001 - test executing a statement multiple times (positional args)"
        self.cursor.execute("truncate table TestTempTable")
        rows = [[n] for n in range(230)]
        self.cursor.arraysize = 100
        self.cursor.executemany(
            "insert into TestTempTable (IntCol) values (:1)",
            rows,
        )
        self.conn.commit()
        self.cursor.execute("select count(*) from TestTempTable")
        (count,) = self.cursor.fetchone()
        self.assertEqual(count, len(rows))

    def test_4002(self):
        "4002 - test executing a statement multiple times (with prepare)"
        self.cursor.execute("truncate table TestTempTable")
        rows = [[n] for n in range(225)]
        self.cursor.arraysize = 100
        self.cursor.prepare("insert into TestTempTable (IntCol) values (:1)")
        self.cursor.executemany(None, rows)
        self.conn.commit()
        self.cursor.execute("select count(*) from TestTempTable")
        (count,) = self.cursor.fetchone()
        self.assertEqual(count, len(rows))

    def test_4003(self):
        "4003 - test executing a statement multiple times (with rebind)"
        self.cursor.execute("truncate table TestTempTable")
        rows = [[n] for n in range(235)]
        self.cursor.arraysize = 100
        statement = "insert into TestTempTable (IntCol) values (:1)"
        self.cursor.executemany(statement, rows[:50])
        self.cursor.executemany(statement, rows[50:])
        self.conn.commit()
        self.cursor.execute("select count(*) from TestTempTable")
        (count,) = self.cursor.fetchone()
        self.assertEqual(count, len(rows))

    def test_4004(self):
        "4004 - test executing multiple times (with input sizes wrong)"
        cursor = self.conn.cursor()
        cursor.setinputsizes(oracledb.NUMBER)
        data = [[decimal.Decimal("25.8")], [decimal.Decimal("30.0")]]
        cursor.executemany("declare t number; begin t := :1; end;", data)

    def test_4005(self):
        "4005 - test executing multiple times (with multiple batches)"
        self.cursor.execute("truncate table TestTempTable")
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        self.cursor.executemany(sql, [(1, None), (2, None)])
        self.cursor.executemany(sql, [(3, None), (4, "Testing")])

    def test_4006(self):
        "4006 - test executemany() with various numeric types"
        self.cursor.execute("truncate table TestTempTable")
        data = [
            (1, 5),
            (2, 7.0),
            (3, 6.5),
            (4, 2**65),
            (5, decimal.Decimal("24.5")),
        ]
        self.cursor.executemany(
            "insert into TestTempTable (IntCol, NumberCol) values (:1, :2)",
            data,
        )
        self.cursor.execute(
            "select IntCol, NumberCol from TestTempTable order by IntCol"
        )
        self.assertEqual(self.cursor.fetchall(), data)

    def test_4007(self):
        "4007 - test executing a statement multiple times (with resize)"
        self.cursor.execute("truncate table TestTempTable")
        rows = [
            (1, "First"),
            (2, "Second"),
            (3, "Third"),
            (4, "Fourth"),
            (5, "Fifth"),
            (6, "Sixth"),
            (7, "Seventh and the longest one"),
        ]
        self.cursor.executemany(
            "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)",
            rows,
        )
        self.cursor.execute(
            "select IntCol, StringCol1 from TestTempTable order by IntCol"
        )
        self.assertEqual(self.cursor.fetchall(), rows)

    def test_4008(self):
        "4008 - test executing a statement multiple times (with exception)"
        self.cursor.execute("truncate table TestTempTable")
        rows = [{"value": n} for n in (1, 2, 3, 2, 5)]
        statement = "insert into TestTempTable (IntCol) values (:value)"
        with self.assertRaisesFullCode("ORA-00001"):
            self.cursor.executemany(statement, rows)
        self.assertEqual(self.cursor.rowcount, 3)

    def test_4009(self):
        "4009 - test calling executemany() with invalid parameters"
        sql = """
                insert into TestTempTable (IntCol, StringCol1)
                values (:1, :2)"""
        with self.assertRaisesFullCode("DPY-2004"):
            self.cursor.executemany(sql, "These are not valid parameters")

    def test_4010(self):
        "4010 - test calling executemany() without any bind parameters"
        num_rows = 5
        self.cursor.execute("truncate table TestTempTable")
        self.cursor.executemany(
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
        self.cursor.execute("select count(*) from TestTempTable")
        (count,) = self.cursor.fetchone()
        self.assertEqual(count, num_rows)

    def test_4011(self):
        "4011 - test calling executemany() with binds performed earlier"
        num_rows = 9
        self.cursor.execute("truncate table TestTempTable")
        var = self.cursor.var(int, arraysize=num_rows)
        self.cursor.setinputsizes(var)
        self.cursor.executemany(
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

    def test_4012(self):
        "4012 - test executing plsql statements multiple times (with binds)"
        var = self.cursor.var(int, arraysize=5)
        self.cursor.setinputsizes(var)
        data = [[25], [30], [None], [35], [None]]
        exepected_data = [25, 30, None, 35, None]
        self.cursor.executemany("declare t number; begin t := :1; end;", data)
        self.assertEqual(var.values, exepected_data)

    def test_4013(self):
        "4013 - test executemany with incorrect parameters"
        with self.assertRaisesFullCode("DPY-2004"):
            self.cursor.executemany("select :1 from dual", [1])

    def test_4014(self):
        "4014 - test executemany with mixed binds (pos first)"
        rows = [["test"], {"value": 1}]
        with self.assertRaisesFullCode("DPY-2006"):
            self.cursor.executemany("select :1 from dual", rows)

    def test_4015(self):
        "4015 - test executemany with mixed binds (name first)"
        rows = [{"value": 1}, ["test"]]
        with self.assertRaisesFullCode("DPY-2006"):
            self.cursor.executemany("select :value from dual", rows)

    def test_4016(self):
        "4016 - test executemany() with a pl/sql statement with dml returning"
        num_rows = 5
        self.cursor.execute("truncate table TestTempTable")
        out_var = self.cursor.var(oracledb.NUMBER, arraysize=5)
        self.cursor.setinputsizes(out_var)
        self.cursor.executemany(
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

    def test_4017(self):
        "4017 - test executemany() with pl/sql in binds and out binds"
        self.cursor.execute("truncate table TestTempTable")
        values = [5, 8, 17, 24, 6]
        data = [(i, f"Test {i}") for i in values]
        out_bind = self.cursor.var(oracledb.NUMBER, arraysize=5)
        self.cursor.setinputsizes(None, None, out_bind)
        self.cursor.executemany(
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

    def test_4018(self):
        "4018 - test executemany() with pl/sql outbinds"
        self.cursor.execute("truncate table TestTempTable")
        out_bind = self.cursor.var(oracledb.NUMBER, arraysize=5)
        self.cursor.setinputsizes(out_bind)
        self.cursor.executemany("begin :out_var := 5; end;", 5)
        self.assertEqual(out_bind.values, [5, 5, 5, 5, 5])

    def test_4019(self):
        "4019 - test re-executemany() with pl/sql in binds and out binds"
        values = [5, 8, 17, 24, 6]
        data = [(i, f"Test {i}") for i in values]
        for i in range(2):
            self.cursor.execute("truncate table TestTempTable")
            out_bind = self.cursor.var(oracledb.NUMBER, arraysize=len(values))
            self.cursor.setinputsizes(None, None, out_bind)
            self.cursor.executemany(
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

    def test_4020(self):
        "4020 - test PL/SQL statement with single row bind"
        value = 4020
        var = self.cursor.var(int)
        self.cursor.executemany("begin :1 := :2; end;", [[var, value]])
        self.assertEqual(var.values, [value])

    def test_4021(self):
        "4021 - test deferral of type assignment"
        self.cursor.execute("truncate table TestTempTable")
        data = [(1, None), (2, 25)]
        self.cursor.executemany(
            """
            insert into TestTempTable
            (IntCol, NumberCol)
            values (:1, :2)
            """,
            data,
        )
        self.conn.commit()
        self.cursor.execute(
            """
            select IntCol, NumberCol
            from TestTempTable
            order by IntCol
            """
        )
        self.assertEqual(self.cursor.fetchall(), data)

    def test_4022(self):
        "4022 - test PL/SQL with a lerge number of binds"
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
        self.cursor.executemany(sql, all_bind_values)
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

    def test_4023(self):
        "3901 - test executing a None statement"
        cursor = self.conn.cursor()
        with self.assertRaisesFullCode("DPY-2001"):
            cursor.executemany(None, [(1,), (2,)])

    def test_4024(self):
        """
        4024 - test executemany with number of iterations
        (previous bind values)
        """
        data = [(2,), (3,), (4,)]
        for num_iterations in range(1, len(data) + 1):
            self.cursor.execute("truncate table TestLongs")
            self.cursor.executemany(
                "insert into TestLongs (IntCol) values (:1)", data
            )
            self.cursor.executemany(None, num_iterations)
            self.cursor.execute("select IntCol from TestLongs")
            expected_value = data + data[:num_iterations]
            self.assertEqual(self.cursor.fetchall(), expected_value)

    def test_4025(self):
        "4025 - test executemany with empty lists and number of iterations"
        values = [[] for _ in range(5)]
        for num_iterations in (4, 6):
            self.cursor.execute("truncate table TestLongs")
            self.cursor.executemany(
                "insert into TestLongs (IntCol) values (67)",
                values,
            )
            self.cursor.executemany(None, num_iterations)
            self.cursor.execute("select IntCol from TestLongs")
            expected_value = [(67,)] * (len(values) + num_iterations)
            self.assertEqual(self.cursor.fetchall(), expected_value)

    def test_4026(self):
        "4026 - test executemany error offset returned correctly"
        data = [(i,) for i in range(1, 11)]
        with self.assertRaises(oracledb.Error) as cm:
            self.cursor.executemany(
                """
                declare
                    t_Value     number;
                begin
                    t_Value := 10 / (4 - :1);
                end;
                """,
                data,
            )
        (error_obj,) = cm.exception.args
        self.assertEqual(error_obj.offset, 3)

    def test_4027(self):
        "4027 - test executemany with number of iterations too small"
        data = [[1], [2], [3]]
        self.cursor.execute("truncate table TestTempTable")
        self.cursor.executemany(
            """
            declare
                t_Value         number;
            begin
                t_Value := :1;
            end;
            """,
            data,
        )
        self.cursor.executemany(None, 2)
        with self.assertRaisesFullCode("DPY-2016"):
            self.cursor.executemany(None, 4)


if __name__ == "__main__":
    test_env.run_test_cases()
