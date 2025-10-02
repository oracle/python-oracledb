# -----------------------------------------------------------------------------
# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
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

import oracledb
import pytest

DIR_NAME = "EXT_TEST_2100_DIR"


@pytest.fixture(autouse=True)
def module_checks(skip_unless_local_database):
    pass


@pytest.fixture
def temp_dir(test_env):
    with tempfile.TemporaryDirectory() as temp_dir:
        user = test_env.main_user
        with test_env.get_admin_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    create or replace directory {DIR_NAME}
                    as '{temp_dir}'
                    """
                )
                cursor.execute(f"grant read on directory {DIR_NAME} to {user}")
        yield temp_dir


def test_ext_2100(temp_dir, cursor):
    "E2100 - test fileexists() and getfilename()"
    file_name = "test_2100.txt"
    contents = b"Some arbitrary data for test 2100"
    with open(os.path.join(temp_dir, file_name), "wb") as f:
        f.write(contents)
    cursor.execute(
        "select bfilename(:1, :2) from dual",
        [DIR_NAME, file_name],
    )
    (bfile,) = cursor.fetchone()
    assert bfile.read() == contents
    assert bfile.fileexists()
    assert bfile.getfilename() == (DIR_NAME, file_name)


def test_ext_2101(temp_dir, cursor):
    "E2101 - test setfilename()"
    file_name = "test_2101.txt"
    contents = b"Some arbitrary data for test 2101"
    new_file_name = "test_2101b.txt"
    new_contents = b"Some arbitrary different data for test 2101"
    with open(os.path.join(temp_dir, file_name), "wb") as f:
        f.write(contents)
    with open(os.path.join(temp_dir, new_file_name), "wb") as f:
        f.write(new_contents)
    cursor.execute(
        "select bfilename(:1, :2) from dual",
        [DIR_NAME, file_name],
    )
    (bfile,) = cursor.fetchone()
    assert bfile.read() == contents
    bfile.setfilename(DIR_NAME, new_file_name)
    assert bfile.read() == new_contents


def test_ext_2102(temp_dir, cursor, test_env):
    "E2102 - test BFILE with LOB methods"
    file_name = "test_2102.txt"
    contents = b"Some arbitrary data for test 2102"
    with open(os.path.join(temp_dir, file_name), "wb") as f:
        f.write(contents)
    cursor.execute(
        "select bfilename(:1, :2) from dual",
        [DIR_NAME, file_name],
    )
    (bfile,) = cursor.fetchone()
    assert bfile.size() == len(contents)
    assert bfile.read(7) == contents[6:]
    assert bfile.read(7, 2) == contents[6:8]
    assert not bfile.isopen()
    bfile.open()
    assert bfile.isopen()
    bfile.close()
    assert not bfile.isopen()
    with test_env.assert_raises_full_code("DPY-3025"):
        bfile.getchunksize()
    with test_env.assert_raises_full_code("DPY-3025"):
        bfile.trim(1)
    with test_env.assert_raises_full_code("DPY-3025"):
        bfile.write("1")


def test_ext_2103(temp_dir, conn, cursor):
    "E2103 - test binding a BFILE"
    file_name = "test_2103.txt"
    contents = b"Some arbitrary data for test 2103"
    with open(os.path.join(temp_dir, file_name), "wb") as f:
        f.write(contents)
    cursor.execute(
        "select bfilename(:1, :2) from dual",
        [DIR_NAME, file_name],
    )
    (bfile,) = cursor.fetchone()
    cursor.execute("truncate table TestBfiles")
    cursor.execute("insert into TestBfiles values (:1, :2)", [1, bfile])
    conn.commit()


def test_ext_2104(temp_dir, cursor, test_env):
    "E2104 - test reading from a missing file"
    file_name = "test_2104.txt"
    cursor.execute(
        "select bfilename(:1, :2) from dual",
        [DIR_NAME, file_name],
    )
    (bfile,) = cursor.fetchone()
    assert bfile.getfilename() == (DIR_NAME, file_name)
    assert not bfile.fileexists()
    with test_env.assert_raises_full_code("ORA-22288"):
        bfile.read()


def test_ext_2105(temp_dir, cursor):
    "E2105 - test setting and getting BFILE var"
    file_name1 = "test1.txt"
    contents1 = b"extended test 2105 - first file"
    with open(os.path.join(temp_dir, file_name1), "wb") as f:
        f.write(contents1)
    file_name2 = "test2.txt"
    contents2 = b"extended test 2105 - second file"
    with open(os.path.join(temp_dir, file_name2), "wb") as f:
        f.write(contents2)
    var1 = cursor.var(oracledb.DB_TYPE_BFILE)
    var2 = cursor.var(oracledb.DB_TYPE_BFILE)
    cursor.execute(
        f"""
        begin
            :1 := BFILENAME('{DIR_NAME}', '{file_name1}');
            :2 := BFILENAME('{DIR_NAME}', '{file_name2}');
        end;
        """,
        [var1, var2],
    )
    assert var1.getvalue().read() == contents1
    assert var2.getvalue().read() == contents2
    cursor.execute("begin :1 := :2; end;", [var1, var2])
    assert var1.getvalue().read() == contents2
