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
3100 - Module for testing boolean variables
"""

import oracledb


def _test_bind_value_as_boolean(cursor, value):
    expected_result = str(bool(value)).upper()
    var = cursor.var(bool)
    var.setvalue(0, value)
    result = cursor.callfunc("pkg_TestBooleans.GetStringRep", str, [var])
    assert result == expected_result


def test_3100(skip_unless_plsql_boolean_supported, cursor):
    "3100 - test binding in a False value"
    result = cursor.callfunc("pkg_TestBooleans.GetStringRep", str, [False])
    assert result == "FALSE"


def test_3101(skip_unless_plsql_boolean_supported, cursor):
    "3101 - test binding in a float as a boolean"
    _test_bind_value_as_boolean(cursor, 0.0)
    _test_bind_value_as_boolean(cursor, 1.0)


def test_3102(skip_unless_plsql_boolean_supported, cursor):
    "3102 - test binding in an integer as a boolean"
    _test_bind_value_as_boolean(cursor, 0)
    _test_bind_value_as_boolean(cursor, 1)


def test_3103(skip_unless_plsql_boolean_supported, cursor):
    "3103 - test binding in a null value"
    cursor.setinputsizes(None, bool)
    result = cursor.callfunc("pkg_TestBooleans.GetStringRep", str, [None])
    assert result == "NULL"


def test_3104(skip_unless_plsql_boolean_supported, cursor):
    "3104 - test binding out a boolean value (False)"
    result = cursor.callfunc(
        "pkg_TestBooleans.IsLessThan10", oracledb.DB_TYPE_BOOLEAN, [15]
    )
    assert not result


def test_3105(skip_unless_plsql_boolean_supported, cursor, test_env):
    "3105 - test binding out a boolean value (True)"
    test_env.skip_unless_server_version(12, 2)
    result = cursor.callfunc("pkg_TestBooleans.IsLessThan10", bool, [5])
    assert result


def test_3106(skip_unless_plsql_boolean_supported, cursor):
    "3106 - test binding in a string as a boolean"
    _test_bind_value_as_boolean(cursor, "")
    _test_bind_value_as_boolean(cursor, "0")


def test_3107(skip_unless_plsql_boolean_supported, cursor):
    "3107 - test binding in a True value"
    result = cursor.callfunc("pkg_TestBooleans.GetStringRep", str, [True])
    assert result == "TRUE"


def test_3108(skip_unless_plsql_boolean_supported, cursor):
    "3108 - test binding out a boolean value (None)"
    result = cursor.callfunc("pkg_TestBooleans.TestOutValueNull", bool)
    assert result is None


def test_3109(skip_unless_native_boolean_supported, cursor):
    "3109 - test binding and fetching boolean with Oracle DB version 23"
    for value in (True, False):
        cursor.execute("select not :1 from dual", [value])
        (fetched_value,) = cursor.fetchone()
        assert isinstance(fetched_value, bool)
        assert fetched_value == (not value)


def test_3110(skip_unless_native_boolean_supported, cursor):
    "3110 - test binding and fetching string literals that represent True"
    cursor.execute("truncate table TestBooleans")
    true_values = ["true", "yes", "on", "1", "t", "y"]
    cursor.executemany(
        """insert into TestBooleans (IntCol, BooleanCol1, BooleanCol2)
        values (:1, :2, :3)""",
        [(i, v, v) for i, v in enumerate(true_values)],
    )
    cursor.execute(
        "select BooleanCol1, BooleanCol2 from TestBooleans order by IntCol"
    )
    expected_values = [(True, True) for _ in true_values]
    assert cursor.fetchall() == expected_values


def test_3111(skip_unless_native_boolean_supported, cursor):
    "3111 - test binding and fetching string literals that represent False"
    cursor.execute("truncate table TestBooleans")
    false_values = ["false", "no", "off", "0", "f", "n"]
    cursor.executemany(
        """insert into TestBooleans (IntCol, BooleanCol1, BooleanCol2)
        values (:1, :2, :3)""",
        [(i, v, v) for i, v in enumerate(false_values)],
    )
    cursor.execute(
        "select BooleanCol1, BooleanCol2 from TestBooleans order by IntCol"
    )
    expected_value = [(False, False) for _ in range(len(false_values))]
    assert cursor.fetchall() == expected_value
