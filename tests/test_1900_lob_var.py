#------------------------------------------------------------------------------
# Copyright (c) 2020, 2022, Oracle and/or its affiliates.
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
#------------------------------------------------------------------------------

"""
1900 - Module for testing LOB (CLOB and BLOB) variables
"""

import pickle

import oracledb
import test_env

class TestCase(test_env.BaseTestCase):

    def __get_temp_lobs(self, sid):
        cursor = self.connection.cursor()
        cursor.execute("""
                select cache_lobs + nocache_lobs + abstract_lobs
                from v$temporary_lobs
                where sid = :sid""", sid = sid)
        row = cursor.fetchone()
        if row is None:
            return 0
        return int(row[0])

    def __perform_test(self, lob_type, input_type):
        long_string = ""
        db_type = getattr(oracledb, "DB_TYPE_" + lob_type)
        self.cursor.execute(f"truncate table Test{lob_type}s")
        for i in range(0, 11):
            if i > 0:
                char = chr(ord('A') + i - 1)
                long_string += char * 25000
            elif input_type is not db_type:
                continue
            self.cursor.setinputsizes(long_string=input_type)
            if lob_type == "BLOB":
                bind_value = long_string.encode()
            else:
                bind_value = long_string
            self.cursor.execute(f"""
                    insert into Test{lob_type}s (
                        IntCol,
                        {lob_type}Col
                    ) values (
                        :integer_value,
                        :long_string
                    )""",
                    integer_value=i,
                    long_string=bind_value)
        self.connection.commit()
        self.cursor.execute(f"""
                select
                    IntCol,
                    {lob_type}Col
                from Test{lob_type}s
                order by IntCol""")
        self.__validate_query(self.cursor, lob_type)

    def __test_bind_ordering(self, lob_type):
        main_col = "A" * 32768
        extra_col_1 = "B" * 65536
        extra_col_2 = "C" * 131072
        if lob_type == "BLOB":
            main_col = main_col.encode()
            extra_col_1 = extra_col_1.encode()
            extra_col_2 = extra_col_2.encode()
        self.connection.stmtcachesize = 0
        self.cursor.execute(f"truncate table Test{lob_type}s")
        data = (1, main_col, 8, extra_col_1, 15, extra_col_2)
        self.cursor.execute(f"""
                insert into Test{lob_type}s (
                    IntCol,
                    {lob_type}Col,
                    ExtraNumCol1,
                    Extra{lob_type}Col1,
                    ExtraNumCol2,
                    Extra{lob_type}Col2
                ) values (:1, :2, :3, :4, :5, :6)""",
                data)
        with test_env.FetchLobsContextManager(False):
            self.cursor.execute(f"select * from Test{lob_type}s")
            fetched_data = self.cursor.fetchone()
            self.assertEqual(fetched_data, data)

    def __test_fetch_lobs_direct(self, lob_type):
        self.cursor.execute(f"truncate table Test{lob_type}s")
        data = []
        long_string = ""
        for i in range(1, 11):
            if i > 0:
                char = chr(ord('A') + i - 1)
                long_string += char * 25000
            if lob_type == "BLOB":
                data.append((i, long_string.encode()))
            else:
                data.append((i, long_string))
        self.cursor.executemany(f"""
                    insert into Test{lob_type}s (
                        IntCol,
                        {lob_type}Col
                    ) values (
                        :1,
                        :2
                    )""", data)
        with test_env.FetchLobsContextManager(False):
            self.cursor.execute(f"""
                    select
                        IntCol,
                        {lob_type}Col
                    from Test{lob_type}s
                    order by IntCol""")
            self.assertEqual(data, self.cursor.fetchall())

    def __test_lob_operations(self, lob_type):
        self.cursor.execute(f"truncate table Test{lob_type}s")
        self.cursor.setinputsizes(long_string=getattr(oracledb, lob_type))
        long_string = "X" * 75000
        write_value = "TEST"
        if lob_type == "BLOB":
            long_string = long_string.encode("ascii")
            write_value = write_value.encode("ascii")
        self.cursor.execute(f"""
                insert into Test{lob_type}s (
                    IntCol,
                    {lob_type}Col
                ) values (
                    :integer_value,
                    :long_string
                )""",
                integer_value=1,
                long_string=long_string)
        self.cursor.execute(f"""
                select {lob_type}Col
                from Test{lob_type}s
                where IntCol = 1""")
        lob, = self.cursor.fetchone()
        self.assertEqual(lob.isopen(), False)
        lob.open()
        self.assertEqual(lob.isopen(), True)
        lob.close()
        self.assertEqual(lob.isopen(), False)
        self.assertEqual(lob.size(), 75000)
        lob.write(write_value, 75001)
        self.assertEqual(lob.size(), 75000 + len(write_value))
        self.assertEqual(lob.read(), long_string + write_value)
        lob.write(write_value, 1)
        self.assertEqual(lob.read(),
                         write_value + long_string[4:] + write_value)
        lob.trim(25000)
        self.assertEqual(lob.size(), 25000)
        lob.trim(newSize=10000)
        self.assertEqual(lob.size(), 10000)
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-2014:",
                               lob.trim, new_size=50, newSize=60)
        lob.trim()
        self.assertEqual(lob.size(), 0)

    def __test_pickle(self, lob_type):
        value = "A test string value for pickling"
        if lob_type == "BLOB":
            value = value.encode("ascii")
        db_type = getattr(oracledb, "DB_TYPE_" + lob_type)
        lob = self.connection.createlob(db_type)
        lob.write(value)
        pickled_data = pickle.dumps(lob)
        unpickled_value = pickle.loads(pickled_data)
        self.assertEqual(unpickled_value, value)

    def __test_temporary_lob(self, lob_type):
        self.cursor.execute(f"truncate table Test{lob_type}s")
        value = "A test string value"
        if lob_type == "BLOB":
            value = value.encode("ascii")
        db_type = getattr(oracledb, "DB_TYPE_" + lob_type)
        lob = self.connection.createlob(db_type)
        lob.write(value)
        self.cursor.execute("""
                insert into Test%ss (IntCol, %sCol)
                values (:int_val, :lob_val)""" % (lob_type, lob_type),
                int_val=1,
                lob_val=lob)
        self.cursor.execute("select %sCol from Test%ss" % (lob_type, lob_type))
        lob, = self.cursor.fetchone()
        self.assertEqual(lob.read(), value)

    def __validate_query(self, rows, lob_type):
        long_string = ""
        db_type = getattr(oracledb, "DB_TYPE_" + lob_type)
        for row in rows:
            integer_value, lob = row
            self.assertEqual(lob.type, db_type)
            if integer_value == 0:
                self.assertEqual(lob.size(), 0)
                expected_value = ""
                if lob_type == "BLOB":
                    expected_value = expected_value.encode()
                self.assertEqual(lob.read(), expected_value)
            else:
                char = chr(ord('A') + integer_value - 1)
                prev_char = chr(ord('A') + integer_value - 2)
                long_string += char * 25000
                if lob_type == "BLOB":
                    expected_value = long_string.encode("ascii")
                    char = char.encode("ascii")
                    prev_char = prev_char.encode("ascii")
                else:
                    expected_value = long_string
                self.assertEqual(lob.size(), len(expected_value))
                self.assertEqual(lob.read(), expected_value)
                if lob_type == "CLOB":
                    self.assertEqual(str(lob), expected_value)
                self.assertEqual(lob.read(len(expected_value)), char)
            if integer_value > 1:
                offset = (integer_value - 1) * 25000 - 4
                string = prev_char * 5 + char * 5
                self.assertEqual(lob.read(offset, 10), string)

    def test_1900_bind_lob_value(self):
        "1900 - test binding a LOB value directly"
        self.cursor.execute("truncate table TestCLOBs")
        self.cursor.execute("""
                insert into TestCLOBs
                (IntCol, ClobCol)
                values (1, 'Short value')""")
        self.cursor.execute("select ClobCol from TestCLOBs")
        lob, = self.cursor.fetchone()
        self.cursor.execute("""
                insert into TestCLOBs
                (IntCol, ClobCol)
                values (2, :value)""",
                value=lob)

    def test_1901_blob_cursor_description(self):
        "1901 - test cursor description is accurate for BLOBs"
        self.cursor.execute("select IntCol, BlobCol from TestBLOBs")
        expected_value = [
            ('INTCOL', oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, 0),
            ('BLOBCOL', oracledb.DB_TYPE_BLOB, None, None, None, None, 0)
        ]
        self.assertEqual(self.cursor.description, expected_value)

    def test_1902_blob_direct(self):
        "1902 - test binding and fetching BLOB data (directly)"
        self.__perform_test("BLOB", oracledb.DB_TYPE_BLOB)

    def test_1903_blob_indirect(self):
        "1903 - test binding and fetching BLOB data (indirectly)"
        self.__perform_test("BLOB", oracledb.DB_TYPE_LONG_RAW)

    def test_1904_blob_operations(self):
        "1904 - test operations on BLOBs"
        self.__test_lob_operations("BLOB")

    def test_1905_clob_cursor_description(self):
        "1905 - test cursor description is accurate for CLOBs"
        self.cursor.execute("select IntCol, ClobCol from TestCLOBs")
        expected_value = [
            ('INTCOL', oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
            ('CLOBCOL', oracledb.DB_TYPE_CLOB, None, None, None, None, False)
        ]
        self.assertEqual(self.cursor.description, expected_value)

    def test_1906_clob_direct(self):
        "1906 - test binding and fetching CLOB data (directly)"
        self.__perform_test("CLOB", oracledb.DB_TYPE_CLOB)

    def test_1907_clob_indirect(self):
        "1907 - test binding and fetching CLOB data (indirectly)"
        self.__perform_test("CLOB", oracledb.DB_TYPE_LONG)

    def test_1908_clob_operations(self):
        "1908 - test operations on CLOBs"
        self.__test_lob_operations("CLOB")

    def test_1909_create_temp_blob(self):
        "1909 - test creating a temporary BLOB"
        self.__test_temporary_lob("BLOB")

    def test_1910_create_temp_clob(self):
        "1910 - test creating a temporary CLOB"
        self.__test_temporary_lob("CLOB")

    def test_1911_create_temp_nclob(self):
        "1911 - test creating a temporary NCLOB"
        self.__test_temporary_lob("NCLOB")

    def test_1912_multiple_fetch(self):
        "1912 - test retrieving data from a CLOB after multiple fetches"
        self.cursor.arraysize = 1
        self.cursor.execute("select * from TestCLOBS")
        rows = self.cursor.fetchall()
        self.__validate_query(rows, "CLOB")

    def test_1913_nclob_cursor_description(self):
        "1913 - test cursor description is accurate for NCLOBs"
        self.cursor.execute("select IntCol, NClobCol from TestNCLOBs")
        expected_value = [
            ('INTCOL', oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, 0),
            ('NCLOBCOL', oracledb.DB_TYPE_NCLOB, None, None, None, None, 0)
        ]
        self.assertEqual(self.cursor.description, expected_value)

    def test_1914_nclob_direct(self):
        "1914 - test binding and fetching NCLOB data (directly)"
        self.__perform_test("NCLOB", oracledb.DB_TYPE_NCLOB)

    def test_1915_nclob_non_ascii_chars(self):
        "1915 - test binding and fetching NCLOB data (with non-ASCII chars)"
        value = "\u03b4\u4e2a"
        self.cursor.execute("truncate table TestNCLOBs")
        self.cursor.setinputsizes(val=oracledb.DB_TYPE_NVARCHAR)
        self.cursor.execute("""
                insert into TestNCLOBs (IntCol, NClobCol)
                values (1, :val)""",
                val=value)
        self.cursor.execute("select NCLOBCol from TestNCLOBs")
        nclob, = self.cursor.fetchone()
        self.cursor.setinputsizes(val=oracledb.DB_TYPE_NVARCHAR)
        self.cursor.execute("update TestNCLOBs set NCLOBCol = :val",
                            val=nclob.read() + value)
        self.cursor.execute("select NCLOBCol from TestNCLOBs")
        nclob, = self.cursor.fetchone()
        self.assertEqual(nclob.read(), value + value)

    def test_1916_nclob_indirect(self):
        "1916 - test binding and fetching NCLOB data (indirectly)"
        self.__perform_test("NCLOB", oracledb.DB_TYPE_LONG)

    def test_1917_nclob_operations(self):
        "1917 - test operations on NCLOBs"
        self.__test_lob_operations("NCLOB")

    def test_1918_temporary_lobs(self):
        "1918 - test temporary LOBs"
        self.cursor.execute("""
                select sys_context('USERENV', 'SID')
                from dual""")
        sid, = self.cursor.fetchone()
        temp_lobs = self.__get_temp_lobs(sid)
        with self.connection.cursor() as cursor:
            cursor.arraysize = 27
            self.assertEqual(temp_lobs, 0)
            cursor.execute("""
                    select extract(xmlcol, '/').getclobval()
                    from TestXML""")
            for lob, in cursor:
                value = lob.read()
                del lob
        temp_lobs = self.__get_temp_lobs(sid)
        self.assertEqual(temp_lobs, 0)

    def test_1919_assign_string_beyond_array_size(self):
        "1919 - test assign string to NCLOB beyond array size"
        nclobVar = self.cursor.var(oracledb.DB_TYPE_NCLOB)
        self.assertRaises(IndexError, nclobVar.setvalue, 1, "test char")

    def test_1920_supplemental_characters(self):
        "1920 - test read/write temporary LOBs using supplemental characters"
        self.cursor.execute("""
                select value
                from nls_database_parameters
                where parameter = 'NLS_CHARACTERSET'""")
        charset, = self.cursor.fetchone()
        if charset != "AL32UTF8":
            self.skipTest("Database character set must be AL32UTF8")
        supplemental_chars = "𠜎 𠜱 𠝹 𠱓 𠱸 𠲖 𠳏 𠳕 𠴕 𠵼 𠵿 𠸎 𠸏 𠹷 𠺝 " \
                "𠺢 𠻗 𠻹 𠻺 𠼭 𠼮 𠽌 𠾴 𠾼 𠿪 𡁜 𡁯 𡁵 𡁶 𡁻 𡃁 𡃉 𡇙 𢃇 " \
                "𢞵 𢫕 𢭃 𢯊 𢱑 𢱕 𢳂 𢴈 𢵌 𢵧 𢺳 𣲷 𤓓 𤶸 𤷪 𥄫 𦉘 𦟌 𦧲 " \
                "𦧺 𧨾 𨅝 𨈇 𨋢 𨳊 𨳍 𨳒 𩶘"
        self.cursor.execute("truncate table TestCLOBs")
        lob = self.connection.createlob(oracledb.DB_TYPE_CLOB)
        lob.write(supplemental_chars)
        self.cursor.execute("""
                insert into TestCLOBs
                (IntCol, ClobCol)
                values (1, :val)""",
                [lob])
        self.connection.commit()
        self.cursor.execute("select ClobCol from TestCLOBs")
        lob, = self.cursor.fetchone()
        self.assertEqual(lob.read(), supplemental_chars)

    def test_1921_plsql_auto_conversion_clob(self):
        "1921 - test automatic conversion to CLOB for PL/SQL"
        var = self.cursor.var(str, outconverter=lambda v: v[-15:])
        var.setvalue(0, "A" * 50000)
        self.cursor.execute("""
                declare
                    t_Clob          clob;
                begin
                    t_Clob := :data;
                    dbms_lob.copy(:data, t_Clob, 50000);
                    dbms_lob.writeappend(:data, 5, 'BBBBB');
                end;""",
                data=var)
        result = var.getvalue()
        self.assertEqual(result, "A" * 10 + "B" * 5)

    def test_1922_plsql_auto_conversion_nclob(self):
        "1922 - test automatic conversion to NCLOB for PL/SQL"
        var = self.cursor.var(oracledb.DB_TYPE_NCHAR,
                              outconverter=lambda v: v[-12:])
        var.setvalue(0, "N" * 51234)
        self.cursor.execute("""
                declare
                    t_Clob          nclob;
                begin
                    t_Clob := :data;
                    dbms_lob.copy(:data, t_Clob, 51234);
                    dbms_lob.writeappend(:data, 7, 'PPPPPPP');
                end;""",
                data=var)
        result = var.getvalue()
        self.assertEqual(result, "N" * 5 + "P" * 7)

    def test_1923_plsql_auto_conversion_blob(self):
        "1923 - test automatic conversion to BLOB for PL/SQL"
        var = self.cursor.var(bytes,
                              outconverter=lambda v: v[-14:])
        var.setvalue(0, b"L" * 52345)
        self.cursor.execute("""
                declare
                    t_Blob          blob;
                begin
                    t_Blob := :data;
                    dbms_lob.copy(:data, t_Blob, 52345);
                    dbms_lob.writeappend(:data, 6, '515151515151');
                end;""",
                data=var)
        result = var.getvalue()
        self.assertEqual(result, b"L" * 8 + b"Q" * 6)

    def test_1924_pickle_blob(self):
        "1924 - test pickling of BLOB"
        self.__test_pickle("BLOB")

    def test_1925_pickle_clob(self):
        "1925 - test pickling of CLOB"
        self.__test_pickle("CLOB")

    def test_1926_pickle_nclob(self):
        "1925 - test pickling of NCLOB"
        self.__test_pickle("NCLOB")

    def test_1927_fetch_blob_as_bytes(self):
        "1927 - test fetching BLOB as bytes"
        self.__test_fetch_lobs_direct("BLOB")

    def test_1928_fetch_clob_as_str(self):
        "1928 - test fetching CLOB as str"
        self.__test_fetch_lobs_direct("CLOB")

    def test_1929_fetch_nclob_as_str(self):
        "1929 - test fetching NCLOB as str"
        self.__test_fetch_lobs_direct("NCLOB")

    def test_1930_bind_order_blob(self):
        "1930 - test bind ordering with BLOB"
        self.__test_bind_ordering("BLOB")

    def test_1931_bind_order_clob(self):
        "1931 - test bind ordering with CLOB"
        self.__test_bind_ordering("CLOB")

    def test_1932_bind_order_nclob(self):
        "1932 - test bind ordering with NCLOB"
        self.__test_bind_ordering("NCLOB")

if __name__ == "__main__":
    test_env.run_test_cases()
