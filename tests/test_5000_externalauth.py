#------------------------------------------------------------------------------
# Copyright (c) 2022, Oracle and/or its affiliates.
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
5000 - Module for testing external authentication
"""

import unittest

import oracledb
import test_env

@unittest.skipIf(not test_env.get_external_user(),
                 "external authentication not supported with this setup")
class TestCase(test_env.BaseTestCase):
    require_connection = False

    def __verify_connection(self, connection, expected_user,
                            expected_proxy_user=None):
        with connection.cursor() as cursor:
            cursor.execute("""
                    select
                        sys_context('userenv', 'session_user'),
                        sys_context('userenv', 'proxy_user')
                    from dual""")
            actual_user, actual_proxy_user = cursor.fetchone()
            self.assertEqual(actual_user, expected_user.upper())
            self.assertEqual(actual_proxy_user,
                             expected_proxy_user and expected_proxy_user.upper())

    def test_5000_pool_with_user_and_password_and_externalauth_enabled(self):
        """
        5000 - test error on creating a pool with user and password specified
        and externalauth enabled
        """
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPI-1032:",
                               test_env.get_pool, min=1, max=2, increment=1,
                               getmode=oracledb.POOL_GETMODE_WAIT,
                               externalauth=True, homogeneous=False)

    def test_5001_pool_with_no_password_and_externalauth_enabled(self):
        """
        5001 - test error on creating a pool without password and with user
        specified and externalauth enabled
        """
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPI-1032:",
                               oracledb.create_pool,
                               user=test_env.get_main_user(),
                               min=1, max=2, increment=1,
                               getmode=oracledb.POOL_GETMODE_WAIT,
                               externalauth=True, homogeneous=False)

    def test_5002_pool_with_no_user_and_externalauth_enabled(self):
        """
        5002 - test error on creating a pool without user and with password
        specified and externalauth enabled
        """
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPI-1032:",
                               oracledb.create_pool,
                               password=test_env.get_main_password(),
                               min=1, max=2, increment=1,
                               getmode=oracledb.POOL_GETMODE_WAIT,
                               externalauth=True, homogeneous=False)

    def test_5003_pool_with_user_and_password_and_externalauth_off(self):
        """
        5003 - test creating a pool with user and password specified and
        externalauth set to False
        """
        pool = test_env.get_pool(min=1, max=2, increment=1,
                                 getmode=oracledb.POOL_GETMODE_WAIT,
                                 externalauth=False, homogeneous=False)
        with pool.acquire() as connection:
            self.__verify_connection(connection, test_env.get_main_user())

    def test_5004_user_and_password_with_externalauth_enabled(self):
        """
        5004 - test error when connecting with user and password specified
        and externalauth enabled
        """
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPI-1032:",
                               oracledb.connect, user=test_env.get_main_user(),
                               password=test_env.get_main_password(),
                               dsn=test_env.get_connect_string(),
                               externalauth=True)

    def test_5005_no_user_with_externalauth_enabled(self):
        """
        5005 - test error when connecting without username and with password
        specified and externalauth enabled
        """
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPI-1032:",
                               oracledb.connect,
                               password=test_env.get_main_password(),
                               dsn=test_env.get_connect_string(),
                               externalauth=True)

        # by default externalauth is False
        self.assertRaisesRegex(oracledb.DatabaseError, "^ORA-01017:",
                               oracledb.connect,
                               password=test_env.get_main_password(),
                               dsn=test_env.get_connect_string())

    def test_5006_user_with_no_password_and_externalauth_enabled(self):
        """
        5006 - test error when connecting without password and with user
        specified and externalauth enabled
        """
        self.assertRaisesRegex(oracledb.DatabaseError, "^ORA-01017:",
                               oracledb.connect, user="[invalid_user]",
                               dsn=test_env.get_connect_string(),
                               externalauth=True)

        # by default externalauth is False
        self.assertRaisesRegex(oracledb.DatabaseError, "^ORA-01017:",
                               oracledb.connect, user="[invalid_user]",
                               dsn=test_env.get_connect_string())

    def test_5007_external_authentication_with_invalid_proxy_user(self):
        "5007 - test external authentication with invalid proxy user"
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPI-1069:",
                               oracledb.connect, user=test_env.get_main_user(),
                               dsn=test_env.get_connect_string(),
                               externalauth=True)

        # by default externalauth is False
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-4001:",
                               oracledb.connect, user=test_env.get_main_user(),
                               dsn=test_env.get_connect_string())

    def test_5008_user_and_password_with_externalauth_off(self):
        """
        5008 - test creating a connection with user and password specified and
        externalauth set to False
        """
        connection = oracledb.connect(user=test_env.get_main_user(),
                                      password=test_env.get_main_password(),
                                      dsn=test_env.get_connect_string(),
                                      externalauth=False)
        self.__verify_connection(connection, test_env.get_main_user())

    def test_5009_external_authentication_with_externalauth_enabled(self):
        """
        5009 - test creating standalone connection with externalauth set to
        True explicitly
        """
        connection = oracledb.connect(dsn=test_env.get_connect_string(),
                                      externalauth=True)
        self.__verify_connection(connection, test_env.get_external_user())

    def test_5010_external_authentication_with_externalauth_not_set(self):
        """
        5010 - test creating standalone connection with no user and password
        specified and externalauth not set
        """
        connection = oracledb.connect(dsn=test_env.get_connect_string())
        self.__verify_connection(connection, test_env.get_external_user())

    def test_5011_pool_with_external_authentication(self):
        "5011 - test creating a pool with external authentication"
        pool = oracledb.create_pool(dsn=test_env.get_connect_string(),
                                    min=1, max=2, increment=1,
                                    getmode=oracledb.POOL_GETMODE_WAIT,
                                    externalauth=True, homogeneous=False)
        self.assertEqual(pool.opened, 0)
        with pool.acquire() as connection:
            self.__verify_connection(connection, test_env.get_external_user())

    def test_5012_pool_with_no_user_and_password_and_externalauth_not_set(self):
        """
        5012 - test creating a pool without user and password specified and
        externalauth not set
        """
        pool = oracledb.create_pool(dsn=test_env.get_connect_string(),
                                    min=1, max=2, increment=1,
                                    getmode=oracledb.POOL_GETMODE_WAIT,
                                    homogeneous=False)
        self.assertRaisesRegex(oracledb.DatabaseError, "^ORA-24415:",
                               pool.acquire)

    def test_5013_pool_min_with_no_effect_under_external_authentication(self):
        "5013 - test pool min is always 0 under external authentication"
        pool = oracledb.create_pool(dsn=test_env.get_connect_string(),
                                    min=5, max=10, increment=3,
                                    getmode=oracledb.POOL_GETMODE_WAIT,
                                    externalauth=True, homogeneous=False)
        self.assertEqual(pool.opened, 0)

    def test_5014_pool_increment_with_no_effect_under_external_auth(self):
        "5014 - test pool increment is always 1 under external authentication"
        pool = oracledb.create_pool(dsn=test_env.get_connect_string(),
                                    min=5, max=10, increment=3,
                                    getmode=oracledb.POOL_GETMODE_WAIT,
                                    externalauth=True, homogeneous=False)
        conn1 = pool.acquire()
        self.assertEqual(pool.opened, 1)
        conn2 = pool.acquire()
        self.assertEqual(pool.opened, 2)

    def test_5015_external_authentication_with_proxy(self):
        "5015 - test external authentication with proxy"
        proxy_user = test_env.get_external_user() # proxy user
        schema_user = test_env.get_main_user()    # schema user
        conn1 = oracledb.connect(user=f"[{schema_user}]",
                                 dsn=test_env.get_connect_string(),
                                 externalauth=True)
        self.__verify_connection(conn1, schema_user, proxy_user)
        conn2 = oracledb.connect(user=f"[{schema_user}]",
                                 dsn=test_env.get_connect_string())
        self.__verify_connection(conn2, schema_user, proxy_user)

    def test_5016_pool_external_authentication_with_proxy(self):
        "5016 - test creating pool using external authentication with proxy"
        proxy_user = test_env.get_external_user()
        schema_user = test_env.get_main_user()
        pool = oracledb.create_pool(externalauth=True, homogeneous=False,
                                    dsn=test_env.get_connect_string(),
                                    min=1, max=2, increment=1,
                                    getmode=oracledb.POOL_GETMODE_WAIT)
        self.assertEqual(pool.opened, 0)
        connection = pool.acquire(user=f"[{schema_user}]")
        self.__verify_connection(connection, schema_user, proxy_user)

if __name__ == "__main__":
    test_env.run_test_cases()
