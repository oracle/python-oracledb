# -----------------------------------------------------------------------------
# Copyright (c) 2024, Oracle and/or its affiliates.
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
E1300 - Module for testing the 11g and 12c verifier types. No special
configuration is needed but a user is created and dropped.
"""

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    requires_connection = False
    user = "ext_test_1300_user"

    @classmethod
    def setUpClass(cls):
        cls.admin_conn = test_env.get_admin_connection()
        cls.password = test_env.get_random_string()
        with cls.admin_conn.cursor() as cursor:
            cursor.execute(
                "select count(*) from user$ where name = :1",
                [cls.user.upper()],
            )
            (count,) = cursor.fetchone()
            keyword = "create" if count == 0 else "alter"
            cursor.execute(
                f"{keyword} user {cls.user} identified by {cls.password}"
            )
            cursor.execute(
                "select spare4 from user$ where name = :1", [cls.user.upper()]
            )
            (password_data,) = cursor.fetchone()
            cls.verifier_11g, cls.verifier_12c = password_data.split(";")
            cursor.execute(f"drop user {cls.user}")

    @classmethod
    def tearDownClass(cls):
        user = test_env.get_main_user()
        password = test_env.get_main_password()
        with cls.admin_conn.cursor() as cursor:
            cursor.execute(f"alter user {user} identified by {password}")

    def _verify_connection(self, verifier):
        """
        Verify the ability to connect to the database using the given verifier.
        """
        user = test_env.get_main_user()
        sql = f"alter user {user} identified by values '{verifier}'"
        with self.admin_conn.cursor() as cursor:
            cursor.execute(sql)
        conn = oracledb.connect(
            user=user,
            password=self.password,
            dsn=test_env.get_connect_string(),
        )
        with conn.cursor() as cursor:
            cursor.execute("select user from dual")
            (fetched_user,) = cursor.fetchone()
            self.assertEqual(fetched_user, user.upper())

    def test_ext_1300(self):
        "E1300 - test with an 11g verifier"
        self._verify_connection(self.verifier_11g)

    def test_ext_1301(self):
        "E1301 - test with a 12c verifier"
        self._verify_connection(self.verifier_12c)


if __name__ == "__main__":
    test_env.run_test_cases()
