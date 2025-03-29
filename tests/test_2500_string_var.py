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
2500 - Module for testing string variables
"""

import random
import string
import unittest

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    def setUp(self):
        super().setUp()
        self.raw_data = []
        self.data_by_key = {}
        for i in range(1, 11):
            string_col = f"String {i}"
            fixed_char_col = f"Fixed Char {i}".ljust(40)
            raw_col = f"Raw {i}".encode("ascii")
            if i % 2:
                nullable_col = f"Nullable {i}"
            else:
                nullable_col = None
            data_tuple = (i, string_col, raw_col, fixed_char_col, nullable_col)
            self.raw_data.append(data_tuple)
            self.data_by_key[i] = data_tuple

    def __return_strings_as_bytes(self, cursor, metadata):
        if metadata.type_code is oracledb.DB_TYPE_VARCHAR:
            return cursor.var(
                str, arraysize=cursor.arraysize, bypass_decode=True
            )

    def test_2500(self):
        "2500 - test creating array var and then increasing the internal size"
        val = ["12345678901234567890"] * 3
        var = self.cursor.arrayvar(str, len(val), 4)
        var.setvalue(0, val)
        self.assertEqual(var.getvalue(), val)

    def test_2501(self):
        "2501 - test binding in a string"
        self.cursor.execute(
            "select * from TestStrings where StringCol = :value",
            value="String 5",
        )
        self.assertEqual(self.cursor.fetchall(), [self.data_by_key[5]])

    def test_2502(self):
        "2502 - test binding a different variable on second execution"
        retval_1 = self.cursor.var(oracledb.STRING, 30)
        retval_2 = self.cursor.var(oracledb.STRING, 30)
        self.cursor.execute("begin :retval := 'Called'; end;", retval=retval_1)
        self.assertEqual(retval_1.getvalue(), "Called")
        self.cursor.execute("begin :retval := 'Called'; end;", retval=retval_2)
        self.assertEqual(retval_2.getvalue(), "Called")

    def test_2503(self):
        "2503 - test exceeding the number of elements returns IndexError"
        var = self.cursor.var(str)
        self.assertRaises(IndexError, var.getvalue, 1)

    def test_2504(self):
        "2504 - test binding in a string after setting input sizes to a number"
        self.cursor.setinputsizes(value=oracledb.NUMBER)
        self.cursor.execute(
            "select * from TestStrings where StringCol = :value",
            value="String 6",
        )
        self.assertEqual(self.cursor.fetchall(), [self.data_by_key[6]])

    def test_2505(self):
        "2505 - test binding in a string array"
        return_value = self.cursor.var(oracledb.NUMBER)
        array = [r[1] for r in self.raw_data]
        statement = """
                begin
                    :return_value := pkg_TestStringArrays.TestInArrays(
                        :integer_value, :array);
                end;"""
        self.cursor.execute(
            statement, return_value=return_value, integer_value=5, array=array
        )
        self.assertEqual(return_value.getvalue(), 86)
        array = [f"String - {i}" for i in range(15)]
        self.cursor.execute(statement, integer_value=8, array=array)
        self.assertEqual(return_value.getvalue(), 163)

    def test_2506(self):
        "2506 - test binding in a string array (with setinputsizes)"
        return_value = self.cursor.var(oracledb.NUMBER)
        self.cursor.setinputsizes(array=[oracledb.STRING, 10])
        array = [r[1] for r in self.raw_data]
        self.cursor.execute(
            """
            begin
                :return_value := pkg_TestStringArrays.TestInArrays(
                    :integer_value, :array);
            end;
            """,
            return_value=return_value,
            integer_value=6,
            array=array,
        )
        self.assertEqual(return_value.getvalue(), 87)

    def test_2507(self):
        "2507 - test binding in a string array (with arrayvar)"
        return_value = self.cursor.var(oracledb.NUMBER)
        array = self.cursor.arrayvar(oracledb.STRING, 10, 20)
        array.setvalue(0, [r[1] for r in self.raw_data])
        self.cursor.execute(
            """
            begin
                :return_value := pkg_TestStringArrays.TestInArrays(
                    :integer_value, :array);
            end;
            """,
            return_value=return_value,
            integer_value=7,
            array=array,
        )
        self.assertEqual(return_value.getvalue(), 88)

    def test_2508(self):
        "2508 - test binding in/out a string array (with arrayvar)"
        array = self.cursor.arrayvar(oracledb.STRING, 10, 100)
        original_data = [r[1] for r in self.raw_data]
        expected_data = [
            "Converted element # %d originally had length %d"
            % (i, len(original_data[i - 1]))
            for i in range(1, 6)
        ] + original_data[5:]
        array.setvalue(0, original_data)
        self.cursor.execute(
            """
            begin
                pkg_TestStringArrays.TestInOutArrays(:num_elems, :array);
            end;
            """,
            num_elems=5,
            array=array,
        )
        self.assertEqual(array.getvalue(), expected_data)

    def test_2509(self):
        "2509 - test binding out a string array (with arrayvar)"
        array = self.cursor.arrayvar(oracledb.STRING, 6, 100)
        expected_data = [f"Test out element # {i}" for i in range(1, 7)]
        self.cursor.execute(
            """
            begin
                pkg_TestStringArrays.TestOutArrays(:num_elems, :array);
            end;
            """,
            num_elems=6,
            array=array,
        )
        self.assertEqual(array.getvalue(), expected_data)

    def test_2510(self):
        "2510 - test binding in a raw"
        self.cursor.setinputsizes(value=oracledb.BINARY)
        self.cursor.execute(
            "select * from TestStrings where RawCol = :value",
            value="Raw 4".encode(),
        )
        self.assertEqual(self.cursor.fetchall(), [self.data_by_key[4]])

    def test_2511(self):
        "2511 - test binding (and fetching) a rowid"
        self.cursor.execute("select rowid from TestStrings where IntCol = 3")
        (rowid,) = self.cursor.fetchone()
        self.cursor.execute(
            "select * from TestStrings where rowid = :value",
            value=rowid,
        )
        self.assertEqual(self.cursor.fetchall(), [self.data_by_key[3]])

    def test_2513(self):
        "2513 - test binding in a null"
        self.cursor.execute(
            "select * from TestStrings where StringCol = :value",
            value=None,
        )
        self.assertEqual(self.cursor.fetchall(), [])

    def test_2514(self):
        "2514 - test binding out with set input sizes defined (by type)"
        bind_vars = self.cursor.setinputsizes(value=oracledb.STRING)
        self.cursor.execute(
            """
            begin
                :value := 'TSI';
            end;
            """
        )
        self.assertEqual(bind_vars["value"].getvalue(), "TSI")

    def test_2515(self):
        "2515 - test binding out with set input sizes defined (by integer)"
        bind_vars = self.cursor.setinputsizes(value=30)
        self.cursor.execute(
            """
            begin
                :value := 'TSI (I)';
            end;
            """
        )
        self.assertEqual(bind_vars["value"].getvalue(), "TSI (I)")

    def test_2516(self):
        "2516 - test binding in/out with set input sizes defined (by type)"
        bind_vars = self.cursor.setinputsizes(value=oracledb.STRING)
        self.cursor.execute(
            """
            begin
                :value := :value || ' TSI';
            end;
            """,
            value="InVal",
        )
        self.assertEqual(bind_vars["value"].getvalue(), "InVal TSI")

    def test_2517(self):
        "2517 - test binding in/out with set input sizes defined (by integer)"
        bind_vars = self.cursor.setinputsizes(value=30)
        self.cursor.execute(
            """
            begin
                :value := :value || ' TSI (I)';
            end;
            """,
            value="InVal",
        )
        self.assertEqual(bind_vars["value"].getvalue(), "InVal TSI (I)")

    def test_2518(self):
        "2518 - test binding out with cursor.var() method"
        var = self.cursor.var(oracledb.STRING)
        self.cursor.execute(
            """
            begin
                :value := 'TSI (VAR)';
            end;
            """,
            value=var,
        )
        self.assertEqual(var.getvalue(), "TSI (VAR)")

    def test_2519(self):
        "2519 - test binding in/out with cursor.var() method"
        var = self.cursor.var(oracledb.STRING)
        var.setvalue(0, "InVal")
        self.cursor.execute(
            """
            begin
                :value := :value || ' TSI (VAR)';
            end;
            """,
            value=var,
        )
        self.assertEqual(var.getvalue(), "InVal TSI (VAR)")

    def test_2520(self):
        "2520 - test that binding a long string succeeds"
        self.cursor.setinputsizes(big_string=oracledb.DB_TYPE_LONG)
        self.cursor.execute(
            """
            declare
                t_Temp varchar2(20000);
            begin
                t_Temp := :big_string;
            end;
            """,
            big_string="X" * 10000,
        )

    def test_2521(self):
        "2521 - test that setinputsizes() returns a long variable"
        var = self.cursor.setinputsizes(test=90000)["test"]
        in_string = "1234567890" * 9000
        var.setvalue(0, in_string)
        out_string = var.getvalue()
        msg = (
            f"output does not match: in was {len(in_string)}, "
            f"out was {len(out_string)}"
        )
        self.assertEqual(in_string, out_string, msg)

    def test_2522(self):
        "2522 - test cursor description is accurate"
        self.cursor.execute("select * from TestStrings")
        varchar_ratio, nvarchar_ratio = test_env.get_charset_ratios()
        expected_value = [
            ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
            (
                "STRINGCOL",
                oracledb.DB_TYPE_VARCHAR,
                20,
                20 * varchar_ratio,
                None,
                None,
                False,
            ),
            ("RAWCOL", oracledb.DB_TYPE_RAW, 30, 30, None, None, False),
            (
                "FIXEDCHARCOL",
                oracledb.DB_TYPE_CHAR,
                40,
                40 * varchar_ratio,
                None,
                None,
                False,
            ),
            (
                "NULLABLECOL",
                oracledb.DB_TYPE_VARCHAR,
                50,
                50 * varchar_ratio,
                None,
                None,
                True,
            ),
        ]
        self.assertEqual(self.cursor.description, expected_value)

    def test_2523(self):
        "2523 - test that fetching all of the data returns the correct results"
        self.cursor.execute("select * From TestStrings order by IntCol")
        self.assertEqual(self.cursor.fetchall(), self.raw_data)
        self.assertEqual(self.cursor.fetchall(), [])

    def test_2524(self):
        "2524 - test that fetching data in chunks returns the correct results"
        self.cursor.execute("select * From TestStrings order by IntCol")
        self.assertEqual(self.cursor.fetchmany(3), self.raw_data[0:3])
        self.assertEqual(self.cursor.fetchmany(2), self.raw_data[3:5])
        self.assertEqual(self.cursor.fetchmany(4), self.raw_data[5:9])
        self.assertEqual(self.cursor.fetchmany(3), self.raw_data[9:])
        self.assertEqual(self.cursor.fetchmany(3), [])

    def test_2525(self):
        "2525 - test that fetching a single row returns the correct results"
        self.cursor.execute(
            """
            select *
            from TestStrings
            where IntCol in (3, 4)
            order by IntCol
            """
        )
        self.assertEqual(self.cursor.fetchone(), self.data_by_key[3])
        self.assertEqual(self.cursor.fetchone(), self.data_by_key[4])
        self.assertIsNone(self.cursor.fetchone())

    def test_2526(self):
        "2526 - test binding and fetching supplemental charcters"
        if test_env.get_charset() != "AL32UTF8":
            self.skipTest("Database character set must be AL32UTF8")
        supplemental_chars = (
            "𠜎 𠜱 𠝹 𠱓 𠱸 𠲖 𠳏 𠳕 𠴕 𠵼 𠵿 𠸎 𠸏 "
            "𠹷 𠺝 𠺢 𠻗 𠻹 𠻺 𠼭 𠼮 𠽌 𠾴 𠾼 𠿪 𡁜 "
            "𡁯 𡁵 𡁶 𡁻 𡃁 𡃉 𡇙 𢃇 𢞵 𢫕 𢭃 𢯊 𢱑 "
            "𢱕 𢳂 𢴈 𢵌 𢵧 𢺳 𣲷 𤓓 𤶸 𤷪 𥄫 𦉘 𦟌 "
            "𦧲 𦧺 𧨾 𨅝 𨈇 𨋢 𨳊 𨳍 𨳒 𩶘"
        )
        self.cursor.execute("truncate table TestTempTable")
        self.cursor.execute(
            """
            insert into TestTempTable (IntCol, StringCol1)
            values (:1, :2)
            """,
            (1, supplemental_chars),
        )
        self.conn.commit()
        self.cursor.execute("select StringCol1 from TestTempTable")
        (value,) = self.cursor.fetchone()
        self.assertEqual(value, supplemental_chars)

    def test_2527(self):
        "2527 - test binding twice with a larger string the second time"
        self.cursor.execute("truncate table TestTempTable")
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        short_string = "short string"
        long_string = "long string " * 30
        self.cursor.execute(sql, (1, short_string))
        self.cursor.execute(sql, (2, long_string))
        self.conn.commit()
        self.cursor.execute(
            """
            select IntCol, StringCol1
            from TestTempTable
            order by IntCol
            """
        )
        self.assertEqual(
            self.cursor.fetchall(), [(1, short_string), (2, long_string)]
        )

    @unittest.skipIf(
        test_env.get_server_version() < (12, 2), "not supported on this server"
    )
    def test_2528(self):
        "2528 - test issue 50 - avoid error ORA-24816"
        cursor = self.conn.cursor()
        try:
            cursor.execute("drop table issue_50 purge")
        except oracledb.DatabaseError:
            pass
        cursor.execute(
            """
            create table issue_50 (
                Id          number(11) primary key,
                Str1        nvarchar2(256),
                Str2        nvarchar2(256),
                Str3        nvarchar2(256),
                NClob1      nclob,
                NClob2      nclob
            )
            """
        )
        id_var = cursor.var(oracledb.NUMBER)
        cursor.execute(
            """
            insert into issue_50 (Id, Str2, Str3, NClob1, NClob2, Str1)
            values (:arg0, :arg1, :arg2, :arg3, :arg4, :arg5)
            returning id into :arg6
            """,
            [1, "555a4c78", "f319ef0e", "23009914", "", "", id_var],
        )
        cursor = self.conn.cursor()
        cursor.execute(
            """
            insert into issue_50 (Id, Str2, Str3, NClob1, NClob2, Str1)
            values (:arg0, :arg1, :arg2, :arg3, :arg4, :arg5)
            returning id into :arg6
            """,
            [2, "d5ff845a", "94275767", "bf161ff6", "", "", id_var],
        )
        cursor.execute("drop table issue_50 purge")

    def test_2529(self):
        "2529 - test assigning a string to rowid"
        var = self.cursor.var(oracledb.ROWID)
        with self.assertRaisesFullCode("DPY-3004"):
            var.setvalue(0, "ABDHRYTHFJGKDKKDH")

    def test_2530(self):
        "2530 - test fetching XMLType (< 1K) as a string"
        self.cursor.execute(
            """
            select XMLElement("string", stringCol) as xml
            from TestStrings
            where intCol = 1
            """
        )
        (actual_value,) = self.cursor.fetchone()
        self.assertEqual(actual_value, "<string>String 1</string>")
        self.assertEqual(
            self.cursor.description,
            [("XML", oracledb.DB_TYPE_XMLTYPE, None, None, None, None, True)],
        )

    def test_2531(self):
        "2531 - test inserting and fetching XMLType (1K) as a string"
        self.cursor.execute("truncate table TestTempXML")
        chars = string.ascii_uppercase + string.ascii_lowercase
        random_string = "".join(random.choice(chars) for _ in range(1024))
        int_val = 2531
        xml_string = f"<data>{random_string}</data>"
        self.cursor.execute(
            "insert into TestTempXML (IntCol, XMLCol) values (:1, :2)",
            (int_val, xml_string),
        )
        self.cursor.execute(
            "select XMLCol from TestTempXML where intCol = :1",
            [int_val],
        )
        (actual_value,) = self.cursor.fetchone()
        self.assertEqual(actual_value.strip(), xml_string)

    def test_2532(self):
        "2532 - fetching null and not null values can use optimised path"
        sql = """
                select * from TestStrings
                where IntCol between :start_value and :end_value"""
        self.cursor.execute(sql, start_value=2, end_value=5)
        self.assertEqual(self.cursor.fetchall(), self.raw_data[1:5])
        self.cursor.execute(sql, start_value=5, end_value=8)
        self.assertEqual(self.cursor.fetchall(), self.raw_data[4:8])
        self.cursor.execute(sql, start_value=8, end_value=10)
        self.assertEqual(self.cursor.fetchall(), self.raw_data[7:10])

    def test_2533(self):
        "2533 - test bypass string decode"
        self.cursor.execute("truncate table TestTempTable")
        string_val = "I bought a cafetière on the Champs-Élysées"
        sql = "insert into TestTempTable (IntCol, StringCol1) values (:1, :2)"
        with self.conn.cursor() as cursor:
            cursor.execute(sql, (1, string_val))
            cursor.execute("select IntCol, StringCol1 from TestTempTable")
            self.assertEqual(cursor.fetchone(), (1, string_val))
        with self.conn.cursor() as cursor:
            cursor.outputtypehandler = self.__return_strings_as_bytes
            cursor.execute("select IntCol, StringCol1 from TestTempTable")
            self.assertEqual(cursor.fetchone(), (1, string_val.encode()))
        with self.conn.cursor() as cursor:
            cursor.outputtypehandler = None
            cursor.execute("select IntCol, StringCol1 from TestTempTable")
            self.assertEqual(cursor.fetchone(), (1, string_val))

    @unittest.skipIf(
        not test_env.get_is_thin(),
        "thick mode doesn't support fetching XMLType > VARCHAR2",
    )
    def test_2534(self):
        "2534 - test inserting and fetching XMLType (32K) as a string"
        self.cursor.execute("truncate table TestTempXML")
        chars = string.ascii_uppercase + string.ascii_lowercase
        random_string = "".join(random.choice(chars) for _ in range(32768))
        int_val = 2534
        xml_string = f"<data>{random_string}</data>"
        lob = self.conn.createlob(oracledb.DB_TYPE_CLOB)
        lob.write(xml_string)
        self.cursor.execute(
            """
            insert into TestTempXML (IntCol, XMLCol)
            values (:1, sys.xmltype(:2))
            """,
            (int_val, lob),
        )
        self.cursor.execute(
            "select XMLCol from TestTempXML where intCol = :1",
            [int_val],
        )
        (actual_value,) = self.cursor.fetchone()
        self.assertEqual(actual_value.strip(), xml_string)


if __name__ == "__main__":
    test_env.run_test_cases()
