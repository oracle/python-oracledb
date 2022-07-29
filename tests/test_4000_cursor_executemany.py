#------------------------------------------------------------------------------
# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
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
#------------------------------------------------------------------------------

"""
4000 - Module for testing the cursor executemany() method
"""

import decimal

import oracledb
import test_env

class TestCase(test_env.BaseTestCase):

    def test_4000_executemany_by_name(self):
        "4000 - test executing a statement multiple times (named args)"
        self.cursor.execute("truncate table TestTempTable")
        rows = [{"value": n} for n in range(250)]
        self.cursor.arraysize = 100
        statement = "insert into TestTempTable (IntCol) values (:value)"
        self.cursor.executemany(statement, rows)
        self.connection.commit()
        self.cursor.execute("select count(*) from TestTempTable")
        count, = self.cursor.fetchone()
        self.assertEqual(count, len(rows))

    def test_4001_executemany_by_position(self):
        "4001 - test executing a statement multiple times (positional args)"
        self.cursor.execute("truncate table TestTempTable")
        rows = [[n] for n in range(230)]
        self.cursor.arraysize = 100
        statement = "insert into TestTempTable (IntCol) values (:1)"
        self.cursor.executemany(statement, rows)
        self.connection.commit()
        self.cursor.execute("select count(*) from TestTempTable")
        count, = self.cursor.fetchone()
        self.assertEqual(count, len(rows))

    def test_4002_executemany_with_prepare(self):
        "4002 - test executing a statement multiple times (with prepare)"
        self.cursor.execute("truncate table TestTempTable")
        rows = [[n] for n in range(225)]
        self.cursor.arraysize = 100
        statement = "insert into TestTempTable (IntCol) values (:1)"
        self.cursor.prepare(statement)
        self.cursor.executemany(None, rows)
        self.connection.commit()
        self.cursor.execute("select count(*) from TestTempTable")
        count, = self.cursor.fetchone()
        self.assertEqual(count, len(rows))

    def test_4003_executemany_with_rebind(self):
        "4003 - test executing a statement multiple times (with rebind)"
        self.cursor.execute("truncate table TestTempTable")
        rows = [[n] for n in range(235)]
        self.cursor.arraysize = 100
        statement = "insert into TestTempTable (IntCol) values (:1)"
        self.cursor.executemany(statement, rows[:50])
        self.cursor.executemany(statement, rows[50:])
        self.connection.commit()
        self.cursor.execute("select count(*) from TestTempTable")
        count, = self.cursor.fetchone()
        self.assertEqual(count, len(rows))

    def test_4004_executemany_with_input_sizes_wrong(self):
        "4004 - test executing multiple times (with input sizes wrong)"
        cursor = self.connection.cursor()
        cursor.setinputsizes(oracledb.NUMBER)
        data = [[decimal.Decimal("25.8")], [decimal.Decimal("30.0")]]
        cursor.executemany("declare t number; begin t := :1; end;", data)

    def test_4005_executemany_with_multiple_batches(self):
        "4005 - test executing multiple times (with multiple batches)"
        self.cursor.execute("truncate table TestTempTable")
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        self.cursor.executemany(sql, [(1, None), (2, None)])
        self.cursor.executemany(sql, [(3, None), (4, "Testing")])

    def test_4006_executemany_numeric(self):
        "4006 - test executemany() with various numeric types"
        self.cursor.execute("truncate table TestTempTable")
        data = [
            (1, 5),
            (2, 7.0),
            (3, 6.5),
            (4, 2 ** 65),
            (5, decimal.Decimal("24.5"))
        ]
        sql = "insert into TestTempTable (IntCol, NumberCol) values (:1, :2)"
        self.cursor.executemany(sql, data)
        self.cursor.execute("""
                select IntCol, NumberCol
                from TestTempTable
                order by IntCol""")
        self.assertEqual(self.cursor.fetchall(), data)

    def test_4007_executemany_with_resize(self):
        "4007 - test executing a statement multiple times (with resize)"
        self.cursor.execute("truncate table TestTempTable")
        rows = [
            (1, "First"),
            (2, "Second"),
            (3, "Third"),
            (4, "Fourth"),
            (5, "Fifth"),
            (6, "Sixth"),
            (7, "Seventh and the longest one")
        ]
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        self.cursor.executemany(sql, rows)
        self.cursor.execute("""
                select IntCol, StringCol1
                from TestTempTable
                order by IntCol""")
        fetched_rows = self.cursor.fetchall()
        self.assertEqual(fetched_rows, rows)

    def test_4008_executemany_with_exception(self):
        "4008 - test executing a statement multiple times (with exception)"
        self.cursor.execute("truncate table TestTempTable")
        rows = [{"value": n} for n in (1, 2, 3, 2, 5)]
        statement = "insert into TestTempTable (IntCol) values (:value)"
        self.assertRaisesRegex(oracledb.DatabaseError, "^ORA-00001:",
                               self.cursor.executemany, statement, rows)
        self.assertEqual(self.cursor.rowcount, 3)

    def test_4009_executemany_with_invalid_parameters(self):
        "4009 - test calling executemany() with invalid parameters"
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        self.assertRaisesRegex(oracledb.ProgrammingError, "^DPY-2004:",
                               self.cursor.executemany, sql,
                               "These are not valid parameters")

    def test_4010_executemany_no_parameters(self):
        "4010 - test calling executemany() without any bind parameters"
        num_rows = 5
        self.cursor.execute("truncate table TestTempTable")
        self.cursor.executemany("""
                declare
                    t_Id          number;
                begin
                    select nvl(count(*), 0) + 1 into t_Id
                    from TestTempTable;

                    insert into TestTempTable (IntCol, StringCol1)
                    values (t_Id, 'Test String ' || t_Id);
                end;""", num_rows)
        self.assertEqual(self.cursor.rowcount, 0)
        self.cursor.execute("select count(*) from TestTempTable")
        count, = self.cursor.fetchone()
        self.assertEqual(count, num_rows)

    def test_4011_executemany_bound_earlier(self):
        "4011 - test calling executemany() with binds performed earlier"
        num_rows = 9
        self.cursor.execute("truncate table TestTempTable")
        var = self.cursor.var(int, arraysize=num_rows)
        self.cursor.setinputsizes(var)
        self.cursor.executemany("""
                declare
                    t_Id          number;
                begin
                    select nvl(count(*), 0) + 1 into t_Id
                    from TestTempTable;

                    insert into TestTempTable (IntCol, StringCol1)
                    values (t_Id, 'Test String ' || t_Id);

                    select sum(IntCol) into :1
                    from TestTempTable;
                end;""", num_rows)
        self.assertEqual(self.cursor.rowcount, 0)
        expected_data = [1, 3, 6, 10, 15, 21, 28, 36, 45]
        self.assertEqual(var.values, expected_data)

    def test_4012_executemany_with_plsql_binds(self):
        "4012 - test executing plsql statements multiple times (with binds)"
        var = self.cursor.var(int, arraysize=5)
        self.cursor.setinputsizes(var)
        data = [[25], [30], [None], [35], [None]]
        exepected_data = [25, 30, None, 35, None]
        self.cursor.executemany("declare t number; begin t := :1; end;", data)
        self.assertEqual(var.values, exepected_data)

    def test_4013_executemany_with_incorrect_params(self):
        "4013 - test executemany with incorrect parameters"
        self.assertRaisesRegex(oracledb.ProgrammingError, "^DPY-2004:",
                               self.cursor.executemany, "select :1 from dual",
                               [1])

    def test_4014_executemany_with_mixed_binds_pos_first(self):
        "4014 - test executemany with mixed binds (pos first)"
        rows = [["test"], {"value": 1}]
        self.assertRaisesRegex(oracledb.ProgrammingError, "^DPY-2006:",
                               self.cursor.executemany, "select :1 from dual",
                               rows)

    def test_4015_executemany_with_mixed_binds_name_first(self):
        "4015 - test executemany with mixed binds (name first)"
        rows = [{"value": 1}, ["test"]]
        self.assertRaisesRegex(oracledb.ProgrammingError, "^DPY-2006:",
                               self.cursor.executemany,
                               "select :value from dual", rows)

    def test_4016_executemany_plsql_dml_returning(self):
        "4016 - test executemany() with a pl/sql statement with dml returning"
        num_rows = 5
        self.cursor.execute("truncate table TestTempTable")
        out_var = self.cursor.var(oracledb.NUMBER, arraysize=5)
        self.cursor.setinputsizes(out_var)
        self.cursor.executemany("""
                declare
                    t_Id          number;
                begin
                    select nvl(count(*), 0) + 1 into t_Id
                    from TestTempTable;

                    insert into TestTempTable (IntCol, StringCol1)
                    values (t_Id, 'Test String ' || t_Id) returning
                    IntCol into :out_bind;
                end;""", num_rows)
        self.assertEqual(out_var.values, [1, 2, 3, 4, 5])

    def test_4017_executemany_pl_sql_with_in_and_out_binds(self):
        "4017 - test executemany() with pl/sql in binds and out binds"
        self.cursor.execute("truncate table TestTempTable")
        int_values = [5, 8, 17, 24, 6]
        str_values = ["Test 5", "Test 8", "Test 17", "Test 24", "Test 6"]
        out_bind = self.cursor.var(oracledb.NUMBER, arraysize=5)
        self.cursor.setinputsizes(None, None, out_bind)
        data = list(zip(int_values, str_values))
        self.cursor.executemany("""
            begin
                insert into TestTempTable (IntCol, StringCol1)
                values (:int_val, :str_val)
                returning IntCol into :out_bind;
            end;""", data)
        self.assertEqual(out_bind.values, [5, 8, 17, 24, 6])

    def test_4018_executemany_pl_sql_out_bind(self):
        "4018 - test executemany() with pl/sql outbinds"
        self.cursor.execute("truncate table TestTempTable")
        out_bind = self.cursor.var(oracledb.NUMBER, arraysize=5)
        self.cursor.setinputsizes(out_bind)
        self.cursor.executemany("""
            begin
                :out_var := 5;
            end;""", 5)
        self.assertEqual(out_bind.values, [5, 5, 5, 5, 5])

    def test_4019_re_executemany_pl_sql_with_in_and_out_binds(self):
        "4019 - test re-executemany() with pl/sql in binds and out binds"
        int_values = [5, 8, 17, 24, 6]
        str_values = ["Test 5", "Test 8", "Test 17", "Test 24", "Test 6"]
        data = list(zip(int_values, str_values))
        for i in range(2):
            self.cursor.execute("truncate table TestTempTable")
            out_bind = self.cursor.var(oracledb.NUMBER, arraysize=5)
            self.cursor.setinputsizes(None, None, out_bind)
            self.cursor.executemany("""
                begin
                    insert into TestTempTable (IntCol, StringCol1)
                    values (:int_val, :str_val)
                    returning IntCol into :out_bind;
                end;""", data)
            self.assertEqual(out_bind.values, [5, 8, 17, 24, 6])

    def test_4020_executemany_with_plsql_single_row(self):
        "4020 - test PL/SQL statement with single row bind"
        value = 4020
        var = self.cursor.var(int)
        data = [[var, value]]
        self.cursor.executemany("begin :1 := :2; end;", data)
        self.assertEqual(var.values, [value])

    def test_4021_defer_type_assignment(self):
        "4021 - test deferral of type assignment"
        self.cursor.execute("truncate table TestTempTable")
        data = [(1, None), (2, 25)]
        self.cursor.executemany("""
                insert into TestTempTable
                (IntCol, NumberCol)
                values (:1, :2)""", data)
        self.connection.commit()
        self.cursor.execute("""
                select IntCol, NumberCol
                from TestTempTable
                order by IntCol""")
        fetched_data = self.cursor.fetchall()
        self.assertEqual(data, fetched_data)

if __name__ == "__main__":
    test_env.run_test_cases()
