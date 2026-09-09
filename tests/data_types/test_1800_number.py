# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2026, Oracle and/or its affiliates.
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
Module for testing number variables
"""

import decimal

import oracledb
import pytest


@pytest.fixture(scope="module")
def module_data():
    data = []
    for i in range(1, 11):
        number_col = i + i * 0.25
        float_col = i + i * 0.75
        unconstrained_col = i**3 + i * 0.5
        if i % 2:
            nullable_col = 143**i
        else:
            nullable_col = None
        data_tuple = (
            i,
            38**i,
            number_col,
            float_col,
            unconstrained_col,
            nullable_col,
        )
        data.append(data_tuple)
    return data


@pytest.fixture(scope="module")
def module_data_by_key(module_data):
    data_by_key = {}
    for row in module_data:
        data_by_key[row[0]] = row
    return data_by_key


def output_type_handler_binary_int(cursor, metadata):
    return cursor.var(
        oracledb.DB_TYPE_BINARY_INTEGER, arraysize=cursor.arraysize
    )


def output_type_handler_decimal(cursor, metadata):
    if metadata.type_code is oracledb.DB_TYPE_NUMBER:
        return cursor.var(
            str,
            255,
            outconverter=decimal.Decimal,
            arraysize=cursor.arraysize,
        )


def output_type_handler_str(cursor, metadata):
    return cursor.var(str, 255, arraysize=cursor.arraysize)


def test_data_types_1800(skip_unless_plsql_boolean_supported, cursor):
    "1800 - test binding in a boolean"
    result = cursor.callfunc("pkg_TestBooleans.GetStringRep", str, [True])
    assert result == "TRUE"


def test_data_types_1801(cursor):
    "1801 - test binding in a boolean as a number"
    var = cursor.var(oracledb.NUMBER)
    var.setvalue(0, True)
    cursor.execute("select :1 from dual", [var])
    (result,) = cursor.fetchone()
    assert result == 1
    var.setvalue(0, False)
    cursor.execute("select :1 from dual", [var])
    (result,) = cursor.fetchone()
    assert result == 0


def test_data_types_1802(cursor, module_data_by_key):
    "1802 - test binding in a decimal.Decimal"
    cursor.execute(
        """
        select *
        from TestNumbers
        where NumberCol - :value1 - :value2 = trunc(NumberCol)
        """,
        value1=decimal.Decimal("0.20"),
        value2=decimal.Decimal("0.05"),
    )
    expected_data = [
        module_data_by_key[1],
        module_data_by_key[5],
        module_data_by_key[9],
    ]
    assert cursor.fetchall() == expected_data


def test_data_types_1803(cursor, module_data_by_key):
    "1803 - test binding in a float"
    cursor.execute(
        """
        select *
        from TestNumbers
        where NumberCol - :value = trunc(NumberCol)
        """,
        value=0.25,
    )
    expected_data = [
        module_data_by_key[1],
        module_data_by_key[5],
        module_data_by_key[9],
    ]
    assert cursor.fetchall() == expected_data


def test_data_types_1804(cursor, module_data_by_key):
    "1804 - test binding in an integer"
    cursor.execute(
        "select * from TestNumbers where IntCol = :value",
        value=2,
    )
    assert cursor.fetchall() == [module_data_by_key[2]]


def test_data_types_1805(cursor):
    "1805 - test binding in a large long integer as Oracle number"
    in_val = 6088343244
    value_var = cursor.var(oracledb.NUMBER)
    value_var.setvalue(0, in_val)
    cursor.execute(
        """
        begin
            :value := :value + 5;
        end;
        """,
        value=value_var,
    )
    assert value_var.getvalue() == in_val + 5


def test_data_types_1806(cursor):
    "1806 - test binding in a large long integer as Python integer"
    long_value = -9999999999999999999
    cursor.execute("select :value from dual", value=long_value)
    (result,) = cursor.fetchone()
    assert result == long_value


def test_data_types_1807(cursor, module_data_by_key):
    "1807 - test binding in an integer after setting input sizes to string"
    cursor.setinputsizes(value=15)
    cursor.execute(
        "select * from TestNumbers where IntCol = :value",
        value=3,
    )
    assert cursor.fetchall() == [module_data_by_key[3]]


def test_data_types_1808(cursor):
    "1808 - test binding in a decimal after setting input sizes to number"
    value = decimal.Decimal("319438950232418390.273596")
    cursor.setinputsizes(value=oracledb.NUMBER)
    cursor.outputtypehandler = output_type_handler_decimal
    cursor.execute("select :value from dual", value=value)
    (out_value,) = cursor.fetchone()
    assert out_value == value


def test_data_types_1809(cursor):
    "1809 - test binding in a null"
    cursor.execute(
        "select * from TestNumbers where IntCol = :value",
        value=None,
    )
    assert cursor.fetchall() == []


def test_data_types_1810(cursor, module_data):
    "1810 - test binding in a number array"
    return_value = cursor.var(oracledb.NUMBER)
    array = [r[2] for r in module_data]
    statement = """
            begin
                :return_value := pkg_TestNumberArrays.TestInArrays(
                    :start_value, :array);
            end;"""
    cursor.execute(
        statement, return_value=return_value, start_value=5, array=array
    )
    assert return_value.getvalue() == 73.75
    array = list(range(15))
    cursor.execute(statement, start_value=10, array=array)
    assert return_value.getvalue() == 115.0


def test_data_types_1811(cursor, module_data):
    "1811 - test binding in a number array (with setinputsizes)"
    return_value = cursor.var(oracledb.NUMBER)
    cursor.setinputsizes(array=[oracledb.NUMBER, 10])
    array = [r[2] for r in module_data]
    cursor.execute(
        """
        begin
            :return_value := pkg_TestNumberArrays.TestInArrays(
                :start_value, :array);
        end;
        """,
        return_value=return_value,
        start_value=6,
        array=array,
    )
    assert return_value.getvalue() == 74.75


def test_data_types_1812(cursor, module_data):
    "1812 - test binding in a number array (with arrayvar)"
    return_value = cursor.var(oracledb.NUMBER)
    array = cursor.arrayvar(oracledb.NUMBER, [r[2] for r in module_data])
    cursor.execute(
        """
        begin
            :return_value := pkg_TestNumberArrays.TestInArrays(
                :integer_value, :array);
        end;
        """,
        return_value=return_value,
        integer_value=7,
        array=array,
    )
    assert return_value.getvalue() == 75.75


def test_data_types_1813(cursor):
    "1813 - test binding in a zero length number array (with arrayvar)"
    return_value = cursor.var(oracledb.NUMBER)
    array = cursor.arrayvar(oracledb.NUMBER, 0)
    cursor.execute(
        """
        begin
            :return_value := pkg_TestNumberArrays.TestInArrays(
                :integer_value, :array);
        end;
        """,
        return_value=return_value,
        integer_value=8,
        array=array,
    )
    assert return_value.getvalue() == 8.0
    assert array.getvalue() == []


def test_data_types_1814(cursor, module_data):
    "1814 - test binding in/out a number array (with arrayvar)"
    array = cursor.arrayvar(oracledb.NUMBER, 10)
    original_data = [r[2] for r in module_data]
    expected_data = [
        original_data[i - 1] * 10 for i in range(1, 6)
    ] + original_data[5:]
    array.setvalue(0, original_data)
    cursor.execute(
        """
        begin
            pkg_TestNumberArrays.TestInOutArrays(:num_elems, :array);
        end;
        """,
        num_elems=5,
        array=array,
    )
    assert array.getvalue() == expected_data


def test_data_types_1815(cursor):
    "1815 - test binding out a Number array (with arrayvar)"
    array = cursor.arrayvar(oracledb.NUMBER, 6)
    expected_data = [i * 100 for i in range(1, 7)]
    cursor.execute(
        """
        begin
            pkg_TestNumberArrays.TestOutArrays(:num_elems, :array);
        end;
        """,
        num_elems=6,
        array=array,
    )
    assert array.getvalue() == expected_data


def test_data_types_1816(cursor):
    "1816 - test binding out with set input sizes defined"
    bind_vars = cursor.setinputsizes(value=oracledb.NUMBER)
    cursor.execute("""
        begin
            :value := 5;
        end;
        """)
    assert bind_vars["value"].getvalue() == 5


def test_data_types_1817(cursor):
    "1817 - test binding in/out with set input sizes defined"
    bind_vars = cursor.setinputsizes(value=oracledb.NUMBER)
    cursor.execute(
        """
        begin
            :value := :value + 5;
        end;
        """,
        value=1.25,
    )
    assert bind_vars["value"].getvalue() == 6.25


def test_data_types_1818(cursor):
    "1818 - test binding out with cursor.var() method"
    var = cursor.var(oracledb.NUMBER)
    cursor.execute(
        """
        begin
            :value := 5;
        end;
        """,
        value=var,
    )
    assert var.getvalue() == 5


def test_data_types_1819(cursor):
    "1819 - test binding in/out with cursor.var() method"
    var = cursor.var(oracledb.NUMBER)
    var.setvalue(0, 2.25)
    cursor.execute(
        """
        begin
            :value := :value + 5;
        end;
        """,
        value=var,
    )
    assert var.getvalue() == 7.25


def test_data_types_1820(cursor):
    "1820 - test cursor description is accurate"
    cursor.execute("select * from TestNumbers")
    expected_value = [
        ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
        ("LONGINTCOL", oracledb.DB_TYPE_NUMBER, 17, None, 16, 0, False),
        ("NUMBERCOL", oracledb.DB_TYPE_NUMBER, 13, None, 9, 2, False),
        ("FLOATCOL", oracledb.DB_TYPE_NUMBER, 127, None, 126, -127, False),
        (
            "UNCONSTRAINEDCOL",
            oracledb.DB_TYPE_NUMBER,
            127,
            None,
            0,
            -127,
            False,
        ),
        ("NULLABLECOL", oracledb.DB_TYPE_NUMBER, 39, None, 38, 0, True),
    ]
    assert cursor.description == expected_value


def test_data_types_1821(cursor, module_data):
    "1821 - test that fetching all of the data returns the correct results"
    cursor.execute("select * From TestNumbers order by IntCol")
    assert cursor.fetchall() == module_data
    assert cursor.fetchall() == []


def test_data_types_1822(cursor, module_data):
    "1822 - test that fetching data in chunks returns the correct results"
    cursor.execute("select * From TestNumbers order by IntCol")
    assert cursor.fetchmany(3) == module_data[0:3]
    assert cursor.fetchmany(2) == module_data[3:5]
    assert cursor.fetchmany(4) == module_data[5:9]
    assert cursor.fetchmany(3) == module_data[9:]
    assert cursor.fetchmany(3) == []


def test_data_types_1823(cursor, module_data_by_key):
    "1823 - test that fetching a single row returns the correct results"
    cursor.execute("""
        select *
        from TestNumbers
        where IntCol in (3, 4)
        order by IntCol
        """)
    assert cursor.fetchone() == module_data_by_key[3]
    assert cursor.fetchone() == module_data_by_key[4]
    assert cursor.fetchone() is None


def test_data_types_1824(cursor):
    "1824 - test that fetching a long integer returns such in Python"
    cursor.execute("""
        select NullableCol
        from TestNumbers
        where IntCol = 9
        """)
    (col,) = cursor.fetchone()
    assert col == 25004854810776297743


def test_data_types_1825(cursor):
    "1825 - test fetching a floating point number returns such in Python"
    cursor.execute("select 1.25 from dual")
    (result,) = cursor.fetchone()
    assert result == 1.25


def test_data_types_1826(cursor):
    "1826 - test that fetching an integer returns such in Python"
    cursor.execute("select 148 from dual")
    (result,) = cursor.fetchone()
    assert result == 148
    assert isinstance(result, int)


def test_data_types_1827(cursor):
    "1827 - test that acceptable boundary numbers are handled properly"
    in_values = [
        decimal.Decimal("9.99999999999999e+125"),
        decimal.Decimal("-9.99999999999999e+125"),
        0.0,
        1e-130,
        -1e-130,
    ]
    out_values = [
        int("9" * 15 + "0" * 111),
        -int("9" * 15 + "0" * 111),
        0,
        1e-130,
        -1e-130,
    ]
    for in_value, out_value in zip(in_values, out_values):
        cursor.execute("select :1 from dual", [in_value])
        (result,) = cursor.fetchone()
        assert result == out_value


def test_data_types_1828(cursor, test_env):
    "1828 - test that unacceptable boundary numbers are rejected"
    test_values = [
        (1e126, "DPY-4003"),
        (-1e126, "DPY-4003"),
        (float("inf"), "DPY-4004"),
        (float("-inf"), "DPY-4004"),
        (float("NaN"), "DPY-4004"),
        (decimal.Decimal("1e126"), "DPY-4003"),
        (decimal.Decimal("-1e126"), "DPY-4003"),
        (decimal.Decimal("inf"), "DPY-4004"),
        (decimal.Decimal("-inf"), "DPY-4004"),
        (decimal.Decimal("NaN"), "DPY-4004"),
    ]
    for value, error in test_values:
        with test_env.assert_raises_full_code(error):
            cursor.execute("select :1 from dual", [value])


def test_data_types_1829(cursor):
    "1829 - test that fetching the result of division returns a float"
    cursor.execute("""
        select IntCol / 7
        from TestNumbers
        where IntCol = 1
        """)
    (result,) = cursor.fetchone()
    assert result == 1.0 / 7.0
    assert isinstance(result, float)


def test_data_types_1830(cursor):
    "1830 - test that string format is returned properly"
    var = cursor.var(oracledb.NUMBER)
    assert var.type is oracledb.DB_TYPE_NUMBER
    assert str(var) == "<oracledb.Var of type DB_TYPE_NUMBER with value None>"
    var.setvalue(0, 4.5)
    assert str(var) == "<oracledb.Var of type DB_TYPE_NUMBER with value 4.5>"


def test_data_types_1831(cursor):
    "1831 - test that binding binary double is possible"
    statement = "select :1 from dual"
    cursor.setinputsizes(oracledb.DB_TYPE_BINARY_DOUBLE)
    cursor.execute(statement, (5,))
    assert cursor.bindvars[0].type == oracledb.DB_TYPE_BINARY_DOUBLE
    (value,) = cursor.fetchone()
    assert value == 5

    cursor.execute(statement, (1.5,))
    assert cursor.bindvars[0].type == oracledb.DB_TYPE_BINARY_DOUBLE
    (value,) = cursor.fetchone()
    assert value == 1.5

    cursor.execute(statement, [decimal.Decimal("NaN")])
    assert cursor.bindvars[0].type == oracledb.DB_TYPE_BINARY_DOUBLE
    (value,) = cursor.fetchone()
    assert str(value) == str(float("NaN"))


def test_data_types_1832(cursor):
    "1832 - test fetching numbers as binary integers"
    cursor.outputtypehandler = output_type_handler_binary_int
    for value in (1, 2**31, 2**63 - 1, -1, -(2**31), -(2**63) + 1):
        cursor.execute("select :1 from dual", [str(value)])
        (fetched_value,) = cursor.fetchone()
        assert value == fetched_value


def test_data_types_1833(cursor):
    "1833 - test binding native integer as an out bind"
    simple_var = cursor.var(oracledb.DB_TYPE_BINARY_INTEGER)
    cursor.execute("begin :value := 2.9; end;", [simple_var])
    assert simple_var.getvalue() == 2

    simple_var = cursor.var(oracledb.DB_TYPE_BINARY_INTEGER)
    cursor.execute("begin :value := 1.5; end;", [simple_var])
    assert simple_var.getvalue() == 1


def test_data_types_1834(cursor):
    "1834 - test binding in a native integer"
    statement = "begin :value := :value + 2.5; end;"
    simple_var = cursor.var(oracledb.DB_TYPE_BINARY_INTEGER)
    simple_var.setvalue(0, 0)
    cursor.execute(statement, [simple_var])
    assert simple_var.getvalue() == 2

    simple_var.setvalue(0, -5)
    cursor.execute(statement, [simple_var])
    assert simple_var.getvalue() == -2


def test_data_types_1835(cursor):
    "1835 - test setting decimal value for binary int"
    simple_var = cursor.var(oracledb.DB_TYPE_BINARY_INTEGER)
    simple_var.setvalue(0, 2.5)
    cursor.execute("begin :value := :value + 2.5; end;", [simple_var])
    assert simple_var.getvalue() == 4


def test_data_types_1836(cursor):
    "1836 - bind a large value to binary int"
    simple_var = cursor.var(oracledb.DB_TYPE_BINARY_INTEGER)
    cursor.execute("begin :value := POWER(2, 31) - 1; end;", [simple_var])
    assert simple_var.getvalue() == 2**31 - 1

    cursor.execute("begin :value := POWER(-2, 31) - 1; end;", [simple_var])
    assert simple_var.getvalue() == -(2**31) - 1


def test_data_types_1837(cursor, disable_fetch_lobs):
    "1837 - fetch a number with oracledb.defaults.fetch_lobs = False"
    cursor.execute("select 1 from dual")
    (result,) = cursor.fetchone()
    assert isinstance(result, int)


def test_data_types_1838(cursor):
    "1838 - fetch a small constant with a decimal point"
    cursor.outputtypehandler = output_type_handler_str
    cursor.execute("select 3 / 2 from dual")
    (result,) = cursor.fetchone()
    assert len(result) == 3
    assert result[0] == "1"
    assert result[2] == "5"
