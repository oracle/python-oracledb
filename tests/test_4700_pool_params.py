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
4700 - Module for testing pool parameters.
"""

import oracledb
import test_env

class TestCase(test_env.BaseTestCase):
    requires_connection = False

    def __test_writable_parameter(self, name, value):
        """
        Tests that a writable parameter can be written to and the modified
        value read back successfully.
        """
        params = oracledb.PoolParams()
        orig_value = getattr(params, name)
        copied_params = params.copy()
        args = {}
        args[name] = value
        params.set(**args)
        self.assertEqual(getattr(params, name), value)
        self.assertEqual(getattr(copied_params, name), orig_value)

    def test_4700_writable_params(self):
        "4700 - test writable parameters"
        self.__test_writable_parameter("min", 8)
        self.__test_writable_parameter("max", 12)
        self.__test_writable_parameter("increment", 2)
        self.__test_writable_parameter("connectiontype", oracledb.Connection)
        self.__test_writable_parameter("getmode", oracledb.POOL_GETMODE_NOWAIT)
        self.__test_writable_parameter("homogeneous", False)
        self.__test_writable_parameter("externalauth", True)
        self.__test_writable_parameter("timeout", 25)
        self.__test_writable_parameter("wait_timeout", 45)
        self.__test_writable_parameter("max_lifetime_session", 65)
        self.__test_writable_parameter("session_callback", lambda c: None)
        self.__test_writable_parameter("max_sessions_per_shard", 5)
        self.__test_writable_parameter("soda_metadata_cache", True)
        self.__test_writable_parameter("ping_interval", 20)

if __name__ == "__main__":
    test_env.run_test_cases()
