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
 * create_schema_21.sql
 *
 * Performs the actual work of creating and populating the schemas with the
 * database objects used by the python-oracledb test suite that require Oracle
 * Database 21c or higher. It is executed by the Python script
 * create_schema.py.
 *---------------------------------------------------------------------------*/

create table &main_user..TestJson (
    IntCol number(9) not null,
    JsonCol json not null
)
/

create table &main_user..TestOsonCols (
    IntCol                              number(9) not null,
    OsonCol                             blob not null,
    constraint TestOsonCols_ck_1 check (OsonCol is json format oson)
)
/

insert into &main_user..TestJsonCols values (2,
    'null', empty_clob(), empty_blob())
/

begin
    dbms_aqadm.create_queue_table('&main_user..JSON_QUEUE_TAB', 'JSON');
    dbms_aqadm.create_queue('&main_user..TEST_JSON_QUEUE',
            '&main_user..JSON_QUEUE_TAB');
    dbms_aqadm.start_queue('&main_user..TEST_JSON_QUEUE');
end;
/
