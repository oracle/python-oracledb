# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2024, Oracle and/or its affiliates.
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
import test_env


class TestCase(test_env.BaseTestCase):
    requires_connection = False

    def __test_compare(self, db_type, api_type):
        self.assertEqual(db_type, db_type)
        self.assertEqual(db_type, api_type)
        self.assertEqual(api_type, db_type)
        self.assertNotEqual(db_type, 5)
        self.assertNotEqual(db_type, oracledb.DB_TYPE_OBJECT)

    def __test_pickle(self, typ):
        self.assertIs(typ, pickle.loads(pickle.dumps(typ)))

    def test_1500(self):
        "1500 - test oracledb.DB_TYPE_BFILE comparisons and pickling"
        self.assertEqual(oracledb.DB_TYPE_BFILE, oracledb.BFILE)
        self.__test_pickle(oracledb.DB_TYPE_BFILE)

    def test_1501(self):
        "1501 - test oracledb.DB_TYPE_BINARY_DOUBLE comparisons and pickling"
        self.__test_compare(oracledb.DB_TYPE_BINARY_DOUBLE, oracledb.NUMBER)
        self.assertEqual(oracledb.DB_TYPE_BINARY_DOUBLE, oracledb.NATIVE_FLOAT)
        self.__test_pickle(oracledb.DB_TYPE_BINARY_DOUBLE)

    def test_1502(self):
        "1502 - test oracledb.DB_TYPE_BINARY_FLOAT comparisons and pickling"
        self.__test_compare(oracledb.DB_TYPE_BINARY_FLOAT, oracledb.NUMBER)
        self.__test_pickle(oracledb.DB_TYPE_BINARY_FLOAT)

    def test_1503(self):
        "1503 - test oracledb.DB_TYPE_BINARY_INTEGER comparisons and pickling"
        self.__test_compare(oracledb.DB_TYPE_BINARY_INTEGER, oracledb.NUMBER)
        self.assertEqual(oracledb.DB_TYPE_BINARY_INTEGER, oracledb.NATIVE_INT)
        self.__test_pickle(oracledb.DB_TYPE_BINARY_INTEGER)

    def test_1504(self):
        "1504 - test oracledb.DB_TYPE_BLOB comparisons and pickling"
        self.assertEqual(oracledb.DB_TYPE_BLOB, oracledb.BLOB)
        self.__test_pickle(oracledb.DB_TYPE_BLOB)

    def test_1505(self):
        "1505 - test oracledb.DB_TYPE_BOOLEAN comparisons and pickling"
        self.assertEqual(oracledb.DB_TYPE_BOOLEAN, oracledb.BOOLEAN)
        self.__test_pickle(oracledb.DB_TYPE_BOOLEAN)

    def test_1506(self):
        "1506 - test oracledb.DB_TYPE_CHAR comparisons and pickling"
        self.__test_compare(oracledb.DB_TYPE_CHAR, oracledb.STRING)
        self.assertEqual(oracledb.DB_TYPE_CHAR, oracledb.FIXED_CHAR)
        self.__test_pickle(oracledb.DB_TYPE_CHAR)

    def test_1507(self):
        "1507 - test oracledb.DB_TYPE_CLOB comparisons and pickling"
        self.assertEqual(oracledb.DB_TYPE_CLOB, oracledb.CLOB)
        self.__test_pickle(oracledb.DB_TYPE_CLOB)

    def test_1508(self):
        "1508 - test oracledb.DB_TYPE_CURSOR comparisons and pickling"
        self.assertEqual(oracledb.DB_TYPE_CURSOR, oracledb.CURSOR)
        self.__test_pickle(oracledb.DB_TYPE_CURSOR)

    def test_1509(self):
        "1509 - test oracledb.DB_TYPE_DATE comparisons and pickling"
        self.__test_compare(oracledb.DB_TYPE_DATE, oracledb.DATETIME)
        self.__test_pickle(oracledb.DB_TYPE_DATE)

    def test_1510(self):
        "1510 - test oracledb.DB_TYPE_INTERVAL_DS comparisons and pickling"
        self.assertEqual(oracledb.DB_TYPE_INTERVAL_DS, oracledb.INTERVAL)
        self.__test_pickle(oracledb.DB_TYPE_INTERVAL_DS)

    def test_1511(self):
        "1511 - test oracledb.DB_TYPE_LONG comparisons and pickling"
        self.__test_compare(oracledb.DB_TYPE_LONG, oracledb.STRING)
        self.assertEqual(oracledb.DB_TYPE_LONG, oracledb.LONG_STRING)
        self.__test_pickle(oracledb.DB_TYPE_LONG)

    def test_1512(self):
        "1512 - test oracledb.DB_TYPE_LONG_RAW comparisons and pickling"
        self.__test_compare(oracledb.DB_TYPE_LONG_RAW, oracledb.BINARY)
        self.assertEqual(oracledb.DB_TYPE_LONG_RAW, oracledb.LONG_BINARY)
        self.__test_pickle(oracledb.DB_TYPE_LONG_RAW)

    def test_1513(self):
        "1513 - test oracledb.DB_TYPE_NCHAR comparisons and pickling"
        self.__test_compare(oracledb.DB_TYPE_NCHAR, oracledb.STRING)
        self.assertEqual(oracledb.DB_TYPE_NCHAR, oracledb.FIXED_NCHAR)
        self.__test_pickle(oracledb.DB_TYPE_NCHAR)

    def test_1514(self):
        "1514 - test oracledb.DB_TYPE_NCLOB comparisons and pickling"
        self.assertEqual(oracledb.DB_TYPE_NCLOB, oracledb.NCLOB)
        self.__test_pickle(oracledb.DB_TYPE_NCLOB)

    def test_1515(self):
        "1515 - test oracledb.DB_TYPE_NUMBER comparisons and pickling"
        self.__test_compare(oracledb.DB_TYPE_NUMBER, oracledb.NUMBER)
        self.__test_pickle(oracledb.DB_TYPE_NUMBER)

    def test_1516(self):
        "1516 - test oracledb.DB_TYPE_NVARCHAR comparisons and pickling"
        self.__test_compare(oracledb.DB_TYPE_NVARCHAR, oracledb.STRING)
        self.assertEqual(oracledb.DB_TYPE_NVARCHAR, oracledb.NCHAR)
        self.__test_pickle(oracledb.DB_TYPE_NVARCHAR)

    def test_1517(self):
        "1517 - test oracledb.DB_TYPE_OBJECT comparisons and pickling"
        self.assertEqual(oracledb.DB_TYPE_OBJECT, oracledb.OBJECT)
        self.__test_pickle(oracledb.DB_TYPE_OBJECT)

    def test_1518(self):
        "1518 - test oracledb.DB_TYPE_RAW comparisons and pickling"
        self.__test_compare(oracledb.DB_TYPE_RAW, oracledb.BINARY)
        self.__test_pickle(oracledb.DB_TYPE_RAW)

    def test_1519(self):
        "1519 - test oracledb.DB_TYPE_ROWID comparisons and pickling"
        self.__test_compare(oracledb.DB_TYPE_ROWID, oracledb.ROWID)
        self.__test_pickle(oracledb.DB_TYPE_ROWID)

    def test_1520(self):
        "1520 - test oracledb.DB_TYPE_TIMESTAMP comparisons and pickling"
        self.__test_compare(oracledb.DB_TYPE_TIMESTAMP, oracledb.DATETIME)
        self.assertEqual(oracledb.DB_TYPE_TIMESTAMP, oracledb.TIMESTAMP)
        self.__test_pickle(oracledb.DB_TYPE_TIMESTAMP)

    def test_1521(self):
        "1521 - test oracledb.DB_TYPE_TIMESTAMP_LTZ comparisons and pickling"
        self.__test_compare(oracledb.DB_TYPE_TIMESTAMP_LTZ, oracledb.DATETIME)
        self.__test_pickle(oracledb.DB_TYPE_TIMESTAMP_LTZ)

    def test_1522(self):
        "1522 - test oracledb.DB_TYPE_TIMESTAMP_TZ comparisons and pickling"
        self.__test_compare(oracledb.DB_TYPE_TIMESTAMP_TZ, oracledb.DATETIME)
        self.__test_pickle(oracledb.DB_TYPE_TIMESTAMP_TZ)

    def test_1523(self):
        "1523 - test oracledb.DB_TYPE_VARCHAR comparisons and pickling"
        self.__test_compare(oracledb.DB_TYPE_VARCHAR, oracledb.STRING)
        self.__test_pickle(oracledb.DB_TYPE_VARCHAR)

    def test_1524(self):
        "1524 - test oracledb.NUMBER pickling"
        self.__test_pickle(oracledb.NUMBER)

    def test_1525(self):
        "1525 - test oracledb.STRING pickling"
        self.__test_pickle(oracledb.STRING)

    def test_1526(self):
        "1526 - test oracledb.DATETIME pickling"
        self.__test_pickle(oracledb.DATETIME)

    def test_1527(self):
        "1527 - test oracledb.BINARY pickling"
        self.__test_pickle(oracledb.BINARY)

    def test_1528(self):
        "1528 - test oracledb.ROWID pickling"
        self.__test_pickle(oracledb.ROWID)

    def test_1529(self):
        "1529 - test oracledb.DB_TYPE_UROWID comparisons and pickling"
        self.__test_compare(oracledb.DB_TYPE_UROWID, oracledb.ROWID)
        self.__test_pickle(oracledb.DB_TYPE_UROWID)

    def test_1530(self):
        "1530 - test oracledb.DB_TYPE_JSON pickling"
        self.__test_pickle(oracledb.DB_TYPE_JSON)

    def test_1531(self):
        "1531 - test oracledb.DB_TYPE_INTERVAL_YM pickling"
        self.__test_pickle(oracledb.DB_TYPE_INTERVAL_YM)


if __name__ == "__main__":
    test_env.run_test_cases()
