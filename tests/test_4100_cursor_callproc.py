# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
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

    def test_4110(self):
        "4110 - test to verify that deprecated keywordParameters works"
        extra_amount = self.cursor.var(oracledb.DB_TYPE_NUMBER)
        extra_amount.setvalue(0, 5)
        kwargs = dict(a_ExtraAmount=extra_amount, a_String="hi")
        results = self.cursor.callfunc(
            "func_Test", oracledb.DB_TYPE_NUMBER, keywordParameters=kwargs
        )
        self.assertEqual(results, 7)

        out_value = self.cursor.var(oracledb.DB_TYPE_NUMBER)
        kwargs = dict(a_OutValue=out_value)
        results = self.cursor.callproc(
            "proc_Test", ("hi", 5), keywordParameters=kwargs
        )
        self.assertEqual(results, ["hi", 10])
        self.assertEqual(out_value.getvalue(), 2.0)

    def test_4111(self):
        "4111 - test callproc with setinputsizes"
        out_value = self.cursor.var(oracledb.DB_TYPE_BOOLEAN)
        self.cursor.setinputsizes(
            oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_NUMBER, out_value
        )
        results = self.cursor.callproc("proc_Test2", ("hi", 5, out_value))
        self.assertEqual(results, ["hi", 10, True])
        self.assertTrue(out_value.getvalue())

    def test_4112(self):
        "4112 - test callfunc with setinputsizes"
        self.cursor.setinputsizes(
            oracledb.DB_TYPE_NUMBER,
            oracledb.DB_TYPE_VARCHAR,
            oracledb.DB_TYPE_NUMBER,
            oracledb.DB_TYPE_BOOLEAN,
        )
        results = self.cursor.callfunc(
            "func_Test2", oracledb.NUMBER, ("hi", 5, True)
        )
        self.assertEqual(results, 7)

    def test_4113(self):
        "4113 - test callproc with setinputsizes with kwargs"
        out_value = self.cursor.var(oracledb.DB_TYPE_BOOLEAN)
        self.cursor.setinputsizes(
            oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_NUMBER, out_value
        )
        kwargs = dict(a_OutValue=out_value)
        results = self.cursor.callproc("proc_Test2", ("hi", 5), kwargs)
        self.assertEqual(results, ["hi", 10])
        self.assertTrue(out_value.getvalue())

        out_value = self.cursor.var(oracledb.DB_TYPE_BOOLEAN)
        self.cursor.setinputsizes(
            oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_NUMBER, out_value
        )
        kwargs = dict(a_InValue="hi", a_InOutValue=5, a_OutValue=out_value)
        results = self.cursor.callproc("proc_Test2", [], kwargs)
        self.assertEqual(results, [])
        self.assertTrue(out_value.getvalue())

        self.cursor.setinputsizes(
            oracledb.DB_TYPE_VARCHAR,
            oracledb.DB_TYPE_NUMBER,
            oracledb.DB_TYPE_BOOLEAN,
        )
        kwargs = dict(a_InValue="hi", a_InOutValue=5, a_OutValue=out_value)
        results = self.cursor.callproc("proc_Test2", [], kwargs)
        self.assertEqual(results, [])
        self.assertTrue(out_value.getvalue())

    def test_4114(self):
        "4114 - test callproc with setinputsizes with kwargs in mixed order"
        out_value = self.cursor.var(oracledb.DB_TYPE_BOOLEAN)
        self.cursor.setinputsizes(
            oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_NUMBER, out_value
        )
        kwargs = dict(a_OutValue=out_value, a_InValue="hi", a_InOutValue=5)
        with self.assertRaisesFullCode("ORA-06550"):
            results = self.cursor.callproc(
                "proc_Test2", keyword_parameters=kwargs
            )
            self.assertEqual(results, [])
            self.assertTrue(out_value.getvalue())

        self.cursor.setinputsizes(
            oracledb.DB_TYPE_VARCHAR,
            oracledb.DB_TYPE_NUMBER,
            oracledb.DB_TYPE_BOOLEAN,
        )
        with self.assertRaisesFullCode("ORA-06550"):
            self.cursor.callproc("proc_Test2", keyword_parameters=kwargs)

    def test_4115(self):
        "4115 - test callfunc with setinputsizes with kwargs"
        extra_amount = self.cursor.var(oracledb.DB_TYPE_NUMBER)
        extra_amount.setvalue(0, 5)
        test_values = [
            (["hi"], dict(a_ExtraAmount=extra_amount, a_Boolean=True)),
            (
                [],
                dict(
                    a_String="hi", a_ExtraAmount=extra_amount, a_Boolean=True
                ),
            ),
        ]
        for args, kwargs in test_values:
            self.cursor.setinputsizes(
                oracledb.DB_TYPE_NUMBER,
                oracledb.DB_TYPE_VARCHAR,
                oracledb.DB_TYPE_NUMBER,
                oracledb.DB_TYPE_BOOLEAN,
            )
            results = self.cursor.callfunc(
                "func_Test2", oracledb.DB_TYPE_NUMBER, args, kwargs
            )
            self.assertEqual(results, 7)

    def test_4116(self):
        "4116 - test callproc with setinputsizes with extra arguments"
        out_value = self.cursor.var(oracledb.DB_TYPE_BOOLEAN)
        test_values = [
            (("hi", 5, out_value), None),
            (("hi",), dict(a_InOutValue=5, a_OutValue=out_value)),
            ([], dict(a_InValue="hi", a_InOutValue=5, a_OutValue=out_value)),
        ]
        for args, kwargs in test_values:
            self.cursor.setinputsizes(
                oracledb.DB_TYPE_VARCHAR,
                oracledb.NUMBER,
                out_value,
                oracledb.DB_TYPE_VARCHAR,  # extra argument
            )
            with self.assertRaisesFullCode("ORA-01036", "DPY-4009"):
                self.cursor.callproc("proc_Test2", args, kwargs)

    def test_4117(self):
        "4117 - test callfunc with setinputsizes with extra arguments"
        extra_amount = self.cursor.var(oracledb.DB_TYPE_NUMBER)
        extra_amount.setvalue(0, 5)
        test_values = [
            (["hi", extra_amount], None),
            (["hi"], dict(a_ExtraAmount=extra_amount)),
            ([], dict(a_ExtraAmount=extra_amount, a_String="hi")),
        ]
        for args, kwargs in test_values:
            self.cursor.setinputsizes(
                oracledb.DB_TYPE_NUMBER,
                oracledb.DB_TYPE_VARCHAR,
                oracledb.DB_TYPE_NUMBER,
                oracledb.DB_TYPE_BOOLEAN,
                oracledb.DB_TYPE_VARCHAR,  # extra argument
            )
            with self.assertRaisesFullCode("ORA-01036", "DPY-4009"):
                self.cursor.callfunc(
                    "func_Test2", oracledb.DB_TYPE_NUMBER, args, kwargs
                )

    def test_4118(self):
        "4118 - test callproc with setinputsizes with too few parameters"
        out_value = self.cursor.var(oracledb.DB_TYPE_BOOLEAN)

        # setinputsizes for 2 args (missed 1 args)
        self.cursor.setinputsizes(
            oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_NUMBER
        )
        results = self.cursor.callproc("proc_Test2", ("hi", 5, out_value))
        self.assertEqual(results, ["hi", 10, out_value.getvalue()])
        self.assertTrue(out_value.getvalue())

        # setinputsizes for 2 args (missed 1 kwargs)
        self.cursor.setinputsizes(
            oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_NUMBER
        )
        kwargs = dict(a_OutValue=out_value)
        results = self.cursor.callproc("proc_Test2", ("hi", 5), kwargs)
        self.assertEqual(results, ["hi", 10])
        self.assertTrue(out_value.getvalue())

        # setinputsizes for 1 args (missed 2 args)
        self.cursor.setinputsizes(oracledb.DB_TYPE_VARCHAR)
        results = self.cursor.callproc("proc_Test2", ("hi", 5, out_value))
        self.assertEqual(results, ["hi", 10, out_value.getvalue()])
        self.assertTrue(out_value.getvalue())

        # setinputsizes for 1 args (missed 1 args and 1 kwargs)
        self.cursor.setinputsizes(oracledb.DB_TYPE_VARCHAR)
        kwargs = dict(a_OutValue=out_value)
        results = self.cursor.callproc("proc_Test2", ("hi", 5), kwargs)
        self.assertEqual(results, ["hi", 10])
        self.assertTrue(out_value.getvalue())

        # setinputsizes for 2 kwargs (missed 1 kwargs)
        self.cursor.setinputsizes(
            oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_NUMBER
        )
        kwargs = dict(a_InValue="hi", a_InOutValue=5, a_OutValue=out_value)
        results = self.cursor.callproc("proc_Test2", [], kwargs)
        self.assertEqual(results, [])
        self.assertTrue(out_value.getvalue())

    def test_4119(self):
        """
        4119 - test callproc with setinputsizes with wrong order of parameters
        """
        # setinputsizes for 2 args (missed 1 kwargs)
        out_value = self.cursor.var(oracledb.DB_TYPE_BOOLEAN)
        self.cursor.setinputsizes(bool, oracledb.DB_TYPE_VARCHAR)
        kwargs = dict(a_OutValue=out_value)
        with self.assertRaisesFullCode("ORA-06550"):
            self.cursor.callproc("proc_Test2", ["hi", 5], kwargs)

        # setinputsizes for 2 kwargs (missed 1 kwargs)
        self.cursor.setinputsizes(bool, oracledb.DB_TYPE_VARCHAR)
        kwargs = dict(a_InValue="hi", a_InOutValue=5, a_OutValue=out_value)
        with self.assertRaisesFullCode("ORA-06550"):
            self.cursor.callproc("proc_Test2", [], kwargs)

    def test_4120(self):
        "4120 - test callfunc with setinputsizes with too few parameters"
        # setinputsizes for return_type and 1 kwargs (missed 2 kwargs)
        bool_var = self.cursor.var(oracledb.DB_TYPE_BOOLEAN)
        bool_var.setvalue(0, False)
        kwargs = dict(a_Boolean=bool_var, a_String="hi", a_ExtraAmount=3)
        self.cursor.setinputsizes(oracledb.NUMBER, oracledb.DB_TYPE_VARCHAR)
        results = self.cursor.callfunc(
            "func_Test2", oracledb.NUMBER, [], kwargs
        )
        self.assertEqual(results, -1)

        # setinputsizes for return_type (missed 3 kwargs)
        bool_var.setvalue(0, False)
        kwargs = dict(a_Boolean=bool_var, a_String="hi", a_ExtraAmount=1)
        self.cursor.setinputsizes(oracledb.NUMBER)
        results = self.cursor.callfunc(
            "func_Test2", oracledb.NUMBER, [], kwargs
        )
        self.assertEqual(results, 1)

        # setinputsizes for return_type (missed 3 args)
        bool_var.setvalue(0, True)
        self.cursor.setinputsizes(oracledb.NUMBER)
        results = self.cursor.callfunc(
            "func_Test2", oracledb.NUMBER, ["hi", 2, bool_var]
        )
        self.assertEqual(results, 4)

    def test_4121(self):
        """
        4121 - test callfunc with setinputsizes with wrong order of parameters
        """
        # setinputsizes for 2 args (missed 2 kwargs)
        bool_var = self.cursor.var(oracledb.DB_TYPE_BOOLEAN)
        bool_var.setvalue(0, True)
        self.cursor.setinputsizes(oracledb.NUMBER, oracledb.DB_TYPE_BOOLEAN)
        kwargs = dict(a_Boolean=bool_var)
        with self.assertRaisesFullCode("ORA-06550"):
            self.cursor.callfunc(
                "func_Test2", oracledb.NUMBER, ["hi", bool_var], kwargs
            )

    def test_4122(self):
        "4122 - test callfunc with setinputsizes without type for return_type"
        # setinputsizes for 1 args and 1 kwargs
        bool_var = self.cursor.var(oracledb.DB_TYPE_BOOLEAN)
        bool_var.setvalue(0, False)
        self.cursor.setinputsizes(oracledb.NUMBER, oracledb.DB_TYPE_BOOLEAN)
        kwargs = dict(a_Boolean=bool_var)
        with self.assertRaisesFullCode("ORA-06550"):
            self.cursor.callfunc(
                "func_Test2", oracledb.DB_TYPE_NUMBER, ["hi"], kwargs
            )

        # setinputsizes for 2 kwargs (missed 1 kwargs)
        bool_var.setvalue(0, False)
        kwargs = dict(a_Boolean=bool_var, a_String="hi", a_ExtraAmount=0)
        self.cursor.setinputsizes(
            oracledb.DB_TYPE_BOOLEAN, oracledb.DB_TYPE_VARCHAR
        )
        results = self.cursor.callfunc(
            "func_Test2", oracledb.DB_TYPE_NUMBER, [], kwargs
        )
        self.assertEqual(results, 2)

        # setinputsizes for 2 args and 1 kwargs
        bool_var.setvalue(0, False)
        self.cursor.setinputsizes(
            oracledb.DB_TYPE_BOOLEAN, oracledb.DB_TYPE_NUMBER
        )
        kwargs = dict(a_Boolean=bool_var)
        results = self.cursor.callfunc(
            "func_Test2", oracledb.DB_TYPE_NUMBER, ["Bye", 2], kwargs
        )
        self.assertEqual(results, 1)

        # setinputsizes for 2 args (missed 1 args)
        bool_var.setvalue(0, False)
        self.cursor.setinputsizes(
            oracledb.DB_TYPE_BOOLEAN, oracledb.DB_TYPE_NUMBER
        )
        kwargs = dict(a_Boolean=bool_var)
        results = self.cursor.callfunc(
            "func_Test2", oracledb.DB_TYPE_NUMBER, ["Light", -1, bool_var]
        )
        self.assertEqual(results, 6)

    def test_4123(self):
        "4123 - test executing a procedure with callfunc"
        with self.assertRaisesFullCode("ORA-06550"):
            self.cursor.callfunc(
                "proc_Test2", oracledb.NUMBER, ("hello", 3, False)
            )

    def test_4124(self):
        "4124 - test executing a function with callproc"
        with self.assertRaisesFullCode("ORA-06550"):
            self.cursor.callproc("func_Test2", ("hello", 5, True))

    def test_4125(self):
        "4125 - test calling a procedure with a string > 32767 characters"
        data = "4125" * 16000
        size_var = self.cursor.var(int)
        self.cursor.callproc("pkg_TestLobs.GetSize", [data, size_var])
        self.assertEqual(size_var.getvalue(), len(data))

    def test_4126(self):
        "4125 - test calling a procedure with raw data > 32767 bytes"
        data = b"4126" * 16250
        size_var = self.cursor.var(int)
        self.cursor.callproc("pkg_TestLobs.GetSize", [data, size_var])
        self.assertEqual(size_var.getvalue(), len(data))


if __name__ == "__main__":
    test_env.run_test_cases()
