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
8400 - Module for testing AQ with DbObject payloads with asyncio.
"""

import decimal
import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    book_type_name = "UDT_BOOK"
    book_queue_name = "TEST_BOOK_QUEUE"
    book_data = [
        ("Wings of Fire", "A.P.J. Abdul Kalam", decimal.Decimal("15.75")),
        ("The Story of My Life", "Hellen Keller", decimal.Decimal("10.50")),
        ("The Chronicles of Narnia", "C.S. Lewis", decimal.Decimal("25.25")),
    ]

    def __verify_attr(self, obj, attrName, value):
        setattr(obj, attrName, value)
        self.assertEqual(getattr(obj, attrName), value)

    async def test_8400(self):
        "8400 - test dequeuing an empty queue"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = await queue.deqone()
        self.assertIsNone(props)

    async def test_8401(self):
        "8401 - test enqueuing and dequeuing multiple messages"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        props = self.conn.msgproperties()
        for title, authors, price in self.book_data:
            props.payload = book = queue.payload_type.newobject()
            book.TITLE = title
            book.AUTHORS = authors
            book.PRICE = price
            await queue.enqone(props)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        results = []
        while True:
            props = await queue.deqone()
            if props is None:
                break
            book = props.payload
            row = (book.TITLE, book.AUTHORS, book.PRICE)
            results.append(row)
        await self.conn.commit()
        self.assertEqual(results, self.book_data)

    async def test_8402(self):
        "8402 - test dequeuing with DEQ_REMOVE_NODATA option"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[1]
        props = self.conn.msgproperties(payload=book)
        await queue.enqone(props)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.mode = oracledb.DEQ_REMOVE_NODATA
        props = await queue.deqone()
        self.assertIsNotNone(props)
        self.assertIsNone(props.payload.TITLE)

    async def test_8403(self):
        "8403 - test getting/setting dequeue options attributes"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
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

    async def test_8404(self):
        "8404 - test getting/setting enqueue options attributes"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        options = queue.enqoptions
        self.__verify_attr(options, "visibility", oracledb.ENQ_IMMEDIATE)

    async def test_8405(self):
        "8405 - test errors for invalid values for enqueue"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        with self.assertRaises(TypeError):
            await queue.enqone(book)

    async def test_8406(self):
        "8406 - test getting/setting message properties attributes"
        props = self.conn.msgproperties()
        self.__verify_attr(props, "correlation", "TEST_CORRELATION")
        self.__verify_attr(props, "delay", 60)
        self.__verify_attr(props, "exceptionq", "TEST_EXCEPTIONQ")
        self.__verify_attr(props, "expiration", 30)
        self.assertEqual(props.attempts, 0)
        self.__verify_attr(props, "priority", 1)
        self.assertEqual(props.state, oracledb.MSG_READY)
        self.assertEqual(props.deliverymode, 0)

    async def test_8407(self):
        "8407 - test enqueue visibility option - ENQ_ON_COMMIT"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqoptions.visibility = oracledb.ENQ_ON_COMMIT
        props = self.conn.msgproperties(payload=book)
        await queue.enqone(props)

        async with test_env.get_connection_async() as other_conn:
            books_type = await other_conn.gettype(self.book_type_name)
            queue = other_conn.queue(self.book_queue_name, books_type)
            queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
            queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
            props = await queue.deqone()
            self.assertIsNone(props)
            await self.conn.commit()
            props = await queue.deqone()
            await other_conn.commit()
            self.assertIsNotNone(props)

    async def test_8408(self):
        "8408 - test enqueue visibility option - ENQ_IMMEDIATE"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=book)
        await queue.enqone(props)

        async with test_env.get_connection_async() as other_conn:
            books_type = await other_conn.gettype(self.book_type_name)
            queue = other_conn.queue(self.book_queue_name, books_type)
            queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
            queue.deqoptions.visibility = oracledb.DEQ_ON_COMMIT
            queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
            props = await queue.deqone()
            book = props.payload
            results = (book.TITLE, book.AUTHORS, book.PRICE)
            await other_conn.commit()
            self.assertEqual(results, self.book_data[0])

    async def test_8409(self):
        "8409 - test enqueue/dequeue delivery modes identical - buffered"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=book)
        await queue.enqone(props)

        async with test_env.get_connection_async() as other_conn:
            books_type = await other_conn.gettype(self.book_type_name)
            queue = other_conn.queue(self.book_queue_name, books_type)
            queue.deqoptions.deliverymode = oracledb.MSG_BUFFERED
            queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
            queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
            queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
            props = await queue.deqone()
            book = props.payload
            results = (book.TITLE, book.AUTHORS, book.PRICE)
            await other_conn.commit()
            self.assertEqual(results, self.book_data[0])

    async def test_8410(self):
        "8410 - test enqueue/dequeue delivery modes identical - persistent"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=book)
        await queue.enqone(props)

        async with test_env.get_connection_async() as other_conn:
            books_type = await other_conn.gettype(self.book_type_name)
            queue = other_conn.queue(self.book_queue_name, books_type)
            queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
            queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
            queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
            queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
            props = await queue.deqone()
            book = props.payload
            results = (book.TITLE, book.AUTHORS, book.PRICE)
            await other_conn.commit()
            self.assertEqual(results, self.book_data[0])

    async def test_8411(self):
        "8411 - test enqueue/dequeue delivery modes the same"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=book)
        await queue.enqone(props)

        async with test_env.get_connection_async() as other_conn:
            books_type = await other_conn.gettype(self.book_type_name)
            queue = other_conn.queue(self.book_queue_name, books_type)
            queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
            queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
            queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
            queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
            props = await queue.deqone()
            book = props.payload
            results = (book.TITLE, book.AUTHORS, book.PRICE)
            await other_conn.commit()
            self.assertEqual(results, self.book_data[0])

    async def test_8412(self):
        "8412 - test enqueue/dequeue delivery modes different"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=book)
        await queue.enqone(props)

        async with test_env.get_connection_async() as other_conn:
            books_type = await other_conn.gettype(self.book_type_name)
            queue = other_conn.queue(self.book_queue_name, books_type)
            queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
            queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
            queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
            queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
            props = await queue.deqone()
            self.assertIsNone(props)

    async def test_8413(self):
        "8413 - test error for message with no payload"
        books_type = await self.conn.gettype(self.book_type_name)
        queue = self.conn.queue(self.book_queue_name, books_type)
        props = self.conn.msgproperties()
        with self.assertRaisesFullCode("DPY-2000"):
            await queue.enqone(props)

    async def test_8414(self):
        "8414 - verify that the msgid property is returned correctly"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        props = self.conn.msgproperties(payload=book)
        self.assertIsNone(props.msgid)
        await queue.enqone(props)
        await self.cursor.execute("select msgid from book_queue_tab")
        (actual_msgid,) = await self.cursor.fetchone()
        self.assertEqual(props.msgid, actual_msgid)
        props = await queue.deqone()
        self.assertEqual(props.msgid, actual_msgid)

    async def test_8415(self):
        "8415 - test message props enqtime"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        await self.cursor.execute("select current_timestamp from dual")
        (start_date,) = await self.cursor.fetchone()
        start_date = start_date.replace(microsecond=0)
        props = self.conn.msgproperties(payload=book)
        await queue.enqone(props)
        props = await queue.deqone()
        await self.cursor.execute("select current_timestamp from dual")
        (end_date,) = await self.cursor.fetchone()
        end_date = end_date.replace(microsecond=0)
        self.assertTrue(start_date <= props.enqtime <= end_date)

    async def test_8416(self):
        "8416 - test message props declared attributes"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        values = dict(
            payload=book,
            correlation="TEST_CORRELATION",
            delay=7,
            exceptionq="TEST_EXCEPTIONQ",
            expiration=10,
            priority=1,
        )
        props = self.conn.msgproperties(**values)
        for attr_name in values:
            self.assertEqual(getattr(props, attr_name), values[attr_name])

    async def test_8417(self):
        "8417 - test error for invalid type for payload_type"
        self.assertRaises(
            TypeError, self.conn.queue, "THE QUEUE", payload_type=4
        )

    async def test_8418(self):
        "8418 - test getting queue attributes"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        self.assertEqual(queue.name, self.book_queue_name)
        self.assertEqual(queue.connection, self.conn)

    async def test_8419(self):
        "8419 - test getting write-only attributes"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        with self.assertRaises(AttributeError):
            queue.enqoptions.deliverymode
        with self.assertRaises(AttributeError):
            queue.deqoptions.deliverymode

    async def test_8420(self):
        "8420 - test correlation deqoption"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        correlations = ["Math", "Programming"]
        num_messages = 3
        messages = [
            self.conn.msgproperties(payload=book, correlation=c)
            for c in correlations
            for i in range(num_messages)
        ]
        await queue.enqmany(messages)
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.correlation = correlations[0]
        correlated_messages = await queue.deqmany(num_messages + 1)
        self.assertEqual(len(correlated_messages), num_messages)

        queue.deqoptions.correlation = correlations[1]
        with self.assertRaisesFullCode("ORA-25241"):
            await queue.deqone()
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        correlated_messages = await queue.deqmany(num_messages + 1)
        self.assertEqual(len(correlated_messages), num_messages)

    async def test_8421(self):
        "8421 - test correlation deqoption with pattern-matching characters"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        for correlation in ("PreCalculus-math1", "Calculus-Math2"):
            props = self.conn.msgproperties(
                payload=book, correlation=correlation
            )
            await queue.enqone(props)
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.correlation = "%Calculus-%ath_"
        messages = await queue.deqmany(5)
        self.assertEqual(len(messages), 2)

    async def test_8422(self):
        "8422 - test condition deqoption with priority"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT

        priorities = [5, 10]
        indexes = [0, 1]
        for priority, ix in zip(priorities, indexes):
            book = queue.payload_type.newobject()
            book.TITLE, book.AUTHORS, book.PRICE = self.book_data[ix]
            props = self.conn.msgproperties(payload=book, priority=priority)
            await queue.enqone(props)

        queue.deqoptions.condition = "priority = 9"
        messages = await queue.deqmany(3)
        self.assertEqual(len(messages), 0)

        for priority, ix in zip(priorities, indexes):
            queue.deqoptions.condition = f"priority = {priority}"
            messages = await queue.deqmany(3)
            self.assertEqual(len(messages), 1)
            book = messages[0].payload
            data = book.TITLE, book.AUTHORS, book.PRICE
            self.assertEqual(data, self.book_data[ix])

    async def test_8423(self):
        "8423 - test mode deqoption with DEQ_REMOVE_NODATA"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.mode = oracledb.DEQ_REMOVE_NODATA

        book = queue.payload_type.newobject()
        for data in self.book_data:
            book.TITLE, book.AUTHORS, book.PRICE = data
            props = self.conn.msgproperties(payload=book)
            await queue.enqone(props)

        messages = await queue.deqmany(5)
        self.assertEqual(len(messages), 3)
        for message in messages:
            self.assertIsNone(message.payload.TITLE)
            self.assertIsNone(message.payload.AUTHORS)
            self.assertIsNone(message.payload.PRICE)

    async def test_8424(self):
        "8424 - test payload_type returns the correct value"
        books_type = await self.conn.gettype(self.book_type_name)
        queue = self.conn.queue(self.book_queue_name, books_type)
        self.assertEqual(queue.payload_type, books_type)

    async def test_8425(self):
        "8425 - test enqueuing to an object queue with the wrong payload"
        queue = await self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        props = self.conn.msgproperties(payload="A string")
        with self.assertRaisesFullCode("DPY-2062"):
            await queue.enqone(props)


if __name__ == "__main__":
    test_env.run_test_cases()
