/*-----------------------------------------------------------------------------
 * Copyright (c) 2020, 2025, Oracle and/or its affiliates.
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
 * create_schema.sql
 *
 * Performs the actual work of creating and populating the schemas with the
 * database objects used by the python-oracledb test suite. It is executed by
 * the Python script create_schema.py.
 *---------------------------------------------------------------------------*/

alter session set nls_date_format = 'YYYY-MM-DD HH24:MI:SS'
/
alter session set nls_numeric_characters='.,'
/
alter session set time_zone='+00:00'
/

create user &main_user identified by &main_password
/

create user &proxy_user identified by &proxy_password
/
alter user &proxy_user grant connect through &main_user
/

grant create session to &proxy_user
/

grant
    create session,
    create table,
    create procedure,
    create type,
    create view,
    select any dictionary,
    change notification,
    unlimited tablespace,
    ctxapp
to &main_user
/

grant aq_administrator_role to &main_user
/

begin

    for r in
            ( select role
              from dba_roles
              where role in ('SODA_APP')
            ) loop
        execute immediate 'grant ' || r.role || ' to &main_user';
    end loop;

end;
/

-- create edition
create edition &edition_name
/

grant use on edition &edition_name to &main_user
/

-- create types
create type &main_user..udt_SubObject as object (
    SubNumberValue                      number,
    SubStringValue                      varchar2(60)
);
/

create type &main_user..udt_ObjectArray as
varray(10) of &main_user..udt_SubObject;
/

create type &main_user..udt_Object as object (
    NumberValue                         number,
    StringValue                         varchar2(60),
    FixedCharValue                      char(10),
    NStringValue                        nvarchar2(60),
    NFixedCharValue                     nchar(10),
    RawValue                            raw(16),
    IntValue                            integer,
    SmallIntValue                       smallint,
    RealValue                           real,
    DoublePrecisionValue                double precision,
    FloatValue                          float,
    BinaryFloatValue                    binary_float,
    BinaryDoubleValue                   binary_double,
    DateValue                           date,
    TimestampValue                      timestamp,
    TimestampTZValue                    timestamp with time zone,
    TimestampLTZValue                   timestamp with local time zone,
    CLOBValue                           clob,
    NCLOBValue                          nclob,
    BLOBValue                           blob,
    SubObjectValue                      &main_user..udt_SubObject,
    SubObjectArray                      &main_user..udt_ObjectArray
);
/

create type &main_user..udt_Array as varray(10) of number;
/

create type &main_user..udt_UnconstrainedTable as table of number;
/

create or replace type &main_user..udt_Building as object (
    BuildingId                          number(9),
    NumFloors                           number(3),
    Description                         varchar2(60),
    DateBuilt                           date
);
/

create or replace type &main_user..udt_Book as object (
    Title                               varchar2(100),
    Authors                             varchar2(100),
    Price                               number(5,2)
);
/

create or replace type &main_user..udt_ObjectWithXmlType as object (
    NumberValue                         number(9),
    XMLValue                            sys.xmltype,
    StringValue                         varchar2(60)
);
/

create or replace type &main_user..udt_XmlTypeArray
as table of sys.xmltype;
/

-- create tables
create table &main_user..TestNumbers (
    IntCol                              number(9) not null,
    LongIntCol                          number(16) not null,
    NumberCol                           number(9, 2) not null,
    FloatCol                            float not null,
    UnconstrainedCol                    number not null,
    NullableCol                         number(38)
)
/

create table &main_user..TestStrings (
    IntCol                              number(9) not null,
    StringCol                           varchar2(20) not null,
    RawCol                              raw(30) not null,
    FixedCharCol                        char(40) not null,
    NullableCol                         varchar2(50)
)
/

create table &main_user..TestUnicodes (
    IntCol                              number(9) not null,
    UnicodeCol                          nvarchar2(20) not null,
    FixedUnicodeCol                     nchar(40) not null,
    NullableCol                         nvarchar2(50)
)
/

create table &main_user..TestDates (
    IntCol                              number(9) not null,
    DateCol                             date not null,
    NullableCol                         date
)
/

create table &main_user..TestCLOBs (
    IntCol                              number(9) not null,
    CLOBCol                             clob not null,
    ExtraNumCol1                        number(9),
    ExtraCLOBCol1                       clob,
    ExtraNumCol2                        number(9),
    ExtraCLOBCol2                       clob
)
/

create table &main_user..TestNCLOBs (
    IntCol                              number(9) not null,
    NCLOBCol                            nclob not null,
    ExtraNumCol1                        number(9),
    ExtraNCLOBCol1                      nclob,
    ExtraNumCol2                        number(9),
    ExtraNCLOBCol2                      nclob
)
/

create table &main_user..TestBLOBs (
    IntCol                              number(9) not null,
    BLOBCol                             blob not null,
    ExtraNumCol1                        number(9),
    ExtraBLOBCol1                       blob,
    ExtraNumCol2                        number(9),
    ExtraBLOBCol2                       blob
)
/

create table &main_user..TestBfiles (
    IntCol                              number(9) not null,
    BfileCol                            bfile not null
)
/

create table &main_user..TestXML (
    IntCol                              number(9) not null,
    XMLCol                              xmltype not null
)
/

create table &main_user..TestTempXML (
    IntCol                              number(9) not null,
    XMLCol                              xmltype not null
)
/

create table &main_user..TestLongs (
    IntCol                              number(9) not null,
    LongCol                             long
) nocompress
/

create table &main_user..TestLongRaws (
    IntCol                              number(9) not null,
    LongRawCol                          long raw
) nocompress
/

create table &main_user..TestTempTable (
    IntCol                              number(9) not null,
    StringCol1                          varchar2(400),
    StringCol2                          varchar2(400),
    NumberCol                           number(25,2),
    constraint TestTempTable_pk primary key (IntCol)
)
/

create table &main_user..TestArrayDML (
    IntCol                              number(9) not null,
    StringCol                           varchar2(100),
    IntCol2                             number(3),
    constraint TestArrayDML_pk primary key (IntCol)
)
/

create table &main_user..TestObjects (
    IntCol                              number(9) not null,
    ObjectCol                           &main_user..udt_Object,
    ArrayCol                            &main_user..udt_Array
)
/

create table &main_user..TestTimestamps (
    IntCol                              number(9) not null,
    TimestampCol                        timestamp not null,
    NullableCol                         timestamp,
    TimestampPrecisionCol               timestamp(4)
)
/

create table &main_user..TestTimestampLTZs (
    IntCol                              number(9) not null,
    TimestampLTZCol                     timestamp with local time zone not null,
    NullableCol                         timestamp with local time zone,
    TimestampLTZPrecisionCol            timestamp(5) with local time zone
)
/

create table &main_user..TestTimestampTZs (
    IntCol                              number(9) not null,
    TimestampTZCol                      timestamp with time zone not null,
    NullableCol                         timestamp with time zone,
    TimestampTZPrecisionCol             timestamp(7) with time zone
)
/

create table &main_user..TestIntervals (
    IntCol                              number(9) not null,
    IntervalCol                         interval day to second not null,
    NullableCol                         interval day to second,
    IntervalPrecisionCol                interval day(7) to second,
    IntervalPrecisionScaleCol           interval day(8) to second(9)
)
/

create table &main_user..TestIntervalYMs (
    IntCol                              number(9) not null,
    IntervalCol                         interval year to month not null,
    NullableCol                         interval year to month,
    IntervalPrecisionCol                interval year(3) to month
)
/

create table &main_user..TestUniversalRowids (
    IntCol                              number(9) not null,
    StringCol                           varchar2(250) not null,
    DateCol                             date not null,
    constraint TestUniversalRowids_pk primary key (IntCol, StringCol, DateCol)
) organization index
/

create table &main_user..TestBuildings (
    BuildingId                          number(9) not null,
    BuildingObj                         &main_user..udt_Building not null
)
/

create table &main_user..TestRowids (
    IntCol                              number(9) not null,
    RowidCol                            rowid,
    URowidCol                           urowid
)
/

create table &main_user..TestJsonCols (
    IntCol                              number(9) not null,
    JsonVarchar                         varchar2(4000) not null,
    JsonClob                            clob not null,
    JsonBlob                            blob not null,
    constraint TestJsonCols_ck_1 check (JsonVarchar is json format json),
    constraint TestJsonCols_ck_2 check (JsonClob is json format json),
    constraint TestJsonCols_ck_3 check (JsonBlob is json format json)
)
/

create table &main_user..TestAllTypes (
    NumberValue                         number,
    StringValue                         varchar2(60),
    FixedCharValue                      char(10),
    NStringValue                        nvarchar2(60),
    NFixedCharValue                     nchar(10),
    RawValue                            raw(16),
    IntValue                            integer,
    SmallIntValue                       smallint,
    RealValue                           real,
    DoublePrecisionValue                double precision,
    FloatValue                          float,
    BinaryFloatValue                    binary_float,
    BinaryDoubleValue                   binary_double,
    DateValue                           date,
    TimestampValue                      timestamp,
    TimestampTZValue                    timestamp with time zone,
    TimestampLTZValue                   timestamp with local time zone,
    CLOBValue                           clob,
    NCLOBValue                          nclob,
    BLOBValue                           blob,
    SubObjectValue                      &main_user..udt_SubObject,
    SubObjectArray                      &main_user..udt_ObjectArray,
    InvisibleValue                      number invisible
)
/

create table &main_user..PlsqlSessionCallbacks (
    RequestedTag          varchar2(250),
    ActualTag             varchar2(250),
    FixupTimestamp        timestamp
)
/

create table &main_user..TestDataframe (
    Id                                  number(9),
    FirstName                           varchar2(100),
    LastName                            varchar2(100),
    City                                varchar2(100),
    Country                             varchar2(100),
    DateOfBirth                         date,
    Salary                              number(9, 2),
    CreditScore                         number(3, 0),
    LastUpdated                         timestamp
)
/

-- create queue table and queues for testing advanced queuing
begin

    dbms_aqadm.create_queue_table('&main_user..BOOK_QUEUE_TAB',
            '&main_user..UDT_BOOK');
    dbms_aqadm.create_queue('&main_user..TEST_BOOK_QUEUE',
            '&main_user..BOOK_QUEUE_TAB');
    dbms_aqadm.start_queue('&main_user..TEST_BOOK_QUEUE');

    dbms_aqadm.create_queue_table('&main_user..RAW_QUEUE_TAB', 'RAW');
    dbms_aqadm.create_queue('&main_user..TEST_RAW_QUEUE',
            '&main_user..RAW_QUEUE_TAB');
    dbms_aqadm.start_queue('&main_user..TEST_RAW_QUEUE');

    dbms_aqadm.create_queue_table('&main_user..BOOK_QUEUE_MULTI_TAB',
            '&main_user..UDT_BOOK', multiple_consumers => TRUE);
    dbms_aqadm.create_queue('&main_user..BOOK_QUEUE_MULTI',
            '&main_user..BOOK_QUEUE_MULTI_TAB');
    dbms_aqadm.start_queue('&main_user..BOOK_QUEUE_MULTI');
    dbms_aqadm.add_subscriber('&main_user..BOOK_QUEUE_MULTI',
            sys.aq$_agent('Sub1', null, null));

end;
/

-- create transformations
begin
    dbms_transform.create_transformation('&main_user', 'transform1',
            '&main_user', 'UDT_BOOK', '&main_user', 'UDT_BOOK',
            '&main_user..UDT_BOOK(source.user_data.TITLE, ' ||
                    'source.user_data.AUTHORS, source.user_data.PRICE + 5)');
    dbms_transform.create_transformation('&main_user', 'transform2',
            '&main_user', 'UDT_BOOK', '&main_user', 'UDT_BOOK',
            '&main_user..UDT_BOOK(source.user_data.TITLE, ' ||
                    'source.user_data.AUTHORS, source.user_data.PRICE + 10)');
end;
/

-- populate tables
begin
    for i in 1..10 loop
        insert into &main_user..TestNumbers
        values (i, power(38, i), i + i * 0.25, i + i * .75, i * i * i + i *.5,
                decode(mod(i, 2), 0, null, power(143, i)));
    end loop;
end;
/

declare

    t_RawValue                          raw(30);

    function ConvertHexDigit(a_Value number) return varchar2 is
    begin
        if a_Value between 0 and 9 then
            return to_char(a_Value);
        end if;
        return chr(ascii('A') + a_Value - 10);
    end;

    function ConvertToHex(a_Value varchar2) return varchar2 is
        t_HexValue                      varchar2(60);
        t_Digit                         number;
    begin
        for i in 1..length(a_Value) loop
            t_Digit := ascii(substr(a_Value, i, 1));
            t_HexValue := t_HexValue ||
                    ConvertHexDigit(trunc(t_Digit / 16)) ||
                    ConvertHexDigit(mod(t_Digit, 16));
        end loop;
        return t_HexValue;
    end;

begin
    for i in 1..10 loop
        t_RawValue := hextoraw(ConvertToHex('Raw ' || to_char(i)));
        insert into &main_user..TestStrings
        values (i, 'String ' || to_char(i), t_RawValue,
                'Fixed Char ' || to_char(i),
                decode(mod(i, 2), 0, null, 'Nullable ' || to_char(i)));
    end loop;
end;
/

begin
    for i in 1..10 loop
        insert into &main_user..TestUnicodes
        values (i, 'Unicode ' || unistr('\3042') || ' ' || to_char(i),
                'Fixed Unicode ' || to_char(i),
                decode(mod(i, 2), 0, null, unistr('Nullable ') || to_char(i)));
    end loop;
end;
/

begin
    for i in 1..10 loop
        insert into &main_user..TestDates
        values (i, to_date(20021209, 'YYYYMMDD') + i + i * .1,
                decode(mod(i, 2), 0, null,
                to_date(20021209, 'YYYYMMDD') + i + i + i * .15));
    end loop;
end;
/

begin
    for i in 1..100 loop
        insert into &main_user..TestXML
        values (i, '<?xml version="1.0"?><records>' ||
                dbms_random.string('x', 1024) || '</records>');
    end loop;
end;
/

begin
    for i in 1..10 loop
        insert into &main_user..TestTimestamps
        values (i, to_timestamp('20021209', 'YYYYMMDD') +
                    to_dsinterval(to_char(i) || ' 00:00:' || to_char(i * 2) ||
                    '.' || to_char(i * 50)),
                decode(mod(i, 2), 0, to_timestamp(null, 'YYYYMMDD'),
                to_timestamp('20021209', 'YYYYMMDD') +
                    to_dsinterval(to_char(i + 1) || ' 00:00:' ||
                    to_char(i * 3) || '.' || to_char(i * 125))),
                to_timestamp('20091214', 'YYYYMMDD'));
    end loop;
end;
/

begin
    for i in 1..10 loop
        insert into &main_user..TestTimestampLTZs
        values (i, to_timestamp_tz('20220602 ' ||
                    decode(mod(i, 2), 0, '-', '+') ||
                    ltrim(to_char(i, '00')) || ':' ||
                    decode(mod(i, 4), 0, '00', '30'), 'YYYYMMDD TZH:TZM') +
                    to_dsinterval(to_char(i) || ' 00:00:' || to_char(i * 2) ||
                    '.' || to_char(i * 50)),
                decode(mod(i, 2), 0, to_timestamp(null, 'YYYYMMDD'),
                to_timestamp_tz('20220602 00:00', 'YYYYMMDD TZH:TZM') +
                    to_dsinterval(to_char(i + 1) || ' 00:00:' ||
                    to_char(i * 3) || '.' || to_char(i * 125))),
                to_timestamp_tz('20091214 00:00', 'YYYYMMDD TZH:TZM'));
    end loop;
end;
/

begin
    for i in 1..10 loop
        insert into &main_user..TestTimestampTZs
        values (i, to_timestamp_tz('20220603 ' ||
                    decode(mod(i, 2), 0, '-', '+') ||
                    ltrim(to_char(i, '00')) || ':' ||
                    decode(mod(i, 4), 0, '00', '30'), 'YYYYMMDD TZH:TZM') +
                    to_dsinterval(to_char(i) || ' 00:00:' || to_char(i * 2) ||
                    '.' || to_char(i * 50)),
                decode(mod(i, 2), 0, to_timestamp(null, 'YYYYMMDD'),
                to_timestamp_tz('20220603 00:00', 'YYYYMMDD TZH:TZM') +
                    to_dsinterval(to_char(i + 1) || ' 00:00:' ||
                    to_char(i * 3) || '.' || to_char(i * 125))),
                to_timestamp_tz('20091214 00:00', 'YYYYMMDD TZH:TZM'));
    end loop;
end;
/

begin
    for i in 1..10 loop
        insert into &main_user..TestIntervals
        values (i, to_dsinterval(to_char(i) || ' ' || to_char(i) || ':' ||
                to_char(i * 2) || ':' || to_char(i * 3)),
                decode(mod(i, 2), 0, to_dsinterval(null),
                to_dsinterval(to_char(i + 5) || ' ' || to_char(i + 2) || ':' ||
                to_char(i * 2 + 5) || ':' || to_char(i * 3 + 5))),
                to_dsinterval('8 05:15:00'),
                to_dsinterval('10 12:15:15'));
    end loop;
end;
/

begin
    for i in 1..10 loop
        insert into &main_user..TestIntervalYMs
        values (i, to_yminterval(to_char(i - 5) || '-' || to_char(i)),
                decode(mod(i, 2), 0, to_yminterval(null),
                to_yminterval(to_char(i + 5) || '-' || to_char(i + 2))),
                to_yminterval('3-8'));
    end loop;
end;
/

insert into &main_user..TestObjects values (1,
    &main_user..udt_Object(1, 'First row', 'First', 'N First Row', 'N First',
        '52617720446174612031', 2, 5, 12.125, 0.5, 12.5, 25.25, 50.125,
        to_date(20070306, 'YYYYMMDD'),
        to_timestamp('20080912 16:40:00', 'YYYYMMDD HH24:MI:SS'),
        to_timestamp_tz('20091013 17:50:00 00:00',
                'YYYYMMDD HH24:MI:SS TZH:TZM'),
        to_timestamp_tz('20101114 18:55:00 00:00',
                'YYYYMMDD HH24:MI:SS TZH:TZM'),
        'Short CLOB value', 'Short NCLOB Value',
        utl_raw.cast_to_raw('Short BLOB value'),
        &main_user..udt_SubObject(11, 'Sub object 1'),
        &main_user..udt_ObjectArray(
                &main_user..udt_SubObject(5, 'first element'),
                &main_user..udt_SubObject(6, 'second element'))),
    &main_user..udt_Array(5, 10, null, 20))
/

insert into &main_user..TestObjects values (2, null,
    &main_user..udt_Array(3, null, 9, 12, 15))
/

insert into &main_user..TestObjects values (3,
    &main_user..udt_Object(3, 'Third row', 'Third', 'N Third Row', 'N Third',
        '52617720446174612033', 4, 10, 6.5, 0.75, 43.25, 86.5, 192.125,
        to_date(20070621, 'YYYYMMDD'),
        to_timestamp('20071213 07:30:45', 'YYYYMMDD HH24:MI:SS'),
        to_timestamp_tz('20170621 23:18:45 00:00',
                'YYYYMMDD HH24:MI:SS TZH:TZM'),
        to_timestamp_tz('20170721 08:27:13 00:00',
                'YYYYMMDD HH24:MI:SS TZH:TZM'),
        'Another short CLOB value', 'Another short NCLOB Value',
        utl_raw.cast_to_raw('Yet another short BLOB value'),
        &main_user..udt_SubObject(13, 'Sub object 3'),
        &main_user..udt_ObjectArray(
                &main_user..udt_SubObject(10, 'element #1'),
                &main_user..udt_SubObject(20, 'element #2'),
                &main_user..udt_SubObject(30, 'element #3'),
                &main_user..udt_SubObject(40, 'element #4'))), null)
/

insert into &main_user..TestJsonCols values (1,
    '[1, 2, 3]', '[4, 5, 6]', utl_raw.cast_to_raw('[7, 8, 9]'))
/

insert into &main_user..TestJsonCols values (2,
    'null', empty_clob(), empty_blob())
/

commit
/

-- create procedures for testing callproc()
create procedure &main_user..proc_Test (
    a_InValue                           varchar2,
    a_InOutValue                        in out number,
    a_OutValue                          out number
) as
begin
    a_InOutValue := a_InOutValue * length(a_InValue);
    a_OutValue := length(a_InValue);
end;
/

create procedure &main_user..proc_Test2 (
    a_InValue                           varchar2,
    a_InOutValue                        in out number,
    a_OutValue                          out boolean
) as
begin
    a_InOutValue := a_InOutValue * length(a_InValue);
    a_OutValue := false;
    if length(a_InValue) >= 2 then
        a_OutValue := true;
    end if;
end;
/

create procedure &main_user..proc_TestNoArgs as
begin
    null;
end;
/

-- create procedure for testing refcursor
create procedure &main_user..myrefcursorproc (
    a_RefCursor                         out sys_refcursor
) as
begin
    open a_RefCursor for
        select *
        from TestTempTable;
end;
/

-- create functions for testing callfunc()
create function &main_user..func_Test (
    a_String                            varchar2,
    a_ExtraAmount                       number
) return number as
begin
    return length(a_String) + a_ExtraAmount;
end;
/

create function &main_user..func_Test2 (
    a_String                            varchar2,
    a_ExtraAmount                       number,
    a_Boolean                           boolean
) return number as
begin
    if a_Boolean then
        return length(a_String) + a_ExtraAmount;
    end if;
    return length(a_String) - a_ExtraAmount;
end;
/

create function &main_user..func_TestNoArgs
return number as
begin
    return 712;
end;
/

-- create packages
create or replace package &main_user..pkg_TestStringArrays as

    type udt_StringList is table of varchar2(100) index by binary_integer;

    function TestInArrays (
        a_StartingLength                number,
        a_Array                         udt_StringList
    ) return number;

    procedure TestInOutArrays (
        a_NumElems                      number,
        a_Array                         in out nocopy udt_StringList
    );

    procedure TestOutArrays (
        a_NumElems                      number,
        a_Array                         out nocopy udt_StringList
    );

    procedure TestIndexBy (
        a_Array                         out nocopy udt_StringList
    );

end;
/

create or replace package body &main_user..pkg_TestStringArrays as

    function TestInArrays (
        a_StartingLength                number,
        a_Array                         udt_StringList
    ) return number is
        t_Length                        number;
    begin
        t_Length := a_StartingLength;
        for i in 1..a_Array.count loop
            t_Length := t_Length + length(a_Array(i));
        end loop;
        return t_Length;
    end;

    procedure TestInOutArrays (
        a_NumElems                      number,
        a_Array                         in out udt_StringList
    ) is
    begin
        for i in 1..a_NumElems loop
            a_Array(i) := 'Converted element # ' ||
                    to_char(i) || ' originally had length ' ||
                    to_char(length(a_Array(i)));
        end loop;
    end;

    procedure TestOutArrays (
        a_NumElems                      number,
        a_Array                         out udt_StringList
    ) is
    begin
        for i in 1..a_NumElems loop
            a_Array(i) := 'Test out element # ' || to_char(i);
        end loop;
    end;

    procedure TestIndexBy (
        a_Array             out nocopy udt_StringList
    ) is
    begin
        a_Array(-1048576) := 'First element';
        a_Array(-576) := 'Second element';
        a_Array(284) := 'Third element';
        a_Array(8388608) := 'Fourth element';
    end;

end;
/

create or replace package &main_user..pkg_TestUnicodeArrays as

    type udt_UnicodeList is table of nvarchar2(100) index by binary_integer;

    function TestInArrays (
        a_StartingLength                number,
        a_Array                         udt_UnicodeList
    ) return number;

    procedure TestInOutArrays (
        a_NumElems                      number,
        a_Array                         in out nocopy udt_UnicodeList
    );

    procedure TestOutArrays (
        a_NumElems                      number,
        a_Array                         out nocopy udt_UnicodeList
    );

end;
/

create or replace package body &main_user..pkg_TestUnicodeArrays as

    function TestInArrays (
        a_StartingLength                number,
        a_Array                         udt_UnicodeList
    ) return number is
        t_Length                        number;
    begin
        t_Length := a_StartingLength;
        for i in 1..a_Array.count loop
            t_Length := t_Length + length(a_Array(i));
        end loop;
        return t_Length;
    end;

    procedure TestInOutArrays (
        a_NumElems                      number,
        a_Array                         in out udt_UnicodeList
    ) is
    begin
        for i in 1..a_NumElems loop
            a_Array(i) := unistr('Converted element ' || unistr('\3042') ||
                    ' # ') || to_char(i) || ' originally had length ' ||
                    to_char(length(a_Array(i)));
        end loop;
    end;

    procedure TestOutArrays (
        a_NumElems                      number,
        a_Array                         out udt_UnicodeList
    ) is
    begin
        for i in 1..a_NumElems loop
            a_Array(i) := unistr('Test out element ') || unistr('\3042') ||
                    ' # ' || to_char(i);
        end loop;
    end;

end;
/

create or replace package &main_user..pkg_TestNumberArrays as

    type udt_NumberList is table of number index by binary_integer;

    function TestInArrays (
        a_StartingValue                 number,
        a_Array                         udt_NumberList
    ) return number;

    procedure TestInOutArrays (
        a_NumElems                      number,
        a_Array                         in out nocopy udt_NumberList
    );

    procedure TestOutArrays (
        a_NumElems                      number,
        a_Array                         out nocopy udt_NumberList
    );

end;
/

create or replace package body &main_user..pkg_TestNumberArrays as

    function TestInArrays (
        a_StartingValue                 number,
        a_Array                         udt_NumberList
    ) return number is
        t_Value                         number;
    begin
        t_Value := a_StartingValue;
        for i in 1..a_Array.count loop
            t_Value := t_Value + a_Array(i);
        end loop;
        return t_Value;
    end;

    procedure TestInOutArrays (
        a_NumElems                      number,
        a_Array                         in out udt_NumberList
    ) is
    begin
        for i in 1..a_NumElems loop
            a_Array(i) := a_Array(i) * 10;
        end loop;
    end;

    procedure TestOutArrays (
        a_NumElems                      number,
        a_Array                         out udt_NumberList
    ) is
    begin
        for i in 1..a_NumElems loop
            a_Array(i) := i * 100;
        end loop;
    end;

end;
/

create or replace package &main_user..pkg_TestDateArrays as

    type udt_DateList is table of date index by binary_integer;

    function TestInArrays (
        a_StartingValue                 number,
        a_BaseDate                      date,
        a_Array                         udt_DateList
    ) return number;

    procedure TestInOutArrays (
        a_NumElems                      number,
        a_Array                         in out nocopy udt_DateList
    );

    procedure TestOutArrays (
        a_NumElems                      number,
        a_Array                         out nocopy udt_DateList
    );

end;
/

create or replace package body &main_user..pkg_TestDateArrays as

    function TestInArrays (
        a_StartingValue                 number,
        a_BaseDate                      date,
        a_Array                         udt_DateList
    ) return number is
        t_Value                         number;
    begin
        t_Value := a_StartingValue;
        for i in 1..a_Array.count loop
            t_Value := t_Value + a_Array(i) - a_BaseDate;
        end loop;
        return t_Value;
    end;

    procedure TestInOutArrays (
        a_NumElems                      number,
        a_Array                         in out udt_DateList
    ) is
    begin
        for i in 1..a_NumElems loop
            a_Array(i) := a_Array(i) + 7;
        end loop;
    end;

    procedure TestOutArrays (
        a_NumElems                      number,
        a_Array                         out udt_DateList
    ) is
    begin
        for i in 1..a_NumElems loop
            a_Array(i) := to_date(20021212, 'YYYYMMDD') + i * 1.2;
        end loop;
    end;

end;
/

create or replace package &main_user..pkg_TestRefCursors as

    procedure TestOutCursor (
        a_MaxIntValue                   number,
        a_Cursor                        out sys_refcursor
    );

    function TestInCursor (
        a_Cursor                        sys_refcursor
    ) return varchar2;

    function TestReturnCursor (
        a_MaxIntValue                   number
    ) return sys_refcursor;

    procedure TestLobCursor (
        a_Value                         varchar2,
        a_Cursor                        out sys_refcursor
    );

    procedure TestCloseCursor (
        a_Cursor                        sys_refcursor
    );

end;
/

create or replace package body &main_user..pkg_TestRefCursors as

    procedure TestOutCursor (
        a_MaxIntValue                   number,
        a_Cursor                        out sys_refcursor
    ) is
    begin
        open a_Cursor for
            select
                IntCol,
                StringCol
            from TestStrings
            where IntCol <= a_MaxIntValue
            order by IntCol;
    end;

    function TestInCursor (
        a_Cursor                        sys_refcursor
    ) return varchar2 is
        t_String                        varchar2(100);
    begin
        fetch a_Cursor into t_String;
        return t_String || ' (Modified)';
    end;

    function TestReturnCursor (
        a_MaxIntValue                   number
    ) return sys_refcursor is
        t_Cursor                        sys_refcursor;
    begin
        open t_Cursor for
            select
                IntCol,
                StringCol
            from TestSTrings
            where IntCol <= a_MaxIntValue
            order by IntCol;
        return t_Cursor;
    end;

    procedure TestLobCursor (
        a_Value                         varchar2,
        a_Cursor                        out sys_refcursor
    ) is
    begin
        open a_Cursor for
            select to_clob(a_Value)
            from dual;
    end;

    procedure TestCloseCursor (
        a_Cursor                        sys_refcursor
    ) is
        t_Id                            number;
        t_StrVal                        varchar2(400);
    begin
        delete from TestTempTable;
        fetch a_Cursor into t_Id, t_StrVal;
        if not a_Cursor%notfound then
            insert into TestTempTable (IntCol, StringCol1)
            values (t_Id, t_StrVal);
        end if;
        close a_Cursor;
        commit;
    end;

end;
/

create or replace package &main_user..pkg_TestBooleans as

    type udt_BooleanList is table of boolean index by binary_integer;

    function GetStringRep (
        a_Value                         boolean
    ) return varchar2;

    function IsLessThan10 (
        a_Value                         number
    ) return boolean;

    function TestInArrays (
        a_Value                         udt_BooleanList
    ) return number;

    function TestOutValueNull
    return boolean;

    procedure TestOutArrays (
        a_NumElements                   number,
        a_Value                         out nocopy udt_BooleanList
    );

end;
/

create or replace package body &main_user..pkg_TestBooleans as

    function GetStringRep (
        a_Value                         boolean
    ) return varchar2 is
    begin
        if a_Value is null then
            return 'NULL';
        elsif a_Value then
            return 'TRUE';
        end if;
        return 'FALSE';
    end;

    function IsLessThan10 (
        a_Value                         number
    ) return boolean is
    begin
        return a_Value < 10;
    end;

    function TestInArrays (
        a_Value                         udt_BooleanList
    ) return number is
        t_Result                        pls_integer;
    begin
        t_Result := 0;
        for i in 1..a_Value.count loop
            if a_Value(i) then
                t_Result := t_Result + 1;
            end if;
        end loop;
        return t_Result;
    end;

    function TestOutValueNull
    return boolean is
    begin
        return null;
    end;

    procedure TestOutArrays (
        a_NumElements                   number,
        a_Value                         out nocopy udt_BooleanList
    ) is
    begin
        for i in 1..a_NumElements loop
            a_Value(i) := (mod(i, 2) = 1);
        end loop;
    end;

end;
/

create or replace package &main_user..pkg_TestBindObject as

    subtype udt_RowType is TestTempTable%rowtype;

    type udt_CollectionRowType is table of udt_RowType index by binary_integer;

    function GetStringRep (
        a_Object                        udt_Object
    ) return varchar2;

    procedure BindObjectOut (
        a_NumberValue                   number,
        a_StringValue                   varchar2,
        a_Object                        out nocopy udt_Object
    );

end;
/

create or replace package body &main_user..pkg_TestBindObject as

    function GetStringRep (
        a_Object                        udt_SubObject
    ) return varchar2 is
    begin
        if a_Object is null then
            return 'null';
        end if;
        return 'udt_SubObject(' ||
                nvl(to_char(a_Object.SubNumberValue), 'null') || ', ' ||
                case when a_Object.SubStringValue is null then 'null'
                else '''' || a_Object.SubStringValue || '''' end || ')';
    end;

    function GetStringRep (
        a_Array         udt_ObjectArray
    ) return varchar2 is
        t_StringRep     varchar2(4000);
    begin
        if a_Array is null then
            return 'null';
        end if;
        t_StringRep := 'udt_ObjectArray(';
        for i in 1..a_Array.count loop
            if i > 1 then
                t_StringRep := t_StringRep || ', ';
            end if;
            t_StringRep := t_StringRep || GetStringRep(a_Array(i));
        end loop;
        return t_StringRep || ')';
    end;

    function GetStringRep (
        a_Object        udt_Object
    ) return varchar2 is
    begin
        if a_Object is null then
            return 'null';
        end if;
        return 'udt_Object(' ||
                nvl(to_char(a_Object.NumberValue), 'null') || ', ' ||
                case when a_Object.StringValue is null then 'null'
                else '''' || a_Object.StringValue || '''' end || ', ' ||
                case when a_Object.FixedCharValue is null then 'null'
                else '''' || a_Object.FixedCharValue || '''' end || ', ' ||
                case when a_Object.DateValue is null then 'null'
                else 'to_date(''' ||
                        to_char(a_Object.DateValue, 'YYYY-MM-DD') ||
                        ''', ''YYYY-MM-DD'')' end || ', ' ||
                case when a_Object.TimestampValue is null then 'null'
                else 'to_timestamp(''' || to_char(a_Object.TimestampValue,
                        'YYYY-MM-DD HH24:MI:SS') ||
                        ''', ''YYYY-MM-DD HH24:MI:SS'')' end || ', ' ||
                GetStringRep(a_Object.SubObjectValue) || ', ' ||
                GetStringRep(a_Object.SubObjectArray) || ')';
    end;

    procedure BindObjectOut (
        a_NumberValue                   number,
        a_StringValue                   varchar2,
        a_Object                        out nocopy udt_Object
    ) is
    begin
        a_Object := udt_Object(a_NumberValue, a_StringValue, null, null, null,
                null, null, null, null, null, null, null, null, null, null,
                null, null, null, null, null, null, null);
    end;

end;
/

create or replace package &main_user..pkg_TestRecords as

    type udt_Record is record (
        NumberValue                     number,
        StringValue                     varchar2(30),
        DateValue                       date,
        TimestampValue                  timestamp,
        BooleanValue                    boolean,
        PlsIntegerValue                 pls_integer,
        BinaryIntegerValue              binary_integer
    );

    type udt_RecordArray is table of udt_Record index by binary_integer;

    function GetStringRep (
        a_Value                         udt_Record
    ) return varchar2;

    procedure TestOut (
        a_Value                         out nocopy udt_Record
    );

    function TestInArrays (
        a_Value                         udt_RecordArray
    ) return varchar2;

end;
/

create or replace package body &main_user..pkg_TestRecords as

    function GetStringRep (
        a_Value                         udt_Record
    ) return varchar2 is
    begin
        return 'udt_Record(' ||
                nvl(to_char(a_Value.NumberValue), 'null') || ', ' ||
                case when a_Value.StringValue is null then 'null'
                else '''' || a_Value.StringValue || '''' end || ', ' ||
                case when a_Value.DateValue is null then 'null'
                else 'to_date(''' ||
                        to_char(a_Value.DateValue, 'YYYY-MM-DD') ||
                        ''', ''YYYY-MM-DD'')' end || ', ' ||
                case when a_Value.TimestampValue is null then 'null'
                else 'to_timestamp(''' || to_char(a_Value.TimestampValue,
                        'YYYY-MM-DD HH24:MI:SS') ||
                        ''', ''YYYY-MM-DD HH24:MI:SS'')' end || ', ' ||
                case when a_Value.BooleanValue is null then 'null'
                when a_Value.BooleanValue then 'true'
                else 'false' end || ', ' ||
                nvl(to_char(a_Value.PlsIntegerValue), 'null') || ', ' ||
                nvl(to_char(a_Value.BinaryIntegerValue), 'null') || ')';
    end;

    procedure TestOut (
        a_Value                         out nocopy udt_Record
    ) is
    begin
        a_Value.NumberValue := 25;
        a_Value.StringValue := 'String in record';
        a_Value.DateValue := to_date(20160216, 'YYYYMMDD');
        a_Value.TimestampValue := to_timestamp('20160216 18:23:55',
                'YYYYMMDD HH24:MI:SS');
        a_Value.BooleanValue := true;
        a_Value.PlsIntegerValue := 45;
        a_Value.BinaryIntegerValue := 10;
    end;

    function TestInArrays (
        a_Value             udt_RecordArray
    ) return varchar2 is
        t_Result            varchar2(4000);
    begin
        for i in 0..a_Value.count - 1 loop
            if t_Result is not null then
                t_Result := t_Result || '; ';
            end if;
            t_Result := t_Result || GetStringRep(a_Value(i));
        end loop;
        return t_Result;
    end;

end;
/

create or replace package &main_user..pkg_TestNestedRecords as

    type udt_Inner is record (
        Attr1                           number,
        Attr2                           number
    );

    type udt_Outer is record (
        Inner1                          udt_Inner,
        Inner2                          udt_Inner
    );

    function GetOuter (
        a_Value1                        number,
        a_Value2                        number
    ) return udt_Outer;

end;
/

create or replace package body &main_user..pkg_TestNestedRecords as

    function GetOuter (
        a_Value1                        number,
        a_Value2                        number
    ) return udt_Outer is
        t_Outer                         udt_Outer;
    begin
        t_Outer.Inner1.Attr2 := a_Value1;
        t_Outer.Inner2.Attr2 := a_Value2;
        return t_Outer;
    end;

end;
/

create or replace package &main_user..pkg_SessionCallback as

    procedure TheCallback (
        a_RequestedTag                  varchar2,
        a_ActualTag                     varchar2
    );

end;
/

create or replace package body &main_user..pkg_SessionCallback as

    type udt_Properties is table of varchar2(64) index by varchar2(64);

    procedure LogCall (
        a_RequestedTag                  varchar2,
        a_ActualTag                     varchar2
    ) is
        pragma autonomous_transaction;
    begin
        insert into PlsqlSessionCallbacks
        values (a_RequestedTag, a_ActualTag, systimestamp);
        commit;
    end;

    procedure ParseProperty (
        a_Property                      varchar2,
        a_Name                          out nocopy varchar2,
        a_Value                         out nocopy varchar2
    ) is
        t_Pos                           number;
    begin
        t_Pos := instr(a_Property, '=');
        if t_Pos = 0 then
            raise_application_error(-20000, 'Tag must contain key=value pairs');
        end if;
        a_Name := substr(a_Property, 1, t_Pos - 1);
        a_Value := substr(a_Property, t_Pos + 1);
    end;

    procedure SetProperty (
        a_Name                          varchar2,
        a_Value                         varchar2
    ) is
        t_ValidValues                   udt_Properties;
    begin
        if a_Name = 'TIME_ZONE' then
            t_ValidValues('UTC') := 'UTC';
            t_ValidValues('MST') := '-07:00';
        elsif a_Name = 'NLS_DATE_FORMAT' then
            t_ValidValues('SIMPLE') := 'YYYY-MM-DD HH24:MI';
            t_ValidValues('FULL') := 'YYYY-MM-DD HH24:MI:SS';
        else
            raise_application_error(-20000, 'Unsupported session setting');
        end if;
        if not t_ValidValues.exists(a_Value) then
            raise_application_error(-20000, 'Unsupported session setting');
        end if;
        execute immediate
                'ALTER SESSION SET ' || a_Name || '=''' ||
                t_ValidValues(a_Value) || '''';
    end;

    procedure ParseTag (
        a_Tag                           varchar2,
        a_Properties                    out nocopy udt_Properties
    ) is
        t_PropertyName                  varchar2(64);
        t_PropertyValue                 varchar2(64);
        t_StartPos                      number;
        t_EndPos                        number;
    begin
        t_StartPos := 1;
        while t_StartPos < length(a_Tag) loop
            t_EndPos := instr(a_Tag, ';', t_StartPos);
            if t_EndPos = 0 then
                t_EndPos := length(a_Tag) + 1;
            end if;
            ParseProperty(substr(a_Tag, t_StartPos, t_EndPos - t_StartPos),
                    t_PropertyName, t_PropertyValue);
            a_Properties(t_PropertyName) := t_PropertyValue;
            t_StartPos := t_EndPos + 1;
        end loop;
    end;

    procedure TheCallback (
        a_RequestedTag                  varchar2,
        a_ActualTag                     varchar2
    ) is
        t_RequestedProps                udt_Properties;
        t_ActualProps                   udt_Properties;
        t_PropertyName                  varchar2(64);
    begin
        LogCall(a_RequestedTag, a_ActualTag);
        ParseTag(a_RequestedTag, t_RequestedProps);
        ParseTag(a_ActualTag, t_ActualProps);
        t_PropertyName := t_RequestedProps.first;
        while t_PropertyName is not null loop
            if not t_ActualProps.exists(t_PropertyName) or
                    t_ActualProps(t_PropertyName) !=
                    t_RequestedProps(t_PropertyName) then
                SetProperty(t_PropertyName, t_RequestedProps(t_PropertyName));
            end if;
            t_PropertyName := t_RequestedProps.next(t_PropertyName);
        end loop;
    end;

end;
/

create or replace package &main_user..pkg_TestLOBs as

    procedure GetSize(
        a_BLOB                          blob,
        a_Size                          out number
    );

    procedure GetSize(
        a_CLOB                          clob,
        a_Size                          out number
    );

    procedure TestInOut (
        a_CLOB                          in out clob,
        a_SearchValue                   varchar2,
        a_ReplaceValue                  varchar2
    );

end;
/

create or replace package body &main_user..pkg_TestLOBs as

    procedure GetSize(
        a_BLOB                          blob,
        a_Size                          out number
    ) is
    begin
        a_Size := dbms_lob.getlength(a_BLOB);
    end;

    procedure GetSize(
        a_CLOB                          clob,
        a_Size                          out number
    ) is
    begin
        a_Size := dbms_lob.getlength(a_CLOB);
    end;

    procedure TestInOut (
        a_CLOB                          in out clob,
        a_SearchValue                   varchar2,
        a_ReplaceValue                  varchar2
    ) is
    begin
        if a_SearchValue is not null then
            a_CLOB := replace(a_CLOB, a_SearchValue, a_ReplaceValue);
        end if;
    end;

end;
/
