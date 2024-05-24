# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
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
3000 - Module for testing subscriptions
"""

import threading
import unittest

import oracledb
import test_env


class SubscriptionData:
    def __init__(self, num_messages_expected):
        self.condition = threading.Condition()
        self.num_messages_expected = num_messages_expected
        self.num_messages_received = 0

    def _process_message(self, message):
        pass

    def callback_handler(self, message):
        if message.type != oracledb.EVENT_DEREG:
            self._process_message(message)
            self.num_messages_received += 1
        if (
            message.type == oracledb.EVENT_DEREG
            or self.num_messages_received == self.num_messages_expected
        ):
            with self.condition:
                self.condition.notify()

    def wait_for_messages(self):
        if self.num_messages_received < self.num_messages_expected:
            with self.condition:
                self.condition.wait(10)


class AQSubscriptionData(SubscriptionData):
    pass


class DMLSubscriptionData(SubscriptionData):
    def __init__(self, num_messages_expected):
        super().__init__(num_messages_expected)
        self.table_operations = []
        self.row_operations = []
        self.rowids = []

    def _process_message(self, message):
        (table,) = message.tables
        self.table_operations.append(table.operation)
        for row in table.rows:
            self.row_operations.append(row.operation)
            self.rowids.append(row.rowid)


@unittest.skipIf(
    test_env.get_is_thin(), "thin mode doesn't support subscriptions"
)
class TestCase(test_env.BaseTestCase):
    @unittest.skipIf(
        test_env.get_client_version() < (23, 1), "crashes in older clients"
    )
    def test_3000(self):
        "3000 - test subscription for insert, update, delete and truncate"

        # skip if running on the Oracle Cloud, which does not support
        # subscriptions currently
        if self.is_on_oracle_cloud():
            message = "Oracle Cloud does not support subscriptions currently"
            self.skipTest(message)

        # truncate table in order to run test in known state
        self.cursor.execute("truncate table TestTempTable")

        # expected values
        table_operations = [
            oracledb.OPCODE_INSERT,
            oracledb.OPCODE_UPDATE,
            oracledb.OPCODE_INSERT,
            oracledb.OPCODE_DELETE,
            oracledb.OPCODE_ALTER | oracledb.OPCODE_ALLROWS,
        ]
        row_operations = [
            oracledb.OPCODE_INSERT,
            oracledb.OPCODE_UPDATE,
            oracledb.OPCODE_INSERT,
            oracledb.OPCODE_DELETE,
        ]
        rowids = []

        # set up subscription
        data = DMLSubscriptionData(5)
        conn = test_env.get_connection(events=True)
        sub = conn.subscribe(
            callback=data.callback_handler,
            timeout=10,
            qos=oracledb.SUBSCR_QOS_ROWIDS,
        )
        sub.registerquery("select * from TestTempTable")
        conn.autocommit = True
        cursor = conn.cursor()

        # insert statement
        cursor.execute(
            "insert into TestTempTable (IntCol, StringCol1) values (1, 'test')"
        )
        cursor.execute("select rowid from TestTempTable where IntCol = 1")
        rowids.extend(r for r, in cursor)

        # update statement
        cursor.execute(
            "update TestTempTable set StringCol1 = 'update' where IntCol = 1"
        )
        cursor.execute("select rowid from TestTempTable where IntCol = 1")
        rowids.extend(r for r, in cursor)

        # second insert statement
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (2, 'test2')
            """
        )
        cursor.execute("select rowid from TestTempTable where IntCol = 2")
        rowids.extend(r for r, in cursor)

        # delete statement
        cursor.execute("delete TestTempTable where IntCol = 2")
        rowids.append(rowids[-1])

        # truncate table
        cursor.execute("truncate table TestTempTable")

        # wait for all messages to be sent
        data.wait_for_messages()

        # verify the correct messages were sent
        self.assertEqual(data.table_operations, table_operations)
        self.assertEqual(data.row_operations, row_operations)
        self.assertEqual(data.rowids, rowids)

        # test string format of subscription object is as expected
        fmt = "<oracledb.Subscription on <oracledb.Connection to %s@%s>>"
        expected = fmt % (
            test_env.get_main_user(),
            test_env.get_connect_string(),
        )
        self.assertEqual(str(sub), expected)

    def test_3001(self):
        "3001 - test to verify deprecations"
        with self.assertRaisesFullCode("DPY-2014"):
            self.conn.subscribe(
                ip_address="www.oracle.in", ipAddress="www.oracle.in"
            )
        with self.assertRaisesFullCode("DPY-2014"):
            self.conn.subscribe(grouping_class=1, groupingClass=1)
        with self.assertRaisesFullCode("DPY-2014"):
            self.conn.subscribe(grouping_value=3, groupingValue=3)
        with self.assertRaisesFullCode("DPY-2014"):
            self.conn.subscribe(grouping_type=2, groupingType=2)
        with self.assertRaisesFullCode("DPY-2014"):
            self.conn.subscribe(client_initiated=True, clientInitiated=True)

    @unittest.skipIf(
        test_env.get_client_version() < (23, 1), "crashes in older clients"
    )
    def test_3002(self):
        "3002 - test subscription for AQ"

        # create queue and clear it of all messages
        queue = self.conn.queue("TEST_RAW_QUEUE")
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        while queue.deqone():
            pass
        self.conn.commit()

        # set up subscription
        data = AQSubscriptionData(1)
        conn = test_env.get_connection(events=True)
        conn.subscribe(
            namespace=oracledb.SUBSCR_NAMESPACE_AQ,
            name=queue.name,
            timeout=10,
            callback=data.callback_handler,
        )

        # enqueue a message
        queue.enqone(self.conn.msgproperties(payload="Some data"))
        self.conn.commit()

        # wait for all messages to be sent
        data.wait_for_messages()

    @unittest.skipIf(
        test_env.get_client_version() < (23, 1), "crashes in older clients"
    )
    def test_3003(self):
        "3003 - test verifying what registerquery returns"
        data = DMLSubscriptionData(5)
        qos_constants = [
            oracledb.SUBSCR_QOS_QUERY,
            oracledb.SUBSCR_QOS_RELIABLE,
            oracledb.SUBSCR_QOS_DEREG_NFY,
            oracledb.SUBSCR_QOS_ROWIDS,
            oracledb.SUBSCR_QOS_BEST_EFFORT,
        ]
        for qos_constant in qos_constants:
            conn = test_env.get_connection(events=True)
            sub = conn.subscribe(
                qos=qos_constant, callback=data.callback_handler
            )
            query_id = sub.registerquery("select * from TestTempTable")
            if qos_constant == oracledb.SUBSCR_QOS_QUERY:
                self.assertIsInstance(query_id, int)
                self.assertIsInstance(sub.id, int)
            else:
                self.assertIsNone(query_id)
            conn.unsubscribe(sub)
            conn.close()

    @unittest.skipIf(
        test_env.get_client_version() < (23, 1), "crashes in older clients"
    )
    def test_3004(self):
        "3004 - test Subscription repr()"
        data = DMLSubscriptionData(5)
        with test_env.get_connection(events=True) as conn:
            sub = conn.subscribe(callback=data.callback_handler)
            self.assertEqual(repr(sub), f"<oracledb.Subscription on {conn}>")
            conn.unsubscribe(sub)

    @unittest.skipIf(
        test_env.get_client_version() < (23, 1), "crashes in older clients"
    )
    def test_3005(self):
        "3005 - test registerquery with invalid parameters"
        data = DMLSubscriptionData(5)
        conn = test_env.get_connection(events=True)
        sub = conn.subscribe(callback=data.callback_handler)
        self.assertRaises(
            TypeError,
            sub.registerquery,
            "select * from TestTempTable",
            "invalid args",
        )
        with self.assertRaisesFullCode("ORA-00942"):
            sub.registerquery("select * from Nonexistent")
        with self.assertRaisesFullCode("DPI-1013"):
            sub.registerquery("insert into TestTempTable (IntCol) values (1)")
        conn.unsubscribe(sub)

    @unittest.skipIf(
        test_env.get_client_version() < (23, 1), "crashes in older clients"
    )
    def test_3006(self):
        "3006 - test getting subscription attributes"
        data = DMLSubscriptionData(1)
        conn = test_env.get_connection(events=True)
        cursor = conn.cursor()
        args = dict(
            callback=data.callback_handler,
            ip_address=None,
            port=0,
            name="Sub1",
            namespace=oracledb.SUBSCR_NAMESPACE_DBCHANGE,
            timeout=10,
            protocol=oracledb.SUBSCR_PROTO_OCI,
            qos=oracledb.SUBSCR_QOS_QUERY,
            operations=oracledb.OPCODE_INSERT,
        )
        sub = conn.subscribe(**args)
        for attr_name in args:
            self.assertEqual(getattr(sub, attr_name), args[attr_name])
        self.assertEqual(sub.connection, conn)
        cursor.execute("select REGID from USER_CHANGE_NOTIFICATION_REGS")
        self.assertEqual(sub.id, cursor.fetchone()[0])
        self.assertEqual(sub.ipAddress, sub.ip_address)
        conn.unsubscribe(sub)
        conn.close()

    @unittest.skipIf(
        test_env.get_client_version() < (23, 1), "crashes in older clients"
    )
    def test_3007(self):
        "3007 - test getting Message, MessageQuery, MessageTable attributes"
        condition = threading.Condition()
        conn = test_env.get_connection(events=True)

        def callback_handler(message):
            self.assertEqual(
                message.dbname.upper(), conn.instance_name.upper()
            )
            self.assertTrue(message.registered)
            self.assertEqual(message.subscription, sub)
            self.assertEqual(message.tables, [])
            self.assertIsInstance(message.txid, bytes)
            self.assertEqual(message.type, oracledb.EVENT_QUERYCHANGE)
            self.assertIsInstance(message.queries, list)
            (queries,) = message.queries
            self.assertEqual(queries.id, sub_id)
            self.assertEqual(queries.operation, oracledb.EVENT_QUERYCHANGE)
            self.assertIsInstance(queries.tables, list)
            (tables,) = queries.tables
            table_name = f"{test_env.get_main_user().upper()}.TESTTEMPTABLE"
            self.assertEqual(tables.name, table_name)
            self.assertIsInstance(tables.operation, int)
            self.assertIsInstance(tables.rows, list)
            with condition:
                condition.notify()

        sub = conn.subscribe(
            callback=callback_handler, qos=oracledb.SUBSCR_QOS_QUERY
        )
        cursor = conn.cursor()
        cursor.execute("truncate table TestTempTable")
        sub_id = sub.registerquery("select * from TestTempTable")
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (1, 'test')
            """
        )
        conn.commit()

        with condition:
            self.assertTrue(condition.wait(5))
        conn.unsubscribe(sub)

    @unittest.skipIf(
        test_env.get_client_version() < (23, 1), "crashes in older clients"
    )
    def test_3008(self):
        "3008 - test unsubscribe with invalid parameter"
        conn = test_env.get_connection(events=True)
        self.assertRaises(TypeError, conn.unsubscribe, "not a sub object")
        sub = conn.subscribe(callback=lambda x: f"Message: {x}")
        conn.unsubscribe(sub)
        with self.assertRaisesFullCode("DPI-1002"):
            conn.unsubscribe(sub)

    @unittest.skipIf(
        test_env.get_client_version() < (23, 1), "crashes in older clients"
    )
    def test_3010(self):
        "3010 - test registerquery in the middle of an active transaction"
        connection = test_env.get_connection(events=True)
        cursor = connection.cursor()
        cursor.execute("truncate table TestTempTable")
        cursor.execute(
            "insert into TestTempTable (IntCol, StringCol1) values (1, 'test')"
        )
        sub = connection.subscribe(callback=lambda x: f"Msg: {x}")
        with self.assertRaisesFullCode("ORA-29975"):
            sub.registerquery("select * from TestTempTable")
        connection.unsubscribe(sub)

    @unittest.skipIf(
        test_env.get_client_version() < (23, 1), "crashes in older clients"
    )
    def test_3011(self):
        "3011 - test registerquery with aq subscription"
        connection = test_env.get_connection(events=True)
        sub = connection.subscribe(
            callback=lambda x: None,
            namespace=oracledb.SUBSCR_NAMESPACE_AQ,
            name="TEST_RAW_QUEUE",
        )
        with self.assertRaisesFullCode("ORA-24315"):
            sub.registerquery("select * from TestTempTable")
        connection.unsubscribe(sub)

    @unittest.skipIf(
        test_env.get_client_version() < (23, 1), "crashes in older clients"
    )
    def test_3013(self):
        "3013 - test subscription with SUBSCR_QOS_DEREG_NFY deregisters"
        if self.is_on_oracle_cloud():
            self.skipTest("AQ notification not supported on the cloud")

        def callback(message):
            self.assertFalse(message.registered)
            with condition:
                condition.notify()

        condition = threading.Condition()
        self.cursor.execute("truncate table TestTempTable")
        conn = test_env.get_connection(events=True)
        cursor = conn.cursor()
        sub = conn.subscribe(
            callback=callback, qos=oracledb.SUBSCR_QOS_DEREG_NFY, timeout=2
        )
        sub.registerquery("select * from TestTempTable")
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (1, 'test')
            """
        )
        conn.commit()
        with condition:
            self.assertTrue(condition.wait(5))
        conn.unsubscribe(sub)

    @unittest.skipIf(
        test_env.get_client_version() < (23, 1), "crashes in older clients"
    )
    def test_3014(self):
        "3014 - test adding a consumer to a single consumer queue (negative)"
        conn = test_env.get_connection(events=True)
        single_consumer_queue = "TEST_RAW_QUEUE"
        with self.assertRaisesFullCode("ORA-25256"):
            conn.subscribe(
                callback=lambda x: None,
                namespace=oracledb.SUBSCR_NAMESPACE_AQ,
                name=f"{single_consumer_queue}:SUBSCRIBER",
            )


if __name__ == "__main__":
    test_env.run_test_cases()
