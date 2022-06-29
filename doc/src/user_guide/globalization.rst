.. _globalization:

********************************
Character Sets and Globalization
********************************

Character Sets
==============

Database Character Set
----------------------

Data fetched from and sent to Oracle Database will be mapped between the
`database character set
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-EA913CC8-C5BA-4FB3-A1B8-882734AF4F43>`__
and the "Oracle client" character set of the Oracle Client libraries used by
python-oracledb. If data cannot be correctly mapped between client and server
character sets, then it may be corrupted or queries may fail with :ref:`"codec
can't decode byte" <codecerror>`.

All database character sets are supported by the python-oracledb.

.. _findingcharset:

To find the database character set, execute the query:

.. code-block:: sql

    SELECT value AS db_charset
    FROM nls_database_parameters
    WHERE parameter = 'NLS_CHARACTERSET';

Database National Character Set
-------------------------------

For the secondary `national character set
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-4E12D991-C286-4F1A-AFC6-F35040A5DE4F>`__
used for NCHAR, NVARCHAR2, and NCLOB data types:

- AL16UTF16 is supported by both the python-oracledb Thin and Thick modes
- UTF8 is not supported by the python-oracledb Thin mode

To find the database's national character set, execute the query:

.. code-block:: sql

     SELECT value AS db_ncharset
     FROM nls_database_parameters
     WHERE parameter = 'NLS_NCHAR_CHARACTERSET';

Setting the Client Character Set
--------------------------------

In python-oracledb, the encoding used for all character data is "UTF-8".  The
``encoding`` and ``nencoding`` parameters of the :meth:`oracledb.connect`
and :meth:`oracledb.create_pool` methods are deprecated and ignored.


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
Environment Variable
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-86A29834-AE29-4BA5-8A78-E19C168B690A>`__

If the ``NLS_LANG`` environment variable is set in the application with
``os.environ['NLS_LANG']``, it must be set before any connection pool is
created, or before any standalone connections are created.

Any client character set value in the ``NLS_LANG`` variable, for example
``JAPANESE_JAPAN.JA16SJIS``, is ignored by python-oracledb.  See `Setting the
Client Character Set`_.

Other Oracle globalization variables, such as ``NLS_DATE_FORMAT`` can also be
set to change the behavior of python-oracledb Thick, see `Setting NLS Parameters
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-6475CA50-6476-4559-AD87-35D431276B20>`__.

For more information, see the `Database Globalization Support Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=NLSPG>`__.

.. _thindatenumber:

Thin Mode Locale-aware Number and Date Conversions
--------------------------------------------------

.. note::

    All NLS environment variables are ignored by the python-oracledb Thin mode.
    Also the ``ORA_SDTZ`` and ``ORA_TZFILE`` variables are ignored.

In the python-oracledb Thin mode, output type handlers need to be used to
perform similar conversions.  The examples below show a simple conversion and
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
    def type_handler1(cursor, name, default_type, size, precision, scale):
        if default_type == oracledb.DB_TYPE_NUMBER:
            return cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=cursor.arraysize,
                    outconverter=lambda v: v.replace('.', ','))

    # locale conversion
    def type_handler2(cursor, name, default_type, size, precision, scale):
        if default_type == oracledb.DB_TYPE_NUMBER:
            return cursor.var(default_type, arraysize=cursor.arraysize,
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
    def type_handler3(cursor, name, default_type, size, precision, scale):
        if default_type == oracledb.DB_TYPE_DATE:
            return cursor.var(default_type, arraysize=cursor.arraysize,
                    outconverter=lambda v: v.strftime("%Y-%m-%d %H:%M:%S"))

    # locale conversion
    def type_handler4(cursor, name, default_type, size, precision, scale):
        if default_type == oracledb.DB_TYPE_DATE:
            return cursor.var(default_type, arraysize=cursor.arraysize,
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
