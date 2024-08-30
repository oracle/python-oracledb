# -----------------------------------------------------------------------------
# Copyright (c) 2024, Oracle and/or its affiliates.
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
1000 - Module for static type checking of the cursor module.
"""

import oracledb


def stc_1000(cursor: oracledb.Cursor):
    cursor.execute(None, parameters=None)
    cursor.execute("sql", parameters=None)
    cursor.execute("sql", parameters=[1, 2, 3])
    cursor.execute("sql", parameters=(1, 2, 3))
    cursor.execute("sql", parameters=dict(arg1=5, arg2=6))


def stc_1001(cursor: oracledb.Cursor):
    cursor.callproc("name", parameters=None)
    cursor.callproc("name", parameters=(1, 2, 3))
    cursor.callproc("name", parameters=[1, 2, 3])
    cursor.callproc("name", keyword_parameters=None)
    cursor.callproc("name", keyword_parameters=dict(arg1=5, arg2=6))
    cursor.callproc("name", keywordParameters=None)
    cursor.callproc("name", keywordParameters=dict(arg1=5, arg2=6))


def stc_1002(cursor: oracledb.Cursor):
    cursor.callfunc("name", str, parameters=None)
    cursor.callfunc("name", str, parameters=(1, 2, 3))
    cursor.callfunc("name", str, parameters=[1, 2, 3])
    cursor.callfunc("name", str, keyword_parameters=None)
    cursor.callfunc("name", str, keyword_parameters=dict(arg1=5, arg2=6))
    cursor.callfunc("name", str, keywordParameters=None)
    cursor.callfunc("name", str, keywordParameters=dict(arg1=5, arg2=6))


def stc_1003(cursor: oracledb.Cursor):
    cursor.executemany(None, [(1, 2, 3), (4, 5, 6)])
    cursor.executemany("sql", [(1, 2, 3), (4, 5, 6)])
    cursor.executemany("sql", 8)


def stc_1004(cursor: oracledb.Cursor):
    cursor.fetchmany(size=None)
    cursor.fetchmany(size=5)
    cursor.fetchmany(numRows=None)
    cursor.fetchmany(numRows=5)


async def stc_1005(cursor: oracledb.AsyncCursor):
    await cursor.callfunc("name", str, parameters=None)
    await cursor.callfunc("name", str, parameters=(1, 2, 3))
    await cursor.callfunc("name", str, parameters=[1, 2, 3])
    await cursor.callfunc("name", str, keyword_parameters=None)
    await cursor.callfunc("name", str, keyword_parameters=dict(arg1=5, arg2=6))


async def stc_1006(cursor: oracledb.AsyncCursor):
    await cursor.callproc("name", parameters=None)
    await cursor.callproc("name", parameters=(1, 2, 3))
    await cursor.callproc("name", parameters=[1, 2, 3])
    await cursor.callproc("name", keyword_parameters=None)
    await cursor.callproc("name", keyword_parameters=dict(arg1=5, arg2=6))


async def stc_1007(cursor: oracledb.AsyncCursor):
    await cursor.execute(None, parameters=None)
    await cursor.execute("sql", parameters=None)
    await cursor.execute("sql", parameters=[1, 2, 3])
    await cursor.execute("sql", parameters=(1, 2, 3))
    await cursor.execute("sql", parameters=dict(arg1=5, arg2=6))


async def stc_1008(cursor: oracledb.AsyncCursor):
    await cursor.executemany(None, [(1, 2, 3), (4, 5, 6)])
    await cursor.executemany("sql", [(1, 2, 3), (4, 5, 6)])
    await cursor.executemany("sql", 8)


async def stc_1009(cursor: oracledb.AsyncCursor):
    await cursor.fetchmany(size=None)
    await cursor.fetchmany(size=5)
