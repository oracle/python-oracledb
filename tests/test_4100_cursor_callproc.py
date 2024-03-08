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
4100 - Module for testing the methods for calling stored procedures and
functions (callproc() and callfunc())
"""

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    def test_4100(self):
        "4100 - test executing a stored procedure"
        var = self.cursor.var(oracledb.NUMBER)
        results = self.cursor.callproc("proc_Test", ("hi", 5, var))
        self.assertEqual(results, ["hi", 10, 2.0])

    def test_4101(self):
        "4101 - test executing a stored procedure with all args keyword args"
        inout_value = self.cursor.var(oracledb.NUMBER)
        inout_value.setvalue(0, 5)
        out_value = self.cursor.var(oracledb.NUMBER)
        kwargs = dict(
            a_InOutValue=inout_value, a_InValue="hi", a_OutValue=out_value
        )
        results = self.cursor.callproc("proc_Test", [], kwargs)
        self.assertEqual(results, [])
        self.assertEqual(inout_value.getvalue(), 10)
        self.assertEqual(out_value.getvalue(), 2.0)

    def test_4102(self):
        "4102 - test executing a stored procedure with last arg as keyword arg"
        out_value = self.cursor.var(oracledb.NUMBER)
        kwargs = dict(a_OutValue=out_value)
        results = self.cursor.callproc("proc_Test", ("hi", 5), kwargs)
        self.assertEqual(results, ["hi", 10])
        self.assertEqual(out_value.getvalue(), 2.0)

    def test_4103(self):
        "4103 - test executing a stored procedure, repeated keyword arg"
        kwargs = dict(
            a_InValue="hi", a_OutValue=self.cursor.var(oracledb.NUMBER)
        )
        with self.assertRaisesFullCode("ORA-06550"):
            self.cursor.callproc("proc_Test", ("hi", 5), kwargs)

    def test_4104(self):
        "4104 - test executing a stored procedure without any arguments"
        results = self.cursor.callproc("proc_TestNoArgs")
        self.assertEqual(results, [])

    def test_4105(self):
        "4105 - test executing a stored function"
        results = self.cursor.callfunc("func_Test", oracledb.NUMBER, ("hi", 5))
        self.assertEqual(results, 7)

    def test_4106(self):
        "4106 - test executing a stored function without any arguments"
        results = self.cursor.callfunc("func_TestNoArgs", oracledb.NUMBER)
        self.assertEqual(results, 712)

    def test_4107(self):
        "4107 - test executing a stored function with wrong parameters"
        func_name = "func_Test"
        with self.assertRaisesFullCode("DPY-2007"):
            self.cursor.callfunc(oracledb.NUMBER, func_name, ("hi", 5))
        with self.assertRaisesFullCode("ORA-06550"):
            self.cursor.callfunc(func_name, oracledb.NUMBER, ("hi", 5, 7))
        with self.assertRaisesFullCode("DPY-2012"):
            self.cursor.callfunc(func_name, oracledb.NUMBER, "hi", 7)
        with self.assertRaisesFullCode("ORA-06502"):
            self.cursor.callfunc(func_name, oracledb.NUMBER, [5, "hi"])
        with self.assertRaisesFullCode("ORA-06550"):
            self.cursor.callfunc(func_name, oracledb.NUMBER)
        with self.assertRaisesFullCode("DPY-2012"):
            self.cursor.callfunc(func_name, oracledb.NUMBER, 5)

    def test_4108(self):
        "4108 - test to verify keywordParameters is deprecated"
        out_value = self.cursor.var(oracledb.NUMBER)
        kwargs = dict(a_OutValue=out_value)
        with self.assertRaisesFullCode("DPY-2014"):
            self.cursor.callproc(
                "proc_Test", ("hi", 5), kwargs, keywordParameters=kwargs
            )
        extra_amount = self.cursor.var(oracledb.NUMBER)
        extra_amount.setvalue(0, 5)
        kwargs = dict(a_ExtraAmount=extra_amount, a_String="hi")
        with self.assertRaisesFullCode("DPY-2014"):
            self.cursor.callfunc(
                "func_Test",
                oracledb.NUMBER,
                [],
                kwargs,
                keywordParameters=kwargs,
            )

    def test_4109(self):
        "4109 - test error for keyword args with invalid type"
        kwargs = [5]
        with self.assertRaisesFullCode("DPY-2013"):
            self.cursor.callproc("proc_Test", [], kwargs)
        with self.assertRaisesFullCode("DPY-2013"):
            self.cursor.callfunc("func_Test", oracledb.NUMBER, [], kwargs)


if __name__ == "__main__":
    test_env.run_test_cases()
