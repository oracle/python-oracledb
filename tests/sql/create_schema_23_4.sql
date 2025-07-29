/*-----------------------------------------------------------------------------
 * Copyright (c) 2023, 2024, Oracle and/or its affiliates.
 *
 * This software is dual-licensed to you under the Universal Permissive License
 * (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl and Apache License
 * 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose
 * either license.*
 *
 * If you elect to accept the software under the Apache License, Version 2.0,
 * the following applies:
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *---------------------------------------------------------------------------*/

/*-----------------------------------------------------------------------------
 * create_schema_23_4.sql
 *
 * Performs the actual work of creating and populating the schemas with the
 * database objects used by the python-oracledb test suite that require Oracle
 * Database 23.4 or higher. It is executed by the Python script
 * create_schema.py.
 *---------------------------------------------------------------------------*/

create domain &main_user..SimpleDomain as number(3, 0) NOT NULL
/

create table &main_user..TableWithDomainAndAnnotations (
    id number(9) not null,
    age number(3, 0) domain &main_user..SimpleDomain
    annotations (
        Anno_1 'first annotation',
        Anno_2 'second annotation',
        Anno_3
    )
)
/

insert into &main_user..TableWithDomainAndAnnotations values (1, 25)
/

commit
/

create table &main_user..TestVectors (
    IntCol                  number(9) not null,
    VectorFlexAllCol        vector,
    VectorFlexTypeCol       vector(2),
    VectorFlex8Col          vector(*, int8),
    VectorFlex32Col         vector(*, float32),
    VectorFlex64Col         vector(*, float64),
    Vector8Col              vector(16, int8),
    Vector32Col             vector(16, float32),
    Vector64Col             vector(16, float64)
)
/

create table &main_user..TestCompressedJson (
    IntCol number(9) not null,
    JsonCol json not null
)
json (JsonCol)
store as (compress high)
/

create table &main_user..TestBooleans (
    IntCol                  number(9) not null,
    BooleanCol1             boolean not null,
    BooleanCol2             boolean,
    BooleanCol3             boolean
)
/
