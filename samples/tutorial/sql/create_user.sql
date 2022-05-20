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
 * create_user.sql (Setup Section)
 *   Creates a database user for the python-oracledb tutorial
 * For Oracle Autonomous Database, use 'admin' instead of system.
 * You will be prompted for the new username and the new password to use.
 *
 * When you no longer need this user, run drop_user.sql to drop the user
 *
 *---------------------------------------------------------------------------*/

create user &user
/

grant
    create session,
    create table,
    create procedure,
    create type,
    create sequence,
    select any dictionary,
    unlimited tablespace
to &user
/

begin

    for r in
            ( select role
              from dba_roles
              where role in ('SODA_APP', 'AQ_ADMINISTRATOR_ROLE')
            ) loop
        execute immediate 'grant ' || r.role || ' to &user';
    end loop;

end;
/

alter user &user identified by "&pw"
/
