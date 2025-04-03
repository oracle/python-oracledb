# -----------------------------------------------------------------------------
# json_insert.py (Section 8.1)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Copyright (c) 2025, Oracle and/or its affiliates.
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
import db_config

con = oracledb.connect(
    user=db_config.user, password=db_config.pw, dsn=db_config.dsn
)
cur = con.cursor()

# Insert JSON data
data = dict(name="Rod", dept="Sales", location="Germany")
inssql = "insert into jtab (id, json_data) values (:1, :2)"
cur.setinputsizes(None, oracledb.DB_TYPE_JSON)
cur.execute(inssql, [101, data])

# Select JSON data
sql = "select c.json_data from jtab c"
for (j,) in cur.execute(sql):
    print(j)

# Dot-notation to extract a value from a JSON column
sql = """select c.json_data.location
         from jtab c
         offset 0 rows fetch next 1 rows only"""
for (j,) in cur.execute(sql):
    print(j)
