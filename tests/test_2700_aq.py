#------------------------------------------------------------------------------
# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
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

    def __clear_books_queue(self):
        books_type = self.connection.gettype(self.book_type_name)
        queue = self.connection.queue(self.book_queue_name, books_type)
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        while queue.deqone():
            pass

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
        self.__clear_books_queue()
        books_type = self.connection.gettype(self.book_type_name)
        queue = self.connection.queue(self.book_queue_name, books_type)
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        self.assertTrue(props is None)

    def test_2701_deq_enq(self):
        "2701 - test enqueuing and dequeuing multiple messages"
        self.__clear_books_queue()
        books_type = self.connection.gettype(self.book_type_name)
        queue = self.connection.queue(self.book_queue_name, books_type)
        props = self.connection.msgproperties()
        for title, authors, price in self.book_data:
            props.payload = book = books_type.newobject()
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
        self.__clear_books_queue()
        books_type = self.connection.gettype(self.book_type_name)
        queue = self.connection.queue(self.book_queue_name, books_type)
        book = books_type.newobject()
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
        books_type = self.connection.gettype(self.book_type_name)
        queue = self.connection.queue(self.book_queue_name, books_type)
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
        self.__clear_books_queue()
        results = []
        thread = threading.Thread(target=self.__deq_in_thread, args=(results,))
        thread.start()
        books_type = self.connection.gettype(self.book_type_name)
        queue = self.connection.queue(self.book_queue_name, books_type)
        book = books_type.newobject()
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
        books_type = self.connection.gettype(self.book_type_name)
        queue = self.connection.queue(self.book_queue_name, books_type)
        options = queue.enqoptions
        self.__verify_attr(options, "visibility", oracledb.ENQ_IMMEDIATE)

    def test_2706_errors_for_invalid_values(self):
        "2706 - test errors for invalid values for enqueue"
        books_type = self.connection.gettype(self.book_type_name)
        queue = self.connection.queue(self.book_queue_name, books_type)
        book = books_type.newobject()
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
        self.__clear_books_queue()
        books_type = self.connection.gettype(self.book_type_name)
        queue = self.connection.queue(self.book_queue_name, books_type)
        book = books_type.newobject()
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
        self.__clear_books_queue()
        books_type = self.connection.gettype(self.book_type_name)
        queue = self.connection.queue(self.book_queue_name, books_type)
        book = books_type.newobject()
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
        self.__clear_books_queue()
        books_type = self.connection.gettype(self.book_type_name)
        queue = self.connection.queue(self.book_queue_name, books_type)
        book = books_type.newobject()
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
        self.__clear_books_queue()
        books_type = self.connection.gettype(self.book_type_name)
        queue = self.connection.queue(self.book_queue_name, books_type)
        book = books_type.newobject()
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
        self.__clear_books_queue()
        books_type = self.connection.gettype(self.book_type_name)
        queue = self.connection.queue(self.book_queue_name, books_type)
        book = books_type.newobject()
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
        self.__clear_books_queue()
        books_type = self.connection.gettype(self.book_type_name)
        queue = self.connection.queue(self.book_queue_name, books_type)
        book = books_type.newobject()
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
        self.__clear_books_queue()
        books_type = self.connection.gettype(self.book_type_name)
        queue = self.connection.queue(self.book_queue_name, books_type)
        book = books_type.newobject()
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
        queue.deqoptions.transformation = \
                "%s.transform2" % self.connection.username
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        self.assertEqual(props.payload.PRICE, expected_price)

    def test_2715_enqueue_transformation(self):
        "2715 - test enqueue transformation"
        self.__clear_books_queue()
        books_type = self.connection.gettype(self.book_type_name)
        queue = self.connection.queue(self.book_queue_name, books_type)
        book = books_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        expected_price = book.PRICE + 5
        queue.enqoptions.transformation = \
                "%s.transform1" % self.connection.username
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
        self.__clear_books_queue()
        books_type = self.connection.gettype(self.book_type_name)
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
        self.__clear_books_queue()
        books_type = self.connection.gettype(self.book_type_name)
        book = books_type.newobject()
        book.TITLE, book.AUTHORS, book.PRICE = self.book_data[0]
        queue = self.connection.queue(self.book_queue_name, books_type)
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

if __name__ == "__main__":
    test_env.run_test_cases()
