# -----------------------------------------------------------------------------
# Copyright (c) 2023, 2024, Oracle and/or its affiliates.
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
6000 - Module for testing the input and output type handlers with asyncio.
"""

import datetime
import json
import unittest

import oracledb
import test_env


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


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    def building_in_converter(self, value):
        return value.to_json()

    def input_type_handler(self, cursor, value, num_elements):
        if isinstance(value, Building):
            return cursor.var(
                oracledb.STRING,
                arraysize=num_elements,
                inconverter=self.building_in_converter,
            )

    def output_type_handler(self, cursor, metadata):
        if metadata.type_code is oracledb.DB_TYPE_VARCHAR:
            return cursor.var(
                metadata.type_code,
                arraysize=cursor.arraysize,
                outconverter=Building.from_json,
            )

    async def test_6000(self):
        "6000 - binding unsupported python object without input type handler"
        await self.cursor.execute("truncate table TestTempTable")
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        building = Building(1, "The First Building", 5)
        with self.assertRaisesFullCode("DPY-3002"):
            await self.cursor.execute(sql, [building.building_id, building])

    async def test_6001(self):
        "6001 - not callable input type handler"
        await self.cursor.execute("truncate table TestTempTable")
        building = Building(1, "The First Building", 5)
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        self.cursor.inputtypehandler = 5
        self.assertEqual(self.cursor.inputtypehandler, 5)
        with self.assertRaises(TypeError):
            await self.cursor.execute(sql, (building.building_id, building))

    async def test_6002(self):
        "6002 - binding unsupported python object with input type handler"
        await self.cursor.execute("truncate table TestTempTable")
        building = Building(1, "The First Building", 5)
        self.cursor.inputtypehandler = self.input_type_handler
        await self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            [building.building_id, building],
        )
        self.assertEqual(
            self.cursor.bindvars[1].inconverter, self.building_in_converter
        )
        await self.conn.commit()
        await self.cursor.execute(
            "select IntCol, StringCol1 from TestTempTable"
        )
        self.assertEqual(
            await self.cursor.fetchall(),
            [(building.building_id, building.to_json())],
        )

    async def test_6003(self):
        "6003 - input type handler and output type handler on cursor level"
        await self.cursor.execute("truncate table TestTempTable")
        building_one = Building(1, "The First Building", 5)
        building_two = Building(2, "The Second Building", 87)
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        cursor_one = self.conn.cursor()
        cursor_two = self.conn.cursor()
        cursor_one.inputtypehandler = self.input_type_handler
        await cursor_one.execute(sql, [building_one.building_id, building_one])
        await self.conn.commit()

        await cursor_one.execute(
            "select IntCol, StringCol1 from TestTempTable"
        )
        self.assertEqual(
            await cursor_one.fetchall(),
            [(building_one.building_id, building_one.to_json())],
        )
        with self.assertRaisesFullCode("DPY-3002"):
            await cursor_two.execute(
                sql, (building_two.building_id, building_two)
            )

        cursor_two.outputtypehandler = self.output_type_handler
        await cursor_two.execute(
            "select IntCol, StringCol1 from TestTempTable"
        )
        self.assertEqual(
            await cursor_two.fetchall(),
            [(building_one.building_id, building_one)],
        )

    async def test_6004(self):
        "6004 - input type handler and output type handler on connection level"
        await self.cursor.execute("truncate table TestTempTable")
        building_one = Building(1, "The First Building", 5)
        building_two = Building(2, "The Second Building", 87)
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        conn = await test_env.get_connection_async()
        conn.inputtypehandler = self.input_type_handler
        self.assertEqual(conn.inputtypehandler, self.input_type_handler)

        cursor_one = conn.cursor()
        cursor_two = conn.cursor()
        await cursor_one.execute(sql, [building_one.building_id, building_one])
        await cursor_two.execute(sql, [building_two.building_id, building_two])
        await conn.commit()

        expected_data = [
            (building_one.building_id, building_one),
            (building_two.building_id, building_two),
        ]
        conn.outputtypehandler = self.output_type_handler
        self.assertEqual(conn.outputtypehandler, self.output_type_handler)
        await cursor_one.execute(
            "select IntCol, StringCol1 from TestTempTable"
        )
        self.assertEqual(
            cursor_one.fetchvars[1].outconverter, Building.from_json
        )
        self.assertEqual(await cursor_one.fetchall(), expected_data)

        await cursor_two.execute(
            "select IntCol, StringCol1 from TestTempTable"
        )
        self.assertEqual(await cursor_two.fetchall(), expected_data)
        other_cursor = self.conn.cursor()
        with self.assertRaisesFullCode("DPY-3002"):
            await other_cursor.execute(
                sql, (building_one.building_id, building_one)
            )

    async def test_6005(self):
        "6005 - output type handler with outconvert and null values"
        await self.cursor.execute("truncate table TestTempTable")
        data_to_insert = [(1, "String 1"), (2, None), (3, "String 2")]
        await self.cursor.executemany(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            data_to_insert,
        )
        await self.conn.commit()

        def converter(value):
            return "CONVERTED"

        def output_type_handler(cursor, metadata):
            if metadata.type_code is oracledb.DB_TYPE_VARCHAR:
                return cursor.var(
                    str, outconverter=converter, arraysize=cursor.arraysize
                )

        self.cursor.outputtypehandler = output_type_handler
        await self.cursor.execute(
            """
            select IntCol, StringCol1
            from TestTempTable
            order by IntCol
            """
        )
        expected_data = [(1, "CONVERTED"), (2, None), (3, "CONVERTED")]
        self.assertEqual(await self.cursor.fetchall(), expected_data)

    @unittest.skipUnless(
        test_env.get_server_version() >= (21, 0), "unsupported server"
    )
    async def test_6006(self):
        "6006 - output type handler for fetching 21c JSON"

        def output_type_handler(cursor, metadata):
            # fetch 21c JSON datatype when using python-oracledb thin mode
            if metadata.type_code is oracledb.DB_TYPE_JSON:
                return cursor.var(
                    str, arraysize=cursor.arraysize, outconverter=json.loads
                )

        await self.cursor.execute("truncate table TestJson")
        insert_sql = "insert into TestJson values (:1, :2)"
        json_data = [
            dict(name="John", city="Delhi"),
            dict(name="George", city="Bangalore"),
            dict(name="Sam", city="Mumbai"),
        ]
        data_to_insert = list(enumerate(json_data))
        self.cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
        await self.cursor.executemany(insert_sql, data_to_insert)
        self.cursor.outputtypehandler = output_type_handler
        await self.cursor.execute("select * from TestJson")
        self.assertEqual(await self.cursor.fetchall(), data_to_insert)

    async def test_6007(self):
        "6007 - output type handler with object implementing __call__()"

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
        with self.conn.cursor() as cursor:
            cursor.outputtypehandler = TimestampOutputTypeHandler("ms")
            cursor.setinputsizes(oracledb.DB_TYPE_TIMESTAMP)
            await cursor.execute("select :d from dual", [d])
            (result,) = await cursor.fetchone()
            self.assertEqual(result, int(d.timestamp() * 1000))
        with self.conn.cursor() as cursor:
            cursor.outputtypehandler = TimestampOutputTypeHandler("s")
            cursor.setinputsizes(oracledb.DB_TYPE_TIMESTAMP)
            await cursor.execute("select :d from dual", [d])
            (result,) = await cursor.fetchone()
            self.assertEqual(result, int(d.timestamp()))


if __name__ == "__main__":
    test_env.run_test_cases()
