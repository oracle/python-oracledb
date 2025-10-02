# -----------------------------------------------------------------------------
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
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
import re

import oracledb
import pytest


def _test_data(
    cursor,
    test_env,
    expected_int_value,
    expected_obj_value,
    expected_array_value,
):
    int_value, object_value, array_value = cursor.fetchone()
    if object_value is not None:
        assert isinstance(object_value.INTVALUE, int)
        assert isinstance(object_value.SMALLINTVALUE, int)
        assert isinstance(object_value.FLOATVALUE, float)
    if object_value is not None:
        object_value = test_env.get_db_object_as_plain_object(object_value)
    if array_value is not None:
        array_value = array_value.aslist()
    assert int_value == expected_int_value
    assert object_value == expected_obj_value
    assert array_value == expected_array_value


def test_2300(cursor):
    "2300 - test binding a null value (IN)"
    var = cursor.var(oracledb.DB_TYPE_OBJECT, typename="UDT_OBJECT")
    result = cursor.callfunc("pkg_TestBindObject.GetStringRep", str, [var])
    assert result == "null"


def test_2301(conn, cursor):
    "2301 - test binding an object (IN)"
    type_obj = conn.gettype("UDT_OBJECT")
    obj = type_obj.newobject()
    obj.NUMBERVALUE = 13
    obj.STRINGVALUE = "Test String"
    result = cursor.callfunc("pkg_TestBindObject.GetStringRep", str, [obj])
    exp = "udt_Object(13, 'Test String', null, null, null, null, null)"
    assert result == exp
    obj.NUMBERVALUE = None
    obj.STRINGVALUE = "Test With Dates"
    obj.DATEVALUE = datetime.datetime(2016, 2, 10)
    obj.TIMESTAMPVALUE = datetime.datetime(2016, 2, 10, 14, 13, 50)
    result = cursor.callfunc("pkg_TestBindObject.GetStringRep", str, [obj])
    expected_value = (
        "udt_Object(null, 'Test With Dates', null, "
        "to_date('2016-02-10', 'YYYY-MM-DD'), "
        "to_timestamp('2016-02-10 14:13:50', "
        "'YYYY-MM-DD HH24:MI:SS'), "
        "null, null)"
    )
    assert result == expected_value
    obj.DATEVALUE = None
    obj.TIMESTAMPVALUE = None
    sub_type_obj = conn.gettype("UDT_SUBOBJECT")
    sub_obj = sub_type_obj.newobject()
    sub_obj.SUBNUMBERVALUE = decimal.Decimal("18.25")
    sub_obj.SUBSTRINGVALUE = "Sub String"
    obj.SUBOBJECTVALUE = sub_obj
    result = cursor.callfunc("pkg_TestBindObject.GetStringRep", str, [obj])
    expected_value = (
        "udt_Object(null, 'Test With Dates', null, null, "
        "null, udt_SubObject(18.25, 'Sub String'), null)"
    )
    assert result == expected_value


def test_2302(conn):
    "2302 - test copying an object"
    type_obj = conn.gettype("UDT_OBJECT")
    obj = type_obj()
    obj.NUMBERVALUE = 5124
    obj.STRINGVALUE = "A test string"
    obj.DATEVALUE = datetime.datetime(2016, 2, 24)
    obj.TIMESTAMPVALUE = datetime.datetime(2016, 2, 24, 13, 39, 10)
    copied_obj = obj.copy()
    assert obj.NUMBERVALUE == copied_obj.NUMBERVALUE
    assert obj.STRINGVALUE == copied_obj.STRINGVALUE
    assert obj.DATEVALUE == copied_obj.DATEVALUE
    assert obj.TIMESTAMPVALUE == copied_obj.TIMESTAMPVALUE


def test_2303(conn):
    "2303 - test getting an empty collection as a list"
    type_obj = conn.gettype("UDT_ARRAY")
    obj = type_obj.newobject()
    assert obj.aslist() == []


def test_2304(cursor, test_env):
    "2304 - test fetching objects"
    cursor.execute(
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
    assert cursor.description == expected_value
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
    _test_data(cursor, test_env, 1, expected_value, [5, 10, None, 20])
    _test_data(cursor, test_env, 2, None, [3, None, 9, 12, 15])
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
    _test_data(cursor, test_env, 3, expected_value, None)


def test_2305(conn):
    "2305 - test getting object type"
    type_obj = conn.gettype("UDT_OBJECT")
    assert not type_obj.iscollection
    assert type_obj.schema == conn.username.upper()
    assert type_obj.name == "UDT_OBJECT"
    sub_object_value_type = conn.gettype("UDT_SUBOBJECT")
    sub_object_array_type = conn.gettype("UDT_OBJECTARRAY")
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
    assert actual_metadata == expected_metadata
    assert sub_object_array_type.iscollection
    assert sub_object_array_type.attributes == []


def test_2306(conn, cursor):
    "2306 - test object type data"
    cursor.execute(
        """
        select ObjectCol
        from TestObjects
        where ObjectCol is not null
          and rownum <= 1
        """
    )
    (obj,) = cursor.fetchone()
    assert obj.type.schema == conn.username.upper()
    assert obj.type.name == "UDT_OBJECT"
    assert obj.type.attributes[0].name == "NUMBERVALUE"


def test_2307(conn, cursor, test_env):
    "2307 - test inserting and then querying object with all data types"
    cursor.execute("delete from TestClobs")
    cursor.execute("delete from TestNClobs")
    cursor.execute("delete from TestBlobs")
    cursor.execute("delete from TestObjects where IntCol > 3")
    cursor.execute(
        """
        insert into TestClobs (IntCol, ClobCol)
        values (1, 'A short CLOB')
        """
    )
    cursor.execute(
        """
        insert into TestNClobs (IntCol, NClobCol)
        values (1, 'A short NCLOB')
        """
    )
    cursor.execute(
        """
        insert into TestBlobs (IntCol, BlobCol)
        values (1, utl_raw.cast_to_raw('A short BLOB'))
        """
    )
    conn.commit()
    cursor.execute("select CLOBCol from TestClobs")
    (clob,) = cursor.fetchone()
    cursor.execute("select NCLOBCol from TestNClobs")
    (nclob,) = cursor.fetchone()
    cursor.execute("select BLOBCol from TestBlobs")
    (blob,) = cursor.fetchone()
    type_obj = conn.gettype("UDT_OBJECT")
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
    sub_type_obj = conn.gettype("UDT_SUBOBJECT")
    sub_obj = sub_type_obj.newobject()
    sub_obj.SUBNUMBERVALUE = 23
    sub_obj.SUBSTRINGVALUE = "Substring value"
    obj.SUBOBJECTVALUE = sub_obj
    cursor.execute(
        """
        insert into TestObjects (IntCol, ObjectCol)
        values (4, :obj)
        """,
        obj=obj,
    )
    cursor.execute(
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
    _test_data(cursor, test_env, 4, expected_value, None)
    obj.CLOBVALUE = "A short CLOB (modified)"
    obj.NCLOBVALUE = "A short NCLOB (modified)"
    obj.BLOBVALUE = "A short BLOB (modified)"
    cursor.execute(
        """
        insert into TestObjects (IntCol, ObjectCol)
        values (5, :obj)
        """,
        obj=obj,
    )
    cursor.execute(
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
    _test_data(cursor, test_env, 5, expected_value, None)
    conn.rollback()


def test_2308(conn, test_env):
    "2308 - test trying to find an object type that does not exist"
    pytest.raises(TypeError, conn.gettype, 2)
    with test_env.assert_raises_full_code("DPY-2035"):
        conn.gettype("A TYPE THAT DOES NOT EXIST")


def test_2309(conn, test_env):
    "2309 - test appending an object of the wrong type to a collection"
    collection_obj_type = conn.gettype("UDT_OBJECTARRAY")
    collection_obj = collection_obj_type.newobject()
    array_obj_type = conn.gettype("UDT_ARRAY")
    array_obj = array_obj_type.newobject()
    with test_env.assert_raises_full_code("DPY-2008"):
        collection_obj.append(array_obj)


def test_2310(conn):
    "2310 - test that referencing a sub object affects the parent object"
    obj_type = conn.gettype("UDT_OBJECT")
    sub_obj_type = conn.gettype("UDT_SUBOBJECT")
    obj = obj_type.newobject()
    obj.SUBOBJECTVALUE = sub_obj_type.newobject()
    obj.SUBOBJECTVALUE.SUBNUMBERVALUE = 5
    obj.SUBOBJECTVALUE.SUBSTRINGVALUE = "Substring"
    assert obj.SUBOBJECTVALUE.SUBNUMBERVALUE == 5
    assert obj.SUBOBJECTVALUE.SUBSTRINGVALUE == "Substring"


def test_2311(conn, test_env):
    "2311 - test accessing sub object after parent object destroyed"
    obj_type = conn.gettype("UDT_OBJECT")
    sub_obj_type = conn.gettype("UDT_SUBOBJECT")
    array_type = conn.gettype("UDT_OBJECTARRAY")
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
    expected = [(2, "AB"), (3, "CDE")]
    assert test_env.get_db_object_as_plain_object(sub_obj_array) == expected


def test_2312(conn, test_env):
    "2312 - test assigning an object of wrong type to an object attribute"
    obj_type = conn.gettype("UDT_OBJECT")
    obj = obj_type.newobject()
    wrong_obj_type = conn.gettype("UDT_OBJECTARRAY")
    wrong_obj = wrong_obj_type.newobject()
    with test_env.assert_raises_full_code("DPY-2008"):
        setattr(obj, "SUBOBJECTVALUE", wrong_obj)


def test_2313(conn, cursor, test_env):
    "2313 - test setting value of object variable to wrong object type"
    wrong_obj_type = conn.gettype("UDT_OBJECTARRAY")
    wrong_obj = wrong_obj_type.newobject()
    var = cursor.var(oracledb.DB_TYPE_OBJECT, typename="UDT_OBJECT")
    with test_env.assert_raises_full_code("DPY-2008"):
        var.setvalue(0, wrong_obj)


def test_2314(conn, test_env):
    "2314 - test object string format"
    obj_type = conn.gettype("UDT_OBJECT")
    user = test_env.main_user.upper()
    assert str(obj_type) == f"<oracledb.DbObjectType {user}.UDT_OBJECT>"
    assert str(obj_type.attributes[0]) == "<oracledb.DbObjectAttr NUMBERVALUE>"


def test_2315(conn, test_env):
    "2315 - test Trim number of elements from collection"
    sub_obj_type = conn.gettype("UDT_SUBOBJECT")
    array_type = conn.gettype("UDT_OBJECTARRAY")
    data = [(1, "AB"), (2, "CDE"), (3, "FGH"), (4, "IJK"), (5, "LMN")]
    array_obj = array_type()
    for num_val, str_val in data:
        subObj = sub_obj_type()
        subObj.SUBNUMBERVALUE = num_val
        subObj.SUBSTRINGVALUE = str_val
        array_obj.append(subObj)
    assert test_env.get_db_object_as_plain_object(array_obj) == data
    array_obj.trim(2)
    assert test_env.get_db_object_as_plain_object(array_obj) == data[:3]
    array_obj.trim(1)
    assert test_env.get_db_object_as_plain_object(array_obj) == data[:2]
    array_obj.trim(0)
    assert test_env.get_db_object_as_plain_object(array_obj) == data[:2]
    array_obj.trim(2)
    assert test_env.get_db_object_as_plain_object(array_obj) == []


def test_2316(conn, test_env):
    "2316 - test the metadata of a SQL type"
    user = test_env.main_user
    typ = conn.gettype("UDT_OBJECTARRAY")
    assert typ.schema == user.upper()
    assert typ.name == "UDT_OBJECTARRAY"
    assert typ.package_name is None
    assert typ.element_type.schema == user.upper()
    assert typ.element_type.name == "UDT_SUBOBJECT"
    assert typ.element_type.package_name is None
    assert typ.attributes == []
    assert typ.iscollection


def test_2317(conn, test_env):
    "2317 - test the metadata of a PL/SQL type"
    user = test_env.main_user
    typ = conn.gettype("PKG_TESTSTRINGARRAYS.UDT_STRINGLIST")
    assert typ.schema == user.upper()
    assert typ.name == "UDT_STRINGLIST"
    assert typ.package_name == "PKG_TESTSTRINGARRAYS"
    assert typ.element_type == oracledb.DB_TYPE_VARCHAR
    assert typ.attributes == []
    assert typ.iscollection


def test_2318(cursor, test_env):
    "2318 - test creating an object variable without a type name"
    with test_env.assert_raises_full_code("DPY-2037"):
        cursor.var(oracledb.DB_TYPE_OBJECT)


def test_2319(conn):
    "2319 - test getting an empty collection as a dictionary"
    type_obj = conn.gettype("UDT_ARRAY")
    obj = type_obj.newobject()
    assert obj.asdict() == {}


def test_2320(conn):
    "2320 - test if an element exists in a collection"
    array_type = conn.gettype("UDT_ARRAY")
    array_obj = array_type.newobject()
    assert not array_obj.exists(0)
    array_obj.append(40)
    assert array_obj.exists(0)
    assert not array_obj.exists(1)


def test_2321(conn):
    "2321 - test first and last methods"
    array_type = conn.gettype("UDT_ARRAY")
    array_obj = array_type.newobject()
    assert array_obj.first() is None
    assert array_obj.last() is None
    for i in range(7):
        array_obj.append(i)
    assert array_obj.first() == 0
    assert array_obj.last() == 6


def test_2322(conn):
    "2322 - test getting the size of a collections"
    array_type = conn.gettype("UDT_ARRAY")
    array_obj = array_type.newobject()
    assert array_obj.size() == 0
    for i in range(5):
        array_obj.append(i)
    assert array_obj.size() == 5


def test_2323(conn):
    "2323 - test prev and next methods"
    array_type = conn.gettype("UDT_ARRAY")
    array_obj = array_type.newobject()
    assert array_obj.prev(0) is None
    assert array_obj.next(0) is None
    for i in range(2):
        array_obj.append(i)
    assert array_obj.prev(0) is None
    assert array_obj.prev(1) == 0
    assert array_obj.next(0) == 1
    assert array_obj.next(1) is None


def test_2324(conn, test_env):
    "2324 - test setting and getting elements from a collection"
    array_type = conn.gettype("UDT_ARRAY")
    array_obj = array_type.newobject()
    with test_env.assert_raises_full_code("DPY-2038"):
        array_obj.getelement(0)
    with test_env.assert_raises_full_code("DPY-2039"):
        array_obj.setelement(0, 7)
    array_obj.append(7)
    assert array_obj.getelement(0) == 7
    array_obj.setelement(0, 10)
    assert array_obj.getelement(0) == 10
    with test_env.assert_raises_full_code("DPY-2039"):
        array_obj.setelement(3, 4)


def test_2325(conn, test_env):
    "2325 - test appending too many elements to a collection"
    array_type = conn.gettype("UDT_ARRAY")
    numbers = [i for i in range(11)]
    with test_env.assert_raises_full_code("DPY-2039"):
        array_type.newobject(numbers)

    array_obj = array_type.newobject()
    with test_env.assert_raises_full_code("DPY-2039"):
        array_obj.extend(numbers)

    array_obj = array_type.newobject()
    for elem in numbers[:10]:
        array_obj.append(elem)
    with test_env.assert_raises_full_code("DPY-2039"):
        array_obj.append(numbers[10])


def test_2326(conn, cursor):
    "2326 - test appending elements to an unconstrained table"
    data = [1, 3, 6, 10, 15, 21]
    typ = conn.gettype("UDT_UNCONSTRAINEDTABLE")
    obj = typ.newobject(data)
    cursor.execute("select :1 from dual", [obj])
    (output_obj,) = cursor.fetchone()
    assert output_obj.aslist() == data


def test_2327(conn, cursor):
    "2327 - test collection with thousands of entries"
    typ = conn.gettype("PKG_TESTNUMBERARRAYS.UDT_NUMBERLIST")
    obj = typ.newobject()
    obj.setelement(1, 1)
    running_total = 1
    for i in range(1, 35000):
        running_total += i + 1
        obj.append(running_total)
    result = cursor.callfunc(
        "pkg_TestNumberArrays.TestInArrays", int, (2327, obj)
    )
    assert result == 7146445847327


def test_2328(skip_unless_thick_mode, conn):
    "2328 - test object with unknown type in one of its attributes"
    typ = conn.gettype("UDT_OBJECTWITHXMLTYPE")
    assert typ.attributes[1].type == oracledb.DB_TYPE_UNKNOWN


def test_2329(skip_unless_thick_mode, conn):
    "2329 - test object with unknown type as the element type"
    typ = conn.gettype("UDT_XMLTYPEARRAY")
    assert typ.element_type == oracledb.DB_TYPE_UNKNOWN


def test_2330(conn):
    "2330 - test DB Object repr()"
    typ = conn.gettype("UDT_ARRAY")
    obj = typ.newobject()
    fqn = f"{typ.schema}.{typ.name}"
    expected_str = f"^<oracledb.DbObject {fqn} at 0x.+>$"
    assert re.fullmatch(expected_str, repr(obj)) is not None

    # object of a package
    typ = conn.gettype("PKG_TESTSTRINGARRAYS.UDT_STRINGLIST")
    obj = typ.newobject()
    fqn = f"{typ.schema}.{typ.package_name}.{typ.name}"
    expected_str = f"^<oracledb.DbObject {fqn} at 0x.+>$"
    assert re.fullmatch(expected_str, repr(obj)) is not None


def test_2331(conn, test_env):
    "2331 - test creating an object with invalid data type"
    type_obj = conn.gettype("UDT_ARRAY")
    with test_env.assert_raises_full_code("DPY-3013"):
        type_obj.newobject([490, "not a number"])
    with test_env.assert_raises_full_code("DPY-3013"):
        type_obj([71, "not a number"])


def test_2332(conn):
    "2332 - test getting an invalid attribute name from an object"
    typ = conn.gettype("UDT_OBJECT")
    obj = typ.newobject()
    with pytest.raises(AttributeError):
        obj.MISSING


def test_2333(conn, test_env):
    "2333 - test validating a string attribute"
    typ = conn.gettype("UDT_OBJECT")
    obj = typ.newobject()
    for attr_name, max_size in [
        ("STRINGVALUE", 60),
        ("FIXEDCHARVALUE", 10),
        ("NSTRINGVALUE", 120),
        ("NFIXEDCHARVALUE", 20),
        ("RAWVALUE", 16),
    ]:
        value = "A" * max_size
        setattr(obj, attr_name, value)
        value += "X"
        with test_env.assert_raises_full_code("DPY-2043"):
            setattr(obj, attr_name, value)


def test_2334(conn, test_env):
    "2334 - test validating a string element value"
    typ = conn.gettype("PKG_TESTSTRINGARRAYS.UDT_STRINGLIST")
    obj = typ.newobject()
    obj.append("A" * 100)
    with test_env.assert_raises_full_code("DPY-2044"):
        obj.append("A" * 101)
    obj.append("B" * 100)
    with test_env.assert_raises_full_code("DPY-2044"):
        obj.setelement(2, "C" * 101)


def test_2335(conn):
    "2335 - test validating a string attribute with null value"
    typ = conn.gettype("UDT_OBJECT")
    obj = typ.newobject()
    obj.STRINGVALUE = None


def test_2336(conn, test_env):
    "2336 - test initializing (with a sequence) a non collection obj"
    obj_type = conn.gettype("UDT_OBJECT")
    with test_env.assert_raises_full_code("DPY-2036"):
        obj_type.newobject([1, 2])
    with test_env.assert_raises_full_code("DPY-2036"):
        obj_type([3, 4])


def test_2337(conn):
    "2337 - test %ROWTYPE with all types"
    sub_obj_type = conn.gettype("UDT_SUBOBJECT")
    sub_arr_type = conn.gettype("UDT_OBJECTARRAY")
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
        ("DECIMALVALUE", oracledb.DB_TYPE_NUMBER, 20, 6, None),
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
    obj_type = conn.gettype("TESTALLTYPES%ROWTYPE")
    actual_metadata = [
        (attr.name, attr.type, attr.precision, attr.scale, attr.max_size)
        for attr in obj_type.attributes
    ]
    assert actual_metadata == expected_metadata


def test_2338(cursor):
    "2338 - test collection iteration"
    cursor.execute("select udt_array(5, 10, 15) from dual")
    (obj,) = cursor.fetchone()
    result = [i for i in obj]
    assert result == [5, 10, 15]


def test_2339(skip_unless_thin_mode, cursor):
    "2339 - test fetching an object containing an XmlType instance"
    num_val = 2339
    xml_val = "<item>test_2339</item>"
    str_val = "A string for test 2339"
    cursor.execute(
        f"""
        select udt_ObjectWithXmlType({num_val}, sys.xmltype('{xml_val}'),
                '{str_val}') from dual
        """
    )
    (obj,) = cursor.fetchone()
    assert obj.NUMBERVALUE == num_val
    assert obj.XMLVALUE == xml_val
    assert obj.STRINGVALUE == str_val


def test_2340(conn, cursor):
    "2340 - test DbObject instances are retained across getvalue() calls"
    typ = conn.gettype("UDT_OBJECT")
    obj = typ.newobject()
    var = cursor.var(typ)
    var.setvalue(0, obj)
    assert var.getvalue() is obj


def test_2341(test_env):
    "2341 - test insufficient privileges for gettype()"
    main_user = test_env.main_user.upper()
    conn = test_env.get_connection(
        user=test_env.proxy_user, password=test_env.proxy_password
    )
    with test_env.assert_raises_full_code("DPY-2035"):
        conn.gettype(f"{main_user}.UDT_OBJECTARRAY")


def test_2342(conn, cursor, test_env):
    "2342 - test nested records"
    test_env.skip_unless_server_version(21)
    options = [(None, None), (1, None), (None, 2), (1, 2)]
    typ = conn.gettype("PKG_TESTNESTEDRECORDS.UDT_OUTER")
    for option in options:
        value1, value2 = option
        obj = cursor.callfunc(
            "pkg_TestNestedRecords.GetOuter", typ, (value1, value2)
        )
        assert obj.INNER1 is not None
        assert obj.INNER1.ATTR1 is None
        assert obj.INNER1.ATTR2 == value1
        assert obj.INNER2 is not None
        assert obj.INNER2.ATTR1 is None
        assert obj.INNER2.ATTR2 == value2


def test_2343(conn, cursor):
    "2343 - test varray of numbers"
    obj_type = conn.gettype("UDT_VARRAYOFNUMBER")
    obj = cursor.callfunc("pkg_NestedTable.GetVarrayOfNumber", obj_type)
    assert obj.aslist() == [10, 20, 30]


def test_2344(conn, cursor):
    "2344 - test table of numbers"
    obj_type = conn.gettype("UDT_TABLEOFNUMBER")
    obj = cursor.callfunc("pkg_NestedTable.GetTableOfNumber", obj_type)
    assert obj.aslist() == [15, 25, 35, 45]


def test_2345(conn, cursor, test_env):
    "2345 - test table of varray of numbers"
    obj_type = conn.gettype("UDT_TABLEOFVARRAYOFNUMBER")
    obj = cursor.callfunc("pkg_NestedTable.GetTableOfVarrayOfNumber", obj_type)
    plain_obj = test_env.get_db_object_as_plain_object(obj)
    assert plain_obj == [[10, 20], [30, 40]]


def test_2346(conn, cursor, test_env):
    "2346 - test nested table of nested tables"
    num_tab_type = conn.gettype("UDT_TABLEOFNUMBER")
    tab_num_tab_type = conn.gettype("UDT_TABLEOFTABLEOFNUMBER")

    num_tab_1 = num_tab_type.newobject([1, 2])
    num_tab_2 = num_tab_type.newobject([3, 4, 5])
    num_tab_3 = num_tab_type.newobject([6, 7, 8, 9, 10])
    tab_num_tab = tab_num_tab_type.newobject(
        [num_tab_1, None, num_tab_2, None, num_tab_3]
    )

    cursor.execute(
        """
        insert into NestedCollectionTests (Id, TableCol)
        values (:1, :2)
        """,
        [1, tab_num_tab],
    )
    cursor.execute("select TableCol from NestedCollectionTests")
    (obj,) = cursor.fetchone()
    plain_obj = test_env.get_db_object_as_plain_object(obj)
    expected_data = [[1, 2], None, [3, 4, 5], None, [6, 7, 8, 9, 10]]
    assert plain_obj == expected_data


def test_2347(conn, cursor, test_env):
    "2347 - test nested table of varrays"
    num_tab_type = conn.gettype("UDT_TABLEOFNUMBER")
    arr_num_tab_type = conn.gettype("UDT_VARRAYOFTABLEOFNUMBER")

    num_tab_1 = num_tab_type.newobject([4, 8])
    num_tab_2 = num_tab_type.newobject([1, 3, 5])
    num_tab_3 = num_tab_type.newobject([2, 6, 10, 7, 9])
    tab_num_tab = arr_num_tab_type.newobject(
        [num_tab_1, None, num_tab_2, None, num_tab_3]
    )

    cursor.execute(
        """
        insert into NestedCollectionTests (Id, VarrayCol)
        values (:1, :2)
        """,
        [1, tab_num_tab],
    )
    cursor.execute("select VarrayCol from NestedCollectionTests")
    (obj,) = cursor.fetchone()
    plain_obj = test_env.get_db_object_as_plain_object(obj)
    expected_data = [[4, 8], None, [1, 3, 5], None, [2, 6, 10, 7, 9]]
    assert plain_obj == expected_data


def test_2348(conn, test_env):
    "2348 - test using collection methods on an object that is not one"
    obj_type = conn.gettype("UDT_OBJECT")
    obj = obj_type.newobject()
    with test_env.assert_raises_full_code("DPY-2036"):
        obj.append(5)
    with test_env.assert_raises_full_code("DPY-2036"):
        obj.asdict()
    with test_env.assert_raises_full_code("DPY-2036"):
        obj.aslist()
    with test_env.assert_raises_full_code("DPY-2036"):
        obj.delete(5)
    with test_env.assert_raises_full_code("DPY-2036"):
        obj.exists(5)
    with test_env.assert_raises_full_code("DPY-2036"):
        obj.extend([5])
    with test_env.assert_raises_full_code("DPY-2036"):
        obj.first()
    with test_env.assert_raises_full_code("DPY-2036"):
        obj.getelement(5)
    with test_env.assert_raises_full_code("DPY-2036"):
        obj.last()
    with test_env.assert_raises_full_code("DPY-2036"):
        obj.next(5)
    with test_env.assert_raises_full_code("DPY-2036"):
        obj.prev(5)
    with test_env.assert_raises_full_code("DPY-2036"):
        obj.setelement(5, None)
    with test_env.assert_raises_full_code("DPY-2036"):
        obj.size()
    with test_env.assert_raises_full_code("DPY-2036"):
        obj.trim(0)
