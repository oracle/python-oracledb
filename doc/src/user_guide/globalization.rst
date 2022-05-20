.. _globalization:

********************************
Character Sets and Globalization
********************************

Data fetched from and sent to Oracle Database will be mapped between the
database character set and the "Oracle client" character set of the Oracle
Client libraries used by python-oracledb. If data cannot be correctly mapped between
client and server character sets, then it may be corrupted or queries may fail
with :ref:`"codec can't decode byte" <codecerror>`.

All database character sets are supported by the python-oracledb Thick mode.
The database performs any required conversion for the python-oracledb Thin
mode.

For the `national character set
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-4E12D991-C286-4F1A-AFC6-F35040A5DE4F>`__
used for NCHAR, NVARCHAR2, and NCLOB data types:

- AL16UTF16 is supported by both the python-oracledb Thin and Thick modes
- UTF8 is not supported by the python-oracledb Thin mode

Python-oracledb Thick mode uses Oracle's National Language Support (NLS) to
assist in globalizing applications, see :ref:`thicklocale`.

.. note::

    All NLS environment variables are ignored by the python-oracledb Thin mode.
    Also the ``ORA_SDTZ`` and ``ORA_TZFILE`` variables are ignored.  See
    :ref:`thindatenumber`.

For more information, see the `Database Globalization Support Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=NLSPG>`__.

Setting the Client Character Set
================================

In python-oracledb, the encoding used for all character data is "UTF-8".  The
``encoding`` and ``nencoding`` parameters of the :meth:`oracledb.connect`
and :meth:`oracledb.create_pool` methods are ignored.

.. _findingcharset:


Finding the Oracle Database Character Set
=========================================

To find the database character set, execute the query:

.. code-block:: sql

    SELECT value AS db_charset
    FROM nls_database_parameters
    WHERE parameter = 'NLS_CHARACTERSET';

To find the database 'national character set' used for NCHAR and related types,
execute the query:

.. code-block:: sql

     SELECT value AS db_ncharset
     FROM nls_database_parameters
     WHERE parameter = 'NLS_NCHAR_CHARACTERSET';

To find the current "client" character set used by python-oracledb, execute the
query:

.. code-block:: sql

    SELECT DISTINCT client_charset AS client_charset
    FROM v$session_connect_info
    WHERE sid = SYS_CONTEXT('USERENV', 'SID');


.. _thindatenumber:

Locale-aware Number and Date Conversions in python-oracledb Thin Mode
=====================================================================

In python-oracledb Thick mode, Oracle NLS routines convert numbers and dates to
strings in the locale specific format.  But in the python-oracledb Thin mode,
output type handlers need to be used to perform similar conversions.  The
examples below show a simple conversion and also how the Python locale module
can be used.

To convert numbers:

.. code-block:: python

    import locale
    import oracledb

    # use this if the environment variable LANG is already set
    #locale.setlocale(locale.LC_ALL, '')

    # use this for programmatic setting of locale
    locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')

    DSN = 'user/password@host/service_name'

    # simple naive conversion
    def type_handler1(cursor, name, default_type, size, precision, scale):
        if default_type == oracledb.DB_TYPE_NUMBER:
            return cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=cursor.arraysize,
                    outconverter=lambda v: v.replace('.', ','))

    # locale conversion
    def type_handler2(cursor, name, default_type, size, precision, scale):
        if default_type == oracledb.DB_TYPE_NUMBER:
            return cursor.var(default_type, arraysize=cursor.arraysize,
                    outconverter=lambda v: locale.format_string("%g", v))


    conn = oracledb.connect(DSN)
    cursor = conn.cursor()

    print("no type handler...")
    cursor.execute("select 2.5 from dual")
    for row in cursor:
        print(row)       # gives 2.5
    print()

    print("with naive type handler...")
    conn.outputtypehandler = type_handler1
    cursor.execute("select 2.5 from dual")
    for row in cursor:
        print(row)       # gives '2,5'
    print()

    print("with locale type handler...")
    conn.outputtypehandler = type_handler2
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

    DSN = 'user/password@host/service_name'

    # simple naive conversion
    def type_handler3(cursor, name, default_type, size, precision, scale):
        if default_type == oracledb.DB_TYPE_DATE:
            return cursor.var(default_type, arraysize=cursor.arraysize,
                    outconverter=lambda v: v.strftime("%Y-%m-%d %H:%M:%S"))

    # locale conversion
    def type_handler4(cursor, name, default_type, size, precision, scale):
        if default_type == oracledb.DB_TYPE_DATE:
            return cursor.var(default_type, arraysize=cursor.arraysize,
                    outconverter=lambda v: v.strftime(locale_date_format))


    conn = oracledb.connect(DSN)
    cursor = conn.cursor()

    print("no type handler...")
    cursor.execute("select sysdate from dual")
    for row in cursor:
        print(row)       # gives datetime.datetime(2021, 12, 15, 19, 49, 37)
    print()

    print("with naive type handler...")
    conn.outputtypehandler = type_handler3
    cursor.execute("select sysdate from dual")
    for row in cursor:
        print(row)       # gives '2021-12-15 19:49:37'
    print()

    print("with locale type handler...")
    conn.outputtypehandler = type_handler4
    cursor.execute("select sysdate from dual")
    for row in cursor:
        print(row)       # gives 'Mi 15 Dez 19:57:56 2021'
    print()


.. _thicklocale:

Setting the Oracle Client Locale in python-oracledb Thick Mode
==============================================================

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
Environment Variable
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-86A29834-AE29-4BA5-8A78-E19C168B690A>`__

If the ``NLS_LANG`` environment variable is set in the application with
``os.environ['NLS_LANG']``, it must be set before any connection pool is
created, or before any standalone connections are created.

Other Oracle globalization variables, such as ``NLS_DATE_FORMAT`` can also be
set to change the behavior of python-oracledb Thick, see `Setting NLS Parameters
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-6475CA50-6476-4559-AD87-35D431276B20>`__.
