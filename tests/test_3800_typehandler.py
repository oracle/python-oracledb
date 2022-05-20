#------------------------------------------------------------------------------
# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
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
#------------------------------------------------------------------------------

"""
3800 - Module for testing the input and output type handlers.
"""

import json
import unittest

import oracledb
import test_env

class Building(object):

    def __init__(self, building_id, description, num_floors):
        self.building_id = building_id
        self.description = description
        self.num_floors = num_floors

    def __repr__(self):
        return "<Building %s: %s>" % (self.building_id, self.description)

    def __eq__(self, other):
        if isinstance(other, Building):
            return other.building_id == self.building_id \
                    and other.description == self.description \
                    and other.num_floors == self.num_floors
        return NotImplemented

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, value):
        result = json.loads(value)
        return cls(**result)


class TestCase(test_env.BaseTestCase):

    def building_in_converter(self, value):
        return value.to_json()

    def input_type_handler(self, cursor, value, num_elements):
        if isinstance(value, Building):
            return cursor.var(oracledb.STRING, arraysize=num_elements,
                              inconverter=self.building_in_converter)

    def output_type_handler(self, cursor, name, default_type, size, precision,
                            scale):
        if default_type == oracledb.STRING:
            return cursor.var(default_type, arraysize=cursor.arraysize,
                              outconverter=Building.from_json)

    def test_3800(self):
        "3800 - binding unsupported python object without input type handler"
        self.cursor.execute("truncate table TestTempTable")
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        building = Building(1, "The First Building", 5)
        self.assertRaisesRegex(oracledb.NotSupportedError, "^DPY-3002:",
                               self.cursor.execute, sql,
                               (building.building_id, building))

    def test_3801(self):
        "3801 - not callable input type handler"
        self.cursor.execute("truncate table TestTempTable")
        building = Building(1, "The First Building", 5)
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        self.cursor.inputtypehandler = 5
        self.assertRaises(TypeError, self.cursor.execute, sql,
                          (building.building_id, building))

    def test_3802(self):
        "3802 - binding unsupported python object with input type handler"
        self.cursor.execute("truncate table TestTempTable")
        building = Building(1, "The First Building", 5)
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        self.cursor.inputtypehandler = self.input_type_handler
        self.cursor.execute(sql, (building.building_id, building))
        self.connection.commit()
        self.cursor.execute("select IntCol, StringCol1 from TestTempTable")
        self.assertEqual(self.cursor.fetchall(),
                         [(building.building_id, building.to_json())])

    def test_3803(self):
        "3803 - input type handler and output type handler on cursor level"
        self.cursor.execute("truncate table TestTempTable")
        building_one = Building(1, "The First Building", 5)
        building_two = Building(2, "The Second Building", 87)
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        cursor_one = self.connection.cursor()
        cursor_two = self.connection.cursor()
        cursor_one.inputtypehandler = self.input_type_handler
        cursor_one.execute(sql, (building_one.building_id, building_one))
        self.connection.commit()
        cursor_one.execute("select IntCol, StringCol1 from TestTempTable")
        self.assertEqual(cursor_one.fetchall(),
                         [(building_one.building_id, building_one.to_json())])
        self.assertRaisesRegex(oracledb.NotSupportedError, "^DPY-3002:",
                               cursor_two.execute, sql,
                               (building_two.building_id, building_two))
        cursor_two.outputtypehandler = self.output_type_handler
        cursor_two.execute("select IntCol, StringCol1 from TestTempTable")
        self.assertEqual(cursor_two.fetchall(),
                         [(building_one.building_id, building_one)])

    def test_3804(self):
        "3804 - input type handler and output type handler on connection level"
        self.cursor.execute("truncate table TestTempTable")
        building_one = Building(1, "The First Building", 5)
        building_two = Building(2, "The Second Building", 87)
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        connection = test_env.get_connection()
        connection.inputtypehandler = self.input_type_handler
        cursor_one = connection.cursor()
        cursor_two = connection.cursor()
        cursor_one.execute(sql, (building_one.building_id, building_one))
        cursor_two.execute(sql, (building_two.building_id, building_two))
        connection.commit()
        expected_data = [
            (building_one.building_id, building_one),
            (building_two.building_id, building_two)
        ]
        connection.outputtypehandler = self.output_type_handler
        cursor_one.execute("select IntCol, StringCol1 from TestTempTable")
        self.assertEqual(cursor_one.fetchall(), expected_data)
        cursor_two.execute("select IntCol, StringCol1 from TestTempTable")
        self.assertEqual(cursor_two.fetchall(), expected_data)
        other_cursor = self.connection.cursor()
        self.assertRaisesRegex(oracledb.NotSupportedError, "^DPY-3002:",
                               other_cursor.execute, sql,
                               (building_one.building_id, building_one))

    def test_3805(self):
        "3805 - output type handler with outconvert and null values"
        self.cursor.execute("truncate table TestTempTable")
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        data_to_insert = [
            (1, "String 1"),
            (2, None),
            (3, "String 2")
        ]
        self.cursor.executemany(sql, data_to_insert)
        self.connection.commit()
        def converter(value):
            return "CONVERTED"
        def output_type_handler(cursor, name, default_type, size, precision,
                                scale):
            if default_type is oracledb.DB_TYPE_VARCHAR:
                return cursor.var(str, outconverter=converter,
                                  arraysize=cursor.arraysize)
        self.cursor.outputtypehandler = output_type_handler
        self.cursor.execute("""
                select IntCol, StringCol1
                from TestTempTable
                order by IntCol""")
        expected_data = [
            (1, "CONVERTED"),
            (2, None),
            (3, "CONVERTED")
        ]
        self.assertEqual(self.cursor.fetchall(), expected_data)

    @unittest.skipUnless(test_env.get_server_version() >= (21, 0),
                         "unsupported server")
    def test_3806(self):
        "3806 - output type handler for fetching 21c JSON"
        self.cursor.execute("truncate table TestJson")
        insert_sql = "insert into TestJson values (:1, :2)"
        json_data = [
            dict(name="John", city="Delhi"),
            dict(name="George", city="Bangalore"),
            dict(name="Sam", city="Mumbai")
        ]
        data_to_insert = list(enumerate(json_data))
        json_as_string = self.connection.thin or \
                test_env.get_client_version() < (21, 0)
        if json_as_string:
            # insert data as JSON string
            self.cursor.executemany(insert_sql,
                    [(i, json.dumps(j)) for i, j in data_to_insert])
        else:
            # take advantage of direct binding
            self.cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
            self.cursor.executemany(insert_sql, data_to_insert)
        def output_type_handler(cursor, name, default_type, size, precision,
                                scale):
            # fetch 21c JSON datatype when using python-oracledb thin mode
            if default_type == oracledb.DB_TYPE_JSON:
                return cursor.var(str, arraysize=cursor.arraysize,
                                  outconverter=json.loads)
            # if using Oracle Client version < 21, then database returns BLOB
            # data type instead of JSON data type
            elif default_type == oracledb.DB_TYPE_BLOB:
                return cursor.var(default_type, arraysize=cursor.arraysize,
                                  outconverter=lambda v: json.loads(v.read()))
        if json_as_string:
            self.cursor.outputtypehandler = output_type_handler
        self.cursor.execute("select * from TestJson")
        self.assertEqual(self.cursor.fetchall(), data_to_insert)

if __name__ == "__main__":
    test_env.run_test_cases()
