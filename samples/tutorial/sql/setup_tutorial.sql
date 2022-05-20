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
 * setup_tutorial.sql (Setup Section)
 *   Creates the tables, sequence etc. used by the python-oracledb tutorial.
 *---------------------------------------------------------------------------*/

begin execute immediate 'drop table emp'; exception when others then if sqlcode <> -942 then raise; end if; end;
/

create table emp
       (empno number(4) not null,
        ename varchar2(10),
        job varchar2(9),
        mgr number(4),
        hiredate date,
        sal number(7, 2),
        comm number(7, 2),
        deptno number(2))
/

insert into emp values
        (7369, 'SMITH',  'CLERK',     7902,
        to_date('17-DEC-1980', 'DD-MON-YYYY'),  800, NULL, 20)
/

insert into emp values
        (7499, 'ALLEN',  'SALESMAN',  7698,
        to_date('20-FEB-1981', 'DD-MON-YYYY'), 1600,  300, 30)
/

insert into emp values
        (7521, 'WARD',   'SALESMAN',  7698,
        to_date('22-FEB-1981', 'DD-MON-YYYY'), 1250,  500, 30)
/

insert into emp values
        (7566, 'JONES',  'MANAGER',   7839,
        to_date('2-APR-1981', 'DD-MON-YYYY'),  2975, NULL, 20)
/

insert into emp values
        (7654, 'MARTIN', 'SALESMAN',  7698,
        to_date('28-SEP-1981', 'DD-MON-YYYY'), 1250, 1400, 30)
/

insert into emp values
        (7698, 'BLAKE',  'MANAGER',   7839,
        to_date('1-MAY-1981', 'DD-MON-YYYY'),  2850, NULL, 30)
/

insert into emp values
        (7782, 'CLARK',  'MANAGER',   7839,
        to_date('9-JUN-1981', 'DD-MON-YYYY'),  2450, NULL, 10)
/

insert into emp values
        (7788, 'SCOTT',  'ANALYST',   7566,
        to_date('09-DEC-1982', 'DD-MON-YYYY'), 3000, NULL, 20)
/
insert into emp values
        (7839, 'KING',   'PRESIDENT', NULL,
        to_date('17-NOV-1981', 'DD-MON-YYYY'), 5000, NULL, 10)
/

insert into emp values
        (7844, 'TURNER', 'SALESMAN',  7698,
        to_date('8-SEP-1981', 'DD-MON-YYYY'),  1500,    0, 30)
/

insert into emp values
        (7876, 'ADAMS',  'CLERK',     7788,
        to_date('12-JAN-1983', 'DD-MON-YYYY'), 1100, NULL, 20)
/

insert into emp values
        (7900, 'JAMES',  'CLERK',     7698,
        to_date('3-DEC-1981', 'DD-MON-YYYY'),   950, NULL, 30)
/

insert into emp values
        (7902, 'FORD',   'ANALYST',   7566,
        to_date('3-DEC-1981', 'DD-MON-YYYY'),  3000, NULL, 20)
/

insert into emp values
        (7934, 'MILLER', 'CLERK',     7782,
        to_date('23-JAN-1982', 'DD-MON-YYYY'), 1300, NULL, 10)
/

begin execute immediate 'drop table dept'; exception when others then if sqlcode <> -942 then raise; end if; end;
/

create table dept
       (deptno number(2),
        dname varchar2(14),
        loc varchar2(13) )
/

insert into dept values (10, 'ACCOUNTING', 'NEW YORK')
/

insert into dept values (20, 'RESEARCH',   'DALLAS')
/

insert into dept values (30, 'SALES',      'CHICAGO')
/

insert into dept values (40, 'OPERATIONS', 'BOSTON')
/

commit
/

-- Table for clob.py and clob_string.py

begin execute immediate 'drop table testclobs'; exception when others then if sqlcode <> -942 then raise; end if; end;
/

create table testclobs (
    id     number not null,
    myclob clob not null
)
/

-- Sequence for connect_pool.py

begin execute immediate 'drop sequence myseq'; exception when others then if sqlcode <> -2289 then raise; end if; end;
/

create sequence myseq
/

-- Table for bind_insert.py
begin
  execute immediate 'drop table mytab';
exception
when others then
  if sqlcode not in (-00942) then
    raise;
  end if;
end;
/

create table mytab (id number, data varchar2(20), constraint my_pk primary key (id))
/

--Table for query_arraysize.py
begin
  execute immediate 'drop table bigtab';
exception
when others then
  if sqlcode not in (-00942) then
    raise;
  end if;
end;
/

create table bigtab (mycol varchar2(20))
/

begin
  for i in 1..20000
  loop
   insert into bigtab (mycol) values (dbms_random.string('A',20));
  end loop;
end;
/

commit
/

-- Table for plsql_func.py
begin
  execute immediate 'drop table ptab';
exception
when others then
  if sqlcode not in (-00942) then
    raise;
  end if;
end;
/

create table ptab (mydata varchar(20), myid number)
/

-- PL/SQL function for plsql_func.py
create or replace function myfunc(d_p in varchar2, i_p in number) return number as
  begin
    insert into ptab (mydata, myid) values (d_p, i_p);
    return (i_p * 2);
  end;
/

--PL/SQL procedure for plsql_proc.py
create or replace procedure myproc(v1_p in number, v2_p out number) as
begin
  v2_p := v1_p * 2;
end;
/
