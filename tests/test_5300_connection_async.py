# -----------------------------------------------------------------------------
# Copyright (c) 2023, 2024, Oracle and/or its affiliates.
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
5300 - Module for testing connections with asyncio
"""

import asyncio
import random
import string
import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    requires_connection = False

    async def __connect_and_drop(self):
        """
        Connect to the database, perform a query and drop the connection.
        """
        await asyncio.sleep(0.1)
        async with test_env.get_connection_async() as conn:
            cursor = conn.cursor()
            await cursor.execute("select count(*) from TestNumbers")
            (count,) = await cursor.fetchone()
            self.assertEqual(count, 10)

    async def __verify_fetched_data(self, connection):
        expected_data = [f"String {i + 1}" for i in range(10)]
        sql = "select StringCol from TestStrings order by IntCol"
        for i in range(5):
            with connection.cursor() as cursor:
                await cursor.execute(sql)
                fetched_data = [s async for s, in cursor]
                self.assertEqual(fetched_data, expected_data)

    async def __verify_attributes(self, connection, attr_name, value, sql):
        setattr(connection, attr_name, value)
        cursor = connection.cursor()
        await cursor.execute(sql)
        (result,) = await cursor.fetchone()
        self.assertEqual(result, value, f"{attr_name} value mismatch")

    async def __verify_connect_arg(self, arg_name, arg_value, sql):
        args = {}
        args[arg_name] = arg_value
        conn = await test_env.get_connection_async(**args)
        cursor = conn.cursor()
        await cursor.execute(sql)
        (fetched_value,) = await cursor.fetchone()
        self.assertEqual(fetched_value, arg_value)

    async def test_5300(self):
        "5300 - simple connection to database"
        async with test_env.get_connection_async() as conn:
            self.assertEqual(
                conn.username, test_env.get_main_user(), "user name differs"
            )
            self.assertEqual(
                conn.dsn, test_env.get_connect_string(), "dsn differs"
            )
            self.assertEqual(conn.thin, test_env.get_is_thin())

    async def test_5303(self):
        "5303 - test connection end-to-end tracing attributes"
        async with test_env.get_connection_async() as conn:
            if not await self.is_on_oracle_cloud(conn):
                sql = """select dbop_name from v$sql_monitor
                         where sid = sys_context('userenv', 'sid')
                         and status = 'EXECUTING'"""
                await self.__verify_attributes(
                    conn, "dbop", "oracledb_dbop", sql
                )
            sql = "select sys_context('userenv', 'action') from dual"
            await self.__verify_attributes(
                conn, "action", "oracledb_Action", sql
            )
            await self.__verify_attributes(conn, "action", None, sql)
            sql = "select sys_context('userenv', 'module') from dual"
            await self.__verify_attributes(
                conn, "module", "oracledb_Module", sql
            )
            await self.__verify_attributes(conn, "module", None, sql)
            sql = "select sys_context('userenv', 'client_info') from dual"
            await self.__verify_attributes(
                conn, "clientinfo", "oracledb_cinfo", sql
            )
            await self.__verify_attributes(conn, "clientinfo", None, sql)
            sql = (
                "select sys_context('userenv', 'client_identifier') from dual"
            )
            await self.__verify_attributes(
                conn, "client_identifier", "oracledb_cid", sql
            )
            await self.__verify_attributes(
                conn, "client_identifier", None, sql
            )

    async def test_5304(self):
        "5304 - test use of autocommit"
        async with test_env.get_connection_async() as conn:
            cursor = conn.cursor()
            other_conn = await test_env.get_connection_async()
            other_cursor = other_conn.cursor()
            await cursor.execute("truncate table TestTempTable")
            await cursor.execute(
                "insert into TestTempTable (IntCol) values (1)"
            )
            await other_cursor.execute("select IntCol from TestTempTable")
            self.assertEqual(await other_cursor.fetchall(), [])
            conn.autocommit = True
            await cursor.execute(
                "insert into TestTempTable (IntCol) values (2)"
            )
            await other_cursor.execute(
                "select IntCol from TestTempTable order by IntCol"
            )
            self.assertEqual(await other_cursor.fetchall(), [(1,), (2,)])

    async def test_5305(self):
        "5305 - connection to database with bad connect string"
        with self.assertRaisesFullCode(
            "DPY-4000", "DPY-4026", "DPY-4027", "ORA-12154"
        ):
            await oracledb.connect_async("not a valid connect string!!")
        with self.assertRaisesFullCode("DPY-4000", "DPY-4001"):
            await oracledb.connect(
                test_env.get_main_user() + "@" + test_env.get_connect_string()
            )

    async def test_5306(self):
        "5306 - connection to database with bad password"
        with self.assertRaisesFullCode("ORA-01017"):
            await test_env.get_connection_async(
                password=test_env.get_main_password() + "X",
            )

    @unittest.skipIf(test_env.get_is_drcp(), "not supported with DRCP")
    async def test_5307(self):
        "5307 - test changing password"
        async with test_env.get_connection_async() as conn:
            if await self.is_on_oracle_cloud(conn):
                self.skipTest(
                    "passwords on Oracle Cloud are strictly controlled"
                )
            sys_random = random.SystemRandom()
            new_password = "".join(
                sys_random.choice(string.ascii_letters) for i in range(20)
            )
            await conn.changepassword(
                test_env.get_main_password(), new_password
            )
            conn = await test_env.get_connection_async(password=new_password)
            await conn.changepassword(
                new_password, test_env.get_main_password()
            )

    @unittest.skipIf(test_env.get_is_drcp(), "not supported with DRCP")
    async def test_5308(self):
        "5308 - test changing password to an invalid value"
        async with test_env.get_connection_async() as conn:
            if await self.is_on_oracle_cloud(conn):
                self.skipTest(
                    "passwords on Oracle Cloud are strictly controlled"
                )
            new_password = "1" * 1500
            with self.assertRaisesFullCode("ORA-01017", "ORA-00988"):
                await conn.changepassword(
                    test_env.get_main_password(), new_password
                )
            with self.assertRaisesFullCode(
                "ORA-01017", "ORA-28008", "ORA-00988"
            ):
                await conn.changepassword(
                    "incorrect old password", new_password
                )

    @unittest.skipIf(test_env.get_is_drcp(), "not supported with DRCP")
    async def test_5309(self):
        "5309 - test connecting with password containing / and @ symbols"
        async with test_env.get_connection_async() as conn:
            if await self.is_on_oracle_cloud(conn):
                self.skipTest(
                    "passwords on Oracle Cloud are strictly controlled"
                )
            sys_random = random.SystemRandom()
            chars = list(
                sys_random.choice(string.ascii_letters) for i in range(20)
            )
            chars[4] = "/"
            chars[8] = "@"
            new_password = "".join(chars)
            await conn.changepassword(
                test_env.get_main_password(), new_password
            )
            try:
                async with test_env.get_connection_async(
                    password=new_password
                ):
                    pass
            finally:
                await conn.changepassword(
                    new_password, test_env.get_main_password()
                )

    async def test_5310(self):
        "5310 - confirm an exception is raised after closing a connection"
        async with await test_env.get_connection_async() as conn:
            await conn.close()
            with self.assertRaisesFullCode("DPY-1001"):
                await conn.rollback()

    async def test_5312(self):
        "5312 - connection version is a string"
        async with test_env.get_connection_async() as conn:
            self.assertIsInstance(conn.version, str)

    async def test_5313(self):
        "5313 - connection rolls back before close"
        async with test_env.get_connection_async() as conn:
            cursor = conn.cursor()
            await cursor.execute("truncate table TestTempTable")
            other_conn = await test_env.get_connection_async()
            other_cursor = other_conn.cursor()
            await other_cursor.execute(
                "insert into TestTempTable (IntCol) values (1)"
            )
            other_cursor.close()
            await other_conn.close()
            await cursor.execute("select count(*) from TestTempTable")
            (count,) = await cursor.fetchone()
            self.assertEqual(count, 0)

    async def test_5315(self):
        "5315 - multiple connections to database with multiple threads"
        coroutines = [self.__connect_and_drop() for i in range(20)]
        await asyncio.gather(*coroutines)

    async def test_5316(self):
        "5316 - test string format of connection"
        async with test_env.get_connection_async() as conn:
            expected_value = "<oracledb.AsyncConnection to %s@%s>" % (
                test_env.get_main_user(),
                test_env.get_connect_string(),
            )
            self.assertEqual(str(conn), expected_value)

    async def test_5317(self):
        "5317 - test context manager - close"
        async with test_env.get_connection_async() as conn:
            cursor = conn.cursor()
            await cursor.execute("truncate table TestTempTable")
            await cursor.execute(
                "insert into TestTempTable (IntCol) values (1)"
            )
            await conn.commit()
            await cursor.execute(
                "insert into TestTempTable (IntCol) values (2)"
            )
        with self.assertRaisesFullCode("DPY-1001"):
            await conn.ping()
        conn = await test_env.get_connection_async()
        cursor = conn.cursor()
        await cursor.execute("select count(*) from TestTempTable")
        (count,) = await cursor.fetchone()
        self.assertEqual(count, 1)

    async def test_5318(self):
        "5318 - test connection attribute values"
        async with test_env.get_connection_async() as conn:
            if test_env.get_client_version() >= (12, 1):
                self.assertEqual(conn.ltxid, b"")
            self.assertIsNone(conn.current_schema)
            conn.current_schema = "test_schema"
            self.assertEqual(conn.current_schema, "test_schema")
            self.assertIsNone(conn.edition)
            conn.external_name = "test_external"
            self.assertEqual(conn.external_name, "test_external")
            conn.internal_name = "test_internal"
            self.assertEqual(conn.internal_name, "test_internal")
            conn.stmtcachesize = 30
            self.assertEqual(conn.stmtcachesize, 30)
            self.assertRaises(TypeError, conn.stmtcachesize, 20.5)
            self.assertRaises(TypeError, conn.stmtcachesize, "value")
            self.assertIsNone(conn.warning)

    async def test_5319(self):
        "5319 - test closed connection attribute values"
        conn = await test_env.get_connection_async()
        await conn.close()
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

    async def test_5320(self):
        "5320 - test connection ping makes a round trip"
        self.conn = test_env.get_connection_async()
        async with self.conn:
            await self.setup_round_trip_checker()
            await self.conn.ping()
            await self.assertRoundTrips(1)

    async def test_5325(self):
        "5325 - single connection to database with multiple threads"
        async with test_env.get_connection_async() as conn:
            coroutines = [self.__verify_fetched_data(conn) for i in range(3)]
            await asyncio.gather(*coroutines)

    @unittest.skipIf(
        test_env.get_is_implicit_pooling(),
        "sessions can change with implicit pooling",
    )
    async def test_5326(self):
        "5326 - test connection cancel"
        async with test_env.get_connection_async() as conn:
            sleep_proc_name = test_env.get_sleep_proc_name()

            async def perform_cancel():
                await asyncio.sleep(0.1)
                conn.cancel()

            async def perform_work():
                with self.assertRaises(oracledb.OperationalError):
                    with conn.cursor() as cursor:
                        await cursor.callproc(sleep_proc_name, [2])

            await asyncio.gather(perform_work(), perform_cancel())

            with conn.cursor() as cursor:
                await cursor.execute("select user from dual")
                (user,) = await cursor.fetchone()
                self.assertEqual(user, test_env.get_main_user().upper())

    @unittest.skipIf(test_env.get_is_drcp(), "not supported with DRCP")
    async def test_5327(self):
        "5327 - test changing password during connect"
        async with test_env.get_connection_async() as conn:
            if await self.is_on_oracle_cloud(conn):
                self.skipTest(
                    "passwords on Oracle Cloud are strictly controlled"
                )
            sys_random = random.SystemRandom()
            new_password = "".join(
                sys_random.choice(string.ascii_letters) for i in range(20)
            )
            conn = await test_env.get_connection_async(
                newpassword=new_password
            )
            conn = await test_env.get_connection_async(password=new_password)
            await conn.changepassword(
                new_password, test_env.get_main_password()
            )

    async def test_5328(self):
        "5328 - test use of autocommit during reexecute"
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        data_to_insert = [(1, "Test String #1"), (2, "Test String #2")]
        async with test_env.get_connection_async() as conn:
            cursor = conn.cursor()
            other_conn = await test_env.get_connection_async()
            other_cursor = other_conn.cursor()
            await cursor.execute("truncate table TestTempTable")
            await cursor.execute(sql, data_to_insert[0])
            await other_cursor.execute(
                "select IntCol, StringCol1 from TestTempTable"
            )
            self.assertEqual(await other_cursor.fetchall(), [])
            conn.autocommit = True
            await cursor.execute(sql, data_to_insert[1])
            await other_cursor.execute(
                "select IntCol, StringCol1 from TestTempTable"
            )
            self.assertEqual(await other_cursor.fetchall(), data_to_insert)

    async def test_5329(self):
        "5329 - test current_schema is set properly"
        async with test_env.get_connection_async() as conn:
            self.assertIsNone(conn.current_schema)

            user = test_env.get_main_user().upper()
            proxy_user = test_env.get_proxy_user().upper()
            cursor = conn.cursor()
            await cursor.execute(
                f"alter session set current_schema={proxy_user}"
            )
            self.assertEqual(conn.current_schema, proxy_user)

            conn.current_schema = user
            self.assertEqual(conn.current_schema, user)

            await cursor.execute(
                "select sys_context('userenv', 'current_schema') from dual"
            )
            (result,) = await cursor.fetchone()
            self.assertEqual(result, user)

    async def test_5330(self):
        "5330 - test dbms_output package"
        async with test_env.get_connection_async() as conn:
            cursor = conn.cursor()
            test_string = "Testing DBMS_OUTPUT package"
            await cursor.callproc("dbms_output.enable")
            await cursor.callproc("dbms_output.put_line", [test_string])
            string_var = cursor.var(str)
            number_var = cursor.var(int)
            await cursor.callproc(
                "dbms_output.get_line", (string_var, number_var)
            )
            self.assertEqual(string_var.getvalue(), test_string)

    async def test_5331(self):
        "5331 - test connection call_timeout"
        async with test_env.get_connection_async() as conn:
            conn.call_timeout = 500  # milliseconds
            self.assertEqual(conn.call_timeout, 500)
            with self.assertRaisesFullCode("DPY-4011", "DPY-4024"):
                with conn.cursor() as cursor:
                    await cursor.callproc(test_env.get_sleep_proc_name(), [2])

    async def test_5332(self):
        "5332 - test Connection repr()"

        class MyConnection(oracledb.AsyncConnection):
            pass

        conn = await test_env.get_connection_async(conn_class=MyConnection)
        qual_name = conn.__class__.__qualname__
        expected_value = (
            f"<{__name__}.{qual_name} to {conn.username}@{conn.dsn}>"
        )
        self.assertEqual(repr(conn), expected_value)

        await conn.close()
        expected_value = f"<{__name__}.{qual_name} disconnected>"
        self.assertEqual(repr(conn), expected_value)

    async def test_5333(self):
        "5333 - test getting write-only attributes"
        async with test_env.get_connection_async() as conn:
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

    async def test_5334(self):
        "5334 - test error for invalid type for params and pool"
        pool = test_env.get_pool_async()
        await pool.close()
        with self.assertRaisesFullCode("DPY-1002"):
            await test_env.get_connection_async(pool=pool)
        with self.assertRaises(TypeError):
            await test_env.get_connection_async(
                pool="This isn't an instance of a pool"
            )
        with self.assertRaisesFullCode("DPY-2025"):
            await oracledb.connect_async(params={"number": 7})

    async def test_5335(self):
        "5335 - test connection instance name"
        async with test_env.get_connection_async() as conn:
            cursor = conn.cursor()
            await cursor.execute(
                """
                select upper(sys_context('userenv', 'instance_name'))
                from dual
                """
            )
            (instance_name,) = await cursor.fetchone()
            self.assertEqual(conn.instance_name.upper(), instance_name)

    @unittest.skipIf(test_env.get_is_drcp(), "not supported with DRCP")
    @unittest.skipIf(
        test_env.get_server_version() < (23, 0),
        "unsupported server",
    )
    async def test_5337(self):
        "5337 - test maximum allowed length for password"
        async with test_env.get_connection_async() as conn:
            if await self.is_on_oracle_cloud(conn):
                self.skipTest(
                    "passwords on Oracle Cloud are strictly controlled"
                )

            original_password = test_env.get_main_password()
            new_password_32 = "a" * 32
            await conn.changepassword(original_password, new_password_32)
            conn = await test_env.get_connection_async(
                password=new_password_32
            )

            new_password_1024 = "a" * 1024
            await conn.changepassword(new_password_32, new_password_1024)
            conn = await test_env.get_connection_async(
                password=new_password_1024
            )
            await conn.changepassword(new_password_1024, original_password)

            new_password_1025 = "a" * 1025
            with self.assertRaisesFullCode("ORA-28218", "ORA-00972"):
                await conn.changepassword(original_password, new_password_1025)

    async def test_5338(self):
        "5338 - test getting db_name"
        async with test_env.get_connection_async() as conn:
            cursor = conn.cursor()
            await cursor.execute("select name from V$DATABASE")
            (db_name,) = await cursor.fetchone()
            self.assertEqual(conn.db_name.upper(), db_name.upper())

    async def test_5339(self):
        "5339 - test getting max_open_cursors"
        async with test_env.get_connection_async() as conn:
            cursor = conn.cursor()
            await cursor.execute(
                "select value from V$PARAMETER where name='open_cursors'"
            )
            (max_open_cursors,) = await cursor.fetchone()
            self.assertEqual(conn.max_open_cursors, int(max_open_cursors))

    async def test_5340(self):
        "5340 - test getting service_name"
        async with test_env.get_connection_async() as conn:
            cursor = conn.cursor()
            await cursor.execute(
                "select sys_context('userenv', 'service_name') from dual"
            )
            (service_name,) = await cursor.fetchone()
            self.assertEqual(conn.service_name, service_name)

    async def test_5341(self):
        "5341 - test transaction_in_progress"
        async with test_env.get_connection_async() as conn:
            self.assertFalse(conn.transaction_in_progress)

            cursor = conn.cursor()
            await cursor.execute("truncate table TestTempTable")
            self.assertFalse(conn.transaction_in_progress)

            await cursor.execute(
                "insert into TestTempTable (IntCol) values (1)"
            )
            self.assertTrue(conn.transaction_in_progress)

            await conn.commit()
            self.assertFalse(conn.transaction_in_progress)

    async def test_5342(self):
        "5342 - test getting db_domain"
        async with test_env.get_connection_async() as conn:
            (db_domain,) = await conn.fetchone(
                "select value from V$PARAMETER where name='db_domain'"
            )
            self.assertEqual(conn.db_domain, db_domain)

    async def test_5343(self):
        "5343 - test connection with invalid conn_class"
        with self.assertRaisesFullCode("DPY-2023"):
            await test_env.get_connection_async(
                conn_class=oracledb.ConnectionPool
            )

    async def test_5344(self):
        "5344 - test connection with an invalid pool"
        with self.assertRaises(TypeError):
            await oracledb.connect_async(pool="not a pool object")

    async def test_5346(self):
        "5346 - test passing program when creating a connection"
        sql = (
            "select program from v$session "
            "where sid = sys_context('userenv', 'sid')"
        )
        await self.__verify_connect_arg("program", "newprogram", sql)

    async def test_5347(self):
        "5347 - test passing machine when creating a connection"
        sql = (
            "select machine from v$session "
            "where sid = sys_context('userenv', 'sid')"
        )
        await self.__verify_connect_arg("machine", "newmachine", sql)

    async def test_5348(self):
        "5348 - test passing terminal when creating a connection"
        sql = (
            "select terminal from v$session "
            "where sid = sys_context('userenv', 'sid')"
        )
        await self.__verify_connect_arg("terminal", "newterminal", sql)

    async def test_5349(self):
        "5349 - test passing osuser when creating a connection"
        sql = (
            "select osuser from v$session "
            "where sid = sys_context('userenv', 'sid')"
        )
        await self.__verify_connect_arg("osuser", "newosuser", sql)

    async def test_5350(self):
        "5350 - test passing driver_name when creating a connection"
        sql = (
            "select distinct client_driver from v$session_connect_info "
            "where sid = sys_context('userenv', 'sid')"
        )
        await self.__verify_connect_arg("driver_name", "newdriver", sql)

    async def test_5351(self):
        "5351 - test getting session id"
        async with test_env.get_connection_async() as conn:
            cursor = conn.cursor()
            await cursor.execute(
                "select dbms_debug_jdwp.current_session_id from dual"
            )
            (fetched_value,) = await cursor.fetchone()
            self.assertEqual(conn.session_id, fetched_value)

    async def test_5352(self):
        "5352 - test getting session serial number"
        async with test_env.get_connection_async() as conn:
            cursor = conn.cursor()
            await cursor.execute(
                "select dbms_debug_jdwp.current_session_serial from dual"
            )
            (fetched_value,) = await cursor.fetchone()
            self.assertEqual(conn.serial_num, fetched_value)

    async def test_5353(self):
        "5353 - test passed params in hook with standalone connection"
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
            await oracledb.connect_async(dsn=connect_string, params=params)
            self.assertEqual(params.sdu, sdu)
        finally:
            oracledb.register_protocol(protocol, None)

    async def test_5354(self):
        "5354 - test altering connection edition"
        conn = await test_env.get_admin_connection_async()
        self.assertIsNone(conn.edition)
        cursor = conn.cursor()
        sql = "select sys_context('USERENV', 'CURRENT_EDITION_NAME') from dual"
        default_edition = "ORA$BASE"
        test_edition = test_env.get_edition_name()
        for edition in [test_edition, default_edition]:
            with self.subTest(edition=edition):
                await cursor.execute(f"alter session set edition = {edition}")
                await cursor.execute(sql)
                (fetched_edition,) = await cursor.fetchone()
                self.assertEqual(fetched_edition, edition.upper())
                self.assertEqual(conn.edition, edition.upper())

    async def test_5355(self):
        "5355 - test connect() with edition"
        edition = test_env.get_edition_name()
        conn = await test_env.get_connection_async(edition=edition)
        cursor = conn.cursor()
        await cursor.execute(
            "select sys_context('USERENV', 'CURRENT_EDITION_NAME') from dual"
        )
        (fetched_edition,) = await cursor.fetchone()
        self.assertEqual(fetched_edition, edition.upper())
        self.assertEqual(conn.edition, edition)

    async def test_5356(self):
        "5356 - test error in the middle of a database response"
        conn = await test_env.get_connection_async()
        cursor = conn.cursor()
        await cursor.execute("truncate table TestTempTable")
        data = [(i + 1, 2 if i < 1499 else 0) for i in range(1500)]
        await cursor.executemany(
            "insert into TestTempTable (IntCol, NumberCol) values (:1, :2)",
            data,
        )
        await conn.commit()
        cursor.arraysize = 1500
        with self.assertRaisesFullCode("ORA-01476"):
            await cursor.execute(
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
            await cursor.fetchall()


if __name__ == "__main__":
    test_env.run_test_cases()
