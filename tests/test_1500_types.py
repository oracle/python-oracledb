# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
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
1500 - Module for testing comparisons with database types and API types,
including the synonyms retained for backwards compatibility. This module also
tests for pickling/unpickling of database types and API types.
"""

import pickle

import oracledb


def _test_compare(db_type, api_type):
    assert db_type == db_type
    assert db_type == api_type
    assert api_type == db_type
    assert db_type != 5
    assert db_type != oracledb.DB_TYPE_OBJECT


def _test_pickle(typ):
    assert typ is pickle.loads(pickle.dumps(typ))


def test_1500():
    "1500 - test oracledb.DB_TYPE_BFILE comparisons and pickling"
    assert oracledb.DB_TYPE_BFILE == oracledb.BFILE
    _test_pickle(oracledb.DB_TYPE_BFILE)


def test_1501():
    "1501 - test oracledb.DB_TYPE_BINARY_DOUBLE comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_BINARY_DOUBLE, oracledb.NUMBER)
    assert oracledb.DB_TYPE_BINARY_DOUBLE == oracledb.NATIVE_FLOAT
    _test_pickle(oracledb.DB_TYPE_BINARY_DOUBLE)


def test_1502():
    "1502 - test oracledb.DB_TYPE_BINARY_FLOAT comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_BINARY_FLOAT, oracledb.NUMBER)
    _test_pickle(oracledb.DB_TYPE_BINARY_FLOAT)


def test_1503():
    "1503 - test oracledb.DB_TYPE_BINARY_INTEGER comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_BINARY_INTEGER, oracledb.NUMBER)
    assert oracledb.DB_TYPE_BINARY_INTEGER == oracledb.NATIVE_INT
    _test_pickle(oracledb.DB_TYPE_BINARY_INTEGER)


def test_1504():
    "1504 - test oracledb.DB_TYPE_BLOB comparisons and pickling"
    assert oracledb.DB_TYPE_BLOB == oracledb.BLOB
    _test_pickle(oracledb.DB_TYPE_BLOB)


def test_1505():
    "1505 - test oracledb.DB_TYPE_BOOLEAN comparisons and pickling"
    assert oracledb.DB_TYPE_BOOLEAN == oracledb.BOOLEAN
    _test_pickle(oracledb.DB_TYPE_BOOLEAN)


def test_1506():
    "1506 - test oracledb.DB_TYPE_CHAR comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_CHAR, oracledb.STRING)
    assert oracledb.DB_TYPE_CHAR == oracledb.FIXED_CHAR
    _test_pickle(oracledb.DB_TYPE_CHAR)


def test_1507():
    "1507 - test oracledb.DB_TYPE_CLOB comparisons and pickling"
    assert oracledb.DB_TYPE_CLOB == oracledb.CLOB
    _test_pickle(oracledb.DB_TYPE_CLOB)


def test_1508():
    "1508 - test oracledb.DB_TYPE_CURSOR comparisons and pickling"
    assert oracledb.DB_TYPE_CURSOR == oracledb.CURSOR
    _test_pickle(oracledb.DB_TYPE_CURSOR)


def test_1509():
    "1509 - test oracledb.DB_TYPE_DATE comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_DATE, oracledb.DATETIME)
    _test_pickle(oracledb.DB_TYPE_DATE)


def test_1510():
    "1510 - test oracledb.DB_TYPE_INTERVAL_DS comparisons and pickling"
    assert oracledb.DB_TYPE_INTERVAL_DS == oracledb.INTERVAL
    _test_pickle(oracledb.DB_TYPE_INTERVAL_DS)


def test_1511():
    "1511 - test oracledb.DB_TYPE_LONG comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_LONG, oracledb.STRING)
    assert oracledb.DB_TYPE_LONG == oracledb.LONG_STRING
    _test_pickle(oracledb.DB_TYPE_LONG)


def test_1512():
    "1512 - test oracledb.DB_TYPE_LONG_RAW comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_LONG_RAW, oracledb.BINARY)
    assert oracledb.DB_TYPE_LONG_RAW == oracledb.LONG_BINARY
    _test_pickle(oracledb.DB_TYPE_LONG_RAW)


def test_1513():
    "1513 - test oracledb.DB_TYPE_NCHAR comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_NCHAR, oracledb.STRING)
    assert oracledb.DB_TYPE_NCHAR == oracledb.FIXED_NCHAR
    _test_pickle(oracledb.DB_TYPE_NCHAR)


def test_1514():
    "1514 - test oracledb.DB_TYPE_NCLOB comparisons and pickling"
    assert oracledb.DB_TYPE_NCLOB == oracledb.NCLOB
    _test_pickle(oracledb.DB_TYPE_NCLOB)


def test_1515():
    "1515 - test oracledb.DB_TYPE_NUMBER comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_NUMBER, oracledb.NUMBER)
    _test_pickle(oracledb.DB_TYPE_NUMBER)


def test_1516():
    "1516 - test oracledb.DB_TYPE_NVARCHAR comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_NVARCHAR, oracledb.STRING)
    assert oracledb.DB_TYPE_NVARCHAR == oracledb.NCHAR
    _test_pickle(oracledb.DB_TYPE_NVARCHAR)


def test_1517():
    "1517 - test oracledb.DB_TYPE_OBJECT comparisons and pickling"
    assert oracledb.DB_TYPE_OBJECT == oracledb.OBJECT
    _test_pickle(oracledb.DB_TYPE_OBJECT)


def test_1518():
    "1518 - test oracledb.DB_TYPE_RAW comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_RAW, oracledb.BINARY)
    _test_pickle(oracledb.DB_TYPE_RAW)


def test_1519():
    "1519 - test oracledb.DB_TYPE_ROWID comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_ROWID, oracledb.ROWID)
    _test_pickle(oracledb.DB_TYPE_ROWID)


def test_1520():
    "1520 - test oracledb.DB_TYPE_TIMESTAMP comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_TIMESTAMP, oracledb.DATETIME)
    assert oracledb.DB_TYPE_TIMESTAMP == oracledb.TIMESTAMP
    _test_pickle(oracledb.DB_TYPE_TIMESTAMP)


def test_1521():
    "1521 - test oracledb.DB_TYPE_TIMESTAMP_LTZ comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_TIMESTAMP_LTZ, oracledb.DATETIME)
    _test_pickle(oracledb.DB_TYPE_TIMESTAMP_LTZ)


def test_1522():
    "1522 - test oracledb.DB_TYPE_TIMESTAMP_TZ comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_TIMESTAMP_TZ, oracledb.DATETIME)
    _test_pickle(oracledb.DB_TYPE_TIMESTAMP_TZ)


def test_1523():
    "1523 - test oracledb.DB_TYPE_VARCHAR comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_VARCHAR, oracledb.STRING)
    _test_pickle(oracledb.DB_TYPE_VARCHAR)


def test_1524():
    "1524 - test oracledb.NUMBER pickling"
    _test_pickle(oracledb.NUMBER)


def test_1525():
    "1525 - test oracledb.STRING pickling"
    _test_pickle(oracledb.STRING)


def test_1526():
    "1526 - test oracledb.DATETIME pickling"
    _test_pickle(oracledb.DATETIME)


def test_1527():
    "1527 - test oracledb.BINARY pickling"
    _test_pickle(oracledb.BINARY)


def test_1528():
    "1528 - test oracledb.ROWID pickling"
    _test_pickle(oracledb.ROWID)


def test_1529():
    "1529 - test oracledb.DB_TYPE_UROWID comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_UROWID, oracledb.ROWID)
    _test_pickle(oracledb.DB_TYPE_UROWID)


def test_1530():
    "1530 - test oracledb.DB_TYPE_JSON pickling"
    _test_pickle(oracledb.DB_TYPE_JSON)


def test_1531():
    "1531 - test oracledb.DB_TYPE_INTERVAL_YM pickling"
    _test_pickle(oracledb.DB_TYPE_INTERVAL_YM)
