# -----------------------------------------------------------------------------
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
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
7100 - Module for testing interval year to month variables
"""

import oracledb
import pytest


@pytest.fixture(scope="module")
def module_data():
    data = []
    for i in range(1, 11):
        delta = oracledb.IntervalYM(i - 5, -i if i - 5 < 0 else i)
        if i % 2 == 0:
            nullable_delta = None
        else:
            nullable_delta = oracledb.IntervalYM(i + 5, i + 2)
        precision_col = oracledb.IntervalYM(3, 8)
        data_tuple = (i, delta, nullable_delta, precision_col)
        data.append(data_tuple)
    return data


@pytest.fixture(scope="module")
def module_data_by_key(module_data):
    data_by_key = {}
    for row in module_data:
        data_by_key[row[0]] = row
    return data_by_key


def test_7100(cursor, module_data_by_key):
    "7100 - test binding in an interval"
    value = oracledb.IntervalYM(1, 6)
    cursor.execute(
        "select * from TestIntervalYMs where IntervalCol = :value",
        value=value,
    )
    assert cursor.fetchall() == [module_data_by_key[6]]


def test_7101(cursor):
    "7101 - test binding in a null"
    cursor.setinputsizes(value=oracledb.DB_TYPE_INTERVAL_YM)
    cursor.execute(
        "select * from TestIntervalYMs where IntervalCol = :value",
        value=None,
    )
    assert cursor.fetchall() == []


def test_7102(cursor):
    "7102 - test binding out with set input sizes defined"
    bind_vars = cursor.setinputsizes(value=oracledb.DB_TYPE_INTERVAL_YM)
    cursor.execute(
        """
        begin
            :value := to_yminterval('-25-7');
        end;
        """
    )
    expected_value = oracledb.IntervalYM(years=-25, months=-7)
    assert bind_vars["value"].getvalue() == expected_value


def test_7103(cursor):
    "7103 - test binding in/out with set input sizes defined"
    bind_vars = cursor.setinputsizes(value=oracledb.DB_TYPE_INTERVAL_YM)
    cursor.execute(
        """
        begin
            :value := :value + to_yminterval('3-8');
        end;
        """,
        value=oracledb.IntervalYM(years=8, months=4),
    )
    expected_value = oracledb.IntervalYM(years=12, months=0)
    assert bind_vars["value"].getvalue() == expected_value


def test_7104(cursor):
    "7104 - test binding out with cursor.var() method"
    var = cursor.var(oracledb.DB_TYPE_INTERVAL_YM)
    cursor.execute(
        """
        begin
            :value := to_yminterval('1-9');
        end;
        """,
        value=var,
    )
    expected_value = oracledb.IntervalYM(years=1, months=9)
    assert var.getvalue() == expected_value


def test_7105(cursor):
    "7105 - test binding in/out with cursor.var() method"
    var = cursor.var(oracledb.DB_TYPE_INTERVAL_YM)
    var.setvalue(0, oracledb.IntervalYM(years=3, months=10))
    cursor.execute(
        """
        begin
            :value := :value + to_yminterval('2-5');
        end;
        """,
        value=var,
    )
    expected_value = oracledb.IntervalYM(years=6, months=3)
    assert var.getvalue() == expected_value


def test_7106(cursor):
    "7106 - test cursor description is accurate"
    cursor.execute("select * from TestIntervalYMs")
    expected_value = [
        ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
        (
            "INTERVALCOL",
            oracledb.DB_TYPE_INTERVAL_YM,
            None,
            None,
            2,
            0,
            False,
        ),
        (
            "NULLABLECOL",
            oracledb.DB_TYPE_INTERVAL_YM,
            None,
            None,
            2,
            0,
            True,
        ),
        (
            "INTERVALPRECISIONCOL",
            oracledb.DB_TYPE_INTERVAL_YM,
            None,
            None,
            3,
            0,
            True,
        ),
    ]
    assert cursor.description == expected_value


def test_7107(cursor, module_data):
    "7107 - test that fetching all of the data returns the correct results"
    cursor.execute("select * From TestIntervalYMs order by IntCol")
    assert cursor.fetchall() == module_data
    assert cursor.fetchall() == []


def test_7108(cursor, module_data):
    "7108 - test that fetching data in chunks returns the correct results"
    cursor.execute("select * From TestIntervalYMs order by IntCol")
    assert cursor.fetchmany(3) == module_data[0:3]
    assert cursor.fetchmany(2) == module_data[3:5]
    assert cursor.fetchmany(4) == module_data[5:9]
    assert cursor.fetchmany(3) == module_data[9:]
    assert cursor.fetchmany(3) == []


def test_7109(cursor, module_data_by_key):
    "7109 - test that fetching a single row returns the correct results"
    cursor.execute(
        """
        select *
        from TestIntervalYMs
        where IntCol in (3, 4)
        order by IntCol
        """
    )
    assert cursor.fetchone() == module_data_by_key[3]
    assert cursor.fetchone() == module_data_by_key[4]
    assert cursor.fetchone() is None


def test_7110(cursor):
    "7110 - test binding and fetching a negative interval"
    value = oracledb.IntervalYM(years=-12, months=-5)
    cursor.execute("select :1 from dual", [value])
    (result,) = cursor.fetchone()
    assert result == value
