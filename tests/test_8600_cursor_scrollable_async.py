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

"""
8600 - Module for testing scrollable cursors with asyncio
"""

import unittest

import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    async def test_8600(self):
        "8600 - test creating a scrollable cursor"
        cursor = self.conn.cursor()
        self.assertEqual(cursor.scrollable, False)
        cursor = self.conn.cursor(True)
        self.assertEqual(cursor.scrollable, True)
        cursor = self.conn.cursor(scrollable=True)
        self.assertEqual(cursor.scrollable, True)
        cursor.scrollable = False
        self.assertEqual(cursor.scrollable, False)

    async def test_8601(self):
        "8601 - test scrolling absolute yields an exception (after result set)"
        cursor = self.conn.cursor(scrollable=True)
        cursor.arraysize = self.cursor.arraysize
        await cursor.execute(
            "select NumberCol from TestNumbers order by IntCol"
        )
        with self.assertRaisesFullCode("DPY-2063"):
            await cursor.scroll(12, "absolute")

    async def test_8602(self):
        "8602 - test scrolling absolute (when in buffers)"
        cursor = self.conn.cursor(scrollable=True)
        cursor.prefetchrows = 0
        cursor.arraysize = self.cursor.arraysize
        await cursor.execute(
            "select NumberCol from TestNumbers order by IntCol"
        )
        await cursor.fetchmany()
        self.assertTrue(
            cursor.arraysize > 1,
            "array size must exceed 1 for this test to work correctly",
        )
        await cursor.scroll(1, mode="absolute")
        (value,) = await cursor.fetchone()
        self.assertEqual(value, 1.25)
        self.assertEqual(cursor.rowcount, 1)

    async def test_8603(self):
        "8603 - test scrolling absolute (when not in buffers)"
        cursor = self.conn.cursor(scrollable=True)
        cursor.arraysize = self.cursor.arraysize
        await cursor.execute(
            "select NumberCol from TestNumbers order by IntCol"
        )
        await cursor.scroll(6, mode="absolute")
        (value,) = await cursor.fetchone()
        self.assertEqual(value, 7.5)
        self.assertEqual(cursor.rowcount, 6)

    async def test_8604(self):
        "8604 - test scrolling to first row in result set (in buffers)"
        cursor = self.conn.cursor(scrollable=True)
        cursor.arraysize = self.cursor.arraysize
        cursor.prefetchrows = 0
        await cursor.execute(
            "select NumberCol from TestNumbers order by IntCol"
        )
        await cursor.fetchmany()
        await cursor.scroll(mode="first")
        (value,) = await cursor.fetchone()
        self.assertEqual(value, 1.25)
        self.assertEqual(cursor.rowcount, 1)

    async def test_8605(self):
        "8605 - test scrolling to first row in result set (not in buffers)"
        cursor = self.conn.cursor(scrollable=True)
        cursor.arraysize = self.cursor.arraysize
        cursor.prefetchrows = 0
        await cursor.execute(
            "select NumberCol from TestNumbers order by IntCol"
        )
        await cursor.fetchmany()
        await cursor.fetchmany()
        await cursor.scroll(mode="first")
        (value,) = await cursor.fetchone()
        self.assertEqual(value, 1.25)
        self.assertEqual(cursor.rowcount, 1)

    async def test_8606(self):
        "8606 - test scrolling to last row in result set"
        cursor = self.conn.cursor(scrollable=True)
        cursor.arraysize = self.cursor.arraysize
        await cursor.execute(
            "select NumberCol from TestNumbers order by IntCol"
        )
        await cursor.scroll(mode="last")
        (value,) = await cursor.fetchone()
        self.assertEqual(value, 12.5)
        self.assertEqual(cursor.rowcount, 10)

    async def test_8607(self):
        "8607 - test scrolling relative yields an exception (after result set)"
        cursor = self.conn.cursor(scrollable=True)
        cursor.arraysize = self.cursor.arraysize
        await cursor.execute(
            "select NumberCol from TestNumbers order by IntCol"
        )
        with self.assertRaisesFullCode("DPY-2063"):
            await cursor.scroll(15)

    async def test_8608(self):
        "8608 - test scrolling relative yields exception (before result set)"
        cursor = self.conn.cursor(scrollable=True)
        cursor.arraysize = self.cursor.arraysize
        await cursor.execute(
            "select NumberCol from TestNumbers order by IntCol"
        )
        with self.assertRaisesFullCode("DPY-2063"):
            await cursor.scroll(-5)

    async def test_8609(self):
        "8609 - test scrolling relative (when in buffers)"
        cursor = self.conn.cursor(scrollable=True)
        cursor.arraysize = self.cursor.arraysize
        cursor.prefetchrows = 0
        await cursor.execute(
            "select NumberCol from TestNumbers order by IntCol"
        )
        await cursor.fetchmany()
        message = "array size must exceed 1 for this test to work correctly"
        self.assertTrue(cursor.arraysize > 1, message)
        await cursor.scroll(2 - cursor.rowcount)
        (value,) = await cursor.fetchone()
        self.assertEqual(value, 2.5)
        self.assertEqual(cursor.rowcount, 2)

    async def test_8610(self):
        "8610 - test scrolling relative (when not in buffers)"
        cursor = self.conn.cursor(scrollable=True)
        cursor.arraysize = self.cursor.arraysize
        await cursor.execute(
            "select NumberCol from TestNumbers order by IntCol"
        )
        await cursor.fetchmany()
        await cursor.fetchmany()
        message = "array size must exceed 1 for this test to work correctly"
        self.assertTrue(cursor.arraysize > 1, message)
        await cursor.scroll(3 - cursor.rowcount)
        (value,) = await cursor.fetchone()
        self.assertEqual(value, 3.75)
        self.assertEqual(cursor.rowcount, 3)

    async def test_8611(self):
        "8611 - test scrolling when there are no rows"
        await self.cursor.execute("truncate table TestTempTable")
        cursor = self.conn.cursor(scrollable=True)
        await cursor.execute("select * from TestTempTable")
        await cursor.scroll(mode="last")
        self.assertEqual(await cursor.fetchall(), [])
        await cursor.scroll(mode="first")
        self.assertEqual(await cursor.fetchall(), [])
        with self.assertRaisesFullCode("DPY-2063"):
            await cursor.scroll(1, mode="absolute")

    async def test_8612(self):
        "8612 - test scrolling with differing array and fetch array sizes"
        await self.cursor.execute("truncate table TestTempTable")
        for i in range(30):
            await self.cursor.execute(
                """
                insert into TestTempTable (IntCol, StringCol1)
                values (:1, null)
                """,
                [i + 1],
            )
        for arraysize in range(1, 6):
            cursor = self.conn.cursor(scrollable=True)
            cursor.arraysize = arraysize
            await cursor.execute(
                "select IntCol from TestTempTable order by IntCol"
            )
            for num_rows in range(1, arraysize + 1):
                await cursor.scroll(15, "absolute")
                rows = await cursor.fetchmany(num_rows)
                self.assertEqual(rows[0][0], 15)
                self.assertEqual(cursor.rowcount, 15 + num_rows - 1)
                await cursor.scroll(9)
                rows = await cursor.fetchmany(num_rows)
                num_rows_fetched = len(rows)
                self.assertEqual(rows[0][0], 15 + num_rows + 8)
                self.assertEqual(
                    cursor.rowcount, 15 + num_rows + num_rows_fetched + 7
                )
                await cursor.scroll(-12)
                rows = await cursor.fetchmany(num_rows)
                count = 15 + num_rows + num_rows_fetched - 5
                self.assertEqual(rows[0][0], count)
                count = 15 + num_rows + num_rows_fetched + num_rows - 6
                self.assertEqual(cursor.rowcount, count)

    async def test_8613(self):
        "8613 - test calling scroll() with invalid mode"
        cursor = self.conn.cursor(scrollable=True)
        cursor.arraysize = self.cursor.arraysize
        await cursor.execute(
            "select NumberCol from TestNumbers order by IntCol"
        )
        await cursor.fetchmany()
        with self.assertRaisesFullCode("DPY-2009"):
            await cursor.scroll(mode="middle")

    async def test_8614(self):
        "8614 - test scroll after fetching all rows"
        cursor = self.conn.cursor(scrollable=True)
        cursor.arraysize = 5
        cursor.prefetchrows = 0
        await cursor.execute(
            "select NumberCol from TestNumbers order by IntCol"
        )
        await cursor.fetchall()
        await cursor.scroll(5, mode="absolute")
        (value,) = await cursor.fetchone()
        self.assertEqual(value, 6.25)
        self.assertEqual(cursor.rowcount, 5)


if __name__ == "__main__":
    test_env.run_test_cases()
