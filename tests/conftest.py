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
#   PYO_TEST_EXTERNAL_USER: user for testing external authentication
#   PYO_TEST_EDITION_NAME: name of edition for editioning tests
#   PYO_TEST_PLUGINS: list of plugins to import before running tests
#   PYO_TEST_ORACLE_CLIENT_PATH: Oracle Client or Instant Client library dir
#
# PYO_TEST_CONNECT_STRING can be set to an Easy Connect string, or a
# Net Service Name from a tnsnames.ora file or external naming service,
# or it can be the name of a local Oracle database instance.
#
# On Windows set PYO_TEST_ORACLE_CLIENT_PATH if Oracle libraries are not in
# PATH. On macOS set the variable to the Instant Client directory. On Linux do
# not set the variable; instead set LD_LIBRARY_PATH or configure ldconfig
# before running Python.
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

import importlib
import os
import platform
import secrets
import string

import numpy
import oracledb
import pandas
import pytest


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

    def _initialize(self, conn, admin_conn):
        self.prev_value = 0
        self.admin_conn = admin_conn
        with conn.cursor() as cursor:
            cursor.execute(self.get_sid_sql)
            (self.sid,) = cursor.fetchone()
        self.get_value()

    async def _initialize_async(self, conn, admin_conn):
        self.prev_value = 0
        self.admin_conn = admin_conn
        with conn.cursor() as cursor:
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


class TestEnv:

    def _convert_df_value(self, df_val):
        """
        This method converts a dataframe cell value to use with assertions
        For e.g. NaN and np.array cannot be compared directly. Values are
        converted according to the following rules:
         - NaN -> None
         - np.array -> np.array.tolist() (Python list)
        """
        if isinstance(df_val, numpy.ndarray):
            return df_val.tolist()
        elif pandas.isna(df_val):
            return None
        elif isinstance(df_val, dict):
            return {k: self._convert_df_value(v) for k, v in df_val.items()}
        else:
            return df_val

    def _get_charset(self, conn):
        """
        Determines the character set in use by the database.
        """
        with conn.cursor() as cursor:
            cursor.execute(
                """
                select value
                from nls_database_parameters
                where parameter = 'NLS_CHARACTERSET'
                """
            )
            (value,) = cursor.fetchone()
            return value

    def _get_charset_ratios(self, conn):
        """
        Calculates the character set ratios used by the database.
        """
        cursor = conn.cursor()
        cursor.execute(
            """
            select
                cast('X' as varchar2(1)),
                cast('Y' as nvarchar2(1))
            from dual
            """
        )
        varchar_info, nvarchar_info = cursor.description
        return (varchar_info.internal_size, nvarchar_info.internal_size)

    def _initialize(self):
        """
        Initializes the remaining items after establishing a connection to the
        database. This is done so that alternative initialization of some
        process wide variables in thick mode can take place independently for
        some tests.
        """

        # if already initialized, nothing to do!
        if self.initialized:
            return

        # setup thick mode, if needed
        if self.use_thick_mode:
            if oracledb.is_thin_mode():
                oracledb.init_oracle_client(lib_dir=self.oracle_client_path)
            oracledb.defaults.thick_mode_dsn_passthrough = False
            self.client_version = oracledb.clientversion()[:2]

        # import any requested plugins
        if self.plugins is not None:
            for name in self.plugins.split(","):
                module_name = f"oracledb.plugins.{name}"
                importlib.import_module(module_name)

        # establish a connection to determine the remaining information
        params = self.get_connect_params()
        conn = oracledb.connect(dsn=self.connect_string, params=params)
        version_parts = conn.version.split(".")[:2]
        self.server_version = tuple(int(s) for s in version_parts)
        self.is_drcp = self._is_drcp()
        self.is_implicit_pooling = self._is_implicit_pooling()
        self.is_on_oracle_cloud = self._is_on_oracle_cloud(conn)
        self.charset = self._get_charset(conn)
        self.charset_ratios = self._get_charset_ratios(conn)
        self.sleep_proc_name = (
            "dbms_session.sleep"
            if self.server_version >= (18, 0)
            else "dbms_lock.sleep"
        )

        # mark environment as fully initialized
        self.initialized = True

    def _is_drcp(self):
        """
        Calculates whether or not DRCP is being used.
        """
        params = oracledb.ConnectParams()
        params.parse_connect_string(self.connect_string)
        server_type = params.server_type
        return (
            server_type == "pooled"
            or isinstance(server_type, list)
            and "pooled" in server_type
        )

    def _is_implicit_pooling(self):
        """
        Calculates whether implicit pooling is being used.
        """
        if not self.is_drcp:
            return False
        params = oracledb.ConnectParams()
        params.parse_connect_string(self.connect_string)
        pool_boundary = params.pool_boundary
        return (
            pool_boundary is not None
            or isinstance(pool_boundary, list)
            and [s for s in pool_boundary if s]
        )

    def _is_on_oracle_cloud(self, conn):
        """
        Calculates whether the database is running on Oracle Cloud.
        """
        if self.server_version < (18, 0):
            return False
        cursor = conn.cursor()
        cursor.execute(
            """
            select sys_context('userenv', 'cloud_service')
            from dual
            """
        )
        (service_name,) = cursor.fetchone()
        return service_name is not None

    def assert_raises_full_code(self, *full_codes):
        """
        Verifies that the block of code raises an exception with the specified
        full codes.
        """
        return FullCodeErrorContextManager(full_codes)

    def create_schema(self, conn):
        """
        Creates the database objects used by the python-oracledb test suite.
        """
        self.drop_schema(conn)
        self.run_sql_script(
            conn,
            "create_schema",
            main_user=self.main_user,
            main_password=self.main_password,
            proxy_user=self.proxy_user,
            proxy_password=self.proxy_password,
            edition_name=self.edition_name,
        )
        if self.has_server_version(21):
            self.run_sql_script(
                conn, "create_schema_21", main_user=self.main_user
            )
        if self.has_server_version(23, 4):
            self.run_sql_script(
                conn, "create_schema_23_4", main_user=self.main_user
            )
        if self.has_server_version(23, 5):
            self.run_sql_script(
                conn, "create_schema_23_5", main_user=self.main_user
            )
        if self.has_server_version(23, 7):
            self.run_sql_script(
                conn, "create_schema_23_7", main_user=self.main_user
            )
        if self.is_on_oracle_cloud:
            self.run_sql_script(
                conn, "create_schema_cloud", main_user=self.main_user
            )

    def drop_schema(self, conn):
        """
        Drops the database objects used by the python-oracledb test suite.
        """
        self.run_sql_script(
            conn,
            "drop_schema",
            main_user=self.main_user,
            proxy_user=self.proxy_user,
            edition_name=self.edition_name,
        )

    def defaults_context_manager(self, attribute, desired_value):
        """
        Returns a defaults context manager which sets the specified attribute
        to the desired value and restores it once the block completes.
        """
        return DefaultsContextManager(attribute, desired_value)

    def get_admin_connection(self, use_async=False):
        """
        Returns an administrative connection to the database.
        """
        if not self.admin_user or not self.admin_password:
            pytest.skip("missing administrative credentials")
        if self.use_thick_mode and oracledb.is_thin_mode():
            oracledb.init_oracle_client(lib_dir=self.oracle_client_path)
        params = self.get_connect_params()
        if self.admin_user.upper() == "SYS":
            params = params.copy()
            params.set(mode=oracledb.AUTH_MODE_SYSDBA)
        method = oracledb.connect_async if use_async else oracledb.connect
        return method(
            dsn=self.connect_string,
            params=params,
            user=self.admin_user,
            password=self.admin_password,
        )

    def get_admin_connection_async(self):
        """
        Returns an administrative connection to the database.
        """
        return self.get_admin_connection(use_async=True)

    def get_and_clear_queue(
        self,
        conn,
        queue_name,
        payload_type=None,
        message="not supported with this client/server combination",
    ):
        if payload_type == "JSON":
            if not self.has_client_and_server_version(21):
                pytest.skip(message)
        elif isinstance(payload_type, str):
            payload_type = conn.gettype(payload_type)
        queue = conn.queue(queue_name, payload_type)
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        while queue.deqone():
            pass
        return conn.queue(queue_name, payload_type)

    async def get_and_clear_queue_async(
        self,
        conn,
        queue_name,
        payload_type=None,
        message="not supported with this client/server combination",
    ):
        if payload_type == "JSON":
            if not self.has_client_and_server_version(21):
                pytest.skip(message)
        elif isinstance(payload_type, str):
            payload_type = await conn.gettype(payload_type)
        queue = conn.queue(queue_name, payload_type)
        queue.deqoptions.wait = oracledb.DEQ_NO_WAIT
        queue.deqoptions.deliverymode = oracledb.MSG_PERSISTENT_OR_BUFFERED
        queue.deqoptions.visibility = oracledb.DEQ_IMMEDIATE
        while await queue.deqone():
            pass
        return conn.queue(queue_name, payload_type)

    def get_connect_params(self):
        """
        Returns an instance of ConnectParams used to manage connection
        parameters.
        """
        return oracledb.ConnectParams(
            user=self.main_user,
            password=self.main_password,
            config_dir=self.wallet_location,
            wallet_location=self.wallet_location,
            wallet_password=self.wallet_password,
            disable_oob=True,
        )

    def get_connection(self, dsn=None, use_async=False, **kwargs):
        """
        Returns a connection to the database.
        """
        self._initialize()
        if dsn is None:
            dsn = self.connect_string
        method = oracledb.connect_async if use_async else oracledb.connect
        return method(dsn=dsn, params=self.get_connect_params(), **kwargs)

    def get_connection_async(self, dsn=None, **kwargs):
        """
        Returns a connection to the database using asyncio.
        """
        return self.get_connection(dsn, use_async=True, **kwargs)

    def get_data_from_df(self, df):
        """
        Returns data from the data frame in a normalized fashion suitable for
        comparison. In particular, NaN values cannot be compared to one another
        so they are converted to the value None for comparison purposes.
        """
        return [
            tuple(self._convert_df_value(v) for v in row)
            for row in df.itertuples(index=False, name=None)
        ]

    def get_db_object_as_plain_object(self, obj):
        """
        Returns a database object as a plain object to make assertions simpler.
        """
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

    async def get_db_object_as_plain_object_async(self, obj):
        """
        Returns a database object as a plain object to make assertions simpler.
        """
        if obj.type.iscollection:
            element_values = []
            for value in obj.aslist():
                if isinstance(value, oracledb.DbObject):
                    value = await self.get_db_object_as_plain_object_async(
                        value
                    )
                elif isinstance(value, oracledb.AsyncLOB):
                    value = await value.read()
                element_values.append(value)
            return element_values
        attr_values = []
        for attribute in obj.type.attributes:
            value = getattr(obj, attribute.name)
            if isinstance(value, oracledb.DbObject):
                value = await self.get_db_object_as_plain_object_async(value)
            elif isinstance(value, oracledb.AsyncLOB):
                value = await value.read()
            attr_values.append(value)
        return tuple(attr_values)

    def get_pool(self, use_async=False, **kwargs):
        """
        Returns a connection pool for the database.
        """
        self._initialize()
        method = (
            oracledb.create_pool_async if use_async else oracledb.create_pool
        )
        return method(
            dsn=self.connect_string, params=self.get_pool_params(), **kwargs
        )

    def get_pool_async(self, **kwargs):
        """
        Returns a connection pool for the database using asyncio.
        """
        return self.get_pool(use_async=True, **kwargs)

    def get_pool_params(self):
        """
        Returns an instance of PoolParams used to manage connection pool
        parameters.
        """
        return oracledb.PoolParams(
            user=self.main_user,
            password=self.main_password,
            config_dir=self.wallet_location,
            wallet_location=self.wallet_location,
            wallet_password=self.wallet_password,
            disable_oob=True,
        )

    def get_random_string(self, length=10):
        """
        Return a random string of the specified length.
        """
        return "".join(
            secrets.choice(string.ascii_letters) for i in range(length)
        )

    def get_sid_serial(self, conn):
        """
        Returns the sid and serial number of the connection as a 2-tuple.
        """
        if not self.use_thick_mode:
            return (conn.session_id, conn.serial_num)
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

    def has_client_and_server_version(self, major_version, minor_version=0):
        """
        Returns a boolean indicating if the test environment is using a client
        version and a database with the specified version or later.
        """
        if not self.has_client_version(major_version, minor_version):
            return False
        if not self.has_server_version(major_version, minor_version):
            return False
        return True

    def has_client_version(self, major_version, minor_version=0):
        """
        Returns a boolean indicating if the test environment is using a client
        version with the specified version or later.
        """
        self._initialize()
        if oracledb.is_thin_mode():
            return True
        return self.client_version >= (major_version, minor_version)

    def has_server_version(self, major_version, minor_version=0):
        """
        Returns a boolean indicating if the test environment is using a server
        version with the specified version or later.
        """
        self._initialize()
        return self.server_version >= (major_version, minor_version)

    def run_sql_script(self, conn, script_name, **kwargs):
        """
        Runs the specified script with the specified replacement values.
        """
        statement_parts = []
        cursor = conn.cursor()
        replace_values = [("&" + k + ".", v) for k, v in kwargs.items()] + [
            ("&" + k, v) for k, v in kwargs.items()
        ]
        script_dir = os.path.dirname(__file__)
        file_name = os.path.join(script_dir, "sql", script_name + ".sql")
        for line in open(file_name):
            if line.strip() == "/":
                statement = "".join(statement_parts).strip()
                if statement:
                    for search_value, replace_value in replace_values:
                        statement = statement.replace(
                            search_value, replace_value
                        )
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
            owner=self.main_user,
        )
        prev_name = prev_obj_type = None
        for name, obj_type, line_num, position, text in cursor:
            if name != prev_name or obj_type != prev_obj_type:
                print("%s (%s)" % (name, obj_type))
                prev_name = name
                prev_obj_type = obj_type
            print("    %s/%s %s" % (line_num, position, text))
        assert prev_name is None

    def skip_unless_client_version(self, major_version, minor_version=0):
        """
        Skips the test unless the specified client version or higher is being
        used.
        """
        if not self.has_client_version(major_version, minor_version):
            if minor_version == 0:
                version = str(major_version)
            else:
                version = f"{major_version}.{minor_version}"
            pytest.skip(f"requires Oracle Client {version} or higher")

    def skip_unless_server_version(self, major_version, minor_version=0):
        """
        Skips the test unless the specified server version or higher is being
        used.
        """
        if not self.has_server_version(major_version, minor_version):
            if minor_version == 0:
                version = str(major_version)
            else:
                version = f"{major_version}.{minor_version}"
            pytest.skip(f"requires Oracle Database {version} or higher")


@pytest.fixture
def admin_conn(test_env):
    """
    Return an administrative connection to the database using the pytest
    configuration.
    """
    with test_env.get_admin_connection() as conn:
        yield conn


@pytest.fixture
def anyio_backend():
    """
    Only asyncio is being tested currently.
    """
    return "asyncio"


@pytest.fixture
async def async_admin_conn(test_env):
    """
    Return an administrative connection to the database using the pytest
    configuration with asyncio.
    """
    async with test_env.get_admin_connection_async() as conn:
        yield conn


@pytest.fixture
async def async_conn(test_env):
    """
    Return a connection to the database using the pytest configuration with
    asyncio
    """
    async with test_env.get_connection_async() as conn:
        with conn.cursor() as cursor:
            await cursor.execute("alter session set time_zone = '+00:00'")
        yield conn


@pytest.fixture
async def async_cursor(async_conn):
    """
    Return a connection to the database using the pytest configuration using
    asyncio.
    """
    with async_conn.cursor() as cursor:
        yield cursor


@pytest.fixture
def conn(test_env):
    """
    Return a connection to the database using the pytest configuration.
    """
    with test_env.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("alter session set time_zone = '+00:00'")
        yield conn


@pytest.fixture
def cursor(conn):
    """
    Return a connection to the database using the pytest configuration.
    """
    with conn.cursor() as cursor:
        yield cursor


@pytest.fixture
def disable_fetch_lobs():
    """
    Disables fetching of LOB locators for the duration of the test.
    """
    orig_value = oracledb.defaults.fetch_lobs
    oracledb.defaults.fetch_lobs = False
    yield
    oracledb.defaults.fetch_lobs = orig_value


def get_env_value(name, default_value=None, required=False):
    """
    Returns the value of the environment variable if it is present and the
    default value if it is not. If marked as required, the test suite will
    immediately fail.
    """
    env_name = f"PYO_TEST_{name}"
    value = os.environ.get(env_name)
    if value is None:
        if required:
            msg = f"missing value for environment variable {env_name}"
            pytest.exit(msg, 1)
        return default_value
    return value


@pytest.fixture
def parse_count_checker(conn, admin_conn, test_env):
    """
    Return an object used for checking the round trips on a connection.
    """
    if test_env.is_implicit_pooling:
        pytest.skip("sessions can change with implicit pooling")
    checker = ParseCountInfo()
    checker._initialize(conn, admin_conn)
    return checker


@pytest.fixture
async def parse_count_checker_async(async_conn, async_admin_conn, test_env):
    """
    Return an object used for checking the round trips on a connection.
    """
    if test_env.is_implicit_pooling:
        pytest.skip("sessions can change with implicit pooling")
    checker = ParseCountInfo()
    await checker._initialize_async(async_conn, async_admin_conn)
    return checker


def pytest_addoption(parser):
    """
    Adds python-oracledb testing options to the command line.
    """
    parser.addoption("--use-thick-mode", action="store_true")


@pytest.fixture
def round_trip_checker(conn, admin_conn, test_env):
    """
    Return an object used for checking the round trips on a connection.
    """
    if test_env.is_implicit_pooling:
        pytest.skip("sessions can change with implicit pooling")
    checker = RoundTripInfo()
    checker._initialize(conn, admin_conn)
    return checker


@pytest.fixture
async def round_trip_checker_async(async_conn, async_admin_conn, test_env):
    """
    Return an object used for checking the round trips on a connection.
    """
    if test_env.is_implicit_pooling:
        pytest.skip("sessions can change with implicit pooling")
    checker = RoundTripInfo()
    await checker._initialize_async(async_conn, async_admin_conn)
    return checker


@pytest.fixture
def skip_if_drcp(test_env):
    """
    Skips the test if running with DRCP.
    """
    test_env._initialize()
    if test_env.is_drcp:
        pytest.skip("not supported with DRCP")


@pytest.fixture
def skip_if_implicit_pooling(test_env):
    """
    Skips the test if running with implicit pooling.
    """
    test_env._initialize()
    if test_env.is_implicit_pooling:
        pytest.skip("not supported with implicit pooling")


@pytest.fixture
def skip_unless_binary_vectors_supported(test_env):
    """
    Skips the test if binary vectors are not supported.
    """
    if not test_env.has_client_and_server_version(23, 5):
        pytest.skip("no binary vector support")


@pytest.fixture
def skip_unless_call_timeout_supported(test_env):
    """
    Skips the test if not running in thin mode.
    """
    if not test_env.has_client_version(18):
        pytest.skip("no call timeout support")


@pytest.fixture
def skip_unless_domains_supported(test_env):
    """
    Skips the test if domains are not supported.
    """
    if not test_env.has_server_version(23):
        pytest.skip("no domain support")


@pytest.fixture
def skip_unless_json_supported(test_env):
    """
    Skips the test if JSON values are not supported.
    """
    if not test_env.has_client_and_server_version(12, 2):
        pytest.skip("no JSON support")


@pytest.fixture
def skip_unless_long_passwords_supported(test_env):
    """
    Skips the test if not running in thin mode.
    """
    if not test_env.has_client_and_server_version(23):
        pytest.skip("no long password support")


@pytest.fixture
def skip_unless_native_boolean_supported(test_env):
    """
    Skips the test if native booleans are not supported.
    """
    if not test_env.has_client_and_server_version(23):
        pytest.skip("no native boolean support")


@pytest.fixture
def skip_unless_native_json_supported(test_env):
    """
    Skips the test if native JSON data is not supported.
    """
    if not test_env.has_client_and_server_version(21):
        pytest.skip("no native JSON support")


@pytest.fixture
def skip_unless_plsql_boolean_supported(test_env):
    """
    Skips the test if PL/SQL booleans are not supported.
    """
    if not test_env.has_client_and_server_version(12, 1):
        pytest.skip("no PL/SQL boolean support")


@pytest.fixture
def skip_unless_pool_timed_wait_supported(test_env):
    """
    Skips the test if pooled timed wait is not supported.
    """
    if not test_env.has_client_and_server_version(12, 2):
        pytest.skip("no pool timed wait support")


@pytest.fixture
def skip_unless_sessionless_transactions_supported(test_env):
    """
    Skips the test if sessionless transactions are not supported.
    """
    if not test_env.has_client_and_server_version(23, 6):
        pytest.skip("no sessionless transactions support")


@pytest.fixture
def skip_unless_sparse_vectors_supported(test_env):
    """
    Skips the test if sparse vectors are not supported.
    """
    if not test_env.has_client_and_server_version(23, 7):
        pytest.skip("no sparse vector support")


@pytest.fixture
def skip_unless_thick_mode(test_env):
    """
    Skips the test if not running in thick mode.
    """
    if not test_env.use_thick_mode:
        pytest.skip("requires thick mode")


@pytest.fixture
def skip_unless_thin_mode(test_env):
    """
    Skips the test if not running in thin mode.
    """
    if test_env.use_thick_mode:
        pytest.skip("requires thin mode")


@pytest.fixture
def skip_unless_vectors_supported(test_env):
    """
    Skips the test if vectors are not supported.
    """
    if not test_env.has_client_and_server_version(23, 4):
        pytest.skip("no vector support")


@pytest.fixture
def soda_db(conn, test_env):
    """
    Return the SODA database object.
    """
    message = "not supported with this client/server combination"
    if not test_env.use_thick_mode:
        pytest.skip(message)
    if not test_env.has_client_version(18, 3):
        pytest.skip(message)
    if not test_env.has_server_version(18):
        pytest.skip(message)
    if test_env.has_server_version(20, 1):
        if not test_env.has_client_version(20, 1):
            pytest.skip(message)
    if test_env.has_client_version(23, 3) and platform.system() == "Darwin":
        pytest.skip(message)
    soda_db = conn.getSodaDatabase()
    for name in soda_db.getCollectionNames():
        soda_db.openCollection(name).drop()
    return soda_db


@pytest.fixture(scope="session")
def test_env(pytestconfig):
    """
    Returns an object containing a test environment which can be used to
    perform common checks.
    """
    env = TestEnv()
    env.use_thick_mode = pytestconfig.getoption("--use-thick-mode")
    env.main_user = get_env_value("MAIN_USER", default_value="pythontest")
    env.main_password = get_env_value("MAIN_PASSWORD", required=True)
    env.proxy_user = get_env_value(
        "PROXY_USER", default_value="pythontestproxy"
    )
    env.proxy_password = get_env_value("PROXY_PASSWORD")
    env.connect_string = get_env_value(
        "CONNECT_STRING", default_value="localhost/orclpdb1"
    )
    env.admin_user = get_env_value("ADMIN_USER", default_value="admin")
    env.admin_password = get_env_value("ADMIN_PASSWORD")
    if env.use_thick_mode:
        env.wallet_location = env.wallet_password = None
    else:
        env.wallet_location = get_env_value("WALLET_LOCATION")
        env.wallet_password = get_env_value("WALLET_PASSWORD")
    env.external_user = get_env_value("EXTERNAL_USER")
    env.edition_name = get_env_value(
        "EDITION_NAME", default_value="pythonedition"
    )
    env.plugins = get_env_value("PLUGINS")
    env.oracle_client_path = (
        get_env_value("ORACLE_CLIENT_PATH")
        if platform.system() in ("Darwin", "Windows")
        else None
    )
    env.initialized = False
    return env
