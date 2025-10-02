# -----------------------------------------------------------------------------
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
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

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(skip_unless_native_json_supported):
    pass


def test_6900(cursor):
    "6900 - test OSON metadata"
    cursor.execute("select * from TestOsonCols")
    int_col_metadata, oson_col_metadata = cursor.description
    assert not int_col_metadata.is_oson
    assert oson_col_metadata.is_oson


def test_6901(conn, cursor):
    "6901 - test simple query of OSON encoded bytes"
    cursor.execute("delete from TestOsonCols")
    cursor.execute(
        """
            insert into TestOsonCols (IntCol, OsonCol)
            values (1, '{"id": 6901, "value" : "string 6901"}')"""
    )
    conn.commit()
    cursor.execute("select OsonCol from TestOsonCols")
    (oson_val,) = cursor.fetchone()
    expected_val = dict(id=6901, value="string 6901")
    assert oson_val == expected_val


def test_6902(conn, cursor):
    "6902 - test round trip of OSON encoded bytes"
    value = dict(id=6902, value="string 6902")
    cursor.execute("delete from TestOsonCols")
    encoded_oson = conn.encode_oson(value)
    cursor.execute(
        "insert into TestOsonCols values (1, :data)", [encoded_oson]
    )
    conn.commit()
    cursor.execute("select OsonCol from TestOsonCols")
    (oson_val,) = cursor.fetchone()
    assert oson_val == value


def test_6903(conn):
    "6903 - test encoding and decoding a value"
    value = dict(id=6903, value="string 6903")
    out_value = conn.decode_oson(conn.encode_oson(value))
    assert out_value == value


def test_6904(conn, test_env):
    "6904 - test decoding a non encoded value"
    value = b"{'not a previous encoded value': 3}"
    with test_env.assert_raises_full_code("DPY-5004"):
        conn.decode_oson(value)


def test_6905(conn, cursor):
    "6905 - test inserting oson inside a lob"
    value = dict(id=6905, value="string 6905")
    cursor.execute("delete from TestOsonCols")
    encoded_oson = conn.encode_oson(value)
    lob = conn.createlob(oracledb.DB_TYPE_BLOB, encoded_oson)
    cursor.execute("insert into TestOsonCols values (1, :data)", [lob])
    conn.commit()
    cursor.execute("select OsonCol from TestOsonCols")
    (oson_val,) = cursor.fetchone()
    assert oson_val == value


def test_6906(conn, cursor):
    "6906 - test inserting oson as json"
    cursor.execute("delete from TestOsonCols")
    value = dict(id=6906, value="string 6906")
    oson = conn.encode_oson(value)
    cursor.setinputsizes(oracledb.DB_TYPE_JSON)
    cursor.execute("insert into TestOsonCols values (1, :data)", [oson])
    conn.commit()
    cursor.execute("select OsonCol from TestOsonCols")
    (oson_val,) = cursor.fetchone()
    oson_val = conn.decode_oson(oson_val)
    assert oson_val == value
