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
7900 - Module for testing AQ with raw queues with asyncio
"""

import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    raw_data = [
        b"sample raw data 1",
        b"sample raw data 2",
        b"sample raw data 3",
        b"sample raw data 4",
        b"sample raw data 5",
        b"sample raw data 6",
    ]

    def __verify_attr(self, obj, attrName, value):
        setattr(obj, attrName, value)
        self.assertEqual(getattr(obj, attrName), value)

    async def test_7900(self):
        "7900 - test dequeuing an empty RAW queue"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = await queue.deqone()
        self.assertIsNone(props)

    async def test_7901(self):
        "7901 - test enqueuing and dequeuing multiple RAW messages"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        props = self.conn.msgproperties()
        for value in self.raw_data:
            props.payload = value
            await queue.enqone(props)
        await self.conn.commit()
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        results = []
        while True:
            props = await queue.deqone()
            if props is None:
                break
            value = props.payload
            results.append(value)
        await self.conn.commit()
        self.assertEqual(results, self.raw_data)

    async def test_7902(self):
        "7902 - test dequeuing with DEQ_REMOVE_NODATA in RAW queue"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[1]
        props = self.conn.msgproperties(payload=value)
        await queue.enqone(props)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.mode = oracledb.DEQ_REMOVE_NODATA
        props = await queue.deqone()
        self.assertIsNotNone(props)
        self.assertEqual(props.payload, b"")

    async def test_7903(self):
        "7903 - test getting/setting dequeue options attributes"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
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

    async def test_7904(self):
        "7904 - test enqueue options attributes RAW queue"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        options = queue.enqoptions
        self.__verify_attr(options, "visibility", oracledb.ENQ_IMMEDIATE)

    async def test_7905(self):
        "7905 - test errors for invalid values for enqueue"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        with self.assertRaises(TypeError):
            await queue.enqone(value)

    async def test_7906(self):
        "7906 - test getting/setting message properties attributes"
        props = self.conn.msgproperties()
        self.__verify_attr(props, "correlation", "TEST_CORRELATION")
        self.__verify_attr(props, "delay", 60)
        self.__verify_attr(props, "exceptionq", "TEST_EXCEPTIONQ")
        self.__verify_attr(props, "expiration", 30)
        self.assertEqual(props.attempts, 0)
        self.__verify_attr(props, "priority", 1)
        self.assertEqual(props.state, oracledb.MSG_READY)
        self.assertEqual(props.deliverymode, 0)

    async def test_7907(self):
        "7907 - test enqueue visibility option - ENQ_ON_COMMIT"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        queue.enqoptions.visibility = oracledb.ENQ_ON_COMMIT
        props = self.conn.msgproperties(payload=value)
        await queue.enqone(props)

        async with test_env.get_connection_async() as other_conn:
            queue = other_conn.queue("TEST_RAW_QUEUE")
            queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
            queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
            props = await queue.deqone()
            self.assertIsNone(props)
            await self.conn.commit()
            props = await queue.deqone()
            self.assertIsNotNone(props)

    async def test_7908(self):
        "7908 - test enqueue visibility option - ENQ_IMMEDIATE"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=value)
        await queue.enqone(props)

        async with test_env.get_connection_async() as other_conn:
            queue = other_conn.queue("TEST_RAW_QUEUE")
            queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
            queue.deqoptions.visibility = oracledb.DEQ_ON_COMMIT
            queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
            props = await queue.deqone()
            value = props.payload
            results = value
            await other_conn.commit()
            self.assertEqual(results, self.raw_data[0])

    async def test_7909(self):
        "7909 - test enqueue/dequeue delivery modes identical - buffered"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=value)
        await queue.enqone(props)

        async with test_env.get_connection_async() as other_conn:
            queue = other_conn.queue("TEST_RAW_QUEUE")
            queue.deqoptions.deliverymode = oracledb.MSG_BUFFERED
            queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
            queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
            queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
            props = await queue.deqone()
            value = props.payload
            results = value
            await other_conn.commit()
            self.assertEqual(results, self.raw_data[0])

    async def test_7910(self):
        "7910 - test enqueue/dequeue delivery modes identical - persistent"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=value)
        await queue.enqone(props)

        async with test_env.get_connection_async() as other_conn:
            queue = other_conn.queue("TEST_RAW_QUEUE")
            queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
            queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
            queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
            queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
            props = await queue.deqone()
            value = props.payload
            results = value
            await other_conn.commit()
            self.assertEqual(results, self.raw_data[0])

    async def test_7911(self):
        "7911 - test enqueue/dequeue delivery modes the same"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=value)
        await queue.enqone(props)

        async with test_env.get_connection_async() as other_conn:
            queue = other_conn.queue("TEST_RAW_QUEUE")
            queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
            queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
            queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
            queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
            props = await queue.deqone()
            value = props.payload
            results = value
            await other_conn.commit()
            self.assertEqual(results, self.raw_data[0])

    async def test_7912(self):
        "7912 - test enqueue/dequeue delivery modes different"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=value)
        await queue.enqone(props)

        async with test_env.get_connection_async() as other_conn:
            queue = other_conn.queue("TEST_RAW_QUEUE")
            queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
            queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
            queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
            queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
            props = await queue.deqone()
            self.assertIsNone(props)

    async def test_7913(self):
        "7913 - test error for message with no payload"
        queue = self.conn.queue("TEST_RAW_QUEUE")
        props = self.conn.msgproperties()
        with self.assertRaisesFullCode("DPY-2000"):
            await queue.enqone(props)

    async def test_7914(self):
        "7914 - verify that the msgid property is returned correctly"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        props = self.conn.msgproperties(payload=value)
        self.assertIsNone(props.msgid)
        await queue.enqone(props)
        await self.cursor.execute("select msgid from RAW_QUEUE_TAB")
        (actual_msgid,) = await self.cursor.fetchone()
        self.assertEqual(props.msgid, actual_msgid)
        props = await queue.deqone()
        self.assertEqual(props.msgid, actual_msgid)

    async def test_7915(self):
        "7915 - test message props enqtime"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        await self.cursor.execute("select current_timestamp from dual")
        (start_date,) = await self.cursor.fetchone()
        start_date = start_date.replace(microsecond=0)
        props = self.conn.msgproperties(payload=value)
        await queue.enqone(props)
        props = await queue.deqone()
        await self.cursor.execute("select current_timestamp from dual")
        (end_date,) = await self.cursor.fetchone()
        end_date = end_date.replace(microsecond=0)
        self.assertTrue(start_date <= props.enqtime <= end_date)

    async def test_7916(self):
        "7916 - test message props declared attributes"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        values = dict(
            payload=value,
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

    async def test_7917(self):
        "7917 - test getting queue attributes"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        self.assertEqual(queue.name, "TEST_RAW_QUEUE")
        self.assertEqual(queue.connection, self.conn)

    async def test_7918(self):
        "7918 - test getting write-only attributes"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        for options in (queue.enqoptions, queue.deqoptions):
            with self.assertRaises(AttributeError):
                options.deliverymode

    async def test_7919(self):
        "7919 - test deqoption condition with priority"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        priorities = [5, 5, 5, 5, 10, 9, 9, 10, 9]
        for priority in priorities:
            value = self.raw_data[0]
            props = self.conn.msgproperties(payload=value, priority=priority)
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

    async def test_7920(self):
        "7920 - test deqoption correlation"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        correlations = [
            "sample",
            "sample correlation",
            "sample",
            "sample",
            "sample correlation",
        ]
        for correlation in correlations:
            value = self.raw_data[0]
            props = self.conn.msgproperties(
                payload=value, correlation=correlation
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

    async def test_7921(self):
        "7921 - test deqoption msgid"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        props = self.conn.msgproperties(payload=value)
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

    async def test_7922(self):
        "7922 - test payload_type returns the correct value"
        queue = self.conn.queue("TEST_RAW_QUEUE")
        self.assertIsNone(queue.payload_type)

    async def test_7923(self):
        "7923 - test deprecated attributes (enqOptions, deqOptions)"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        self.assertEqual(queue.enqOptions, queue.enqoptions)
        self.assertEqual(queue.deqOptions, queue.deqoptions)

    async def test_7924(self):
        "7924 - test wrong payload type"
        queue = await self.get_and_clear_queue("TEST_RAW_QUEUE")
        typ = await self.conn.gettype("UDT_BOOK")
        obj = typ.newobject()
        props = self.conn.msgproperties(payload=obj)
        with self.assertRaisesFullCode("DPY-2062"):
            await queue.enqone(props)


if __name__ == "__main__":
    test_env.run_test_cases()
