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
        if message.type == oracledb.EVENT_DEREG or \
                self.num_messages_received == self.num_messages_expected:
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
        table, = message.tables
        self.table_operations.append(table.operation)
        for row in table.rows:
            self.row_operations.append(row.operation)
            self.rowids.append(row.rowid)


@unittest.skipIf(test_env.get_is_thin(),
                 "thin mode doesn't support subscriptions")
class TestCase(test_env.BaseTestCase):

    @unittest.skipIf(test_env.get_client_version() < (23, 1),
                     "crashes in older clients")
    def test_3000_dml_subscription(self):
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
            oracledb.OPCODE_ALTER | oracledb.OPCODE_ALLROWS
        ]
        row_operations = [
            oracledb.OPCODE_INSERT,
            oracledb.OPCODE_UPDATE,
            oracledb.OPCODE_INSERT,
            oracledb.OPCODE_DELETE
        ]
        rowids = []

        # set up subscription
        data = DMLSubscriptionData(5)
        connection = test_env.get_connection(events=True)
        sub = connection.subscribe(callback=data.callback_handler,
                                   timeout=10, qos=oracledb.SUBSCR_QOS_ROWIDS)
        sub.registerquery("select * from TestTempTable")
        connection.autocommit = True
        cursor = connection.cursor()

        # insert statement
        cursor.execute("""
                insert into TestTempTable (IntCol, StringCol1)
                values (1, 'test')""")
        cursor.execute("select rowid from TestTempTable where IntCol = 1")
        rowids.extend(r for r, in cursor)

        # update statement
        cursor.execute("""
                update TestTempTable set
                    StringCol1 = 'update'
                where IntCol = 1""")
        cursor.execute("select rowid from TestTempTable where IntCol = 1")
        rowids.extend(r for r, in cursor)

        # second insert statement
        cursor.execute("""
                insert into TestTempTable (IntCol, StringCol1)
                values (2, 'test2')""")
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
        expected = fmt % \
                   (test_env.get_main_user(), test_env.get_connect_string())
        self.assertEqual(str(sub), expected)

    def test_3001_deprecations(self):
        "3001 - test to verify deprecations"
        self.assertRaisesRegex(oracledb.ProgrammingError, "^DPY-2014:",
                               self.connection.subscribe,
                               ip_address='www.oracle.in',
                               ipAddress='www.oracle.in')
        self.assertRaisesRegex(oracledb.ProgrammingError, "^DPY-2014:",
                               self.connection.subscribe, grouping_class=1,
                               groupingClass=1)
        self.assertRaisesRegex(oracledb.ProgrammingError, "^DPY-2014:",
                               self.connection.subscribe, grouping_value=3,
                               groupingValue=3)
        self.assertRaisesRegex(oracledb.ProgrammingError, "^DPY-2014:",
                               self.connection.subscribe, grouping_type=2,
                               groupingType=2)
        self.assertRaisesRegex(oracledb.ProgrammingError, "^DPY-2014:",
                               self.connection.subscribe,
                               client_initiated=True, clientInitiated=True)

    @unittest.skipIf(test_env.get_client_version() < (23, 1),
                     "crashes in older clients")
    def test_3002_aq_subscription(self):
        "3002 - test subscription for AQ"

        # create queue and clear it of all messages
        queue = self.connection.queue("TEST_RAW_QUEUE")
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        while queue.deqone():
            pass
        self.connection.commit()

        # set up subscription
        data = AQSubscriptionData(1)
        connection = test_env.get_connection(events=True)
        sub = connection.subscribe(namespace=oracledb.SUBSCR_NAMESPACE_AQ,
                                   name=queue.name, timeout=10,
                                   callback=data.callback_handler)

        # enqueue a message
        queue.enqone(self.connection.msgproperties(payload="Some data"))
        self.connection.commit()

        # wait for all messages to be sent
        data.wait_for_messages()

    @unittest.skipIf(test_env.get_client_version() < (23, 1),
                     "crashes in older clients")
    def test_3003_registerquery_returns(self):
        "3003 - test verifying what registerquery returns"
        data = DMLSubscriptionData(5)
        qos_constants = [
                oracledb.SUBSCR_QOS_QUERY,
                oracledb.SUBSCR_QOS_RELIABLE,
                oracledb.SUBSCR_QOS_DEREG_NFY,
                oracledb.SUBSCR_QOS_ROWIDS,
                oracledb.SUBSCR_QOS_BEST_EFFORT
        ]
        for qos_constant in qos_constants:
            connection = test_env.get_connection(events=True)
            sub = connection.subscribe(qos=qos_constant,
                                       callback=data.callback_handler)
            query_id = sub.registerquery("select * from TestTempTable")
            if qos_constant == oracledb.SUBSCR_QOS_QUERY:
                self.assertEqual(type(query_id), int)
                self.assertEqual(type(sub.id), int)
            else:
                self.assertEqual(query_id, None)
            connection.unsubscribe(sub)
            connection.close()

    @unittest.skipIf(test_env.get_client_version() < (23, 1),
                     "crashes in older clients")
    def test_3004_repr(self):
        "3004 - test Subscription repr()"
        data = DMLSubscriptionData(5)
        with test_env.get_connection(events=True) as conn:
            sub = conn.subscribe(callback=data.callback_handler)
            self.assertEqual(repr(sub), f"<oracledb.Subscription on {conn}>")
            conn.unsubscribe(sub)

    @unittest.skipIf(test_env.get_client_version() < (23, 1),
                     "crashes in older clients")
    def test_3005_registerquery_negative(self):
        "3005 - test registerquery with invalid parameters"
        data = DMLSubscriptionData(5)
        connection = test_env.get_connection(events=True)
        sub = connection.subscribe(callback=data.callback_handler)
        self.assertRaises(TypeError, sub.registerquery,
                          "select * from TestTempTable", "invalid args")
        self.assertRaisesRegex(oracledb.DatabaseError, "^ORA-00942",
                               sub.registerquery, "select * from Nonexistent")
        connection.unsubscribe(sub)

    @unittest.skipIf(test_env.get_client_version() < (23, 1),
                     "crashes in older clients")
    def test_3006_attributes(self):
        "3006 - test getting subscription attributes"
        data = DMLSubscriptionData(1)
        connection = test_env.get_connection(events=True)
        cursor = connection.cursor()
        args = dict(callback=data.callback_handler, ip_address=None, port=0,
                    name="Sub1", namespace=oracledb.SUBSCR_NAMESPACE_DBCHANGE,
                    timeout=10, protocol=oracledb.SUBSCR_PROTO_OCI,
                    qos=oracledb.SUBSCR_QOS_QUERY,
                    operations=oracledb.OPCODE_INSERT)
        sub = connection.subscribe(**args)
        for attr_name in args:
            self.assertEqual(getattr(sub, attr_name), args[attr_name])
        self.assertEqual(sub.connection, connection)
        cursor.execute("select REGID from USER_CHANGE_NOTIFICATION_REGS")
        self.assertEqual(sub.id, cursor.fetchone()[0])
        connection.unsubscribe(sub)
        connection.close()

if __name__ == "__main__":
    test_env.run_test_cases()
