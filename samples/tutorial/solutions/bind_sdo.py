# -----------------------------------------------------------------------------
# bind_sdo.py (Section 12.1)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Copyright (c) 2017, 2025, Oracle and/or its affiliates.
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

import oracledb
import db_config

con = oracledb.connect(
    user=db_config.user, password=db_config.pw, dsn=db_config.dsn
)
cur = con.cursor()

# Create table
cur.execute(
    """
    begin
        execute immediate 'drop table testgeometry';
    exception when others then
        if sqlcode <> -942 then
            raise;
        end if;
    end;
    """
)
cur.execute(
    """
    create table testgeometry (
        id number(9) not null,
        geometry MDSYS.SDO_GEOMETRY not null
    )
    """
)

# Create and populate Oracle objects
type_obj = con.gettype("MDSYS.SDO_GEOMETRY")
element_info_type_obj = con.gettype("MDSYS.SDO_ELEM_INFO_ARRAY")
ordinate_type_obj = con.gettype("MDSYS.SDO_ORDINATE_ARRAY")
obj = type_obj.newobject()
obj.SDO_GTYPE = 2003
obj.SDO_ELEM_INFO = element_info_type_obj.newobject()
obj.SDO_ELEM_INFO.extend([1, 1003, 3])
obj.SDO_ORDINATES = ordinate_type_obj.newobject()
obj.SDO_ORDINATES.extend([1, 1, 5, 7])

point_type_obj = con.gettype("MDSYS.SDO_POINT_TYPE")
obj.SDO_POINT = point_type_obj.newobject()
obj.SDO_POINT.X = 1
obj.SDO_POINT.Y = 2
obj.SDO_POINT.Z = 3

print("Created object", obj)

# Add a new row
print("Adding row to table...")
cur.execute("insert into testgeometry values (1, :objbv)", objbv=obj)
print("Row added!")

# (Change below here)

# Define a function to dump the contents of an Oracle object


def dumpobject(obj, prefix="  "):
    if obj.type.iscollection:
        print(prefix, "[")
        for value in obj.aslist():
            if isinstance(value, oracledb.Object):
                dumpobject(value, prefix + "  ")
            else:
                print(prefix + "  ", repr(value))
        print(prefix, "]")
    else:
        print(prefix, "{")
        for attr in obj.type.attributes:
            value = getattr(obj, attr.name)
            if isinstance(value, oracledb.Object):
                print(prefix + "  " + attr.name + " :")
                dumpobject(value, prefix + "    ")
            else:
                print(prefix + "  " + attr.name + " :", repr(value))
        print(prefix, "}")


# Query the row
print("Querying row just inserted...")
cur.execute("select id, geometry from testgeometry")
for id, obj in cur:
    print("Id: ", id)
    dumpobject(obj)
