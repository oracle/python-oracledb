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
3900 - Module for testing the cursor execute() method
"""

import oracledb
import test_env

class TestCase(test_env.BaseTestCase):

    def test_3900_execute_no_args(self):
        "3900 - test executing a statement without any arguments"
        result = self.cursor.execute("begin null; end;")
        self.assertEqual(result, None)

    def test_3901_execute_no_statement_with_args(self):
        "3901 - test executing a None statement with bind variables"
        self.assertRaisesRegex(oracledb.ProgrammingError, "^DPY-2001:",
                               self.cursor.execute, None, x=5)

    def test_3902_execute_empty_keyword_args(self):
        "3902 - test executing a statement with args and empty keyword args"
        simple_var = self.cursor.var(oracledb.NUMBER)
        args = [simple_var]
        kwargs = {}
        result = self.cursor.execute("begin :1 := 25; end;", args, **kwargs)
        self.assertEqual(result, None)
        self.assertEqual(simple_var.getvalue(), 25)

    def test_3903_execute_keyword_args(self):
        "3903 - test executing a statement with keyword arguments"
        simple_var = self.cursor.var(oracledb.NUMBER)
        result = self.cursor.execute("begin :value := 5; end;",
                                     value=simple_var)
        self.assertEqual(result, None)
        self.assertEqual(simple_var.getvalue(), 5)

    def test_3904_execute_dictionary_arg(self):
        "3904 - test executing a statement with a dictionary argument"
        simple_var = self.cursor.var(oracledb.NUMBER)
        dict_arg = dict(value=simple_var)
        result = self.cursor.execute("begin :value := 10; end;", dict_arg)
        self.assertEqual(result, None)
        self.assertEqual(simple_var.getvalue(), 10)

    def test_3905_execute_multiple_arg_types(self):
        "3905 - test executing a statement with both a dict and keyword args"
        simple_var = self.cursor.var(oracledb.NUMBER)
        dict_arg = dict(value=simple_var)
        self.assertRaisesRegex(oracledb.ProgrammingError, "^DPY-2005:",
                               self.cursor.execute,
                               "begin :value := 15; end;", dict_arg,
                               value=simple_var)

    def test_3906_execute_and_modify_array_size(self):
        "3906 - test executing a statement and then changing the array size"
        self.cursor.execute("select IntCol from TestNumbers")
        self.cursor.arraysize = 20
        self.assertEqual(len(self.cursor.fetchall()), 10)

    def test_3907_bad_execute(self):
        "3907 - test that subsequent executes succeed after bad execute"
        sql = "begin raise_application_error(-20000, 'this); end;"
        self.assertRaisesRegex(oracledb.DatabaseError,
                               "^ORA-06550:|^ORA-01756:", self.cursor.execute,
                               sql)
        self.cursor.execute("begin null; end;")

    def test_3908_fetch_after_bad_execute(self):
        "3908 - test that subsequent fetches fail after bad execute"
        self.assertRaisesRegex(oracledb.DatabaseError, "^ORA-00904:",
                               self.cursor.execute, "select y from dual")
        self.assertRaisesRegex(oracledb.InterfaceError, "^DPY-1003:",
                               self.cursor.fetchall)

    def test_3909_execute_bind_names_with_incorrect_bind(self):
        "3909 - test executing a statement with an incorrect named bind"
        statement = "select * from TestStrings where IntCol = :value"
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-4008:|^ORA-01036:",
                               self.cursor.execute, statement, value2=3)

    def test_3910_execute_with_named_binds(self):
        "3910 - test executing a statement with named binds"
        statement = "select * from TestNumbers where IntCol = :value1 " + \
                    "and LongIntCol = :value2"
        result = self.cursor.execute(statement, value1=1, value2=38)
        self.assertEqual(len(result.fetchall()), 1)

    def test_3911_execute_bind_position_with_incorrect_bind(self):
        "3911 - test executing a statement with an incorrect positional bind"
        statement = "select * from TestNumbers where IntCol = :value " + \
                    "and LongIntCol = :value2"
        self.assertRaisesRegex(oracledb.DatabaseError,
                               "^DPY-4009:|^ORA-01008:",
                               self.cursor.execute, statement, [3])

    def test_3912_execute_with_positional_binds(self):
        "3912 - test executing a statement with positional binds"
        statement = "select * from TestNumbers where IntCol = :value " + \
                    "and LongIntCol = :value2"
        result = self.cursor.execute(statement, [1,38])
        self.assertEqual(len(result.fetchall()), 1)

    def test_3913_execute_with_rebinding_bind_name(self):
        "3913 - test executing a statement after rebinding a named bind"
        statement = "begin :value := :value2 + 5; end;"
        simple_var = self.cursor.var(oracledb.NUMBER)
        simple_var2 = self.cursor.var(oracledb.NUMBER)
        simple_var2.setvalue(0, 5)
        result = self.cursor.execute(statement, value=simple_var,
                                     value2=simple_var2)
        self.assertEqual(result, None)
        self.assertEqual(simple_var.getvalue(), 10)

        simple_var = self.cursor.var(oracledb.NATIVE_FLOAT)
        simple_var2 = self.cursor.var(oracledb.NATIVE_FLOAT)
        simple_var2.setvalue(0, 10)
        result = self.cursor.execute(statement, value=simple_var,
                                     value2=simple_var2)
        self.assertEqual(result, None)
        self.assertEqual(simple_var.getvalue(), 15)

    def test_3914_bind_by_name_with_duplicates(self):
        "3914 - test executing a PL/SQL statement with duplicate binds"
        statement = "begin :value := :value + 5; end;"
        simple_var = self.cursor.var(oracledb.NUMBER)
        simple_var.setvalue(0, 5)
        result = self.cursor.execute(statement, value=simple_var)
        self.assertEqual(result, None)
        self.assertEqual(simple_var.getvalue(), 10)

    def test_3915_positional_bind_with_duplicates(self):
        "3915 - test executing a PL/SQL statement with duplicate binds"
        statement = "begin :value := :value + 5; end;"
        simple_var = self.cursor.var(oracledb.NUMBER)
        simple_var.setvalue(0, 5)
        self.cursor.execute(statement, [simple_var])
        self.assertEqual(simple_var.getvalue(), 10)

    def test_3916_execute_with_incorrect_bind_values(self):
        "3916 - test executing a statement with an incorrect number of binds"
        statement = "begin :value := :value2 + 5; end;"
        var = self.cursor.var(oracledb.NUMBER)
        var.setvalue(0, 5)
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-4010:|^ORA-01008:",
                               self.cursor.execute, statement)
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-4010:|^ORA-01008:",
                               self.cursor.execute, statement, value=var)
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-4008:|^ORA-01036:",
                               self.cursor.execute, statement, value=var,
                               value2=var, value3=var)

    def test_3917_change_in_size_on_successive_bind(self):
        "3917 - change in size on subsequent binds does not use optimised path"
        self.cursor.execute("truncate table TestTempTable")
        data = [
            (1, "Test String #1"),
            (2, "ABC" * 100)
        ]
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        for row in data:
            self.cursor.execute(sql, row)
        self.connection.commit()
        self.cursor.execute("select IntCol, StringCol1 from TestTempTable")
        self.assertEqual(self.cursor.fetchall(), data)

    def test_3918_dml_can_use_optimised_path(self):
        "3918 - test that dml can use optimised path"
        data_to_insert = [
            (1, "Test String #1"),
            (2, "Test String #2"),
            (3, "Test String #3")
        ]
        self.cursor.execute("truncate table TestTempTable")
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        for row in data_to_insert:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, row)
        self.connection.commit()
        self.cursor.execute("""
                select IntCol, StringCol1
                from TestTempTable
                order by IntCol""")
        self.assertEqual(self.cursor.fetchall(), data_to_insert)

    def test_3919_execute_with_invalid_parameters(self):
        "3919 - test calling execute() with invalid parameters"
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        self.assertRaisesRegex(oracledb.ProgrammingError, "^DPY-2003:",
                               self.cursor.execute, sql,
                               "These are not valid parameters")

    def test_3920_execute_with_mixed_binds(self):
        "3920 - test calling execute() with mixed binds"
        self.cursor.execute("truncate table TestTempTable")
        self.cursor.setinputsizes(None, None, str)
        data = dict(val1=1, val2="Test String 1")
        self.assertRaisesRegex(oracledb.ProgrammingError, "^DPY-2006:",
                               self.cursor.execute, """
                               insert into TestTempTable (IntCol, StringCol1)
                               values (:1, :2)
                               returning StringCol1 into :out_var""", data)

    def test_3921_bind_by_name_with_double_quotes(self):
        "3921 - test binding by name with double quotes"
        sql = 'select :"_value1" + :"VaLue_2" + :"3VALUE" from dual'
        data = {'"_value1"': 1, '"VaLue_2"': 2, '"3VALUE"': 3}
        self.cursor.execute(sql, data)
        result, = self.cursor.fetchone()
        self.assertEqual(result, 6)

    def test_3922_resize_buffer(self):
        "3922 - test executing a statement with different input buffer sizes"
        sql = """
                insert into TestTempTable (IntCol, StringCol1, StringCol2)
                values (:int_col, :str_val1, :str_val2) returning IntCol
                into :ret_data"""
        values1 = {"int_col" : 1, "str_val1": '{"a", "b"}', "str_val2" : None}
        values2 = {"int_col" : 2, "str_val1": None, "str_val2" : '{"a", "b"}'}
        values3 = {"int_col" : 3, "str_val1": '{"a"}', "str_val2" : None}

        self.cursor.execute("truncate table TestTempTable")
        ret_bind = self.cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=1)
        self.cursor.setinputsizes(ret_data=ret_bind)
        self.cursor.execute(sql, values1)
        self.assertEqual(ret_bind.values, [['1']])

        ret_bind = self.cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=1)
        self.cursor.setinputsizes(ret_data=ret_bind)
        self.cursor.execute(sql, values2)
        self.assertEqual(ret_bind.values, [['2']])

        ret_bind = self.cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=1)
        self.cursor.setinputsizes(ret_data=ret_bind)
        self.cursor.execute(sql, values3)
        self.assertEqual(ret_bind.values, [['3']])

    def test_3923_rowfactory_callable(self):
        "3923 - test using rowfactory"
        self.cursor.execute("truncate table TestTempTable")
        self.cursor.execute("""
                insert into TestTempTable (IntCol, StringCol1)
                values (1, 'Test 1')""")
        self.connection.commit()
        self.cursor.execute("select IntCol, StringCol1 from TestTempTable")
        column_names = [col[0] for col in self.cursor.description]
        self.cursor.rowfactory = lambda *row: dict(zip(column_names, row))
        self.assertEqual(self.cursor.fetchall(),
                         [{'INTCOL': 1, 'STRINGCOL1': 'Test 1'}])

    def test_3924_rowfactory_execute_same_sql(self):
        "3924 - test executing same query after setting rowfactory"
        self.cursor.execute("truncate table TestTempTable")
        data = [
            (1, 'Test 1'),
            (2, 'Test 2')
        ]
        self.cursor.executemany("""
                insert into TestTempTable (IntCol, StringCol1)
                values (:1, :2)""", data)
        self.connection.commit()
        self.cursor.execute("select IntCol, StringCol1 from TestTempTable")
        column_names = [col[0] for col in self.cursor.description]
        self.cursor.rowfactory = lambda *row: dict(zip(column_names, row))
        results_1 = self.cursor.fetchall()
        self.cursor.execute("select IntCol, StringCol1 from TestTempTable")
        results_2 = self.cursor.fetchall()
        self.assertEqual(results_1, results_2)

    def test_3925_rowfactory_execute_different_sql(self):
        "3925 - test executing different query after setting rowfactory"
        self.cursor.execute("truncate table TestTempTable")
        data = [
            (1, 'Test 1'),
            (2, 'Test 2')
        ]
        self.cursor.executemany("""
                insert into TestTempTable (IntCol, StringCol1)
                values (:1, :2)""", data)
        self.connection.commit()
        self.cursor.execute("select IntCol, StringCol1 from TestTempTable")
        column_names = [col[0] for col in self.cursor.description]
        self.cursor.rowfactory = lambda *row: dict(zip(column_names, row))
        self.cursor.execute("""
                select IntCol, StringCol from TestSTrings
                where IntCol between 1 and 3 order by IntCol""")
        expected_data = [
            (1, 'String 1'),
            (2, 'String 2'),
            (3, 'String 3')
        ]
        self.assertEqual(self.cursor.fetchall(), expected_data)

    def test_3926_rowfactory_on_refcursor(self):
        "3926 - test setting rowfactory on a REF cursor"
        with self.connection.cursor() as cursor:
            ref_cursor = cursor.callfunc("pkg_TestRefCursors.TestReturnCursor",
                                         oracledb.DB_TYPE_CURSOR, [2])
            column_names = [col[0] for col in ref_cursor.description]
            ref_cursor.rowfactory = lambda *row: dict(zip(column_names, row))
            self.assertEqual(ref_cursor.fetchall(),
                             [{'INTCOL': 1, 'STRINGCOL': 'String 1'},
                              {'INTCOL': 2, 'STRINGCOL': 'String 2'}])

    def test_3927_subclassed_string(self):
        "3927 - test using a subclassed string as bind parameter keys"
        class my_str(str):
            pass
        self.cursor.execute("truncate table TestTempTable")
        keys = {my_str("str_val"): oracledb.DB_TYPE_VARCHAR}
        self.cursor.setinputsizes(**keys)
        values = {
            my_str("int_val"): 3927,
            my_str("str_val"): "3927 - String Value"
        }
        self.cursor.execute("""
                insert into TestTempTable (IntCol, StringCol1)
                values (:int_val, :str_val)""", values)
        self.cursor.execute("select IntCol, StringCol1 from TestTempTable")
        self.assertEqual(self.cursor.fetchall(),
                         [(3927, "3927 - String Value")])

if __name__ == "__main__":
    test_env.run_test_cases()
