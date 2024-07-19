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
E2100 - Module for testing BFILE. No special setup is required but the tests
here will only be run if the local_database is enabled.
"""

import os
import tempfile
import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_extended_config_bool("local_database"),
    "extended configuration local_database is disabled",
)
class TestCase(test_env.BaseTestCase):
    dir_name = "EXT_TEST_2100_DIR"

    def _setup_directory(self, local_name):
        """
        Setups the directory using the given local name.
        """
        user = test_env.get_main_user()
        with test_env.get_admin_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    create or replace directory {self.dir_name}
                    as '{local_name}'
                    """
                )
                cursor.execute(
                    f"grant read on directory {self.dir_name} to {user}"
                )

    def test_ext_2100(self):
        "E2100 - test fileexists() and getfilename()"
        with tempfile.TemporaryDirectory() as temp_dir:
            self._setup_directory(temp_dir)
            file_name = "test_2100.txt"
            contents = b"Some arbitrary data for test 2100"
            with open(os.path.join(temp_dir, file_name), "wb") as f:
                f.write(contents)
            self.cursor.execute(
                "select bfilename(:1, :2) from dual",
                [self.dir_name, file_name],
            )
            (bfile,) = self.cursor.fetchone()
            self.assertEqual(bfile.read(), contents)
            self.assertTrue(bfile.fileexists())
            self.assertEqual(bfile.getfilename(), (self.dir_name, file_name))

    def test_ext_2101(self):
        "E2101 - test setfilename()"
        with tempfile.TemporaryDirectory() as temp_dir:
            self._setup_directory(temp_dir)
            file_name = "test_2101.txt"
            contents = b"Some arbitrary data for test 2101"
            new_file_name = "test_2101b.txt"
            new_contents = b"Some arbitrary different data for test 2101"
            with open(os.path.join(temp_dir, file_name), "wb") as f:
                f.write(contents)
            with open(os.path.join(temp_dir, new_file_name), "wb") as f:
                f.write(new_contents)
            self.cursor.execute(
                "select bfilename(:1, :2) from dual",
                [self.dir_name, file_name],
            )
            (bfile,) = self.cursor.fetchone()
            self.assertEqual(bfile.read(), contents)
            bfile.setfilename(self.dir_name, new_file_name)
            self.assertEqual(bfile.read(), new_contents)

    def test_ext_2102(self):
        "E2102 - test BFILE with LOB methods"
        with tempfile.TemporaryDirectory() as temp_dir:
            self._setup_directory(temp_dir)
            file_name = "test_2102.txt"
            contents = b"Some arbitrary data for test 2102"
            with open(os.path.join(temp_dir, file_name), "wb") as f:
                f.write(contents)
            self.cursor.execute(
                "select bfilename(:1, :2) from dual",
                [self.dir_name, file_name],
            )
            (bfile,) = self.cursor.fetchone()
            self.assertEqual(bfile.size(), len(contents))
            self.assertEqual(bfile.read(7), contents[6:])
            self.assertEqual(bfile.read(7, 2), contents[6:8])
            self.assertFalse(bfile.isopen())
            bfile.open()
            self.assertTrue(bfile.isopen())
            bfile.close()
            self.assertFalse(bfile.isopen())
            with self.assertRaisesFullCode("DPY-3025"):
                bfile.getchunksize()
            with self.assertRaisesFullCode("DPY-3025"):
                bfile.trim(1)
            with self.assertRaisesFullCode("DPY-3025"):
                bfile.write("1")

    def test_ext_2103(self):
        "E2103 - test binding a BFILE"
        with tempfile.TemporaryDirectory() as temp_dir:
            self._setup_directory(temp_dir)
            file_name = "test_2103.txt"
            contents = b"Some arbitrary data for test 2103"
            with open(os.path.join(temp_dir, file_name), "wb") as f:
                f.write(contents)
            self.cursor.execute(
                "select bfilename(:1, :2) from dual",
                [self.dir_name, file_name],
            )
            (bfile,) = self.cursor.fetchone()
            self.cursor.execute("truncate table TestBfiles")
            self.cursor.execute(
                "insert into TestBfiles values (:1, :2)", [1, bfile]
            )
            self.conn.commit()

    def test_ext_2104(self):
        "E2104 - test reading from a missing file"
        with tempfile.TemporaryDirectory() as temp_dir:
            self._setup_directory(temp_dir)
            file_name = "test_2104.txt"
            self.cursor.execute(
                "select bfilename(:1, :2) from dual",
                [self.dir_name, file_name],
            )
            (bfile,) = self.cursor.fetchone()
            self.assertEqual(bfile.getfilename(), (self.dir_name, file_name))
            self.assertFalse(bfile.fileexists())
            with self.assertRaisesFullCode("ORA-22288"):
                bfile.read()

    def test_ext_2105(self):
        "E2105 - test setting and getting BFILE var"
        with tempfile.TemporaryDirectory() as temp_dir:
            self._setup_directory(temp_dir)
            file_name1 = "test1.txt"
            contents1 = b"extended test 2105 - first file"
            with open(os.path.join(temp_dir, file_name1), "wb") as f:
                f.write(contents1)
            file_name2 = "test2.txt"
            contents2 = b"extended test 2105 - second file"
            with open(os.path.join(temp_dir, file_name2), "wb") as f:
                f.write(contents2)
            var1 = self.cursor.var(oracledb.DB_TYPE_BFILE)
            var2 = self.cursor.var(oracledb.DB_TYPE_BFILE)
            self.cursor.execute(
                f"""
                begin
                    :1 := BFILENAME('{self.dir_name}', '{file_name1}');
                    :2 := BFILENAME('{self.dir_name}', '{file_name2}');
                end;
                """,
                [var1, var2],
            )
            self.assertEqual(var1.getvalue().read(), contents1)
            self.assertEqual(var2.getvalue().read(), contents2)
            self.cursor.execute("begin :1 := :2; end;", [var1, var2])
            self.assertEqual(var1.getvalue().read(), contents2)


if __name__ == "__main__":
    test_env.run_test_cases()
