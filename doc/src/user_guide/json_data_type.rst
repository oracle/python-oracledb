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

**Oracle Database 21c JSON Data Type**

Oracle Database 21c introduced a dedicated JSON data type with a new `binary
storage format <https://blogs.oracle.com/jsondb/osonformat>`__ that improves
performance and functionality compared with earlier releases.  To take
advantage of the dedicated JSON type with Oracle Database 21c, or later, you
can use python-oracledb in Thin or Thick modes.  With Thick mode the Oracle
Client libraries should be version 21, or later.

To create a table with a column called ``JSON_DATA`` for JSON data you might
use:

.. code-block:: sql

    create table CustomersAsJson (
        id integer not null primary key,
        json_data json
    );


**Oracle Database 12c JSON Data Type**

In Oracle Database 12c, or later, JSON in relational tables can be stored as
BLOB, CLOB or VARCHAR2 data.  All of these types can be used with
python-oracledb in Thin or Thick modes.  BLOB is preferred to avoid character
set conversion overheads.

The syntax to create a table with a JSON column using BLOB storage is like:

.. code-block:: sql

    create table CustomersAsBlob (
        id integer not null primary key,
        json_data blob check (json_data is json)
    );

The check constraint with the clause ``IS JSON`` ensures only JSON data is
stored in that column.

This older syntax can still be used in Oracle Database 21c (and later);
however, the recommendation is to move to the new JSON type.

Using the Oracle Database 21c JSON Type in python-oracledb
==========================================================

Using python-oracledb Thin mode with Oracle Database 21c, or using Thick mode
with Oracle Database 21c and Oracle Client 21c (or later), you can insert by
binding as shown below:

.. code-block:: python

    data = [
      (5, dict(name="Sally", dept="Sales", location="France")),
    ]
    insert_sql = "insert into CustomersAsJson values (:1, :2)"

    # Take advantage of direct binding
    cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
    cursor.execute(insert_sql, [1, data])

.. _json21fetch:

To fetch a JSON column, use:

.. code-block:: python

    for row in cursor.execute("select * from CustomersAsJson"):
        print(row)

See `json_direct.py
<https://github.com/oracle/python-oracledb/tree/main/samples/json_direct.py>`__
for a runnable example.  The example also shows how to use this type when
python-oracledb Thick mode uses older Oracle Client libraries.

Using the Oracle 12c JSON type in python-oracledb
=================================================

When using Oracle Database 12c or later with JSON using BLOB storage, you can
insert JSON strings like:

.. code-block:: python

    import json

    data = dict(name="Rod", dept="Sales", location="Germany")
    inssql = "insert into CustomersAsBlob values (:1, :2)"

    cursor.execute(inssql, [1, json.dumps(data)])

You can fetch VARCHAR2 and LOB columns that contain JSON data in the same way
that :ref:`JSON type columns <json21fetch>` are fetched when using Oracle
Database 21c or later. If you are using python-oracledb Thick mode, you must
use Oracle Client 19c (or later). For example:

.. code-block:: python

    for row in cursor.execute("select * from CustomersAsBlob"):
        print(row)

.. versionchanged:: 2.0

    Previously, the ``oracledb.__future__.old_json_col_as_obj`` attribute
    needed to be set to *True* to fetch VARCHAR2 and LOB columns that
    contained JSON data. Also, you could fetch JSON data without setting this
    attribute with a call to ``json.loads()`` on the returned data. With this
    change, the ``oracledb.__future__.old_json_col_as_obj`` attribute is
    desupported. VARCHAR2 and LOB columns containing JSON data can now be
    fetched directly without setting the
    ``oracledb.__future__.old_json_col_as_obj`` attribute or without needing
    to call ``json.loads()`` on the value.

See `json_blob.py
<https://github.com/oracle/python-oracledb/tree/main/samples/json_blob.py>`__
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
        insert into mytab (
            myjsoncol
        ) values (
            json_object(key 'mydocument' value json_scalar(to_clob(:b)) returning json)
        )""",
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

    import json

    for blob, in cursor.execute("""
        select
            json_data
        from
            customers
        where
            json_exists(json_data,
            '$.location')"""):
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
        select
            json_object('deptId' is d.department_id,
                        'name' is d.department_name) department
        from
            departments d
        where
            department_id < :did
        order by
            d.department_id""",
            [50]);
    for row in cursor:
        print(row)

This produces::

    ('{"deptId":10,"name":"Administration"}',)
    ('{"deptId":20,"name":"Marketing"}',)
    ('{"deptId":30,"name":"Purchasing"}',)
    ('{"deptId":40,"name":"Human Resources"}',)

To select a result set from a relational query as a single object you can use
`JSON_ARRAYAGG
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-6D56077D-78DE-4CC0-9498-225DDC42E054>`__,
for example:

.. code-block:: python

    oracledb.defaults.fetch_lobs = False

    cursor.execute("""
        select
            json_arrayagg(
                json_object('deptid' is d.department_id,
                            'name' is d.department_name) returning clob)
        from
            departments d
        where
            department_id < :did""",
       [50]);
    j, = cursor.fetchone()
    print(j)


This produces::

    [{"deptid":10,"name":"Administration"},{"deptid":20,"name":"Marketing"},{"deptid":30,"name":"Purchasing"},{"deptid":40,"name":"Human Resources"}]
