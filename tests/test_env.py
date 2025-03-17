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

# -----------------------------------------------------------------------------
# Sets the environment used by the python-oracledb test suite. Production
# applications should consider using External Authentication to avoid hard
# coded credentials.
#
# You can set values in environment variables to bypass having the test suite
# request the information it requires.
#
#   PYO_TEST_MAIN_USER: user used for most test cases
#   PYO_TEST_MAIN_PASSWORD: password of user used for most test cases
#   PYO_TEST_PROXY_USER: user for testing proxying
#   PYO_TEST_PROXY_PASSWORD: password of user for testing proxying
#   PYO_TEST_CONNECT_STRING: connect string for test suite
#   PYO_TEST_ADMIN_USER: administrative user for test suite
#   PYO_TEST_ADMIN_PASSWORD: administrative password for test suite
#   PYO_TEST_WALLET_LOCATION: location of wallet file (thin mode, mTLS)
#   PYO_TEST_WALLET_PASSWORD: password for wallet file (thin mode, mTLS)
#   PYO_TEST_DRIVER_MODE: python-oracledb mode (thick or thin) to use
#   PYO_TEST_EXTERNAL_USER: user for testing external authentication
#   PYO_TEST_EDITION_NAME: name of edition for editioning tests
#   PYO_TEST_PLUGINS: list of plugins to import before running tests
#
# PYO_TEST_CONNECT_STRING can be set to an Easy Connect string, or a
# Net Service Name from a tnsnames.ora file or external naming service,
# or it can be the name of a local Oracle database instance.
#
# If oracledb is using Instant Client, then an Easy Connect string is generally
# appropriate. The syntax is:
#
#   [//]host_name[:port][/service_name][:server_type][/instance_name]
#
# Commonly just the host_name and service_name are needed
# e.g. "localhost/orclpdb1" or "localhost/XEPDB1"
#
# If using a tnsnames.ora file, the file can be in a default
# location such as $ORACLE_HOME/network/admin/tnsnames.ora or
# /etc/tnsnames.ora.  Alternatively set the TNS_ADMIN environment
# variable and put the file in $TNS_ADMIN/tnsnames.ora.
#
# The administrative user for cloud databases is ADMIN and the administrative
# user for on premises databases is SYSTEM.
# -----------------------------------------------------------------------------

import getpass
import importlib
import os
import secrets
import sys
import string
import unittest

import oracledb

# default values
DEFAULT_MAIN_USER = "pythontest"
DEFAULT_PROXY_USER = "pythontestproxy"
DEFAULT_CONNECT_STRING = "localhost/orclpdb1"
DEFAULT_EDITION_NAME = "pythonedition"

# dictionary containing all parameters; these are acquired as needed by the
# methods below (which should be used instead of consulting this dictionary
# directly) and then stored so that a value is not requested more than once
PARAMETERS = {}


def _initialize():
    """
    Performs initialization of the test environment. This ensures the desired
    mode is set and imports any required plugins.
    """
    if PARAMETERS.get("INITIALIZED"):
        return
    if not get_is_thin() and oracledb.is_thin_mode():
        oracledb.init_oracle_client()
        oracledb.defaults.thick_mode_dsn_passthrough = False
    plugin_names = os.environ.get("PYO_TEST_PLUGINS")
    if plugin_names is not None:
        for name in plugin_names.split(","):
            module_name = f"oracledb.plugins.{name}"
            print("importing module", module_name)
            importlib.import_module(module_name)
    PARAMETERS["INITIALIZED"] = True


def get_value(name, label, default_value=None, password=False):
    try:
        return PARAMETERS[name]
    except KeyError:
        pass
    env_name = "PYO_TEST_" + name
    value = os.environ.get(env_name)
    if value is None:
        if default_value is not None:
            label += " [%s]" % default_value
        label += ": "
        if password:
            value = getpass.getpass(label)
        else:
            value = input(label).strip()
    if not value:
        value = default_value
    PARAMETERS[name] = value
    return value


def get_admin_connection(use_async=False):
    _initialize()
    admin_user = get_value("ADMIN_USER", "Administrative user", "admin")
    admin_password = get_value(
        "ADMIN_PASSWORD", f"Password for {admin_user}", password=True
    )
    params = get_connect_params()
    if admin_user and admin_user.upper() == "SYS":
        params = params.copy()
        params.set(mode=oracledb.AUTH_MODE_SYSDBA)
    method = oracledb.connect_async if use_async else oracledb.connect
    return method(
        dsn=get_connect_string(),
        params=params,
        user=admin_user,
        password=admin_password,
    )


async def get_admin_connection_async(use_async=False):
    return await get_admin_connection(use_async=True)


def get_charset():
    value = PARAMETERS.get("CHARSET")
    if value is None:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    select value
                    from nls_database_parameters
                    where parameter = 'NLS_CHARACTERSET'
                    """
                )
                (value,) = cursor.fetchone()
                PARAMETERS["CHARSET"] = value
    return value


async def get_charset_async():
    value = PARAMETERS.get("CHARSET")
    if value is None:
        async with get_connection_async() as conn:
            with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    select value
                    from nls_database_parameters
                    where parameter = 'NLS_CHARACTERSET'
                    """
                )
                (value,) = await cursor.fetchone()
                PARAMETERS["CHARSET"] = value
    return value


def get_charset_ratios():
    value = PARAMETERS.get("CS_RATIO")
    if value is None:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            """
            select
                cast('X' as varchar2(1)),
                cast('Y' as nvarchar2(1))
            from dual
            """
        )
        varchar_column_info, nvarchar_column_info = cursor.description
        value = (varchar_column_info[3], nvarchar_column_info[3])
        PARAMETERS["CS_RATIO"] = value
    return value


async def get_charset_ratios_async():
    value = PARAMETERS.get("CS_RATIO")
    if value is None:
        connection = await get_connection_async()
        cursor = connection.cursor()
        await cursor.execute(
            """
            select
                cast('X' as varchar2(1)),
                cast('Y' as nvarchar2(1))
            from dual
            """
        )
        varchar_column_info, nvarchar_column_info = cursor.description
        value = (varchar_column_info[3], nvarchar_column_info[3])
        PARAMETERS["CS_RATIO"] = value
    return value


def get_client_version():
    name = "CLIENT_VERSION"
    value = PARAMETERS.get(name)
    if value is None:
        if get_is_thin():
            value = (23, 7)
        else:
            _initialize()
            value = oracledb.clientversion()[:2]
        PARAMETERS[name] = value
    return value


def get_connect_params():
    wallet_location = get_wallet_location()
    return oracledb.ConnectParams(
        user=get_main_user(),
        password=get_main_password(),
        config_dir=wallet_location,
        wallet_location=wallet_location,
        wallet_password=get_wallet_password(),
        disable_oob=True,
    )


def get_connection(dsn=None, use_async=False, **kwargs):
    _initialize()
    if dsn is None:
        dsn = get_connect_string()
    method = oracledb.connect_async if use_async else oracledb.connect
    return method(dsn=dsn, params=get_connect_params(), **kwargs)


def get_connection_async(dsn=None, **kwargs):
    return get_connection(dsn, use_async=True, **kwargs)


def get_connect_string():
    return get_value(
        "CONNECT_STRING", "Connect String", DEFAULT_CONNECT_STRING
    )


def get_edition_name():
    return get_value("EDITION_NAME", "Edition Name", DEFAULT_EDITION_NAME)


def get_is_drcp():
    value = PARAMETERS.get("IS_DRCP")
    if value is None:
        params = oracledb.ConnectParams()
        params.parse_connect_string(get_connect_string())
        server_type = params.server_type
        value = (
            server_type == "pooled"
            or isinstance(server_type, list)
            and "pooled" in server_type
        )
        PARAMETERS["IS_DRCP"] = value
    return value


def get_is_implicit_pooling():
    value = PARAMETERS.get("IS_IMPLICIT_POOLING")
    if value is None:
        if not get_is_drcp():
            value = False
        else:
            params = oracledb.ConnectParams()
            params.parse_connect_string(get_connect_string())
            pool_boundary = params.pool_boundary
            value = (
                pool_boundary is not None
                or isinstance(pool_boundary, list)
                and [s for s in pool_boundary if s]
            )
        PARAMETERS["IS_IMPLICIT_POOLING"] = value
    return value


def get_is_thin():
    driver_mode = get_value("DRIVER_MODE", "Driver mode (thin|thick)", "thin")
    return driver_mode == "thin"


def get_main_password():
    return get_value(
        "MAIN_PASSWORD", f"Password for {get_main_user()}", password=True
    )


def get_main_user():
    return get_value("MAIN_USER", "Main User Name", DEFAULT_MAIN_USER)


def get_pool(use_async=False, **kwargs):
    _initialize()
    method = oracledb.create_pool_async if use_async else oracledb.create_pool
    return method(dsn=get_connect_string(), params=get_pool_params(), **kwargs)


def get_pool_async(**kwargs):
    return get_pool(use_async=True, **kwargs)


def get_pool_params():
    wallet_location = get_wallet_location()
    return oracledb.PoolParams(
        user=get_main_user(),
        password=get_main_password(),
        config_dir=wallet_location,
        wallet_location=wallet_location,
        wallet_password=get_wallet_password(),
    )


def get_proxy_password():
    return get_value(
        "PROXY_PASSWORD", f"Password for {get_proxy_user()}", password=True
    )


def get_proxy_user():
    return get_value("PROXY_USER", "Proxy User Name", DEFAULT_PROXY_USER)


def get_sleep_proc_name():
    server_version = get_server_version()
    return (
        "dbms_session.sleep" if server_version[0] >= 18 else "dbms_lock.sleep"
    )


def get_server_version():
    name = "SERVER_VERSION"
    value = PARAMETERS.get(name)
    if value is None:
        conn = get_connection()
        value = tuple(int(s) for s in conn.version.split("."))[:2]
        PARAMETERS[name] = value
    return value


async def get_server_version_async():
    name = "SERVER_VERSION"
    value = PARAMETERS.get(name)
    if value is None:
        async with await get_connection_async() as conn:
            value = tuple(int(s) for s in conn.version.split("."))[:2]
            PARAMETERS[name] = value
    return value


def get_wallet_location():
    if get_is_thin():
        return get_value("WALLET_LOCATION", "Wallet Location")


def get_wallet_password():
    if get_is_thin():
        return get_value("WALLET_PASSWORD", "Wallet Password", password=True)


def get_external_user():
    if not get_is_thin():
        return get_value("EXTERNAL_USER", "External User")


def get_random_string(length=10):
    return "".join(secrets.choice(string.ascii_letters) for i in range(length))


def is_on_oracle_cloud(connection):
    server = get_server_version()
    if server < (18, 0):
        return False
    cursor = connection.cursor()
    cursor.execute(
        """
        select sys_context('userenv', 'cloud_service')
        from dual
        """
    )
    (service_name,) = cursor.fetchone()
    return service_name is not None


async def is_on_oracle_cloud_async(connection):
    server = await get_server_version_async()
    if server < (18, 0):
        return False
    cursor = connection.cursor()
    await cursor.execute(
        """
        select sys_context('userenv', 'cloud_service')
        from dual
        """
    )
    (service_name,) = await cursor.fetchone()
    return service_name is not None


def run_sql_script(conn, script_name, **kwargs):
    statement_parts = []
    cursor = conn.cursor()
    replace_values = [("&" + k + ".", v) for k, v in kwargs.items()] + [
        ("&" + k, v) for k, v in kwargs.items()
    ]
    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    file_name = os.path.join(script_dir, "sql", script_name + ".sql")
    for line in open(file_name):
        if line.strip() == "/":
            statement = "".join(statement_parts).strip()
            if statement:
                for search_value, replace_value in replace_values:
                    statement = statement.replace(search_value, replace_value)
                try:
                    cursor.execute(statement)
                except:
                    print("Failed to execute SQL:", statement)
                    raise
            statement_parts = []
        else:
            statement_parts.append(line)
    cursor.execute(
        """
        select name, type, line, position, text
        from dba_errors
        where owner = upper(:owner)
        order by name, type, line, position
        """,
        owner=get_main_user(),
    )
    prev_name = prev_obj_type = None
    for name, obj_type, line_num, position, text in cursor:
        if name != prev_name or obj_type != prev_obj_type:
            print("%s (%s)" % (name, obj_type))
            prev_name = name
            prev_obj_type = obj_type
        print("    %s/%s %s" % (line_num, position, text))


def run_test_cases():
    get_is_thin()
    unittest.main(testRunner=unittest.TextTestRunner(verbosity=2))


def skip_soda_tests():
    if get_is_thin():
        return True
    client = get_client_version()
    if client < (18, 3):
        return True
    server = get_server_version()
    if server < (18, 0):
        return True
    if server > (20, 1) and client < (20, 1):
        return True
    return False


class DefaultsContextManager:
    def __init__(self, attribute, desired_value):
        self.attribute = attribute
        self.desired_value = desired_value

    def __enter__(self):
        self.original_value = getattr(oracledb.defaults, self.attribute)
        setattr(oracledb.defaults, self.attribute, self.desired_value)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        setattr(oracledb.defaults, self.attribute, self.original_value)


class SystemStatInfo:
    get_sid_sql = "select sys_context('userenv', 'sid') from dual"
    get_stat_sql = """
          select ss.value
          from v$sesstat ss, v$statname sn
          where ss.sid = :sid
              and ss.statistic# = sn.statistic#
              and sn.name = :stat_name
          """
    stat_name = None

    def _initialize(self, connection):
        self.prev_value = 0
        self.admin_conn = get_admin_connection()
        with connection.cursor() as cursor:
            cursor.execute(self.get_sid_sql)
            (self.sid,) = cursor.fetchone()
        self.get_value()

    async def _initialize_async(self, connection):
        self.prev_value = 0
        self.admin_conn = await get_admin_connection_async()
        with connection.cursor() as cursor:
            await cursor.execute(self.get_sid_sql)
            (self.sid,) = await cursor.fetchone()
        await self.get_value_async()

    def get_value(self):
        with self.admin_conn.cursor() as cursor:
            cursor.execute(
                self.get_stat_sql, sid=self.sid, stat_name=self.stat_name
            )
            (current_value,) = cursor.fetchone()
            diff_value = current_value - self.prev_value
            self.prev_value = current_value
            return diff_value

    async def get_value_async(self):
        with self.admin_conn.cursor() as cursor:
            await cursor.execute(
                self.get_stat_sql, sid=self.sid, stat_name=self.stat_name
            )
            (current_value,) = await cursor.fetchone()
            diff_value = current_value - self.prev_value
            self.prev_value = current_value
            return diff_value


class RoundTripInfo(SystemStatInfo):
    stat_name = "SQL*Net roundtrips to/from client"


class ParseCountInfo(SystemStatInfo):
    stat_name = "parse count (total)"


class FullCodeErrorContextManager:

    def __init__(self, full_codes):
        self.full_codes = full_codes
        if len(full_codes) == 1:
            self.message_fragment = f'Error "{full_codes[0]}"'
        else:
            message_fragment = ", ".join(f'"{s}"' for s in full_codes[:-1])
            message_fragment += f' or "{full_codes[-1]}"'
            self.message_fragment = f"One of the errors {message_fragment}"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_type is None:
            raise AssertionError(f"{self.message_fragment} was not raised.")
        if not issubclass(exc_type, oracledb.Error):
            return False
        if issubclass(exc_type, oracledb.Error):
            self.error_obj = exc_value.args[0]
            if self.error_obj.full_code not in self.full_codes:
                message = (
                    f"{self.message_fragment} should have been raised but "
                    f'"{self.error_obj.full_code}" was raised instead.'
                )
                raise AssertionError(message)
        return True


class BaseTestCase(unittest.TestCase):
    requires_connection = True

    def assertParseCount(self, n):
        self.assertEqual(self.parse_count_info.get_value(), n)

    def assertRaisesFullCode(self, *full_codes):
        return FullCodeErrorContextManager(full_codes)

    def assertRoundTrips(self, n):
        self.assertEqual(self.round_trip_info.get_value(), n)

    def get_and_clear_queue(
        self,
        queue_name,
        payload_type=None,
        message="not supported with this client/server combination",
    ):
        if payload_type == "JSON":
            min_version = (21, 0)
            if (
                get_client_version() < min_version
                or get_server_version() < min_version
            ):
                self.skipTest(message)
        elif isinstance(payload_type, str):
            payload_type = self.conn.gettype(payload_type)
        queue = self.conn.queue(queue_name, payload_type)
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        while queue.deqone():
            pass
        return self.conn.queue(queue_name, payload_type)

    def get_db_object_as_plain_object(self, obj):
        if obj.type.iscollection:
            element_values = []
            for value in obj.aslist():
                if isinstance(value, oracledb.DbObject):
                    value = self.get_db_object_as_plain_object(value)
                elif isinstance(value, oracledb.LOB):
                    value = value.read()
                element_values.append(value)
            return element_values
        attr_values = []
        for attribute in obj.type.attributes:
            value = getattr(obj, attribute.name)
            if isinstance(value, oracledb.DbObject):
                value = self.get_db_object_as_plain_object(value)
            elif isinstance(value, oracledb.LOB):
                value = value.read()
            attr_values.append(value)
        return tuple(attr_values)

    def get_sid_serial(self, conn=None):
        """
        Returns the sid and serial number of the connection as a 2-tuple.
        """
        if conn is None:
            conn = self.conn
        if get_is_thin():
            return (conn.session_id, conn.serial_num)
        else:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    select
                        dbms_debug_jdwp.current_session_id,
                        dbms_debug_jdwp.current_session_serial
                    from dual
                    """
                )
                return cursor.fetchone()

    def get_soda_database(
        self,
        minclient=(18, 3),
        minserver=(18, 0),
        message="not supported with this client/server combination",
        drop_collections=True,
    ):
        client = get_client_version()
        if client < minclient:
            self.skipTest(message)
        server = get_server_version()
        if server < minserver:
            self.skipTest(message)
        if server > (20, 1) and client < (20, 1):
            self.skipTest(message)
        soda_db = self.conn.getSodaDatabase()
        if drop_collections:
            for name in soda_db.getCollectionNames():
                soda_db.openCollection(name).drop()
        return soda_db

    def is_on_oracle_cloud(self, connection=None):
        if connection is None:
            connection = self.conn
        return is_on_oracle_cloud(connection)

    def setUp(self):
        if self.requires_connection:
            self.conn = get_connection()
            self.cursor = self.conn.cursor()
            self.cursor.execute("alter session set time_zone = '+00:00'")

    def setup_parse_count_checker(self, conn=None):
        if get_is_implicit_pooling():
            self.skipTest("sessions can change with implicit pooling")
        self.parse_count_info = ParseCountInfo()
        self.parse_count_info._initialize(conn or self.conn)

    def setup_round_trip_checker(self, conn=None):
        if get_is_implicit_pooling():
            self.skipTest("sessions can change with implicit pooling")
        self.round_trip_info = RoundTripInfo()
        self.round_trip_info._initialize(conn or self.conn)

    def tearDown(self):
        if self.requires_connection:
            self.conn.close()
            del self.cursor
            del self.conn


class BaseAsyncTestCase(unittest.IsolatedAsyncioTestCase):
    requires_connection = True

    async def assertParseCount(self, n):
        self.assertEqual(await self.parse_count_info.get_value_async(), n)

    def assertRaisesFullCode(self, *full_codes):
        return FullCodeErrorContextManager(full_codes)

    async def assertRoundTrips(self, n):
        self.assertEqual(await self.round_trip_info.get_value_async(), n)

    async def asyncSetUp(self):
        if self.requires_connection:
            self.conn = await get_connection_async()
            self.cursor = self.conn.cursor()
            await self.cursor.execute("alter session set time_zone = '+00:00'")

    async def asyncTearDown(self):
        if self.requires_connection:
            await self.conn.close()
            del self.cursor
            del self.conn

    async def get_and_clear_queue(
        self,
        queue_name,
        payload_type=None,
        message="not supported with this client/server combination",
    ):
        if payload_type == "JSON":
            if get_server_version() < (21, 0):
                self.skipTest(message)
        elif isinstance(payload_type, str):
            payload_type = await self.conn.gettype(payload_type)
        queue = self.conn.queue(queue_name, payload_type)
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        while await queue.deqone():
            pass
        return self.conn.queue(queue_name, payload_type)

    async def get_db_object_as_plain_object(self, obj):
        if obj.type.iscollection:
            element_values = []
            for value in obj.aslist():
                if isinstance(value, oracledb.DbObject):
                    value = await self.get_db_object_as_plain_object(value)
                elif isinstance(value, oracledb.AsyncLOB):
                    value = await value.read()
                element_values.append(value)
            return element_values
        attr_values = []
        for attribute in obj.type.attributes:
            value = getattr(obj, attribute.name)
            if isinstance(value, oracledb.DbObject):
                value = await self.get_db_object_as_plain_object(value)
            elif isinstance(value, oracledb.AsyncLOB):
                value = await value.read()
            attr_values.append(value)
        return tuple(attr_values)

    async def get_sid_serial(self, conn=None):
        """
        Returns the sid and serial number of the connection as a 2-tuple.
        """
        if conn is None:
            conn = self.conn
        if get_is_thin():
            return (conn.session_id, conn.serial_num)
        else:
            with conn.cursor() as cursor:
                await cursor.execute(
                    """
                    select
                        dbms_debug_jdwp.current_session_id,
                        dbms_debug_jdwp.current_session_serial
                    from dual
                    """
                )
                return await cursor.fetchone()

    async def is_on_oracle_cloud(self, connection=None):
        if connection is None:
            connection = self.conn
        return await is_on_oracle_cloud_async(connection)

    async def setup_parse_count_checker(self, conn=None):
        if get_is_implicit_pooling():
            self.skipTest("sessions can change with implicit pooling")
        self.parse_count_info = ParseCountInfo()
        await self.parse_count_info._initialize_async(conn or self.conn)

    async def setup_round_trip_checker(self, conn=None):
        if get_is_implicit_pooling():
            self.skipTest("sessions can change with implicit pooling")
        self.round_trip_info = RoundTripInfo()
        await self.round_trip_info._initialize_async(conn or self.conn)
