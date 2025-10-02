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
1400 - Module for testing date/time variables
"""

import pytest
import datetime

import oracledb


@pytest.fixture(scope="module")
def module_data():
    data = []
    for i in range(1, 11):
        base_date = datetime.datetime(2002, 12, 9)
        date_interval = datetime.timedelta(days=i, hours=i * 2, minutes=i * 24)
        date_col = base_date + date_interval
        if i % 2:
            date_interval = datetime.timedelta(
                days=i * 2, hours=i * 3, minutes=i * 36
            )
            nullable_col = base_date + date_interval
        else:
            nullable_col = None
        data_tuple = (i, date_col, nullable_col)
        data.append(data_tuple)
    return data


@pytest.fixture(scope="module")
def module_data_by_key(module_data):
    data_by_key = {}
    for row in module_data:
        data_by_key[row[0]] = row
    return data_by_key


def test_1400(cursor, module_data_by_key):
    "1400 - test binding in a date"
    cursor.execute(
        "select * from TestDates where DateCol = :value",
        value=datetime.datetime(2002, 12, 13, 9, 36, 0),
    )
    assert cursor.fetchall() == [module_data_by_key[4]]


def test_1401(cursor, module_data_by_key):
    "1401 - test binding in a datetime.datetime value"
    cursor.execute(
        "select * from TestDates where DateCol = :value",
        value=datetime.datetime(2002, 12, 13, 9, 36, 0),
    )
    assert cursor.fetchall() == [module_data_by_key[4]]


def test_1402(cursor):
    "1402 - test binding date in a datetime variable"
    var = cursor.var(oracledb.DATETIME)
    date_val = datetime.date.today()
    var.setvalue(0, date_val)
    cursor.execute("select :1 from dual", [var])
    (result,) = cursor.fetchone()
    assert result.date() == date_val


def test_1403(cursor, module_data_by_key):
    "1403 - test binding in a date after setting input sizes to a string"
    cursor.setinputsizes(value=15)
    cursor.execute(
        "select * from TestDates where DateCol = :value",
        value=datetime.datetime(2002, 12, 14, 12, 0, 0),
    )
    assert cursor.fetchall() == [module_data_by_key[5]]


def test_1404(cursor):
    "1404 - test binding in a null"
    cursor.setinputsizes(value=oracledb.DATETIME)
    cursor.execute(
        "select * from TestDates where DateCol = :value",
        value=None,
    )
    assert cursor.fetchall() == []


def test_1405(cursor, module_data):
    "1405 - test binding in a date array"
    array = [r[1] for r in module_data]
    return_value = cursor.callfunc(
        "pkg_TestDateArrays.TestInArrays",
        oracledb.DB_TYPE_NUMBER,
        [5, datetime.date(2002, 12, 12), array],
    )
    assert return_value == 35.5
    array += array[:5]
    return_value = cursor.callfunc(
        "pkg_TestDateArrays.TestInArrays",
        oracledb.DB_TYPE_NUMBER,
        [7, datetime.date(2002, 12, 13), array],
    )
    assert return_value == 24.0


def test_1406(cursor, module_data):
    "1406 - test binding in a date array (with setinputsizes)"
    return_value = cursor.var(oracledb.NUMBER)
    cursor.setinputsizes(array=[oracledb.DATETIME, 10])
    array = [r[1] for r in module_data]
    cursor.execute(
        """
        begin
            :return_value := pkg_TestDateArrays.TestInArrays(
                :start_value, :base_date, :array);
        end;
        """,
        return_value=return_value,
        start_value=6,
        base_date=oracledb.Date(2002, 12, 13),
        array=array,
    )
    assert return_value.getvalue() == 26.5


def test_1407(cursor, module_data):
    "1407 - test binding in a date array (with arrayvar)"
    return_value = cursor.var(oracledb.NUMBER)
    array = cursor.arrayvar(oracledb.DATETIME, 10, 20)
    array.setvalue(0, [r[1] for r in module_data])
    cursor.execute(
        """
        begin
            :return_value := pkg_TestDateArrays.TestInArrays(
                :start_value, :base_date, :array);
        end;
        """,
        return_value=return_value,
        start_value=7,
        base_date=oracledb.Date(2002, 12, 14),
        array=array,
    )
    assert return_value.getvalue() == 17.5


def test_1408(cursor, module_data):
    "1408 - test binding in/out a date array (with arrayvar)"
    array = cursor.arrayvar(oracledb.DATETIME, 10, 100)
    original_data = [r[1] for r in module_data]
    array.setvalue(0, original_data)
    cursor.execute(
        """
        begin
            pkg_TestDateArrays.TestInOutArrays(:num_elems, :array);
        end;
        """,
        num_elems=5,
        array=array,
    )
    expected_value = [
        datetime.datetime(2002, 12, 17, 2, 24, 0),
        datetime.datetime(2002, 12, 18, 4, 48, 0),
        datetime.datetime(2002, 12, 19, 7, 12, 0),
        datetime.datetime(2002, 12, 20, 9, 36, 0),
        datetime.datetime(2002, 12, 21, 12, 0, 0),
    ] + original_data[5:]
    assert array.getvalue() == expected_value


def test_1409(cursor):
    "1409 - test binding out a date array (with arrayvar)"
    array = cursor.arrayvar(oracledb.DATETIME, 6, 100)
    cursor.execute(
        """
        begin
            pkg_TestDateArrays.TestOutArrays(:num_elems, :array);
        end;
        """,
        num_elems=6,
        array=array,
    )
    expected_value = [
        datetime.datetime(2002, 12, 13, 4, 48, 0),
        datetime.datetime(2002, 12, 14, 9, 36, 0),
        datetime.datetime(2002, 12, 15, 14, 24, 0),
        datetime.datetime(2002, 12, 16, 19, 12, 0),
        datetime.datetime(2002, 12, 18, 0, 0, 0),
        datetime.datetime(2002, 12, 19, 4, 48, 0),
    ]
    assert array.getvalue() == expected_value


def test_1410(cursor):
    "1410 - test binding out with set input sizes defined"
    bind_vars = cursor.setinputsizes(value=oracledb.DATETIME)
    cursor.execute(
        """
        begin
            :value := to_date(20021209, 'YYYYMMDD');
        end;
        """
    )
    assert bind_vars["value"].getvalue() == datetime.datetime(2002, 12, 9)


def test_1411(cursor):
    "1411 - test binding in/out with set input sizes defined"
    bind_vars = cursor.setinputsizes(value=oracledb.DATETIME)
    cursor.execute(
        """
        begin
            :value := :value + 5.25;
        end;
        """,
        value=datetime.datetime(2002, 12, 12, 10, 0, 0),
    )
    fetched_value = bind_vars["value"].getvalue()
    assert fetched_value == datetime.datetime(2002, 12, 17, 16, 0, 0)


def test_1412(cursor):
    "1412 - test binding out with cursor.var() method"
    var = cursor.var(oracledb.DATETIME)
    cursor.execute(
        """
        begin
            :value := to_date('20021231 12:31:00', 'YYYYMMDD HH24:MI:SS');
        end;
        """,
        value=var,
    )
    assert var.getvalue() == datetime.datetime(2002, 12, 31, 12, 31, 0)


def test_1413(cursor):
    "1413 - test binding in/out with cursor.var() method"
    var = cursor.var(oracledb.DATETIME)
    var.setvalue(0, datetime.datetime(2002, 12, 9, 6, 0, 0))
    cursor.execute(
        """
        begin
            :value := :value + 5.25;
        end;
        """,
        value=var,
    )
    assert var.getvalue() == datetime.datetime(2002, 12, 14, 12, 0, 0)


def test_1414(cursor):
    "1414 - test cursor description is accurate"
    cursor.execute("select * from TestDates")
    expected_value = [
        ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
        ("DATECOL", oracledb.DB_TYPE_DATE, 23, None, None, None, False),
        ("NULLABLECOL", oracledb.DB_TYPE_DATE, 23, None, None, None, True),
    ]
    assert cursor.description == expected_value


def test_1415(cursor, module_data):
    "1415 - test that fetching all of the data returns the correct results"
    cursor.execute("select * From TestDates order by IntCol")
    assert cursor.fetchall() == module_data
    assert cursor.fetchall() == []


def test_1416(cursor, module_data):
    "1416 - test that fetching data in chunks returns the correct results"
    cursor.execute("select * From TestDates order by IntCol")
    assert cursor.fetchmany(3) == module_data[0:3]
    assert cursor.fetchmany(2) == module_data[3:5]
    assert cursor.fetchmany(4) == module_data[5:9]
    assert cursor.fetchmany(3) == module_data[9:]
    assert cursor.fetchmany(3) == []


def test_1417(cursor, module_data_by_key):
    "1417 - test that fetching a single row returns the correct results"
    cursor.execute(
        """
        select *
        from TestDates
        where IntCol in (3, 4)
        order by IntCol
        """
    )
    assert cursor.fetchone() == module_data_by_key[3]
    assert cursor.fetchone() == module_data_by_key[4]
    assert cursor.fetchone() is None


def test_1418(cursor):
    "1418 - test fetching a date with year < 0"
    with pytest.raises(ValueError):
        cursor.execute(
            "select to_date('-4712-01-01', 'SYYYY-MM-DD') from dual"
        )
        cursor.fetchone()
