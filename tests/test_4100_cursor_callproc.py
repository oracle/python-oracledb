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


def test_4100(cursor):
    "4100 - test executing a stored procedure"
    var = cursor.var(oracledb.NUMBER)
    results = cursor.callproc("proc_Test", ("hi", 5, var))
    assert results == ["hi", 10, 2.0]


def test_4101(cursor):
    "4101 - test executing a stored procedure with all args keyword args"
    inout_value = cursor.var(oracledb.NUMBER)
    inout_value.setvalue(0, 5)
    out_value = cursor.var(oracledb.NUMBER)
    kwargs = dict(
        a_InOutValue=inout_value, a_InValue="hi", a_OutValue=out_value
    )
    results = cursor.callproc("proc_Test", [], kwargs)
    assert results == []
    assert inout_value.getvalue() == 10
    assert out_value.getvalue() == 2.0


def test_4102(cursor):
    "4102 - test executing a stored procedure with last arg as keyword arg"
    out_value = cursor.var(oracledb.NUMBER)
    kwargs = dict(a_OutValue=out_value)
    results = cursor.callproc("proc_Test", ("hi", 5), kwargs)
    assert results == ["hi", 10]
    assert out_value.getvalue() == 2.0


def test_4103(cursor, test_env):
    "4103 - test executing a stored procedure, repeated keyword arg"
    kwargs = dict(a_InValue="hi", a_OutValue=cursor.var(oracledb.NUMBER))
    with test_env.assert_raises_full_code("ORA-06550"):
        cursor.callproc("proc_Test", ("hi", 5), kwargs)


def test_4104(cursor):
    "4104 - test executing a stored procedure without any arguments"
    results = cursor.callproc("proc_TestNoArgs")
    assert results == []


def test_4105(cursor):
    "4105 - test executing a stored function"
    results = cursor.callfunc("func_Test", oracledb.NUMBER, ("hi", 5))
    assert results == 7


def test_4106(cursor):
    "4106 - test executing a stored function without any arguments"
    results = cursor.callfunc("func_TestNoArgs", oracledb.NUMBER)
    assert results == 712


def test_4107(cursor, test_env):
    "4107 - test executing a stored function with wrong parameters"
    func_name = "func_Test"
    with test_env.assert_raises_full_code("DPY-2007"):
        cursor.callfunc(oracledb.NUMBER, func_name, ("hi", 5))
    with test_env.assert_raises_full_code("ORA-06550"):
        cursor.callfunc(func_name, oracledb.NUMBER, ("hi", 5, 7))
    with test_env.assert_raises_full_code("DPY-2012"):
        cursor.callfunc(func_name, oracledb.NUMBER, "hi", 7)
    with test_env.assert_raises_full_code("ORA-06502"):
        cursor.callfunc(func_name, oracledb.NUMBER, [5, "hi"])
    with test_env.assert_raises_full_code("ORA-06550"):
        cursor.callfunc(func_name, oracledb.NUMBER)
    with test_env.assert_raises_full_code("DPY-2012"):
        cursor.callfunc(func_name, oracledb.NUMBER, 5)


def test_4108(cursor, test_env):
    "4108 - test to verify keywordParameters is deprecated"
    out_value = cursor.var(oracledb.NUMBER)
    kwargs = dict(a_OutValue=out_value)
    with test_env.assert_raises_full_code("DPY-2014"):
        cursor.callproc(
            "proc_Test", ("hi", 5), kwargs, keywordParameters=kwargs
        )
    extra_amount = cursor.var(oracledb.NUMBER)
    extra_amount.setvalue(0, 5)
    kwargs = dict(a_ExtraAmount=extra_amount, a_String="hi")
    with test_env.assert_raises_full_code("DPY-2014"):
        cursor.callfunc(
            "func_Test",
            oracledb.NUMBER,
            [],
            kwargs,
            keywordParameters=kwargs,
        )


def test_4109(cursor, test_env):
    "4109 - test error for keyword args with invalid type"
    kwargs = [5]
    with test_env.assert_raises_full_code("DPY-2013"):
        cursor.callproc("proc_Test", [], kwargs)
    with test_env.assert_raises_full_code("DPY-2013"):
        cursor.callfunc("func_Test", oracledb.NUMBER, [], kwargs)


def test_4110(cursor):
    "4110 - test to verify that deprecated keywordParameters works"
    extra_amount = cursor.var(oracledb.DB_TYPE_NUMBER)
    extra_amount.setvalue(0, 5)
    kwargs = dict(a_ExtraAmount=extra_amount, a_String="hi")
    results = cursor.callfunc(
        "func_Test", oracledb.DB_TYPE_NUMBER, keywordParameters=kwargs
    )
    assert results == 7

    out_value = cursor.var(oracledb.DB_TYPE_NUMBER)
    kwargs = dict(a_OutValue=out_value)
    results = cursor.callproc("proc_Test", ("hi", 5), keywordParameters=kwargs)
    assert results == ["hi", 10]
    assert out_value.getvalue() == 2.0


def test_4111(cursor, test_env):
    "4111 - test callproc with setinputsizes"
    test_env.skip_unless_server_version(12, 2)
    out_value = cursor.var(oracledb.DB_TYPE_BOOLEAN)
    cursor.setinputsizes(
        oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_NUMBER, out_value
    )
    results = cursor.callproc("proc_Test2", ("hi", 5, out_value))
    assert results == ["hi", 10, True]
    assert out_value.getvalue()


def test_4112(cursor):
    "4112 - test callfunc with setinputsizes"
    cursor.setinputsizes(
        oracledb.DB_TYPE_NUMBER,
        oracledb.DB_TYPE_VARCHAR,
        oracledb.DB_TYPE_NUMBER,
        oracledb.DB_TYPE_BOOLEAN,
    )
    results = cursor.callfunc("func_Test2", oracledb.NUMBER, ("hi", 5, True))
    assert results == 7


def test_4113(cursor, test_env):
    "4113 - test callproc with setinputsizes with kwargs"
    test_env.skip_unless_server_version(12, 2)
    out_value = cursor.var(oracledb.DB_TYPE_BOOLEAN)
    cursor.setinputsizes(
        oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_NUMBER, out_value
    )
    kwargs = dict(a_OutValue=out_value)
    results = cursor.callproc("proc_Test2", ("hi", 5), kwargs)
    assert results == ["hi", 10]
    assert out_value.getvalue()

    out_value = cursor.var(oracledb.DB_TYPE_BOOLEAN)
    cursor.setinputsizes(
        oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_NUMBER, out_value
    )
    kwargs = dict(a_InValue="hi", a_InOutValue=5, a_OutValue=out_value)
    results = cursor.callproc("proc_Test2", [], kwargs)
    assert results == []
    assert out_value.getvalue()

    cursor.setinputsizes(
        oracledb.DB_TYPE_VARCHAR,
        oracledb.DB_TYPE_NUMBER,
        oracledb.DB_TYPE_BOOLEAN,
    )
    kwargs = dict(a_InValue="hi", a_InOutValue=5, a_OutValue=out_value)
    results = cursor.callproc("proc_Test2", [], kwargs)
    assert results == []
    assert out_value.getvalue()


def test_4114(cursor, test_env):
    "4114 - test callproc with setinputsizes with kwargs in mixed order"
    out_value = cursor.var(oracledb.DB_TYPE_BOOLEAN)
    cursor.setinputsizes(
        oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_NUMBER, out_value
    )
    kwargs = dict(a_OutValue=out_value, a_InValue="hi", a_InOutValue=5)
    with test_env.assert_raises_full_code("ORA-06550"):
        results = cursor.callproc("proc_Test2", keyword_parameters=kwargs)
        assert results == []
        assert out_value.getvalue()

    cursor.setinputsizes(
        oracledb.DB_TYPE_VARCHAR,
        oracledb.DB_TYPE_NUMBER,
        oracledb.DB_TYPE_BOOLEAN,
    )
    with test_env.assert_raises_full_code("ORA-06550"):
        cursor.callproc("proc_Test2", keyword_parameters=kwargs)


def test_4115(cursor):
    "4115 - test callfunc with setinputsizes with kwargs"
    extra_amount = cursor.var(oracledb.DB_TYPE_NUMBER)
    extra_amount.setvalue(0, 5)
    test_values = [
        (["hi"], dict(a_ExtraAmount=extra_amount, a_Boolean=True)),
        (
            [],
            dict(a_String="hi", a_ExtraAmount=extra_amount, a_Boolean=True),
        ),
    ]
    for args, kwargs in test_values:
        cursor.setinputsizes(
            oracledb.DB_TYPE_NUMBER,
            oracledb.DB_TYPE_VARCHAR,
            oracledb.DB_TYPE_NUMBER,
            oracledb.DB_TYPE_BOOLEAN,
        )
        results = cursor.callfunc(
            "func_Test2", oracledb.DB_TYPE_NUMBER, args, kwargs
        )
        assert results == 7


def test_4116(cursor, test_env):
    "4116 - test callproc with setinputsizes with extra arguments"
    out_value = cursor.var(oracledb.DB_TYPE_BOOLEAN)
    test_values = [
        (("hi", 5, out_value), None),
        (("hi",), dict(a_InOutValue=5, a_OutValue=out_value)),
        ([], dict(a_InValue="hi", a_InOutValue=5, a_OutValue=out_value)),
    ]
    for args, kwargs in test_values:
        cursor.setinputsizes(
            oracledb.DB_TYPE_VARCHAR,
            oracledb.NUMBER,
            out_value,
            oracledb.DB_TYPE_VARCHAR,  # extra argument
        )
        with test_env.assert_raises_full_code("ORA-01036", "DPY-4009"):
            cursor.callproc("proc_Test2", args, kwargs)


def test_4117(cursor, test_env):
    "4117 - test callfunc with setinputsizes with extra arguments"
    extra_amount = cursor.var(oracledb.DB_TYPE_NUMBER)
    extra_amount.setvalue(0, 5)
    test_values = [
        (["hi", extra_amount], None),
        (["hi"], dict(a_ExtraAmount=extra_amount)),
        ([], dict(a_ExtraAmount=extra_amount, a_String="hi")),
    ]
    for args, kwargs in test_values:
        cursor.setinputsizes(
            oracledb.DB_TYPE_NUMBER,
            oracledb.DB_TYPE_VARCHAR,
            oracledb.DB_TYPE_NUMBER,
            oracledb.DB_TYPE_BOOLEAN,
            oracledb.DB_TYPE_VARCHAR,  # extra argument
        )
        with test_env.assert_raises_full_code("ORA-01036", "DPY-4009"):
            cursor.callfunc(
                "func_Test2", oracledb.DB_TYPE_NUMBER, args, kwargs
            )


def test_4118(cursor, test_env):
    "4118 - test callproc with setinputsizes with too few parameters"
    test_env.skip_unless_server_version(12, 2)
    out_value = cursor.var(oracledb.DB_TYPE_BOOLEAN)

    # setinputsizes for 2 args (missed 1 args)
    cursor.setinputsizes(oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_NUMBER)
    results = cursor.callproc("proc_Test2", ("hi", 5, out_value))
    assert results == ["hi", 10, out_value.getvalue()]
    assert out_value.getvalue()

    # setinputsizes for 2 args (missed 1 kwargs)
    cursor.setinputsizes(oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_NUMBER)
    kwargs = dict(a_OutValue=out_value)
    results = cursor.callproc("proc_Test2", ("hi", 5), kwargs)
    assert results == ["hi", 10]
    assert out_value.getvalue()

    # setinputsizes for 1 args (missed 2 args)
    cursor.setinputsizes(oracledb.DB_TYPE_VARCHAR)
    results = cursor.callproc("proc_Test2", ("hi", 5, out_value))
    assert results == ["hi", 10, out_value.getvalue()]
    assert out_value.getvalue()

    # setinputsizes for 1 args (missed 1 args and 1 kwargs)
    cursor.setinputsizes(oracledb.DB_TYPE_VARCHAR)
    kwargs = dict(a_OutValue=out_value)
    results = cursor.callproc("proc_Test2", ("hi", 5), kwargs)
    assert results == ["hi", 10]
    assert out_value.getvalue()

    # setinputsizes for 2 kwargs (missed 1 kwargs)
    cursor.setinputsizes(oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_NUMBER)
    kwargs = dict(a_InValue="hi", a_InOutValue=5, a_OutValue=out_value)
    results = cursor.callproc("proc_Test2", [], kwargs)
    assert results == []
    assert out_value.getvalue()


def test_4119(cursor, test_env):
    """
    4119 - test callproc with setinputsizes with wrong order of parameters
    """
    # setinputsizes for 2 args (missed 1 kwargs)
    out_value = cursor.var(oracledb.DB_TYPE_BOOLEAN)
    cursor.setinputsizes(bool, oracledb.DB_TYPE_VARCHAR)
    kwargs = dict(a_OutValue=out_value)
    with test_env.assert_raises_full_code("ORA-06550"):
        cursor.callproc("proc_Test2", ["hi", 5], kwargs)

    # setinputsizes for 2 kwargs (missed 1 kwargs)
    cursor.setinputsizes(bool, oracledb.DB_TYPE_VARCHAR)
    kwargs = dict(a_InValue="hi", a_InOutValue=5, a_OutValue=out_value)
    with test_env.assert_raises_full_code("ORA-06550"):
        cursor.callproc("proc_Test2", [], kwargs)


def test_4120(cursor):
    "4120 - test callfunc with setinputsizes with too few parameters"
    # setinputsizes for return_type and 1 kwargs (missed 2 kwargs)
    bool_var = cursor.var(oracledb.DB_TYPE_BOOLEAN)
    bool_var.setvalue(0, False)
    kwargs = dict(a_Boolean=bool_var, a_String="hi", a_ExtraAmount=3)
    cursor.setinputsizes(oracledb.NUMBER, oracledb.DB_TYPE_VARCHAR)
    results = cursor.callfunc("func_Test2", oracledb.NUMBER, [], kwargs)
    assert results == -1

    # setinputsizes for return_type (missed 3 kwargs)
    bool_var.setvalue(0, False)
    kwargs = dict(a_Boolean=bool_var, a_String="hi", a_ExtraAmount=1)
    cursor.setinputsizes(oracledb.NUMBER)
    results = cursor.callfunc("func_Test2", oracledb.NUMBER, [], kwargs)
    assert results == 1

    # setinputsizes for return_type (missed 3 args)
    bool_var.setvalue(0, True)
    cursor.setinputsizes(oracledb.NUMBER)
    results = cursor.callfunc(
        "func_Test2", oracledb.NUMBER, ["hi", 2, bool_var]
    )
    assert results == 4


def test_4121(cursor, test_env):
    "4121 - test callfunc with setinputsizes with wrong order of parameters"
    # setinputsizes for 2 args (missed 2 kwargs)
    bool_var = cursor.var(oracledb.DB_TYPE_BOOLEAN)
    bool_var.setvalue(0, True)
    cursor.setinputsizes(oracledb.NUMBER, oracledb.DB_TYPE_BOOLEAN)
    kwargs = dict(a_Boolean=bool_var)
    with test_env.assert_raises_full_code("ORA-06550"):
        cursor.callfunc(
            "func_Test2", oracledb.NUMBER, ["hi", bool_var], kwargs
        )


def test_4122(cursor, test_env):
    "4122 - test callfunc with setinputsizes without type for return_type"
    # setinputsizes for 1 args and 1 kwargs
    bool_var = cursor.var(oracledb.DB_TYPE_BOOLEAN)
    bool_var.setvalue(0, False)
    cursor.setinputsizes(oracledb.NUMBER, oracledb.DB_TYPE_BOOLEAN)
    kwargs = dict(a_Boolean=bool_var)
    with test_env.assert_raises_full_code("ORA-06550"):
        cursor.callfunc("func_Test2", oracledb.DB_TYPE_NUMBER, ["hi"], kwargs)

    # setinputsizes for 2 kwargs (missed 1 kwargs)
    bool_var.setvalue(0, False)
    kwargs = dict(a_Boolean=bool_var, a_String="hi", a_ExtraAmount=0)
    cursor.setinputsizes(oracledb.DB_TYPE_BOOLEAN, oracledb.DB_TYPE_VARCHAR)
    results = cursor.callfunc(
        "func_Test2", oracledb.DB_TYPE_NUMBER, [], kwargs
    )
    assert results == 2

    # setinputsizes for 2 args and 1 kwargs
    bool_var.setvalue(0, False)
    cursor.setinputsizes(oracledb.DB_TYPE_BOOLEAN, oracledb.DB_TYPE_NUMBER)
    kwargs = dict(a_Boolean=bool_var)
    results = cursor.callfunc(
        "func_Test2", oracledb.DB_TYPE_NUMBER, ["Bye", 2], kwargs
    )
    assert results == 1

    # setinputsizes for 2 args (missed 1 args)
    bool_var.setvalue(0, False)
    cursor.setinputsizes(oracledb.DB_TYPE_BOOLEAN, oracledb.DB_TYPE_NUMBER)
    kwargs = dict(a_Boolean=bool_var)
    results = cursor.callfunc(
        "func_Test2", oracledb.DB_TYPE_NUMBER, ["Light", -1, bool_var]
    )
    assert results == 6


def test_4123(cursor, test_env):
    "4123 - test executing a procedure with callfunc"
    with test_env.assert_raises_full_code("ORA-06550"):
        cursor.callfunc("proc_Test2", oracledb.NUMBER, ("hello", 3, False))


def test_4124(cursor, test_env):
    "4124 - test executing a function with callproc"
    with test_env.assert_raises_full_code("ORA-06550"):
        cursor.callproc("func_Test2", ("hello", 5, True))


def test_4125(cursor):
    "4125 - test calling a procedure with a string > 32767 characters"
    data = "4125" * 16000
    size_var = cursor.var(int)
    cursor.callproc("pkg_TestLobs.GetSize", [data, size_var])
    assert size_var.getvalue() == len(data)


def test_4126(cursor):
    "4125 - test calling a procedure with raw data > 32767 bytes"
    data = b"4126" * 16250
    size_var = cursor.var(int)
    cursor.callproc("pkg_TestLobs.GetSize", [data, size_var])
    assert size_var.getvalue() == len(data)
