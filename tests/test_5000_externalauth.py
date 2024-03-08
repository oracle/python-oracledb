# -----------------------------------------------------------------------------
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
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
5000 - Module for testing external authentication
"""

import unittest

import oracledb
import test_env


@unittest.skipIf(
    not test_env.get_external_user(),
    "external authentication not supported with this setup",
)
class TestCase(test_env.BaseTestCase):
    require_connection = False

    def __verify_connection(
        self, connection, expected_user, expected_proxy_user=None
    ):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select
                    sys_context('userenv', 'session_user'),
                    sys_context('userenv', 'proxy_user')
                from dual
                """
            )
            actual_user, actual_proxy_user = cursor.fetchone()
            self.assertEqual(actual_user, expected_user.upper())
            self.assertEqual(
                actual_proxy_user,
                expected_proxy_user and expected_proxy_user.upper(),
            )

    def test_5000(self):
        """
        5000 - test error on creating a pool with user and password specified
        and externalauth enabled
        """
        with self.assertRaisesFullCode("DPI-1032"):
            test_env.get_pool(
                min=1,
                max=2,
                increment=1,
                getmode=oracledb.POOL_GETMODE_WAIT,
                externalauth=True,
                homogeneous=False,
            )

    def test_5001(self):
        """
        5001 - test error on creating a pool without password and with user
        specified and externalauth enabled
        """
        with self.assertRaisesFullCode("DPI-1032"):
            oracledb.create_pool(
                user=test_env.get_main_user(),
                min=1,
                max=2,
                increment=1,
                getmode=oracledb.POOL_GETMODE_WAIT,
                externalauth=True,
                homogeneous=False,
            )

    def test_5002(self):
        """
        5002 - test error on creating a pool without user and with password
        specified and externalauth enabled
        """
        with self.assertRaisesFullCode("DPI-1032"):
            oracledb.create_pool(
                password=test_env.get_main_password(),
                min=1,
                max=2,
                increment=1,
                getmode=oracledb.POOL_GETMODE_WAIT,
                externalauth=True,
                homogeneous=False,
            )

    def test_5003(self):
        """
        5003 - test creating a pool with user and password specified and
        externalauth set to False
        """
        pool = test_env.get_pool(
            min=1,
            max=2,
            increment=1,
            getmode=oracledb.POOL_GETMODE_WAIT,
            externalauth=False,
            homogeneous=False,
        )
        with pool.acquire() as conn:
            self.__verify_connection(conn, test_env.get_main_user())

    def test_5004(self):
        """
        5004 - test error when connecting with user and password specified
        and externalauth enabled
        """
        with self.assertRaisesFullCode("DPI-1032"):
            oracledb.connect(
                user=test_env.get_main_user(),
                password=test_env.get_main_password(),
                dsn=test_env.get_connect_string(),
                externalauth=True,
            )

    def test_5005(self):
        """
        5005 - test error when connecting without username and with password
        specified and externalauth enabled
        """
        with self.assertRaisesFullCode("DPI-1032"):
            oracledb.connect(
                password=test_env.get_main_password(),
                dsn=test_env.get_connect_string(),
                externalauth=True,
            )

        # by default externalauth is False
        with self.assertRaisesFullCode("ORA-01017"):
            oracledb.connect(
                password=test_env.get_main_password(),
                dsn=test_env.get_connect_string(),
            )

    def test_5006(self):
        """
        5006 - test error when connecting without password and with user
        specified and externalauth enabled
        """
        with self.assertRaisesFullCode("ORA-01017"):
            oracledb.connect(
                user="[invalid_user]",
                dsn=test_env.get_connect_string(),
                externalauth=True,
            )

        # by default externalauth is False
        with self.assertRaisesFullCode("ORA-01017"):
            oracledb.connect(
                user="[invalid_user]", dsn=test_env.get_connect_string()
            )

    def test_5007(self):
        "5007 - test external authentication with invalid proxy user"
        with self.assertRaisesFullCode("DPI-1069"):
            oracledb.connect(
                user=test_env.get_main_user(),
                dsn=test_env.get_connect_string(),
                externalauth=True,
            )

        # by default externalauth is False
        with self.assertRaisesFullCode("DPY-4001"):
            oracledb.connect(
                user=test_env.get_main_user(),
                dsn=test_env.get_connect_string(),
            )

    def test_5008(self):
        """
        5008 - test creating a connection with user and password specified and
        externalauth set to False
        """
        conn = oracledb.connect(
            user=test_env.get_main_user(),
            password=test_env.get_main_password(),
            dsn=test_env.get_connect_string(),
            externalauth=False,
        )
        self.__verify_connection(conn, test_env.get_main_user())

    def test_5009(self):
        """
        5009 - test creating standalone connection with externalauth set to
        True explicitly
        """
        conn = oracledb.connect(
            dsn=test_env.get_connect_string(), externalauth=True
        )
        self.__verify_connection(conn, test_env.get_external_user())

    def test_5010(self):
        """
        5010 - test creating standalone connection with no user and password
        specified and externalauth not set
        """
        conn = oracledb.connect(dsn=test_env.get_connect_string())
        self.__verify_connection(conn, test_env.get_external_user())

    def test_5011(self):
        "5011 - test creating a pool with external authentication"
        pool = oracledb.create_pool(
            dsn=test_env.get_connect_string(),
            min=1,
            max=2,
            increment=1,
            getmode=oracledb.POOL_GETMODE_WAIT,
            externalauth=True,
            homogeneous=False,
        )
        self.assertEqual(pool.opened, 0)
        with pool.acquire() as conn:
            self.__verify_connection(conn, test_env.get_external_user())

    def test_5012(
        self,
    ):
        """
        5012 - test creating a pool without user and password specified and
        externalauth not set
        """
        pool = oracledb.create_pool(
            dsn=test_env.get_connect_string(),
            min=1,
            max=2,
            increment=1,
            getmode=oracledb.POOL_GETMODE_WAIT,
            homogeneous=False,
        )
        with self.assertRaisesFullCode("ORA-24415"):
            pool.acquire()

    def test_5013(self):
        "5013 - test pool min is always 0 under external authentication"
        pool = oracledb.create_pool(
            dsn=test_env.get_connect_string(),
            min=5,
            max=10,
            increment=3,
            getmode=oracledb.POOL_GETMODE_WAIT,
            externalauth=True,
            homogeneous=False,
        )
        self.assertEqual(pool.opened, 0)

    def test_5014(self):
        "5014 - test pool increment is always 1 under external authentication"
        pool = oracledb.create_pool(
            dsn=test_env.get_connect_string(),
            min=5,
            max=10,
            increment=3,
            getmode=oracledb.POOL_GETMODE_WAIT,
            externalauth=True,
            homogeneous=False,
        )
        conn1 = pool.acquire()
        self.assertEqual(pool.opened, 1)
        conn2 = pool.acquire()
        self.assertEqual(pool.opened, 2)
        conn1.close()
        conn2.close()

    def test_5015(self):
        "5015 - test external authentication with proxy"
        proxy_user = test_env.get_external_user()  # proxy user
        schema_user = test_env.get_main_user()  # schema user
        conn1 = oracledb.connect(
            user=f"[{schema_user}]",
            dsn=test_env.get_connect_string(),
            externalauth=True,
        )
        self.__verify_connection(conn1, schema_user, proxy_user)
        conn2 = oracledb.connect(
            user=f"[{schema_user}]", dsn=test_env.get_connect_string()
        )
        self.__verify_connection(conn2, schema_user, proxy_user)

    def test_5016(self):
        "5016 - test creating pool using external authentication with proxy"
        proxy_user = test_env.get_external_user()
        schema_user = test_env.get_main_user()
        pool = oracledb.create_pool(
            externalauth=True,
            homogeneous=False,
            dsn=test_env.get_connect_string(),
            min=1,
            max=2,
            increment=1,
            getmode=oracledb.POOL_GETMODE_WAIT,
        )
        self.assertEqual(pool.opened, 0)
        conn = pool.acquire(user=f"[{schema_user}]")
        self.__verify_connection(conn, schema_user, proxy_user)


if __name__ == "__main__":
    test_env.run_test_cases()
