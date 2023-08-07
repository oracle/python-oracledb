#------------------------------------------------------------------------------
# Copyright (c) 2020, 2023, Oracle and/or its affiliates.
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
2300 - Module for testing object variables
"""

import datetime
import decimal
import unittest

import oracledb
import test_env

class TestCase(test_env.BaseTestCase):

    def __test_data(self, expected_int_value, expected_obj_value,
                    expected_array_value):
        int_value, object_value, array_value = self.cursor.fetchone()
        if object_value is not None:
            object_value = self.get_db_object_as_plain_object(object_value)
        if array_value is not None:
            array_value = array_value.aslist()
        self.assertEqual(int_value, expected_int_value)
        self.assertEqual(object_value, expected_obj_value)
        self.assertEqual(array_value, expected_array_value)

    def test_2300_bind_null_in(self):
        "2300 - test binding a null value (IN)"
        var = self.cursor.var(oracledb.DB_TYPE_OBJECT, typename="UDT_OBJECT")
        result = self.cursor.callfunc("pkg_TestBindObject.GetStringRep", str,
                                      (var,))
        self.assertEqual(result, "null")

    def test_2301_bind_object_in(self):
        "2301 - test binding an object (IN)"
        type_obj = self.connection.gettype("UDT_OBJECT")
        obj = type_obj.newobject()
        obj.NUMBERVALUE = 13
        obj.STRINGVALUE = "Test String"
        result = self.cursor.callfunc("pkg_TestBindObject.GetStringRep", str,
                                      (obj,))
        exp = "udt_Object(13, 'Test String', null, null, null, null, null)"
        self.assertEqual(result, exp)
        obj.NUMBERVALUE = None
        obj.STRINGVALUE = "Test With Dates"
        obj.DATEVALUE = datetime.datetime(2016, 2, 10)
        obj.TIMESTAMPVALUE = datetime.datetime(2016, 2, 10, 14, 13, 50)
        result = self.cursor.callfunc("pkg_TestBindObject.GetStringRep", str,
                                      (obj,))
        self.assertEqual(result,
                         "udt_Object(null, 'Test With Dates', null, " \
                         "to_date('2016-02-10', 'YYYY-MM-DD'), " \
                         "to_timestamp('2016-02-10 14:13:50', " \
                                 "'YYYY-MM-DD HH24:MI:SS'), " \
                         "null, null)")
        obj.DATEVALUE = None
        obj.TIMESTAMPVALUE = None
        sub_type_obj = self.connection.gettype("UDT_SUBOBJECT")
        sub_obj = sub_type_obj.newobject()
        sub_obj.SUBNUMBERVALUE = decimal.Decimal("18.25")
        sub_obj.SUBSTRINGVALUE = "Sub String"
        obj.SUBOBJECTVALUE = sub_obj
        result = self.cursor.callfunc("pkg_TestBindObject.GetStringRep", str,
                                      (obj,))
        self.assertEqual(result,
                         "udt_Object(null, 'Test With Dates', null, null, " \
                         "null, udt_SubObject(18.25, 'Sub String'), null)")

    def test_2302_copy_object(self):
        "2302 - test copying an object"
        type_obj = self.connection.gettype("UDT_OBJECT")
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

    def test_2303_empty_collection_as_list(self):
        "2303 - test getting an empty collection as a list"
        type_obj = self.connection.gettype("UDT_ARRAY")
        obj = type_obj.newobject()
        self.assertEqual(obj.aslist(), [])

    def test_2304_fetch_data(self):
        "2304 - test fetching objects"
        self.cursor.execute("""
                select IntCol, ObjectCol, ArrayCol
                from TestObjects
                order by IntCol""")
        expected_value = [
            ('INTCOL', oracledb.DB_TYPE_NUMBER, 10, None, 9, 0, False),
            ('OBJECTCOL', oracledb.DB_TYPE_OBJECT, None, None, None, None,
                    True),
            ('ARRAYCOL', oracledb.DB_TYPE_OBJECT, None, None, None, None, True)
        ]
        self.assertEqual(self.cursor.description, expected_value)
        expected_value = (
            1,
            'First row',
            'First     ',
            'N First Row',
            'N First   ',
            b'Raw Data 1',
            2,
            5,
            12.125,
            0.5,
            12.5,
            25.25,
            50.125,
            oracledb.Timestamp(2007, 3, 6, 0, 0, 0),
            oracledb.Timestamp(2008, 9, 12, 16, 40),
            oracledb.Timestamp(2009, 10, 13, 17, 50),
            oracledb.Timestamp(2010, 11, 14, 18, 55),
            'Short CLOB value',
            'Short NCLOB Value',
            b'Short BLOB value',
            (11, 'Sub object 1'),
            [(5, 'first element'), (6, 'second element')]
        )
        self.__test_data(1, expected_value, [5, 10, None, 20])
        self.__test_data(2, None, [3, None, 9, 12, 15])
        expected_value = (
            3,
            'Third row',
            'Third     ',
            'N Third Row',
            'N Third   ',
            b'Raw Data 3',
            4,
            10,
            6.5,
            0.75,
            43.25,
            86.5,
            192.125,
            oracledb.Timestamp(2007, 6, 21, 0, 0, 0),
            oracledb.Timestamp(2007, 12, 13, 7, 30, 45),
            oracledb.Timestamp(2017, 6, 21, 23, 18, 45),
            oracledb.Timestamp(2017, 7, 21, 8, 27, 13),
            'Another short CLOB value',
            'Another short NCLOB Value',
            b'Yet another short BLOB value',
            (13, 'Sub object 3'),
            [
                (10, 'element #1'),
                (20, 'element #2'),
                (30, 'element #3'),
                (40, 'element #4')
            ]
        )
        self.__test_data(3, expected_value, None)

    def test_2305_get_object_type(self):
        "2305 - test getting object type"
        type_obj = self.connection.gettype("UDT_OBJECT")
        self.assertEqual(type_obj.iscollection, False)
        self.assertEqual(type_obj.schema, self.connection.username.upper())
        self.assertEqual(type_obj.name, "UDT_OBJECT")
        sub_object_value_type = self.connection.gettype("UDT_SUBOBJECT")
        sub_object_array_type = self.connection.gettype("UDT_OBJECTARRAY")
        expected_attr_names = [
            "NUMBERVALUE",
            "STRINGVALUE",
            "FIXEDCHARVALUE",
            "NSTRINGVALUE",
            "NFIXEDCHARVALUE",
            "RAWVALUE",
            "INTVALUE",
            "SMALLINTVALUE",
            "REALVALUE",
            "DOUBLEPRECISIONVALUE",
            "FLOATVALUE",
            "BINARYFLOATVALUE",
            "BINARYDOUBLEVALUE",
            "DATEVALUE",
            "TIMESTAMPVALUE",
            "TIMESTAMPTZVALUE",
            "TIMESTAMPLTZVALUE",
            "CLOBVALUE",
            "NCLOBVALUE",
            "BLOBVALUE",
            "SUBOBJECTVALUE",
            "SUBOBJECTARRAY"
        ]
        actual_attr_names = [a.name for a in type_obj.attributes]
        self.assertEqual(actual_attr_names, expected_attr_names)
        expected_attr_types = [
            oracledb.DB_TYPE_NUMBER,
            oracledb.DB_TYPE_VARCHAR,
            oracledb.DB_TYPE_CHAR,
            oracledb.DB_TYPE_NVARCHAR,
            oracledb.DB_TYPE_NCHAR,
            oracledb.DB_TYPE_RAW,
            oracledb.DB_TYPE_NUMBER,
            oracledb.DB_TYPE_NUMBER,
            oracledb.DB_TYPE_NUMBER,
            oracledb.DB_TYPE_NUMBER,
            oracledb.DB_TYPE_NUMBER,
            oracledb.DB_TYPE_BINARY_FLOAT,
            oracledb.DB_TYPE_BINARY_DOUBLE,
            oracledb.DB_TYPE_DATE,
            oracledb.DB_TYPE_TIMESTAMP,
            oracledb.DB_TYPE_TIMESTAMP_TZ,
            oracledb.DB_TYPE_TIMESTAMP_LTZ,
            oracledb.DB_TYPE_CLOB,
            oracledb.DB_TYPE_NCLOB,
            oracledb.DB_TYPE_BLOB,
            sub_object_value_type,
            sub_object_array_type
        ]
        actual_attr_types = [a.type for a in type_obj.attributes]
        self.assertEqual(actual_attr_types, expected_attr_types)
        self.assertEqual(sub_object_array_type.iscollection, True)
        self.assertEqual(sub_object_array_type.attributes, [])

    def test_2306_object_type(self):
        "2306 - test object type data"
        self.cursor.execute("""
                select ObjectCol
                from TestObjects
                where ObjectCol is not null
                  and rownum <= 1""")
        obj, = self.cursor.fetchone()
        self.assertEqual(obj.type.schema, self.connection.username.upper())
        self.assertEqual(obj.type.name, "UDT_OBJECT")
        self.assertEqual(obj.type.attributes[0].name, "NUMBERVALUE")

    def test_2307_round_trip_object(self):
        "2307 - test inserting and then querying object with all data types"
        self.cursor.execute("truncate table TestClobs")
        self.cursor.execute("truncate table TestNClobs")
        self.cursor.execute("truncate table TestBlobs")
        self.cursor.execute("""
                insert into TestClobs
                (IntCol, ClobCol)
                values (1, 'A short CLOB')""")
        self.cursor.execute("""
                insert into TestNClobs
                (IntCol, NClobCol)
                values (1, 'A short NCLOB')""")
        self.cursor.execute("""
                insert into TestBlobs
                (IntCol, BlobCol)
                values (1, utl_raw.cast_to_raw('A short BLOB'))""")
        self.connection.commit()
        self.cursor.execute("select CLOBCol from TestClobs")
        clob, = self.cursor.fetchone()
        self.cursor.execute("select NCLOBCol from TestNClobs")
        nclob, = self.cursor.fetchone()
        self.cursor.execute("select BLOBCol from TestBlobs")
        blob, = self.cursor.fetchone()
        type_obj = self.connection.gettype("UDT_OBJECT")
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
        sub_type_obj = self.connection.gettype("UDT_SUBOBJECT")
        sub_obj = sub_type_obj.newobject()
        sub_obj.SUBNUMBERVALUE = 23
        sub_obj.SUBSTRINGVALUE = "Substring value"
        obj.SUBOBJECTVALUE = sub_obj
        self.cursor.execute("insert into TestObjects (IntCol, ObjectCol) " \
                            "values (4, :obj)", obj=obj)
        self.cursor.execute("""
                select IntCol, ObjectCol, ArrayCol
                from TestObjects
                where IntCol = 4""")
        expected_value = (
            5,
            'A string',
            'Fixed str ',
            'A NCHAR string',
            'Fixed N   ',
            b'Raw Value',
            27,
            13,
            184.875,
            1.375,
            23.75,
            14.25,
            29.1625,
            oracledb.Timestamp(2017, 5, 9, 0, 0, 0),
            oracledb.Timestamp(2017, 5, 9, 9, 41, 13),
            oracledb.Timestamp(1986, 8, 2, 15, 27, 38),
            oracledb.Timestamp(1999, 11, 12, 23, 5, 2),
            'A short CLOB',
            'A short NCLOB',
            b'A short BLOB',
            (23, 'Substring value'),
            None
        )
        self.__test_data(4, expected_value, None)
        obj.CLOBVALUE = "A short CLOB (modified)"
        obj.NCLOBVALUE = "A short NCLOB (modified)"
        obj.BLOBVALUE = "A short BLOB (modified)"
        self.cursor.execute("insert into TestObjects (IntCol, ObjectCol) " \
                            "values (5, :obj)", obj = obj)
        self.cursor.execute("""
                select IntCol, ObjectCol, ArrayCol
                from TestObjects
                where IntCol = 5""")
        expected_value = (
            5,
            'A string',
            'Fixed str ',
            'A NCHAR string',
            'Fixed N   ',
            b'Raw Value',
            27,
            13,
            184.875,
            1.375,
            23.75,
            14.25,
            29.1625,
            oracledb.Timestamp(2017, 5, 9, 0, 0, 0),
            oracledb.Timestamp(2017, 5, 9, 9, 41, 13),
            oracledb.Timestamp(1986, 8, 2, 15, 27, 38),
            oracledb.Timestamp(1999, 11, 12, 23, 5, 2),
            'A short CLOB (modified)',
            'A short NCLOB (modified)',
            b'A short BLOB (modified)',
            (23, 'Substring value'),
            None
        )
        self.__test_data(5, expected_value, None)
        self.connection.rollback()

    def test_2308_invalid_type_object(self):
        "2308 - test trying to find an object type that does not exist"
        self.assertRaises(TypeError, self.connection.gettype, 2)
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-2035:",
                               self.connection.gettype,
                               "A TYPE THAT DOES NOT EXIST")

    def test_2309_appending_wrong_object_type(self):
        "2309 - test appending an object of the wrong type to a collection"
        collection_obj_type = self.connection.gettype("UDT_OBJECTARRAY")
        collection_obj = collection_obj_type.newobject()
        array_obj_type = self.connection.gettype("UDT_ARRAY")
        array_obj = array_obj_type.newobject()
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-2008:",
                               collection_obj.append, array_obj)

    def test_2310_referencing_sub_obj(self):
        "2310 - test that referencing a sub object affects the parent object"
        obj_type = self.connection.gettype("UDT_OBJECT")
        sub_obj_type = self.connection.gettype("UDT_SUBOBJECT")
        obj = obj_type.newobject()
        obj.SUBOBJECTVALUE = sub_obj_type.newobject()
        obj.SUBOBJECTVALUE.SUBNUMBERVALUE = 5
        obj.SUBOBJECTVALUE.SUBSTRINGVALUE = "Substring"
        self.assertEqual(obj.SUBOBJECTVALUE.SUBNUMBERVALUE, 5)
        self.assertEqual(obj.SUBOBJECTVALUE.SUBSTRINGVALUE, "Substring")

    def test_2311_access_sub_object_parent_object_destroyed(self):
        "2311 - test accessing sub object after parent object destroyed"
        obj_type = self.connection.gettype("UDT_OBJECT")
        sub_obj_type = self.connection.gettype("UDT_SUBOBJECT")
        array_type = self.connection.gettype("UDT_OBJECTARRAY")
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
        self.assertEqual(self.get_db_object_as_plain_object(sub_obj_array),
                         [(2, "AB"), (3, "CDE")])

    def test_2312_setting_attr_wrong_object_type(self):
        "2312 - test assigning an object of wrong type to an object attribute"
        obj_type = self.connection.gettype("UDT_OBJECT")
        obj = obj_type.newobject()
        wrong_obj_type = self.connection.gettype("UDT_OBJECTARRAY")
        wrong_obj = wrong_obj_type.newobject()
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-2008:", setattr,
                               obj, "SUBOBJECTVALUE", wrong_obj)

    def test_2313_setting_var_wrong_object_type(self):
        "2313 - test setting value of object variable to wrong object type"
        wrong_obj_type = self.connection.gettype("UDT_OBJECTARRAY")
        wrong_obj = wrong_obj_type.newobject()
        var = self.cursor.var(oracledb.DB_TYPE_OBJECT, typename="UDT_OBJECT")
        self.assertRaisesRegex(oracledb.ProgrammingError, "^DPY-2008:",
                               var.setvalue, 0, wrong_obj)

    def test_2314_string_format(self):
        "2314 - test object string format"
        obj_type = self.connection.gettype("UDT_OBJECT")
        user = test_env.get_main_user()
        self.assertEqual(str(obj_type),
                "<oracledb.DbObjectType %s.UDT_OBJECT>" % user.upper())
        self.assertEqual(str(obj_type.attributes[0]),
                         "<oracledb.DbObjectAttr NUMBERVALUE>")

    def test_2315_trim_collection_list(self):
        "2315 - test Trim number of elements from collection"
        sub_obj_type = self.connection.gettype("UDT_SUBOBJECT")
        array_type = self.connection.gettype("UDT_OBJECTARRAY")
        data = [(1, "AB"), (2, "CDE"), (3, "FGH"), (4, "IJK"), (5, "LMN")]
        array_obj = array_type()
        for num_val, str_val in data:
            subObj = sub_obj_type()
            subObj.SUBNUMBERVALUE = num_val
            subObj.SUBSTRINGVALUE = str_val
            array_obj.append(subObj)
        self.assertEqual(self.get_db_object_as_plain_object(array_obj), data)
        array_obj.trim(2)
        self.assertEqual(self.get_db_object_as_plain_object(array_obj),
                         data[:3])
        array_obj.trim(1)
        self.assertEqual(self.get_db_object_as_plain_object(array_obj),
                         data[:2])
        array_obj.trim(0)
        self.assertEqual(self.get_db_object_as_plain_object(array_obj),
                         data[:2])
        array_obj.trim(2)
        self.assertEqual(self.get_db_object_as_plain_object(array_obj), [])

    def test_2316_sql_type_metadata(self):
        "2316 - test the metadata of a SQL type"
        user = test_env.get_main_user()
        typ = self.connection.gettype("UDT_OBJECTARRAY")
        self.assertEqual(typ.schema, user.upper())
        self.assertEqual(typ.name, "UDT_OBJECTARRAY")
        self.assertEqual(typ.package_name, None)
        self.assertEqual(typ.element_type.schema, user.upper())
        self.assertEqual(typ.element_type.name, "UDT_SUBOBJECT")
        self.assertEqual(typ.element_type.package_name, None)

    def test_2317_plsql_type_metadata(self):
        "2317 - test the metadata of a PL/SQL type"
        user = test_env.get_main_user()
        typ = self.connection.gettype("PKG_TESTSTRINGARRAYS.UDT_STRINGLIST")
        self.assertEqual(typ.schema, user.upper())
        self.assertEqual(typ.name, "UDT_STRINGLIST")
        self.assertEqual(typ.package_name, "PKG_TESTSTRINGARRAYS")
        self.assertEqual(typ.element_type, oracledb.DB_TYPE_VARCHAR)

    def test_2318_negative_create_object_var_no_type_name(self):
        "2318 - test creating an object variable without a type name"
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-2037:",
                               self.cursor.var, oracledb.DB_TYPE_OBJECT)

    def test_2319_collection_as_dictionary(self):
        "2319 - test getting an empty collection as a dictionary"
        type_obj = self.connection.gettype("UDT_ARRAY")
        obj = type_obj.newobject()
        self.assertEqual(obj.asdict(), {})

    def test_2320_exists_in_collection(self):
        "2320 - test if an element exists in a collection"
        array_type = self.connection.gettype("UDT_ARRAY")
        array_obj = array_type.newobject()
        self.assertEqual(array_obj.exists(0), False)
        array_obj.append(40)
        self.assertEqual(array_obj.exists(0), True)
        self.assertEqual(array_obj.exists(1), False)

    def test_2321_first_and_last_indexes(self):
        "2321 - test first and last methods"
        array_type = self.connection.gettype("UDT_ARRAY")
        array_obj = array_type.newobject()
        self.assertEqual(array_obj.first(), None)
        self.assertEqual(array_obj.last(), None)
        for i in range(7):
            array_obj.append(i)
        self.assertEqual(array_obj.first(), 0)
        self.assertEqual(array_obj.last(), 6)

    def test_2322_size(self):
        "2322 - test getting the size of a collections"
        array_type = self.connection.gettype("UDT_ARRAY")
        array_obj = array_type.newobject()
        self.assertEqual(array_obj.size(), 0)
        for i in range(5):
            array_obj.append(i)
        self.assertEqual(array_obj.size(), 5)

    def test_2323_prev_next(self):
        "2323 - test prev and next methods"
        array_type = self.connection.gettype("UDT_ARRAY")
        array_obj = array_type.newobject()
        self.assertEqual(array_obj.prev(0), None)
        self.assertEqual(array_obj.next(0), None)
        for i in range(2):
            array_obj.append(i)
        self.assertEqual(array_obj.prev(0), None)
        self.assertEqual(array_obj.prev(1), 0)
        self.assertEqual(array_obj.next(0), 1)
        self.assertEqual(array_obj.next(1), None)

    def test_2324_set_get_element(self):
        "2324 - test setting and getting elements from a collection"
        array_type = self.connection.gettype("UDT_ARRAY")
        array_obj = array_type.newobject()
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-2038:",
                               array_obj.getelement, 0)
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-2039:",
                               array_obj.setelement, 0, 7)
        array_obj.append(7)
        self.assertEqual(array_obj.getelement(0), 7)
        array_obj.setelement(0, 10)
        self.assertEqual(array_obj.getelement(0), 10)
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-2039:",
                               array_obj.setelement, 3, 4)

    def test_2325_add_too_many_elements_to_collection(self):
        "2325 - test appending too many elements to a collection"
        array_type = self.connection.gettype("UDT_ARRAY")
        numbers = [i for i in range(11)]
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-2039:",
                               array_type.newobject, numbers)

        array_obj = array_type.newobject()
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-2039:",
                               array_obj.extend, numbers)

        array_obj = array_type.newobject()
        for elem in numbers[:10]:
            array_obj.append(elem)
        self.assertRaisesRegex(oracledb.DatabaseError, "^DPY-2039:",
                               array_obj.append, numbers[10])

    def test_2326_test_unconstrained_table(self):
        "2326 - test appending elements to an unconstrained table"
        data = [1, 3, 6, 10, 15, 21]
        typ = self.connection.gettype("UDT_UNCONSTRAINEDTABLE")
        obj = typ.newobject(data)
        self.cursor.execute("select :1 from dual", [obj])
        output_obj, = self.cursor.fetchone()
        self.assertEqual(output_obj.aslist(), data)

    def test_2327_large_collection(self):
        "2327 - test collection with thousands of entries"
        typ = self.connection.gettype("PKG_TESTNUMBERARRAYS.UDT_NUMBERLIST")
        obj = typ.newobject()
        obj.setelement(1, 1)
        running_total = 1
        for i in range(1, 35000):
            running_total += (i + 1)
            obj.append(running_total)
        result = self.cursor.callfunc("pkg_TestNumberArrays.TestInArrays", int,
                                      (2327, obj))
        self.assertEqual(result, 7146445847327)

    @unittest.skipIf(test_env.get_is_thin(),
                     "thin mode doesn't have any unknown types currently")
    def test_2328_unknown_type_attribute(self):
        "2328 - test object with unknown type in one of its attributes"
        typ = self.connection.gettype("UDT_UNKNOWNATTRIBUTETYPE")
        self.assertEqual(typ.attributes[1].type, oracledb.DB_TYPE_UNKNOWN)

    @unittest.skipIf(test_env.get_is_thin(),
                     "thin mode doesn't have any unknown types currently")
    def test_2329_unknown_type_element(self):
        "2329 - test object with unknown type as the element type"
        typ = self.connection.gettype("UDT_UNKNOWNELEMENTTYPE")
        self.assertEqual(typ.element_type, oracledb.DB_TYPE_UNKNOWN)

    def test_2330_repr(self):
        "2330 - test DB Object repr()"
        typ = self.connection.gettype("UDT_ARRAY")
        obj = typ.newobject()
        fqn = f"{typ.schema}.{typ.name}"
        expected_str = f"^<oracledb.DbObject {fqn} at 0x.+>$"
        self.assertRegex(repr(obj), expected_str)

    def test_2331_new_object_negative(self):
        "2331 - test creating an object with invalid data type"
        type_obj = self.connection.gettype("UDT_ARRAY")
        self.assertRaisesRegex(oracledb.NotSupportedError, "^DPY-3013:",
                               type_obj.newobject, [490, "not a number"])
        self.assertRaisesRegex(oracledb.NotSupportedError, "^DPY-3013:",
                               type_obj, [71, "not a number"])

if __name__ == "__main__":
    test_env.run_test_cases()
