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
Module for testing Simple Oracle Document Access (SODA) Database
"""

import datetime
import decimal
import json

import pytest


def _verify_doc(
    doc,
    bytes_content,
    str_content=None,
    content=None,
    key=None,
    media_type="application/json",
):
    assert doc.getContentAsBytes() == bytes_content
    if str_content is not None:
        assert doc.getContentAsString() == str_content
    if content is not None:
        assert doc.getContent() == content
    assert doc.key == key
    assert doc.mediaType == media_type
    assert doc.version is None
    assert doc.lastModified is None
    assert doc.createdOn is None


def test_1000(soda_db, test_env):
    "1000 - test creating documents with JSON data"
    val = {"testKey1": "testValue1", "testKey2": "testValue2"}
    if test_env.has_client_version(23, 4):
        str_val = str(val)
    else:
        str_val = json.dumps(val)
    bytes_val = str_val.encode()
    key = "MyKey"
    media_type = "text/plain"
    doc = soda_db.createDocument(val)
    _verify_doc(doc, bytes_val, str_val, val)
    str_val = json.dumps(val)
    bytes_val = str_val.encode()
    doc = soda_db.createDocument(str_val, key)
    _verify_doc(doc, bytes_val, str_val, val, key)
    doc = soda_db.createDocument(bytes_val, key, media_type)
    _verify_doc(doc, bytes_val, str_val, bytes_val, key, media_type)


def test_1001(soda_db):
    "1001 - test creating documents with raw data"
    val = b"<html/>"
    key = "MyRawKey"
    media_type = "text/html"
    doc = soda_db.createDocument(val)
    _verify_doc(doc, val)
    doc = soda_db.createDocument(val, key)
    _verify_doc(doc, val, key=key)
    doc = soda_db.createDocument(val, key, media_type)
    _verify_doc(doc, val, key=key, media_type=media_type)


def test_1002(soda_db):
    "1002 - test getting collection names from the database"
    assert soda_db.getCollectionNames() == []
    names = ["zCol", "dCol", "sCol", "aCol", "gCol"]
    sorted_names = list(sorted(names))
    for name in names:
        soda_db.createCollection(name)
    assert soda_db.getCollectionNames() == sorted_names
    assert soda_db.getCollectionNames(limit=2) == sorted_names[:2]
    assert soda_db.getCollectionNames("a") == sorted_names
    assert soda_db.getCollectionNames("C") == sorted_names
    assert soda_db.getCollectionNames("b", limit=3) == sorted_names[1:4]
    assert soda_db.getCollectionNames("z") == sorted_names[-1:]


def test_1003(soda_db):
    "1003 - test opening a collection"
    coll = soda_db.openCollection("CollectionThatDoesNotExist")
    assert coll is None
    created_coll = soda_db.createCollection("TestOpenCollection")
    coll = soda_db.openCollection(created_coll.name)
    assert coll.name == created_coll.name


def test_1004(soda_db, conn):
    "1004 - test SodaDatabase repr() and str()"
    assert repr(soda_db) == f"<oracledb.SodaDatabase on {conn}>"
    assert str(soda_db) == f"<oracledb.SodaDatabase on {conn}>"


def test_1005(soda_db, test_env):
    "1005 - test negative cases for SODA database methods"
    pytest.raises(TypeError, soda_db.createCollection)
    pytest.raises(TypeError, soda_db.createCollection, 1)
    with test_env.assert_raises_full_code("ORA-40658"):
        soda_db.createCollection(None)
    with test_env.assert_raises_full_code("ORA-40675"):
        soda_db.createCollection("CollMetadata", 7)
    pytest.raises(TypeError, soda_db.getCollectionNames, 1)


def test_1006(soda_db, test_env):
    "1006 - test creating documents with JSON data using extended types"
    if not test_env.has_client_version(23, 4):
        pytest.skip("unsupported data types")
    val = {
        "testKey1": "testValue1",
        "testKey2": decimal.Decimal("12.78"),
        "testKey3": datetime.datetime(2023, 7, 3, 11, 10, 24),
    }
    doc = soda_db.createDocument(val)
    str_val = str(val)
    bytes_val = str_val.encode()
    _verify_doc(doc, bytes_val, str_val, val)


def test_1007(soda_db):
    "1007 - test creating documents with int scalar value"
    val = 144
    str_val = "144"
    bytes_val = b"144"
    key = "MyKey"
    media_type = "application/json"
    doc = soda_db.createDocument(val)
    _verify_doc(doc, bytes_val, str_val, val)
    doc = soda_db.createDocument(val, key)
    _verify_doc(doc, bytes_val, str_val, val, key)
    doc = soda_db.createDocument(val, key, media_type)
    _verify_doc(doc, bytes_val, str_val, val, key, media_type)


def test_1008(soda_db, test_env):
    "1008 - test creating documents with float scalar value"
    if not test_env.has_client_and_server_version(23, 4):
        pytest.skip("data types serialized differently")
    val = 12.2
    str_val = "12.2"
    bytes_val = b"12.2"
    decimal_val = decimal.Decimal(str_val)
    key = "MyKey"
    media_type = "application/json"
    doc = soda_db.createDocument(val)
    _verify_doc(doc, bytes_val, str_val, decimal_val)
    doc = soda_db.createDocument(val, key)
    _verify_doc(doc, bytes_val, str_val, decimal_val, key)
    doc = soda_db.createDocument(val, key, media_type)
    _verify_doc(doc, bytes_val, str_val, decimal_val, key, media_type)


def test_1009(soda_db, test_env):
    "1009 - test creating documents with a list"
    if not test_env.has_client_and_server_version(23, 4):
        pytest.skip("unsupported data types")
    val = [12, "str", b"bytes", [1], {"dict": "3"}]
    decimal_val = [
        decimal.Decimal("12"),
        "str",
        b"bytes",
        [decimal.Decimal("1")],
        {"dict": "3"},
    ]
    str_val = "[Decimal('12'), 'str', b'bytes', [Decimal('1')], {'dict': '3'}]"
    bytes_val = (
        b"[Decimal('12'), 'str', b'bytes', [Decimal('1')], {'dict': '3'}]"
    )
    key = "MyKey"
    media_type = "application/json"
    doc = soda_db.createDocument(val)
    _verify_doc(doc, bytes_val, str_val, decimal_val)
    doc = soda_db.createDocument(val, key)
    _verify_doc(doc, bytes_val, str_val, decimal_val, key)
    doc = soda_db.createDocument(val, key, media_type)
    _verify_doc(doc, bytes_val, str_val, decimal_val, key, media_type)


def test_1010(soda_db, test_env):
    "1010 - test creating documents with a boolean scalar value"
    if not test_env.has_client_and_server_version(23, 4):
        pytest.skip("data types serialized differently")
    test_values = [(True, "True", b"True"), (False, "False", b"False")]
    key = "MyKey"
    media_type = "application/json"
    for val, str_val, bytes_val in test_values:
        doc = soda_db.createDocument(val)
        _verify_doc(doc, bytes_val, str_val, val)
        doc = soda_db.createDocument(val, key)
        _verify_doc(doc, bytes_val, str_val, val, key)
        doc = soda_db.createDocument(val, key, media_type)
        _verify_doc(doc, bytes_val, str_val, val, key, media_type)


def test_1011(soda_db, test_env):
    "1011 - test creating documents with unsupported types"
    if not test_env.has_client_and_server_version(23, 4):
        pytest.skip("data types serialized differently")
    values = [
        tuple([144, 2]),
        set("144"),
        bytearray("omg", "utf-8"),
        complex(2j),
        range(4),
    ]
    for value in values:
        with test_env.assert_raises_full_code("DPY-3003"):
            soda_db.createDocument(value)
