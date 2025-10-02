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
2100 - Module for testing NCHAR variables
"""

import oracledb
import pytest


@pytest.fixture(scope="module")
def module_data():
    data = []
    for i in range(1, 11):
        unicode_col = f"Unicode \u3042 {i}"
        fixed_char_col = f"Fixed Unicode {i}".ljust(40)
        if i % 2:
            nullable_col = f"Nullable {i}"
        else:
            nullable_col = None
        data_tuple = (i, unicode_col, fixed_char_col, nullable_col)
        data.append(data_tuple)
    return data


@pytest.fixture(scope="module")
def module_data_by_key(module_data):
    data_by_key = {}
    for row in module_data:
        data_by_key[row[0]] = row
    return data_by_key


def test_2100(cursor):
    "2100 - test value length"
    return_value = cursor.var(int)
    cursor.execute(
        """
        begin
            :retval := LENGTH(:value);
        end;
        """,
        value="InVal \u3042",
        retval=return_value,
    )
    assert return_value.getvalue() == 7


def test_2101(cursor, module_data_by_key):
    "2101 - test binding in a unicode"
    cursor.setinputsizes(value=oracledb.DB_TYPE_NVARCHAR)
    cursor.execute(
        "select * from TestUnicodes where UnicodeCol = :value",
        value="Unicode \u3042 5",
    )
    assert cursor.fetchall() == [module_data_by_key[5]]


def test_2102(cursor):
    "2102 - test binding a different variable on second execution"
    retval_1 = cursor.var(oracledb.DB_TYPE_NVARCHAR, 30)
    retval_2 = cursor.var(oracledb.DB_TYPE_NVARCHAR, 30)
    cursor.execute(
        r"begin :retval := unistr('Called \3042'); end;", retval=retval_1
    )
    assert retval_1.getvalue() == "Called \u3042"
    cursor.execute("begin :retval := 'Called'; end;", retval=retval_2)
    assert retval_2.getvalue() == "Called"


def test_2103(cursor, module_data_by_key):
    "2103 - test binding in a string after setting input sizes to a number"
    unicode_val = cursor.var(oracledb.DB_TYPE_NVARCHAR)
    unicode_val.setvalue(0, "Unicode \u3042 6")
    cursor.setinputsizes(value=oracledb.NUMBER)
    cursor.execute(
        "select * from TestUnicodes where UnicodeCol = :value",
        value=unicode_val,
    )
    assert cursor.fetchall() == [module_data_by_key[6]]


def test_2104(cursor, module_data):
    "2104 - test binding in a unicode array"
    return_value = cursor.var(oracledb.NUMBER)
    array = [r[1] for r in module_data]
    array_var = cursor.arrayvar(oracledb.DB_TYPE_NVARCHAR, array)
    statement = """
            begin
                :retval := pkg_TestUnicodeArrays.TestInArrays(
                    :integer_value, :array);
            end;"""
    cursor.execute(
        statement, retval=return_value, integer_value=5, array=array_var
    )
    assert return_value.getvalue() == 116
    array = [f"Unicode - \u3042 {i}" for i in range(15)]
    array_var = cursor.arrayvar(oracledb.DB_TYPE_NVARCHAR, array)
    cursor.execute(statement, integer_value=8, array=array_var)
    assert return_value.getvalue() == 208


def test_2105(cursor, module_data):
    "2105 - test binding in a unicode array (with setinputsizes)"
    return_value = cursor.var(oracledb.NUMBER)
    cursor.setinputsizes(array=[oracledb.DB_TYPE_NVARCHAR, 10])
    array = [r[1] for r in module_data]
    cursor.execute(
        """
        begin
            :retval := pkg_TestUnicodeArrays.TestInArrays(
                :integer_value, :array);
        end;
        """,
        retval=return_value,
        integer_value=6,
        array=array,
    )
    assert return_value.getvalue() == 117


def test_2106(cursor, module_data):
    "2106 - test binding in a unicode array (with arrayvar)"
    return_value = cursor.var(oracledb.NUMBER)
    array = cursor.arrayvar(oracledb.DB_TYPE_NVARCHAR, 10, 20)
    array.setvalue(0, [r[1] for r in module_data])
    cursor.execute(
        """
        begin
            :retval := pkg_TestUnicodeArrays.TestInArrays(
                :integer_value, :array);
        end;
        """,
        retval=return_value,
        integer_value=7,
        array=array,
    )
    assert return_value.getvalue() == 118


def test_2107(cursor, module_data):
    "2107 - test binding in/out a unicode array (with arrayvar)"
    array = cursor.arrayvar(oracledb.DB_TYPE_NVARCHAR, 10, 100)
    original_data = [r[1] for r in module_data]
    fmt = "Converted element \u3042 # %d originally had length %d"
    expected_data = [
        fmt % (i, len(original_data[i - 1])) for i in range(1, 6)
    ] + original_data[5:]
    array.setvalue(0, original_data)
    cursor.execute(
        """
        begin
            pkg_TestUnicodeArrays.TestInOutArrays(:numElems, :array);
        end;
        """,
        numElems=5,
        array=array,
    )
    assert array.getvalue() == expected_data


def test_2108(cursor):
    "2108 - test binding out a unicode array (with arrayvar)"
    array = cursor.arrayvar(oracledb.DB_TYPE_NVARCHAR, 6, 100)
    fmt = "Test out element \u3042 # %d"
    expected_data = [fmt % i for i in range(1, 7)]
    cursor.execute(
        """
        begin
            pkg_TestUnicodeArrays.TestOutArrays(:numElems, :array);
        end;
        """,
        numElems=6,
        array=array,
    )
    assert array.getvalue() == expected_data


def test_2109(cursor):
    "2109 - test binding in a null"
    cursor.execute(
        "select * from TestUnicodes where UnicodeCol = :value",
        value=None,
    )
    assert cursor.fetchall() == []


def test_2110(cursor):
    "2110 - test binding out with set input sizes defined (by type)"
    bind_vars = cursor.setinputsizes(value=oracledb.DB_TYPE_NVARCHAR)
    cursor.execute(
        r"""
        begin
            :value := unistr('TSI \3042');
        end;
        """
    )
    assert bind_vars["value"].getvalue() == "TSI \u3042"


def test_2111(cursor):
    "2111 - test binding in/out with set input sizes defined (by type)"
    bind_vars = cursor.setinputsizes(value=oracledb.DB_TYPE_NVARCHAR)
    cursor.execute(
        r"""
        begin
            :value := :value || unistr(' TSI \3042');
        end;
        """,
        value="InVal \u3041",
    )
    assert bind_vars["value"].getvalue() == "InVal \u3041 TSI \u3042"


def test_2112(cursor):
    "2112 - test binding out with cursor.var() method"
    var = cursor.var(oracledb.DB_TYPE_NVARCHAR)
    cursor.execute(
        r"""
        begin
            :value := unistr('TSI (VAR) \3042');
        end;
        """,
        value=var,
    )
    assert var.getvalue() == "TSI (VAR) \u3042"


def test_2113(cursor):
    "2113 - test binding in/out with cursor.var() method"
    var = cursor.var(oracledb.DB_TYPE_NVARCHAR)
    var.setvalue(0, "InVal \u3041")
    cursor.execute(
        r"""
        begin
            :value := :value || unistr(' TSI (VAR) \3042');
        end;
        """,
        value=var,
    )
    assert var.getvalue() == "InVal \u3041 TSI (VAR) \u3042"


def test_2114(cursor, test_env):
    "2114 - test cursor description is accurate"
    cursor.execute("select * from TestUnicodes")
    varchar_ratio, nvarchar_ratio = test_env.charset_ratios
    expected_value = [
        ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
        (
            "UNICODECOL",
            oracledb.DB_TYPE_NVARCHAR,
            20,
            20 * nvarchar_ratio,
            None,
            None,
            False,
        ),
        (
            "FIXEDUNICODECOL",
            oracledb.DB_TYPE_NCHAR,
            40,
            40 * nvarchar_ratio,
            None,
            None,
            False,
        ),
        (
            "NULLABLECOL",
            oracledb.DB_TYPE_NVARCHAR,
            50,
            50 * nvarchar_ratio,
            None,
            None,
            True,
        ),
    ]
    assert cursor.description == expected_value


def test_2115(cursor, module_data):
    "2115 - test that fetching all of the data returns the correct results"
    cursor.execute("select * From TestUnicodes order by IntCol")
    assert cursor.fetchall() == module_data
    assert cursor.fetchall() == []


def test_2116(cursor, module_data):
    "2116 - test that fetching data in chunks returns the correct results"
    cursor.execute("select * From TestUnicodes order by IntCol")
    assert cursor.fetchmany(3) == module_data[0:3]
    assert cursor.fetchmany(2) == module_data[3:5]
    assert cursor.fetchmany(4) == module_data[5:9]
    assert cursor.fetchmany(3) == module_data[9:]
    assert cursor.fetchmany(3) == []


def test_2117(cursor, module_data_by_key):
    "2117 - test that fetching a single row returns the correct results"
    cursor.execute(
        """
        select *
        from TestUnicodes
        where IntCol in (3, 4)
        order by IntCol
        """
    )
    assert cursor.fetchone() == module_data_by_key[3]
    assert cursor.fetchone() == module_data_by_key[4]
    assert cursor.fetchone() is None
