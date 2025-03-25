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
2700 - Module for testing AQ with DbObject payloads.
"""

import decimal
import threading
import unittest

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    book_type_name = "UDT_BOOK"
    book_queue_name = "TEST_BOOK_QUEUE"
    book_data = [
        ("Wings of Fire", "A.P.J. Abdul Kalam", decimal.Decimal("15.75")),
        ("The Story of My Life", "Hellen Keller", decimal.Decimal("10.50")),
        ("The Chronicles of Narnia", "C.S. Lewis", decimal.Decimal("25.25")),
    ]

    def __deq_in_thread(self, results):
        with test_env.get_connection() as conn:
            books_type = conn.gettype(self.book_type_name)
            queue = conn.queue(self.book_queue_name, books_type)
            queue.deqoptions.wait = 10
            props = queue.deqone()
            if props is not None:
                book = props.payload
                results.append((book.TITLE, book.AUTHORS, book.PRICE))
            conn.commit()

    def __verify_attr(self, obj, attrName, value):
        setattr(obj, attrName, value)
        self.assertEqual(getattr(obj, attrName), value)

    def test_2700(self):
        "2700 - test dequeuing an empty queue"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        self.assertIsNone(props)

    def test_2701(self):
        "2701 - test enqueuing and dequeuing multiple messages"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        props = self.conn.msgproperties()
        for title, authors, price in self.book_data:
            props.payload = book = queue.payload_type.newobject()
            book.TITLE = title
            book.AUTHORS = authors
            book.PRICE = price
            queue.enqone(props)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        results = []
        while True:
            props = queue.deqone()
            if props is None:
                break
            book = props.payload
            row = (book.TITLE, book.AUTHORS, book.PRICE)
            results.append(row)
        self.conn.commit()
        self.assertEqual(results, self.book_data)

    def test_2702(self):
        "2702 - test dequeuing with DEQ_REMOVE_NODATA option"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[1]
        props = self.conn.msgproperties(payload=book)
        queue.enqone(props)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.mode = oracledb.DEQ_REMOVE_NODATA
        props = queue.deqone()
        self.assertIsNotNone(props)
        self.assertIsNone(props.payload.TITLE)

    def test_2703(self):
        "2703 - test getting/setting dequeue options attributes"
        queue = self.get_and_clear_queue(
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

    def test_2704(self):
        "2704 - test waiting for dequeue"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        results = []
        thread = threading.Thread(target=self.__deq_in_thread, args=(results,))
        thread.start()
        book = queue.payload_type.newobject()
        title, authors, price = self.book_data[0]
        book.TITLE = title
        book.AUTHORS = authors
        book.PRICE = price
        props = self.conn.msgproperties(payload=book)
        queue.enqone(props)
        self.conn.commit()
        thread.join()
        self.assertEqual(results, [(title, authors, price)])

    def test_2705(self):
        "2705 - test getting/setting enqueue options attributes"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        options = queue.enqoptions
        self.__verify_attr(options, "visibility", oracledb.ENQ_IMMEDIATE)

    def test_2706(self):
        "2706 - test errors for invalid values for enqueue"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        self.assertRaises(TypeError, queue.enqone, book)

    def test_2707(self):
        "2707 - test getting/setting message properties attributes"
        props = self.conn.msgproperties()
        self.__verify_attr(props, "correlation", "TEST_CORRELATION")
        self.__verify_attr(props, "delay", 60)
        self.__verify_attr(props, "exceptionq", "TEST_EXCEPTIONQ")
        self.__verify_attr(props, "expiration", 30)
        self.assertEqual(props.attempts, 0)
        self.__verify_attr(props, "priority", 1)
        self.assertEqual(props.state, oracledb.MSG_READY)
        self.assertEqual(props.deliverymode, 0)

    def test_2708(self):
        "2708 - test enqueue visibility option - ENQ_ON_COMMIT"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqoptions.visibility = oracledb.ENQ_ON_COMMIT
        props = self.conn.msgproperties(payload=book)
        queue.enqone(props)

        other_conn = test_env.get_connection()
        books_type = other_conn.gettype(self.book_type_name)
        queue = other_conn.queue(self.book_queue_name, books_type)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        self.assertIsNone(props)
        self.conn.commit()
        props = queue.deqone()
        other_conn.commit()
        self.assertIsNotNone(props)

    def test_2709(self):
        "2709 - test enqueue visibility option - ENQ_IMMEDIATE"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=book)
        queue.enqone(props)

        other_conn = test_env.get_connection()
        books_type = other_conn.gettype(self.book_type_name)
        queue = other_conn.queue(self.book_queue_name, books_type)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_ON_COMMIT
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        book = props.payload
        results = (book.TITLE, book.AUTHORS, book.PRICE)
        other_conn.commit()
        self.assertEqual(results, self.book_data[0])

    def test_2710(self):
        "2710 - test enqueue/dequeue delivery modes identical - buffered"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=book)
        queue.enqone(props)

        other_conn = test_env.get_connection()
        books_type = other_conn.gettype(self.book_type_name)
        queue = other_conn.queue(self.book_queue_name, books_type)
        queue.deqoptions.deliverymode = oracledb.MSG_BUFFERED
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        book = props.payload
        results = (book.TITLE, book.AUTHORS, book.PRICE)
        other_conn.commit()
        self.assertEqual(results, self.book_data[0])

    def test_2711(self):
        "2711 - test enqueue/dequeue delivery modes identical - persistent"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=book)
        queue.enqone(props)

        other_conn = test_env.get_connection()
        books_type = other_conn.gettype(self.book_type_name)
        queue = other_conn.queue(self.book_queue_name, books_type)
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        book = props.payload
        results = (book.TITLE, book.AUTHORS, book.PRICE)
        other_conn.commit()
        self.assertEqual(results, self.book_data[0])

    def test_2712(self):
        "2712 - test enqueue/dequeue delivery modes the same"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=book)
        queue.enqone(props)

        other_conn = test_env.get_connection()
        books_type = other_conn.gettype(self.book_type_name)
        queue = other_conn.queue(self.book_queue_name, books_type)
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        book = props.payload
        results = (book.TITLE, book.AUTHORS, book.PRICE)
        other_conn.commit()
        self.assertEqual(results, self.book_data[0])

    def test_2713(self):
        "2713 - test enqueue/dequeue delivery modes different"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=book)
        queue.enqone(props)

        other_conn = test_env.get_connection()
        books_type = other_conn.gettype(self.book_type_name)
        queue = other_conn.queue(self.book_queue_name, books_type)
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        self.assertIsNone(props)

    @unittest.skipIf(
        test_env.get_is_thin(), "Thin mode doesn't support transformation yet"
    )
    def test_2714(self):
        "2714 - test dequeue transformation"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        expected_price = book.PRICE + 10
        props = self.conn.msgproperties(payload=book)
        queue.enqone(props)
        self.conn.commit()

        other_conn = test_env.get_connection()
        books_type = other_conn.gettype(self.book_type_name)
        queue = other_conn.queue(self.book_queue_name, books_type)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        transformation_str = f"{self.conn.username}.transform2"
        queue.deqoptions.transformation = transformation_str
        self.assertEqual(queue.deqoptions.transformation, transformation_str)
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        self.assertEqual(props.payload.PRICE, expected_price)

    @unittest.skipIf(
        test_env.get_is_thin(), "Thin mode doesn't support transformation yet"
    )
    def test_2715(self):
        "2715 - test enqueue transformation"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        expected_price = book.PRICE + 5
        queue.enqoptions.transformation = transformation_str = (
            f"{self.conn.username}.transform1"
        )
        queue.enqoptions.transformation = transformation_str
        if test_env.get_client_version() >= (23, 1):
            self.assertEqual(
                queue.enqoptions.transformation, transformation_str
            )
        props = self.conn.msgproperties(payload=book)
        queue.enqone(props)
        self.conn.commit()

        other_conn = test_env.get_connection()
        books_type = other_conn.gettype(self.book_type_name)
        queue = other_conn.queue(self.book_queue_name, books_type)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        self.assertEqual(props.payload.PRICE, expected_price)

    def test_2716(self):
        "2716 - test to verify payloadType is deprecated"
        books_type = self.conn.gettype(self.book_type_name)
        queue = self.conn.queue(self.book_queue_name, payloadType=books_type)
        self.assertEqual(queue.payload_type, books_type)
        self.assertEqual(queue.payloadType, books_type)
        with self.assertRaisesFullCode("DPY-2014"):
            self.conn.queue(
                self.book_queue_name, books_type, payloadType=books_type
            )

    def test_2717(self):
        "2717 - test error for message with no payload"
        books_type = self.conn.gettype(self.book_type_name)
        queue = self.conn.queue(self.book_queue_name, books_type)
        props = self.conn.msgproperties()
        with self.assertRaisesFullCode("DPY-2000"):
            queue.enqone(props)

    def test_2718(self):
        "2718 - verify that the msgid property is returned correctly"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        props = self.conn.msgproperties(payload=book)
        self.assertIsNone(props.msgid)
        queue.enqone(props)
        self.cursor.execute("select msgid from book_queue_tab")
        (actual_msgid,) = self.cursor.fetchone()
        self.assertEqual(props.msgid, actual_msgid)
        props = queue.deqone()
        self.assertEqual(props.msgid, actual_msgid)

    @unittest.skipIf(
        test_env.get_is_thin(), "Thin mode doesn't support recipient list yet"
    )
    def test_2719(self):
        "2719 - verify use of recipients property"
        books_type = self.conn.gettype(self.book_type_name)
        book = books_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue = self.conn.queue("BOOK_QUEUE_MULTI", books_type)
        props = self.conn.msgproperties(
            payload=book, recipients=["sub2", "sub3"]
        )
        self.assertEqual(props.recipients, ["sub2", "sub3"])
        queue.enqone(props)
        self.conn.commit()
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.consumername = "sub3"
        props1 = queue.deqone()
        book = props1.payload
        results = (book.TITLE, book.AUTHORS, book.PRICE)
        self.assertEqual(results, self.book_data[0])
        queue.deqoptions.consumername = "sub1"
        props1 = queue.deqone()
        self.assertIsNone(props1)

    @unittest.skipIf(
        test_env.get_is_thin(), "thin mode doesn't support notification yet"
    )
    def test_2720(self):
        "2720 - verify attributes of AQ message which spawned notification"
        if self.is_on_oracle_cloud(self.conn):
            self.skipTest("AQ notification not supported on the cloud")
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        condition = threading.Condition()
        conn = test_env.get_connection(events=True)

        def notification_callback(message):
            self.cursor.execute("select msgid from book_queue_tab")
            (actual_msgid,) = self.cursor.fetchone()
            self.assertEqual(message.msgid, actual_msgid)
            self.assertIsNone(message.consumer_name)
            main_user = test_env.get_main_user().upper()
            self.assertEqual(
                message.queue_name, f'"{main_user}"."{queue.name}"'
            )
            self.assertEqual(message.type, oracledb.EVENT_AQ)
            with condition:
                condition.notify()

        sub = conn.subscribe(
            namespace=oracledb.SUBSCR_NAMESPACE_AQ,
            name=self.book_queue_name,
            timeout=300,
            callback=notification_callback,
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        props = self.conn.msgproperties(payload=book)
        queue.enqone(props)
        self.conn.commit()
        with condition:
            self.assertTrue(condition.wait(5))
        conn.unsubscribe(sub)

    def test_2721(self):
        "2721 - test message props enqtime"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        self.cursor.execute("select current_timestamp from dual")
        (start_date,) = self.cursor.fetchone()
        start_date = start_date.replace(microsecond=0)
        props = self.conn.msgproperties(payload=book)
        queue.enqone(props)
        props = queue.deqone()
        self.cursor.execute("select current_timestamp from dual")
        (end_date,) = self.cursor.fetchone()
        end_date = end_date.replace(microsecond=0)
        self.assertTrue(start_date <= props.enqtime <= end_date)

    def test_2722(self):
        "2722 - test message props declared attributes"
        queue = self.get_and_clear_queue(
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

    def test_2723(self):
        "2723 - test error for invalid type for payload_type"
        self.assertRaises(
            TypeError, self.conn.queue, "THE QUEUE", payload_type=4
        )

    def test_2724(self):
        "2724 - test setting bytes to payload"
        props = self.conn.msgproperties()
        bytes_val = b"Hello there"
        props.payload = bytes_val
        self.assertEqual(props.payload, bytes_val)

    def test_2725(self):
        "2725 - test getting queue attributes"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        self.assertEqual(queue.name, self.book_queue_name)
        self.assertEqual(queue.connection, self.conn)

    def test_2726(self):
        "2726 - test getting write-only attributes"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        with self.assertRaises(AttributeError):
            queue.enqoptions.deliverymode
        with self.assertRaises(AttributeError):
            queue.deqoptions.deliverymode

    def test_2727(self):
        "2727 - test correlation deqoption"
        queue = self.get_and_clear_queue(
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
        queue.enqmany(messages)
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.correlation = correlations[0]
        correlated_messages = queue.deqmany(num_messages + 1)
        self.assertEqual(len(correlated_messages), num_messages)

        queue.deqoptions.correlation = correlations[1]
        with self.assertRaisesFullCode("ORA-25241"):
            queue.deqone()
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        correlated_messages = queue.deqmany(num_messages + 1)
        self.assertEqual(len(correlated_messages), num_messages)

    def test_2728(self):
        "2728 - test correlation deqoption with pattern-matching characters"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        for correlation in ("PreCalculus-math1", "Calculus-Math2"):
            props = self.conn.msgproperties(
                payload=book, correlation=correlation
            )
            queue.enqone(props)
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.correlation = "%Calculus-%ath_"
        messages = queue.deqmany(5)
        self.assertEqual(len(messages), 2)

    def test_2729(self):
        "2729 - test condition deqoption with priority"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT

        priorities = [5, 10]
        indexes = [0, 1]
        for priority, ix in zip(priorities, indexes):
            book = queue.payload_type.newobject()
            book.TITLE, book.AUTHORS, book.PRICE = self.book_data[ix]
            props = self.conn.msgproperties(payload=book, priority=priority)
            queue.enqone(props)

        queue.deqoptions.condition = "priority = 9"
        messages = queue.deqmany(3)
        self.assertEqual(len(messages), 0)

        for priority, ix in zip(priorities, indexes):
            queue.deqoptions.condition = f"priority = {priority}"
            messages = queue.deqmany(3)
            self.assertEqual(len(messages), 1)
            book = messages[0].payload
            data = book.TITLE, book.AUTHORS, book.PRICE
            self.assertEqual(data, self.book_data[ix])

    def test_2730(self):
        "2730 - test mode deqoption with DEQ_REMOVE_NODATA"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.mode = oracledb.DEQ_REMOVE_NODATA

        book = queue.payload_type.newobject()
        for data in self.book_data:
            book.TITLE, book.AUTHORS, book.PRICE = data
            props = self.conn.msgproperties(payload=book)
            queue.enqone(props)

        messages = queue.deqmany(5)
        self.assertEqual(len(messages), 3)
        for message in messages:
            self.assertIsNone(message.payload.TITLE)
            self.assertIsNone(message.payload.AUTHORS)
            self.assertIsNone(message.payload.PRICE)

    def test_2731(self):
        "2731 - test payload_type returns the correct value"
        books_type = self.conn.gettype(self.book_type_name)
        queue = self.conn.queue(self.book_queue_name, books_type)
        self.assertEqual(queue.payload_type, books_type)

    def test_2732(self):
        "2732 - test deprecated attributes (enqOptions, deqOptions)"
        books_type = self.conn.gettype(self.book_type_name)
        queue = self.conn.queue(self.book_queue_name, books_type)
        self.assertEqual(queue.enqOptions, queue.enqoptions)
        self.assertEqual(queue.deqOptions, queue.deqoptions)

    def test_2733(self):
        "2733 - test deprecated AQ methods (enqOne, deqOne)"
        books_type = self.conn.gettype(self.book_type_name)
        queue = self.conn.queue(self.book_queue_name, books_type)
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqOne(self.conn.msgproperties(book))
        props = queue.deqOne()
        book = props.payload
        results = (book.TITLE, book.AUTHORS, book.PRICE)
        self.assertEqual(results, self.book_data[0])

    def test_2734(self):
        "2734 - test enqueuing to an object queue with the wrong payload"
        queue = self.get_and_clear_queue(
            self.book_queue_name, self.book_type_name
        )
        props = self.conn.msgproperties(payload="A string")
        with self.assertRaisesFullCode("DPY-2062"):
            queue.enqone(props)


if __name__ == "__main__":
    test_env.run_test_cases()
