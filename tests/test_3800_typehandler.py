# -----------------------------------------------------------------------------
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
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
3800 - Module for testing the input and output type handlers.
"""

import datetime
import json

import oracledb
import pytest


class Building:
    def __init__(self, building_id, description, num_floors):
        self.building_id = building_id
        self.description = description
        self.num_floors = num_floors

    def __repr__(self):
        return f"<Building {self.building_id}: {self.description}>"

    def __eq__(self, other):
        if isinstance(other, Building):
            return (
                other.building_id == self.building_id
                and other.description == self.description
                and other.num_floors == self.num_floors
            )
        return NotImplemented

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, value):
        result = json.loads(value)
        return cls(**result)


def building_in_converter(value):
    return value.to_json()


def input_type_handler(cursor, value, num_elements):
    if isinstance(value, Building):
        return cursor.var(
            oracledb.STRING,
            arraysize=num_elements,
            inconverter=building_in_converter,
        )


def output_type_handler(cursor, metadata):
    if metadata.type_code is oracledb.DB_TYPE_VARCHAR:
        return cursor.var(
            metadata.type_code,
            arraysize=cursor.arraysize,
            outconverter=Building.from_json,
        )


def test_3800(cursor, test_env):
    "3800 - binding unsupported python object without input type handler"
    cursor.execute("truncate table TestTempTable")
    sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
    building = Building(1, "The First Building", 5)
    with test_env.assert_raises_full_code("DPY-3002"):
        cursor.execute(sql, [building.building_id, building])


def test_3801(cursor):
    "3801 - not callable input type handler"
    cursor.execute("truncate table TestTempTable")
    building = Building(1, "The First Building", 5)
    sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
    cursor.inputtypehandler = 5
    assert cursor.inputtypehandler == 5
    with pytest.raises(TypeError):
        cursor.execute(sql, (building.building_id, building))


def test_3802(conn, cursor):
    "3802 - binding unsupported python object with input type handler"
    cursor.execute("truncate table TestTempTable")
    building = Building(1, "The First Building", 5)
    cursor.inputtypehandler = input_type_handler
    cursor.execute(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        [building.building_id, building],
    )
    assert cursor.bindvars[1].inconverter == building_in_converter
    conn.commit()
    cursor.execute("select IntCol, StringCol1 from TestTempTable")
    assert cursor.fetchall() == [(building.building_id, building.to_json())]


def test_3803(conn, cursor, test_env):
    "3803 - input type handler and output type handler on cursor level"
    cursor.execute("truncate table TestTempTable")
    building_one = Building(1, "The First Building", 5)
    building_two = Building(2, "The Second Building", 87)
    sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
    cursor_one = conn.cursor()
    cursor_two = conn.cursor()
    cursor_one.inputtypehandler = input_type_handler
    cursor_one.execute(sql, [building_one.building_id, building_one])
    conn.commit()

    cursor_one.execute("select IntCol, StringCol1 from TestTempTable")
    assert cursor_one.fetchall() == [
        (building_one.building_id, building_one.to_json())
    ]
    with test_env.assert_raises_full_code("DPY-3002"):
        cursor_two.execute(
            sql,
            (building_two.building_id, building_two),
        )

    cursor_two.outputtypehandler = output_type_handler
    cursor_two.execute("select IntCol, StringCol1 from TestTempTable")
    assert cursor_two.fetchall() == [(building_one.building_id, building_one)]


def test_3804(cursor, test_env):
    "3804 - input type handler and output type handler on connection level"
    cursor.execute("truncate table TestTempTable")
    building_one = Building(1, "The First Building", 5)
    building_two = Building(2, "The Second Building", 87)
    sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
    conn = test_env.get_connection()
    conn.inputtypehandler = input_type_handler
    assert conn.inputtypehandler == input_type_handler

    cursor_one = conn.cursor()
    cursor_two = conn.cursor()
    cursor_one.execute(sql, [building_one.building_id, building_one])
    cursor_two.execute(sql, [building_two.building_id, building_two])
    conn.commit()

    expected_data = [
        (building_one.building_id, building_one),
        (building_two.building_id, building_two),
    ]
    conn.outputtypehandler = output_type_handler
    assert conn.outputtypehandler == output_type_handler
    cursor_one.execute("select IntCol, StringCol1 from TestTempTable")
    assert cursor_one.fetchvars[1].outconverter == Building.from_json
    assert cursor_one.fetchall() == expected_data

    cursor_two.execute("select IntCol, StringCol1 from TestTempTable")
    assert cursor_two.fetchall() == expected_data
    other_cursor = cursor.connection.cursor()
    with test_env.assert_raises_full_code("DPY-3002"):
        other_cursor.execute(sql, (building_one.building_id, building_one))


def test_3805(conn, cursor):
    "3805 - output type handler with outconvert and null values"
    cursor.execute("truncate table TestTempTable")
    data_to_insert = [(1, "String 1"), (2, None), (3, "String 2")]
    cursor.executemany(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        data_to_insert,
    )
    conn.commit()

    def converter(value):
        return "CONVERTED"

    def output_type_handler(cursor, metadata):
        if metadata.type_code is oracledb.DB_TYPE_VARCHAR:
            return cursor.var(
                str, outconverter=converter, arraysize=cursor.arraysize
            )

    cursor.outputtypehandler = output_type_handler
    cursor.execute(
        """
        select IntCol, StringCol1
        from TestTempTable
        order by IntCol
        """
    )
    expected_data = [(1, "CONVERTED"), (2, None), (3, "CONVERTED")]
    assert cursor.fetchall() == expected_data


def test_3806(cursor, test_env):
    "3806 - output type handler for fetching 21c JSON"

    def output_type_handler(cursor, metadata):
        # fetch 21c JSON datatype when using python-oracledb thin mode
        if metadata.type_code is oracledb.DB_TYPE_JSON:
            return cursor.var(
                str, arraysize=cursor.arraysize, outconverter=json.loads
            )
        # if using Oracle Client version < 21, then database returns BLOB
        # data type instead of JSON data type
        elif metadata.type_code is oracledb.DB_TYPE_BLOB:
            return cursor.var(
                metadata.type,
                arraysize=cursor.arraysize,
                outconverter=lambda v: json.loads(v.read()),
            )

    # require a 21c+ database
    if not test_env.has_server_version(21):
        pytest.skip("unsupported database")

    cursor.execute("delete from TestJson")
    insert_sql = "insert into TestJson values (:1, :2)"
    json_data = [
        dict(name="John", city="Delhi"),
        dict(name="George", city="Bangalore"),
        dict(name="Sam", city="Mumbai"),
    ]
    data_to_insert = list(enumerate(json_data))
    if test_env.has_client_version(21):
        # take advantage of direct binding
        cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
        cursor.executemany(insert_sql, data_to_insert)
    else:
        # insert data as JSON string
        json_string_data = [(i, json.dumps(j)) for i, j in data_to_insert]
        cursor.executemany(insert_sql, json_string_data)

    if not test_env.has_client_version(21):
        cursor.outputtypehandler = output_type_handler
    cursor.execute("select * from TestJson")
    assert cursor.fetchall() == data_to_insert


def test_3807(cursor, test_env):
    "3807 - output type handler for encoding errors"

    if test_env.charset != "AL32UTF8":
        pytest.skip("Database character set must be AL32UTF8")

    def output_type_handler(cursor, metadata):
        if metadata.type_code is oracledb.DB_TYPE_VARCHAR:
            return cursor.var(
                metadata.type_code,
                arraysize=cursor.arraysize,
                encoding_errors="replace",
            )

    cursor.outputtypehandler = output_type_handler
    cursor.execute("select utl_raw.cast_to_varchar2('41ab42cd43ef') from dual")
    (result,) = cursor.fetchone()
    rc = chr(0xFFFD)
    expected_result = f"A{rc}B{rc}C{rc}"
    assert result == expected_result


def test_3808(conn):
    "3808 - output type handler with object implementing __call__()"

    class TimestampOutputTypeHandler:

        def __init__(self, unit="s"):
            if unit == "ms":
                self.factor = 1000
            else:
                self.factor = 1

        def converter(self, d):
            return int(d.timestamp() * self.factor)

        def __call__(self, cursor, metadata):
            if metadata.type_code is oracledb.DB_TYPE_TIMESTAMP:
                return cursor.var(
                    metadata.type_code,
                    arraysize=cursor.arraysize,
                    outconverter=self.converter,
                )

    d = datetime.datetime.today()
    with conn.cursor() as cursor:
        cursor.outputtypehandler = TimestampOutputTypeHandler("ms")
        cursor.setinputsizes(oracledb.DB_TYPE_TIMESTAMP)
        cursor.execute("select :d from dual", [d])
        (result,) = cursor.fetchone()
        assert result == int(d.timestamp() * 1000)
    with conn.cursor() as cursor:
        cursor.outputtypehandler = TimestampOutputTypeHandler("s")
        cursor.setinputsizes(oracledb.DB_TYPE_TIMESTAMP)
        cursor.execute("select :d from dual", [d])
        (result,) = cursor.fetchone()
        assert result == int(d.timestamp())
