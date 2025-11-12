.. _jsondatatype:

.. currentmodule:: oracledb

***************
Using JSON Data
***************

JSON data can be used with relational database features, including
transactions, indexing, declarative querying, and views. You can project JSON
data relationally, making it available for relational processes and
tools. :ref:`JSON-Relational Duality Views <jsondualityviews>` provide the
benefits of the relational model and SQL access, while also allowing read and
write access to data as JSON documents. Also see :ref:`Simple Oracle Document
Access (SODA) <sodausermanual>`, which allows access to JSON documents through
a set of NoSQL-style APIs.

Support for JSON was introduced in Oracle Database 12c. For more information
about using JSON in Oracle Database see the `Database JSON Developer's Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=ADJSN>`__.

Using the Oracle Database JSON Type in python-oracledb
======================================================

Oracle Database 21c introduced a dedicated JSON data type with a new `binary
storage format OSON <https://blogs.oracle.com/jsondb/osonformat>`__ that
improves performance and functionality compared with earlier releases. Both
python-oracledb Thin and Thick modes support the JSON data type.  With Thick
mode, the Oracle Client libraries should be version 21, or later.

To create a table with a column called JSON_DATA for JSON data you might
use:

.. code-block:: sql

    create table CustomersAsJson (
        id integer not null primary key,
        json_data json
    );


With Oracle Database 21c (or later), when using python-oracledb Thin mode or
when using Thick mode with Oracle Client 21c (or later), you can insert JSON
data by binding directly:

.. code-block:: python

    data = dict(name="Sally", dept="Sales", location="France")
    insert_sql = "insert into CustomersAsJson values (:1, :2)"

    # Take advantage of direct binding
    cursor.setinputsizes(None, oracledb.DB_TYPE_JSON)
    cursor.execute(insert_sql, [1, data])

The call to :meth:`Cursor.setinputsizes()` uses None to indicate that the type
for the first bind variable placeholder should be inferred from the data value
(that is, it is numeric), and uses ``oracledb.DB_TYPE_JSON`` to indicate that
the second placeholder in the SQL statement should be bound as a JSON type.

.. _json21fetch:

Fetching a JSON column automatically returns a Python object:

.. code-block:: python

    for row in cursor.execute("select * from CustomersAsJson"):
        print(row)

This gives::

    (1, {'name': 'Sally', 'dept': 'Sales', 'location': 'France'})

See `json_direct.py
<https://github.com/oracle/python-oracledb/tree/main/samples/json_direct.py>`__
for a runnable example.  The example also shows how to use this type when
python-oracledb Thick mode uses older Oracle Client libraries.

Using JSON stored in BLOB, CLOB or VARCHAR2 columns
===================================================

In Oracle Database 12c, or later, JSON can be stored in BLOB, CLOB or VARCHAR2
relational table columns. All of these types can be used with python-oracledb
in Thin or Thick modes. BLOB is preferred to avoid character set conversion
overheads.

The syntax to create a table with a JSON column using BLOB storage is like:

.. code-block:: sql

    create table CustomersAsBlob (
        id integer not null primary key,
        json_data blob check (json_data is json)
    );

The check constraint with the clause ``IS JSON`` ensures only JSON data is
stored in that column.

This older syntax can still be used in Oracle Database 21c (and later).
However the recommendation is to move to the new JSON type.

When using Oracle Database 12c or later with JSON using BLOB storage, you can
insert JSON strings like:

.. code-block:: python

    import json

    data = dict(name="Rod", dept="Sales", location="Germany")
    inssql = "insert into CustomersAsBlob values (:1, :2)"

    cursor.setinputsizes(None, oracledb.DB_TYPE_LONG_RAW)
    cursor.execute(inssql, [1, json.dumps(data)])

You can fetch VARCHAR2 and LOB columns that contain JSON data in the same way
that :ref:`JSON type columns <json21fetch>` are fetched when using Oracle
Database 21c or later. If you are using python-oracledb Thick mode, you must
use Oracle Client 19c (or later). For example:

.. code-block:: python

    for row in cursor.execute("select * from CustomersAsBlob"):
        print(row)

.. versionchanged:: 2.0

    The behavior when fetching JSON data stored in VARCHAR2 and LOB columns
    which have the check constraint ``IS JSON`` changed in python-oracledb
    versions 1.4 and 2.0.

    In python-oracledb 2.0, fetching from these columns in Oracle Database 12c
    (or later) has the same behavior as fetching from a column of type JSON in
    Oracle Database 21c (or later): a Python object is returned
    automatically. You do not need to explicitly invoke ``json.loads()``.

    In python-oracledb 1.4 you could set the attribute
    ``oracledb.__future__.old_json_col_as_obj`` to change how these columns
    were returned. When set to False (its default value), your application
    needed to invoke ``json.loads()`` on the fetched values.  When the
    attribute was True, the data was automatically returned as Python objects.
    The attribute provided a forward migration path to python-oracledb 2.0.

    With all python-oracledb version prior to 1.4 your application always
    needed to call ``json.loads()`` on the returned data.

    The attribute ``oracledb.__future__.old_json_col_as_obj`` was added in
    python-oracledb 1.4 and removed in version 2.0.

See `json_blob.py
<https://github.com/oracle/python-oracledb/tree/main/samples/json_blob.py>`__
for a runnable example.

Using OSON storage
------------------

When using JSON with VARCHAR or LOB storage in databases that support `OSON
<https://blogs.oracle.com/jsondb/osonformat>`__, Oracle's optimized binary JSON
format, you can set this as the storage option:

.. code-block:: sql

     create table mytab (json_data blob check (json_data is json format oson));

To insert into this table, encode the data using
:meth:`Connection.encode_oson()`, and use :meth:`Cursor.setinputsizes()` to
specify that the bind variable placeholder represents JSON:

.. code-block:: python

     data = dict(name="Sally", dept="Sales", location="France")

     oson = connection.encode_oson(data)
     cursor.setinputsizes(oracledb.DB_TYPE_JSON)
     cursor.execute("insert into mytab (json_data) values (:1)", [oson])

When fetching, use :meth:`Connection.decode_json()` to extract the values:

.. code-block:: python

     for (o,) in cursor.execute("select * from mytab"):
         d = connection.decode_oson(o)
         print(d)

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
    * - :ref:`oracledb.IntervalYM <interval_ym>`
      - INTERVAL YEAR TO MONTH
      - json_scalar(to_yminterval('+5-9'))
    * - datetime.timedelta
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
      - :ref:`oracledb.IntervalYM <interval_ym>`
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

For example, the previously created CUSTOMERS table with JSON column
JSON_DATA can be queried like:

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

In Oracle Database 12.2 or later, the `JSON_OBJECT <https://www.oracle.com/pls/
topic/lookup?ctx=dblatest&id=GUID-1EF347AE-7FDA-4B41-AFE0-DD5A49E8B370>`__
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

    cursor.execute("""
        select
            json_arrayagg(
                json_object('deptid' is d.department_id,
                            'name' is d.department_name) returning clob)
        from
            departments d
        where
            department_id < :did""",
       [50],
       fetch_lobs=False)
    j, = cursor.fetchone()
    print(j)


This produces::

    [{"deptid":10,"name":"Administration"},{"deptid":20,"name":"Marketing"},{"deptid":30,"name":"Purchasing"},{"deptid":40,"name":"Human Resources"}]

.. _jsondualityviews:

JSON-Relational Duality Views
=============================

Oracle AI Database 26ai JSON-Relational Duality Views allow data to be
stored as rows in tables to provide the benefits of the relational model and
SQL access, while also allowing read and write access to data as JSON documents
for application simplicity. See the `JSON-Relational Duality Developer's Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=JSNVU>`__ for more
information.

For example, if the tables ``AuthorTab`` and ``BookTab`` exist::

    create table AuthorTab (
        AuthorId number generated by default on null as identity primary key,
        AuthorName varchar2(100)
    );

    create table BookTab (
        BookId number generated by default on null as identity primary key,
        BookTitle varchar2(100),
        AuthorId number references AuthorTab (AuthorId)
    );

Then a JSON Duality View over the tables could be created in SQL*Plus::

    create or replace json relational duality view BookDV as
    BookTab @insert @update @delete
    {
        _id: BookId,
        book_title: BookTitle,
        author: AuthorTab @insert @update
        {
            author_id: AuthorId,
            author_name: AuthorName
        }
    };

Applications can choose whether to use relational access to the underlying
tables, or use the duality view.

You can use SQL/JSON to query the view and return JSON. The query uses the
special column DATA:

.. code-block:: python

    sql = """select b.data.book_title, b.data.author.author_name
             from BookDV b
             where b.data.author.author_id = :1"""
    for r in cursor.execute(sql, [1]):
        print(r)

Inserting JSON into the view will update the base relational tables:

.. code-block:: python

    data = dict(_id=1000, book_title="My New Book",
                author=dict(author_id=2000, author_name="John Doe"))
    cursor.setinputsizes(oracledb.DB_TYPE_JSON)
    cursor.execute("insert into BookDV values (:1)", [data])

See `json_duality.py
<https://github.com/oracle/python-oracledb/tree/main/samples/json_duality.py>`__
for a runnable example.

.. _sodadv:

You can also access a duality view directly using :ref:`SODA <sodausermanual>`
NoSQL-style document APIs by opening the view as if it were a SODA
collection. For example, to run a query-by-example on book titles:

.. code-block:: python

    soda = connection.getSodaDatabase()
    collection = soda.openCollection('BOOKDV')

    qbe = {'book_title': {'$like': 'The%'}}
    for doc in collection.find().filter(qbe).getDocuments():
        content = doc.getContent()
        print(content["book_title"])


See `soda_json_duality.py
<https://github.com/oracle/python-oracledb/tree/main/samples/soda_json_duality.py>`__
for a runnable example.
