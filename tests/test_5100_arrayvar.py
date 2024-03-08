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
5100 - Module for testing array variables.
"""

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    def test_5100(self):
        "5100 - checking the attributes of an array variable"
        var = self.cursor.arrayvar(oracledb.DB_TYPE_NUMBER, 1000)
        self.assertEqual(var.size, 0)
        self.assertEqual(var.values, [])
        self.assertEqual(var.num_elements, 1000)
        self.assertEqual(var.actual_elements, 0)

        var = self.cursor.arrayvar(oracledb.DB_TYPE_NUMBER, [1, 2])
        self.assertEqual(var.values, [1, 2])
        self.assertEqual(var.num_elements, 2)
        self.assertEqual(var.actual_elements, 2)

    def test_5101(self):
        "5101 - setting values in an array variable"
        var = self.cursor.arrayvar(oracledb.DB_TYPE_VARCHAR, 10, 2000)
        self.assertEqual(var.values, [])
        self.assertEqual(var.actual_elements, 0)
        data = [str(i) for i in range(5)]
        var.setvalue(0, data)
        self.assertEqual(var.values, data)
        self.assertEqual(var.actual_elements, len(data))

    def test_5102(self):
        "5102 - checking the default size of VARCHAR and RAW types"
        types = [oracledb.DB_TYPE_VARCHAR, oracledb.DB_TYPE_RAW]
        for typ in types:
            var = self.cursor.arrayvar(typ, ["ab"])
            self.assertEqual(var.size, 4000)

    def test_5103(self):
        "5103 - creating array variables with invalid parameters"
        self.assertRaises(
            TypeError, self.cursor.arrayvar, oracledb.DB_TYPE_NUMBER, "10", 40
        )
        self.assertRaises(
            TypeError, self.cursor.arrayvar, oracledb.DB_TYPE_NUMBER, 10, "40"
        )
        self.assertRaises(
            TypeError, self.cursor.arrayvar, oracledb.DB_TYPE_NUMBER, 10, []
        )

    def test_5104(self):
        "5104 - declaring an array variable with an incorrect Python type"
        with self.assertRaisesFullCode("DPY-3013"):
            self.cursor.arrayvar(oracledb.DB_TYPE_NUMBER, [3, "ab"])

    def test_5105(self):
        "5105 - adding more elements than declared to an array variable"
        var = self.cursor.arrayvar(oracledb.DB_TYPE_NUMBER, 4)
        with self.assertRaisesFullCode("DPY-2016"):
            var.setvalue(0, [i for i in range(5)])

    def test_5106(self):
        "5106 - creating an invalid array of arrays"
        var = self.cursor.arrayvar(oracledb.DB_TYPE_NUMBER, 4)
        with self.assertRaisesFullCode("DPY-3005"):
            var.setvalue(1, [1, 2])


if __name__ == "__main__":
    test_env.run_test_cases()
