# -----------------------------------------------------------------------------
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
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

import oracledb
import pytest


@pytest.fixture(autouse=True)
def module_checks(anyio_backend, skip_unless_thin_mode):
    pass


async def _test_data(
    cursor,
    test_env,
    expected_int_value,
    expected_obj_value,
    expected_array_value,
):
    int_value, object_value, array_value = await cursor.fetchone()
    if object_value is not None:
        object_value = await test_env.get_db_object_as_plain_object_async(
            object_value
        )
    if array_value is not None:
        array_value = array_value.aslist()
    assert int_value == expected_int_value
    assert object_value == expected_obj_value
    assert array_value == expected_array_value


async def test_5600(async_conn, async_cursor):
    "5600 - test binding an object (IN)"
    type_obj = await async_conn.gettype("UDT_OBJECT")
    obj = type_obj.newobject()
    obj.NUMBERVALUE = 13
    obj.STRINGVALUE = "Test String"
    result = await async_cursor.callfunc(
        "pkg_TestBindObject.GetStringRep", str, [obj]
    )
    exp = "udt_Object(13, 'Test String', null, null, null, null, null)"
    assert result == exp
    obj.NUMBERVALUE = None
    obj.STRINGVALUE = "Test With Dates"
    obj.DATEVALUE = datetime.datetime(2016, 2, 10)
    obj.TIMESTAMPVALUE = datetime.datetime(2016, 2, 10, 14, 13, 50)
    result = await async_cursor.callfunc(
        "pkg_TestBindObject.GetStringRep", str, [obj]
    )
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
    sub_type_obj = await async_conn.gettype("UDT_SUBOBJECT")
    sub_obj = sub_type_obj.newobject()
    sub_obj.SUBNUMBERVALUE = decimal.Decimal("18.25")
    sub_obj.SUBSTRINGVALUE = "Sub String"
    obj.SUBOBJECTVALUE = sub_obj
    result = await async_cursor.callfunc(
        "pkg_TestBindObject.GetStringRep", str, [obj]
    )
    expected_value = (
        "udt_Object(null, 'Test With Dates', null, null, "
        "null, udt_SubObject(18.25, 'Sub String'), null)"
    )
    assert result == expected_value


async def test_5601(async_conn):
    "5601 - test copying an object"
    type_obj = await async_conn.gettype("UDT_OBJECT")
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


async def test_5602(async_cursor, test_env):
    "5602 - test fetching objects"
    await async_cursor.execute(
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
    assert async_cursor.description == expected_value
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
    await _test_data(
        async_cursor, test_env, 1, expected_value, [5, 10, None, 20]
    )
    await _test_data(async_cursor, test_env, 2, None, [3, None, 9, 12, 15])
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
    await _test_data(async_cursor, test_env, 3, expected_value, None)


async def test_5603(async_conn):
    "5603 - test getting object type"
    type_obj = await async_conn.gettype("UDT_OBJECT")
    assert not type_obj.iscollection
    assert type_obj.schema == async_conn.username.upper()
    assert type_obj.name == "UDT_OBJECT"
    sub_object_value_type = await async_conn.gettype("UDT_SUBOBJECT")
    sub_object_array_type = await async_conn.gettype("UDT_OBJECTARRAY")
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


async def test_5604(async_conn, async_cursor):
    "5604 - test object type data"
    await async_cursor.execute(
        """
        select ObjectCol
        from TestObjects
        where ObjectCol is not null
          and rownum <= 1
        """
    )
    (obj,) = await async_cursor.fetchone()
    assert obj.type.schema == async_conn.username.upper()
    assert obj.type.name == "UDT_OBJECT"
    assert obj.type.attributes[0].name == "NUMBERVALUE"


async def test_5605(async_conn, async_cursor, test_env):
    "5605 - test inserting and then querying object with all data types"
    await async_cursor.execute("delete from TestClobs")
    await async_cursor.execute("delete from TestNClobs")
    await async_cursor.execute("delete from TestBlobs")
    await async_cursor.execute("delete from TestObjects where IntCol > 3")
    await async_cursor.execute(
        """
        insert into TestClobs (IntCol, ClobCol)
        values (1, 'A short CLOB')
        """
    )
    await async_cursor.execute(
        """
        insert into TestNClobs (IntCol, NClobCol)
        values (1, 'A short NCLOB')
        """
    )
    await async_cursor.execute(
        """
        insert into TestBlobs (IntCol, BlobCol)
        values (1, utl_raw.cast_to_raw('A short BLOB'))
        """
    )
    await async_conn.commit()
    await async_cursor.execute("select CLOBCol from TestClobs")
    (clob,) = await async_cursor.fetchone()
    await async_cursor.execute("select NCLOBCol from TestNClobs")
    (nclob,) = await async_cursor.fetchone()
    await async_cursor.execute("select BLOBCol from TestBlobs")
    (blob,) = await async_cursor.fetchone()
    type_obj = await async_conn.gettype("UDT_OBJECT")
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
    sub_type_obj = await async_conn.gettype("UDT_SUBOBJECT")
    sub_obj = sub_type_obj.newobject()
    sub_obj.SUBNUMBERVALUE = 23
    sub_obj.SUBSTRINGVALUE = "Substring value"
    obj.SUBOBJECTVALUE = sub_obj
    await async_cursor.execute(
        """
        insert into TestObjects (IntCol, ObjectCol)
        values (4, :obj)
        """,
        obj=obj,
    )
    await async_cursor.execute(
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
    await _test_data(async_cursor, test_env, 4, expected_value, None)

    obj.CLOBVALUE = await async_conn.createlob(oracledb.DB_TYPE_CLOB)
    obj.NCLOBVALUE = await async_conn.createlob(oracledb.DB_TYPE_NCLOB)
    obj.BLOBVALUE = await async_conn.createlob(oracledb.DB_TYPE_BLOB)
    await obj.CLOBVALUE.write("A short CLOB (modified)")
    await obj.NCLOBVALUE.write("A short NCLOB (modified)")
    await obj.BLOBVALUE.write(b"A short BLOB (modified)")
    await async_cursor.execute(
        """
        insert into TestObjects (IntCol, ObjectCol)
        values (5, :obj)
        """,
        obj=obj,
    )
    await async_cursor.execute(
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
    await _test_data(async_cursor, test_env, 5, expected_value, None)
    await async_conn.rollback()


async def test_5606(async_conn, test_env):
    "5606 - test trying to find an object type that does not exist"
    with pytest.raises(TypeError):
        await async_conn.gettype(2)
    with test_env.assert_raises_full_code("DPY-2035"):
        await async_conn.gettype("A TYPE THAT DOES NOT EXIST")


async def test_5607(async_conn, test_env):
    "5607 - test appending an object of the wrong type to a collection"
    collection_obj_type = await async_conn.gettype("UDT_OBJECTARRAY")
    collection_obj = collection_obj_type.newobject()
    array_obj_type = await async_conn.gettype("UDT_ARRAY")
    array_obj = array_obj_type.newobject()
    with test_env.assert_raises_full_code("DPY-2008"):
        collection_obj.append(array_obj)


async def test_5608(async_conn):
    "5608 - test that referencing a sub object affects the parent object"
    obj_type = await async_conn.gettype("UDT_OBJECT")
    sub_obj_type = await async_conn.gettype("UDT_SUBOBJECT")
    obj = obj_type.newobject()
    obj.SUBOBJECTVALUE = sub_obj_type.newobject()
    obj.SUBOBJECTVALUE.SUBNUMBERVALUE = 5
    obj.SUBOBJECTVALUE.SUBSTRINGVALUE = "Substring"
    assert obj.SUBOBJECTVALUE.SUBNUMBERVALUE == 5
    assert obj.SUBOBJECTVALUE.SUBSTRINGVALUE == "Substring"


async def test_5609(async_conn, test_env):
    "5609 - test accessing sub object after parent object destroyed"
    obj_type = await async_conn.gettype("UDT_OBJECT")
    sub_obj_type = await async_conn.gettype("UDT_SUBOBJECT")
    array_type = await async_conn.gettype("UDT_OBJECTARRAY")
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
    val = await test_env.get_db_object_as_plain_object_async(sub_obj_array)
    assert val == [(2, "AB"), (3, "CDE")]


async def test_5610(async_conn, test_env):
    "5610 - test assigning an object of wrong type to an object attribute"
    obj_type = await async_conn.gettype("UDT_OBJECT")
    obj = obj_type.newobject()
    wrong_obj_type = await async_conn.gettype("UDT_OBJECTARRAY")
    wrong_obj = wrong_obj_type.newobject()
    with test_env.assert_raises_full_code("DPY-2008"):
        setattr(obj, "SUBOBJECTVALUE", wrong_obj)


async def test_5611(async_conn, async_cursor, test_env):
    "5611 - test setting value of object variable to wrong object type"
    obj_type = await async_conn.gettype("UDT_OBJECT")
    wrong_obj_type = await async_conn.gettype("UDT_OBJECTARRAY")
    wrong_obj = wrong_obj_type.newobject()
    var = async_cursor.var(obj_type)
    with test_env.assert_raises_full_code("DPY-2008"):
        var.setvalue(0, wrong_obj)


async def test_5612(async_conn, test_env):
    "5612 - test trimming a number of elements from a collection"
    sub_obj_type = await async_conn.gettype("UDT_SUBOBJECT")
    array_type = await async_conn.gettype("UDT_OBJECTARRAY")
    data = [(1, "AB"), (2, "CDE"), (3, "FGH"), (4, "IJK"), (5, "LMN")]
    array_obj = array_type()
    for num_val, str_val in data:
        subObj = sub_obj_type()
        subObj.SUBNUMBERVALUE = num_val
        subObj.SUBSTRINGVALUE = str_val
        array_obj.append(subObj)
    assert (
        await test_env.get_db_object_as_plain_object_async(array_obj) == data
    )
    array_obj.trim(2)
    assert (
        await test_env.get_db_object_as_plain_object_async(array_obj)
        == data[:3]
    )
    array_obj.trim(1)
    assert (
        await test_env.get_db_object_as_plain_object_async(array_obj)
        == data[:2]
    )
    array_obj.trim(0)
    assert (
        await test_env.get_db_object_as_plain_object_async(array_obj)
        == data[:2]
    )
    array_obj.trim(2)
    assert await test_env.get_db_object_as_plain_object_async(array_obj) == []


async def test_5613(async_conn, test_env):
    "5613 - test the metadata of a SQL type"
    user = test_env.main_user.upper()
    typ = await async_conn.gettype("UDT_OBJECTARRAY")
    assert typ.schema == user
    assert typ.name == "UDT_OBJECTARRAY"
    assert typ.package_name is None
    assert typ.element_type.schema == user
    assert typ.element_type.name == "UDT_SUBOBJECT"
    assert typ.element_type.package_name is None


async def test_5614(async_conn, test_env):
    "5614 - test the metadata of a PL/SQL type"
    typ = await async_conn.gettype("PKG_TESTSTRINGARRAYS.UDT_STRINGLIST")
    assert typ.schema == test_env.main_user.upper()
    assert typ.name == "UDT_STRINGLIST"
    assert typ.package_name == "PKG_TESTSTRINGARRAYS"
    assert typ.element_type == oracledb.DB_TYPE_VARCHAR


async def test_5615(async_conn, async_cursor):
    "5615 - test collection with thousands of entries"
    typ = await async_conn.gettype("PKG_TESTNUMBERARRAYS.UDT_NUMBERLIST")
    obj = typ.newobject()
    obj.setelement(1, 1)
    running_total = 1
    for i in range(1, 35000):
        running_total += i + 1
        obj.append(running_total)
    result = await async_cursor.callfunc(
        "pkg_TestNumberArrays.TestInArrays", int, (2327, obj)
    )
    assert result == 7146445847327


async def test_5616(async_conn):
    "5616 - test %ROWTYPE with all types"
    sub_obj_type = await async_conn.gettype("UDT_SUBOBJECT")
    sub_arr_type = await async_conn.gettype("UDT_OBJECTARRAY")
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
    obj_type = await async_conn.gettype("TESTALLTYPES%ROWTYPE")
    actual_metadata = [
        (attr.name, attr.type, attr.precision, attr.scale, attr.max_size)
        for attr in obj_type.attributes
    ]
    assert actual_metadata == expected_metadata


async def test_5617(async_cursor):
    "5617 - test collection iteration"
    await async_cursor.execute("select udt_array(5, 10, 15) from dual")
    (obj,) = await async_cursor.fetchone()
    result = [i for i in obj]
    assert result == [5, 10, 15]


async def test_5618(test_env):
    "5618 - test insufficient privileges for gettype()"
    user = test_env.proxy_user
    password = test_env.proxy_password
    main_user = test_env.main_user.upper()
    async with await test_env.get_connection_async(
        user=user, password=password
    ) as conn:
        with test_env.assert_raises_full_code("DPY-2035"):
            await conn.gettype(f"{main_user}.UDT_OBJECTARRAY")


async def test_5619(async_conn, async_cursor):
    "5619 - test nested records"
    options = [(None, None), (1, None), (None, 2), (1, 2)]
    typ = await async_conn.gettype("PKG_TESTNESTEDRECORDS.UDT_OUTER")
    for option in options:
        value1, value2 = option
        obj = await async_cursor.callfunc(
            "pkg_TestNestedRecords.GetOuter", typ, (value1, value2)
        )
        assert obj.INNER1 is not None
        assert obj.INNER1.ATTR1 is None
        assert obj.INNER1.ATTR2 == value1
        assert obj.INNER2 is not None
        assert obj.INNER2.ATTR1 is None
        assert obj.INNER2.ATTR2 == value2
