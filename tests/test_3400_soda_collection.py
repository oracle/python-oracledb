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
3400 - Module for testing Simple Oracle Document Access (SODA) Collections
"""

import datetime
import decimal
import json
import re

import oracledb
import pytest


@pytest.fixture
def skip_if_map_mode_not_supported(test_env):
    """
    Map mode is not supported in Oracle Client version 23.
    """
    if test_env.has_client_version(23):
        pytest.skip("map mode not supported with native collections")


@pytest.fixture
def skip_if_save_not_supported(test_env):
    """
    save() is not supported in Oracle Database version 23. It also requires
    a minimum client version of 19.9 as well.
    """
    if test_env.has_client_version(23):
        pytest.skip("save() is not implemented in Oracle Database version 23")
    if not test_env.has_client_version(19, 9):
        pytest.skip("unsupported client")


def _normalize_docs(docs):
    """
    Remove the embedded OID added in Oracle Database version 23, if found,
    in order to ease comparison.
    """
    for doc in docs:
        if doc is not None and "_id" in doc:
            del doc["_id"]


def _test_skip(coll, num_to_skip, expected_content):
    filter_spec = {"$orderby": [{"path": "name", "order": "desc"}]}
    doc = coll.find().filter(filter_spec).skip(num_to_skip).getOne()
    content = doc.getContent() if doc is not None else None
    _normalize_docs([content])
    assert content == expected_content


def test_3400(soda_db, test_env):
    "3400 - test inserting invalid JSON value into SODA collection"
    invalid_json = "{testKey:testValue}"
    coll = soda_db.createCollection("InvalidJSON")
    doc = soda_db.createDocument(invalid_json)
    with test_env.assert_raises_full_code("ORA-40780", "ORA-02290"):
        coll.insertOne(doc)


def test_3401(soda_db, conn):
    "3401 - test inserting documents into a SODA collection"
    coll = soda_db.createCollection("TestInsertDocs")
    values_to_insert = [
        {"name": "George", "age": 47},
        {"name": "Susan", "age": 39},
        {"name": "John", "age": 50},
        {"name": "Jill", "age": 54},
    ]
    inserted_keys = []
    for value in values_to_insert:
        doc = coll.insertOneAndGet(value)
        inserted_keys.append(doc.key)
    conn.commit()
    assert coll.find().count() == len(values_to_insert)
    for key, value in zip(inserted_keys, values_to_insert):
        doc = coll.find().key(key).getOne().getContent()
        _normalize_docs([doc])
        assert doc == value


def test_3402(soda_db, conn):
    "3402 - test skipping documents in a SODA collection"
    coll = soda_db.createCollection("TestSkipDocs")
    values_to_insert = [
        {"name": "Anna", "age": 62},
        {"name": "Mark", "age": 37},
        {"name": "Martha", "age": 43},
        {"name": "Matthew", "age": 28},
    ]
    for value in values_to_insert:
        coll.insertOne(value)
    conn.commit()
    _test_skip(coll, 0, values_to_insert[3])
    _test_skip(coll, 1, values_to_insert[2])
    _test_skip(coll, 3, values_to_insert[0])
    _test_skip(coll, 4, None)
    _test_skip(coll, 125, None)


def test_3403(soda_db, conn):
    "3403 - test replace documents in SODA collection"
    coll = soda_db.createCollection("TestReplaceDoc")
    content = {"name": "John", "address": {"city": "Sydney"}}
    doc = coll.insertOneAndGet(content)
    new_content = {"name": "John", "address": {"city": "Melbourne"}}
    replaced = coll.find().key(doc.key).replaceOne(new_content)
    assert replaced
    conn.commit()
    doc = coll.find().key(doc.key).getOne().getContent()
    _normalize_docs([doc])
    assert doc == new_content


def test_3404(soda_db, conn):
    "3404 - test search documents with different QBEs"
    coll = soda_db.createCollection("TestSearchDocContent")
    data = [
        {
            "name": "John",
            "age": 22,
            "birthday": "2000-12-15",
            "locations": [{"city": "Bangalore"}, {"city": "Other"}],
        },
        {
            "name": "Johnson",
            "age": 45,
            "birthday": "1978-02-03",
            "locations": [{"city": "Banaras"}, {"city": "Manhattan"}],
        },
        {
            "name": "William",
            "age": 32,
            "birthday": "1991-05-17",
            "locations": {"city": "New Banaras"},
        },
    ]
    coll.insertMany(data)
    conn.commit()

    # create index so $contains works
    index = {"name": "js_ix_3404"}
    coll.createIndex(index)

    filter_specs = [
        ({"name": {"$contains": "John"}}, 1),
        ({"age": {"$contains": "45"}}, 1),
        ({"name": {"$like": "J%n"}}, 2),
        ({"name": {"$regex": ".*[ho]n"}}, 2),
        ("""{"locations.city": {"$regex": "^Ban.*"}}""", 2),
        ({"birthday": {"$date": {"$gt": "2000-01-01"}}}, 1),
        ({"birthday": {"$date": "2000-12-15"}}, 1),
        ({"age": {"$gt": 18}}, 3),
        ({"age": {"$lt": 25}}, 1),
        (
            {
                "$or": [
                    {"age": {"$gt": 50}},
                    {"locations[*].city": {"$like": "%Ban%"}},
                ]
            },
            3,
        ),
        (
            {
                "$and": [
                    {"age": {"$gt": 40}},
                    {"locations[0 to 1].city": {"$like": "%aras"}},
                ]
            },
            1,
        ),
        ({"name": {"$hasSubstring": "John"}}, 2),
        ({"name": {"$instr": "John"}}, 2),
        ({"name": {"$startsWith": "John"}}, 2),
        ({"name": {"$upper": {"$startsWith": "JO"}}}, 2),
        ({"age": {"$not": {"$eq": 22}}}, 2),
        ({"age": {"$not": {"$lt": 30, "$gt": 10}}}, 2),
        ({"locations": {"$type": "array"}}, 2),
    ]
    for filter_spec, expected_count in filter_specs:
        assert (
            coll.find().filter(filter_spec).count() == expected_count
        ), filter_spec


def test_3405(soda_db, conn):
    "3405 - test removing documents"
    coll = soda_db.createCollection("TestRemoveDocs")
    data = [
        {"name": "John", "address": {"city": "Bangalore"}},
        {"name": "Johnson", "address": {"city": "Banaras"}},
        {"name": "Joseph", "address": {"city": "Mangalore"}},
        {"name": "Jibin", "address": {"city": "Secunderabad"}},
        {"name": "Andrew", "address": {"city": "Hyderabad"}},
        {"name": "Matthew", "address": {"city": "Mumbai"}},
    ]
    docs = [coll.insertOneAndGet(v) for v in data]
    assert coll.find().key(docs[3].key).remove() == 1
    assert coll.find().count() == len(data) - 1
    search_results = coll.find().filter({"name": {"$like": "Jibin"}})
    assert search_results.count() == 0
    assert coll.find().filter({"name": {"$like": "John%"}}).remove() == 2
    assert coll.find().count() == len(data) - 3
    assert coll.find().filter({"name": {"$regex": "J.*"}}).remove() == 1
    assert coll.find().count() == len(data) - 4
    conn.commit()


def test_3406(soda_db, conn, test_env):
    "3406 - test create and drop Index"
    index_name = "TestIndexes_ix_1"
    index_spec = {
        "name": index_name,
        "fields": [
            {"path": "address.city", "datatype": "string", "order": "asc"}
        ],
    }
    coll = soda_db.createCollection("TestIndexes")
    conn.commit()
    coll.dropIndex(index_name)
    coll.createIndex(index_spec)
    pytest.raises(TypeError, coll.createIndex, 3)
    with test_env.assert_raises_full_code("ORA-40733"):
        coll.createIndex(index_spec)
    assert coll.dropIndex(index_name)
    assert not coll.dropIndex(index_name)


def test_3407(soda_db, conn):
    "3407 - test getting documents from Collection"
    conn.autocommit = True
    coll = soda_db.createCollection("TestGetDocs")
    data = [
        {"name": "John", "address": {"city": "Bangalore"}},
        {"name": "Johnson", "address": {"city": "Banaras"}},
        {"name": "Joseph", "address": {"city": "Mangalore"}},
        {"name": "Jibin", "address": {"city": "Secunderabad"}},
        {"name": "Andrew", "address": {"city": "Hyderabad"}},
    ]
    inserted_keys = list(sorted(coll.insertOneAndGet(v).key for v in data))
    fetched_keys = list(sorted(doc.key for doc in coll.find().getDocuments()))
    assert fetched_keys == inserted_keys


def test_3408(soda_db, conn):
    "3408 - test fetching documents from a cursor"
    conn.autocommit = True
    coll = soda_db.createCollection("TestFindViaCursor")
    data = [
        {"name": "John", "address": {"city": "Bangalore"}},
        {"name": "Johnson", "address": {"city": "Banaras"}},
        {"name": "Joseph", "address": {"city": "Mangalore"}},
    ]
    inserted_keys = list(sorted(coll.insertOneAndGet(v).key for v in data))
    fetched_keys = list(sorted(doc.key for doc in coll.find().getCursor()))
    assert fetched_keys == inserted_keys


def test_3409(soda_db, conn):
    "3409 - test removing multiple documents using multiple keys"
    coll = soda_db.createCollection("TestRemoveMultipleDocs")
    data = [
        {"name": "John", "address": {"city": "Bangalore"}},
        {"name": "Johnson", "address": {"city": "Banaras"}},
        {"name": "Joseph", "address": {"city": "Mangalore"}},
        {"name": "Jibin", "address": {"city": "Secunderabad"}},
        {"name": "Andrew", "address": {"city": "Hyderabad"}},
        {"name": "Matthew", "address": {"city": "Mumbai"}},
    ]
    docs = [coll.insertOneAndGet(v) for v in data]
    keys = [docs[i].key for i in (1, 3, 5)]
    num_removed = coll.find().keys(keys).remove()
    assert num_removed == len(keys)
    assert coll.find().count() == len(data) - len(keys)
    conn.commit()


def test_3410(soda_db, conn):
    "3410 - test using version to get documents and remove them"
    coll = soda_db.createCollection("TestDocumentVersion")
    content = {"name": "John", "address": {"city": "Bangalore"}}
    inserted_doc = coll.insertOneAndGet(content)
    key = inserted_doc.key
    version = inserted_doc.version
    doc = coll.find().key(key).version(version).getOne().getContent()
    _normalize_docs([doc])
    assert doc == content
    new_content = {"name": "James", "address": {"city": "Delhi"}}
    replaced_doc = coll.find().key(key).replaceOneAndGet(new_content)
    new_version = replaced_doc.version
    doc = coll.find().key(key).version(version).getOne()
    assert doc is None
    doc = coll.find().key(key).version(new_version).getOne().getContent()
    _normalize_docs([doc])
    assert doc == new_content
    assert coll.find().key(key).version(version).remove() == 0
    assert coll.find().key(key).version(new_version).remove() == 1
    assert coll.find().count() == 0
    conn.commit()


def test_3411(soda_db, conn):
    "3411 - test keys with GetCursor"
    coll = soda_db.createCollection("TestKeysWithGetCursor")
    values_to_insert = [
        {"name": "John", "address": {"city": "Bangalore"}},
        {"name": "Johnson", "address": {"city": "Banaras"}},
        {"name": "Joseph", "address": {"city": "Mangalore"}},
        {"name": "Jibin", "address": {"city": "Secunderabad"}},
        {"name": "Andrew", "address": {"city": "Hyderabad"}},
        {"name": "Matthew", "address": {"city": "Mumbai"}},
    ]
    docs = [coll.insertOneAndGet(value) for value in values_to_insert]
    keys = [docs[i].key for i in (2, 4, 5)]
    fetched_keys = [doc.key for doc in coll.find().keys(keys).getCursor()]
    assert list(sorted(fetched_keys)) == list(sorted(keys))
    conn.commit()


def test_3412(soda_db):
    "3412 - test createdOn attribute of Document"
    coll = soda_db.createCollection("CreatedOn")
    data = {"name": "John", "address": {"city": "Bangalore"}}
    doc = coll.insertOneAndGet(data)
    assert doc.createdOn == doc.lastModified


def test_3413(soda_db, conn, test_env):
    "3413 - test Soda truncate"
    if not test_env.has_client_version(20):
        pytest.skip("unsupported client")
    coll = soda_db.createCollection("TestTruncateDocs")
    values_to_insert = [
        {"name": "George", "age": 47},
        {"name": "Susan", "age": 39},
        {"name": "John", "age": 50},
        {"name": "Jill", "age": 54},
    ]
    for value in values_to_insert:
        coll.insertOne(value)
    conn.commit()
    assert coll.find().count() == len(values_to_insert)
    coll.truncate()
    assert coll.find().count() == 0


def test_3414(soda_db, cursor, test_env):
    "3414 - verify hints are reflected in the executed SQL statement"
    if not test_env.has_client_version(19, 11):
        pytest.skip("client version not supported")
    statement = """
            SELECT
                ( SELECT t2.sql_fulltext
                  FROM v$sql t2
                  WHERE t2.sql_id = t1.prev_sql_id
                    AND t2.child_number = t1.prev_child_number
                )
            FROM v$session t1
            WHERE t1.audsid = sys_context('userenv', 'sessionid')"""
    coll = soda_db.createCollection("TestSodaHint")
    values_to_insert = [
        {"name": "George", "age": 47},
        {"name": "Susan", "age": 39},
    ]
    coll.insertOneAndGet(values_to_insert[0], hint="MONITOR")
    cursor.execute(statement)
    (result,) = cursor.fetchone()
    assert "MONITOR" in result.read()

    coll.find().hint("MONITOR").getOne().getContent()
    cursor.execute(statement)
    (result,) = cursor.fetchone()
    assert "MONITOR" in result.read()

    coll.insertOneAndGet(values_to_insert[1], hint="NO_MONITOR")
    cursor.execute(statement)
    (result,) = cursor.fetchone()
    assert "NO_MONITOR" in result.read()


def test_3415(soda_db):
    "3415 - test error for invalid type for soda hint"
    coll = soda_db.createCollection("InvalidSodaHint")
    pytest.raises(
        TypeError, coll.insertOneAndGet, dict(name="Fred", age=16), hint=5
    )
    pytest.raises(
        TypeError,
        coll.insertManyAndGet,
        dict(name="George", age=25),
        hint=10,
    )
    pytest.raises(
        TypeError, coll.saveAndGet, dict(name="Sally", age=36), hint=5
    )
    pytest.raises(TypeError, coll.find().hint, 2)


def test_3416(soda_db):
    "3416 - test name and metadata attribute"
    collection_name = "TestCollectionMetadata"
    coll = soda_db.createCollection(collection_name)
    assert coll.name == collection_name
    assert coll.metadata["tableName"] == collection_name


def test_3417(soda_db, conn, test_env):
    "3417 - test insertMany"
    if not test_env.has_client_version(18, 5):
        pytest.skip("unsupported client")
    coll = soda_db.createCollection("TestInsertMany")
    values_to_insert = [
        dict(name="George", age=25),
        soda_db.createDocument(dict(name="Lucas", age=47)),
    ]
    coll.insertMany(values_to_insert)
    conn.commit()
    fetched_values = [doc.getContent() for doc in coll.find().getCursor()]
    fetched_values.sort(key=lambda x: x["name"])
    for fetched_val, expected_val in zip(fetched_values, values_to_insert):
        if not isinstance(expected_val, dict):
            expected_val = expected_val.getContent()
        assert fetched_val == fetched_val
    with test_env.assert_raises_full_code("DPI-1031"):
        coll.insertMany([])


def test_3418(skip_if_save_not_supported, soda_db, conn, test_env):
    "3418 - test save"
    coll = soda_db.createCollection("TestSodaSave")
    values_to_save = [
        dict(name="Jill", age=37),
        soda_db.createDocument(dict(name="John", age=7)),
        soda_db.createDocument(dict(name="Charles", age=24)),
    ]
    for value in values_to_save:
        coll.save(value)
    conn.commit()
    fetched_docs = coll.find().getDocuments()
    for fetched_doc, expected_doc in zip(fetched_docs, values_to_save):
        if isinstance(expected_doc, dict):
            expected_doc = soda_db.createDocument(expected_doc)
        assert fetched_doc.getContent() == expected_doc.getContent()


def test_3419(skip_if_save_not_supported, soda_db, cursor, test_env):
    "3419 - test saveAndGet with hint"
    statement = """
            SELECT
                ( SELECT t2.sql_fulltext
                  FROM v$sql t2
                  WHERE t2.sql_id = t1.prev_sql_id
                    AND t2.child_number = t1.prev_child_number
                )
            FROM v$session t1
            WHERE t1.audsid = sys_context('userenv', 'sessionid')"""
    coll = soda_db.createCollection("TestSodaSaveWithHint")

    values_to_save = [
        dict(name="Jordan", age=59),
        dict(name="Curry", age=34),
    ]
    hints = ["MONITOR", "NO_MONITOR"]
    for value, hint in zip(values_to_save, hints):
        coll.saveAndGet(value, hint=hint)
        coll.find().hint(hint).getOne().getContent()
        cursor.execute(statement)
        (result,) = cursor.fetchone()
        assert hint in result.read()


def test_3420(skip_if_save_not_supported, soda_db, conn):
    "3420 - test saveAndGet"
    coll = soda_db.createCollection("TestSodaSaveAndGet")
    values_to_save = [
        dict(name="John", age=50),
        soda_db.createDocument(dict(name="Mark", age=45)),
        soda_db.createDocument(dict(name="Jill", age=32)),
    ]
    inserted_keys = []
    for value in values_to_save:
        doc = coll.saveAndGet(value)
        inserted_keys.append(doc.key)
    fetched_docs = coll.find().getDocuments()
    conn.commit()
    assert coll.find().count() == len(values_to_save)
    for key, fetched_doc in zip(inserted_keys, fetched_docs):
        doc = coll.find().key(key).getOne()
        assert doc.getContent() == fetched_doc.getContent()


def test_3421(soda_db, conn, test_env):
    "3421 - test insert many and get"
    if not test_env.has_client_version(18, 5):
        pytest.skip("unsupported client")
    for name in soda_db.getCollectionNames():
        soda_db.openCollection(name).drop()
    coll = soda_db.createCollection("TestInsertManyAndGet")
    values_to_insert = [
        dict(name="George", age=25),
        soda_db.createDocument(dict(name="Lucas", age=47)),
    ]
    docs = coll.insertManyAndGet(values_to_insert)
    inserted_keys = [doc.key for doc in docs]
    conn.commit()
    assert coll.find().count() == len(values_to_insert)
    for key, expected_doc in zip(inserted_keys, values_to_insert):
        if isinstance(expected_doc, dict):
            expected_doc = soda_db.createDocument(expected_doc)
        doc = coll.find().key(key).getOne().getContent()
        _normalize_docs([doc])
        assert doc == expected_doc.getContent()


def test_3422(soda_db, test_env):
    "3422 - close document cursor and confirm exception is raised"
    coll = soda_db.createCollection("TestCloseSodaDocCursor")
    cursor = coll.find().getCursor()
    cursor.close()
    with test_env.assert_raises_full_code("DPY-1006"):
        cursor.close()
    with test_env.assert_raises_full_code("DPY-1006"):
        next(cursor)


def test_3423(soda_db, conn):
    "3423 - test limit to get specific amount of documents"
    coll = soda_db.createCollection("TestSodaLimit")
    values_to_insert = [{"group": "Camila"} for i in range(20)]
    coll.insertMany(values_to_insert)
    conn.commit()
    docs = coll.find().getDocuments()
    assert len(docs) == len(values_to_insert)
    docs = coll.find().limit(3).getDocuments()
    assert len(docs) == 3


def test_3424(soda_db, conn, test_env):
    "3424 - get count exceptions when using limit and skip"
    coll = soda_db.createCollection("TestSodaCountExceptions")
    data = [{"song": "WYMCA"} for i in range(20)]
    coll.insertMany(data)
    conn.commit()
    with test_env.assert_raises_full_code("ORA-40748"):
        coll.find().limit(5).count()
    with test_env.assert_raises_full_code("ORA-40748"):
        coll.find().skip(10).count()


def test_3425(skip_if_map_mode_not_supported, soda_db, conn, test_env):
    "3425 - test mapMode parameter"
    data = [{"price": 4900}, {"price": 8}]
    expected_data = data * 2

    original_coll = soda_db.createCollection("TestCollMapMode")
    original_coll.insertMany(data)
    mapped_coll = soda_db.createCollection("TestCollMapMode", mapMode=True)
    mapped_coll.insertMany(data)

    for coll in [original_coll, mapped_coll]:
        fetched_data = list(
            doc.getContent() for doc in coll.find().getDocuments()
        )
        _normalize_docs(fetched_data)
        assert fetched_data == expected_data
        with test_env.assert_raises_full_code("ORA-40626"):
            coll.drop()
    conn.commit()
    assert original_coll.drop()
    assert not mapped_coll.drop()


def test_3426(skip_if_map_mode_not_supported, soda_db, test_env):
    "3426 - test mapping a new collection from an non-existent table"
    with test_env.assert_raises_full_code("ORA-40623"):
        soda_db.createCollection("TestSodaMapNonExistent", mapMode=True)


def test_3427(soda_db):
    "3427 - test negative cases for SodaOperation methods"
    coll = soda_db.createCollection("TestSodaOperationNegative")
    pytest.raises(TypeError, coll.find().filter, 5)
    pytest.raises(TypeError, coll.find().key, 2)
    pytest.raises(TypeError, coll.find().keys, [1, 2, 3])
    pytest.raises(TypeError, coll.find().skip, "word")
    pytest.raises(TypeError, coll.find().skip, -5)
    pytest.raises(TypeError, coll.find().version, 1971)
    pytest.raises(TypeError, coll.find().limit, "a word")


def test_3428(soda_db, conn, round_trip_checker, test_env):
    "3428 - test fetchArraySize"
    if not test_env.has_client_version(19, 5):
        pytest.skip("unsupported client")
    coll = soda_db.createCollection("TestSodaFetchArraySize")
    for i in range(90):
        coll.insertOne({"name": "Emmanuel", "age": i + 1})
    conn.commit()

    # setting array size to 0 will use the default value of 100
    # requires a single round-trip
    round_trip_checker.get_value()
    coll.find().fetchArraySize(0).getDocuments()
    assert round_trip_checker.get_value() == 1

    # setting array size to 1 requires a round-trip for each SodaDoc
    coll.find().fetchArraySize(1).getDocuments()
    assert round_trip_checker.get_value() == 91

    # setting array size to 20 requires 5 round-trips
    coll.find().fetchArraySize(20).getDocuments()
    assert round_trip_checker.get_value() == 5

    # getting a SodaDocCursor requires a round-trip
    coll.find().fetchArraySize(0).getCursor()
    assert round_trip_checker.get_value() == 1

    # setting array size to 1 and iterating the SodaDocCursor requires a
    # round-trip for each SodaDoc
    soda_doc_cursor = coll.find().fetchArraySize(1).getCursor()
    for soda_doc in soda_doc_cursor:
        continue
    assert round_trip_checker.get_value() == 91

    # setting array size to 50 and iterating the SodaDocCursor requires
    # two round-trips
    soda_doc_cursor = coll.find().fetchArraySize(50).getCursor()
    for soda_doc in soda_doc_cursor:
        continue
    assert round_trip_checker.get_value() == 2

    # check a few negative scenarios
    pytest.raises(TypeError, coll.find().fetchArraySize, "Mijares")
    pytest.raises(TypeError, coll.find().fetchArraySize, -1)


def test_3429(soda_db, test_env):
    "3429 - test getting indexes on a collection"
    test_env.skip_unless_client_version(19, 13)
    coll = soda_db.createCollection("TestSodaListIndexes")
    index_1 = {
        "name": "ix_3428-1",
        "fields": [
            {"path": "address.city", "datatype": "string", "order": "asc"}
        ],
    }
    index_2 = {
        "name": "ix_3428-2",
        "fields": [
            {
                "path": "address.postal_code",
                "datatype": "string",
                "order": "asc",
            }
        ],
    }
    assert coll.listIndexes() == []
    coll.createIndex(index_1)
    coll.createIndex(index_2)
    indexes = coll.listIndexes()
    indexes.sort(key=lambda x: x["name"])
    assert indexes[0]["fields"][0]["path"] == "address.city"
    assert indexes[1]["fields"][0]["path"] == "address.postal_code"


def test_3430(soda_db, test_env):
    "3430 - test locking documents on fetch"
    if not test_env.has_client_version(19, 11):
        pytest.skip("unsupported client")
    coll = soda_db.createCollection("TestSodaLockDocs")
    values_to_insert = [
        {"name": "Bob", "age": 46},
        {"name": "Barb", "age": 45},
        {"name": "Sandy", "age": 47},
    ]
    coll.insertMany(values_to_insert)
    coll.find().lock().getDocuments()


def test_3431(soda_db):
    "3431 - test that drop returns the correct boolean"
    coll = soda_db.createCollection("TestDropCollection")
    assert coll.drop()

    # the collection has already been dropped
    assert not coll.drop()


def test_3432(skip_if_map_mode_not_supported, soda_db):
    "3432 - test drop with an empty mapped collection"
    original_coll = soda_db.createCollection("TestDropMapMode")
    mapped_coll = soda_db.createCollection("TestDropMapMode", mapMode=True)
    assert mapped_coll.drop()
    assert not original_coll.drop()


def test_3433(soda_db, conn):
    "3433 - test that replaceOne() returns a correct boolean"
    coll = soda_db.createCollection("TestReplaceDocReturns")
    doc = coll.insertOneAndGet({"address": {"city": "Sydney"}})

    new_content = {"address": {"city": "Melbourne"}}
    assert coll.find().key(doc.key).replaceOne(new_content)

    unregistered_key = "DB4A2628F1E0985C891F3F4836"
    assert not coll.find().key(unregistered_key).replaceOne(new_content)
    conn.commit()


def test_3434(soda_db, test_env):
    "3434 - replaceOne() and replaceOneAndGet() with invalid scenarios"
    coll = soda_db.createCollection("TestReplaceOneNegative")
    coll.insertMany([{"Wisdom": 1.7} for d in range(2)])
    keys = [d.key for d in coll.find().getDocuments()]
    with test_env.assert_raises_full_code("ORA-40734"):
        coll.find().keys(keys).replaceOne({"data": "new"})
    with test_env.assert_raises_full_code("ORA-40734"):
        coll.find().keys(keys).replaceOneAndGet({"data": "new"})


def test_3435(soda_db, test_env):
    "3435 - test writting a read-only collection"
    if not test_env.has_client_version(19, 9):
        pytest.skip("client version not supported")

    metadata = {
        "readOnly": True,
    }
    coll = soda_db.createCollection("TestCollReadOnly", metadata)

    methods = [
        coll.insertOne,
        coll.insertOneAndGet,
        coll.insertMany,
        coll.insertManyAndGet,
        coll.save,
        coll.saveAndGet,
    ]
    for method in methods:
        with test_env.assert_raises_full_code("ORA-40663"):
            method({"Song 1": "No end"})


def test_3436(soda_db):
    "3436 - createCollection() with the same name and metadata"
    coll_name = "TestCollSameMetadata"
    coll1 = soda_db.createCollection(coll_name, {"readOnly": True})
    coll2 = soda_db.createCollection(coll_name, {"readOnly": True})
    assert coll1.drop()
    assert not coll2.drop()


def test_3437(soda_db, test_env):
    "3437 - createCollection() with the same name but different metadata"
    coll_name = "TestCollDifferentMetadata"
    coll = soda_db.createCollection(coll_name)
    with test_env.assert_raises_full_code("ORA-40669"):
        soda_db.createCollection(coll_name, {"readOnly": False})
    coll.drop()

    coll = soda_db.createCollection(coll_name, {"readOnly": True})
    with test_env.assert_raises_full_code("ORA-40669"):
        soda_db.createCollection(coll_name, {"readOnly": False})


def test_3438(soda_db, conn, test_env):
    "3438 - test getDataGuide() with an index with data-guide support"
    coll = soda_db.createCollection("TestSodaDataGuideEnabled")
    data = [
        {
            "team": "backend",
            "created_in": 2001,
            "members": [{"developer": "Joseph"}, {"tester": "Mark"}],
        },
        {"team": "frontend", "area": "user interface"},
    ]
    coll.insertMany(data)
    conn.commit()
    index = {
        "name": "ix_3438",
        "dataguide": "on",
    }
    coll.createIndex(index)

    data_guide = coll.getDataGuide().getContent()
    if test_env.has_client_and_server_version(23, 4):
        assert data_guide["properties"]["_id"]["type"] == "id"

    values = [
        ("team", "string"),
        ("created_in", "number"),
        ("area", "string"),
    ]
    for name, typ in values:
        assert data_guide["properties"][name]["type"] == typ
        regex = f"(JSON_DOCUMENT|DATA)\\${name}"
        val = data_guide["properties"][name]["o:preferred_column_name"]
        assert re.fullmatch(regex, val) is not None

    members_values = [
        ("tester", "string", 4),
        ("developer", "string", 8),
    ]
    for name, typ, length in members_values:
        members_items = data_guide["properties"]["members"]["items"]
        assert members_items["properties"][name]["type"] == typ
        assert members_items["properties"][name]["o:length"] == length
        regex = f"(JSON_DOCUMENT|DATA)\\${name}"
        val = members_items["properties"][name]["o:preferred_column_name"]
        assert re.fullmatch(regex, val) is not None


def test_3439(soda_db, conn, test_env):
    "3439 - test getDataGuide() with an index without data-guide support"
    coll = soda_db.createCollection("TestSodaDataGuideDisabled")

    coll.insertOne({"data": "test_3439"})
    conn.commit()
    index = {
        "name": "ix-3439",
        "dataguide": "off",
    }
    coll.createIndex(index)
    with test_env.assert_raises_full_code("ORA-40582"):
        coll.getDataGuide()


def test_3440(soda_db):
    "3440 - test getDataGuide() with an empty collection"
    coll = soda_db.createCollection("TestDataGuideWithEmptyColl")
    coll.createIndex({"name": "ix_3440", "dataguide": "on"})
    assert coll.getDataGuide() is None


def test_3441(soda_db, test_env):
    "3441 - test getDataGuide() without a json search index"
    coll = soda_db.createCollection("TestSodaDataGuideWithoutIndex")
    with test_env.assert_raises_full_code("ORA-40582"):
        coll.getDataGuide()


def test_3442(soda_db, conn, test_env):
    "3442 - test mapMode parameter with metadata"
    data = [{"price": 4900}, {"price": 8}]
    expected_data = data * 2
    coll_name = "TestCollOriginal"

    metadata = {
        "tableName": coll_name,
        "keyColumn": {"name": "ID"},
        "contentColumn": {"name": "JSON_DOCUMENT", "sqlType": "BLOB"},
        "versionColumn": {"name": "VERSION", "method": "UUID"},
        "lastModifiedColumn": {"name": "LAST_MODIFIED"},
        "creationTimeColumn": {"name": "CREATED_ON"},
    }

    original_coll = soda_db.createCollection(coll_name, metadata=metadata)
    original_coll.insertMany(data)
    mapped_coll = soda_db.createCollection(
        "TestCollMapMode", metadata=metadata, mapMode=True
    )
    mapped_coll.insertMany(data)

    for coll in [original_coll, mapped_coll]:
        fetched_data = list(
            doc.getContent() for doc in coll.find().getDocuments()
        )
        _normalize_docs(fetched_data)
        assert fetched_data == expected_data

    with test_env.assert_raises_full_code("ORA-40626"):
        original_coll.drop()
    assert mapped_coll.drop()
    conn.commit()
    assert original_coll.drop()
    assert not mapped_coll.drop()


def test_3443(soda_db, test_env):
    "3443 - test mapping a new collection from an non-existent table"
    metadata = {"tableName": "TestNone"}
    with test_env.assert_raises_full_code("ORA-40623"):
        soda_db.createCollection(
            "TestSodaMapNonExistent", metadata=metadata, mapMode=True
        )


def test_3444(soda_db):
    "3444 - test collections with mixture of media types"
    metadata = dict(mediaTypeColumn=dict(name="media_type"))
    coll = soda_db.createCollection("TestMixedMedia", metadata=metadata)
    test_data = [
        (dict(name="George", age=28), "application/json"),
        ("Sample Text", "text/plain"),
        (b"\x57\x25\xfe\x34\x56", "application/octet-stream"),
    ]
    for value, media_type in test_data:
        coll.find().remove()
        coll.insertOne(soda_db.createDocument(value, mediaType=media_type))
        fetched_doc = coll.find().getDocuments()[0]
        assert fetched_doc.mediaType == media_type
        if media_type == "application/json":
            assert fetched_doc.getContent() == value
            assert json.loads(fetched_doc.getContentAsString()) == value
            as_bytes = fetched_doc.getContentAsBytes().decode()
            assert json.loads(as_bytes) == value
        elif media_type == "text/plain":
            assert fetched_doc.getContent() == value.encode()
            assert fetched_doc.getContentAsString() == value
            assert fetched_doc.getContentAsBytes() == value.encode()
        else:
            assert fetched_doc.getContent() == value
            assert fetched_doc.getContentAsBytes() == value
            pytest.raises(UnicodeDecodeError, fetched_doc.getContentAsString)


def test_3445(soda_db, test_env):
    "3445 - test fetching documents with JSON data using extended types"
    if not test_env.has_client_and_server_version(23, 4):
        pytest.skip("unsupported data types")

    val = {
        "testKey1": "testValue1",
        "testKey2": decimal.Decimal("12.78"),
        "testKey3": datetime.datetime(2023, 7, 3, 11, 10, 24),
    }
    doc = soda_db.createDocument(val)
    assert doc.getContent() == val
    coll = soda_db.createCollection("TestJSONExtendedTypes")
    coll.insertOne(doc)
    fetched_doc = coll.find().getDocuments()[0]
    fetched_content = fetched_doc.getContent()
    _normalize_docs([fetched_content])
    assert fetched_content == val
    assert doc.getContent() == val


def test_3446(soda_db, conn, test_env):
    "3446 - test round-trip of JsonId"
    if not test_env.has_client_and_server_version(23, 4):
        pytest.skip("unsupported data types")
    coll = soda_db.createCollection("TestJsonId")
    val = {
        "key1": 5,
        "key2": "A string",
        "key3": b"Raw data",
        "key4": datetime.datetime(2024, 3, 2, 10, 1, 36),
    }
    doc = soda_db.createDocument(val)
    coll.insertOne(doc)
    conn.commit()
    fetched_doc = coll.find().getDocuments()[0]
    fetched_content = fetched_doc.getContent()
    assert type(fetched_content["_id"]) is oracledb.JsonId
    updated_val = val.copy()
    updated_val["key1"] = 25
    content = fetched_content.copy()
    content["key1"] = updated_val["key1"]
    updated_doc = soda_db.createDocument(content)
    coll.find().key(fetched_doc.key).replaceOne(updated_doc)
    fetched_doc = coll.find().getDocuments()[0]
    assert fetched_doc.getContent() == content


def test_3447(soda_db):
    "3447 - test getting documents with client-assigned keys"
    metadata = {"keyColumn": {"assignmentMethod": "client"}}
    coll = soda_db.createCollection("TestSearchByClientAssignedKeys", metadata)
    test_values = [
        ("doc1", {"name": "Help others", "files": []}),
        ("doc2", {"name": "Family", "files": ["kids.txt"]}),
        ("doc3", {"name": "Our pets", "files": ["dogs.pdf"]}),
    ]
    docs = [soda_db.createDocument(d, k) for k, d in test_values]
    coll.insertMany(docs)

    for key, data in test_values:
        (fetched_doc,) = coll.find().key(key).getDocuments()
        assert fetched_doc.getContent() == data

    keys = [key for key, _ in test_values]
    fetched_docs = coll.find().keys(keys).getDocuments()
    assert len(fetched_docs) == 3
