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
2000 - Module for testing long and long raw variables
"""

import unittest

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    def __perform_test(self, typ):
        name_part = "Long" if typ is oracledb.DB_TYPE_LONG else "LongRaw"

        self.cursor.execute(f"truncate table Test{name_part}s")
        self.cursor.setinputsizes(long_string=typ)
        long_string = ""
        for i in range(1, 11):
            char = chr(ord("A") + i - 1)
            long_string += char * 25000
            if i % 3 == 1:
                bind_value = None
            else:
                if typ is oracledb.DB_TYPE_LONG_RAW:
                    bind_value = long_string.encode()
                else:
                    bind_value = long_string
            self.cursor.execute(
                f"""
                insert into Test{name_part}s (IntCol, {name_part}Col)
                values (:integer_value, :long_string)
                """,
                integer_value=i,
                long_string=bind_value,
            )
        self.conn.commit()
        self.cursor.execute(f"select * from Test{name_part}s order by IntCol")
        long_string = ""
        for integer_value, fetched_value in self.cursor:
            char = chr(ord("A") + integer_value - 1)
            long_string += char * 25000
            if integer_value % 3 == 1:
                expected_value = None
            else:
                if typ is oracledb.DB_TYPE_LONG_RAW:
                    expected_value = long_string.encode()
                else:
                    expected_value = long_string
            if fetched_value is not None:
                self.assertEqual(len(fetched_value), integer_value * 25000)
            self.assertEqual(fetched_value, expected_value)

    def test_2000(self):
        "2000 - test binding and fetching long data"
        self.__perform_test(oracledb.DB_TYPE_LONG)

    def test_2001(self):
        "2001 - test binding long data with executemany()"
        data = []
        self.cursor.execute("truncate table TestLongs")
        for i in range(5):
            char = chr(ord("A") + i)
            long_str = char * (32768 * (i + 1))
            data.append((i + 1, long_str))
        self.cursor.executemany("insert into TestLongs values (:1, :2)", data)
        self.conn.commit()
        self.cursor.execute("select * from TestLongs order by IntCol")
        self.assertEqual(self.cursor.fetchall(), data)

    def test_2002(self):
        "2002 - test binding and fetching long raw data"
        self.__perform_test(oracledb.DB_TYPE_LONG_RAW)

    def test_2003(self):
        "2003 - test cursor description is accurate for longs"
        self.cursor.execute("select * from TestLongs")
        expected_value = [
            ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
            ("LONGCOL", oracledb.DB_TYPE_LONG, None, None, None, None, True),
        ]
        self.assertEqual(self.cursor.description, expected_value)

    def test_2004(self):
        "2004 - test cursor description is accurate for long raws"
        self.cursor.execute("select * from TestLongRaws")
        expected_value = [
            ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
            (
                "LONGRAWCOL",
                oracledb.DB_TYPE_LONG_RAW,
                None,
                None,
                None,
                None,
                True,
            ),
        ]
        self.assertEqual(self.cursor.description, expected_value)

    @unittest.skipIf(test_env.get_is_thin(), "not relevant for thin mode")
    def test_2005(self):
        "2005 - test array size too large generates an exception"
        self.cursor.arraysize = 268435456
        with self.assertRaisesFullCode("DPI-1015"):
            self.cursor.execute("select * from TestLongRaws")


if __name__ == "__main__":
    test_env.run_test_cases()
