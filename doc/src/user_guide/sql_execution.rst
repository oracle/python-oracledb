.. _sqlexecution:

.. currentmodule:: oracledb

*************
Executing SQL
*************

Executing SQL statements is the primary way in which a Python application
communicates with Oracle Database. Statements include queries, Data
Manipulation Language (DML), and Data Definition Language (DDL).  A few other
`specialty statements <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-E1749EF5-2264-44DF-99EF-AEBEB943BED6>`__ can also be
executed. Statements are executed using one of these methods
:meth:`Cursor.execute()`, :meth:`Cursor.executemany()`,
:meth:`Connection.fetch_df_all()`, :meth:`Connection.fetch_df_batches()`,
:meth:`AsyncCursor.execute()`, :meth:`AsyncCursor.executemany()`,
:meth:`AsyncConnection.execute()`, :meth:`AsyncConnection.executemany()`,
:meth:`AsyncConnection.fetch_df_all()`,
:meth:`AsyncConnection.fetch_df_batches()`, or
:meth:`AsyncConnection.run_pipeline()`.

This chapter discusses python-oracledb's synchronous methods. The asynchronous
methods and pipelining functionality are discussed in detail in :ref:`asyncio`.

PL/SQL statements are discussed in :ref:`plsqlexecution`. The following
chapters contain information on specific data types and features:

- :ref:`batchstmnt`
- :ref:`pipelining`
- :ref:`lobdata`
- :ref:`jsondatatype`
-  :ref:`xmldatatype`

To help you create SQL and PL/SQL statements, Oracle hosts `FreeSQL.com
<https://freesql.com/>`__ which gives you an online editor immediately
connected to a database. It also has tutorials and a library of statements.

**Executing SQL Scripts**

Python-oracledb can be used to execute individual statements, one at a time.
Once a statement has finished execution, only then will the next statement
execute. If you try to execute statements concurrently in a single connection,
the statements are queued and run consecutively in the order they are executed
in the application code. This includes :ref:`Pipelined statements
<pipelining>`.

Python-oracledb does not read SQL*Plus ".sql" files.  To read SQL files, use a
technique like the one in ``run_sql_script()`` in `samples/sample_env.py
<https://github.com/oracle/python-oracledb/blob/main/samples/sample_env.py>`__.

**SQL Statement Syntax**

SQL statements executed in python-oracledb should not contain a trailing
semicolon (";") or forward slash ("/"). This will fail:

.. code-block:: python

    cursor.execute("select * from MyTable;")   # fails due to semicolon

This is correct:

.. code-block:: python

    cursor.execute("select * from MyTable")

.. IMPORTANT::

    Interpolating or concatenating user data with SQL statements, for example
    ``cursor.execute("SELECT * FROM mytab WHERE mycol = '" + myvar + "'")`` is
    a security risk and impacts performance.  Use :ref:`bind variables <bind>`
    instead, for example ``cursor.execute("SELECT * FROM mytab WHERE mycol =
    :mybv", mybv=myvar)``.


SQL Queries
===========

Queries (statements beginning with SELECT or WITH) can be executed using the
method :meth:`Cursor.execute()`.  Rows can then be iterated over, or can be
fetched using one of the methods :meth:`Cursor.fetchone()`,
:meth:`Cursor.fetchmany()` or :meth:`Cursor.fetchall()`. This lets you handle
rows directly or stream them if needed. There is a :ref:`default type mapping
<defaultfetchtypes>` to Python types that can be optionally :ref:`overridden
<outputtypehandlers>`.

.. _fetching:

Fetch Methods
-------------

Rows can be fetched in various ways.

- After :meth:`Cursor.execute()`, the cursor is returned as a convenience. This
  allows code to iterate over rows like:

  .. code-block:: python

      cursor = connection.cursor()
      for row in cursor.execute("select * from MyTable"):
          print(row)

- Rows can also be fetched one at a time using the method
  :meth:`Cursor.fetchone()`:

  .. code-block:: python

      cursor = connection.cursor()
      cursor.execute("select * from MyTable")
      while True:
          row = cursor.fetchone()
          if row is None:
              break
          print(row)

- If rows need to be streamed or processed in batches, the method
  :meth:`Cursor.fetchmany()` can be used. The size of the batch is controlled
  by the ``size`` parameter, which defaults to the value of
  :attr:`Cursor.arraysize`.

  .. code-block:: python

      cursor = connection.cursor()
      cursor.execute("select * from MyTable")
      num_rows = 10
      while True:
          rows = cursor.fetchmany(size=num_rows)
          if not rows:
              break
          for row in rows:
              print(row)

  Note the ``size`` parameter only affects the number of rows returned to the
  application, not to the internal buffer size used for tuning fetch
  performance. That internal buffer size is controlled only by changing
  :attr:`Cursor.arraysize` or :attr:`oracledb.defaults.arraysize
  <Defaults.arraysize>`, see :ref:`tuningfetch`.

- If all of the rows need to be fetched and can be contained in memory, the
  method :meth:`Cursor.fetchall()` can be used.

  .. code-block:: python

      cursor = connection.cursor()
      cursor.execute("select * from MyTable")
      rows = cursor.fetchall()
      for row in rows:
          print(row)

  The fetch methods return data as tuples.  To return results as dictionaries, see
  :ref:`rowfactories`.

- Data can also be fetched in data frame format, see :ref:`dataframeformat`.

Closing Cursors
---------------

Once cursors are no longer needed, they should be closed in order to reclaim
resources in the database.  Note cursors may be used to execute multiple
statements before being closed.

Cursors can be closed in various ways:

- A cursor will be closed automatically when the variable referencing it goes
  out of scope (and no further references are retained). A ``with`` context
  manager block is a convenient and preferred way to ensure this. For example:

  .. code-block:: python

      with connection.cursor() as cursor:
          for row in cursor.execute("select * from MyTable"):
              print(row)

  This code ensures that once the block is completed, the cursor is closed and
  database resources can be reclaimed. In addition, any attempt to use the
  variable ``cursor`` outside of the block will fail.

- Cursors can be explicitly closed by calling :meth:`Cursor.close()`:

  .. code-block:: python

      cursor = connection.cursor()

      ...

      cursor.close()


.. _querymetadata:

Query Column Metadata
---------------------

After executing a query, the column metadata such as column names and data types
can be obtained using :attr:`Cursor.description`:

.. code-block:: python

    with connection.cursor() as cursor:
        cursor.execute("select * from MyTable")
        for column in cursor.description:
            print(column)

This could result in metadata like::

    ('ID', <class 'oracledb.DB_TYPE_NUMBER'>, 39, None, 38, 0, 0)
    ('NAME', <class 'oracledb.DB_TYPE_VARCHAR'>, 20, 20, None, None, 1)

To extract the column names from a query you can use code like:

.. code-block:: python

    with connection.cursor() as cursor:
        cursor.execute("select * from locations")
        columns = [col.name for col in cursor.description]
        print(columns)
        for r in cursor:
            print(r)

This will print::

    ['LOCATION_ID', 'STREET_ADDRESS', 'POSTAL_CODE', 'CITY', 'STATE_PROVINCE', 'COUNTRY_ID']
    (1000, '1297 Via Cola di Rie', '00989', 'Roma', None, 'IT')
    (1100, '93091 Calle della Testa', '10934', 'Venice', None, 'IT')
    . . .

**Changing Column Names to Lowercase**

To change all column names to lowercase you could do:

.. code-block:: python

    cursor.execute("select * from locations where location_id = 1000")

    columns = [col.name.lower() for col in cursor.description]
    print(columns)

The output is::

    ['location_id', 'street_address', 'postal_code', 'city', 'state_province',
    'country_id']

.. _defaultfetchtypes:

Fetch Data Types
----------------

The following table provides a list of all of the data types that python-oracledb
knows how to fetch. The middle column gives the type that is returned in the
:ref:`query metadata <querymetadata>`.  The last column gives the type of
Python object that is returned by default. Python types can be changed with
:ref:`Output Type Handlers <outputtypehandlers>`.

.. list-table-with-summary::
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 1 1 1
    :align: left
    :summary: The first column is the Oracle Database Type. The second column is the oracledb Database Type that is returned in the query metadata. The third column is the type of Python object that is returned by default.

    * - Oracle Database Type
      - oracledb Database Type
      - Default Python type
    * - BFILE
      - :attr:`oracledb.DB_TYPE_BFILE`
      - :ref:`oracledb.LOB <lobobj>`
    * - BINARY_DOUBLE
      - :attr:`oracledb.DB_TYPE_BINARY_DOUBLE`
      - float
    * - BINARY_FLOAT
      - :attr:`oracledb.DB_TYPE_BINARY_FLOAT`
      - float
    * - BLOB
      - :attr:`oracledb.DB_TYPE_BLOB`
      - :ref:`oracledb.LOB <lobobj>`
    * - CHAR
      - :attr:`oracledb.DB_TYPE_CHAR`
      - str
    * - CLOB
      - :attr:`oracledb.DB_TYPE_CLOB`
      - :ref:`oracledb.LOB <lobobj>`
    * - CURSOR
      - :attr:`oracledb.DB_TYPE_CURSOR`
      - :ref:`oracledb.Cursor <cursorobj>`
    * - DATE
      - :attr:`oracledb.DB_TYPE_DATE`
      - datetime.datetime
    * - INTERVAL DAY TO SECOND
      - :attr:`oracledb.DB_TYPE_INTERVAL_DS`
      - datetime.timedelta
    * - INTERVAL YEAR TO MONTH
      - :data:`oracledb.DB_TYPE_INTERVAL_YM`
      - :ref:`oracledb.IntervalYM <interval_ym>`
    * - JSON
      - :attr:`oracledb.DB_TYPE_JSON`
      - dict, list or a scalar value [4]_
    * - LONG
      - :attr:`oracledb.DB_TYPE_LONG`
      - str
    * - LONG RAW
      - :attr:`oracledb.DB_TYPE_LONG_RAW`
      - bytes
    * - NCHAR
      - :attr:`oracledb.DB_TYPE_NCHAR`
      - str
    * - NCLOB
      - :attr:`oracledb.DB_TYPE_NCLOB`
      - :ref:`oracledb.LOB <lobobj>`
    * - NUMBER
      - :attr:`oracledb.DB_TYPE_NUMBER`
      - float or int [1]_
    * - NVARCHAR2
      - :attr:`oracledb.DB_TYPE_NVARCHAR`
      - str
    * - OBJECT [3]_
      - :attr:`oracledb.DB_TYPE_OBJECT`
      - :ref:`oracledb.Object <dbobjecttype>`
    * - RAW
      - :attr:`oracledb.DB_TYPE_RAW`
      - bytes
    * - ROWID
      - :attr:`oracledb.DB_TYPE_ROWID`
      - str
    * - TIMESTAMP
      - :attr:`oracledb.DB_TYPE_TIMESTAMP`
      - datetime.datetime
    * - TIMESTAMP WITH LOCAL TIME ZONE
      - :attr:`oracledb.DB_TYPE_TIMESTAMP_LTZ`
      - datetime.datetime [2]_
    * - TIMESTAMP WITH TIME ZONE
      - :attr:`oracledb.DB_TYPE_TIMESTAMP_TZ`
      - datetime.datetime [2]_
    * - UROWID
      - :attr:`oracledb.DB_TYPE_ROWID`, :attr:`oracledb.DB_TYPE_UROWID`
      - str
    * - VARCHAR2
      - :attr:`oracledb.DB_TYPE_VARCHAR`
      - str

.. [1] If the precision and scale obtained from query column metadata indicate
       that the value can be expressed as an integer, the value will be
       returned as an int. If the column is unconstrained (no precision and
       scale specified), the value will be returned as a float or an int
       depending on whether the value itself is an integer. In all other cases
       the value is returned as a float.
.. [2] The timestamps returned are naive timestamps without any time zone
       information present.
.. [3] These include all user-defined types such as VARRAY, NESTED TABLE, etc.

.. [4] If the JSON is an object, then a dict is returned. If it is an array,
       then a list is returned. If it is a scalar value, then that particular
       scalar value is returned.


.. _changingdata:

Changing Fetched Data
---------------------

Data returned by python-oracledb queries can be changed by using output type
handlers, by using "outconverters", or by using row factories.

.. _outputtypehandlers:

Changing Fetched Data Types with Output Type Handlers
+++++++++++++++++++++++++++++++++++++++++++++++++++++

Sometimes the default conversion from an Oracle Database type to a Python type
must be changed in order to prevent data loss or to fit the purposes of the
Python application. In such cases, an output type handler can be specified for
queries.  This asks the database to do a conversion from the column type to a
different type before the data is returned from the database to
python-oracledb.  If the database does not support such a mapping, an error
will be returned.  Output type handlers only affect query output and do not
affect values returned from :meth:`Cursor.callfunc()` or
:meth:`Cursor.callproc()`.

Output type handlers can be specified on a :attr:`connection
<Connection.outputtypehandler>` or on a :attr:`cursor
<Cursor.outputtypehandler>`. If specified on a cursor, fetch type handling is
only changed on that particular cursor. If specified on a connection, all
cursors created by that connection will have their fetch type handling changed.

The output type handler is expected to be a function with the following
signature::

    handler(cursor, metadata)

The metadata parameter is a :ref:`FetchInfo object<fetchinfoobj>`, which is the
same value found in :attr:`Cursor.description`.

The function is called once for each column that is going to be
fetched. The function is expected to return a :ref:`variable object <varobj>`
(generally by a call to :func:`Cursor.var()`) or the value ``None``. The value
``None`` indicates that the default type should be used.

For example:

.. code-block:: python

    def output_type_handler(cursor, metadata):
        if metadata.type_code is oracledb.DB_TYPE_NUMBER:
            return cursor.var(oracledb.DB_TYPE_VARCHAR, arraysize=cursor.arraysize)

This output type handler is called once for each column in the SELECT query.
For each numeric column, the database will now return a string representation
of each row's value.  Using it in a query:

.. code-block:: python

    cursor.outputtypehandler = output_type_handler

    cursor.execute("select 123 from dual")
    r = cursor.fetchone()
    print(r)

prints ``('123',)`` showing the number was converted to a string.  Without the
type handler, the output would have been ``(123,)``.

When creating variables using :meth:`Cursor.var()` in a handler, the
``arraysize`` parameter should be the same as the :attr:`Cursor.arraysize` of
the query cursor.  In python-oracledb Thick mode, the query (and ``var()``)
arraysize multiplied by the byte size of the particular column must be less
than INT_MAX.

To unset an output type handler, set it to ``None``.  For example if you had
previously set a type handler on a cursor, you can remove it with:

.. code-block:: python

    cursor.outputtypehandler = None

Other examples of output handlers are shown in :ref:`numberprecision`,
:ref:`directlobs`, and :ref:`fetching-raw-data`.  Also see samples such as
`samples/type_handlers_json_strings.py
<https://github.com/oracle/python-oracledb/blob/main/samples/type_handlers_
json_strings.py>`__.

.. _outconverters:

Changing Query Results with Outconverters
+++++++++++++++++++++++++++++++++++++++++

Python-oracledb "outconverters" can be used with :ref:`output type handlers
<outputtypehandlers>` to change returned data.

For example, to convert numbers to strings:

.. code-block:: python

    def output_type_handler(cursor, metadata):

        def out_converter(d):
            if isinstance(d, str):
                return f"{d} was a string"
            else:
                return f"{d} was not a string"

        if metadata.type_code is oracledb.DB_TYPE_NUMBER:
            return cursor.var(oracledb.DB_TYPE_VARCHAR,
                 arraysize=cursor.arraysize, outconverter=out_converter)

The output type handler is called once for each column in the SELECT query.
For each numeric column, the database will now return a string representation
of each row's value, and the outconverter will be called for each of those
values.

Using it in a query:

.. code-block:: python

    cursor.outputtypehandler = output_type_handler

    cursor.execute("select 123 as col1, 'abc' as col2 from dual")
    for r in cursor.fetchall():
        print(r)

prints::

    ('123 was a string', 'abc')

This shows that the number was first converted to a string by the database, as
requested in the output type handler.  The ``out_converter`` function then
appended "was a string" to the data before the value was returned to the
application.

Note outconverters are not called for NULL data values unless the
:meth:`Cursor.var()` parameter ``convert_nulls`` is *True*.

Another example of an outconverter is shown in :ref:`fetching VECTORs as lists
<vecoutputtypehandlerlist>`.

.. _rowfactories:

Changing Query Results with Rowfactories
++++++++++++++++++++++++++++++++++++++++

Python-oracledb "rowfactories" are methods called for each row retrieved from
the database. The :meth:`Cursor.rowfactory` method is called with the tuple
fetched from the database before it is returned to the application.  The method
can convert the tuple to a different value or representation.

A rowfactory should be set on a cursor after a call to :meth:`Cursor.execute()`
before fetching data from the cursor. Calling :meth:`~Cursor.execute()` again
will clear any previous rowfactory.

**Fetching Rows using a Data Class**

Python `Data Classes <https://docs.python.org/3/library/dataclasses.html>`__
provide a simple way to encapsulate data. An example of using them with a query
rowfactory is:

.. code-block:: python

    import dataclasses
    import datetime

    . . .

    @dataclasses.dataclass
    class MyRow:
        employee_id: int
        last_name: str
        hire_date: datetime.datetime

    cursor.execute(
        """select employee_id, last_name, hire_date
           from employees
           where employee_id < 105
           order by employee_id""")

    cursor.rowfactory = MyRow

    for row in cursor:
        print("Number:", row.employee_id)
        print("Name:", row.last_name)
        print("Hire Date:", row.hire_date)

The output is::

    Number: 100
    Name: King
    Hire Date: 2003-06-17 00:00:00
    Number: 101
    Name: Kochhar
    Hire Date: 2005-09-21 00:00:00
    Number: 102
    Name: De Haan
    Hire Date: 2001-01-13 00:00:00

**Fetching Rows as Dictionaries**

To fetch each row of a query as a dictionary, you can use
:meth:`Cursor.rowfactory` like:

.. code-block:: python

    cursor.execute("select * from locations where location_id = 1000")

    columns = [col.name for col in cursor.description]
    cursor.rowfactory = lambda *args: dict(zip(columns, args))
    data = cursor.fetchone()
    print(data)

The output is::

    {'LOCATION_ID': 1000, 'STREET_ADDRESS': '1297 Via Cola di Rie',
    'POSTAL_CODE': '00989', 'CITY': 'Roma', 'STATE_PROVINCE': None,
    'COUNTRY_ID': 'IT'}

Also see how ``JSON_OBJECT`` is used in :ref:`jsondatatype`, since querying
directly as JSON may be preferable.

If you join tables where the same column name occurs in both tables with
different meanings or values, then use a column alias in the query.  Otherwise,
only one of the similarly named columns will be included in the dictionary:

.. code-block:: sql

    select
        cat_name,
        cats.color as cat_color,
        dog_name,
        dogs.color
    from cats, dogs

**Example with an Output Type Handler, Outconverter, and Row Factory**

An example showing an :ref:`output type handler <outputtypehandlers>`, an
:ref:`outconverter <outconverters>`, and a :ref:`row factory <rowfactories>`
is:

.. code-block:: python

    def output_type_handler(cursor, metadata):

        def out_converter(d):
            if type(d) is str:
                return f"{d} was a string"
            else:
                return f"{d} was not a string"

        if metadata.type_code is oracledb.DB_TYPE_NUMBER:
            return cursor.var(oracledb.DB_TYPE_VARCHAR,
                arraysize=cursor.arraysize, outconverter=out_converter)

    cursor.outputtypehandler = output_type_handler

    cursor.execute("select 123 as col1, 'abc' as col2 from dual")

    columns = [col.name.lower() for col in cursor.description]
    cursor.rowfactory = lambda *args: dict(zip(columns, args))
    for r in cursor.fetchall():
        print(r)

The database converts the number to a string before it is returned to
python-oracledb. The outconverter appends "was a string" to this value. The
column names are converted to lowercase. Finally, the row factory changes the
complete row to a dictionary. The output is::

    {'col1': '123 was a string', 'col2': 'abc'}

.. _numberprecision:

Fetched Number Precision
------------------------

Oracle Database uses decimal numbers and these cannot be converted seamlessly
to binary number representations like Python floats. In addition, the range of
Oracle numbers exceeds that of floating point numbers. Python has decimal
objects which do not have these limitations. In python-oracledb you can set
:attr:`oracledb.defaults.fetch_decimals <Defaults.fetch_decimals>` so that
Decimals are returned to the application, ensuring that numeric precision is
not lost when fetching certain numbers.

The following code sample demonstrates the issue:

.. code-block:: python

    cursor.execute("create table test_float (X number(5, 3))")
    cursor.execute("insert into test_float values (7.1)")

    cursor.execute("select * from test_float")
    val, = cursor.fetchone()
    print(val, "* 3 =", val * 3)

This displays ``7.1 * 3 = 21.299999999999997``

Using Python decimal objects, however, there is no loss of precision:

.. code-block:: python

    oracledb.defaults.fetch_decimals = True

    cursor.execute("select * from test_float")
    val, = cursor.fetchone()
    print(val, "* 3 =", val * 3)

This displays ``7.1 * 3 = 21.3``

See `samples/return_numbers_as_decimals.py
<https://github.com/oracle/python-oracledb/blob/main/samples/return_numbers_as_decimals.py>`__

An equivalent, longer, older coding idiom to setting
:attr:`oracledb.defaults.fetch_decimals <Defaults.fetch_decimals>` is to use an
:ref:`output type handler <outputtypehandlers>` to do the conversion.

.. code-block:: python

    import decimal

    def number_to_decimal(cursor, metadata):
        if metadata.type_code is oracledb.DB_TYPE_NUMBER:
            return cursor.var(decimal.Decimal, arraysize=cursor.arraysize)

    cursor.outputtypehandler = number_to_decimal

    cursor.execute("select * from test_float")
    val, = cursor.fetchone()
    print(val, "* 3 =", val * 3)

This displays ``7.1 * 3 = 21.3``

The Python ``decimal.Decimal`` converter gets called with the string
representation of the Oracle number.  The output from ``decimal.Decimal`` is
returned in the output tuple.

.. _scrollablecursors:

Scrollable Cursors
------------------

Scrollable cursors enable applications to move backwards, forwards, to skip
rows, and to move to a particular row in a query result set. The result set is
cached on the database server until the cursor is closed. In contrast, regular
cursors are restricted to moving forward.

A scrollable cursor is created by setting the parameter ``scrollable=True``
when creating the cursor. The method :meth:`Cursor.scroll()` is used to move to
different locations in the result set.

Examples are:

.. code-block:: python

    cursor = connection.cursor(scrollable=True)
    cursor.execute("select * from ChildTable order by ChildId")

    cursor.scroll(mode="last")
    print("LAST ROW:", cursor.fetchone())

    cursor.scroll(mode="first")
    print("FIRST ROW:", cursor.fetchone())

    cursor.scroll(8, mode="absolute")
    print("ROW 8:", cursor.fetchone())

    cursor.scroll(6)
    print("SKIP 6 ROWS:", cursor.fetchone())

    cursor.scroll(-4)
    print("SKIP BACK 4 ROWS:", cursor.fetchone())

See `samples/scrollable_cursors.py <https://github.com/oracle/python-oracledb/
blob/main/samples/scrollable_cursors.py>`__ for a runnable example.


.. _fetchobjects:

Fetching Oracle Database Objects and Collections
------------------------------------------------

Oracle Database named object types and user-defined types can be fetched
directly in queries.  Each item is represented as a :ref:`Python object
<dbobjecttype>` corresponding to the Oracle Database object.  This Python
object can be traversed to access its elements.  Attributes including
:attr:`DbObjectType.name` and :attr:`DbObjectType.iscollection`, and methods
including :meth:`DbObject.aslist` and :meth:`DbObject.asdict` are available.

For example, if a table MYGEOMETRYTAB contains a column GEOMETRY of
Oracle's predefined Spatial object type `SDO_GEOMETRY
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-683FF8C5-A773-4018-932D-2AF6EC8BC119>`__,
then it can be queried and printed:

.. code-block:: python

    cursor.execute("select geometry from mygeometrytab")
    for obj, in cursor:
        dumpobject(obj)

Where ``dumpobject()`` is defined as:

.. code-block:: python

    def dumpobject(obj, prefix = ""):
        if obj.type.iscollection:
            print(prefix, "[")
            for value in obj.aslist():
                if isinstance(value, oracledb.Object):
                    dumpobject(value, prefix + "  ")
                else:
                    print(prefix + "  ", repr(value))
            print(prefix, "]")
        else:
            print(prefix, "{")
            for attr in obj.type.attributes:
                value = getattr(obj, attr.name)
                if isinstance(value, oracledb.Object):
                    print(prefix + "   " + attr.name + ":")
                    dumpobject(value, prefix + "  ")
                else:
                    print(prefix + "   " + attr.name + ":", repr(value))
            print(prefix, "}")

This might produce output like::

    {
      SDO_GTYPE: 2003
      SDO_SRID: None
      SDO_POINT:
      {
        X: 1
        Y: 2
        Z: 3
      }
      SDO_ELEM_INFO:
      [
        1
        1003
        3
      ]
      SDO_ORDINATES:
      [
        1
        1
        5
        7
      ]
    }

Other information on using Oracle objects is in :ref:`Using Bind Variables
<bind>`.

Performance-sensitive applications should consider using scalar types instead of
objects. If you do use objects, avoid calling :meth:`Connection.gettype()`
unnecessarily, and avoid objects with large numbers of attributes.

.. _rowlimit:

Limiting Rows
-------------

Query data is commonly broken into one or more sets:

- To give an upper bound on the number of rows that a query has to process,
  which can help improve database scalability.

- To perform 'Web pagination' that allows moving from one set of rows to a
  next, or previous, set on demand.

- For fetching of all data in consecutive small sets for batch processing.
  This happens because the number of records is too large for Python to handle
  at one time.

The latter can be handled by calling :meth:`Cursor.fetchmany()` with one
execution of the SQL query.

'Web pagination' and limiting the maximum number of rows are detailed in this
section.  For each 'page' of results, a SQL query is executed to get the
appropriate set of rows from a table.  Since the query may be executed more
than once, ensure to use :ref:`bind variables <bind>` for row numbers and
row limits.

Oracle Database 12c SQL introduced an ``OFFSET`` / ``FETCH`` clause which is
similar to the ``LIMIT`` keyword of MySQL.  In Python, you can fetch a set of
rows using:

.. code-block:: python

    myoffset = 0       # do not skip any rows (start at row 1)
    mymaxnumrows = 20  # get 20 rows

    sql =
      """SELECT last_name
         FROM employees
         ORDER BY last_name
         OFFSET :offset ROWS FETCH NEXT :maxnumrows ROWS ONLY"""

    with connection.cursor() as cursor:

        cursor.prefetchrows = mymaxnumrows + 1
        cursor.arraysize = mymaxnumrows

        for row in cursor.execute(sql, offset=myoffset, maxnumrows=mymaxnumrows):
            print(row)

In applications where the SQL query is not known in advance, this method
sometimes involves appending the ``OFFSET`` clause to the 'real' user query. Be
very careful to avoid SQL injection security issues.

For Oracle Database 11g and earlier there are several alternative ways
to limit the number of rows returned.  The old, canonical paging query
is::

    SELECT *
    FROM (SELECT a.*, ROWNUM AS rnum
          FROM (YOUR_QUERY_GOES_HERE -- including the order by) a
          WHERE ROWNUM <= MAX_ROW)
    WHERE rnum >= MIN_ROW

Here, ``MIN_ROW`` is the row number of first row and ``MAX_ROW`` is the row
number of the last row to return.  For example::

   SELECT *
   FROM (SELECT a.*, ROWNUM AS rnum
         FROM (SELECT last_name FROM employees ORDER BY last_name) a
         WHERE ROWNUM <= 20)
   WHERE rnum >= 1

This always has an 'extra' column, here called RNUM.

An alternative and preferred query syntax for Oracle Database 11g uses the
analytic ``ROW_NUMBER()`` function. For example, to get the 1st to 20th names
the query is::

    SELECT last_name FROM
    (SELECT last_name,
            ROW_NUMBER() OVER (ORDER BY last_name) AS myr
            FROM employees)
    WHERE myr BETWEEN 1 and 20

Ensure to use :ref:`bind variables <bind>` for the upper and lower limit
values.

.. _parallelqueries:

Fetching Data in Parallel
-------------------------

The performance benefit of selecting table data in parallel from Oracle
Database compared with a executing a single query depends on many
factors. Partitioning the table and reading one partition per connection is
usually the most efficient database-side solution. However, even if a parallel
solution appears to be faster, it could be inefficient, thereby impacting, or
eventually being limited by, everyone else. Only benchmarking in your
environment will determine whether to use this technique.

A naive example using multiple threads is:

.. code-block:: python

    # A naive example for fetching data in parallel.
    # Many factors affect whether this is beneficial

    # The degree of parallelism / number of connections to open
    NUM_THREADS = 10

    # How many rows to fetch in each thread
    BATCH_SIZE = 1000

    # Internal buffer size: Tune for performance
    oracledb.defaults.arraysize = 1000

    # Note OFFSET/FETCH is not particularly efficient.
    # It would be better to use a partitioned table
    SQL = """
        select data
        from demo
        order by id
        offset :rowoffset rows fetch next :maxrows rows only
        """

    def do_query(tn):
        with pool.acquire() as connection:
            with connection.cursor() as cursor:
                cursor.execute(SQL, rowoffset=(tn*BATCH_SIZE), maxrows=BATCH_SIZE)
                while True:
                    rows = cursor.fetchmany()
                    if not rows:
                        break
                    print(f'Thread {tn}', rows)


    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb",
                                min=NUM_THREADS, max=NUM_THREADS)

    thread = []
    for i in range(NUM_THREADS):
        t = threading.Thread(target=do_query, args=(i,))
        t.start()
        thread.append(t)

    for i in range(NUM_THREADS):
        thread[i].join()

When considering to parallelize queries from a table, some of the many factors
include:

- Each connection to Oracle Database can only execute one statement at a time,
  so to parallelize queries requires using multiple connections.

- Python's threading behavior and impact of the Python's Global Interpreter
  Lock (GIL) may have an impact. You may need to spread work over multiple
  processes.

- What level of parallelism is most efficient?

- How many rows to fetch in each batch?

- What is your application doing with the data - can the receiving end
  efficiently process it, or write it to a disk?

- The OFFSET FETCH syntax will still cause database table blocks to be scanned
  even though not all data is returned to the application.  Can the table be
  partitioned instead?

- There will be extra load on the database, both from the additional
  connections, and the work they are performing.

- Do your queries use up all of the database's parallel servers?

- Is the data in the database spread across multiple disk spindles or is it the
  one disk which continually has to seek?

- Are Oracle Database zone maps being used?

- Is Oracle Exadata with storage indexes being used?

- Do you have function based indexes that are being invoked for every row?

.. _fetching-raw-data:

Fetching Raw Data
-----------------

Sometimes python-oracledb may have problems converting data stored in the database to
Python strings. This can occur if the data stored in the database does not match
the character set defined by the database. The ``encoding_errors`` parameter to
:meth:`Cursor.var()` permits the data to be returned with some invalid data
replaced, but for additional control the parameter ``bypass_decode`` can be set
to True and python-oracledb will bypass the decode step and return `bytes` instead
of `str` for data stored in the database as strings. The data can then be
examined and corrected as required. This approach should only be used for
troubleshooting and correcting invalid data, not for general use!

The following sample demonstrates how to use this feature:

    .. code-block:: python

        # define output type handler
        def return_strings_as_bytes(cursor, metadata):
            if metadata.type_code is oracledb.DB_TYPE_VARCHAR:
                return cursor.var(str, arraysize=cursor.arraysize,
                                  bypass_decode=True)

        # set output type handler on cursor before fetching data
        with connection.cursor() as cursor:
            cursor.outputtypehandler = return_strings_as_bytes
            cursor.execute("select content, charset from SomeTable")
            data = cursor.fetchall()

This will produce output as::

    [(b'Fianc\xc3\xa9', b'UTF-8')]


Note that last ``\xc3\xa9`` is é in UTF-8. Since this is valid UTF-8 you can then
perform a decode on the data (the part that was bypassed):

    .. code-block:: python

        value = data[0][0].decode("UTF-8")

This will return the value "Fiancé".

If you want to save ``b'Fianc\xc3\xa9'`` into the database directly without
using a Python string, you will need to create a variable using
:meth:`Cursor.var()` that specifies the type as
:data:`oracledb.DB_TYPE_VARCHAR` (otherwise the value will be treated as
:data:`oracledb.DB_TYPE_RAW`). The following sample demonstrates this:

    .. code-block:: python

        with oracledb.connect(user="hr", password=userpwd,
                               dsn="dbhost.example.com/orclpdb") as conn:
            with conn.cursor() cursor:
                var = cursor.var(oracledb.DB_TYPE_VARCHAR)
                var.setvalue(0, b"Fianc\xc4\x9b")
                cursor.execute("""
                    update SomeTable set
                        SomeColumn = :param
                    where id = 1""",
                    param=var)

.. warning::

    The database will assume that the bytes provided are in the character set
    expected by the database so only use this for troubleshooting or as
    directed.


.. _codecerror:

Querying Corrupt Data
---------------------

If queries fail with the error "codec can't decode byte" when you select data,
then:

* Check if your :ref:`character set <globalization>` is correct.  Review the
  :ref:`database character sets <findingcharset>`.  Check
  :ref:`fetching-raw-data`. Note that the encoding used for all character
  data in python-oracledb is "UTF-8".

* Check for corrupt data in the database and fix it.  For example, if you have
  a table MYTABLE with a character column MYVALUE that you suspect has some
  corrupt values, then you may be able to identify the problem data by using a
  query like ``select id from mytable where
  utl_i18n.validate_character_encoding(myvalue) > 0`` which will print out the
  keys of the rows with invalid data.

If corrupt data cannot be modified, you can pass options to the internal
`decode() <https://docs.python.org/3/library/stdtypes.html#bytes.decode>`__
used by python-oracledb to allow it to be selected and prevent the whole query
failing.  Do this by creating an :ref:`outputtypehandler <outputtypehandlers>`
and setting ``encoding_errors``.  For example, to replace corrupt characters in
character columns:

.. code-block:: python

    def output_type_handler(cursor, metadata):
        if metadata.type_code is oracledb.DB_TYPE_VARCHAR:
            return cursor.var(metadata.type_code, size,
                              arraysize=cursor.arraysize,
                              encoding_errors="replace")

    cursor.outputtypehandler = output_type_handler

    cursor.execute("select column1, column2 from SomeTableWithBadData")

Other codec behaviors can be chosen for ``encoding_errors``, see `Error Handlers
<https://docs.python.org/3/library/codecs.html#error-handlers>`__.

.. _dml:


INSERT and UPDATE Statements
============================

SQL Data Manipulation Language statements (DML) such as INSERT and UPDATE can
easily be executed with python-oracledb.  For example:

.. code-block:: python

    with connection.cursor() as cursor:
      cursor.execute("insert into MyTable values (:idbv, :nmbv)", [1, "Fredico"])

Do not concatenate or interpolate user data into SQL statements.  See
:ref:`bind` instead.

When handling multiple data values, use :meth:`Cursor.executemany()` or
:meth:`Connection.direct_path_load()` for performance. See :ref:`batchstmnt`

By default data is not committed to the database and other users will not be
able to see your changes until your connection commits them by calling
:meth:`Connection.commit()`. You can optionally rollback changes by calling
:meth:`Connection.rollback()`. An implicit rollback will occur if your
application finishes and does not explicitly commit any work.

To commit your changes, call:

.. code-block:: python

    connection.commit()

Note that the commit occurs on the connection, not the cursor.

If the attribute :attr:`Connection.autocommit` is ``True``, then each statement
executed is automatically committed without the need to call
:meth:`Connection.commit()`. However overuse of the attribute causes extra
database load, and can destroy transactional consistency.

See :ref:`txnmgmnt` for best practices on committing and rolling back data
changes.

Inserting NULLs
---------------

Oracle Database requires a type, even for null values. When you pass the value
None, then python-oracledb assumes its type is a string.  If this is not the
desired type, you can explicitly set it.  For example, to insert a null
:ref:`Oracle Spatial SDO_GEOMETRY <spatial>` object:

.. code-block:: python

    type_obj = connection.gettype("SDO_GEOMETRY")
    cursor = connection.cursor()
    cursor.setinputsizes(type_obj)
    cursor.execute("insert into sometable values (:1)", [None])
