# -----------------------------------------------------------------------------
# soda.py (Section 15.2)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Copyright (c) 2019, 2023, Oracle and/or its affiliates.
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

import oracledb
import db_config_thick as db_config

con = oracledb.connect(
    user=db_config.user, password=db_config.pw, dsn=db_config.dsn
)

soda = con.getSodaDatabase()

# Explicit metadata is used for maximum version portability
metadata = {
    "keyColumn": {"name": "ID"},
    "contentColumn": {"name": "JSON_DOCUMENT", "sqlType": "BLOB"},
    "versionColumn": {"name": "VERSION", "method": "UUID"},
    "lastModifiedColumn": {"name": "LAST_MODIFIED"},
    "creationTimeColumn": {"name": "CREATED_ON"},
}

collection = soda.createCollection("friends", metadata)

content = {"name": "Jared", "age": 35, "address": {"city": "Melbourne"}}

doc = collection.insertOneAndGet(content)
key = doc.key

doc = collection.find().key(key).getOne()
content = doc.getContent()
print("Retrieved SODA document dictionary is:")
print(content)

my_docs = [
    {"name": "Gerald", "age": 21, "address": {"city": "London"}},
    {"name": "David", "age": 28, "address": {"city": "Melbourne"}},
    {"name": "Shawn", "age": 20, "address": {"city": "San Francisco"}},
]
collection.insertMany(my_docs)

filter_spec = {"address.city": "Melbourne"}
my_documents = collection.find().filter(filter_spec).getDocuments()

print("Melbourne people:")
for doc in my_documents:
    print(doc.getContent()["name"])

filter_spec = {"age": {"$lt": 25}}
my_documents = collection.find().filter(filter_spec).getDocuments()

print("Young people:")
for doc in my_documents:
    print(doc.getContent()["name"])
