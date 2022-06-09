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

#------------------------------------------------------------------------------
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
#------------------------------------------------------------------------------

import getpass
import os
import sys
import unittest

import oracledb

# default values
DEFAULT_MAIN_USER = "pythontest"
DEFAULT_PROXY_USER = "pythontestproxy"
DEFAULT_CONNECT_STRING = "localhost/orclpdb1"

# dictionary containing all parameters; these are acquired as needed by the
# methods below (which should be used instead of consulting this dictionary
# directly) and then stored so that a value is not requested more than once
PARAMETERS = {}

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

def get_admin_connection():
    admin_user = get_value("ADMIN_USER", "Administrative user", "admin")
    admin_password = get_value("ADMIN_PASSWORD", f"Password for {admin_user}",
                               password=True)
    return oracledb.connect(dsn=get_connect_string(),
                            params=get_connect_params(),
                            user=admin_user, password=admin_password)

def get_charset_ratios():
    value = PARAMETERS.get("CS_RATIO")
    if value is None:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
                select
                    cast('X' as varchar2(1)),
                    cast('Y' as nvarchar2(1))
                from dual""")
        varchar_column_info, nvarchar_column_info = cursor.description
        value = (varchar_column_info[3], nvarchar_column_info[3])
        PARAMETERS["CS_RATIO"] = value
    return value

def get_client_version():
    name = "CLIENT_VERSION"
    value = PARAMETERS.get(name)
    if value is None:
        if get_is_thin():
            value = (21, 3)
        else:
            value = oracledb.clientversion()[:2]
        PARAMETERS[name] = value
    return value

def get_connect_params():
    name = "CONNECT_PARAMS"
    params = PARAMETERS.get(name)
    if params is None:
        wallet_location = get_wallet_location()
        params = oracledb.ConnectParams(user=get_main_user(),
                                        password=get_main_password(),
                                        config_dir=wallet_location,
                                        wallet_location=wallet_location,
                                        wallet_password=get_wallet_password())
        PARAMETERS[name] = params
    return params

def get_connection(dsn=None, **kwargs):
    if dsn is None:
        dsn = get_connect_string()
    return oracledb.connect(dsn=dsn, params=get_connect_params(), **kwargs)

def get_connect_string():
    return get_value("CONNECT_STRING", "Connect String",
                     DEFAULT_CONNECT_STRING)

def get_is_thin():
    driver_mode = get_value("DRIVER_MODE", "Driver mode (thin|thick)", "thin")
    return driver_mode == "thin"

def get_main_password():
    return get_value("MAIN_PASSWORD", f"Password for {get_main_user()}",
                     password=True)

def get_main_user():
    return get_value("MAIN_USER", "Main User Name", DEFAULT_MAIN_USER)

def get_pool(**kwargs):
    return oracledb.create_pool(dsn=get_connect_string(),
                                params=get_pool_params(), **kwargs)

def get_pool_params():
    name = "POOL_PARAMS"
    params = PARAMETERS.get(name)
    if params is None:
        wallet_location = get_wallet_location()
        params = oracledb.PoolParams(user=get_main_user(),
                                     password=get_main_password(),
                                     config_dir=wallet_location,
                                     wallet_location=wallet_location,
                                     wallet_password=get_wallet_password())
        PARAMETERS[name] = params
    return params

def get_proxy_password():
    return get_value("PROXY_PASSWORD", f"Password for {get_proxy_user()}",
                     password=True)

def get_proxy_user():
    return get_value("PROXY_USER", "Proxy User Name", DEFAULT_PROXY_USER)

def get_sleep_proc_name():
    server_version = get_server_version()
    return "dbms_session.sleep" if server_version[0] >= 18 \
            else "dbms_lock.sleep"

def get_server_version():
    name = "SERVER_VERSION"
    value = PARAMETERS.get(name)
    if value is None:
        conn = get_connection()
        value = tuple(int(s) for s in conn.version.split("."))[:2]
        PARAMETERS[name] = value
    return value

def get_wallet_location():
    if get_is_thin():
        return get_value("WALLET_LOCATION", "Wallet Location")

def get_wallet_password():
    if get_is_thin():
        return get_value("WALLET_PASSWORD", "Wallet Password", password=True)

def run_sql_script(conn, script_name, **kwargs):
    statement_parts = []
    cursor = conn.cursor()
    replace_values = [("&" + k + ".", v) for k, v in kwargs.items()] + \
                     [("&" + k, v) for k, v in kwargs.items()]
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
    cursor.execute("""
            select name, type, line, position, text
            from dba_errors
            where owner = upper(:owner)
            order by name, type, line, position""",
            owner = get_main_user())
    prev_name = prev_obj_type = None
    for name, obj_type, line_num, position, text in cursor:
        if name != prev_name or obj_type != prev_obj_type:
            print("%s (%s)" % (name, obj_type))
            prev_name = name
            prev_obj_type = obj_type
        print("    %s/%s %s" % (line_num, position, text))

def run_test_cases():
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


class FetchLobsContextManager:

    def __init__(self, desired_value):
        self.desired_value = desired_value

    def __enter__(self):
        self.original_value = oracledb.defaults.fetch_lobs
        oracledb.defaults.fetch_lobs = self.desired_value
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        oracledb.defaults.fetch_lobs = self.original_value


class SystemStatInfo:
    stat_name = None

    def __init__(self, connection):
        self.prev_value = 0
        self.admin_conn = get_admin_connection()
        with connection.cursor() as cursor:
            cursor.execute("select sys_context('userenv', 'sid') from dual")
            self.sid, = cursor.fetchone()
        self.get_value()

    def get_value(self):
        with self.admin_conn.cursor() as cursor:
            cursor.execute("""
                    select ss.value
                    from v$sesstat ss, v$statname sn
                    where ss.sid = :sid
                        and ss.statistic# = sn.statistic#
                        and sn.name = :stat_name""",
                    sid=self.sid, stat_name=self.stat_name)
            current_value, = cursor.fetchone()
            diff_value = current_value - self.prev_value
            self.prev_value = current_value
            return diff_value


class RoundTripInfo(SystemStatInfo):
    stat_name = "SQL*Net roundtrips to/from client"


class ParseCountInfo(SystemStatInfo):
    stat_name = "parse count (total)"


class BaseTestCase(unittest.TestCase):
    requires_connection = True

    def assertParseCount(self, n):
        self.assertEqual(self.parse_count_info.get_value(), n)

    def assertRoundTrips(self, n):
        self.assertEqual(self.round_trip_info.get_value(), n)

    def get_db_object_as_plain_object(self, obj):
        if obj.type.iscollection:
            element_values = []
            for value in obj.aslist():
                if isinstance(value, oracledb.Object):
                    value = self.get_db_object_as_plain_object(value)
                elif isinstance(value, oracledb.LOB):
                    value = value.read()
                element_values.append(value)
            return element_values
        attr_values = []
        for attribute in obj.type.attributes:
            value = getattr(obj, attribute.name)
            if isinstance(value, oracledb.Object):
                value = self.get_db_object_as_plain_object(value)
            elif isinstance(value, oracledb.LOB):
                value = value.read()
            attr_values.append(value)
        return tuple(attr_values)

    def get_soda_database(self, minclient=(18, 3), minserver=(18, 0),
                          message="not supported with this client/server " \
                                  "combination"):
        client = get_client_version()
        if client < minclient:
            self.skipTest(message)
        server = get_server_version()
        if server < minserver:
            self.skipTest(message)
        if server > (20, 1) and client < (20, 1):
            self.skipTest(message)
        return self.connection.getSodaDatabase()

    def is_on_oracle_cloud(self, connection=None):
        server = get_server_version()
        if server < (18, 0):
            return False
        if connection is None:
            connection = self.connection
        cursor = connection.cursor()
        cursor.execute("""
                select sys_context('userenv', 'cloud_service')
                from dual""")
        service_name, = cursor.fetchone()
        return service_name is not None

    def setUp(self):
        if self.requires_connection:
            self.connection = get_connection()
            self.cursor = self.connection.cursor()

    def setup_parse_count_checker(self):
        self.parse_count_info = ParseCountInfo(self.connection)

    def setup_round_trip_checker(self):
        self.round_trip_info = RoundTripInfo(self.connection)

    def tearDown(self):
        if self.requires_connection:
            self.connection.close()
            del self.cursor
            del self.connection

# ensure that thick mode is enabled, if desired
if not get_is_thin():
    oracledb.init_oracle_client()
