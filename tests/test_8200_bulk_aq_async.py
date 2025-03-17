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
8200 - Module for testing AQ Bulk enqueue/dequeue with asyncio
"""

import datetime
import threading
import unittest

import oracledb
import test_env

RAW_QUEUE_NAME = "TEST_RAW_QUEUE"
JSON_QUEUE_NAME = "TEST_JSON_QUEUE"
RAW_PAYLOAD_DATA = [
    "The first message",
    "The second message",
    "The third message",
    "The fourth message",
    "The fifth message",
    "The sixth message",
    "The seventh message",
    "The eighth message",
    "The ninth message",
    "The tenth message",
    "The eleventh message",
    "The twelfth and final message",
]

JSON_DATA_PAYLOAD = [
    [
        2.75,
        True,
        "Ocean Beach",
        b"Some bytes",
        {"keyA": 1.0, "KeyB": "Melbourne"},
        datetime.datetime(2022, 8, 1, 0, 0),
    ],
    dict(name="John", age=30, city="New York"),
]


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    async def __deq_in_thread(self, results):
        async with test_env.get_connection_async() as conn:
            queue = conn.queue(RAW_QUEUE_NAME)
            queue.deqoptions.wait = 10
            queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
            while len(results) < len(RAW_PAYLOAD_DATA):
                messages = await queue.deqmany(5)
                if not messages:
                    break
                for message in messages:
                    results.append(message.payload.decode())
            await conn.commit()

    async def test_8200(self):
        "8200 - test bulk enqueue and dequeue"
        queue = await self.get_and_clear_queue(RAW_QUEUE_NAME)
        messages = [
            self.conn.msgproperties(payload=data) for data in RAW_PAYLOAD_DATA
        ]
        await queue.enqmany(messages)
        messages = await queue.deqmany(len(RAW_PAYLOAD_DATA))
        data = [message.payload.decode() for message in messages]
        await self.conn.commit()
        self.assertEqual(data, RAW_PAYLOAD_DATA)

    async def test_8201(self):
        "8201 - test empty bulk dequeue"
        queue = await self.get_and_clear_queue(RAW_QUEUE_NAME)
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        messages = await queue.deqmany(5)
        await self.conn.commit()
        self.assertEqual(messages, [])

    @unittest.skipIf(
        test_env.get_is_thin(), "thin mode doesn't support enq immediate yet"
    )
    async def test_8202(self):
        "8202 - test bulk dequeue with wait"
        queue = await self.get_and_clear_queue(RAW_QUEUE_NAME)
        results = []
        thread = threading.Thread(target=self.__deq_in_thread, args=(results,))
        thread.start()
        messages = [
            self.conn.msgproperties(payload=data) for data in RAW_PAYLOAD_DATA
        ]
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        await queue.enqmany(messages)
        thread.join()
        self.assertEqual(results, RAW_PAYLOAD_DATA)

    async def test_8203(self):
        "8203 - test enqueue and dequeue multiple times"
        queue = await self.get_and_clear_queue(RAW_QUEUE_NAME)
        data_to_enqueue = RAW_PAYLOAD_DATA
        for num in (2, 6, 4):
            messages = [
                self.conn.msgproperties(payload=data)
                for data in data_to_enqueue[:num]
            ]
            data_to_enqueue = data_to_enqueue[num:]
            await queue.enqmany(messages)
        await self.conn.commit()
        all_data = []
        for num in (3, 5, 10):
            messages = await queue.deqmany(num)
            all_data.extend(message.payload.decode() for message in messages)
        await self.conn.commit()
        self.assertEqual(all_data, RAW_PAYLOAD_DATA)

    @unittest.skipIf(
        test_env.get_is_thin(), "thin mode doesn't support enq immediate yet"
    )
    async def test_8204(self):
        "8204 - test visibility option for enqueue and dequeue"
        queue = await self.get_and_clear_queue(RAW_QUEUE_NAME)

        # first test with ENQ_ON_COMMIT (commit required)
        queue.enqoptions.visibility = oracledb.ENQ_ON_COMMIT
        props1 = self.conn.msgproperties(payload="A first message")
        props2 = self.conn.msgproperties(payload="A second message")
        await queue.enqmany([props1, props2])
        async with test_env.get_connection_async() as other_conn:
            other_queue = other_conn.queue(RAW_QUEUE_NAME)
            other_queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
            other_queue.deqoptions.visibility = oracledb.DEQ_ON_COMMIT
            messages = await other_queue.deqmany(5)
            self.assertEqual(len(messages), 0)
            await self.conn.commit()
            messages = await other_queue.deqmany(5)
            self.assertEqual(len(messages), 2)
            await other_conn.rollback()

            # second test with ENQ_IMMEDIATE (no commit required)
            queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
            other_queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
            queue.enqmany([props1, props2])
            messages = await other_queue.deqmany(5)
            self.assertEqual(len(messages), 4)
            await other_conn.rollback()
            messages = await other_queue.deqmany(5)
            self.assertEqual(len(messages), 0)

    async def test_8205(self):
        "8205 - test error for messages with no payload"
        queue = await self.get_and_clear_queue(RAW_QUEUE_NAME)
        messages = [self.conn.msgproperties() for _ in RAW_PAYLOAD_DATA]
        with self.assertRaisesFullCode("DPY-2000"):
            await queue.enqmany(messages)

    async def test_8206(self):
        "8206 - verify that the msgid property is returned correctly"
        queue = await self.get_and_clear_queue(RAW_QUEUE_NAME)
        messages = [
            self.conn.msgproperties(payload=data) for data in RAW_PAYLOAD_DATA
        ]
        await queue.enqmany(messages)
        await self.cursor.execute("select msgid from raw_queue_tab")
        actual_msgids = set(m for m, in await self.cursor.fetchall())
        msgids = set(message.msgid for message in messages)
        self.assertEqual(msgids, actual_msgids)
        messages = await queue.deqmany(len(RAW_PAYLOAD_DATA))
        msgids = set(message.msgid for message in messages)
        self.assertEqual(msgids, actual_msgids)

    async def test_8207(self):
        "4800 - test enqueuing and dequeuing JSON message"
        queue = await self.get_and_clear_queue(JSON_QUEUE_NAME, "JSON")
        props = [
            self.conn.msgproperties(payload=data) for data in JSON_DATA_PAYLOAD
        ]
        await queue.enqmany(props)
        await self.conn.commit()
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        messages = await queue.deqmany(5)
        actual_data = [message.payload for message in messages]
        self.assertEqual(actual_data, JSON_DATA_PAYLOAD)

    async def test_8208(self):
        "8208 - test enqueuing to a JSON queue without a JSON payload"
        queue = await self.get_and_clear_queue(JSON_QUEUE_NAME, "JSON")
        props = self.conn.msgproperties(payload="string message")
        with self.assertRaisesFullCode("DPY-2062"):
            await queue.enqmany([props, props])

    async def test_8209(self):
        "8209 - test errors for invalid values for enqmany and deqmany"
        queue = await self.get_and_clear_queue(JSON_QUEUE_NAME, "JSON")
        props = self.conn.msgproperties(payload="string message")
        with self.assertRaises(TypeError):
            await queue.enqmany(props)
        with self.assertRaises(TypeError):
            await queue.enqmany(["Not", "msgproperties"])
        with self.assertRaises(TypeError):
            await queue.deqmany("5")


if __name__ == "__main__":
    test_env.run_test_cases()
