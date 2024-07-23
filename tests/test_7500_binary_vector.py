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
7500 - Module for testing the VECTOR database type with storage format BINARY
available in Oracle Database 23.5 and higher.
"""

import array
import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_client_version() >= (23, 5), "unsupported client"
)
@unittest.skipUnless(
    test_env.get_server_version() >= (23, 5), "unsupported server"
)
class TestCase(test_env.BaseTestCase):

    def test_7500(self):
        "7500 - test binding and fetching a BINARY format vector."
        value = array.array("B", [4, 8, 12, 4, 98, 127, 25, 78])
        self.cursor.execute("delete from TestBinaryVectors")
        self.cursor.execute(
            """
            insert into TestBinaryVectors (IntCol, VectorBinaryCol)
            values(1, :value)
            """,
            value=value,
        )
        self.conn.commit()
        self.cursor.execute("select VectorBinaryCol from TestBinaryVectors")
        (fetched_value,) = self.cursor.fetchone()
        self.assertIsInstance(fetched_value, array.array)
        self.assertEqual(fetched_value.typecode, "B")
        self.assertEqual(fetched_value, value)

    def test_7501(self):
        "7501 - verify fetch info contents"
        attr_names = [
            "name",
            "type_code",
            "vector_dimensions",
            "vector_format",
        ]
        expected_values = [
            ["INTCOL", oracledb.DB_TYPE_NUMBER, None, None],
            [
                "VECTORBINARYCOL",
                oracledb.DB_TYPE_VECTOR,
                64,
                oracledb.VECTOR_FORMAT_BINARY,
            ],
        ]
        self.cursor.execute("select * from TestBinaryVectors")
        values = [
            [getattr(i, n) for n in attr_names]
            for i in self.cursor.description
        ]
        self.assertEqual(values, expected_values)
        self.assertIs(
            self.cursor.description[1].vector_format,
            oracledb.VectorFormat.BINARY,
        )

    def test_7502(self):
        "7502 - test comparing BINARY vectors"
        value = array.array("B", [20, 9, 15, 34, 108, 125, 35, 88])
        self.cursor.execute("delete from TestBinaryVectors")
        self.cursor.execute(
            """
            insert into TestBinaryVectors (IntCol, VectorBinaryCol)
            values(1, :value)
            """,
            value=value,
        )
        self.conn.commit()
        self.cursor.execute(
            """
            select vector_distance(VectorBinaryCol, :value)
            from TestBinaryVectors
            """,
            value=value,
        )
        (result,) = self.cursor.fetchone()
        self.assertAlmostEqual(result, 0)


if __name__ == "__main__":
    test_env.run_test_cases()
