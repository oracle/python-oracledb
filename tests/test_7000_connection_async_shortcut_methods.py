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
7000 - Module for testing async connections shortcut methods
"""

import unittest

import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):

    async def test_7700(self):
        "7700 - test execute()"
        await self.conn.execute("truncate table TestTempTable")
        await self.conn.execute(
            "insert into TestTempTable (IntCol) values (:1)", [77]
        )
        await self.conn.execute(
            "insert into TestTempTable (IntCol) values (:val)", dict(val=15)
        )
        await self.conn.commit()

        res = await self.conn.fetchall(
            "select IntCol from TestTempTable order by IntCol"
        )
        self.assertEqual(res, [(15,), (77,)])

    async def test_7701(self):
        "7701 - test fetchall()"
        await self.conn.execute("truncate table TestTempTable")
        data = [(2,), (3,)]
        await self.conn.executemany(
            "insert into TestTempTable (IntCol) values (:1)", data
        )
        res = await self.conn.fetchall(
            "select IntCol from TestTempTable order by IntCol"
        )
        self.assertEqual(res, data)

    async def test_7702(self):
        "7702 - test fetchall() with arraysize"
        await self.conn.execute("truncate table TestTempTable")
        await self.conn.executemany(
            "insert into TestTempTable (IntCol) values (:value)",
            [{"value": i} for i in range(3)],
        )
        await self.conn.commit()
        res = await self.conn.fetchall(
            "select IntCol from TestTempTable order by IntCol", arraysize=1
        )
        self.assertEqual(res, [(0,), (1,), (2,)])

    async def test_7703(self):
        "7703 - test fetchall() with rowfactory"
        await self.conn.execute("truncate table TestTempTable")
        await self.conn.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (1, 'test_7703')
            """
        )
        await self.conn.commit()

        column_names = ["INTCOL", "STRINGCOL1"]

        def rowfactory(*row):
            return dict(zip(column_names, row))

        res = await self.conn.fetchall(
            "select IntCol, StringCol1 from TestTempTable",
            rowfactory=rowfactory,
        )
        expected_value = [{"INTCOL": 1, "STRINGCOL1": "test_7703"}]
        self.assertEqual(res, expected_value)

    async def test_7704(self):
        "7704 - test executemany()"
        await self.conn.execute("truncate table TestTempTable")
        await self.conn.executemany(
            "insert into TestTempTable (IntCol) values (:1)", [(1,), (2,)]
        )
        await self.conn.executemany(
            "insert into TestTempTable (IntCol) values (:value)",
            [{"value": 3}, {"value": 4}],
        )
        await self.conn.commit()
        res = await self.conn.fetchall(
            "select IntCol from TestTempTable order by IntCol"
        )
        self.assertEqual(res, [(1,), (2,), (3,), (4,)])

    async def test_7705(self):
        "7705 - test fetchone()"
        await self.conn.execute("truncate table TestTempTable")
        await self.conn.executemany(
            "insert into TestTempTable (IntCol) values (:1)", [(9,), (10,)]
        )
        await self.conn.commit()

        res = await self.conn.fetchone(
            "select IntCol from TestTempTable order by IntCol"
        )
        self.assertEqual(res, (9,))

        res = await self.conn.fetchone("select :1 from dual", [23])
        self.assertEqual(res, (23,))

        res = await self.conn.fetchone("select :val from dual", {"val": 5})
        self.assertEqual(res, (5,))

    async def test_7706(self):
        "7706 - test fetchmany()"
        data = [(i,) for i in range(10)]
        await self.conn.execute("truncate table TestTempTable")
        await self.conn.executemany(
            "insert into TestTempTable (IntCol) values (:1)", data
        )
        await self.conn.commit()
        res = await self.conn.fetchmany(
            "select IntCol from TestTempTable order by IntCol",
            num_rows=3,
        )
        self.assertEqual(res, data[:3])


if __name__ == "__main__":
    test_env.run_test_cases()
