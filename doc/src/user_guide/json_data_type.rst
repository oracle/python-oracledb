.. _jsondatatype:

***************
Using JSON Data
***************

Native support for JavaScript Object Notation (JSON) data was introduced in
Oracle Database 12c.  You can use JSON with relational database features,
including transactions, indexing, declarative querying, and views.  You can
project JSON data relationally, making it available for relational processes
and tools.  Also see :ref:`Simple Oracle Document Access (SODA) <sodausermanual>`,
which allows access to JSON documents through a set of NoSQL-style APIs.

For more information about using JSON in Oracle Database see the `Database JSON
Developer's Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=ADJSN>`__.

**Oracle Database 12c JSON Data Type**

In Oracle Database 12c, JSON in relational tables is stored as BLOB, CLOB or
VARCHAR2 data.  All of these types can be used with python-oracledb in Thin or
Thick modes.

The older syntax to create a table with a JSON column is like:

.. code-block:: sql

    create table CustomersAsBlob (
        id integer not null primary key,
        json_data blob check (json_data is json)
    );

The check constraint with the clause ``IS JSON`` ensures only JSON data is
stored in that column.

The older syntax can still be used in Oracle Database 21c; however, the
recommendation is to move to the new JSON type.  With the old syntax, the
storage can be BLOB, CLOB, or VARCHAR2.  Of these, BLOB is preferred to avoid
character set conversion overheads.

**Oracle Database 21c JSON Data Type**

Oracle Database 21c introduced a dedicated JSON data type with a new `binary
storage format <https://blogs.oracle.com/jsondb/osonformat>`__ that improves
performance and functionality.  To fully take advantage of the dedicated JSON
type, use python-oracledb in Thick mode with Oracle Client libraries version
21, or later.

In Oracle Database 21, to create a table with a column called ``JSON_DATA`` for
JSON data you might use:

.. code-block:: sql

    create table CustomersAsJson (
        id integer not null primary key,
        json_data json
    );


Using the Oracle Database 21c JSON Type in python-oracledb Thick Mode
=====================================================================

Using python-oracledb Thick mode with Oracle Database 21c and Oracle Client 21c
(or later), you can insert by binding as shown below:

.. code-block:: python

    data = [
      (5, dict(name="Sally", dept="Sales", location="France")),
    ]
    insert_sql = "insert into CustomersAsJson values (:1, :2)"

    # Take advantage of direct binding
    cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
    cursor.execute(insert_sql, [1, data])

To fetch a JSON column, use:

.. code-block:: python

    for row in cursor.execute("select * from CustomersAsJson"):
        print(row)

See `json_direct.py
<https://github.com/oracle/python-oracledb/tree/main/samplesjson_direct.py>`__
for a runnable example.  The example also shows how to use this type when
python-oracledb Thick mode uses older Oracle Client libraries.

Using the Oracle Database 21c JSON Type and python-oracledb Thin Mode
=====================================================================

Using python-oracledb Thin mode with Oracle Database 21c, you can insert into a
JSON column as shown below:

.. code:: python

    data = [
      (1, dict(name="Rod", dept="Sales", location="Germany")),
      (2, dict(name="George", dept="Marketing", location="Bangalore")),
      (3, dict(name="Sam", dept="Sales", location="Mumbai")),
      (4, dict(name="Jill", dept="Marketing", location="Germany"))
    ]

    insert_sql = "insert into CustomersAsJson values (:1, :2)"

    # Insert the data as a JSON string
    cursor.executemany(insert_sql, [(i, json.dumps(j)) for i, j in data])

For python-oracledb Thin mode, a type handler is required to fetch the Oracle
21c JSON datatype.  If a type handler is used in the python-oracledb Thick
mode, then the behavior is same in both the python-oracledb modes. The
following example shows a type handler:

.. code-block:: python

    def my_type_handler(cursor, name, default_type, size, precision, scale):
        if default_type == oracledb.DB_TYPE_JSON:
            return cursor.var(str, arraysize=cursor.arraysize, outconverter=json.loads)

    cursor.outputtypehandler = my_type_handler

    for row in cursor.execute("select * from CustomersAsJson"):
        print(row)

With a type handler, the python-oracledb Thin mode is equivalent
to using the python-oracledb Thick mode with Oracle Client 21c. The
python-oracledb Thin mode returns timestamps in a string representation.
Without a type handler, the python-oracledb Thin mode gives an error that
``DB_TYPE_JSON`` is not supported.

A type handler is not needed when fetching from the Oracle Database 19c JSON
type, since this is represented as VARCHAR2 or LOB.

See `json_type.py
<https://github.com/oracle/python-oracledb/tree/main/samplesjson_type.py>`__
for a runnable example.

Using the Oracle 12c JSON type in python-oracledb
=================================================

When using Oracle Database 12c or later with JSON using BLOB storage to insert
JSON strings, use:

.. code-block:: python

    data = dict(name="Rod", dept="Sales", location="Germany")
    inssql = "insert into CustomersAsBlob values (:1, :2)"

    cursor.execute(inssql, [1, json.dumps(data)])

To fetch JSON strings, use:

.. code-block:: python

    import json

    sql = "SELECT c.json_data FROM CustomersAsBlob c"
    for j, in cursor.execute(sql):
        print(json.loads(j.read()))

See `json_blob.py
<https://github.com/oracle/python-oracledb/tree/main/samplesjson_blob.py>`__
for a runnable example.

IN Bind Type Mapping
====================

When binding to a JSON value, the ``type`` parameter for the variable must be
specified as :data:`oracledb.DB_TYPE_JSON`. Python values are converted to
JSON values as shown in the following table.  The 'SQL Equivalent' syntax can
be used in SQL INSERT and UPDATE statements if specific attribute types are
needed but there is no direct mapping from Python.

.. list-table-with-summary::
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 1 1 1
    :summary: The first column is the Python Type or Value. The second column is the equivalent JSON Attribute Type or Value. The third column is the SQL Equivalent syntax.
    :align: left

    * - Python Type or Value
      - JSON Attribute Type or Value
      - SQL Equivalent Example
    * - None
      - null
      - NULL
    * - True
      - true
      - n/a
    * - False
      - false
      - n/a
    * - int
      - NUMBER
      - json_scalar(1)
    * - float
      - NUMBER
      - json_scalar(1)
    * - decimal.Decimal
      - NUMBER
      - json_scalar(1)
    * - str
      - VARCHAR2
      - json_scalar('String')
    * - datetime.date
      - TIMESTAMP
      - json_scalar(to_timestamp('2020-03-10', 'YYYY-MM-DD'))
    * - datetime.datetime
      - TIMESTAMP
      - json_scalar(to_timestamp('2020-03-10', 'YYYY-MM-DD'))
    * - bytes
      - RAW
      - json_scalar(utl_raw.cast_to_raw('A raw value'))
    * - list
      - Array
      - json_array(1, 2, 3 returning json)
    * - dict
      - Object
      - json_object(key 'Fred' value json_scalar(5), key 'George' value json_scalar('A string') returning json)
    * - n/a
      - CLOB
      - json_scalar(to_clob('A short CLOB'))
    * - n/a
      - BLOB
      - json_scalar(to_blob(utl_raw.cast_to_raw('A short BLOB')))
    * - n/a
      - DATE
      - json_scalar(to_date('2020-03-10', 'YYYY-MM-DD'))
    * - n/a
      - INTERVAL YEAR TO MONTH
      - json_scalar(to_yminterval('+5-9'))
    * - n/a
      - INTERVAL DAY TO SECOND
      - json_scalar(to_dsinterval('P25DT8H25M'))
    * - n/a
      - BINARY_DOUBLE
      - json_scalar(to_binary_double(25))
    * - n/a
      - BINARY_FLOAT
      - json_scalar(to_binary_float(15.5))

An example of creating a CLOB attribute with key ``mydocument`` in a JSON column
using SQL is:

.. code-block:: python

    cursor.execute("""
            insert into mytab (myjsoncol) values
            (json_object(key 'mydocument' value json_scalar(to_clob(:b))
                    returning json))""",
            ['A short CLOB'])

When `mytab` is queried in python-oracledb, the CLOB data will be returned as a
Python string, as shown by the following table.  Output might be like::

    {mydocument: 'A short CLOB'}


Query and OUT Bind Type Mapping
===============================

When getting Oracle Database 21 JSON values from the database, the following
attribute mapping occurs:

.. list-table-with-summary::
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 1 1
    :align: left
    :summary: The first column is the Database JSON Attribute Type or Value. The second column is the corresponding Python Type or Value mapped.


    * - Database JSON Attribute Type or Value
      - Python Type or Value
    * - null
      - None
    * - false
      - False
    * - true
      - True
    * - NUMBER
      - decimal.Decimal
    * - VARCHAR2
      - str
    * - RAW
      - bytes
    * - CLOB
      - str
    * - BLOB
      - bytes
    * - DATE
      - datetime.datetime
    * - TIMESTAMP
      - datetime.datetime
    * - INTERVAL YEAR TO MONTH
      - not supported
    * - INTERVAL DAY TO SECOND
      - datetime.timedelta
    * - BINARY_DOUBLE
      - float
    * - BINARY_FLOAT
      - float
    * - Arrays
      - list
    * - Objects
      - dict

SQL/JSON Path Expressions
=========================

Oracle Database provides SQL access to JSON data using SQL/JSON path
expressions.  A path expression selects zero or more JSON values that match, or
satisfy, it.  Path expressions can use wildcards and array ranges.  A simple
path expression is ``$.friends`` which is the value of the JSON field
``friends``.

For example, the previously created ``customers`` table with JSON column
``json_data`` can be queried like:

.. code-block:: sql

    select c.json_data.location FROM customers c

With the JSON ``'{"name":"Rod","dept":"Sales","location":"Germany"}'`` stored
in the table, the queried value would be ``Germany``.

The JSON_EXISTS functions tests for the existence of a particular value within
some JSON data.  To look for JSON entries that have a ``location`` field:

.. code-block:: python

    for blob, in cursor.execute("""
            select json_data
            from customers
            where json_exists(json_data, '$.location')"""):
        data = json.loads(blob.read())
        print(data)

This query might display::

    {'name': 'Rod', 'dept': 'Sales', 'location': 'Germany'}

The SQL/JSON functions ``JSON_VALUE`` and ``JSON_QUERY`` can also be used.

Note that the default error-handling behavior for these functions is
``NULL ON ERROR``, which means that no value is returned if an error occurs.
To ensure that an error is raised, use ``ERROR ON ERROR``.

For more information, see `SQL/JSON Path Expressions
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-2DC05D71-3D62-4A14-855F-76E054032494>`__
in the Oracle JSON Developer's Guide.


Accessing Relational Data as JSON
=================================

In Oracle Database 12.2 or later, the `JSON_OBJECT
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-1EF347AE-7FDA-4B41-AFE0-DD5A49E8B370>`__
function is a great way to convert relational table data to JSON:

.. code-block:: python

    cursor.execute("""
            select json_object('deptId' is d.department_id, 'name' is d.department_name) department
            from departments d
            where department_id < :did
            order by d.department_id""",
            [50]);
    for row in cursor:
        print(row)

This produces::

    ('{"deptId":10,"name":"Administration"}',)
    ('{"deptId":20,"name":"Marketing"}',)
    ('{"deptId":30,"name":"Purchasing"}',)
    ('{"deptId":40,"name":"Human Resources"}',)
