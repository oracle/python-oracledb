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
3300 - Module for testing Simple Oracle Document Access (SODA) Database
"""

import datetime
import decimal
import json
import unittest

import test_env


@unittest.skipIf(
    test_env.skip_soda_tests(), "unsupported client/server combination"
)
class TestCase(test_env.BaseTestCase):
    def __verify_doc(
        self,
        doc,
        bytes_content,
        str_content=None,
        content=None,
        key=None,
        media_type="application/json",
    ):
        self.assertEqual(doc.getContentAsBytes(), bytes_content)
        if str_content is not None:
            self.assertEqual(doc.getContentAsString(), str_content)
        if content is not None:
            self.assertEqual(doc.getContent(), content)
        self.assertEqual(doc.key, key)
        self.assertEqual(doc.mediaType, media_type)
        self.assertIsNone(doc.version)
        self.assertIsNone(doc.lastModified)
        self.assertIsNone(doc.createdOn)

    def test_3300(self):
        "3300 - test creating documents with JSON data"
        soda_db = self.get_soda_database()
        val = {"testKey1": "testValue1", "testKey2": "testValue2"}
        if test_env.get_client_version() < (23, 4):
            str_val = json.dumps(val)
        else:
            str_val = str(val)
        bytes_val = str_val.encode()
        key = "MyKey"
        media_type = "text/plain"
        doc = soda_db.createDocument(val)
        self.__verify_doc(doc, bytes_val, str_val, val)
        str_val = json.dumps(val)
        bytes_val = str_val.encode()
        doc = soda_db.createDocument(str_val, key)
        self.__verify_doc(doc, bytes_val, str_val, val, key)
        doc = soda_db.createDocument(bytes_val, key, media_type)
        self.__verify_doc(doc, bytes_val, str_val, bytes_val, key, media_type)

    def test_3301(self):
        "3301 - test creating documents with raw data"
        soda_db = self.get_soda_database()
        val = b"<html/>"
        key = "MyRawKey"
        media_type = "text/html"
        doc = soda_db.createDocument(val)
        self.__verify_doc(doc, val)
        doc = soda_db.createDocument(val, key)
        self.__verify_doc(doc, val, key=key)
        doc = soda_db.createDocument(val, key, media_type)
        self.__verify_doc(doc, val, key=key, media_type=media_type)

    def test_3302(self):
        "3302 - test getting collection names from the database"
        soda_db = self.get_soda_database()
        self.assertEqual(soda_db.getCollectionNames(), [])
        names = ["zCol", "dCol", "sCol", "aCol", "gCol"]
        sorted_names = list(sorted(names))
        for name in names:
            soda_db.createCollection(name)
        self.assertEqual(soda_db.getCollectionNames(), sorted_names)
        self.assertEqual(soda_db.getCollectionNames(limit=2), sorted_names[:2])
        self.assertEqual(soda_db.getCollectionNames("a"), sorted_names)
        self.assertEqual(soda_db.getCollectionNames("C"), sorted_names)
        self.assertEqual(
            soda_db.getCollectionNames("b", limit=3), sorted_names[1:4]
        )
        self.assertEqual(soda_db.getCollectionNames("z"), sorted_names[-1:])

    def test_3303(self):
        "3303 - test opening a collection"
        soda_db = self.get_soda_database()
        coll = soda_db.openCollection("CollectionThatDoesNotExist")
        self.assertIsNone(coll)
        created_coll = soda_db.createCollection("TestOpenCollection")
        coll = soda_db.openCollection(created_coll.name)
        self.assertEqual(coll.name, created_coll.name)

    def test_3304(self):
        "3304 - test SodaDatabase repr() and str()"
        soda_db = self.get_soda_database()
        self.assertEqual(
            repr(soda_db), f"<oracledb.SodaDatabase on {self.conn}>"
        )
        self.assertEqual(
            str(soda_db), f"<oracledb.SodaDatabase on {self.conn}>"
        )

    def test_3305(self):
        "3305 - test negative cases for SODA database methods"
        soda_db = self.get_soda_database()
        self.assertRaises(TypeError, soda_db.createCollection)
        self.assertRaises(TypeError, soda_db.createCollection, 1)
        with self.assertRaisesFullCode("ORA-40658"):
            soda_db.createCollection(None)
        with self.assertRaisesFullCode("ORA-40675"):
            soda_db.createCollection("CollMetadata", 7)
        self.assertRaises(TypeError, soda_db.getCollectionNames, 1)

    @unittest.skipIf(
        test_env.get_client_version() < (23, 4), "unsupported data types"
    )
    def test_3306(self):
        "3306 - test creating documents with JSON data using extended types"
        soda_db = self.get_soda_database()
        val = {
            "testKey1": "testValue1",
            "testKey2": decimal.Decimal("12.78"),
            "testKey3": datetime.datetime(2023, 7, 3, 11, 10, 24),
        }
        doc = soda_db.createDocument(val)
        str_val = str(val)
        bytes_val = str_val.encode()
        self.__verify_doc(doc, bytes_val, str_val, val)


if __name__ == "__main__":
    test_env.run_test_cases()
