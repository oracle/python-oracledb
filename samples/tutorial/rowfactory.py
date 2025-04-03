# -----------------------------------------------------------------------------
# rowfactory.py (Section 10.1)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Copyright (c) 2017, 2025, Oracle and/or its affiliates.
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

import collections
import oracledb
import db_config

con = oracledb.connect(
    user=db_config.user, password=db_config.pw, dsn=db_config.dsn
)
cur = con.cursor()

cur.execute("select deptno, dname from dept")
res = cur.fetchall()

print("Array indexes:")
for row in res:
    print(row[0], "->", row[1])

print("Loop target variables:")
for c1, c2 in res:
    print(c1, "->", c2)
