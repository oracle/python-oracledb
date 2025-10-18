.. _globalization:

.. currentmodule:: oracledb

********************************
Character Sets and Globalization
********************************

Character Sets
==============

Database Character Set
----------------------

Data fetched from and sent to Oracle Database will be mapped between the
`database character set <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-EA913CC8-C5BA-4FB3-A1B8-882734AF4F43>`__ and the "Oracle client"
character set of the Oracle Client libraries used by python-oracledb. If data
cannot be correctly mapped between client and server character sets, then it
may be corrupted or queries may fail with
:ref:`"codec can't decode byte" <codecerror>`.

All database character sets are supported by python-oracledb.

.. _findingcharset:

To find the database character set, execute the query:

.. code-block:: sql

    SELECT value AS db_charset
    FROM nls_database_parameters
    WHERE parameter = 'NLS_CHARACTERSET';

Database National Character Set
-------------------------------

For the secondary `national character set <https://www.oracle.com/pls/topic/
lookup?ctx=dblatest&id=GUID-4E12D991-C286-4F1A-AFC6-F35040A5DE4F>`__ used for
NCHAR, NVARCHAR2, and NCLOB data types:

- AL16UTF16 is supported by both python-oracledb Thin and Thick modes
- UTF8 is not supported by python-oracledb Thin mode

To find the database's national character set, execute the query:

.. code-block:: sql

     SELECT value AS db_ncharset
     FROM nls_database_parameters
     WHERE parameter = 'NLS_NCHAR_CHARACTERSET';

Setting the Client Character Set
--------------------------------

In python-oracledb, the encoding used for all character data is "UTF-8".  Older
versions of the driver allowed ``encoding`` and ``nencoding`` parameters to be
passed to the :meth:`oracledb.connect` and :meth:`oracledb.create_pool` methods
but these parameters are now desupported.

.. _timezonefiles:

Time Zone Files
===============

This section applies to python-oracledb Thick mode.

Oracle Client libraries and the Oracle Database use time zone files for date
operations. The files are versioned, but do not always have to be the same
version on the database and client. However, if you use the TIMESTAMP WITH
TIMEZONE data type and have a named time zone, you will get the error `ORA-1805
<https://docs.oracle.com/en/error-help/db/ora-01805/>`__ when the database and
the client time zone file versions differ.

Finding the Time Zone Files in Use
----------------------------------

You can find the time zone file used by the database itself by executing a
query, for example:

.. code-block:: sql

    SQL> select * from v$timezone_file;

    FILENAME                VERSION     CON_ID
    -------------------- ---------- ----------
    timezlrg_43.dat              43          0


The time zone files on the client side can be shown by running the utility
``genezi -v``.  In Instant Client, this is in the Basic and Basic Light
packages.  The output will be like::

    $ genezi -v

    . . .

    TIMEZONE INFORMATION
    --------------------
    Operating in Instant Client mode.

    Small timezone file = /opt/oracle/instantclient/oracore/zoneinfo/timezone_43.dat
    Large timezone file = /opt/oracle/instantclient/oracore/zoneinfo/timezlrg_43.dat

With Instant Client, the paths refer to a virtual file system in the Oracle
libraries. These files are not present on the operating system file system.

The larger file ``timezlrg_<n>.dat`` contains all time zone information. This
is the file used by default.  The smaller ``timezone_<n>.dat`` file contains
only the most commonly used time zones.

The filenames shows the version of the time zone files, in this example it is
version 43.

The Oracle Database documentation contains more information about time zone
files, see `Choosing a Time Zone File <https://www.oracle.com/pls/topic/
lookup?ctx=dblatest&id=GUID-805AB986-DE12-4FEA-AF56-5AABCD2132DF>`__.

Changing the Oracle Database Time Zone File
-------------------------------------------

To control the database time zone file in on-premise databases, use the
`DBMS_DST <https://www.oracle.com/pls/topic/lookup?ctx=
dblatest&id=GUID-55300506-481A-4957-A67D-0183D3D986DF>`__ package.

For Oracle Autonomous Database, use ``AUTO_DST_UPGRADE`` and
``AUTO_DST_UPGRADE_EXCL_DATA`` as shown in the documentation `Manage Time Zone
File Updates on Autonomous AI Database <https://www.oracle.com/pls/topic/
lookup?ctx=dblatest&id=GUID-BACC9C4A-C0FA-4912-862A-1A2A24D6A0C2>`__.

Changing the Oracle Client Time Zone File
-----------------------------------------

You can get updated time zone files from a full Oracle Database installation,
or by downloading a patch from `Oracle Support <https://support.oracle.com/>`_.
For use with Instant Client, unzip the patch and copy the necessary files:
installing the patch itself will not work.

**Using a New Time Zone File in Instant Client**

From Oracle Instant Client 12.2, you can use an external time zone file,
allowing you to update time zone information without updating the complete
Instant Client installation.  Changing the file in earlier versions of Instant
Client is not possible.

To change the time zone file, do one of the following:

- Create a subdirectory ``oracore/zoneinfo`` under the Instant Client
  directory and move the file into it.  Then set ``ORA_TZFILE`` to the file
  name, without any absolute or relative directory prefix prefix.  For
  example, if Instant Client is in ``/opt/oracle/instantclient``::

    mkdir -p /opt/oracle/instantclient/oracore/zoneinfo
    cp timezone_43.dat /opt/oracle/instantclient/oracore/zoneinfo/
    export ORA_TZFILE=timezone_43.dat

- Alternatively, from Oracle Instant Client 19.18, you can place the external
  time zone file in any directory and then set the ``ORA_TZFILE`` environment
  variable to the absolute path of the file. For example::

    mkdir -p /opt/oracle/myconfig
    cp timezone_43.dat /opt/oracle/myconfig/
    export ORA_TZFILE=/opt/oracle/myconfig/timezone_43.dat

After installing a new client time zone file, run ``genezi -v`` again to check
if it is readable.

**Using the Embedded Small Time Zone File in Instant Client**

By default, Instant Client uses its larger embedded ``timezlrg_<n>.dat`` file.
If you want to use the smaller embedded ``timezone_<n>.dat`` file, then set the
``ORA_TZFILE`` environment variable to the name of the file without any
absolute or relative directory prefix. For example::

    export ORA_TZFILE=timezone_43.dat

**Using a New Time Zone File in a Full Oracle Client**

If python-oracledb Thick mode is using Oracle Client libraries from a full
Oracle Client software installation (such as installed with Oracle's GUI
installer), and you want to use a non-default time zone file, then set
``ORA_TZFILE`` to the file name with an absolute path directory prefix. For
example::

    export ORA_TZFILE=/opt/oracle/myconfig/timezone_43.dat

This also works if python-oracledb Thick mode is using libraries from an Oracle
Database installation.

Setting the Client Locale
=========================

Thick Mode Oracle Database National Language Support (NLS)
----------------------------------------------------------

The python-oracledb Thick mode uses Oracle Database's National Language Support
(NLS) functionality to assist in globalizing applications, for example to
convert numbers and dates to strings in the locale specific format.

You can use the ``NLS_LANG`` environment variable to set the language and
territory used by the Oracle Client libraries.  For example, on Linux you could
set::

    export NLS_LANG=JAPANESE_JAPAN

The language ("JAPANESE" in this example) specifies conventions such as the
language used for Oracle Database messages, sorting, day names, and month
names.  The territory ("JAPAN") specifies conventions such as the default date,
monetary, and numeric formats. If the language is not specified, then the value
defaults to AMERICAN.  If the territory is not specified, then the value is
derived from the language value.  See `Choosing a Locale with the NLS_LANG
Environment Variable <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-86A29834-AE29-4BA5-8A78-E19C168B690A>`__.

If the ``NLS_LANG`` environment variable is set in the application with
``os.environ['NLS_LANG']``, it must be set before any connection pool is
created, or before any standalone connections are created.

Any client character set value in the ``NLS_LANG`` variable, for example
``JAPANESE_JAPAN.JA16SJIS``, is ignored by python-oracledb.  See `Setting the
Client Character Set`_.

Other Oracle globalization variables, such as ``NLS_DATE_FORMAT`` can also be
set to change the behavior of python-oracledb Thick, see `Setting NLS
Parameters <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-
6475CA50-6476-4559-AD87-35D431276B20>`__.

For more information, see the `Database Globalization Support Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=NLSPG>`__.

.. _thindatenumber:

Thin Mode Locale-aware Number and Date Conversions
--------------------------------------------------

.. note::

    All NLS environment variables are ignored by python-oracledb Thin mode.
    Also the ``ORA_TZFILE`` variable is ignored.

.. note::

    Trying to access TIMESTAMP WITH TIME ZONE data that contains a named time
    zone will throw ``DPY-3022: named time zones are not supported in thin
    mode``.  Data stored with a numeric offset such as ``+00:00`` can be
    fetched.

In python-oracledb Thin mode, output type handlers need to be used to perform
date and number localizations. The examples below show a simple conversion and
also how the Python locale module can be used.  Type handlers like those below
can also be used in python-oracledb Thick mode.

To convert numbers:

.. code-block:: python

    import locale
    import oracledb

    # use this if the environment variable LANG is already set
    #locale.setlocale(locale.LC_ALL, '')

    # use this for programmatic setting of locale
    locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')

    # simple naive conversion
    def type_handler1(cursor, metadata):
        if metadata.type_code is oracledb.DB_TYPE_NUMBER:
            return cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=cursor.arraysize,
                              outconverter=lambda v: v.replace('.', ','))

    # locale conversion
    def type_handler2(cursor, metadata):
        if metadata.type_code is oracledb.DB_TYPE_NUMBER:
            return cursor.var(metadata.type_code, arraysize=cursor.arraysize,
                              outconverter=lambda v: locale.format_string("%g", v))


    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb")

    with connection.cursor() as cursor:

        print("no type handler...")
        cursor.execute("select 2.5 from dual")
        for row in cursor:
            print(row)       # gives 2.5
        print()

        print("with naive type handler...")
        connection.outputtypehandler = type_handler1
        cursor.execute("select 2.5 from dual")
        for row in cursor:
            print(row)       # gives '2,5'
        print()

        print("with locale type handler...")
        connection.outputtypehandler = type_handler2
        cursor.execute("select 2.5 from dual")
        for row in cursor:
            print(row)       # gives '2,5'
        print()


To convert dates:

.. code-block:: python

    import locale
    import oracledb

    # use this if the environment variable LANG is already set
    #locale.setlocale(locale.LC_ALL, '')

    # use this for programmatic setting of locale
    locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
    locale_date_format = locale.nl_langinfo(locale.D_T_FMT)

    # simple naive conversion
    def type_handler3(cursor, metadata):
        if metadata.type_code is oracledb.DB_TYPE_DATE:
            return cursor.var(metadata.type_code, arraysize=cursor.arraysize,
                              outconverter=lambda v: v.strftime("%Y-%m-%d %H:%M:%S"))

    # locale conversion
    def type_handler4(cursor, name, default_type, size, precision, scale):
        if metadata.type_code is oracledb.DB_TYPE_DATE:
            return cursor.var(metadata.type_code, arraysize=cursor.arraysize,
                              outconverter=lambda v: v.strftime(locale_date_format))


    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb")

    with connection.cursor() as cursor:

         print("no type handler...")
         cursor.execute("select sysdate from dual")
         for row in cursor:
             print(row)       # gives datetime.datetime(2021, 12, 15, 19, 49, 37)
         print()

         print("with naive type handler...")
         connection.outputtypehandler = type_handler3
         cursor.execute("select sysdate from dual")
         for row in cursor:
             print(row)       # gives '2021-12-15 19:49:37'
         print()

         print("with locale type handler...")
         connection.outputtypehandler = type_handler4
         cursor.execute("select sysdate from dual")
         for row in cursor:
             print(row)       # gives 'Mi 15 Dez 19:57:56 2021'
         print()

Inserting NVARCHAR2 and NCHAR Data
----------------------------------

To bind NVARCHAR2 data, use :func:`Cursor.setinputsizes()` or create a bind
variable with the correct type by calling :func:`Cursor.var()`.  This removes
an internal character set conversion to the standard `Database Character Set`_
that may corrupt data.  By binding as :data:`oracledb.DB_TYPE_NVARCHAR`, the
data is inserted directly as the `Database National Character Set`_. For
example, to insert into a table containing two NVARCHAR2 columns:

.. code-block:: python

    sql = "insert into mytable values (:1, :2)"
    bv = ['data1', 'data2']
    cursor.setinputsizes(oracledb.DB_TYPE_NVARCHAR, oracledb.DB_TYPE_NVARCHAR)
    cursor.execute(sql, bv)

For NCHAR data, bind as :data:`oracledb.DB_TYPE_NCHAR`.
