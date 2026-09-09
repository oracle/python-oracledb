# -----------------------------------------------------------------------------
# Copyright (c) 2022, 2026, Oracle and/or its affiliates.
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
Module for testing timestamp with time zone variables
"""

import datetime

import oracledb
import pytest


@pytest.fixture(scope="module")
def module_data():
    data = []
    base_date = datetime.datetime(2022, 6, 3)
    for i in range(1, 11):
        microseconds = int(str(i * 50).ljust(6, "0"))
        offset = datetime.timedelta(
            days=i, seconds=i * 2, microseconds=microseconds
        )
        col = base_date + offset
        if i % 2:
            microseconds = int(str(i * 125).ljust(6, "0"))
            offset = datetime.timedelta(
                days=i + 1, seconds=i * 3, microseconds=microseconds
            )
            nullable_col = base_date + offset
        else:
            nullable_col = None
        precision_col = datetime.datetime(2009, 12, 14)
        data_tuple = (i, col, nullable_col, precision_col)
        data.append(data_tuple)
    return data


@pytest.fixture(scope="module")
def module_data_by_key(module_data):
    data_by_key = {}
    for row in module_data:
        data_by_key[row[0]] = row
    return data_by_key


def test_data_types_2300(cursor, module_data_by_key):
    "2300 - test binding in a timestamp"
    cursor.setinputsizes(value=oracledb.DB_TYPE_TIMESTAMP_TZ)
    cursor.execute(
        """
        select *
        from TestTimestampTZs
        where TimestampTZCol = :value
        """,
        value=datetime.datetime(2022, 6, 7, 18, 30, 10, 250000),
    )
    assert cursor.fetchall() == [module_data_by_key[5]]


def test_data_types_2301(cursor):
    "2301 - test binding in a null"
    cursor.setinputsizes(value=oracledb.DB_TYPE_TIMESTAMP_TZ)
    cursor.execute(
        """
        select *
        from TestTimestampTZs
        where TimestampTZCol = :value
        """,
        value=None,
    )
    assert cursor.fetchall() == []


def test_data_types_2302(cursor):
    "2302 - test binding out with set input sizes defined"
    bv = cursor.setinputsizes(value=oracledb.DB_TYPE_TIMESTAMP_TZ)
    cursor.execute("""
        begin
            :value := to_timestamp('20220603', 'YYYYMMDD');
        end;
        """)
    assert bv["value"].getvalue() == datetime.datetime(2022, 6, 3)


def test_data_types_2303(cursor):
    "2303 - test binding in/out with set input sizes defined"
    bv = cursor.setinputsizes(value=oracledb.DB_TYPE_TIMESTAMP_TZ)
    cursor.execute(
        """
        begin
            :value := :value + to_dsinterval('5 06:00:00');
        end;
        """,
        value=datetime.datetime(2022, 5, 25),
    )
    assert bv["value"].getvalue() == datetime.datetime(2022, 5, 30, 6, 0, 0)


def test_data_types_2304(cursor):
    "2304 - test binding out with cursor.var() method"
    var = cursor.var(oracledb.DB_TYPE_TIMESTAMP_TZ)
    cursor.execute(
        """
        begin
            :value := to_date('20021231 12:31:00', 'YYYYMMDD HH24:MI:SS');
        end;
        """,
        value=var,
    )
    assert var.getvalue() == datetime.datetime(2002, 12, 31, 12, 31, 0)


def test_data_types_2305(cursor):
    "2305 - test binding in/out with cursor.var() method"
    var = cursor.var(oracledb.DB_TYPE_TIMESTAMP_TZ)
    var.setvalue(0, datetime.datetime(2022, 6, 3, 6, 0, 0))
    cursor.execute(
        """
        begin
            :value := :value + to_dsinterval('5 06:00:00');
        end;
        """,
        value=var,
    )
    assert var.getvalue() == datetime.datetime(2022, 6, 8, 12, 0, 0)


def test_data_types_2306(cursor):
    "2306 - test cursor description is accurate"
    cursor.execute("select * from TestTimestampTZs")
    expected_value = [
        ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
        (
            "TIMESTAMPTZCOL",
            oracledb.DB_TYPE_TIMESTAMP_TZ,
            23,
            None,
            0,
            6,
            False,
        ),
        (
            "NULLABLECOL",
            oracledb.DB_TYPE_TIMESTAMP_TZ,
            23,
            None,
            0,
            6,
            True,
        ),
        (
            "TIMESTAMPTZPRECISIONCOL",
            oracledb.DB_TYPE_TIMESTAMP_TZ,
            23,
            None,
            0,
            7,
            True,
        ),
    ]
    assert cursor.description == expected_value


def test_data_types_2307(cursor, module_data):
    "2307 - test that fetching all of the data returns the correct results"
    cursor.execute("select * From TestTimestampTZs order by IntCol")
    assert cursor.fetchall() == module_data
    assert cursor.fetchall() == []


def test_data_types_2308(cursor, module_data):
    "2308 - test that fetching data in chunks returns the correct results"
    cursor.execute("select * From TestTimestampTZs order by IntCol")
    assert cursor.fetchmany(3) == module_data[0:3]
    assert cursor.fetchmany(2) == module_data[3:5]
    assert cursor.fetchmany(4) == module_data[5:9]
    assert cursor.fetchmany(3) == module_data[9:]
    assert cursor.fetchmany(3) == []


def test_data_types_2309(cursor, module_data_by_key):
    "2309 - test that fetching a single row returns the correct results"
    cursor.execute("""
        select *
        from TestTimestampTZs
        where IntCol in (3, 4)
        order by IntCol
        """)
    assert cursor.fetchone() == module_data_by_key[3]
    assert cursor.fetchone() == module_data_by_key[4]
    assert cursor.fetchone() is None


def test_data_types_2310(cursor, module_data_by_key):
    "2310 - test binding a timestamp with zero fractional seconds"
    cursor.setinputsizes(value=oracledb.DB_TYPE_TIMESTAMP_TZ)
    cursor.execute(
        """
        select *
        from TestTimestampTZs
        where trunc(TimestampTZCol) = :value
        """,
        value=datetime.datetime(2022, 6, 8),
    )
    assert cursor.fetchall() == [module_data_by_key[5]]


def test_data_types_2311(cursor, module_data_by_key):
    "2311 - test binding a timestamp with datetime.date as input"
    cursor.setinputsizes(value=oracledb.DB_TYPE_TIMESTAMP_TZ)
    cursor.execute(
        """
        select *
        from TestTimestampTZs
        where trunc(TimestampTZCol) = :value
        """,
        value=datetime.date(2022, 6, 8),
    )
    assert cursor.fetchall() == [module_data_by_key[5]]
