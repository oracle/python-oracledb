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
7800 - Module for testing AQ with raw queues
"""

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
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

    def test_7800(self):
        "7800 - test dequeuing an empty RAW queue"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        self.assertIsNone(props)

    def test_7801(self):
        "7801 - test enqueuing and dequeuing multiple RAW messages"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        props = self.conn.msgproperties()
        for value in self.raw_data:
            props.payload = value
            queue.enqone(props)
        self.conn.commit()
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        results = []
        while True:
            props = queue.deqone()
            if props is None:
                break
            value = props.payload
            results.append(value)
        self.conn.commit()
        self.assertEqual(results, self.raw_data)

    def test_7802(self):
        "7802 - test dequeuing with DEQ_REMOVE_NODATA in RAW queue"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[1]
        props = self.conn.msgproperties(payload=value)
        queue.enqone(props)
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.mode = oracledb.DEQ_REMOVE_NODATA
        props = queue.deqone()
        self.assertIsNotNone(props)
        self.assertEqual(props.payload, b"")

    def test_7803(self):
        "7803 - test getting/setting dequeue options attributes"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
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

    def test_7804(self):
        "7804 - test enqueue options attributes RAW queue"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        options = queue.enqoptions
        self.__verify_attr(options, "visibility", oracledb.ENQ_IMMEDIATE)

    def test_7805(self):
        "7805 - test errors for invalid values for enqueue"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        self.assertRaises(TypeError, queue.enqone, value)

    def test_7806(self):
        "7806 - test getting/setting message properties attributes"
        props = self.conn.msgproperties()
        self.__verify_attr(props, "correlation", "TEST_CORRELATION")
        self.__verify_attr(props, "delay", 60)
        self.__verify_attr(props, "exceptionq", "TEST_EXCEPTIONQ")
        self.__verify_attr(props, "expiration", 30)
        self.assertEqual(props.attempts, 0)
        self.__verify_attr(props, "priority", 1)
        self.assertEqual(props.state, oracledb.MSG_READY)
        self.assertEqual(props.deliverymode, 0)

    def test_7807(self):
        "7807 - test enqueue visibility option - ENQ_ON_COMMIT"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        queue.enqoptions.visibility = oracledb.ENQ_ON_COMMIT
        props = self.conn.msgproperties(payload=value)
        queue.enqone(props)

        other_conn = test_env.get_connection()
        queue = other_conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        self.assertIsNone(props)
        self.conn.commit()
        props = queue.deqone()
        self.assertIsNotNone(props)

    def test_7808(self):
        "7808 - test enqueue visibility option - ENQ_IMMEDIATE"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=value)
        queue.enqone(props)

        other_conn = test_env.get_connection()
        queue = other_conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_ON_COMMIT
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        value = props.payload
        results = value
        other_conn.commit()
        self.assertEqual(results, self.raw_data[0])

    def test_7809(self):
        "7809 - test enqueue/dequeue delivery modes identical - buffered"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=value)
        queue.enqone(props)

        other_conn = test_env.get_connection()
        queue = other_conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.deliverymode = oracledb.MSG_BUFFERED
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        value = props.payload
        results = value
        other_conn.commit()
        self.assertEqual(results, self.raw_data[0])

    def test_7810(self):
        "7810 - test enqueue/dequeue delivery modes identical - persistent"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=value)
        queue.enqone(props)

        other_conn = test_env.get_connection()
        queue = other_conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        value = props.payload
        results = value
        other_conn.commit()
        self.assertEqual(results, self.raw_data[0])

    def test_7811(self):
        "7811 - test enqueue/dequeue delivery modes the same"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=value)
        queue.enqone(props)

        other_conn = test_env.get_connection()
        queue = other_conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        value = props.payload
        results = value
        other_conn.commit()
        self.assertEqual(results, self.raw_data[0])

    def test_7812(self):
        "7812 - test enqueue/dequeue delivery modes different"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        queue.enqoptions.deliverymode = oracledb.MSG_BUFFERED
        queue.enqoptions.visibility = oracledb.ENQ_IMMEDIATE
        props = self.conn.msgproperties(payload=value)
        queue.enqone(props)

        other_conn = test_env.get_connection()
        queue = other_conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT
        queue.deqoptions.navigation = oracledb.DEQ_FIRST_MSG
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        props = queue.deqone()
        self.assertIsNone(props)

    def test_7813(self):
        "7813 - test error for message with no payload"
        queue = self.conn.queue("TEST_RAW_QUEUE")
        props = self.conn.msgproperties()
        with self.assertRaisesFullCode("DPY-2000"):
            queue.enqone(props)

    def test_7814(self):
        "7814 - verify that the msgid property is returned correctly"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        props = self.conn.msgproperties(payload=value)
        self.assertIsNone(props.msgid)
        queue.enqone(props)
        self.cursor.execute("select msgid from RAW_QUEUE_TAB")
        (actual_msgid,) = self.cursor.fetchone()
        self.assertEqual(props.msgid, actual_msgid)
        props = queue.deqone()
        self.assertEqual(props.msgid, actual_msgid)

    def test_7815(self):
        "7815 - test message props enqtime"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        self.cursor.execute("select current_timestamp from dual")
        (start_date,) = self.cursor.fetchone()
        start_date = start_date.replace(microsecond=0)
        props = self.conn.msgproperties(payload=value)
        queue.enqone(props)
        props = queue.deqone()
        self.cursor.execute("select current_timestamp from dual")
        (end_date,) = self.cursor.fetchone()
        end_date = end_date.replace(microsecond=0)
        self.assertTrue(start_date <= props.enqtime <= end_date)

    def test_7816(self):
        "7816 - test message props declared attributes"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
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
        queue.enqone(props)
        self.conn.commit()
        prop = queue.deqone()
        for attr_name in values:
            self.assertEqual(getattr(prop, attr_name), values[attr_name])

    def test_7817(self):
        "7817 - test getting queue attributes"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        self.assertEqual(queue.name, "TEST_RAW_QUEUE")
        self.assertEqual(queue.connection, self.conn)

    def test_7818(self):
        "7818 - test getting write-only attributes"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        for options in (queue.enqoptions, queue.deqoptions):
            with self.assertRaises(AttributeError):
                options.deliverymode

    def test_7819(self):
        "7819 - test deqoption condition with priority"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        priorities = [5, 5, 5, 5, 10, 9, 9, 10, 9]
        for priority in priorities:
            value = self.raw_data[0]
            props = self.conn.msgproperties(payload=value, priority=priority)
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

    def test_7820(self):
        "7820 - test deqoption correlation"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
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

    def test_7821(self):
        "7821 - test deqoption msgid"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        value = self.raw_data[0]
        props = self.conn.msgproperties(payload=value)
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

    def test_7822(self):
        "7822 - test payload_type returns the correct value"
        queue = self.conn.queue("TEST_RAW_QUEUE")
        self.assertIsNone(queue.payload_type)

    def test_7823(self):
        "7823 - test deprecated attributes (enqOptions, deqOptions)"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        self.assertEqual(queue.enqOptions, queue.enqoptions)
        self.assertEqual(queue.deqOptions, queue.deqoptions)

    def test_7824(self):
        "7824 - test deprecated AQ methods (enqOne, deqOne)"
        value = b"Test 7823"
        queue = self.get_and_clear_queue("TEST_RAW_QUEUE")
        queue.enqOne(self.conn.msgproperties(value))
        props = queue.deqOne()
        self.assertEqual(props.payload, value)


if __name__ == "__main__":
    test_env.run_test_cases()
