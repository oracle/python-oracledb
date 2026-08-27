# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2026, Oracle and/or its affiliates.
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
Module for testing Rowids
"""

import datetime

import oracledb


def _populate_test_universal_rowids(cursor):
    cursor.execute("truncate table TestUniversalRowids")
    data = [
        (1, "ABC" * 75, datetime.datetime(2017, 4, 11)),
        (2, "DEF" * 80, datetime.datetime(2017, 4, 12)),
    ]
    cursor.executemany(
        "insert into TestUniversalRowids values (:1, :2, :3)",
        data,
    )
    cursor.connection.commit()


def _test_select_rowids(cursor, table_name):
    cursor.execute(f"select rowid, IntCol from {table_name}")
    sql = f"select IntCol from {table_name} where rowid = :val"
    for rowid, int_val in cursor.fetchall():
        cursor.execute(sql, val=rowid)
        assert cursor.fetchall() == [(int_val,)]


def test_3400(cursor):
    "3400 - test selecting all rowids from a regular table"
    _test_select_rowids(cursor, "TestNumbers")


def test_3401(cursor):
    "3401 - test selecting all rowids from an index organised table"
    _populate_test_universal_rowids(cursor)
    _test_select_rowids(cursor, "TestUniversalRowids")


def test_3402(cursor, test_env):
    "3402 - test inserting an invalid rowid"
    sql = "insert into TestRowids (IntCol, RowidCol) values (1, :rid)"
    with test_env.assert_raises_full_code("ORA-00932"):
        cursor.execute(sql, rid=12345)
    with test_env.assert_raises_full_code("ORA-01410"):
        cursor.execute(sql, rid="523lkhlf")


def test_3403(conn, cursor):
    "3403 - test selecting regular rowids stored in a urowid column"
    cursor.execute("truncate table TestRowids")
    cursor.execute("""
        insert into TestRowids (IntCol, UrowidCol)
        select IntCol, rowid
        from TestNumbers
        """)
    conn.commit()
    cursor.execute("select IntCol, UrowidCol from TestRowids")
    for int_val, rowid in cursor.fetchall():
        cursor.execute(
            "select IntCol from TestNumbers where rowid = :val",
            val=rowid,
        )
        assert cursor.fetchall() == [(int_val,)]


def test_3404(conn, cursor):
    "3404 - test selecting regular rowids stored in a rowid column"
    cursor.execute("truncate table TestRowids")
    cursor.execute("""
        insert into TestRowids (IntCol, RowidCol)
        select IntCol, rowid
        from TestNumbers
        """)
    conn.commit()
    cursor.execute("select IntCol, RowidCol from TestRowids")
    for int_val, rowid in cursor.fetchall():
        cursor.execute(
            """
            select IntCol
            from TestNumbers
            where rowid = :val
            """,
            val=rowid,
        )
        assert cursor.fetchall() == [(int_val,)]


def test_3405(conn, cursor):
    "3405 - binding and inserting a rowid"
    cursor.execute("truncate table TestRowids")
    insert_data = [
        (1, "String #1"),
        (2, "String #2"),
        (3, "String #3"),
        (4, "String #4"),
    ]
    cursor.execute("truncate table TestTempTable")
    cursor.executemany(
        """
        insert into TestTempTable (IntCol, StringCol1)
        values (:1, :2)
        """,
        insert_data,
    )
    conn.commit()
    ridvar = cursor.var(oracledb.ROWID)
    cursor.execute(
        """
        begin
            select rowid into :rid
            from TestTempTable
            where IntCol = 3;
        end;
        """,
        rid=ridvar,
    )
    cursor.setinputsizes(r1=oracledb.ROWID)
    cursor.execute(
        """
        insert into TestRowids (IntCol, RowidCol)
        values(1, :r1)
        """,
        r1=ridvar,
    )
    conn.commit()
    cursor.execute("select IntCol, RowidCol from TestRowids")
    int_val, rowid = cursor.fetchone()
    cursor.execute(
        """
        select IntCol, StringCol1 from TestTempTable
        where rowid = :val
        """,
        val=rowid,
    )
    assert cursor.fetchone() == (3, "String #3")


def test_3406(skip_unless_thin_mode, conn, cursor):
    "3406 - binding and inserting a rowid as urowid"
    cursor.execute("truncate table TestRowids")
    insert_data = [
        (1, "String #1", datetime.datetime(2017, 4, 4)),
        (2, "String #2", datetime.datetime(2017, 4, 5)),
        (3, "String #3", datetime.datetime(2017, 4, 6)),
        (4, "A" * 250, datetime.datetime(2017, 4, 7)),
    ]
    cursor.execute("truncate table TestUniversalRowids")
    cursor.executemany(
        """
        insert into TestUniversalRowids
        values (:1, :2, :3)
        """,
        insert_data,
    )
    conn.commit()
    ridvar = cursor.var(oracledb.DB_TYPE_UROWID)
    cursor.execute(
        """
        begin
            select rowid into :rid
            from TestUniversalRowids
            where IntCol = 3;
        end;
        """,
        rid=ridvar,
    )
    cursor.setinputsizes(r1=oracledb.DB_TYPE_UROWID)
    cursor.execute(
        """
        insert into TestRowids (IntCol, UrowidCol)
        values(1, :r1)
        """,
        r1=ridvar,
    )
    conn.commit()
    cursor.execute("select IntCol, UrowidCol from TestRowids")
    int_val, rowid = cursor.fetchone()
    cursor.execute(
        """
        select IntCol, StringCol, DateCol
        from TestUniversalRowids
        where rowid = :val
        """,
        val=rowid,
    )
    assert cursor.fetchone() == (3, "String #3", datetime.datetime(2017, 4, 6))


def test_3407(conn, cursor):
    "3407 - fetching a null rowid"
    cursor.execute("truncate table TestRowids")
    cursor.execute("insert into TestRowids (IntCol) values (1)")
    conn.commit()
    cursor.execute("select * from TestRowids")
    assert cursor.fetchone() == (1, None, None)
