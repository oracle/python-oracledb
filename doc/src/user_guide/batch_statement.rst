.. _batchstmnt:

.. currentmodule:: oracledb

****************************************
Batch Statement and Bulk Copy Operations
****************************************

Python-oracledb is perfect for large ETL ("Extract, Transform, Load") data
operations.

This chapter focuses on efficient data ingestion. Python-oracledb lets you
easily optimize batch insertion, and also allows "noisy" data (values not in a
suitable format) to be filtered for review while other, correct, values are
inserted.

In addition to Oracle Database "Array DML" batch loading,
:ref:`directpathloads` can be used for very fast loading of large data sets if
certain schema criteria can be met. Another option for frequent, small inserts
is to load data using the Oracle Database :ref:`memoptimized`.

Related topics include :ref:`tuning` and :ref:`dataframeformat`.

Batch Statement Execution
=========================

Inserting, updating or deleting multiple rows can be performed efficiently with
:meth:`Cursor.executemany()`, making it easy to work with large data sets with
python-oracledb.  This method can significantly outperform repeated calls to
:meth:`Cursor.execute()` by reducing network transfer costs and database
overheads.  The :meth:`~Cursor.executemany()` method can also be used to
execute a PL/SQL statement multiple times in one call.

There are examples in the `GitHub examples
<https://github.com/oracle/python-oracledb/tree/main/samples>`__
directory.

The following tables will be used in the samples that follow:

.. code-block:: sql

    create table ParentTable (
        ParentId              number(9) not null,
        Description           varchar2(60) not null,
        constraint ParentTable_pk primary key (ParentId)
    );

    create table ChildTable (
        ChildId               number(9) not null,
        ParentId              number(9) not null,
        Description           varchar2(60) not null,
        constraint ChildTable_pk primary key (ChildId),
        constraint ChildTable_fk foreign key (ParentId)
                references ParentTable
    );


Batch Execution of SQL
----------------------

The following example inserts five rows into the table ``ParentTable``:

.. code-block:: python

    data = [
        (10, "Parent 10"),
        (20, "Parent 20"),
        (30, "Parent 30"),
        (40, "Parent 40"),
        (50, "Parent 50")
    ]
    cursor.executemany("insert into ParentTable values (:1, :2)", data)

Each tuple value maps to one of the bind variable placeholders.

This code requires only one :ref:`round-trip <roundtrips>` from the client to
the database instead of the five round-trips that would be required for
repeated calls to :meth:`~Cursor.execute()`.

To insert a single column, make sure the bind variables are correctly created
as tuples, for example:

.. code-block:: python

    data = [
        (10,),
        (20,),
        (30,),
    ]
    cursor.executemany('insert into mytable (mycol) values (:1)', data)

Named binds can be performed by passing an array of dicts, where the keys match
the bind variable placeholder names:

.. code-block:: python

    data = [
        {"pid": 10, "pdesc": "Parent 10"},
        {"pid": 20, "pdesc": "Parent 20"},
        {"pid": 30, "pdesc": "Parent 30"},
        {"pid": 40, "pdesc": "Parent 40"},
        {"pid": 50, "pdesc": "Parent 50"}
    ]
    cursor.executemany("insert into ParentTable values :pid, :pdesc)", data)


A data frame can alternatively be passed to :meth:`Cursor.executemany()`, see
:ref:`dfinsert`.

.. _predefmemory:

Predefining Memory Areas
------------------------

When multiple rows of data are being processed there is the possibility that
the data is not uniform in type and size.  In such cases, python-oracledb makes
some effort to accommodate such differences.  Type determination for each
column is deferred until a value that is not ``None`` is found in the column's
data.  If all values in a particular column are ``None``, then python-oracledb
assumes the type is a string and has a length of 1.  Python-oracledb will also
adjust the size of the buffers used to store strings and bytes when a longer
value is encountered in the data.  These sorts of operations incur overhead as
memory has to be reallocated and data copied.  To eliminate this overhead,
using :meth:`~Cursor.setinputsizes()` tells python-oracledb about the type and
size of the data that is going to be used.

Consider the following code:

.. code-block:: python

    data = [
        (110, "Parent 110"),
        (2000, "Parent 2000"),
        (30000, "Parent 30000"),
        (400000, "Parent 400000"),
        (5000000, "Parent 5000000")
    ]
    cursor.setinputsizes(None, 20)
    cursor.executemany("""
            insert into ParentTable (ParentId, Description)
            values (:1, :2)""", data)

If this example did not call :meth:`~Cursor.setinputsizes()`, then
python-oracledb performs five allocations of increasing size and perform
data copies as it discovers each new, longer string.  However,
``cursor.setinputsizes(None, 20)`` tells python-oracledb that the maximum size
of the strings that will be processed is 20 characters.  The first parameter of
``None`` tells python-oracledb that its default processing will be sufficient
since numeric data is already stored efficiently.  Since python-oracledb
allocates memory for each row based on the supplied values, do not oversize
them.

If the size of the buffers allocated for any of the bind values exceeds 2 GB,
you will receive the error ``DPI-1015: array size of <n> is too large``, where
<n> varies with the size of each element being allocated in the buffer. If you
receive this error, decrease the number of rows being inserted.

With named bind variables, use named parameters when calling
:meth:`~Cursor.setinputsizes()`:

.. code-block:: python

    data = [
        {"pid": 110, "pdesc": "Parent 110"},
        {"pid": 2000, "pdesc": "Parent 2000"},
        {"pid": 30000, "pdesc": "Parent 30000"},
        {"pid": 400000, "pdesc": "Parent 400000"},
        {"pid": 5000000, "pdesc": "Parent 5000000"}
    ]
    cursor.setinputsizes(pdesc=20)
    cursor.executemany("""
            insert into ParentTable (ParentId, Description)
            values (:pid, :pdesc)""", data)


Batching of Large Datasets
--------------------------

For very large data sets, there may be a buffer or network limit on how many
rows can be processed. The limit is based on both the number of records as
well as the size of each record that is being processed. In other cases, it may
be faster to process smaller sets of records.

To reduce the data sizes involved, you can either make repeated calls to
:meth:`~Cursor.executemany()` as shown later in the CSV examples, or you can
use the ``batch_size`` parameter to optimize transfer across the network to the
database. For example:

.. code-block:: python

    data = [
        (1, "Parent 1"),
        (2, "Parent 2"),
        . . .
        (9_999_999, "Parent 9,999,999"),
        (10_000_000, "Parent 10,000,000"),

    ]

    cursor.executemany("insert into ParentTable values (:1, :2)", data, batch_size=200_000)

This will send the data to the database in batches of 200,000 records until all
10,000,000 records have been inserted.

If :attr:`Connection.autocommit` is ``True``, then a commit will take place per
batch of records processed.

.. _batchplsql:

Batch Execution of PL/SQL
-------------------------

Using :meth:`~Cursor.executemany()` can improve performance when PL/SQL
functions, procedures, or anonymous blocks need to be called multiple times.

Runnable examples are in `plsql_batch.py <https://github.com/oracle/python-
oracledb/tree/main/samples/plsql_batch.py>`__.

**IN Binds**

An example using :ref:`bind by position <bindbyposition>` for IN binds is:

.. code-block:: python

    data = [
        (10, "Parent 10"),
        (20, "Parent 20"),
        (30, "Parent 30"),
        (40, "Parent 40"),
        (50, "Parent 50")
    ]
    cursor.executemany("begin mypkg.create_parent(:1, :2); end;", data)

Note that the ``batcherrors`` parameter of :meth:`~Cursor.executemany()`
(discussed in :ref:`batcherrors`) cannot be used with PL/SQL block execution.

**OUT Binds**

When using OUT binds in PL/SQL, the input data omits entries for the OUT bind
variable placeholders. An example PL/SQL procedure that returns OUT binds is:

.. code-block:: sql

    create or replace procedure myproc(p1 in number, p2 out number) as
    begin
        p2 := p1 * 2;
    end;

This can be called in python-oracledb using positional binds like:

.. code-block:: python

    data = [
        (100,),
        (200,),
        (300,)
    ]

    outvals = cursor.var(oracledb.DB_TYPE_NUMBER, arraysize=len(data))
    cursor.setinputsizes(None, outvals)

    cursor.executemany("begin myproc(:1, :2); end;", data)
    print(outvals.values)

The output is::

    [200, 400, 600]

The equivalent code using named binds is:

.. code-block:: python

    data = [
        {"p1bv": 100},
        {"p1bv": 200},
        {"p1bv": 300}
    ]

    outvals = cursor.var(oracledb.DB_TYPE_NUMBER, arraysize=len(data))
    cursor.setinputsizes(p1bv=None, p2bv=outvals)

    cursor.executemany("begin myproc(:p1bv, :p2bv); end;", data)
    print(outvals.values)

Note that in python-oracledb Thick mode, when :meth:`~Cursor.executemany()` is
used for PL/SQL code that returns OUT binds, it will have the same performance
characteristics as repeated calls to :meth:`~Cursor.execute()`.

**IN/OUT Binds**

An example PL/SQL procedure that returns IN/OUT binds is:

.. code-block:: sql

    create or replace procedure myproc2 (p1 in number, p2 in out varchar2) as
    begin
        p2 := p2 || ' ' || p1;
    end;

This can be called in python-oracledb using positional binds like:

.. code-block:: python

    data = [
        (440, 'Gregory'),
        (550, 'Haley'),
        (660, 'Ian')
    ]
    outvals = cursor.var(oracledb.DB_TYPE_VARCHAR, size=100, arraysize=len(data))
    cursor.setinputsizes(None, outvals)

    cursor.executemany("begin myproc2(:1, :2); end;", data)
    print(outvals.values)

The ``size`` parameter of :meth:`Cursor.var()` indicates the maximum length of
the string that can be returned.

Output is::

    ['Gregory 440', 'Haley 550', 'Ian 660']

The equivalent code using named binds is:

.. code-block:: python

    data = [
        {"p1bv": 440, "p2bv": 'Gregory'},
        {"p1bv": 550, "p2bv": 'Haley'},
        {"p1bv": 660, "p2bv": 'Ian'}
    ]
    outvals = cursor.var(oracledb.DB_TYPE_VARCHAR, size=100, arraysize=len(data))
    cursor.setinputsizes(p1bv=None, p2bv=outvals)

    cursor.executemany("begin myproc2(:p1bv, :p2bv); end;", data)
    print(outvals.values)

.. _batcherrors:

Handling Data Errors
--------------------

Large datasets may contain some invalid data.  When using batch execution as
discussed above, the entire batch will be discarded if a single error is
detected, potentially eliminating the performance benefits of batch execution
and increasing the complexity of the code required to handle those errors. If
the parameter ``batchErrors`` is set to the value ``True`` when calling
:meth:`~Cursor.executemany()`, however, processing will continue even if there
are data errors in some rows, and the rows containing errors can be examined
afterwards to determine what course the application should take. Note that if
any errors are detected, a transaction will be started but not committed, even
if :attr:`Connection.autocommit` is set to ``True``. After examining the errors
and deciding what to do with them, the application needs to explicitly commit
or roll back the transaction with :meth:`Connection.commit()` or
:meth:`Connection.rollback()`, as needed.

This example shows how data errors can be identified:

.. code-block:: python

    data = [
        (60, "Parent 60"),
        (70, "Parent 70"),
        (70, "Parent 70 (duplicate)"),
        (80, "Parent 80"),
        (80, "Parent 80 (duplicate)"),
        (90, "Parent 90")
    ]
    cursor.executemany("insert into ParentTable values (:1, :2)", data,
                       batcherrors=True)
    for error in cursor.getbatcherrors():
        print("Error", error.message, "at row offset", error.offset)

The output is::

    Error ORA-00001: unique constraint (PYTHONDEMO.PARENTTABLE_PK) violated at row offset 2
    Error ORA-00001: unique constraint (PYTHONDEMO.PARENTTABLE_PK) violated at row offset 4

The row offset is the index into the array of the data that could not be
inserted due to errors.  The application could choose to commit or rollback the
other rows that were successfully inserted.  Alternatively, it could correct
the data for the two invalid rows and attempt to insert them again before
committing.


Identifying Affected Rows
-------------------------

When executing a DML statement using :meth:`~Cursor.execute()`, the number of
rows affected can be examined by looking at the attribute
:attr:`~Cursor.rowcount`. When performing batch execution with
:meth:`Cursor.executemany()`, the row count will return the *total*
number of rows that were affected. If you want to know the total number of rows
affected by each row of data that is bound you must set the parameter
``arraydmlrowcounts`` to ``True``, as shown:

.. code-block:: python

    parent_ids_to_delete = [20, 30, 50]
    cursor.executemany("delete from ChildTable where ParentId = :1",
                       [(i,) for i in parent_ids_to_delete],
                       arraydmlrowcounts=True)
    row_counts = cursor.getarraydmlrowcounts()
    for parent_id, count in zip(parent_ids_to_delete, row_counts):
        print("Parent ID:", parent_id, "deleted", count, "rows.")

Using the data found in the `GitHub samples
<https://github.com/oracle/python-oracledb/tree/main/samples>`__ the output
is as follows::

    Parent ID: 20 deleted 3 rows.
    Parent ID: 30 deleted 2 rows.
    Parent ID: 50 deleted 4 rows.


DML RETURNING
-------------

DML statements like INSERT, UPDATE, DELETE, and MERGE can return values by using
the DML RETURNING syntax. A bind variable can be created to accept this data.
See :ref:`bind` for more information.

If, instead of merely deleting the rows as shown in the previous example, you
also wanted to know some information about each of the rows that were deleted,
you can use the following code:

.. code-block:: python

    parent_ids_to_delete = [20, 30, 50]
    child_id_var = cursor.var(int, arraysize=len(parent_ids_to_delete))
    cursor.setinputsizes(None, child_id_var)
    cursor.executemany("""
            delete from ChildTable
            where ParentId = :1
            returning ChildId into :2""",
            [(i,) for i in parent_ids_to_delete])
    for ix, parent_id in enumerate(parent_ids_to_delete):
        print("Child IDs deleted for parent ID", parent_id, "are",
              child_id_var.getvalue(ix))

The output will be::

    Child IDs deleted for parent ID 20 are [1002, 1003, 1004]
    Child IDs deleted for parent ID 30 are [1005, 1006]
    Child IDs deleted for parent ID 50 are [1012, 1013, 1014, 1015]

Note that the bind variable created to accept the returned data must have an
arraysize large enough to hold data for each row that is processed. Also, the
call to :meth:`Cursor.setinputsizes()` binds this variable immediately so that
it does not have to be passed in each row of data.

Bulk Copy Operations
====================

Bulk copy operations are facilitated with the use of
:meth:`Cursor.executemany()`, the use of appropriate SQL statements, and the
use of Python modules.

Also, see :ref:`dataframeformat` and :ref:`Oracle Database Pipelining
<pipelining>`.

Loading CSV Files into Oracle Database
--------------------------------------

The :meth:`Cursor.executemany()` method and Python's `csv module
<https://docs.python.org/3/library/csv.html#module-csv>`__ can be used to
efficiently insert CSV (Comma Separated Values) data.  For example, consider
the file ``data.csv``::

    101,Abel
    154,Baker
    132,Charlie
    199,Delta
    . . .

And the schema:

.. code-block:: sql

    create table test (id number, name varchar2(25));

Data loading can be done in batches of records since Python memory limitations
may prevent all the records being held in memory at once:

.. code-block:: python

    import oracledb
    import csv

    # CSV file
    FILE_NAME = 'data.csv'

    # Adjust the number of rows to be inserted in each iteration
    # to meet your memory and performance requirements
    BATCH_SIZE = 10000

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb")

    with connection.cursor() as cursor:

        # Predefine the memory areas to match the table definition.
        # This can improve performance by avoiding memory reallocations.
        # Here, one parameter is passed for each of the columns.
        # "None" is used for the ID column, since the size of NUMBER isn't
        # variable.  The "25" matches the maximum expected data size for the
        # NAME column
        cursor.setinputsizes(None, 25)

        with open(FILE_NAME, 'r') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            sql = "insert into test (id, name) values (:1, :2)"
            data = []
            for line in csv_reader:
                data.append((line[0], line[1]))
                if len(data) % BATCH_SIZE == 0:
                    cursor.executemany(sql, data)
                    data = []
            if data:
                cursor.executemany(sql, data)
            connection.commit()

Depending on data sizes and business requirements, database changes such as
temporarily disabling redo logging on the table, or disabling indexes may also
be beneficial.

The PyArrow package's CSV methods may be more efficient than the default CSV
module.

See `samples/load_csv.py <https://github.com/oracle/python-oracledb/tree/main/
samples/load_csv.py>`__ for a runnable example showing both the CSV module and
PyArrow's CSV functionality.

You should also review whether Oracle's specialized data loading tools and
features suit your environment. These can be faster than using Python. See
`SQL*Loader <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-DD843EE2-1FAB-4E72-A115-21D97A501ECC>`__ and `External Tables
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-44323E01-7D72-45EC-915A-99E596769D9E>`__.


Creating CSV Files from Oracle Database
---------------------------------------

Python's `csv module <https://docs.python.org/3/library/csv.html#module-csv>`__
can be used to efficiently create CSV (Comma Separated Values) files.  For
example:

.. code-block:: python

    cursor.arraysize = 1000  # tune this for large queries
    print(f"Writing to {FILE_NAME}")
    with open(FILE_NAME, "w") as f:
        writer = csv.writer(
            f, lineterminator="\n", quoting=csv.QUOTE_NONNUMERIC
        )
        cursor.execute("""select rownum, sysdate, mycol from BigTab""")
        writer.writerow(info.name for info in cursor.description)
        writer.writerows(cursor)


See `samples/write_csv.py <https://github.com/oracle/python-oracledb/tree/main/
samples/write_csv.py>`__ for a runnable example.


Bulk Copying Data between Databases
-----------------------------------

The :meth:`Cursor.executemany()` function is useful for copying data from one
database to another, for example in an ETL ("Extract, Transform, Load")
workflow:

.. code-block:: python

    # Connect to both databases
    source_connection = oracledb.connect(user=un1, password=pw1, dsn=cs1)
    target_connection = oracledb.connect(user=un2, password=pw2, dsn=cs2)

    # Setup cursors
    source_cursor = source_connection.cursor()
    source_cursor.arraysize = 1000              # tune this for query performance

    target_cursor = target_connection.cursor()
    target_cursor.setinputsizes(None, 25)       # set according to column types

    # Perform bulk fetch and insertion
    source_cursor.execute("select c1, c2 from MySrcTable")
    while True:

        # Extract the records
        rows = source_cursor.fetchmany()
        if not rows:
            break

        # Optionally transform the records here
        # ...

        # Load the records into the target database
        target_cursor.executemany("insert into MyDestTable values (:1, :2)", rows)

    target_connection.commit()

The :attr:`~Cursor.arraysize` value alters how many rows each
:meth:`Cursor.fetchmany()` call returns, see :ref:`tuningfetch`.  The
:meth:`~Cursor.setinputsizes()` call is used to optimize memory allocation when
inserting with :meth:`~Cursor.executemany()`, see :ref:`predefmemory`.  You
may also want to tune the SDU setting for best nework performance, see
:ref:`tuning`.

If you are inserting back into the same database that the records originally
came from, you do not need to open a second connection. Instead, both cursors
can be obtained from one connection.

**Avoiding Copying Data Over the Network**

When copying data to another table in the same database, it may be preferable
to use INSERT INTO SELECT or CREATE AS SELECT to avoid the overhead of copying
data to, and back from, the Python process. This also avoids any data type
changes.  For example to create a complete copy of a table:

.. code-block:: python

   cursor.execute("create table new_table as select * from old_table")

Similarly, when copying to a different database, consider creating a `database
link <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-D966642A-
B19E-449D-9968-1121AF06D793>`__ between the databases and using
INSERT INTO SELECT or CREATE AS SELECT.

You can control the data transfer by changing your SELECT statement.

.. _directpathloads:

Direct Path Loads
=================

Direct Path Loads allow data being inserted into Oracle Database to bypass
code layers such as the database buffer cache. Also there are no INSERT
statements used. This can be very efficient for ingestion of huge amounts of
data but, as a consequence of the architecture, there are restrictions on when
Direct Path Loads can be used. For more information see Oracle Database
documentation such as on SQL*Loader `Direct Path Loads
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-0D576DEF-7918-4DD2-A184-754D217C021F>`__ and on the Oracle Call Interface
`Direct Path Load Interface
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-596F5F9B-47A1-48DB-8702-FEED7BE038B9>`__.

The end-to-end insertion time when using Direct Path Loads for smaller data
sets may not be faster than using :meth:`Cursor.executemany()`, however there
can still be reduced load on the database.

.. note::

    Direct Path Loads are only supported in python-oracledb Thin mode.

Direct Path Loading is performed by the :meth:`Connection.direct_path_load()`
method. For example, if you have the table::

    create table TestDirectPathLoad (
        id    number(9),
        name  varchar2(20)
    );

Then you can load data into it using the code:

.. code-block:: python

    SCHEMA_NAME = "HR"
    TABLE_NAME = "TESTDIRECTPATHLOAD"
    COLUMN_NAMES = ["ID", "NAME"]
    DATA = [
        (1, "A first row"),
        (2, "A second row"),
        (3, "A third row"),
    ]

    connection.direct_path_load(
        schema_name=SCHEMA_NAME,
        table_name=TABLE_NAME,
        column_names=COLUMN_NAMES,
        data=DATA
    )

The records are always implicitly committed.

The ``data`` parameter can be a list of sequences, a :ref:`DataFrame
<oracledataframeobj>` object, or a third-party DataFrame instance that supports
the Apache Arrow PyCapsule Interface, see :ref:`dfppl`.

To load into VECTOR columns, pass an appropriate `Python array.array()
<https://docs.python.org/3/library/array.html>`__ value, or a list of values.
For example, if you have the table::

    create table TestDirectPathLoad (
        id    number(9),
        name  varchar2(20),
        v64   vector(3, float64)
    );

Then you can load data into it using the code:

.. code-block:: python

    SCHEMA_NAME = "HR"
    TABLE_NAME = "TESTDIRECTPATHLOAD"
    COLUMN_NAMES = ["ID", "NAME", "V64"]
    DATA = [
        (1, "A first row", array.array("d", [1, 2, 3])),
        (2, "A second row", [4, 5, 6]),
        (3, "A third row", array.array("d", [7, 8, 9])),
    ]

    connection.direct_path_load(
        schema_name=SCHEMA_NAME,
        table_name=TABLE_NAME,
        column_names=COLUMN_NAMES,
        data=DATA
    )


For more on vectors, see :ref:`vectors`.

Runnable Direct Path Load examples are in the `GitHub examples
<https://github.com/oracle/python-oracledb/tree/main/samples>`__ directory.

**Notes on Direct Path Loads**

- Data is implicitly committed.
- Data being inserted into CLOB or BLOB columns must be strings or bytes, not
  python-oracledb :ref:`LOB Objects <lobobj>`.
- Insertion of python-oracledb :ref:`DbObjectType Objects <dbobjecttype>` is
  not supported

Review Oracle Database documentation for database requirements and
restrictions.

Batching of Direct Path Loads
-----------------------------

If buffer, network, or database limits make it desirable to process smaller
sets of records, you can either make repeated calls to
:meth:`Connection.direct_path_load()` or you can use the ``batch_size``
parameter. For example:

.. code-block:: python

    SCHEMA_NAME = "HR"
    TABLE_NAME = "TESTDIRECTPATHLOAD"
    COLUMN_NAMES = ["ID", "NAME"]
    DATA = [
        (1, "A first row"),
        (2, "A second row"),
        . . .
        (10_000_000, "Ten millionth row"),
    ]

    connection.direct_path_load(
        schema_name=SCHEMA_NAME,
        table_name=TABLE_NAME,
        column_names=COLUMN_NAMES,
        data=DATA,
        batch_size=1_000_000
    )

This will send the data to the database in batches of 1,000,000 records until
all 10,000,000 records have been inserted.

.. _memoptimized:

Memoptimized Rowstore
=====================

The Memoptimized Rowstore is another Oracle Database feature for data
ingestion, particularly for frequent single row inserts. It can also aid query
performance. Configuration and control is handled by database configuration and
the use of specific SQL statements. As a result, there is no specific
python-oracledb requirement or API needed to take advantage of the feature.

To use the Memoptimized Rowstore see Oracle Database documentation `Enabling
High Performance Data Streaming with the Memoptimized Rowstore
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-9752E93D-55A7-
4584-B09B-9623B33B5CCF>`__.
