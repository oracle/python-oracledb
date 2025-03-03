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
2300 - Module for testing object variables
"""

import datetime
import decimal
import unittest

import oracledb
import test_env


class TestCase(test_env.BaseTestCase):
    def __test_data(
        self, expected_int_value, expected_obj_value, expected_array_value
    ):
        int_value, object_value, array_value = self.cursor.fetchone()
        if object_value is not None:
            self.assertIsInstance(object_value.INTVALUE, int)
            self.assertIsInstance(object_value.SMALLINTVALUE, int)
            self.assertIsInstance(object_value.FLOATVALUE, float)
        if object_value is not None:
            object_value = self.get_db_object_as_plain_object(object_value)
        if array_value is not None:
            array_value = array_value.aslist()
        self.assertEqual(int_value, expected_int_value)
        self.assertEqual(object_value, expected_obj_value)
        self.assertEqual(array_value, expected_array_value)

    def test_2300(self):
        "2300 - test binding a null value (IN)"
        var = self.cursor.var(oracledb.DB_TYPE_OBJECT, typename="UDT_OBJECT")
        result = self.cursor.callfunc(
            "pkg_TestBindObject.GetStringRep", str, [var]
        )
        self.assertEqual(result, "null")

    def test_2301(self):
        "2301 - test binding an object (IN)"
        type_obj = self.conn.gettype("UDT_OBJECT")
        obj = type_obj.newobject()
        obj.NUMBERVALUE = 13
        obj.STRINGVALUE = "Test String"
        result = self.cursor.callfunc(
            "pkg_TestBindObject.GetStringRep", str, [obj]
        )
        exp = "udt_Object(13, 'Test String', null, null, null, null, null)"
        self.assertEqual(result, exp)
        obj.NUMBERVALUE = None
        obj.STRINGVALUE = "Test With Dates"
        obj.DATEVALUE = datetime.datetime(2016, 2, 10)
        obj.TIMESTAMPVALUE = datetime.datetime(2016, 2, 10, 14, 13, 50)
        result = self.cursor.callfunc(
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
        sub_type_obj = self.conn.gettype("UDT_SUBOBJECT")
        sub_obj = sub_type_obj.newobject()
        sub_obj.SUBNUMBERVALUE = decimal.Decimal("18.25")
        sub_obj.SUBSTRINGVALUE = "Sub String"
        obj.SUBOBJECTVALUE = sub_obj
        result = self.cursor.callfunc(
            "pkg_TestBindObject.GetStringRep", str, [obj]
        )
        expected_value = (
            "udt_Object(null, 'Test With Dates', null, null, "
            "null, udt_SubObject(18.25, 'Sub String'), null)"
        )
        self.assertEqual(result, expected_value)

    def test_2302(self):
        "2302 - test copying an object"
        type_obj = self.conn.gettype("UDT_OBJECT")
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

    def test_2303(self):
        "2303 - test getting an empty collection as a list"
        type_obj = self.conn.gettype("UDT_ARRAY")
        obj = type_obj.newobject()
        self.assertEqual(obj.aslist(), [])

    def test_2304(self):
        "2304 - test fetching objects"
        self.cursor.execute(
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
        self.__test_data(1, expected_value, [5, 10, None, 20])
        self.__test_data(2, None, [3, None, 9, 12, 15])
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
        self.__test_data(3, expected_value, None)

    def test_2305(self):
        "2305 - test getting object type"
        type_obj = self.conn.gettype("UDT_OBJECT")
        self.assertFalse(type_obj.iscollection)
        self.assertEqual(type_obj.schema, self.conn.username.upper())
        self.assertEqual(type_obj.name, "UDT_OBJECT")
        sub_object_value_type = self.conn.gettype("UDT_SUBOBJECT")
        sub_object_array_type = self.conn.gettype("UDT_OBJECTARRAY")
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

    def test_2306(self):
        "2306 - test object type data"
        self.cursor.execute(
            """
            select ObjectCol
            from TestObjects
            where ObjectCol is not null
              and rownum <= 1
            """
        )
        (obj,) = self.cursor.fetchone()
        self.assertEqual(obj.type.schema, self.conn.username.upper())
        self.assertEqual(obj.type.name, "UDT_OBJECT")
        self.assertEqual(obj.type.attributes[0].name, "NUMBERVALUE")

    def test_2307(self):
        "2307 - test inserting and then querying object with all data types"
        self.cursor.execute("delete from TestClobs")
        self.cursor.execute("delete from TestNClobs")
        self.cursor.execute("delete from TestBlobs")
        self.cursor.execute("delete from TestObjects where IntCol > 3")
        self.cursor.execute(
            """
            insert into TestClobs (IntCol, ClobCol)
            values (1, 'A short CLOB')
            """
        )
        self.cursor.execute(
            """
            insert into TestNClobs (IntCol, NClobCol)
            values (1, 'A short NCLOB')
            """
        )
        self.cursor.execute(
            """
            insert into TestBlobs (IntCol, BlobCol)
            values (1, utl_raw.cast_to_raw('A short BLOB'))
            """
        )
        self.conn.commit()
        self.cursor.execute("select CLOBCol from TestClobs")
        (clob,) = self.cursor.fetchone()
        self.cursor.execute("select NCLOBCol from TestNClobs")
        (nclob,) = self.cursor.fetchone()
        self.cursor.execute("select BLOBCol from TestBlobs")
        (blob,) = self.cursor.fetchone()
        type_obj = self.conn.gettype("UDT_OBJECT")
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
        obj.FLOATVALUE = 23.0
        obj.DATEVALUE = datetime.date(2017, 5, 9)
        obj.TIMESTAMPVALUE = datetime.datetime(2017, 5, 9, 9, 41, 13)
        obj.TIMESTAMPTZVALUE = datetime.datetime(1986, 8, 2, 15, 27, 38)
        obj.TIMESTAMPLTZVALUE = datetime.datetime(1999, 11, 12, 23, 5, 2)
        obj.BINARYFLOATVALUE = 14.25
        obj.BINARYDOUBLEVALUE = 29.1625
        obj.CLOBVALUE = clob
        obj.NCLOBVALUE = nclob
        obj.BLOBVALUE = blob
        sub_type_obj = self.conn.gettype("UDT_SUBOBJECT")
        sub_obj = sub_type_obj.newobject()
        sub_obj.SUBNUMBERVALUE = 23
        sub_obj.SUBSTRINGVALUE = "Substring value"
        obj.SUBOBJECTVALUE = sub_obj
        self.cursor.execute(
            """
            insert into TestObjects (IntCol, ObjectCol)
            values (4, :obj)
            """,
            obj=obj,
        )
        self.cursor.execute(
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
            23.0,
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
        self.__test_data(4, expected_value, None)
        obj.CLOBVALUE = "A short CLOB (modified)"
        obj.NCLOBVALUE = "A short NCLOB (modified)"
        obj.BLOBVALUE = "A short BLOB (modified)"
        self.cursor.execute(
            """
            insert into TestObjects (IntCol, ObjectCol)
            values (5, :obj)
            """,
            obj=obj,
        )
        self.cursor.execute(
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
            23.0,
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
        self.__test_data(5, expected_value, None)
        self.conn.rollback()

    def test_2308(self):
        "2308 - test trying to find an object type that does not exist"
        self.assertRaises(TypeError, self.conn.gettype, 2)
        with self.assertRaisesFullCode("DPY-2035"):
            self.conn.gettype("A TYPE THAT DOES NOT EXIST")

    def test_2309(self):
        "2309 - test appending an object of the wrong type to a collection"
        collection_obj_type = self.conn.gettype("UDT_OBJECTARRAY")
        collection_obj = collection_obj_type.newobject()
        array_obj_type = self.conn.gettype("UDT_ARRAY")
        array_obj = array_obj_type.newobject()
        with self.assertRaisesFullCode("DPY-2008"):
            collection_obj.append(array_obj)

    def test_2310(self):
        "2310 - test that referencing a sub object affects the parent object"
        obj_type = self.conn.gettype("UDT_OBJECT")
        sub_obj_type = self.conn.gettype("UDT_SUBOBJECT")
        obj = obj_type.newobject()
        obj.SUBOBJECTVALUE = sub_obj_type.newobject()
        obj.SUBOBJECTVALUE.SUBNUMBERVALUE = 5
        obj.SUBOBJECTVALUE.SUBSTRINGVALUE = "Substring"
        self.assertEqual(obj.SUBOBJECTVALUE.SUBNUMBERVALUE, 5)
        self.assertEqual(obj.SUBOBJECTVALUE.SUBSTRINGVALUE, "Substring")

    def test_2311(self):
        "2311 - test accessing sub object after parent object destroyed"
        obj_type = self.conn.gettype("UDT_OBJECT")
        sub_obj_type = self.conn.gettype("UDT_SUBOBJECT")
        array_type = self.conn.gettype("UDT_OBJECTARRAY")
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
            self.get_db_object_as_plain_object(sub_obj_array),
            [(2, "AB"), (3, "CDE")],
        )

    def test_2312(self):
        "2312 - test assigning an object of wrong type to an object attribute"
        obj_type = self.conn.gettype("UDT_OBJECT")
        obj = obj_type.newobject()
        wrong_obj_type = self.conn.gettype("UDT_OBJECTARRAY")
        wrong_obj = wrong_obj_type.newobject()
        with self.assertRaisesFullCode("DPY-2008"):
            setattr(obj, "SUBOBJECTVALUE", wrong_obj)

    def test_2313(self):
        "2313 - test setting value of object variable to wrong object type"
        wrong_obj_type = self.conn.gettype("UDT_OBJECTARRAY")
        wrong_obj = wrong_obj_type.newobject()
        var = self.cursor.var(oracledb.DB_TYPE_OBJECT, typename="UDT_OBJECT")
        with self.assertRaisesFullCode("DPY-2008"):
            var.setvalue(0, wrong_obj)

    def test_2314(self):
        "2314 - test object string format"
        obj_type = self.conn.gettype("UDT_OBJECT")
        user = test_env.get_main_user()
        self.assertEqual(
            str(obj_type), f"<oracledb.DbObjectType {user.upper()}.UDT_OBJECT>"
        )
        self.assertEqual(
            str(obj_type.attributes[0]), "<oracledb.DbObjectAttr NUMBERVALUE>"
        )

    def test_2315(self):
        "2315 - test Trim number of elements from collection"
        sub_obj_type = self.conn.gettype("UDT_SUBOBJECT")
        array_type = self.conn.gettype("UDT_OBJECTARRAY")
        data = [(1, "AB"), (2, "CDE"), (3, "FGH"), (4, "IJK"), (5, "LMN")]
        array_obj = array_type()
        for num_val, str_val in data:
            subObj = sub_obj_type()
            subObj.SUBNUMBERVALUE = num_val
            subObj.SUBSTRINGVALUE = str_val
            array_obj.append(subObj)
        self.assertEqual(self.get_db_object_as_plain_object(array_obj), data)
        array_obj.trim(2)
        self.assertEqual(
            self.get_db_object_as_plain_object(array_obj), data[:3]
        )
        array_obj.trim(1)
        self.assertEqual(
            self.get_db_object_as_plain_object(array_obj), data[:2]
        )
        array_obj.trim(0)
        self.assertEqual(
            self.get_db_object_as_plain_object(array_obj), data[:2]
        )
        array_obj.trim(2)
        self.assertEqual(self.get_db_object_as_plain_object(array_obj), [])

    def test_2316(self):
        "2316 - test the metadata of a SQL type"
        user = test_env.get_main_user()
        typ = self.conn.gettype("UDT_OBJECTARRAY")
        self.assertEqual(typ.schema, user.upper())
        self.assertEqual(typ.name, "UDT_OBJECTARRAY")
        self.assertIsNone(typ.package_name)
        self.assertEqual(typ.element_type.schema, user.upper())
        self.assertEqual(typ.element_type.name, "UDT_SUBOBJECT")
        self.assertIsNone(typ.element_type.package_name)
        self.assertEqual(typ.attributes, [])
        self.assertTrue(typ.iscollection)

    def test_2317(self):
        "2317 - test the metadata of a PL/SQL type"
        user = test_env.get_main_user()
        typ = self.conn.gettype("PKG_TESTSTRINGARRAYS.UDT_STRINGLIST")
        self.assertEqual(typ.schema, user.upper())
        self.assertEqual(typ.name, "UDT_STRINGLIST")
        self.assertEqual(typ.package_name, "PKG_TESTSTRINGARRAYS")
        self.assertEqual(typ.element_type, oracledb.DB_TYPE_VARCHAR)
        self.assertEqual(typ.attributes, [])
        self.assertTrue(typ.iscollection)

    def test_2318(self):
        "2318 - test creating an object variable without a type name"
        with self.assertRaisesFullCode("DPY-2037"):
            self.cursor.var(oracledb.DB_TYPE_OBJECT)

    def test_2319(self):
        "2319 - test getting an empty collection as a dictionary"
        type_obj = self.conn.gettype("UDT_ARRAY")
        obj = type_obj.newobject()
        self.assertEqual(obj.asdict(), {})

    def test_2320(self):
        "2320 - test if an element exists in a collection"
        array_type = self.conn.gettype("UDT_ARRAY")
        array_obj = array_type.newobject()
        self.assertFalse(array_obj.exists(0))
        array_obj.append(40)
        self.assertTrue(array_obj.exists(0))
        self.assertFalse(array_obj.exists(1))

    def test_2321(self):
        "2321 - test first and last methods"
        array_type = self.conn.gettype("UDT_ARRAY")
        array_obj = array_type.newobject()
        self.assertIsNone(array_obj.first())
        self.assertIsNone(array_obj.last())
        for i in range(7):
            array_obj.append(i)
        self.assertEqual(array_obj.first(), 0)
        self.assertEqual(array_obj.last(), 6)

    def test_2322(self):
        "2322 - test getting the size of a collections"
        array_type = self.conn.gettype("UDT_ARRAY")
        array_obj = array_type.newobject()
        self.assertEqual(array_obj.size(), 0)
        for i in range(5):
            array_obj.append(i)
        self.assertEqual(array_obj.size(), 5)

    def test_2323(self):
        "2323 - test prev and next methods"
        array_type = self.conn.gettype("UDT_ARRAY")
        array_obj = array_type.newobject()
        self.assertIsNone(array_obj.prev(0))
        self.assertIsNone(array_obj.next(0))
        for i in range(2):
            array_obj.append(i)
        self.assertIsNone(array_obj.prev(0))
        self.assertEqual(array_obj.prev(1), 0)
        self.assertEqual(array_obj.next(0), 1)
        self.assertIsNone(array_obj.next(1))

    def test_2324(self):
        "2324 - test setting and getting elements from a collection"
        array_type = self.conn.gettype("UDT_ARRAY")
        array_obj = array_type.newobject()
        with self.assertRaisesFullCode("DPY-2038"):
            array_obj.getelement(0)
        with self.assertRaisesFullCode("DPY-2039"):
            array_obj.setelement(0, 7)
        array_obj.append(7)
        self.assertEqual(array_obj.getelement(0), 7)
        array_obj.setelement(0, 10)
        self.assertEqual(array_obj.getelement(0), 10)
        with self.assertRaisesFullCode("DPY-2039"):
            array_obj.setelement(3, 4)

    def test_2325(self):
        "2325 - test appending too many elements to a collection"
        array_type = self.conn.gettype("UDT_ARRAY")
        numbers = [i for i in range(11)]
        with self.assertRaisesFullCode("DPY-2039"):
            array_type.newobject(numbers)

        array_obj = array_type.newobject()
        with self.assertRaisesFullCode("DPY-2039"):
            array_obj.extend(numbers)

        array_obj = array_type.newobject()
        for elem in numbers[:10]:
            array_obj.append(elem)
        with self.assertRaisesFullCode("DPY-2039"):
            array_obj.append(numbers[10])

    def test_2326(self):
        "2326 - test appending elements to an unconstrained table"
        data = [1, 3, 6, 10, 15, 21]
        typ = self.conn.gettype("UDT_UNCONSTRAINEDTABLE")
        obj = typ.newobject(data)
        self.cursor.execute("select :1 from dual", [obj])
        (output_obj,) = self.cursor.fetchone()
        self.assertEqual(output_obj.aslist(), data)

    def test_2327(self):
        "2327 - test collection with thousands of entries"
        typ = self.conn.gettype("PKG_TESTNUMBERARRAYS.UDT_NUMBERLIST")
        obj = typ.newobject()
        obj.setelement(1, 1)
        running_total = 1
        for i in range(1, 35000):
            running_total += i + 1
            obj.append(running_total)
        result = self.cursor.callfunc(
            "pkg_TestNumberArrays.TestInArrays", int, (2327, obj)
        )
        self.assertEqual(result, 7146445847327)

    @unittest.skipIf(test_env.get_is_thin(), "thin mode supports xmltype")
    def test_2328(self):
        "2328 - test object with unknown type in one of its attributes"
        typ = self.conn.gettype("UDT_OBJECTWITHXMLTYPE")
        self.assertEqual(typ.attributes[1].type, oracledb.DB_TYPE_UNKNOWN)

    @unittest.skipIf(test_env.get_is_thin(), "thin mode supports xmltype")
    def test_2329(self):
        "2329 - test object with unknown type as the element type"
        typ = self.conn.gettype("UDT_XMLTYPEARRAY")
        self.assertEqual(typ.element_type, oracledb.DB_TYPE_UNKNOWN)

    def test_2330(self):
        "2330 - test DB Object repr()"
        typ = self.conn.gettype("UDT_ARRAY")
        obj = typ.newobject()
        fqn = f"{typ.schema}.{typ.name}"
        expected_str = f"^<oracledb.DbObject {fqn} at 0x.+>$"
        self.assertRegex(repr(obj), expected_str)

        # object of a package
        typ = self.conn.gettype("PKG_TESTSTRINGARRAYS.UDT_STRINGLIST")
        obj = typ.newobject()
        fqn = f"{typ.schema}.{typ.package_name}.{typ.name}"
        expected_str = f"^<oracledb.DbObject {fqn} at 0x.+>$"
        self.assertRegex(repr(obj), expected_str)

    def test_2331(self):
        "2331 - test creating an object with invalid data type"
        type_obj = self.conn.gettype("UDT_ARRAY")
        with self.assertRaisesFullCode("DPY-3013"):
            type_obj.newobject([490, "not a number"])
        with self.assertRaisesFullCode("DPY-3013"):
            type_obj([71, "not a number"])

    def test_2332(self):
        "2332 - test getting an invalid attribute name from an object"
        typ = self.conn.gettype("UDT_OBJECT")
        obj = typ.newobject()
        with self.assertRaises(AttributeError):
            obj.MISSING

    def test_2333(self):
        "2333 - test validating a string attribute"
        typ = self.conn.gettype("UDT_OBJECT")
        obj = typ.newobject()
        for attr_name, max_size in [
            ("STRINGVALUE", 60),
            ("FIXEDCHARVALUE", 10),
            ("NSTRINGVALUE", 120),
            ("NFIXEDCHARVALUE", 20),
            ("RAWVALUE", 16),
        ]:
            with self.subTest(attr_name=attr_name, max_size=max_size):
                value = "A" * max_size
                setattr(obj, attr_name, value)
                value += "X"
                with self.assertRaisesFullCode("DPY-2043"):
                    setattr(obj, attr_name, value)

    def test_2334(self):
        "2334 - test validating a string element value"
        typ = self.conn.gettype("PKG_TESTSTRINGARRAYS.UDT_STRINGLIST")
        obj = typ.newobject()
        obj.append("A" * 100)
        with self.assertRaisesFullCode("DPY-2044"):
            obj.append("A" * 101)
        obj.append("B" * 100)
        with self.assertRaisesFullCode("DPY-2044"):
            obj.setelement(2, "C" * 101)

    def test_2335(self):
        "2335 - test validating a string attribute with null value"
        typ = self.conn.gettype("UDT_OBJECT")
        obj = typ.newobject()
        obj.STRINGVALUE = None

    def test_2336(self):
        "2336 - test initializing (with a sequence) a non collection obj"
        obj_type = self.conn.gettype("UDT_OBJECT")
        with self.assertRaisesFullCode("DPY-2036"):
            obj_type.newobject([1, 2])
        with self.assertRaisesFullCode("DPY-2036"):
            obj_type([3, 4])

    def test_2337(self):
        "2337 - test %ROWTYPE with all types"
        sub_obj_type = self.conn.gettype("UDT_SUBOBJECT")
        sub_arr_type = self.conn.gettype("UDT_OBJECTARRAY")
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
        obj_type = self.conn.gettype("TESTALLTYPES%ROWTYPE")
        actual_metadata = [
            (attr.name, attr.type, attr.precision, attr.scale, attr.max_size)
            for attr in obj_type.attributes
        ]
        self.assertEqual(actual_metadata, expected_metadata)

    def test_2338(self):
        "2338 - test collection iteration"
        self.cursor.execute("select udt_array(5, 10, 15) from dual")
        (obj,) = self.cursor.fetchone()
        result = [i for i in obj]
        self.assertEqual(result, [5, 10, 15])

    @unittest.skipUnless(
        test_env.get_is_thin(), "thick mode does not support xmltype"
    )
    def test_2339(self):
        "2339 - test fetching an object containing an XmlType instance"
        num_val = 2339
        xml_val = "<item>test_2339</item>"
        str_val = "A string for test 2339"
        self.cursor.execute(
            f"""
            select udt_ObjectWithXmlType({num_val}, sys.xmltype('{xml_val}'),
                    '{str_val}') from dual
            """
        )
        (obj,) = self.cursor.fetchone()
        self.assertEqual(obj.NUMBERVALUE, num_val)
        self.assertEqual(obj.XMLVALUE, xml_val)
        self.assertEqual(obj.STRINGVALUE, str_val)

    def test_2340(self):
        "2340 - test DbObject instances are retained across getvalue() calls"
        typ = self.conn.gettype("UDT_OBJECT")
        obj = typ.newobject()
        var = self.cursor.var(typ)
        var.setvalue(0, obj)
        self.assertIs(var.getvalue(), obj)

    def test_2341(self):
        "2341 - test insufficient privileges for gettype()"
        user = test_env.get_proxy_user()
        password = test_env.get_proxy_password()
        main_user = test_env.get_main_user().upper()
        conn = test_env.get_connection(user=user, password=password)
        with self.assertRaisesFullCode("DPY-2035"):
            conn.gettype(f"{main_user}.UDT_OBJECTARRAY")

    def test_2342(self):
        "2342 - test nested records"
        options = [(None, None), (1, None), (None, 2), (1, 2)]
        typ = self.conn.gettype("PKG_TESTNESTEDRECORDS.UDT_OUTER")
        for option in options:
            with self.subTest(option=option):
                value1, value2 = option
                obj = self.cursor.callfunc(
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
