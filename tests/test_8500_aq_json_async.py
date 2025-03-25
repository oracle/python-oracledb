# -----------------------------------------------------------------------------
# Copyright (c) 2025, Oracle and/or its affiliates.
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
8500 - Module for testing AQ with JSON queues with asyncio
"""

import asyncio
import datetime
import decimal
import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    json_queue_name = "TEST_JSON_QUEUE"
    json_data = [
        [
            2.75,
            True,
            "Ocean Beach",
            b"Some bytes",
            {"keyA": 1.0, "KeyB": "Melbourne"},
            datetime.datetime(2022, 8, 1, 0, 0),
        ],
        [
            True,
            False,
            "String",
            b"Some Bytes",
            {},
            {"name": None},
            {"name": "John"},
            {"age": 30},
            {"Permanent": True},
            {
                "employee": {
                    "name": "John",
                    "age": 30,
                    "city": "Delhi",
                    "Parmanent": True,
                }
            },
            {"employees": ["John", "Matthew", "James"]},
            {
                "employees": [
                    {"employee1": {"name": "John", "city": "Delhi"}},
                    {"employee2": {"name": "Matthew", "city": "Mumbai"}},
                    {"employee3": {"name": "James", "city": "Bangalore"}},
                ]
            },
        ],
        [
            datetime.datetime.today(),
            datetime.datetime(2004, 2, 1, 3, 4, 5),
            datetime.datetime(2020, 12, 2, 13, 29, 14),
            datetime.timedelta(8.5),
            datetime.datetime(2002, 12, 13, 9, 36, 0),
            oracledb.Timestamp(2002, 12, 13, 9, 36, 0),
            datetime.datetime(2002, 12, 13),
        ],
        dict(name="John", age=30, city="New York"),
        [
            0,
            1,
            25.25,
            6088343244,
            -9999999999999999999,
            decimal.Decimal("0.25"),
            decimal.Decimal("10.25"),
            decimal.Decimal("319438950232418390.273596"),
        ],
    ]

    async def __deq_in_task(self, results):
        async with test_env.get_connection_async() as conn:
            queue = conn.queue(self.json_queue_name, "JSON")
            queue.deqoptions.wait = 10
            props = await queue.deqone()
            if props is not None:
                results.append(props.payload)
            await conn.commit()

    def __verify_attr(self, obj, attrName, value):
        setattr(obj, attrName, value)
        self.assertEqual(getattr(obj, attrName), value)

    async def test_8500(self):
        "8500 - test dequeuing an empty JSON queue"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = await queue.deqone()
        self.assertIsNone(props)

    async def test_8501(self):
        "8501 - test enqueuing and dequeuing multiple JSON messages"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        props = self.conn.msgproperties()
        for data in self.json_data:
            props.payload = data
            await queue.enqone(props)
        await self.conn.commit()
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        results = []
        while True:
            props = await queue.deqone()
            if props is None:
                break
            results.append(props.payload)
        await self.conn.commit()
        self.assertEqual(results, self.json_data)

    @unittest.skip("awaiting fix for bug 37746852")
    async def test_8502(self):
        "8502 - test dequeuing with DEQ_REMOVE_NODATA option"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        data = self.json_data[1]
        props = self.conn.msgproperties(payload=data)
        await queue.enqone(props)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.mode = oracledb.DEQ_REMOVE_NODATA
        props = await queue.deqone()
        self.assertIsNotNone(props)
        self.assertIsNone(props.payload)

    async def test_8503(self):
        "8503 - test getting/setting dequeue options attributes"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        options = queue.deqoptions
        self.__verify_attr(options, "condition", "TEST_CONDITION")
        self.__verify_attr(options, "consumername", "TEST_CONSUMERNAME")
        self.__verify_attr(options, "correlation", "TEST_CORRELATION")
        self.__verify_attr(options, "mode", oracledb.DEQ_LOCKED)
        self.__verify_attr(
            options, "navigation", oracledb.DEQ_NEXT_TRANSACTION
        )
        self.__verify_attr(options, "transformation", "TEST_TRANSFORMATION")
        self.__verify_attr(options, "visibility", oracledb.ENQ_IMMEDIATE)
        self.__verify_attr(options, "wait", 1287)
        self.__verify_attr(options, "msgid", b"mID")

    async def test_8504(self):
        "8504 - test waiting for dequeue"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        results = []
        task = asyncio.create_task(self.__deq_in_task(results))
        data = self.json_data[0]
        props = self.conn.msgproperties(payload=data)
        await queue.enqone(props)
        await self.conn.commit()
        await task
        self.assertEqual(results, [data])

    async def test_8505(self):
        "8505 - test getting/setting enqueue options attributes"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        options = queue.enqoptions
        self.__verify_attr(options, "visibility", oracledb.ENQ_IMMEDIATE)

    async def test_8506(self):
        "8506 - test getting/setting message properties attributes"
        props = self.conn.msgproperties()
        self.__verify_attr(props, "correlation", "TEST_CORRELATION")
        self.__verify_attr(props, "delay", 60)
        self.__verify_attr(props, "exceptionq", "TEST_EXCEPTIONQ")
        self.__verify_attr(props, "expiration", 30)
        self.assertEqual(props.attempts, 0)
        self.__verify_attr(props, "priority", 1)
        self.assertEqual(props.state, oracledb.MSG_READY)
        self.assertEqual(props.deliverymode, 0)

    async def test_8507(self):
        "8507 - test enqueue visibility options - ENQ_ON_COMMIT"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        data = self.json_data[0]
        queue.enqoptions.visibility = oracledb.ENQ_ON_COMMIT
        props = self.conn.msgproperties(payload=data)
        await queue.enqone(props)

        async with test_env.get_connection_async() as other_conn:
            queue = other_conn.queue(self.json_queue_name, "JSON")
            queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
            queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
            props = await queue.deqone()
            self.assertIsNone(props)
            await self.conn.commit()
            props = await queue.deqone()
            self.assertIsNotNone(props)

    async def test_8508(self):
        "8508 - test enqueue visibility option - ENQ_IMMEDIATE"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        data = self.json_data[0]
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=data)
        await queue.enqone(props)

        async with test_env.get_connection_async() as other_conn:
            queue = other_conn.queue(self.json_queue_name, "JSON")
            queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
            queue.deqoptions.visibility = oracledb.DEQ_ON_COMMIT
            queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
            props = await queue.deqone()
            data = props.payload
            results = data
            await other_conn.commit()
            self.assertEqual(results, self.json_data[0])

    async def test_8509(self):
        "8509 - test enqueue/dequeue delivery modes identical - persistent"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        data = self.json_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=data)
        await queue.enqone(props)

        async with test_env.get_connection_async() as other_conn:
            queue = other_conn.queue(self.json_queue_name, "JSON")
            queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
            queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
            queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
            queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
            props = await queue.deqone()
            data = props.payload
            results = data
            await other_conn.commit()
            self.assertEqual(results, self.json_data[0])

    async def test_8510(self):
        "8510 - test error for message with no payload"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        props = self.conn.msgproperties()
        with self.assertRaisesFullCode("DPY-2000"):
            await queue.enqone(props)

    async def test_8511(self):
        "8511 - verify that the msgid property is returned correctly"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        data = self.json_data[0]
        props = self.conn.msgproperties(payload=data)
        self.assertIsNone(props.msgid)
        await queue.enqone(props)
        await self.cursor.execute("select msgid from JSON_QUEUE_TAB")
        (actual_msgid,) = await self.cursor.fetchone()
        self.assertEqual(props.msgid, actual_msgid)
        props = await queue.deqone()
        self.assertEqual(props.msgid, actual_msgid)

    async def test_8512(self):
        "8512 - test message props enqtime"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        data = self.json_data[0]
        await self.cursor.execute("select current_timestamp from dual")
        (start_date,) = await self.cursor.fetchone()
        start_date = start_date.replace(microsecond=0)
        props = self.conn.msgproperties(payload=data)
        await queue.enqone(props)
        props = await queue.deqone()
        await self.cursor.execute("select current_timestamp from dual")
        (end_date,) = await self.cursor.fetchone()
        end_date = end_date.replace(microsecond=0)
        self.assertTrue(start_date <= props.enqtime <= end_date)

    async def test_8513(self):
        "8513 - test message props declared attributes"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        data = self.json_data[0]
        values = dict(
            payload=data,
            correlation="TEST_CORRELATION",
            delay=0,
            exceptionq="PYTHONTEST.TEST_EXCEPTIONQ",
            expiration=15,
            priority=1,
        )
        props = self.conn.msgproperties(**values)
        for attr_name in values:
            self.assertEqual(getattr(props, attr_name), values[attr_name])
        await queue.enqone(props)
        await self.conn.commit()
        prop = await queue.deqone()
        for attr_name in values:
            self.assertEqual(getattr(prop, attr_name), values[attr_name])

    async def test_8514(self):
        "8514 - test getting queue attributes"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        self.assertEqual(queue.name, "TEST_JSON_QUEUE")
        self.assertEqual(queue.connection, self.conn)

    async def test_8515(self):
        "8515 - test getting write-only attributes"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        for options in (queue.enqoptions, queue.deqoptions):
            with self.assertRaises(AttributeError):
                options.deliverymode

    async def test_8516(self):
        "8516 - test deqoption condition with priority"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        priorities = [5, 5, 5, 5, 10, 9, 9, 10, 9]
        for priority in priorities:
            data = self.json_data[0]
            props = self.conn.msgproperties(payload=data, priority=priority)
            await queue.enqone(props)

        queue.deqoptions.condition = "priority = 9"
        results = []
        while True:
            props = await queue.deqone()
            if props is None:
                break
            results.append(props.payload)
        await self.conn.commit()
        self.assertEqual(len(results), 3)

    async def test_8517(self):
        "8517 - test deqoption correlation"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        correlations = [
            "sample",
            "sample correlation",
            "sample",
            "sample",
            "sample correlation",
        ]
        for correlation in correlations:
            data = self.json_data[0]
            props = self.conn.msgproperties(
                payload=data, correlation=correlation
            )
            await queue.enqone(props)
        await self.conn.commit()
        queue.deqoptions.correlation = "sample correlation"
        results = []
        while True:
            props = await queue.deqone()
            if props is None:
                break
            results.append(props.payload)
        await self.conn.commit()
        self.assertEqual(len(results), 2)

    async def test_8518(self):
        "8518 - test deqoption msgid"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        data = self.json_data[0]
        props = self.conn.msgproperties(payload=data)
        await queue.enqone(props)
        await queue.enqone(props)
        await self.conn.commit()
        msgid = props.msgid
        await queue.enqone(props)
        await self.conn.commit()
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.msgid = msgid
        prop = await queue.deqone()
        await self.conn.commit()
        self.assertEqual(prop.msgid, msgid)

    async def test_8519(self):
        "8519 - test payload_type returns the correct value"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        self.assertEqual(queue.payload_type, "JSON")

    async def test_8520(self):
        "8520 - test deprecated attributes (enqOptions, deqOptions)"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        self.assertEqual(queue.enqOptions, queue.enqoptions)
        self.assertEqual(queue.deqOptions, queue.deqoptions)

    async def test_8521(self):
        "8521 - test wrong payload type"
        queue = await self.get_and_clear_queue(self.json_queue_name, "JSON")
        props = self.conn.msgproperties(payload="A string")
        with self.assertRaisesFullCode("DPY-2062"):
            await queue.enqone(props)


if __name__ == "__main__":
    test_env.run_test_cases()
