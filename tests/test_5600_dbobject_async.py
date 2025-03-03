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
5600 - Module for testing object variables with asyncio
"""

import datetime
import decimal
import unittest

import oracledb
import test_env


@unittest.skipUnless(
    test_env.get_is_thin(), "asyncio not supported in thick mode"
)
class TestCase(test_env.BaseAsyncTestCase):
    maxDiff = None

    async def __test_data(
        self, expected_int_value, expected_obj_value, expected_array_value
    ):
        int_value, object_value, array_value = await self.cursor.fetchone()
        if object_value is not None:
            object_value = await self.get_db_object_as_plain_object(
                object_value
            )
        if array_value is not None:
            array_value = array_value.aslist()
        self.assertEqual(int_value, expected_int_value)
        self.assertEqual(object_value, expected_obj_value)
        self.assertEqual(array_value, expected_array_value)

    async def test_5600(self):
        "5600 - test binding an object (IN)"
        type_obj = await self.conn.gettype("UDT_OBJECT")
        obj = type_obj.newobject()
        obj.NUMBERVALUE = 13
        obj.STRINGVALUE = "Test String"
        result = await self.cursor.callfunc(
            "pkg_TestBindObject.GetStringRep", str, [obj]
        )
        exp = "udt_Object(13, 'Test String', null, null, null, null, null)"
        self.assertEqual(result, exp)
        obj.NUMBERVALUE = None
        obj.STRINGVALUE = "Test With Dates"
        obj.DATEVALUE = datetime.datetime(2016, 2, 10)
        obj.TIMESTAMPVALUE = datetime.datetime(2016, 2, 10, 14, 13, 50)
        result = await self.cursor.callfunc(
            "pkg_TestBindObject.GetStringRep", str, [obj]
        )
        expected_value = (
            "udt_Object(null, 'Test With Dates', null, "
            "to_date('2016-02-10', 'YYYY-MM-DD'), "
            "to_timestamp('2016-02-10 14:13:50', "
            "'YYYY-MM-DD HH24:MI:SS'), "
            "null, null)"
        )
        self.assertEqual(result, expected_value)
        obj.DATEVALUE = None
        obj.TIMESTAMPVALUE = None
        sub_type_obj = await self.conn.gettype("UDT_SUBOBJECT")
        sub_obj = sub_type_obj.newobject()
        sub_obj.SUBNUMBERVALUE = decimal.Decimal("18.25")
        sub_obj.SUBSTRINGVALUE = "Sub String"
        obj.SUBOBJECTVALUE = sub_obj
        result = await self.cursor.callfunc(
            "pkg_TestBindObject.GetStringRep", str, [obj]
        )
        expected_value = (
            "udt_Object(null, 'Test With Dates', null, null, "
            "null, udt_SubObject(18.25, 'Sub String'), null)"
        )
        self.assertEqual(result, expected_value)

    async def test_5601(self):
        "5601 - test copying an object"
        type_obj = await self.conn.gettype("UDT_OBJECT")
        obj = type_obj()
        obj.NUMBERVALUE = 5124
        obj.STRINGVALUE = "A test string"
        obj.DATEVALUE = datetime.datetime(2016, 2, 24)
        obj.TIMESTAMPVALUE = datetime.datetime(2016, 2, 24, 13, 39, 10)
        copied_obj = obj.copy()
        self.assertEqual(obj.NUMBERVALUE, copied_obj.NUMBERVALUE)
        self.assertEqual(obj.STRINGVALUE, copied_obj.STRINGVALUE)
        self.assertEqual(obj.DATEVALUE, copied_obj.DATEVALUE)
        self.assertEqual(obj.TIMESTAMPVALUE, copied_obj.TIMESTAMPVALUE)

    async def test_5602(self):
        "5602 - test fetching objects"
        await self.cursor.execute(
            """
            select IntCol, ObjectCol, ArrayCol
            from TestObjects
            order by IntCol
            """
        )
        expected_value = [
            ("INTCOL", oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
            (
                "OBJECTCOL",
                oracledb.DB_TYPE_OBJECT,
                None,
                None,
                None,
                None,
                True,
            ),
            (
                "ARRAYCOL",
                oracledb.DB_TYPE_OBJECT,
                None,
                None,
                None,
                None,
                True,
            ),
        ]
        self.assertEqual(self.cursor.description, expected_value)
        expected_value = (
            1,
            "First row",
            "First     ",
            "N First Row",
            "N First   ",
            b"Raw Data 1",
            2,
            5,
            12.125,
            0.5,
            12.5,
            25.25,
            50.125,
            datetime.datetime(2007, 3, 6, 0, 0, 0),
            datetime.datetime(2008, 9, 12, 16, 40),
            datetime.datetime(2009, 10, 13, 17, 50),
            oracledb.Timestamp(2010, 11, 14, 18, 55),
            "Short CLOB value",
            "Short NCLOB Value",
            b"Short BLOB value",
            (11, "Sub object 1"),
            [(5, "first element"), (6, "second element")],
        )
        await self.__test_data(1, expected_value, [5, 10, None, 20])
        await self.__test_data(2, None, [3, None, 9, 12, 15])
        expected_value = (
            3,
            "Third row",
            "Third     ",
            "N Third Row",
            "N Third   ",
            b"Raw Data 3",
            4,
            10,
            6.5,
            0.75,
            43.25,
            86.5,
            192.125,
            datetime.datetime(2007, 6, 21, 0, 0, 0),
            datetime.datetime(2007, 12, 13, 7, 30, 45),
            datetime.datetime(2017, 6, 21, 23, 18, 45),
            oracledb.Timestamp(2017, 7, 21, 8, 27, 13),
            "Another short CLOB value",
            "Another short NCLOB Value",
            b"Yet another short BLOB value",
            (13, "Sub object 3"),
            [
                (10, "element #1"),
                (20, "element #2"),
                (30, "element #3"),
                (40, "element #4"),
            ],
        )
        await self.__test_data(3, expected_value, None)

    async def test_5603(self):
        "5603 - test getting object type"
        type_obj = await self.conn.gettype("UDT_OBJECT")
        self.assertFalse(type_obj.iscollection)
        self.assertEqual(type_obj.schema, self.conn.username.upper())
        self.assertEqual(type_obj.name, "UDT_OBJECT")
        sub_object_value_type = await self.conn.gettype("UDT_SUBOBJECT")
        sub_object_array_type = await self.conn.gettype("UDT_OBJECTARRAY")
        expected_metadata = [
            ("NUMBERVALUE", oracledb.DB_TYPE_NUMBER, 0, -127, None),
            ("STRINGVALUE", oracledb.DB_TYPE_VARCHAR, None, None, 60),
            ("FIXEDCHARVALUE", oracledb.DB_TYPE_CHAR, None, None, 10),
            ("NSTRINGVALUE", oracledb.DB_TYPE_NVARCHAR, None, None, 120),
            ("NFIXEDCHARVALUE", oracledb.DB_TYPE_NCHAR, None, None, 20),
            ("RAWVALUE", oracledb.DB_TYPE_RAW, None, None, 16),
            ("INTVALUE", oracledb.DB_TYPE_NUMBER, 38, 0, None),
            ("SMALLINTVALUE", oracledb.DB_TYPE_NUMBER, 38, 0, None),
            ("REALVALUE", oracledb.DB_TYPE_NUMBER, 63, -127, None),
            ("DOUBLEPRECISIONVALUE", oracledb.DB_TYPE_NUMBER, 126, -127, None),
            ("FLOATVALUE", oracledb.DB_TYPE_NUMBER, 126, -127, None),
            (
                "BINARYFLOATVALUE",
                oracledb.DB_TYPE_BINARY_FLOAT,
                None,
                None,
                None,
            ),
            (
                "BINARYDOUBLEVALUE",
                oracledb.DB_TYPE_BINARY_DOUBLE,
                None,
                None,
                None,
            ),
            ("DATEVALUE", oracledb.DB_TYPE_DATE, None, None, None),
            ("TIMESTAMPVALUE", oracledb.DB_TYPE_TIMESTAMP, None, None, None),
            (
                "TIMESTAMPTZVALUE",
                oracledb.DB_TYPE_TIMESTAMP_TZ,
                None,
                None,
                None,
            ),
            (
                "TIMESTAMPLTZVALUE",
                oracledb.DB_TYPE_TIMESTAMP_LTZ,
                None,
                None,
                None,
            ),
            ("CLOBVALUE", oracledb.DB_TYPE_CLOB, None, None, None),
            ("NCLOBVALUE", oracledb.DB_TYPE_NCLOB, None, None, None),
            ("BLOBVALUE", oracledb.DB_TYPE_BLOB, None, None, None),
            ("SUBOBJECTVALUE", sub_object_value_type, None, None, None),
            ("SUBOBJECTARRAY", sub_object_array_type, None, None, None),
        ]
        actual_metadata = [
            (attr.name, attr.type, attr.precision, attr.scale, attr.max_size)
            for attr in type_obj.attributes
        ]
        self.assertEqual(actual_metadata, expected_metadata)
        self.assertEqual(sub_object_array_type.iscollection, True)
        self.assertEqual(sub_object_array_type.attributes, [])

    async def test_5604(self):
        "5604 - test object type data"
        await self.cursor.execute(
            """
            select ObjectCol
            from TestObjects
            where ObjectCol is not null
              and rownum <= 1
            """
        )
        (obj,) = await self.cursor.fetchone()
        self.assertEqual(obj.type.schema, self.conn.username.upper())
        self.assertEqual(obj.type.name, "UDT_OBJECT")
        self.assertEqual(obj.type.attributes[0].name, "NUMBERVALUE")

    async def test_5605(self):
        "5605 - test inserting and then querying object with all data types"
        await self.cursor.execute("delete from TestClobs")
        await self.cursor.execute("delete from TestNClobs")
        await self.cursor.execute("delete from TestBlobs")
        await self.cursor.execute("delete from TestObjects where IntCol > 3")
        await self.cursor.execute(
            """
            insert into TestClobs (IntCol, ClobCol)
            values (1, 'A short CLOB')
            """
        )
        await self.cursor.execute(
            """
            insert into TestNClobs (IntCol, NClobCol)
            values (1, 'A short NCLOB')
            """
        )
        await self.cursor.execute(
            """
            insert into TestBlobs (IntCol, BlobCol)
            values (1, utl_raw.cast_to_raw('A short BLOB'))
            """
        )
        await self.conn.commit()
        await self.cursor.execute("select CLOBCol from TestClobs")
        (clob,) = await self.cursor.fetchone()
        await self.cursor.execute("select NCLOBCol from TestNClobs")
        (nclob,) = await self.cursor.fetchone()
        await self.cursor.execute("select BLOBCol from TestBlobs")
        (blob,) = await self.cursor.fetchone()
        type_obj = await self.conn.gettype("UDT_OBJECT")
        obj = type_obj.newobject()
        obj.NUMBERVALUE = 5
        obj.STRINGVALUE = "A string"
        obj.FIXEDCHARVALUE = "Fixed str"
        obj.NSTRINGVALUE = "A NCHAR string"
        obj.NFIXEDCHARVALUE = "Fixed N"
        obj.RAWVALUE = b"Raw Value"
        obj.INTVALUE = 27
        obj.SMALLINTVALUE = 13
        obj.REALVALUE = 184.875
        obj.DOUBLEPRECISIONVALUE = 1.375
        obj.FLOATVALUE = 23.75
        obj.DATEVALUE = datetime.date(2017, 5, 9)
        obj.TIMESTAMPVALUE = datetime.datetime(2017, 5, 9, 9, 41, 13)
        obj.TIMESTAMPTZVALUE = datetime.datetime(1986, 8, 2, 15, 27, 38)
        obj.TIMESTAMPLTZVALUE = datetime.datetime(1999, 11, 12, 23, 5, 2)
        obj.BINARYFLOATVALUE = 14.25
        obj.BINARYDOUBLEVALUE = 29.1625
        obj.CLOBVALUE = clob
        obj.NCLOBVALUE = nclob
        obj.BLOBVALUE = blob
        sub_type_obj = await self.conn.gettype("UDT_SUBOBJECT")
        sub_obj = sub_type_obj.newobject()
        sub_obj.SUBNUMBERVALUE = 23
        sub_obj.SUBSTRINGVALUE = "Substring value"
        obj.SUBOBJECTVALUE = sub_obj
        await self.cursor.execute(
            """
            insert into TestObjects (IntCol, ObjectCol)
            values (4, :obj)
            """,
            obj=obj,
        )
        await self.cursor.execute(
            """
            select IntCol, ObjectCol, ArrayCol
            from TestObjects
            where IntCol = 4
            """
        )
        expected_value = (
            5,
            "A string",
            "Fixed str ",
            "A NCHAR string",
            "Fixed N   ",
            b"Raw Value",
            27,
            13,
            184.875,
            1.375,
            23.75,
            14.25,
            29.1625,
            datetime.datetime(2017, 5, 9, 0, 0, 0),
            datetime.datetime(2017, 5, 9, 9, 41, 13),
            datetime.datetime(1986, 8, 2, 15, 27, 38),
            oracledb.Timestamp(1999, 11, 12, 23, 5, 2),
            "A short CLOB",
            "A short NCLOB",
            b"A short BLOB",
            (23, "Substring value"),
            None,
        )
        await self.__test_data(4, expected_value, None)

        obj.CLOBVALUE = await self.conn.createlob(oracledb.DB_TYPE_CLOB)
        obj.NCLOBVALUE = await self.conn.createlob(oracledb.DB_TYPE_NCLOB)
        obj.BLOBVALUE = await self.conn.createlob(oracledb.DB_TYPE_BLOB)
        await obj.CLOBVALUE.write("A short CLOB (modified)")
        await obj.NCLOBVALUE.write("A short NCLOB (modified)")
        await obj.BLOBVALUE.write(b"A short BLOB (modified)")
        await self.cursor.execute(
            """
            insert into TestObjects (IntCol, ObjectCol)
            values (5, :obj)
            """,
            obj=obj,
        )
        await self.cursor.execute(
            """
            select IntCol, ObjectCol, ArrayCol
            from TestObjects
            where IntCol = 5
            """
        )
        expected_value = (
            5,
            "A string",
            "Fixed str ",
            "A NCHAR string",
            "Fixed N   ",
            b"Raw Value",
            27,
            13,
            184.875,
            1.375,
            23.75,
            14.25,
            29.1625,
            datetime.datetime(2017, 5, 9, 0, 0, 0),
            datetime.datetime(2017, 5, 9, 9, 41, 13),
            datetime.datetime(1986, 8, 2, 15, 27, 38),
            oracledb.Timestamp(1999, 11, 12, 23, 5, 2),
            "A short CLOB (modified)",
            "A short NCLOB (modified)",
            b"A short BLOB (modified)",
            (23, "Substring value"),
            None,
        )
        await self.__test_data(5, expected_value, None)
        await self.conn.rollback()

    async def test_5606(self):
        "5606 - test trying to find an object type that does not exist"
        with self.assertRaises(TypeError):
            await self.conn.gettype(2)
        with self.assertRaisesFullCode("DPY-2035"):
            await self.conn.gettype("A TYPE THAT DOES NOT EXIST")

    async def test_5607(self):
        "5607 - test appending an object of the wrong type to a collection"
        collection_obj_type = await self.conn.gettype("UDT_OBJECTARRAY")
        collection_obj = collection_obj_type.newobject()
        array_obj_type = await self.conn.gettype("UDT_ARRAY")
        array_obj = array_obj_type.newobject()
        with self.assertRaisesFullCode("DPY-2008"):
            collection_obj.append(array_obj)

    async def test_5608(self):
        "5608 - test that referencing a sub object affects the parent object"
        obj_type = await self.conn.gettype("UDT_OBJECT")
        sub_obj_type = await self.conn.gettype("UDT_SUBOBJECT")
        obj = obj_type.newobject()
        obj.SUBOBJECTVALUE = sub_obj_type.newobject()
        obj.SUBOBJECTVALUE.SUBNUMBERVALUE = 5
        obj.SUBOBJECTVALUE.SUBSTRINGVALUE = "Substring"
        self.assertEqual(obj.SUBOBJECTVALUE.SUBNUMBERVALUE, 5)
        self.assertEqual(obj.SUBOBJECTVALUE.SUBSTRINGVALUE, "Substring")

    async def test_5609(self):
        "5609 - test accessing sub object after parent object destroyed"
        obj_type = await self.conn.gettype("UDT_OBJECT")
        sub_obj_type = await self.conn.gettype("UDT_SUBOBJECT")
        array_type = await self.conn.gettype("UDT_OBJECTARRAY")
        sub_obj1 = sub_obj_type.newobject()
        sub_obj1.SUBNUMBERVALUE = 2
        sub_obj1.SUBSTRINGVALUE = "AB"
        sub_obj2 = sub_obj_type.newobject()
        sub_obj2.SUBNUMBERVALUE = 3
        sub_obj2.SUBSTRINGVALUE = "CDE"
        obj = obj_type.newobject()
        obj.SUBOBJECTARRAY = array_type.newobject([sub_obj1, sub_obj2])
        sub_obj_array = obj.SUBOBJECTARRAY
        del obj
        self.assertEqual(
            await self.get_db_object_as_plain_object(sub_obj_array),
            [(2, "AB"), (3, "CDE")],
        )

    async def test_5610(self):
        "5610 - test assigning an object of wrong type to an object attribute"
        obj_type = await self.conn.gettype("UDT_OBJECT")
        obj = obj_type.newobject()
        wrong_obj_type = await self.conn.gettype("UDT_OBJECTARRAY")
        wrong_obj = wrong_obj_type.newobject()
        with self.assertRaisesFullCode("DPY-2008"):
            setattr(obj, "SUBOBJECTVALUE", wrong_obj)

    async def test_5611(self):
        "5611 - test setting value of object variable to wrong object type"
        obj_type = await self.conn.gettype("UDT_OBJECT")
        wrong_obj_type = await self.conn.gettype("UDT_OBJECTARRAY")
        wrong_obj = wrong_obj_type.newobject()
        var = self.cursor.var(obj_type)
        with self.assertRaisesFullCode("DPY-2008"):
            var.setvalue(0, wrong_obj)

    async def test_5612(self):
        "5612 - test trimming a number of elements from a collection"
        sub_obj_type = await self.conn.gettype("UDT_SUBOBJECT")
        array_type = await self.conn.gettype("UDT_OBJECTARRAY")
        data = [(1, "AB"), (2, "CDE"), (3, "FGH"), (4, "IJK"), (5, "LMN")]
        array_obj = array_type()
        for num_val, str_val in data:
            subObj = sub_obj_type()
            subObj.SUBNUMBERVALUE = num_val
            subObj.SUBSTRINGVALUE = str_val
            array_obj.append(subObj)
        self.assertEqual(
            await self.get_db_object_as_plain_object(array_obj), data
        )
        array_obj.trim(2)
        self.assertEqual(
            await self.get_db_object_as_plain_object(array_obj), data[:3]
        )
        array_obj.trim(1)
        self.assertEqual(
            await self.get_db_object_as_plain_object(array_obj), data[:2]
        )
        array_obj.trim(0)
        self.assertEqual(
            await self.get_db_object_as_plain_object(array_obj), data[:2]
        )
        array_obj.trim(2)
        self.assertEqual(
            await self.get_db_object_as_plain_object(array_obj), []
        )

    async def test_5613(self):
        "5613 - test the metadata of a SQL type"
        user = test_env.get_main_user()
        typ = await self.conn.gettype("UDT_OBJECTARRAY")
        self.assertEqual(typ.schema, user.upper())
        self.assertEqual(typ.name, "UDT_OBJECTARRAY")
        self.assertIsNone(typ.package_name)
        self.assertEqual(typ.element_type.schema, user.upper())
        self.assertEqual(typ.element_type.name, "UDT_SUBOBJECT")
        self.assertIsNone(typ.element_type.package_name)

    async def test_5614(self):
        "5614 - test the metadata of a PL/SQL type"
        user = test_env.get_main_user()
        typ = await self.conn.gettype("PKG_TESTSTRINGARRAYS.UDT_STRINGLIST")
        self.assertEqual(typ.schema, user.upper())
        self.assertEqual(typ.name, "UDT_STRINGLIST")
        self.assertEqual(typ.package_name, "PKG_TESTSTRINGARRAYS")
        self.assertEqual(typ.element_type, oracledb.DB_TYPE_VARCHAR)

    async def test_5615(self):
        "5615 - test collection with thousands of entries"
        typ = await self.conn.gettype("PKG_TESTNUMBERARRAYS.UDT_NUMBERLIST")
        obj = typ.newobject()
        obj.setelement(1, 1)
        running_total = 1
        for i in range(1, 35000):
            running_total += i + 1
            obj.append(running_total)
        result = await self.cursor.callfunc(
            "pkg_TestNumberArrays.TestInArrays", int, (2327, obj)
        )
        self.assertEqual(result, 7146445847327)

    async def test_5616(self):
        "5616 - test %ROWTYPE with all types"
        sub_obj_type = await self.conn.gettype("UDT_SUBOBJECT")
        sub_arr_type = await self.conn.gettype("UDT_OBJECTARRAY")
        expected_metadata = [
            ("NUMBERVALUE", oracledb.DB_TYPE_NUMBER, 0, -127, None),
            ("STRINGVALUE", oracledb.DB_TYPE_VARCHAR, None, None, 60),
            ("FIXEDCHARVALUE", oracledb.DB_TYPE_CHAR, None, None, 10),
            ("NSTRINGVALUE", oracledb.DB_TYPE_NVARCHAR, None, None, 120),
            ("NFIXEDCHARVALUE", oracledb.DB_TYPE_NCHAR, None, None, 20),
            ("RAWVALUE", oracledb.DB_TYPE_RAW, None, None, 16),
            ("INTVALUE", oracledb.DB_TYPE_NUMBER, 38, 0, None),
            ("SMALLINTVALUE", oracledb.DB_TYPE_NUMBER, 38, 0, None),
            ("REALVALUE", oracledb.DB_TYPE_NUMBER, 63, -127, None),
            ("DOUBLEPRECISIONVALUE", oracledb.DB_TYPE_NUMBER, 126, -127, None),
            ("FLOATVALUE", oracledb.DB_TYPE_NUMBER, 126, -127, None),
            (
                "BINARYFLOATVALUE",
                oracledb.DB_TYPE_BINARY_FLOAT,
                None,
                None,
                None,
            ),
            (
                "BINARYDOUBLEVALUE",
                oracledb.DB_TYPE_BINARY_DOUBLE,
                None,
                None,
                None,
            ),
            ("DATEVALUE", oracledb.DB_TYPE_DATE, None, None, None),
            ("TIMESTAMPVALUE", oracledb.DB_TYPE_TIMESTAMP, None, None, None),
            (
                "TIMESTAMPTZVALUE",
                oracledb.DB_TYPE_TIMESTAMP_TZ,
                None,
                None,
                None,
            ),
            (
                "TIMESTAMPLTZVALUE",
                oracledb.DB_TYPE_TIMESTAMP_LTZ,
                None,
                None,
                None,
            ),
            ("CLOBVALUE", oracledb.DB_TYPE_CLOB, None, None, None),
            ("NCLOBVALUE", oracledb.DB_TYPE_NCLOB, None, None, None),
            ("BLOBVALUE", oracledb.DB_TYPE_BLOB, None, None, None),
            ("SUBOBJECTVALUE", sub_obj_type, None, None, None),
            ("SUBOBJECTARRAY", sub_arr_type, None, None, None),
        ]
        obj_type = await self.conn.gettype("TESTALLTYPES%ROWTYPE")
        actual_metadata = [
            (attr.name, attr.type, attr.precision, attr.scale, attr.max_size)
            for attr in obj_type.attributes
        ]
        self.assertEqual(actual_metadata, expected_metadata)

    async def test_5617(self):
        "5617 - test collection iteration"
        await self.cursor.execute("select udt_array(5, 10, 15) from dual")
        (obj,) = await self.cursor.fetchone()
        result = [i for i in obj]
        self.assertEqual(result, [5, 10, 15])

    async def test_5618(self):
        "5618 - test insufficient privileges for gettype()"
        user = test_env.get_proxy_user()
        password = test_env.get_proxy_password()
        main_user = test_env.get_main_user().upper()
        async with await test_env.get_connection_async(
            user=user, password=password
        ) as conn:
            with self.assertRaisesFullCode("DPY-2035"):
                await conn.gettype(f"{main_user}.UDT_OBJECTARRAY")

    async def test_5619(self):
        "5619 - test nested records"
        options = [(None, None), (1, None), (None, 2), (1, 2)]
        typ = await self.conn.gettype("PKG_TESTNESTEDRECORDS.UDT_OUTER")
        for option in options:
            with self.subTest(option=option):
                value1, value2 = option
                obj = await self.cursor.callfunc(
                    "pkg_TestNestedRecords.GetOuter", typ, (value1, value2)
                )
                self.assertIsNotNone(obj.INNER1)
                self.assertIsNone(obj.INNER1.ATTR1)
                self.assertEqual(obj.INNER1.ATTR2, value1)
                self.assertIsNotNone(obj.INNER2)
                self.assertIsNone(obj.INNER2.ATTR1)
                self.assertEqual(obj.INNER2.ATTR2, value2)


if __name__ == "__main__":
    test_env.run_test_cases()
