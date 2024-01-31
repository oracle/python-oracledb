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
6900 - Module for testing OSON encoding and decoding.
"""

import unittest

import test_env


@unittest.skipUnless(
    test_env.get_client_version() >= (21, 0), "unsupported client"
)
@unittest.skipUnless(
    test_env.get_server_version() >= (21, 0), "unsupported server"
)
class TestCase(test_env.BaseTestCase):
    def test_6900(self):
        "6900 - test OSON metadata"
        self.cursor.execute("select * from TestOsonCols")
        int_col_metadata, oson_col_metadata = self.cursor.description
        self.assertFalse(int_col_metadata.is_oson)
        self.assertTrue(oson_col_metadata.is_oson)


if __name__ == "__main__":
    test_env.run_test_cases()
