# -----------------------------------------------------------------------------
# type_input.py (Section 6.3)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Copyright (c) 2017, 2023, Oracle and/or its affiliates.
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
import json

con = oracledb.connect(
    user=db_config.user, password=db_config.pw, dsn=db_config.dsn
)
cur = con.cursor()

# Create table
cur.execute(
    """
    begin
        execute immediate 'drop table BuildingTable';
    exception when others then
        if sqlcode <> -942 then
            raise;
        end if;
    end;
    """
)
cur.execute(
    """
    create table BuildingTable (
        ID number(9) not null,
        BuildingDetails varchar2(400),
        constraint TestTempTable_pk primary key (ID)
    )
    """
)

# Create a Python class for a Building


class Building(object):
    def __init__(self, building_id, description, num_floors):
        self.building_id = building_id
        self.description = description
        self.num_floors = num_floors

    def __repr__(self):
        return "<Building %s: %s>" % (self.building_id, self.description)

    def __eq__(self, other):
        if isinstance(other, Building):
            return (
                other.building_id == self.building_id
                and other.description == self.description
                and other.num_floors == self.num_floors
            )
        return NotImplemented

    def to_json(self):
        return json.dumps(self.__dict__)

    @classmethod
    def from_json(cls, value):
        result = json.loads(value)
        return cls(**result)


# Convert a Python building object to a SQL JSON type that can be read as a
# string


def building_in_converter(value):
    return value.to_json()


def input_type_handler(cursor, value, num_elements):
    if isinstance(value, Building):
        return cursor.var(
            oracledb.DB_TYPE_VARCHAR,
            arraysize=num_elements,
            inconverter=building_in_converter,
        )


building = Building(1, "The First Building", 5)  # Python object
cur.execute("truncate table BuildingTable")
cur.inputtypehandler = input_type_handler
cur.execute(
    "insert into BuildingTable (ID, BuildingDetails) values (:1, :2)",
    (building.building_id, building),
)
con.commit()

# Query the row
print("Querying the row just inserted...")
cur.execute("select ID, BuildingDetails from BuildingTable")
for int_col, string_col in cur:
    print("Building ID:", int_col)
    print("Building Details in JSON format:", string_col)
