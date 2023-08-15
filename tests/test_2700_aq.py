#------------------------------------------------------------------------------
# Copyright (c) 2020, 2023, Oracle and/or its affiliates.
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
2700 - Module for testing AQ
"""

import datetime
import decimal
import threading
import unittest

import oracledb
import test_env

@unittest.skipIf(test_env.get_is_thin(), "thin mode doesn't support AQ yet")
class TestCase(test_env.BaseTestCase):
    book_type_name = "UDT_BOOK"
    book_queue_name = "TEST_BOOK_QUEUE"
    book_data = [
        ("Wings of Fire", "A.P.J. Abdul Kalam", decimal.Decimal("15.75")),
        ("The Story of My Life", "Hellen Keller", decimal.Decimal("10.50")),
        ("The Chronicles of Narnia", "C.S. Lewis", decimal.Decimal("25.25"))
    ]
    json_queue_name = "TEST_JSON_QUEUE"
    json_data = [
        [
            2.75,
            True,
            'Ocean Beach',
            b'Some bytes',
            {'keyA': 1.0, 'KeyB': 'Melbourne'},
            datetime.datetime(2022, 8, 1, 0, 0)
        ],
        [
            True,
            False,
            'String',
            b'Some Bytes',
            {},
            {"name": None},
            {"name": "John"},
            {"age": 30},
            {"Permanent": True},
            {
                "employee": {
                    "name":"John",
                    "age": 30,
                    "city": "Delhi",
                    "Parmanent": True
                }
            },
            {
                "employees": ["John", "Matthew", "James"]
            },
            {
                "employees": [
                    {
                        "employee1": {"name": "John", "city": "Delhi"}
                    },
                    {
                        "employee2": {"name": "Matthew", "city": "Mumbai"}
                    },
                    {
                        "employee3": {"name": "James", "city": "Bangalore"}
                    }
                ]
            }
        ],
        [
            datetime.datetime.today(),
            datetime.datetime(2004, 2, 1, 3, 4, 5),
            datetime.datetime(2020, 12, 2, 13, 29, 14),
            datetime.timedelta(8.5),
            datetime.datetime(2002, 12, 13, 9, 36, 0),
            oracledb.Timestamp(2002, 12, 13, 9, 36, 0),
            datetime.datetime(2002, 12, 13)
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
            decimal.Decimal("319438950232418390.273596")
        ]
    ]

    def __deq_in_thread(self, results):
        with test_env.get_connection() as connection:
            books_type = connection.gettype(self.book_type_name)
            queue = connection.queue(self.book_queue_name, books_type)
            queue.deqoptions.wait = 10
            props = queue.deqone()
            if props is not None:
                book = props.payload
                results.append((book.TITLE, book.AUTHORS, book.PRICE))
            connection.commit()

    def __verify_attr(self, obj, attrName, value):
        setattr(obj, attrName, value)
        self.assertEqual(getattr(obj, attrName), value)

    def test_2700_deq_empty(self):
        "2700 - test dequeuing an empty queue"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        self.assertTrue(props is None)

    def test_2701_deq_enq(self):
        "2701 - test enqueuing and dequeuing multiple messages"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        props = self.connection.msgproperties()
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
        self.connection.commit()
        self.assertEqual(results, self.book_data)

    def test_2702_deq_mode_remove_no_data(self):
        "2702 - test dequeuing with DEQ_REMOVE_NODATA option"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        book = queue.payload_type.newobject()
        title, authors, price = self.book_data[1]
        book.TITLE = title
        book.AUTHORS = authors
        book.PRICE = price
        props = self.connection.msgproperties(payload=book)
        queue.enqone(props)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.mode = oracledb.DEQ_REMOVE_NODATA
        props = queue.deqone()
        self.assertTrue(props is not None)
        self.assertTrue(props.payload.TITLE is None)

    def test_2703_deq_options(self):
        "2703 - test getting/setting dequeue options attributes"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        options = queue.deqoptions
        self.__verify_attr(options, "condition", "TEST_CONDITION")
        self.__verify_attr(options, "consumername", "TEST_CONSUMERNAME")
        self.__verify_attr(options, "correlation", "TEST_CORRELATION")
        self.__verify_attr(options, "mode", oracledb.DEQ_LOCKED)
        self.__verify_attr(options, "navigation",
                           oracledb.DEQ_NEXT_TRANSACTION)
        self.__verify_attr(options, "transformation", "TEST_TRANSFORMATION")
        self.__verify_attr(options, "visibility", oracledb.ENQ_IMMEDIATE)
        self.__verify_attr(options, "wait", 1287)
        self.__verify_attr(options, "msgid", b'mID')

    def test_2704_deq_with_wait(self):
        "2704 - test waiting for dequeue"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        results = []
        thread = threading.Thread(target=self.__deq_in_thread, args=(results,))
        thread.start()
        book = queue.payload_type.newobject()
        title, authors, price = self.book_data[0]
        book.TITLE = title
        book.AUTHORS = authors
        book.PRICE = price
        props = self.connection.msgproperties(payload=book)
        queue.enqone(props)
        self.connection.commit()
        thread.join()
        self.assertEqual(results, [(title, authors, price)])

    def test_2705_enq_options(self):
        "2705 - test getting/setting enqueue options attributes"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        options = queue.enqoptions
        self.__verify_attr(options, "visibility", oracledb.ENQ_IMMEDIATE)

    def test_2706_errors_for_invalid_values(self):
        "2706 - test errors for invalid values for enqueue"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        book = queue.payload_type.newobject()
        self.assertRaises(TypeError, queue.enqone, book)

    def test_2707_msg_props(self):
        "2707 - test getting/setting message properties attributes"
        props = self.connection.msgproperties()
        self.__verify_attr(props, "correlation", "TEST_CORRELATION")
        self.__verify_attr(props, "delay", 60)
        self.__verify_attr(props, "exceptionq", "TEST_EXCEPTIONQ")
        self.__verify_attr(props, "expiration", 30)
        self.assertEqual(props.attempts, 0)
        self.__verify_attr(props, "priority", 1)
        self.assertEqual(props.state, oracledb.MSG_READY)
        self.assertEqual(props.deliverymode, 0)

    def test_2708_visibility_mode_commit(self):
        "2708 - test enqueue visibility option - ENQ_ON_COMMIT"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqoptions.visibility = oracledb.ENQ_ON_COMMIT
        props = self.connection.msgproperties(payload=book)
        queue.enqone(props)

        other_connection = test_env.get_connection()
        books_type = other_connection.gettype(self.book_type_name)
        queue = other_connection.queue(self.book_queue_name, books_type)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        self.assertTrue(props is None)
        self.connection.commit()
        props = queue.deqone()
        self.assertTrue(props is not None)

    def test_2709_visibility_mode_immediate(self):
        "2709 - test enqueue visibility option - ENQ_IMMEDIATE"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.connection.msgproperties(payload=book)
        queue.enqone(props)

        other_connection = test_env.get_connection()
        books_type = other_connection.gettype(self.book_type_name)
        queue = other_connection.queue(self.book_queue_name, books_type)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_ON_COMMIT
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        book = props.payload
        results = (book.TITLE, book.AUTHORS, book.PRICE)
        other_connection.commit()
        self.assertEqual(results, self.book_data[0])

    def test_2710_delivery_mode_same_buffered(self):
        "2710 - test enqueue/dequeue delivery modes identical - buffered"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.connection.msgproperties(payload=book)
        queue.enqone(props)

        other_connection = test_env.get_connection()
        books_type = other_connection.gettype(self.book_type_name)
        queue = other_connection.queue(self.book_queue_name, books_type)
        queue.deqoptions.deliverymode = oracledb.MSG_BUFFERED
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        book = props.payload
        results = (book.TITLE, book.AUTHORS, book.PRICE)
        other_connection.commit()
        self.assertEqual(results, self.book_data[0])

    def test_2711_delivery_mode_same_persistent(self):
        "2711 - test enqueue/dequeue delivery modes identical - persistent"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.connection.msgproperties(payload=book)
        queue.enqone(props)

        other_connection = test_env.get_connection()
        books_type = other_connection.gettype(self.book_type_name)
        queue = other_connection.queue(self.book_queue_name, books_type)
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        book = props.payload
        results = (book.TITLE, book.AUTHORS, book.PRICE)
        other_connection.commit()
        self.assertEqual(results, self.book_data[0])

    def test_2712_delivery_mode_same_persistent_buffered(self):
        "2712 - test enqueue/dequeue delivery modes the same"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.connection.msgproperties(payload=book)
        queue.enqone(props)

        other_connection = test_env.get_connection()
        books_type = other_connection.gettype(self.book_type_name)
        queue = other_connection.queue(self.book_queue_name, books_type)
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        book = props.payload
        results = (book.TITLE, book.AUTHORS, book.PRICE)
        other_connection.commit()
        self.assertEqual(results, self.book_data[0])

    def test_2713_delivery_mode_different(self):
        "2713 - test enqueue/dequeue delivery modes different"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.connection.msgproperties(payload=book)
        queue.enqone(props)

        other_connection = test_env.get_connection()
        books_type = other_connection.gettype(self.book_type_name)
        queue = other_connection.queue(self.book_queue_name, books_type)
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        self.assertTrue(props is None)

    def test_2714_dequeue_transformation(self):
        "2714 - test dequeue transformation"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        expected_price = book.PRICE + 10
        props = self.connection.msgproperties(payload=book)
        queue.enqone(props)
        self.connection.commit()

        other_connection = test_env.get_connection()
        books_type = other_connection.gettype(self.book_type_name)
        queue = other_connection.queue(self.book_queue_name, books_type)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        transformation_str = "%s.transform2" % self.connection.username
        queue.deqoptions.transformation = transformation_str
        self.assertEqual(queue.deqOptions.transformation, transformation_str)
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        self.assertEqual(props.payload.PRICE, expected_price)

    def test_2715_enqueue_transformation(self):
        "2715 - test enqueue transformation"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        expected_price = book.PRICE + 5
        queue.enqoptions.transformation = \
        transformation_str = "%s.transform1" % self.connection.username
        queue.enqoptions.transformation = transformation_str
        if test_env.get_client_version() >= (23, 1):
            self.assertEqual(queue.enqoptions.transformation,
                             transformation_str)
        props = self.connection.msgproperties(payload=book)
        queue.enqone(props)
        self.connection.commit()

        other_connection = test_env.get_connection()
        books_type = other_connection.gettype(self.book_type_name)
        queue = other_connection.queue(self.book_queue_name, books_type)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        self.assertEqual(props.payload.PRICE, expected_price)

    def test_2716_payloadType_deprecation(self):
        "2716 - test to verify payloadType is deprecated"
        books_type = self.connection.gettype(self.book_type_name)
        queue = self.connection.queue(self.book_queue_name,
                                      payloadType=books_type)
        self.assertEqual(queue.payload_type, books_type)
        self.assertEqual(queue.payloadType, books_type)
        self.assertRaisesRegex(oracledb.ProgrammingError, "^DPY-2014:",
                               self.connection.queue, self.book_queue_name,
                               books_type, payloadType=books_type)

    def test_2717_message_with_no_payload(self):
        "2717 - test error for message with no payload"
        books_type = self.connection.gettype(self.book_type_name)
        queue = self.connection.queue(self.book_queue_name, books_type)
        props = self.connection.msgproperties()
        self.assertRaisesRegex(oracledb.ProgrammingError, "^DPY-2000:",
                               queue.enqone, props)

    def test_2718_verify_msgid(self):
        "2718 - verify that the msgid property is returned correctly"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        props = self.connection.msgproperties(payload=book)
        self.assertEqual(props.msgid, None)
        queue.enqone(props)
        self.cursor.execute("select msgid from book_queue_tab")
        actual_msgid, = self.cursor.fetchone()
        self.assertEqual(props.msgid, actual_msgid)
        props = queue.deqone()
        self.assertEqual(props.msgid, actual_msgid)

    def test_2719_recipients_list(self):
        "2719 - verify use of recipients property"
        books_type = self.connection.gettype(self.book_type_name)
        book = books_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue = self.connection.queue("BOOK_QUEUE_MULTI", books_type)
        props = self.connection.msgproperties(payload=book,
                                              recipients=["sub2", "sub3"])
        self.assertEqual(props.recipients, ["sub2", "sub3"])
        queue.enqone(props)
        self.connection.commit()
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.consumername = "sub3"
        props1 = queue.deqone()
        book = props1.payload
        results = (book.TITLE, book.AUTHORS, book.PRICE)
        self.assertEqual(results, self.book_data[0])
        queue.deqoptions.consumername = "sub1"
        props1 = queue.deqone()
        self.assertTrue(props1 is None)

    def test_2720_aq_message_attributes(self):
        "2720 - verify attributes of AQ message which spawned notification"
        if self.is_on_oracle_cloud(self.connection):
            self.skipTest("AQ notification not supported on the cloud")
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        condition = threading.Condition()
        connection = test_env.get_connection(events=True)
        def notification_callback(message):
            self.cursor.execute("select msgid from book_queue_tab")
            actual_msgid, = self.cursor.fetchone()
            self.assertEqual(message.msgid, actual_msgid)
            self.assertEqual(message.consumer_name, None)
            main_user = test_env.get_main_user().upper()
            self.assertEqual(message.queue_name,
                             f'"{main_user}"."{queue.name}"')
            self.assertEqual(message.type, oracledb.EVENT_AQ)
            with condition:
                condition.notify()
        sub = connection.subscribe(namespace=oracledb.SUBSCR_NAMESPACE_AQ,
                                   name=self.book_queue_name,
                                   callback=notification_callback, timeout=300)
        book = queue.payload_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        props = self.connection.msgproperties(payload=book)
        queue.enqone(props)
        self.connection.commit()
        with condition:
            self.assertTrue(condition.wait(5))

    def test_2721_json_enq_deq(self):
        "2721 - test enqueuing and dequeuing JSON payloads"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        self.assertEqual(queue.payload_type, "JSON")
        for data in self.json_data:
            props = self.connection.msgproperties(payload=data)
            queue.enqone(props)
        self.connection.commit()
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        results = []
        while True:
            props = queue.deqone()
            if props is None:
                break
            results.append(props.payload)
        self.connection.commit()
        self.assertEqual(results, self.json_data)

    def test_2722_no_json_payload(self):
        "2722 - test enqueuing to a JSON queue without a JSON payload"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        random_string = "This is a string message"
        props = self.connection.msgproperties(payload=random_string)
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPI-1071:",
                               queue.enqone, props)

    def test_2723_enqtime(self):
        "2723 - test message props enqtime"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        book = queue.payload_type.newobject()
        self.cursor.execute("select sysdate from dual")
        start_date, = self.cursor.fetchone()
        props = self.connection.msgproperties(payload=book)
        queue.enqone(props)
        props = queue.deqone()
        self.cursor.execute("select sysdate from dual")
        end_date, = self.cursor.fetchone()
        self.assertTrue(start_date <= props.enqtime <= end_date)

    def test_2724_msgproperties_constructor(self):
        "2724 - test message props declared attributes"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        book = queue.payload_type.newobject()
        values = dict(payload=book, correlation="TEST_CORRELATION", delay=7,
                      exceptionq="TEST_EXCEPTIONQ", expiration=10, priority=1)
        props = self.connection.msgproperties(**values)
        for attr_name in values:
            self.assertEqual(getattr(props, attr_name), values[attr_name])

    def test_2725_payload_type_negative(self):
        "2725 - test error for invalid type for payload_type"
        self.assertRaises(TypeError, self.connection.queue, "THE QUEUE",
                          payload_type=4)

    def test_2726_set_payload_bytes(self):
        "2726 - test setting bytes to payload"
        props = self.connection.msgproperties()
        bytes_val = b"Hello there"
        props.payload = bytes_val
        self.assertEqual(props.payload, bytes_val)

    def test_2727_queue_attributes(self):
        "2727 - test getting queue attributes"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        self.assertEqual(queue.name, self.book_queue_name)
        self.assertEqual(queue.connection, self.connection)

    def test_2728_get_write_only_attributes(self):
        "2728 - test getting write-only attributes"
        queue = self.get_and_clear_queue(self.book_queue_name,
                                         self.book_type_name)
        with self.assertRaises(AttributeError):
            queue.enqoptions.deliverymode
        with self.assertRaises(AttributeError):
            queue.deqoptions.deliverymode

if __name__ == "__main__":
    test_env.run_test_cases()
