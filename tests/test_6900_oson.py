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

import oracledb
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

    def test_6901(self):
        "6901 - test simple query of OSON encoded bytes"
        self.cursor.execute("delete from TestOsonCols")
        self.cursor.execute(
            """
                insert into TestOsonCols (IntCol, OsonCol)
                values (1, '{"id": 6901, "value" : "string 6901"}')"""
        )
        self.conn.commit()
        self.cursor.execute("select OsonCol from TestOsonCols")
        (oson_val,) = self.cursor.fetchone()
        expected_val = dict(id=6901, value="string 6901")
        self.assertEqual(oson_val, expected_val)

    def test_6902(self):
        "6902 - test round trip of OSON encoded bytes"
        value = dict(id=6902, value="string 6902")
        self.cursor.execute("delete from TestOsonCols")
        encoded_oson = self.conn.encode_oson(value)
        self.cursor.execute(
            "insert into TestOsonCols values (1, :data)", [encoded_oson]
        )
        self.conn.commit()
        self.cursor.execute("select OsonCol from TestOsonCols")
        (oson_val,) = self.cursor.fetchone()
        self.assertEqual(oson_val, value)

    def test_6903(self):
        "6903 - test encoding and decoding a value"
        value = dict(id=6903, value="string 6903")
        out_value = self.conn.decode_oson(self.conn.encode_oson(value))
        self.assertEqual(out_value, value)

    def test_6904(self):
        "6904 - test decoding a non encoded value"
        value = b"{'not a previous encoded value': 3}"
        with self.assertRaisesFullCode("DPY-5004"):
            self.conn.decode_oson(value)

    def test_6905(self):
        "6905 - test inserting oson inside a lob"
        value = dict(id=6905, value="string 6905")
        self.cursor.execute("delete from TestOsonCols")
        encoded_oson = self.conn.encode_oson(value)
        lob = self.conn.createlob(oracledb.DB_TYPE_BLOB, encoded_oson)
        self.cursor.execute(
            "insert into TestOsonCols values (1, :data)", [lob]
        )
        self.conn.commit()
        self.cursor.execute("select OsonCol from TestOsonCols")
        (oson_val,) = self.cursor.fetchone()
        self.assertEqual(oson_val, value)

    def test_6906(self):
        "6906 - test inserting oson as json"
        self.cursor.execute("delete from TestOsonCols")
        value = dict(id=6906, value="string 6906")
        oson = self.conn.encode_oson(value)
        self.cursor.setinputsizes(oracledb.DB_TYPE_JSON)
        self.cursor.execute(
            "insert into TestOsonCols values (1, :data)", [oson]
        )
        self.conn.commit()
        self.cursor.execute("select OsonCol from TestOsonCols")
        (oson_val,) = self.cursor.fetchone()
        oson_val = self.conn.decode_oson(oson_val)
        self.assertEqual(oson_val, value)


if __name__ == "__main__":
    test_env.run_test_cases()
