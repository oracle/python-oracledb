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
1100 - Module for testing connections
"""

import random
import string
import threading
import time
import unittest

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    requires_connection = False

    def __connect_and_drop(self):
        """
        Connect to the database, perform a query and drop the connection.
        """
        with test_env.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("select count(*) from TestNumbers")
            (count,) = cursor.fetchone()
            self.assertEqual(count, 10)

    def __verify_fetched_data(self, connection):
        expected_data = [f"String {i + 1}" for i in range(10)]
        sql = "select StringCol from TestStrings order by IntCol"
        for i in range(5):
            with connection.cursor() as cursor:
                fetched_data = [s for s, in cursor.execute(sql)]
                self.assertEqual(fetched_data, expected_data)

    def __verify_attributes(self, connection, attr_name, value, sql):
        setattr(connection, attr_name, value)
        cursor = connection.cursor()
        cursor.execute(sql)
        (result,) = cursor.fetchone()
        self.assertEqual(result, value, f"{attr_name} value mismatch")

    def __verify_connect_arg(self, arg_name, arg_value, sql):
        args = {}
        args[arg_name] = arg_value
        conn = test_env.get_connection(**args)
        cursor = conn.cursor()
        cursor.execute(sql)
        (fetched_value,) = cursor.fetchone()
        self.assertEqual(fetched_value, arg_value)

    def test_1100(self):
        "1100 - simple connection to database"
        conn = test_env.get_connection()
        self.assertEqual(
            conn.username, test_env.get_main_user(), "user name differs"
        )
        self.assertEqual(
            conn.dsn, test_env.get_connect_string(), "dsn differs"
        )
        self.assertEqual(conn.thin, test_env.get_is_thin())

    @unittest.skipIf(test_env.get_is_drcp(), "not supported with DRCP")
    def test_1101(self):
        "1101 - test use of application context"
        namespace = "CLIENTCONTEXT"
        app_context_entries = [
            (namespace, "ATTR1", "VALUE1"),
            (namespace, "ATTR2", "VALUE2"),
            (namespace, "ATTR3", "VALUE3"),
        ]
        conn = test_env.get_connection(appcontext=app_context_entries)
        cursor = conn.cursor()
        for namespace, name, value in app_context_entries:
            cursor.execute(
                "select sys_context(:1, :2) from dual", (namespace, name)
            )
            (actual_value,) = cursor.fetchone()
            self.assertEqual(actual_value, value)

    def test_1102(self):
        "1102 - test invalid use of application context"
        self.assertRaises(
            TypeError,
            test_env.get_connection,
            appcontext=[("userenv", "action")],
        )

    def test_1103(self):
        "1103 - test connection end-to-end tracing attributes"
        conn = test_env.get_connection()
        if test_env.get_client_version() >= (
            12,
            1,
        ) and not self.is_on_oracle_cloud(conn):
            sql = """select dbop_name from v$sql_monitor
                     where sid = sys_context('userenv', 'sid')
                     and status = 'EXECUTING'"""
            self.__verify_attributes(conn, "dbop", "oracledb_dbop", sql)
        sql = "select sys_context('userenv', 'action') from dual"
        self.__verify_attributes(conn, "action", "oracledb_Action", sql)
        self.__verify_attributes(conn, "action", None, sql)
        sql = "select sys_context('userenv', 'module') from dual"
        self.__verify_attributes(conn, "module", "oracledb_Module", sql)
        self.__verify_attributes(conn, "module", None, sql)
        sql = "select sys_context('userenv', 'client_info') from dual"
        self.__verify_attributes(conn, "clientinfo", "oracledb_cinfo", sql)
        self.__verify_attributes(conn, "clientinfo", None, sql)
        sql = "select sys_context('userenv', 'client_identifier') from dual"
        self.__verify_attributes(
            conn, "client_identifier", "oracledb_cid", sql
        )
        self.__verify_attributes(conn, "client_identifier", None, sql)
        if not test_env.get_is_thin():
            sql = """select ecid from v$session
                     where sid = sys_context('userenv', 'sid')"""
            self.__verify_attributes(conn, "econtext_id", "oracledb_ecid", sql)
            self.__verify_attributes(conn, "econtext_id", None, sql)

    def test_1104(self):
        "1104 - test use of autocommit"
        conn = test_env.get_connection()
        cursor = conn.cursor()
        other_conn = test_env.get_connection()
        other_cursor = other_conn.cursor()
        cursor.execute("truncate table TestTempTable")
        cursor.execute("insert into TestTempTable (IntCol) values (1)")
        other_cursor.execute("select IntCol from TestTempTable")
        self.assertEqual(other_cursor.fetchall(), [])
        conn.autocommit = True
        cursor.execute("insert into TestTempTable (IntCol) values (2)")
        other_cursor.execute(
            "select IntCol from TestTempTable order by IntCol"
        )
        self.assertEqual(other_cursor.fetchall(), [(1,), (2,)])

    def test_1105(self):
        "1105 - connection to database with bad connect string"
        with self.assertRaisesFullCode(
            "DPY-4000", "DPY-4026", "DPY-4027", "ORA-12154"
        ):
            oracledb.connect("not a valid connect string!!")
        with self.assertRaisesFullCode("DPY-4000", "DPY-4001"):
            dsn = (
                test_env.get_main_user() + "@" + test_env.get_connect_string()
            )
            oracledb.connect(dsn)

    def test_1106(self):
        "1106 - connection to database with bad password"
        with self.assertRaisesFullCode("ORA-01017"):
            test_env.get_connection(
                password=test_env.get_main_password() + "X"
            )

    @unittest.skipIf(test_env.get_is_drcp(), "not supported with DRCP")
    def test_1107(self):
        "1107 - test changing password"
        conn = test_env.get_connection()
        if self.is_on_oracle_cloud(conn):
            self.skipTest("passwords on Oracle Cloud are strictly controlled")
        sys_random = random.SystemRandom()
        new_password = "".join(
            sys_random.choice(string.ascii_letters) for i in range(20)
        )
        conn.changepassword(test_env.get_main_password(), new_password)
        conn = test_env.get_connection(password=new_password)
        conn.changepassword(new_password, test_env.get_main_password())

    @unittest.skipIf(test_env.get_is_drcp(), "not supported with DRCP")
    def test_1108(self):
        "1108 - test changing password to an invalid value"
        conn = test_env.get_connection()
        if self.is_on_oracle_cloud(conn):
            self.skipTest("passwords on Oracle Cloud are strictly controlled")
        new_password = "1" * 1500
        with self.assertRaisesFullCode("ORA-01017", "ORA-00988"):
            conn.changepassword(test_env.get_main_password(), new_password)
        with self.assertRaisesFullCode("ORA-01017", "ORA-00988", "ORA-28008"):
            conn.changepassword("incorrect old password", new_password)

    @unittest.skipIf(test_env.get_is_drcp(), "not supported with DRCP")
    def test_1109(self):
        "1109 - test connecting with password containing / and @ symbols"
        conn = test_env.get_connection()
        if self.is_on_oracle_cloud(conn):
            self.skipTest("passwords on Oracle Cloud are strictly controlled")
        sys_random = random.SystemRandom()
        chars = list(
            sys_random.choice(string.ascii_letters) for i in range(20)
        )
        chars[4] = "/"
        chars[8] = "@"
        new_password = "".join(chars)
        conn.changepassword(test_env.get_main_password(), new_password)
        try:
            test_env.get_connection(password=new_password)
        finally:
            conn.changepassword(new_password, test_env.get_main_password())

    def test_1110(self):
        "1110 - confirm an exception is raised after closing a connection"
        conn = test_env.get_connection()
        conn.close()
        with self.assertRaisesFullCode("DPY-1001"):
            conn.rollback()

    @unittest.skipIf(test_env.get_is_thin(), "not relevant for thin mode")
    def test_1111(self):
        "1111 - test creating a connection using a handle"
        conn = test_env.get_connection()
        cursor = conn.cursor()
        cursor.execute("truncate table TestTempTable")
        int_value = random.randint(1, 32768)
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:val, null)
            """,
            val=int_value,
        )
        conn2 = oracledb.connect(handle=conn.handle)
        cursor = conn2.cursor()
        cursor.execute("select IntCol from TestTempTable")
        (fetched_int_value,) = cursor.fetchone()
        self.assertEqual(fetched_int_value, int_value)

        cursor.close()
        with self.assertRaisesFullCode("DPI-1034"):
            conn2.close()
        conn.close()

    def test_1112(self):
        "1112 - connection version is a string"
        conn = test_env.get_connection()
        self.assertIsInstance(conn.version, str)

    def test_1113(self):
        "1113 - connection rolls back before close"
        conn = test_env.get_connection()
        cursor = conn.cursor()
        cursor.execute("truncate table TestTempTable")
        other_conn = test_env.get_connection()
        other_cursor = other_conn.cursor()
        other_cursor.execute("insert into TestTempTable (IntCol) values (1)")
        other_cursor.close()
        other_conn.close()
        cursor.execute("select count(*) from TestTempTable")
        (count,) = cursor.fetchone()
        self.assertEqual(count, 0)

    def test_1114(self):
        "1114 - connection rolls back before destruction"
        conn = test_env.get_connection()
        cursor = conn.cursor()
        cursor.execute("truncate table TestTempTable")
        other_conn = test_env.get_connection()
        other_cursor = other_conn.cursor()
        other_cursor.execute("insert into TestTempTable (IntCol) values (1)")
        del other_cursor
        del other_conn
        cursor.execute("select count(*) from TestTempTable")
        (count,) = cursor.fetchone()
        self.assertEqual(count, 0)

    def test_1115(self):
        "1115 - multiple connections to database with multiple threads"
        threads = []
        for i in range(20):
            thread = threading.Thread(None, self.__connect_and_drop)
            threads.append(thread)
            thread.start()
            time.sleep(0.1)
        for thread in threads:
            thread.join()

    def test_1116(self):
        "1116 - test string format of connection"
        conn = test_env.get_connection()
        expected_value = "<oracledb.Connection to %s@%s>" % (
            test_env.get_main_user(),
            test_env.get_connect_string(),
        )
        self.assertEqual(str(conn), expected_value)

    def test_1117(self):
        "1117 - test context manager - close"
        with test_env.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("truncate table TestTempTable")
            cursor.execute("insert into TestTempTable (IntCol) values (1)")
            conn.commit()
            cursor.execute("insert into TestTempTable (IntCol) values (2)")
        with self.assertRaisesFullCode("DPY-1001"):
            conn.ping()
        conn = test_env.get_connection()
        cursor = conn.cursor()
        cursor.execute("select count(*) from TestTempTable")
        (count,) = cursor.fetchone()
        self.assertEqual(count, 1)

    def test_1118(self):
        "1118 - test connection attribute values"
        conn = test_env.get_connection()
        if test_env.get_client_version() >= (12, 1):
            self.assertEqual(conn.ltxid, b"")
        self.assertFalse(conn.autocommit)
        conn.autocommit = True
        self.assertTrue(conn.autocommit)
        self.assertIsNone(conn.current_schema)
        conn.current_schema = "test_schema"
        self.assertEqual(conn.current_schema, "test_schema")
        self.assertIsNone(conn.edition)
        conn.external_name = "test_external"
        self.assertEqual(conn.external_name, "test_external")
        conn.internal_name = "test_internal"
        self.assertEqual(conn.internal_name, "test_internal")
        if conn.max_identifier_length is not None:
            self.assertIsInstance(conn.max_identifier_length, int)
        conn.stmtcachesize = 30
        self.assertEqual(conn.stmtcachesize, 30)
        self.assertRaises(TypeError, conn.stmtcachesize, 20.5)
        self.assertRaises(TypeError, conn.stmtcachesize, "value")
        self.assertIsNone(conn.warning)

    def test_1119(self):
        "1119 - test closed connection attribute values"
        conn = test_env.get_connection()
        conn.close()
        attr_names = [
            "current_schema",
            "edition",
            "external_name",
            "internal_name",
            "stmtcachesize",
            "warning",
        ]
        if test_env.get_client_version() >= (12, 1):
            attr_names.append("ltxid")
        for name in attr_names:
            with self.assertRaisesFullCode("DPY-1001"):
                getattr(conn, name)

    def test_1120(self):
        "1120 - test connection ping makes a round trip"
        self.conn = test_env.get_connection()
        self.setup_round_trip_checker()
        self.conn.ping()
        self.assertRoundTrips(1)

    @unittest.skipIf(
        test_env.get_is_thin(),
        "thin mode doesn't support two-phase commit yet",
    )
    def test_1121(self):
        "1121 - test begin, prepare, cancel transaction"
        conn = test_env.get_connection()
        cursor = conn.cursor()
        cursor.execute("truncate table TestTempTable")
        conn.begin(10, "trxnId", "branchId")
        self.assertFalse(conn.prepare())
        conn.begin(10, "trxnId", "branchId")
        cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (1, 'tesName')
            """
        )
        self.assertTrue(conn.prepare())
        conn.cancel()
        conn.rollback()
        cursor.execute("select count(*) from TestTempTable")
        (count,) = cursor.fetchone()
        self.assertEqual(count, 0)

    @unittest.skipIf(
        test_env.get_is_thin(),
        "thin mode doesn't support two-phase commit yet",
    )
    def test_1122(self):
        "1122 - test multiple transactions on the same connection"
        conn = test_env.get_connection()
        with conn.cursor() as cursor:
            cursor.execute("truncate table TestTempTable")

        id_ = random.randint(0, 2**128)
        xid = (0x1234, "%032x" % id_, "%032x" % 9)
        conn.begin(*xid)
        with conn.cursor() as cursor:
            cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (1, 'tesName')
                """
            )
            self.assertTrue(conn.prepare())
            conn.commit()

        for begin_trans in (True, False):
            val = 3
            if begin_trans:
                conn.begin()
                val = 2
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    insert into TestTempTable (IntCol, StringCol1)
                    values (:int_val, 'tesName')
                    """,
                    int_val=val,
                )
                conn.commit()

        expected_rows = [(1, "tesName"), (2, "tesName"), (3, "tesName")]
        with conn.cursor() as cursor:
            cursor.execute("select IntCol, StringCol1 from TestTempTable")
            self.assertEqual(cursor.fetchall(), expected_rows)

    @unittest.skipIf(
        test_env.get_is_thin(),
        "thin mode doesn't support two-phase commit yet",
    )
    def test_1123(self):
        "1123 - test multiple global transactions on the same connection"
        conn = test_env.get_connection()
        with conn.cursor() as cursor:
            cursor.execute("truncate table TestTempTable")

        id_ = random.randint(0, 2**128)
        xid = (0x1234, "%032x" % id_, "%032x" % 9)
        conn.begin(*xid)
        with conn.cursor() as cursor:
            cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (1, 'tesName')
                """
            )
            self.assertTrue(conn.prepare())
            conn.commit()

        for begin_trans in (True, False):
            val = 3
            if begin_trans:
                conn.begin()
                val = 2
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    insert into TestTempTable (IntCol, StringCol1)
                    values (:int_val, 'tesName')
                    """,
                    int_val=val,
                )
                conn.commit()

        id2_ = random.randint(0, 2**128)
        xid2 = (0x1234, "%032x" % id2_, "%032x" % 9)
        conn.begin(*xid2)
        with conn.cursor() as cursor:
            cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (4, 'tesName')
                """
            )
            self.assertTrue(conn.prepare())
            conn.commit()

        expected_rows = [
            (1, "tesName"),
            (2, "tesName"),
            (3, "tesName"),
            (4, "tesName"),
        ]
        with conn.cursor() as cursor:
            cursor.execute("select IntCol, StringCol1 from TestTempTable")
            self.assertEqual(cursor.fetchall(), expected_rows)

    @unittest.skipIf(
        test_env.get_is_thin(),
        "thin mode doesn't support two-phase commit yet",
    )
    def test_1124(self):
        "1124 - test creating global txn after a local txn"
        conn = test_env.get_connection()
        with conn.cursor() as cursor:
            cursor.execute("truncate table TestTempTable")

        with conn.cursor() as cursor:
            cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (2, 'tesName')
                """
            )

        id_ = random.randint(0, 2**128)
        xid = (0x1234, "%032x" % id_, "%032x" % 9)
        with self.assertRaisesFullCode("ORA-24776"):
            conn.begin(*xid)

    def test_1125(self):
        "1125 - single connection to database with multiple threads"
        with test_env.get_connection() as conn:
            threads = [
                threading.Thread(
                    target=self.__verify_fetched_data, args=(conn,)
                )
                for i in range(3)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

    def test_1126(self):
        "1126 - test connection cancel"
        conn = test_env.get_connection()
        sleep_proc_name = test_env.get_sleep_proc_name()

        def perform_cancel():
            time.sleep(0.1)
            conn.cancel()

        thread = threading.Thread(target=perform_cancel)
        thread.start()
        try:
            with conn.cursor() as cursor:
                self.assertRaises(
                    oracledb.OperationalError,
                    cursor.callproc,
                    sleep_proc_name,
                    [2],
                )
        finally:
            thread.join()
        with conn.cursor() as cursor:
            cursor.execute("select user from dual")
            (user,) = cursor.fetchone()
            self.assertEqual(user, test_env.get_main_user().upper())

    @unittest.skipIf(test_env.get_is_drcp(), "not supported with DRCP")
    def test_1127(self):
        "1127 - test changing password during connect"
        conn = test_env.get_connection()
        if self.is_on_oracle_cloud(conn):
            self.skipTest("passwords on Oracle Cloud are strictly controlled")
        sys_random = random.SystemRandom()
        new_password = "".join(
            sys_random.choice(string.ascii_letters) for i in range(20)
        )
        conn = test_env.get_connection(newpassword=new_password)
        conn = test_env.get_connection(password=new_password)
        conn.changepassword(new_password, test_env.get_main_password())

    def test_1128(self):
        "1128 - test use of autocommit during reexecute"
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        data_to_insert = [(1, "Test String #1"), (2, "Test String #2")]
        conn = test_env.get_connection()
        cursor = conn.cursor()
        other_conn = test_env.get_connection()
        other_cursor = other_conn.cursor()
        cursor.execute("truncate table TestTempTable")
        cursor.execute(sql, data_to_insert[0])
        other_cursor.execute("select IntCol, StringCol1 from TestTempTable")
        self.assertEqual(other_cursor.fetchall(), [])
        conn.autocommit = True
        cursor.execute(sql, data_to_insert[1])
        other_cursor.execute("select IntCol, StringCol1 from TestTempTable")
        self.assertEqual(other_cursor.fetchall(), data_to_insert)

    def test_1129(self):
        "1129 - test current_schema is set properly"
        conn = test_env.get_connection()
        self.assertIsNone(conn.current_schema)

        user = test_env.get_main_user().upper()
        proxy_user = test_env.get_proxy_user().upper()
        cursor = conn.cursor()
        cursor.execute(f"alter session set current_schema={proxy_user}")
        self.assertEqual(conn.current_schema, proxy_user)

        conn.current_schema = user
        self.assertEqual(conn.current_schema, user)

        cursor.execute(
            "select sys_context('userenv', 'current_schema') from dual"
        )
        (result,) = cursor.fetchone()
        self.assertEqual(result, user)

    def test_1130(self):
        "1130 - test dbms_output package"
        conn = test_env.get_connection()
        cursor = conn.cursor()
        test_string = "Testing DBMS_OUTPUT package"
        cursor.callproc("dbms_output.enable")
        cursor.callproc("dbms_output.put_line", [test_string])
        string_var = cursor.var(str)
        number_var = cursor.var(int)
        cursor.callproc("dbms_output.get_line", (string_var, number_var))
        self.assertEqual(string_var.getvalue(), test_string)

    @unittest.skipIf(
        not test_env.get_is_thin() and test_env.get_client_version() < (18, 1),
        "unsupported client",
    )
    def test_1131(self):
        "1131 - test connection call_timeout"
        conn = test_env.get_connection()
        conn.call_timeout = 500  # milliseconds
        self.assertEqual(conn.call_timeout, 500)
        with self.assertRaisesFullCode("DPY-4011", "DPY-4024"):
            conn.cursor().callproc(test_env.get_sleep_proc_name(), [2])

    def test_1132(self):
        "1132 - test Connection repr()"

        class MyConnection(oracledb.Connection):
            pass

        conn = test_env.get_connection(conn_class=MyConnection)
        qual_name = conn.__class__.__qualname__
        expected_value = (
            f"<{__name__}.{qual_name} to {conn.username}@{conn.dsn}>"
        )
        self.assertEqual(repr(conn), expected_value)

        conn.close()
        expected_value = f"<{__name__}.{qual_name} disconnected>"
        self.assertEqual(repr(conn), expected_value)

    def test_1133(self):
        "1133 - test getting write-only attributes"
        conn = test_env.get_connection()
        with self.assertRaises(AttributeError):
            conn.action
        with self.assertRaises(AttributeError):
            conn.dbop
        with self.assertRaises(AttributeError):
            conn.clientinfo
        with self.assertRaises(AttributeError):
            conn.econtext_id
        with self.assertRaises(AttributeError):
            conn.module
        with self.assertRaises(AttributeError):
            conn.client_identifier

    def test_1134(self):
        "1134 - test error for invalid type for params and pool"
        pool = test_env.get_pool()
        pool.close()
        with self.assertRaisesFullCode("DPY-1002"):
            test_env.get_connection(pool=pool)
        self.assertRaises(
            TypeError,
            test_env.get_connection,
            pool="This isn't an instance of a pool",
        )
        with self.assertRaisesFullCode("DPY-2025"):
            oracledb.connect(params={"number": 7})

    def test_1135(self):
        "1135 - test connection instance name"
        conn = test_env.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            select upper(sys_context('userenv', 'instance_name'))
            from dual
            """
        )
        (instance_name,) = cursor.fetchone()
        self.assertEqual(conn.instance_name.upper(), instance_name)

    @unittest.skipIf(
        test_env.get_client_version() < (18, 1), "not supported on this client"
    )
    def test_1136(self):
        "1136 - test deprecated attributes"
        conn = test_env.get_connection()
        conn.callTimeout = 500
        self.assertEqual(conn.callTimeout, 500)

    @unittest.skipIf(test_env.get_is_drcp(), "not supported with DRCP")
    @unittest.skipIf(
        test_env.get_server_version() < (23, 0)
        or test_env.get_client_version() < (23, 0),
        "unsupported client/server",
    )
    def test_1137(self):
        "1137 - test maximum allowed length for password"
        conn = test_env.get_connection()
        if self.is_on_oracle_cloud(conn):
            self.skipTest("passwords on Oracle Cloud are strictly controlled")

        original_password = test_env.get_main_password()
        new_password_32 = "a" * 32
        conn.changepassword(original_password, new_password_32)
        conn = test_env.get_connection(password=new_password_32)

        new_password_1024 = "a" * 1024
        conn.changepassword(new_password_32, new_password_1024)
        conn = test_env.get_connection(password=new_password_1024)
        conn.changepassword(new_password_1024, original_password)

        new_password_1025 = "a" * 1025
        with self.assertRaisesFullCode("ORA-28218", "ORA-00972"):
            conn.changepassword(original_password, new_password_1025)

    def test_1138(self):
        "1138 - test getting db_name"
        conn = test_env.get_connection()
        cursor = conn.cursor()
        cursor.execute("select name from V$DATABASE")
        (db_name,) = cursor.fetchone()
        self.assertEqual(conn.db_name.upper(), db_name.upper())

    def test_1139(self):
        "1139 - test getting max_open_cursors"
        conn = test_env.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "select value from V$PARAMETER where name='open_cursors'"
        )
        (max_open_cursors,) = cursor.fetchone()
        self.assertEqual(conn.max_open_cursors, int(max_open_cursors))

    def test_1140(self):
        "1140 - test getting service_name"
        conn = test_env.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "select sys_context('userenv', 'service_name') from dual"
        )
        (service_name,) = cursor.fetchone()
        self.assertEqual(conn.service_name.upper(), service_name.upper())

    def test_1141(self):
        "1141 - test transaction_in_progress"
        conn = test_env.get_connection()
        self.assertFalse(conn.transaction_in_progress)

        cursor = conn.cursor()
        cursor.execute("truncate table TestTempTable")
        self.assertFalse(conn.transaction_in_progress)

        cursor.execute("insert into TestTempTable (IntCol) values (1)")
        self.assertTrue(conn.transaction_in_progress)

        conn.commit()
        self.assertFalse(conn.transaction_in_progress)

    def test_1142(self):
        "1142 - test getting db_domain"
        conn = test_env.get_connection()
        cursor = conn.cursor()
        cursor.execute("select value from V$PARAMETER where name='db_domain'")
        (db_domain,) = cursor.fetchone()
        self.assertEqual(conn.db_domain, db_domain)

    def test_1143(self):
        "1143 - test connecting with a proxy user"
        proxy_user = test_env.get_proxy_user()
        conn = test_env.get_connection(proxy_user=proxy_user)
        self.assertEqual(conn.username, test_env.get_main_user())
        self.assertEqual(conn.proxy_user, proxy_user)

    @unittest.skipIf(
        not test_env.get_is_thin(), "thick mode doesn't support SDU yet"
    )
    def test_1144(self):
        "1144 - test connection.sdu"
        conn = test_env.get_connection()
        sdu = random.randint(512, conn.sdu)
        conn = test_env.get_connection(sdu=sdu)
        self.assertEqual(conn.sdu, sdu)

    def test_1145(self):
        "1145 - test connection with invalid conn_class"
        with self.assertRaisesFullCode("DPY-2023"):
            test_env.get_connection(conn_class=oracledb.ConnectionPool)

    @unittest.skipUnless(
        test_env.get_is_thin(),
        "thick mode doesn't support program yet",
    )
    def test_1146(self):
        "1146 - test passing program when creating a connection"
        sql = (
            "select program from v$session "
            "where sid = sys_context('userenv', 'sid')"
        )
        self.__verify_connect_arg("program", "newprogram", sql)

    @unittest.skipUnless(
        test_env.get_is_thin(),
        "thick mode doesn't support machine yet",
    )
    def test_1147(self):
        "1147 - test passing machine when creating a connection"
        sql = (
            "select machine from v$session "
            "where sid = sys_context('userenv', 'sid')"
        )
        self.__verify_connect_arg("machine", "newmachine", sql)

    @unittest.skipUnless(
        test_env.get_is_thin(),
        "thick mode doesn't support terminal yet",
    )
    def test_1148(self):
        "1148 - test passing terminal when creating a connection"
        sql = (
            "select terminal from v$session "
            "where sid = sys_context('userenv', 'sid')"
        )
        self.__verify_connect_arg("terminal", "newterminal", sql)

    @unittest.skipUnless(
        test_env.get_is_thin(),
        "thick mode doesn't support osuser yet",
    )
    def test_1149(self):
        "1149 - test passing osuser when creating a connection"
        sql = (
            "select osuser from v$session "
            "where sid = sys_context('userenv', 'sid')"
        )
        self.__verify_connect_arg("osuser", "newosuser", sql)

    def test_1150(self):
        "1150 - test passing driver_name when creating a connection"
        sql = (
            "select distinct client_driver from v$session_connect_info "
            "where sid = sys_context('userenv', 'sid')"
        )
        self.__verify_connect_arg("driver_name", "newdriver", sql)

    @unittest.skipUnless(
        test_env.get_is_thin(), "thick mode doesn't support session_id yet"
    )
    def test_1151(self):
        "1151 - test getting session id"
        conn = test_env.get_connection()
        cursor = conn.cursor()
        cursor.execute("select dbms_debug_jdwp.current_session_id from dual")
        (fetched_value,) = cursor.fetchone()
        self.assertEqual(conn.session_id, fetched_value)

    @unittest.skipUnless(
        test_env.get_is_thin(), "thick mode doesn't support serial_num yet"
    )
    def test_1152(self):
        "1152 - test getting session serial number"
        conn = test_env.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "select dbms_debug_jdwp.current_session_serial from dual"
        )
        (fetched_value,) = cursor.fetchone()
        self.assertEqual(conn.serial_num, fetched_value)

    @unittest.skipUnless(
        test_env.get_is_thin(),
        "thick mode doesn't support registered protocols",
    )
    def test_1153(self):
        "1153 - test passed params in hook with standalone connection"
        sdu = 4096
        params = test_env.get_connect_params()
        protocol = "proto-test"
        orig_connect_string = test_env.get_connect_string()
        connect_string = f"{protocol}://{orig_connect_string}"

        def hook(passed_protocol, passed_protocol_arg, passed_params):
            self.assertEqual(passed_protocol, protocol)
            self.assertEqual(passed_protocol_arg, orig_connect_string)
            passed_params.parse_connect_string(passed_protocol_arg)
            passed_params.set(sdu=sdu)

        try:
            oracledb.register_protocol(protocol, hook)
            oracledb.connect(dsn=connect_string, params=params)
            self.assertEqual(params.sdu, sdu)
        finally:
            oracledb.register_protocol(protocol, None)

    def test_1154(self):
        "1154 - test altering connection edition"
        conn = test_env.get_connection()
        self.assertIsNone(conn.edition)
        cursor = conn.cursor()
        sql = "select sys_context('USERENV', 'CURRENT_EDITION_NAME') from dual"
        default_edition = "ORA$BASE"
        test_edition = test_env.get_edition_name()
        for edition in [test_edition, default_edition]:
            with self.subTest(edition=edition):
                cursor.execute(f"alter session set edition = {edition}")
                cursor.execute(sql)
                self.assertEqual(conn.edition, cursor.fetchone()[0])
                self.assertEqual(conn.edition, edition.upper())

    def test_1155(self):
        "1155 - test connect() with edition"
        edition = test_env.get_edition_name()
        conn = test_env.get_connection(edition=edition)
        cursor = conn.cursor()
        cursor.execute(
            "select sys_context('USERENV', 'CURRENT_EDITION_NAME') from dual"
        )
        self.assertEqual(cursor.fetchone()[0], edition.upper())
        self.assertEqual(conn.edition, edition)

    def test_1156(self):
        "1156 - test connect() with parameters hook"
        conn = test_env.get_connection()
        orig_stmtcachesize = conn.stmtcachesize
        stmtcachesize = orig_stmtcachesize + 10

        def hook(params):
            params.set(stmtcachesize=stmtcachesize)

        try:
            oracledb.register_params_hook(hook)
            conn = test_env.get_connection()
            self.assertEqual(conn.stmtcachesize, stmtcachesize)
        finally:
            oracledb.unregister_params_hook(hook)

        conn = test_env.get_connection()
        self.assertEqual(conn.stmtcachesize, orig_stmtcachesize)

    def test_1157(self):
        "1157 - test connect() with multiple parameters hooks"

        def hook1(params):
            order.append("first")

        def hook2(params):
            order.append("second")

        def hook3(params):
            order.append("third")

        oracledb.register_params_hook(hook1)
        oracledb.register_params_hook(hook2)
        oracledb.register_params_hook(hook3)
        try:
            order = []
            test_env.get_connection()
            self.assertEqual(order, ["first", "second", "third"])
        finally:
            oracledb.unregister_params_hook(hook1)
            oracledb.unregister_params_hook(hook2)
            oracledb.unregister_params_hook(hook3)

    def test_1158(self):
        "1158 - test error in the middle of a database response"
        conn = test_env.get_connection()
        cursor = conn.cursor()
        cursor.execute("truncate table TestTempTable")
        data = [(i + 1, 2 if i < 1499 else 0) for i in range(1500)]
        cursor.executemany(
            "insert into TestTempTable (IntCol, NumberCol) values (:1, :2)",
            data,
        )
        conn.commit()
        cursor.arraysize = 1500
        with self.assertRaisesFullCode("ORA-01476"):
            cursor.execute(
                """
                select IntCol, 1 / NumberCol
                from TestTempTable
                where IntCol < 1500
                union all
                select IntCol, 1 / NumberCol
                from TestTempTable
                where IntCol = 1500
                """
            )
            cursor.fetchall()


if __name__ == "__main__":
    test_env.run_test_cases()
