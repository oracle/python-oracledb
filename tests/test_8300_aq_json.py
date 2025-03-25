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
8300 - Module for testing AQ with JSON queues
"""

import datetime
import decimal
import threading
import unittest

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
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

    def __deq_in_thread(self, results):
        with test_env.get_connection() as conn:
            queue = conn.queue(self.json_queue_name, "JSON")
            queue.deqoptions.wait = 10
            props = queue.deqone()
            if props is not None:
                results.append(props.payload)
            conn.commit()

    def __verify_attr(self, obj, attrName, value):
        setattr(obj, attrName, value)
        self.assertEqual(getattr(obj, attrName), value)

    def test_8300(self):
        "8300 - test dequeuing an empty JSON queue"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        self.assertIsNone(props)

    def test_8301(self):
        "8301 - test enqueuing and dequeuing multiple JSON messages"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        props = self.conn.msgproperties()
        for data in self.json_data:
            props.payload = data
            queue.enqone(props)
        self.conn.commit()
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        results = []
        while True:
            props = queue.deqone()
            if props is None:
                break
            results.append(props.payload)
        self.conn.commit()
        self.assertEqual(results, self.json_data)

    @unittest.skip("awaiting fix for bug 37746852")
    def test_8302(self):
        "8302 - test dequeuing with DEQ_REMOVE_NODATA option"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        data = self.json_data[1]
        props = self.conn.msgproperties(payload=data)
        queue.enqone(props)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.mode = oracledb.DEQ_REMOVE_NODATA
        props = queue.deqone()
        self.assertIsNotNone(props)
        self.assertIsNone(props.payload)

    def test_8303(self):
        "8303 - test getting/setting dequeue options attributes"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
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

    def test_8304(self):
        "8304 - test waiting for dequeue"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        results = []
        thread = threading.Thread(target=self.__deq_in_thread, args=(results,))
        thread.start()
        data = self.json_data[0]
        props = self.conn.msgproperties(payload=data)
        queue.enqone(props)
        self.conn.commit()
        thread.join()
        self.assertEqual(results, [data])

    def test_8305(self):
        "8305 - test getting/setting enqueue options attributes"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        options = queue.enqoptions
        self.__verify_attr(options, "visibility", oracledb.ENQ_IMMEDIATE)

    def test_8306(self):
        "8306 - test getting/setting message properties attributes"
        props = self.conn.msgproperties()
        self.__verify_attr(props, "correlation", "TEST_CORRELATION")
        self.__verify_attr(props, "delay", 60)
        self.__verify_attr(props, "exceptionq", "TEST_EXCEPTIONQ")
        self.__verify_attr(props, "expiration", 30)
        self.assertEqual(props.attempts, 0)
        self.__verify_attr(props, "priority", 1)
        self.assertEqual(props.state, oracledb.MSG_READY)
        self.assertEqual(props.deliverymode, 0)

    def test_8307(self):
        "8307 - test enqueue visibility options - ENQ_ON_COMMIT"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        data = self.json_data[0]
        queue.enqoptions.visibility = oracledb.ENQ_ON_COMMIT
        props = self.conn.msgproperties(payload=data)
        queue.enqone(props)

        other_conn = test_env.get_connection()
        queue = other_conn.queue(self.json_queue_name, "JSON")
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        self.assertIsNone(props)
        self.conn.commit()
        props = queue.deqone()
        self.assertIsNotNone(props)

    def test_8308(self):
        "8308 - test enqueue visibility option - ENQ_IMMEDIATE"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        data = self.json_data[0]
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=data)
        queue.enqone(props)

        other_conn = test_env.get_connection()
        queue = other_conn.queue(self.json_queue_name, "JSON")
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_ON_COMMIT
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        data = props.payload
        results = data
        other_conn.commit()
        self.assertEqual(results, self.json_data[0])

    def test_8309(self):
        "8309 - test enqueue/dequeue delivery modes identical - persistent"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        data = self.json_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=data)
        queue.enqone(props)

        other_conn = test_env.get_connection()
        queue = other_conn.queue(self.json_queue_name, "JSON")
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        data = props.payload
        results = data
        other_conn.commit()
        self.assertEqual(results, self.json_data[0])

    def test_8310(self):
        "8310 - test error for message with no payload"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        props = self.conn.msgproperties()
        with self.assertRaisesFullCode("DPY-2000"):
            queue.enqone(props)

    def test_8311(self):
        "8311 - verify that the msgid property is returned correctly"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        data = self.json_data[0]
        props = self.conn.msgproperties(payload=data)
        self.assertIsNone(props.msgid)
        queue.enqone(props)
        self.cursor.execute("select msgid from JSON_QUEUE_TAB")
        (actual_msgid,) = self.cursor.fetchone()
        self.assertEqual(props.msgid, actual_msgid)
        props = queue.deqone()
        self.assertEqual(props.msgid, actual_msgid)

    def test_8312(self):
        "8312 - test message props enqtime"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        data = self.json_data[0]
        self.cursor.execute("select current_timestamp from dual")
        (start_date,) = self.cursor.fetchone()
        start_date = start_date.replace(microsecond=0)
        props = self.conn.msgproperties(payload=data)
        queue.enqone(props)
        props = queue.deqone()
        self.cursor.execute("select current_timestamp from dual")
        (end_date,) = self.cursor.fetchone()
        end_date = end_date.replace(microsecond=0)
        self.assertTrue(start_date <= props.enqtime <= end_date)

    def test_8313(self):
        "8313 - test message props declared attributes"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
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
        queue.enqone(props)
        self.conn.commit()
        prop = queue.deqone()
        for attr_name in values:
            self.assertEqual(getattr(prop, attr_name), values[attr_name])

    def test_8314(self):
        "8314 - test getting queue attributes"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        self.assertEqual(queue.name, "TEST_JSON_QUEUE")
        self.assertEqual(queue.connection, self.conn)

    def test_8315(self):
        "8315 - test getting write-only attributes"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        for options in (queue.enqoptions, queue.deqoptions):
            with self.assertRaises(AttributeError):
                options.deliverymode

    def test_8316(self):
        "8316 - test deqoption condition with priority"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        priorities = [5, 5, 5, 5, 10, 9, 9, 10, 9]
        for priority in priorities:
            data = self.json_data[0]
            props = self.conn.msgproperties(payload=data, priority=priority)
            queue.enqone(props)

        queue.deqoptions.condition = "priority = 9"
        results = []
        while True:
            props = queue.deqone()
            if props is None:
                break
            results.append(props.payload)
        self.conn.commit()
        self.assertEqual(len(results), 3)

    def test_8317(self):
        "8317 - test deqoption correlation"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
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
            queue.enqone(props)
        self.conn.commit()
        queue.deqoptions.correlation = "sample correlation"
        results = []
        while True:
            props = queue.deqone()
            if props is None:
                break
            results.append(props.payload)
        self.conn.commit()
        self.assertEqual(len(results), 2)

    def test_8318(self):
        "8318 - test deqoption msgid"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        data = self.json_data[0]
        props = self.conn.msgproperties(payload=data)
        queue.enqone(props)
        queue.enqone(props)
        self.conn.commit()
        msgid = props.msgid
        queue.enqone(props)
        self.conn.commit()
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.msgid = msgid
        prop = queue.deqone()
        self.conn.commit()
        self.assertEqual(prop.msgid, msgid)

    def test_8319(self):
        "8319 - test payload_type returns the correct value"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        self.assertEqual(queue.payload_type, "JSON")

    def test_8320(self):
        "8320 - test deprecated attributes (enqOptions, deqOptions)"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        self.assertEqual(queue.enqOptions, queue.enqoptions)
        self.assertEqual(queue.deqOptions, queue.deqoptions)

    def test_8321(self):
        "8321 - test deprecated AQ methods (enqOne, deqOne)"
        data = self.json_data[0]
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        queue.enqOne(self.conn.msgproperties(payload=data))
        props = queue.deqOne()
        self.assertEqual(props.payload, data)

    def test_8322(self):
        "8322 - test wrong payload type"
        queue = self.get_and_clear_queue(self.json_queue_name, "JSON")
        props = self.conn.msgproperties(payload="A string")
        with self.assertRaisesFullCode("DPY-2062"):
            queue.enqone(props)


if __name__ == "__main__":
    test_env.run_test_cases()
