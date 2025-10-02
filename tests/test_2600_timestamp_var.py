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
2600 - Module for testing timestamp variables
"""

import datetime

import oracledb
import pytest


@pytest.fixture(scope="module")
def module_data():
    data = []
    for i in range(1, 11):
        base_date = datetime.datetime(2002, 12, 9)
        date_interval = datetime.timedelta(days=i)
        date_value = base_date + date_interval
        str_value = str(i * 50)
        fsecond = int(str_value + "0" * (6 - len(str_value)))
        date_col = datetime.datetime(
            date_value.year,
            date_value.month,
            date_value.day,
            date_value.hour,
            date_value.minute,
            i * 2,
            fsecond,
        )
        if i % 2:
            date_interval = datetime.timedelta(days=i + 1)
            date_value = base_date + date_interval
            str_value = str(i * 125)
            fsecond = int(str_value + "0" * (6 - len(str_value)))
            nullable_col = datetime.datetime(
                date_value.year,
                date_value.month,
                date_value.day,
                date_value.hour,
                date_value.minute,
                i * 3,
                fsecond,
            )
        else:
            nullable_col = None
        precision_col = datetime.datetime(2009, 12, 14)
        data_tuple = (i, date_col, nullable_col, precision_col)
        data.append(data_tuple)
    return data


@pytest.fixture(scope="module")
def module_data_by_key(module_data):
    data_by_key = {}
    for row in module_data:
        data_by_key[row[0]] = row
    return data_by_key


def test_2600(cursor, module_data_by_key):
    "2600 - test binding in a timestamp"
    cursor.setinputsizes(value=oracledb.DB_TYPE_TIMESTAMP)
    cursor.execute(
        "select * from TestTimestamps where TimestampCol = :value",
        value=datetime.datetime(2002, 12, 14, 0, 0, 10, 250000),
    )
    assert cursor.fetchall() == [module_data_by_key[5]]


def test_2601(cursor):
    "2601 - test binding in a null"
    cursor.setinputsizes(value=oracledb.DB_TYPE_TIMESTAMP)
    cursor.execute(
        "select * from TestTimestamps where TimestampCol = :value",
        value=None,
    )
    assert cursor.fetchall() == []


def test_2602(cursor):
    "2602 - test binding out with set input sizes defined"
    bind_vars = cursor.setinputsizes(value=oracledb.DB_TYPE_TIMESTAMP)
    cursor.execute(
        """
        begin
            :value := to_timestamp('20021209', 'YYYYMMDD');
        end;
        """
    )
    assert bind_vars["value"].getvalue() == datetime.datetime(2002, 12, 9)


def test_2603(cursor):
    "2603 - test binding in/out with set input sizes defined"
    bind_vars = cursor.setinputsizes(value=oracledb.DB_TYPE_TIMESTAMP)
    cursor.execute(
        """
        begin
            :value := :value + 5.25;
        end;
        """,
        value=datetime.datetime(2002, 12, 12, 10, 0, 0),
    )
    value = bind_vars["value"].getvalue()
    assert value == datetime.datetime(2002, 12, 17, 16, 0, 0)


def test_2604(cursor):
    "2604 - test binding out with cursor.var() method"
    var = cursor.var(oracledb.DB_TYPE_TIMESTAMP)
    cursor.execute(
        """
        begin
            :value := to_date('20021231 12:31:00',
                'YYYYMMDD HH24:MI:SS');
        end;
        """,
        value=var,
    )
    assert var.getvalue() == datetime.datetime(2002, 12, 31, 12, 31, 0)


def test_2605(cursor):
    "2605 - test binding in/out with cursor.var() method"
    var = cursor.var(oracledb.DB_TYPE_TIMESTAMP)
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


def test_2606(cursor):
    "2606 - test cursor description is accurate"
    cursor.execute("select * from TestTimestamps")
    expected_value = [
        ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
        (
            "TIMESTAMPCOL",
            oracledb.DB_TYPE_TIMESTAMP,
            23,
            None,
            0,
            6,
            False,
        ),
        ("NULLABLECOL", oracledb.DB_TYPE_TIMESTAMP, 23, None, 0, 6, True),
        (
            "TIMESTAMPPRECISIONCOL",
            oracledb.DB_TYPE_TIMESTAMP,
            23,
            None,
            0,
            4,
            True,
        ),
    ]
    assert cursor.description == expected_value


def test_2607(cursor, module_data):
    "2607 - test that fetching all of the data returns the correct results"
    cursor.execute("select * From TestTimestamps order by IntCol")
    assert cursor.fetchall() == module_data
    assert cursor.fetchall() == []


def test_2608(cursor, module_data):
    "2608 - test that fetching data in chunks returns the correct results"
    cursor.execute("select * From TestTimestamps order by IntCol")
    assert cursor.fetchmany(3) == module_data[0:3]
    assert cursor.fetchmany(2) == module_data[3:5]
    assert cursor.fetchmany(4) == module_data[5:9]
    assert cursor.fetchmany(3) == module_data[9:]
    assert cursor.fetchmany(3) == []


def test_2609(cursor, module_data_by_key):
    "2609 - test that fetching a single row returns the correct results"
    cursor.execute(
        """
        select *
        from TestTimestamps
        where IntCol in (3, 4)
        order by IntCol
        """
    )
    assert cursor.fetchone() == module_data_by_key[3]
    assert cursor.fetchone() == module_data_by_key[4]
    assert cursor.fetchone() is None


def test_2610(cursor, module_data_by_key):
    "2610 - test binding a timestamp with zero fractional seconds"
    cursor.setinputsizes(value=oracledb.DB_TYPE_TIMESTAMP)
    cursor.execute(
        """
        select *
        from TestTimestamps
        where trunc(TimestampCol) = :value
        """,
        value=datetime.datetime(2002, 12, 14),
    )
    assert cursor.fetchall() == [module_data_by_key[5]]


def test_2611(cursor, module_data_by_key):
    "2611 - test binding a timestamp with datetime.date as input"
    cursor.setinputsizes(value=oracledb.DB_TYPE_TIMESTAMP)
    cursor.execute(
        """
        select *
        from TestTimestamps
        where trunc(TimestampCol) = :value
        """,
        value=datetime.date(2002, 12, 14),
    )
    assert cursor.fetchall() == [module_data_by_key[5]]
