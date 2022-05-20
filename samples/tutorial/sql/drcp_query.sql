/*-----------------------------------------------------------------------------
 * Copyright (c) 2017, 2022, Oracle and/or its affiliates.
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
 * drcp_query.sql (Section 2.4 and 2.5)
 *---------------------------------------------------------------------------*/

set echo off verify off feedback off linesize 80 pagesize 1000

accept pw char prompt 'Enter database password for SYSTEM: ' hide
accept connect_string char prompt 'Enter database connection string: '

-- Connect to the CDB to see pool statistics
connect system/&pw@&connect_string

col cclass_name format a40

-- Some DRCP pool statistics
select cclass_name, num_requests, num_hits, num_misses from v$cpool_cc_stats;

exit
