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

@unittest.skipIf(test_env.get_is_thin(),
                 "thin mode doesn't support external authentication yet")
class TestCase(test_env.BaseTestCase):
    require_connection = False

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

if __name__ == "__main__":
    test_env.run_test_cases()
