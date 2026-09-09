# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2026, Oracle and/or its affiliates.
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
Module for testing comparisons with database types and API types, including the
synonyms retained for backwards compatibility. This module also tests for
pickling/unpickling of database types and API types.
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


def test_data_types_1200():
    "1200 - test oracledb.DB_TYPE_BFILE comparisons and pickling"
    assert oracledb.DB_TYPE_BFILE == oracledb.BFILE
    _test_pickle(oracledb.DB_TYPE_BFILE)


def test_data_types_1201():
    "1201 - test oracledb.DB_TYPE_BINARY_DOUBLE comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_BINARY_DOUBLE, oracledb.NUMBER)
    assert oracledb.DB_TYPE_BINARY_DOUBLE == oracledb.NATIVE_FLOAT
    _test_pickle(oracledb.DB_TYPE_BINARY_DOUBLE)


def test_data_types_1202():
    "1202 - test oracledb.DB_TYPE_BINARY_FLOAT comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_BINARY_FLOAT, oracledb.NUMBER)
    _test_pickle(oracledb.DB_TYPE_BINARY_FLOAT)


def test_data_types_1203():
    "1203 - test oracledb.DB_TYPE_BINARY_INTEGER comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_BINARY_INTEGER, oracledb.NUMBER)
    assert oracledb.DB_TYPE_BINARY_INTEGER == oracledb.NATIVE_INT
    _test_pickle(oracledb.DB_TYPE_BINARY_INTEGER)


def test_data_types_1204():
    "1204 - test oracledb.DB_TYPE_BLOB comparisons and pickling"
    assert oracledb.DB_TYPE_BLOB == oracledb.BLOB
    _test_pickle(oracledb.DB_TYPE_BLOB)


def test_data_types_1205():
    "1205 - test oracledb.DB_TYPE_BOOLEAN comparisons and pickling"
    assert oracledb.DB_TYPE_BOOLEAN == oracledb.BOOLEAN
    _test_pickle(oracledb.DB_TYPE_BOOLEAN)


def test_data_types_1206():
    "1206 - test oracledb.DB_TYPE_CHAR comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_CHAR, oracledb.STRING)
    assert oracledb.DB_TYPE_CHAR == oracledb.FIXED_CHAR
    _test_pickle(oracledb.DB_TYPE_CHAR)


def test_data_types_1207():
    "1207 - test oracledb.DB_TYPE_CLOB comparisons and pickling"
    assert oracledb.DB_TYPE_CLOB == oracledb.CLOB
    _test_pickle(oracledb.DB_TYPE_CLOB)


def test_data_types_1208():
    "1208 - test oracledb.DB_TYPE_CURSOR comparisons and pickling"
    assert oracledb.DB_TYPE_CURSOR == oracledb.CURSOR
    _test_pickle(oracledb.DB_TYPE_CURSOR)


def test_data_types_1209():
    "1209 - test oracledb.DB_TYPE_DATE comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_DATE, oracledb.DATETIME)
    _test_pickle(oracledb.DB_TYPE_DATE)


def test_data_types_1210():
    "1210 - test oracledb.DB_TYPE_INTERVAL_DS comparisons and pickling"
    assert oracledb.DB_TYPE_INTERVAL_DS == oracledb.INTERVAL
    _test_pickle(oracledb.DB_TYPE_INTERVAL_DS)


def test_data_types_1211():
    "1211 - test oracledb.DB_TYPE_LONG comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_LONG, oracledb.STRING)
    assert oracledb.DB_TYPE_LONG == oracledb.LONG_STRING
    _test_pickle(oracledb.DB_TYPE_LONG)


def test_data_types_1212():
    "1212 - test oracledb.DB_TYPE_LONG_RAW comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_LONG_RAW, oracledb.BINARY)
    assert oracledb.DB_TYPE_LONG_RAW == oracledb.LONG_BINARY
    _test_pickle(oracledb.DB_TYPE_LONG_RAW)


def test_data_types_1213():
    "1213 - test oracledb.DB_TYPE_NCHAR comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_NCHAR, oracledb.STRING)
    assert oracledb.DB_TYPE_NCHAR == oracledb.FIXED_NCHAR
    _test_pickle(oracledb.DB_TYPE_NCHAR)


def test_data_types_1214():
    "1214 - test oracledb.DB_TYPE_NCLOB comparisons and pickling"
    assert oracledb.DB_TYPE_NCLOB == oracledb.NCLOB
    _test_pickle(oracledb.DB_TYPE_NCLOB)


def test_data_types_1215():
    "1215 - test oracledb.DB_TYPE_NUMBER comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_NUMBER, oracledb.NUMBER)
    _test_pickle(oracledb.DB_TYPE_NUMBER)


def test_data_types_1216():
    "1216 - test oracledb.DB_TYPE_NVARCHAR comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_NVARCHAR, oracledb.STRING)
    assert oracledb.DB_TYPE_NVARCHAR == oracledb.NCHAR
    _test_pickle(oracledb.DB_TYPE_NVARCHAR)


def test_data_types_1217():
    "1217 - test oracledb.DB_TYPE_OBJECT comparisons and pickling"
    assert oracledb.DB_TYPE_OBJECT == oracledb.OBJECT
    _test_pickle(oracledb.DB_TYPE_OBJECT)


def test_data_types_1218():
    "1218 - test oracledb.DB_TYPE_RAW comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_RAW, oracledb.BINARY)
    _test_pickle(oracledb.DB_TYPE_RAW)


def test_data_types_1219():
    "1219 - test oracledb.DB_TYPE_ROWID comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_ROWID, oracledb.ROWID)
    _test_pickle(oracledb.DB_TYPE_ROWID)


def test_data_types_1220():
    "1220 - test oracledb.DB_TYPE_TIMESTAMP comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_TIMESTAMP, oracledb.DATETIME)
    assert oracledb.DB_TYPE_TIMESTAMP == oracledb.TIMESTAMP
    _test_pickle(oracledb.DB_TYPE_TIMESTAMP)


def test_data_types_1221():
    "1221 - test oracledb.DB_TYPE_TIMESTAMP_LTZ comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_TIMESTAMP_LTZ, oracledb.DATETIME)
    _test_pickle(oracledb.DB_TYPE_TIMESTAMP_LTZ)


def test_data_types_1222():
    "1222 - test oracledb.DB_TYPE_TIMESTAMP_TZ comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_TIMESTAMP_TZ, oracledb.DATETIME)
    _test_pickle(oracledb.DB_TYPE_TIMESTAMP_TZ)


def test_data_types_1223():
    "1223 - test oracledb.DB_TYPE_VARCHAR comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_VARCHAR, oracledb.STRING)
    _test_pickle(oracledb.DB_TYPE_VARCHAR)


def test_data_types_1224():
    "1224 - test oracledb.NUMBER pickling"
    _test_pickle(oracledb.NUMBER)


def test_data_types_1225():
    "1225 - test oracledb.STRING pickling"
    _test_pickle(oracledb.STRING)


def test_data_types_1226():
    "1226 - test oracledb.DATETIME pickling"
    _test_pickle(oracledb.DATETIME)


def test_data_types_1227():
    "1227 - test oracledb.BINARY pickling"
    _test_pickle(oracledb.BINARY)


def test_data_types_1228():
    "1228 - test oracledb.ROWID pickling"
    _test_pickle(oracledb.ROWID)


def test_data_types_1229():
    "1229 - test oracledb.DB_TYPE_UROWID comparisons and pickling"
    _test_compare(oracledb.DB_TYPE_UROWID, oracledb.ROWID)
    _test_pickle(oracledb.DB_TYPE_UROWID)


def test_data_types_1230():
    "1230 - test oracledb.DB_TYPE_JSON pickling"
    _test_pickle(oracledb.DB_TYPE_JSON)


def test_data_types_1231():
    "1231 - test oracledb.DB_TYPE_INTERVAL_YM pickling"
    _test_pickle(oracledb.DB_TYPE_INTERVAL_YM)
