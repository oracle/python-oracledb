# -----------------------------------------------------------------------------
# Copyright (c) 2023, 2024, Oracle and/or its affiliates.
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
5700 - Module for testing LOB (CLOB and BLOB) variables with asyncio
"""

import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    async def __get_temp_lobs(self, sid):
        cursor = self.conn.cursor()
        await cursor.execute(
            """
            select cache_lobs + nocache_lobs + abstract_lobs
            from v$temporary_lobs
            where sid = :sid
            """,
            sid=sid,
        )
        row = await cursor.fetchone()
        if row is None:
            return 0
        return int(row[0])

    async def __perform_test(self, lob_type, input_type):
        long_string = ""
        db_type = getattr(oracledb, f"DB_TYPE_{lob_type}")
        await self.cursor.execute(f"delete from Test{lob_type}s")
        for i in range(11):
            if i > 0:
                char = chr(ord("A") + i - 1)
                long_string += char * 25000
            elif input_type is not db_type:
                continue
            self.cursor.setinputsizes(long_string=input_type)
            if lob_type == "BLOB":
                bind_value = long_string.encode()
            else:
                bind_value = long_string
            await self.cursor.execute(
                f"""
                insert into Test{lob_type}s (IntCol, {lob_type}Col)
                values (:integer_value, :long_string)
                """,
                integer_value=i,
                long_string=bind_value,
            )
        await self.conn.commit()
        await self.cursor.execute(
            f"""
            select IntCol, {lob_type}Col
            from Test{lob_type}s
            order by IntCol
            """
        )
        await self.__validate_query(await self.cursor.fetchall(), lob_type)

    async def __test_bind_ordering(self, lob_type):
        main_col = "A" * 32768
        extra_col_1 = "B" * 65536
        extra_col_2 = "C" * 131072
        if lob_type == "BLOB":
            main_col = main_col.encode()
            extra_col_1 = extra_col_1.encode()
            extra_col_2 = extra_col_2.encode()
        self.conn.stmtcachesize = 0
        await self.cursor.execute(f"delete from Test{lob_type}s")
        await self.conn.commit()
        data = (1, main_col, 8, extra_col_1, 15, extra_col_2)
        await self.cursor.execute(
            f"""
            insert into Test{lob_type}s (IntCol, {lob_type}Col,
                ExtraNumCol1, Extra{lob_type}Col1, ExtraNumCol2,
                Extra{lob_type}Col2)
            values (:1, :2, :3, :4, :5, :6)
            """,
            data,
        )
        with test_env.DefaultsContextManager("fetch_lobs", False):
            await self.cursor.execute(f"select * from Test{lob_type}s")
            self.assertEqual(await self.cursor.fetchone(), data)

    async def __test_fetch_lobs_direct(self, lob_type):
        await self.cursor.execute(f"delete from Test{lob_type}s")
        await self.conn.commit()
        data = []
        long_string = ""
        for i in range(1, 11):
            if i > 0:
                char = chr(ord("A") + i - 1)
                long_string += char * 25000
            if lob_type == "BLOB":
                data.append((i, long_string.encode()))
            else:
                data.append((i, long_string))
        await self.cursor.executemany(
            f"""
            insert into Test{lob_type}s (IntCol, {lob_type}Col)
            values (:1, :2)
            """,
            data,
        )
        with test_env.DefaultsContextManager("fetch_lobs", False):
            await self.cursor.execute(
                f"""
                select IntCol, {lob_type}Col
                from Test{lob_type}s
                order by IntCol
                """
            )
            self.assertEqual(await self.cursor.fetchall(), data)

    async def __test_lob_operations(self, lob_type):
        await self.cursor.execute(f"delete from Test{lob_type}s")
        await self.conn.commit()
        self.cursor.setinputsizes(long_string=getattr(oracledb, lob_type))
        long_string = "X" * 75000
        write_value = "TEST"
        if lob_type == "BLOB":
            long_string = long_string.encode("ascii")
            write_value = write_value.encode("ascii")
        await self.cursor.execute(
            f"""
            insert into Test{lob_type}s (IntCol, {lob_type}Col)
            values (:integer_value, :long_string)
            """,
            integer_value=1,
            long_string=long_string,
        )
        await self.cursor.execute(
            f"""
            select {lob_type}Col
            from Test{lob_type}s
            where IntCol = 1
            """
        )
        (lob,) = await self.cursor.fetchone()
        self.assertFalse(await lob.isopen())
        await lob.open()
        with self.assertRaisesFullCode("ORA-22293"):
            await lob.open()
        self.assertTrue(await lob.isopen())
        await lob.close()
        with self.assertRaisesFullCode("ORA-22289"):
            await lob.close()
        self.assertFalse(await lob.isopen())
        self.assertEqual(await lob.size(), 75000)
        await lob.write(write_value, 75001)
        self.assertEqual(await lob.size(), 75000 + len(write_value))
        with self.assertRaisesFullCode("DPY-2030"):
            await lob.read(0)
        with self.assertRaisesFullCode("DPY-2030"):
            await lob.read(-25)
        self.assertEqual(await lob.read(), long_string + write_value)
        await lob.write(write_value, 1)
        self.assertEqual(
            await lob.read(), write_value + long_string[4:] + write_value
        )
        await lob.trim(25000)
        self.assertEqual(await lob.size(), 25000)
        await lob.trim(newSize=10000)
        self.assertEqual(await lob.size(), 10000)
        with self.assertRaisesFullCode("DPY-2014"):
            await lob.trim(new_size=50, newSize=60)
        with self.assertRaises(TypeError):
            await lob.trim(new_size="10000")
        await lob.trim(new_size=40)
        self.assertEqual(await lob.size(), 40)
        await lob.trim()
        self.assertEqual(await lob.size(), 0)
        self.assertIsInstance(await lob.getchunksize(), int)

    async def __test_temporary_lob(self, lob_type):
        await self.cursor.execute(f"delete from Test{lob_type}s")
        value = "A test string value"
        if lob_type == "BLOB":
            value = value.encode("ascii")
        db_type = getattr(oracledb, f"DB_TYPE_{lob_type}")
        lob = await self.conn.createlob(db_type, value)
        await self.cursor.execute(
            f"""
            insert into Test{lob_type}s (IntCol, {lob_type}Col)
            values (:int_val, :lob_val)
            """,
            int_val=1,
            lob_val=lob,
        )
        await self.conn.commit()
        await self.cursor.execute(f"select {lob_type}Col from Test{lob_type}s")
        (lob,) = await self.cursor.fetchone()
        self.assertEqual(await lob.read(), value)

    async def __validate_query(self, rows, lob_type):
        long_string = ""
        db_type = getattr(oracledb, f"DB_TYPE_{lob_type}")
        for row in rows:
            integer_value, lob = row
            self.assertEqual(lob.type, db_type)
            if integer_value == 0:
                self.assertEqual(await lob.size(), 0)
                expected_value = ""
                if lob_type == "BLOB":
                    expected_value = expected_value.encode()
                self.assertEqual(await lob.read(), expected_value)
            else:
                char = chr(ord("A") + integer_value - 1)
                prev_char = chr(ord("A") + integer_value - 2)
                long_string += char * 25000
                if lob_type == "BLOB":
                    expected_value = long_string.encode("ascii")
                    char = char.encode("ascii")
                    prev_char = prev_char.encode("ascii")
                else:
                    expected_value = long_string
                self.assertEqual(await lob.size(), len(expected_value))
                self.assertEqual(await lob.read(), expected_value)
                self.assertEqual(await lob.read(len(expected_value)), char)
            if integer_value > 1:
                offset = (integer_value - 1) * 25000 - 4
                string = prev_char * 5 + char * 5
                self.assertEqual(await lob.read(offset, 10), string)

    async def test_5700(self):
        "5700 - test binding a LOB value directly"
        await self.cursor.execute("delete from TestCLOBs")
        await self.cursor.execute(
            """
            insert into TestCLOBs
            (IntCol, ClobCol)
            values (1, 'Short value')
            """
        )
        await self.cursor.execute("select ClobCol from TestCLOBs")
        (lob,) = await self.cursor.fetchone()
        await self.cursor.execute(
            """
            insert into TestCLOBs
            (IntCol, ClobCol)
            values (2, :value)
            """,
            value=lob,
        )
        await self.conn.commit()

    async def test_5701(self):
        "5701 - test cursor description is accurate for BLOBs"
        await self.cursor.execute("select IntCol, BlobCol from TestBLOBs")
        expected_value = [
            ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, 0),
            ("BLOBCOL", oracledb.DB_TYPE_BLOB, None, None, None, None, 0),
        ]
        self.assertEqual(self.cursor.description, expected_value)

    async def test_5702(self):
        "5703 - test binding and fetching BLOB data (indirectly)"
        await self.__perform_test("BLOB", oracledb.DB_TYPE_LONG_RAW)

    async def test_5703(self):
        "5703 - test operations on BLOBs"
        await self.__test_lob_operations("BLOB")

    async def test_5704(self):
        "5704 - test cursor description is accurate for CLOBs"
        await self.cursor.execute("select IntCol, ClobCol from TestCLOBs")
        expected_value = [
            ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
            ("CLOBCOL", oracledb.DB_TYPE_CLOB, None, None, None, None, False),
        ]
        self.assertEqual(self.cursor.description, expected_value)

    async def test_5705(self):
        "5705 - test binding and fetching CLOB data (indirectly)"
        await self.__perform_test("CLOB", oracledb.DB_TYPE_LONG)

    async def test_5706(self):
        "5706 - test operations on CLOBs"
        await self.__test_lob_operations("CLOB")

    async def test_5707(self):
        "5707 - test creating a temporary BLOB"
        await self.__test_temporary_lob("BLOB")

    async def test_5708(self):
        "5708 - test creating a temporary CLOB"
        await self.__test_temporary_lob("CLOB")

    async def test_5709(self):
        "5709 - test creating a temporary NCLOB"
        await self.__test_temporary_lob("NCLOB")

    async def test_5710(self):
        "5710 - test retrieving data from a CLOB after multiple fetches"
        self.cursor.arraysize = 1
        await self.__perform_test("CLOB", oracledb.DB_TYPE_LONG)

    async def test_5711(self):
        "5711 - test cursor description is accurate for NCLOBs"
        await self.cursor.execute("select IntCol, NClobCol from TestNCLOBs")
        expected_value = [
            ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, 0),
            ("NCLOBCOL", oracledb.DB_TYPE_NCLOB, None, None, None, None, 0),
        ]
        self.assertEqual(self.cursor.description, expected_value)

    async def test_5712(self):
        "5712 - test binding and fetching NCLOB data (with non-ASCII chars)"
        value = "\u03b4\u4e2a"
        await self.cursor.execute("delete from TestNCLOBs")
        self.cursor.setinputsizes(val=oracledb.DB_TYPE_NVARCHAR)
        await self.cursor.execute(
            """
            insert into TestNCLOBs (IntCol, NClobCol)
            values (1, :val)
            """,
            val=value,
        )
        await self.conn.commit()
        await self.cursor.execute("select NCLOBCol from TestNCLOBs")
        (nclob,) = await self.cursor.fetchone()
        self.cursor.setinputsizes(val=oracledb.DB_TYPE_NVARCHAR)
        await self.cursor.execute(
            "update TestNCLOBs set NCLOBCol = :val",
            val=await nclob.read() + value,
        )
        await self.cursor.execute("select NCLOBCol from TestNCLOBs")
        (nclob,) = await self.cursor.fetchone()
        self.assertEqual(await nclob.read(), value + value)

    async def test_5713(self):
        "5713 - test binding and fetching NCLOB data (indirectly)"
        await self.__perform_test("NCLOB", oracledb.DB_TYPE_LONG)

    async def test_5714(self):
        "5714 - test operations on NCLOBs"
        await self.__test_lob_operations("NCLOB")

    @unittest.skipIf(
        test_env.get_is_implicit_pooling(),
        "sessions can change with implicit pooling",
    )
    async def test_5715(self):
        "5715 - test temporary LOBs"
        await self.cursor.execute(
            "select sys_context('USERENV', 'SID') from dual"
        )
        (sid,) = await self.cursor.fetchone()
        temp_lobs = await self.__get_temp_lobs(sid)
        with self.conn.cursor() as cursor:
            cursor.arraysize = 27
            self.assertEqual(temp_lobs, 0)
            await cursor.execute(
                "select extract(xmlcol, '/').getclobval() from TestXML"
            )
            async for (lob,) in cursor:
                await lob.read()
                del lob
        temp_lobs = await self.__get_temp_lobs(sid)
        self.assertEqual(temp_lobs, 0)

    async def test_5716(self):
        "5716 - test read/write temporary LOBs using supplemental characters"
        charset = await test_env.get_charset_async()
        if charset != "AL32UTF8":
            self.skipTest("Database character set must be AL32UTF8")
        supplemental_chars = (
            "𠜎 𠜱 𠝹 𠱓 𠱸 𠲖 𠳏 𠳕 𠴕 𠵼 𠵿 𠸎 𠸏 𠹷 𠺝 𠺢 𠻗 𠻹 𠻺 𠼭 𠼮 "
            "𠽌 𠾴 𠾼 𠿪 𡁜 𡁯 𡁵 𡁶 𡁻 𡃁 𡃉 𡇙 𢃇 𢞵 𢫕 𢭃 𢯊 𢱑 𢱕 𢳂 𢴈 "
            "𢵌 𢵧 𢺳 𣲷 𤓓 𤶸 𤷪 𥄫 𦉘 𦟌 𦧲 𦧺 𧨾 𨅝 𨈇 𨋢 𨳊 𨳍 𨳒 𩶘"
        )
        await self.cursor.execute("delete from TestCLOBs")
        lob = await self.conn.createlob(
            oracledb.DB_TYPE_CLOB, supplemental_chars
        )
        await self.cursor.execute(
            """
            insert into TestCLOBs
            (IntCol, ClobCol)
            values (1, :val)
            """,
            [lob],
        )
        await self.conn.commit()
        await self.cursor.execute("select ClobCol from TestCLOBs")
        (lob,) = await self.cursor.fetchone()
        self.assertEqual(await lob.read(), supplemental_chars)

    async def test_5717(self):
        "5717 - test fetching BLOB as bytes"
        await self.__test_fetch_lobs_direct("BLOB")

    async def test_5718(self):
        "5718 - test fetching CLOB as str"
        await self.__test_fetch_lobs_direct("CLOB")

    async def test_5719(self):
        "5719 - test fetching NCLOB as str"
        await self.__test_fetch_lobs_direct("NCLOB")

    async def test_5720(self):
        "5720 - test bind ordering with BLOB"
        await self.__test_bind_ordering("BLOB")

    async def test_5721(self):
        "5721 - test bind ordering with CLOB"
        await self.__test_bind_ordering("CLOB")

    async def test_5722(self):
        "5722 - test bind ordering with NCLOB"
        await self.__test_bind_ordering("NCLOB")

    async def test_5723(self):
        "5723 - test creating a lob with an invalid type"
        with self.assertRaises(TypeError):
            await self.conn.createlob(oracledb.DB_TYPE_NUMBER)
        with self.assertRaises(TypeError):
            await self.conn.createlob(oracledb.DB_TYPE_BFILE)

    async def test_5724(self):
        "5724 - test creation of temporary LOBs with varying data"
        cases = [
            (oracledb.DB_TYPE_BLOB, b"test_5724A", b"!", b"test_5724A!"),
            (oracledb.DB_TYPE_BLOB, "test_5724B", "!", b"test_5724B!"),
            (oracledb.DB_TYPE_CLOB, b"test_5724C", b"!", "test_5724C!"),
            (oracledb.DB_TYPE_CLOB, "test_5724D", "!", "test_5724D!"),
            (oracledb.DB_TYPE_NCLOB, b"test_5724E", b"!", "test_5724E!"),
            (oracledb.DB_TYPE_NCLOB, "test_5724F", "!", "test_5724F!"),
        ]
        for typ, initial_data, additional_data, expected_result in cases:
            with self.subTest():
                lob = await self.conn.createlob(typ, initial_data)
                await lob.write(additional_data, len(initial_data) + 1)
                self.assertEqual(await lob.read(), expected_result)

    async def test_5725(self):
        "5725 - test reading and writing a LOB with a closed connection"
        types = [
            oracledb.DB_TYPE_BLOB,
            oracledb.DB_TYPE_CLOB,
            oracledb.DB_TYPE_NCLOB,
        ]
        for typ in types:
            conn = await test_env.get_connection(use_async=True)
            lob = await conn.createlob(typ, "Temp LOB")
            await conn.close()
            with self.assertRaisesFullCode("DPY-1001"):
                await lob.read()
            with self.assertRaisesFullCode("DPY-1001"):
                await lob.write("x")

    async def test_5726(self):
        "5726 - test reading a non-existent directory"
        directory_name = "TEST_5726_MISSING_DIR"
        file_name = "test_5726_missing_file.txt"
        await self.cursor.execute(
            "select BFILENAME(:1, :2) from dual", [directory_name, file_name]
        )
        (bfile,) = await self.cursor.fetchone()
        self.assertEqual(bfile.getfilename(), (directory_name, file_name))
        with self.assertRaisesFullCode("ORA-22285"):
            await bfile.fileexists()
        with self.assertRaisesFullCode("ORA-22285"):
            await bfile.read()

    async def test_5727(self):
        "5727 - test using BFILE methods on non-BFILE LOBs"
        types = [
            oracledb.DB_TYPE_BLOB,
            oracledb.DB_TYPE_CLOB,
            oracledb.DB_TYPE_NCLOB,
        ]
        for typ in types:
            lob = await self.conn.createlob(typ)
            with self.assertRaisesFullCode("DPY-3026"):
                lob.getfilename()
            with self.assertRaisesFullCode("DPY-3026"):
                lob.setfilename("not_relevant", "not_relevant")
            with self.assertRaisesFullCode("DPY-3026"):
                await lob.fileexists()


if __name__ == "__main__":
    test_env.run_test_cases()
