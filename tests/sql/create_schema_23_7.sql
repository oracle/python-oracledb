/*-----------------------------------------------------------------------------
 * Copyright (c) 2024, 2025, Oracle and/or its affiliates.
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
 * create_schema_23_7.sql
 *
 * Performs the actual work of creating and populating the schemas with the
 * database objects used by the python-oracledb test suite that require Oracle
 * Database 23.7 or higher. It is executed by the Python script
 * create_schema.py.
 *---------------------------------------------------------------------------*/

create table &main_user..TestSparseVectors (
    IntCol                      number(9) not null,
    SparseVectorFlexAllCol      vector(*, *, sparse),
    SparseVectorFlexTypeCol     vector(2, *, sparse),
    SparseVectorFlex8Col        vector(*, int8, sparse),
    SparseVectorFlex32Col       vector(*, float32, sparse),
    SparseVectorFlex64Col       vector(*, float64, sparse),
    SparseVector8Col            vector(16, int8, sparse),
    SparseVector32Col           vector(16, float32, sparse),
    SparseVector64Col           vector(16, float64, sparse)
)
/
