.. _asyncio:

**************************************************
Concurrent Programming with asyncio and Pipelining
**************************************************

:ref:`concurrentprogramming` and :ref:`Oracle Database Pipelining <pipelining>`
significantly enhances the overall performance and responsiveness of
applications.

.. _concurrentprogramming:

Concurrent Programming with asyncio
===================================

The `Asynchronous I/O (asyncio) <https://docs.python.org/3/library/asyncio.
html>`__ Python library can be used with python-oracledb Thin mode for
concurrent programming. This library allows you to run operations in parallel,
for example to run a long-running operation in the background without blocking
the rest of the application. With asyncio, you can easily write concurrent code
with the ``async`` and ``await`` syntax. See Python's `Developing with asyncio
<https://docs.python.org/3/library/asyncio-dev.html>`__ documentation for
useful tips.

The python-oracledb asynchronous API is a part of the standard python-oracledb
module. All the synchronous methods that require a round-trip to the database
now have corresponding asynchronous counterparts. You can choose whether to
use the synchronous API or the asynchronous API in your code. It is
recommended to *not* use both at the same time in your application.

The asynchronous API classes are :ref:`AsyncConnection <asyncconnobj>`,
:ref:`AsyncConnectionPool <asyncconnpool>`,
:ref:`AsyncCursor <asynccursorobj>`, and :ref:`AsyncLOB <asynclobobj>`.

.. note::

    Concurrent programming with asyncio is only supported in
    python-oracledb Thin mode.

.. _connasync:

Connecting to Oracle Database Asynchronously
--------------------------------------------

With python-oracledb, you can create an asynchronous connection to Oracle
Database using either :ref:`standalone connections <asyncstandalone>` or
:ref:`pooled connections <asyncconnpool>`. (For discussion of synchronous
programming, see :ref:`connhandling`.)

.. _asyncstandalone:

Standalone Connections
++++++++++++++++++++++

Standalone connections are useful for applications that need only a single
connection to a database.

An asynchronous standalone connection can be created by calling the
asynchronous method :meth:`oracledb.connect_async()` which establishes a
connection to the database and returns an :ref:`AsyncConnection Object
<asyncconnobj>`. Once connections are created, all objects created by these
connections follow the asynchronous programming model. Subject to appropriate
use of ``await`` for calls that require a round-trip to the database,
asynchronous connections are used in the same way that synchronous programs use
:ref:`standaloneconnection`.

Asynchronous connections should be released when they are no longer needed to
ensure Oracle Database gracefully cleans up. A preferred method is to use an
asynchronous context manager. For example:

.. code-block:: python

    import asyncio
    import oracledb

    async def main():

        async with oracledb.connect_async(user="hr", password=userpwd,
                                          dsn="localhost/orclpdb") as connection:
            with connection.cursor() as cursor:
                await cursor.execute("select user from dual")
                async for result in cursor:
                    print(result)

    asyncio.run(main())

This code ensures that once the block is completed, the connection is closed
and resources are reclaimed by the database. In addition, any attempt to use
the variable ``connection`` outside of the block will fail.

If you do not use a context manager, you should explicitly close connections
when they are no longer needed, for example:

.. code-block:: python

    connection = await oracle.connect_async(user="hr", password=userpwd,
                                            dsn="localhost/orclpdb")

    cursor = connection.cursor()

    await cursor.execute("select user from dual")
    async for result in cursor:
        print(result)

    cursor.close()
    await connection.close()


.. _asyncconnpool:

Connection Pools
++++++++++++++++

Connection pooling allows applications to create and maintain a pool of open
connections to the database. Connection pooling is important for performance
and scalability when applications need to handle a large number of users who do
database work for short periods of time but have relatively long periods when
the connections are not needed. The high availability features of pools also
make small pools useful for applications that want a few connections available
for infrequent use and requires them to be immediately usable when acquired.

An asynchronous connection pool can be created by calling
:meth:`oracledb.create_pool_async()` which returns an :ref:`AsyncConnectionPool
Object <asyncconnpoolobj>`. Note that this method is *synchronous* and does not
use ``await``. Once the pool has been created, your application can get a
connection from it by calling :meth:`AsyncConnectionPool.acquire()`.  After
your application has used a connection, it should be released back to the pool
to make it available for other users. This can be done by explicitly closing
the connection or by using an asynchronous context manager, for example:

.. code-block:: python

    import asyncio
    import oracledb

    async def main():

        pool = oracle.create_pool_async(user="hr", password=userpwd,
                                        dsn="localhost/orclpdb",
                                        min=1, max=4, increment=1)

        async with pool.acquire() as connection:
            with connection.cursor() as cursor:
                await cursor.execute("select user from dual")
                async for result in cursor:
                    print(result)

        await pool.close()

    asyncio.run(main())


.. _sqlexecuteasync:

Executing SQL Using Asynchronous Methods
----------------------------------------

This section covers executing SQL using the asynchronous programming model.
For discussion of synchronous programming, see :ref:`sqlexecution`.

Your application communicates with Oracle Database by executing SQL
statements. Statements such as queries (statements beginning with SELECT or
WITH), Data Manipulation Language (DML), and Data Definition Language (DDL) are
executed using the asynchronous methods :meth:`AsyncCursor.execute()` or
:meth:`AsyncCursor.executemany()`. Rows can be iterated over, or fetched using
one of the methods :meth:`AsyncCursor.fetchone()`,
:meth:`AsyncCursor.fetchone()`, :meth:`AsyncCursor.fetchmany()`, or
:meth:`AsyncCursor.fetchall()`.

You can also use shortcut methods on the :ref:`asyncconnobj` object such as
:meth:`AsyncConnection.execute()` or
:meth:`AsyncConnection.executemany()`. Rows can be fetched using one of the
shortcut methods :meth:`AsyncConnection.fetchone()`,
:meth:`AsyncConnection.fetchmany()`, :meth:`AsyncConnection.fetchall()`,
:meth:`AsyncConnection.fetch_df_all()`, or
:meth:`AsyncConnection.fetch_df_batches()`.

An example of using :meth:`AsyncConnection.fetchall()`:

.. code-block:: python

    import asyncio
    import oracledb

    async def main():

        async with oracledb.connect_async(user="hr", password=userpwd,
                                          dsn="localhost/orclpdb") as connection:
            res = await connection.fetchall("select * from locations")
            print(res)

    asyncio.run(main())

An example that uses asyncio for parallelization and shows the execution of
multiple coroutines:

.. code-block:: python

    import asyncio
    import oracledb

    # Number of coroutines to run
    CONCURRENCY = 5

    # Query the unique session identifier/serial number combination of a connection
    SQL = """SELECT UNIQUE CURRENT_TIMESTAMP AS CT, sid||'-'||serial# AS SIDSER
             FROM V$SESSION_CONNECT_INFO
             WHERE sid = SYS_CONTEXT('USERENV', 'SID')"""

    # Show the unique session identifier/serial number of each connection that the
    # pool opens
    async def init_session(connection, requested_tag):
        res = await connection.fetchone(SQL)
        print(res[0].strftime("%H:%M:%S.%f"), '- init_session with SID-SERIAL#', res[1])

    # The coroutine simply shows the session identifier/serial number of the
    # connection returned by the pool.acquire() call
    async def query(pool):
        async with pool.acquire() as connection:
            await connection.callproc("dbms_session.sleep", [1])
            res = await connection.fetchone(SQL)
            print(res[0].strftime("%H:%M:%S.%f"), '- query with SID-SERIAL#', res[1])

    async def main():

        pool = oracledb.create_pool_async(user="hr", password=userpwd,
                                          dsn="localhost/orclpdb",
                                          min=1, max=CONCURRENCY,
                                          session_callback=init_session)

        coroutines = [ query(pool) for i in range(CONCURRENCY) ]

        await asyncio.gather(*coroutines)

        await pool.close()

    asyncio.run(main())

When you run this, you will see that multiple connections (identified by the
unique Session Identifier and Serial Number combination) are opened and are
used by ``query()``. For example::

    12:09:29.711525 - init_session with SID-SERIAL# 36-38096
    12:09:29.909769 - init_session with SID-SERIAL# 33-56225
    12:09:30.085537 - init_session with SID-SERIAL# 14-31431
    12:09:30.257232 - init_session with SID-SERIAL# 285-40270
    12:09:30.434538 - init_session with SID-SERIAL# 282-32608
    12:09:30.730166 - query with SID-SERIAL# 36-38096
    12:09:30.933957 - query with SID-SERIAL# 33-56225
    12:09:31.115008 - query with SID-SERIAL# 14-31431
    12:09:31.283593 - query with SID-SERIAL# 285-40270
    12:09:31.457474 - query with SID-SERIAL# 282-32608

Your results may vary depending how fast your environment is.

See `async_gather.py <https://github.com/oracle/python-oracledb/tree/main/
samples/async_gather.py>`__ for a runnable example.

.. _txnasync:

Managing Transactions Using Asynchronous Methods
------------------------------------------------

This section covers managing transactions using the asynchronous programming
model. For discussion of synchronous programming, see :ref:`txnmgmnt`.

When :meth:`AsyncCursor.execute()` or :meth:`AsyncCursor.executemany()`
executes a SQL statement, a transaction is started or continued. By default,
python-oracledb does not commit this transaction to the database. The methods
:meth:`AsyncConnection.commit()` and :meth:`AsyncConnection.rollback()`
methods can be used to explicitly commit or rollback a transaction:

.. code-block:: python

    async def main():
        async with oracledb.connect_async(user="hr", password=userpwd,
                                          dsn="localhost/orclpdb") as connection:

            with connection.cursor as cursor:
                await cursor.execute("INSERT INTO mytab (name) VALUES ('John')")
                await connection.commit()

When a database connection is closed, such as with
:meth:`AsyncConnection.close()`, or when variables referencing the connection
go out of scope, any uncommitted transaction will be rolled back.

An alternative way to commit is to set the attribute
:attr:`AsyncConnection.autocommit` of the connection to ``True``. This
ensures all :ref:`DML <dml>` statements (INSERT, UPDATE, and so on) are
committed as they are executed.

Note that irrespective of the autocommit value, Oracle Database will always
commit an open transaction when a DDL statement is executed.

When executing multiple DML statements that constitute a single transaction, it
is recommended to use autocommit mode only for the last DML statement in the
sequence of operations. Unnecessarily committing causes extra database load,
and can destroy transactional consistency.

.. _pipelining:

Pipelining Database Operations
==============================

Pipelining allows an application to send multiple, independent statements to
Oracle Database with one call. The database can be kept busy without waiting
for the application to receive a result set and send the next statement.  While
the database processes the pipeline of statements, the application can continue
with non-database work. When the database has executed all the pipelined
operations, their results are returned to the application.

Pipelined operations are executed sequentially by the database. They do not
execute concurrently. It is local tasks that can be executed at the same time
the database is working.

Effective use of Oracle Database Pipelining can increase the responsiveness of
an application and improve overall system throughput. Pipelining is useful when
many small operations are being performed in rapid succession. It is most
beneficial when the network to the database is slow. This is because of its
reduction in :ref:`round-trips <roundtrips>` compared with those required if
the equivalent SQL statements were individually executed with calls like
:meth:`AsyncCursor.execute()`.

Pipelining is only supported in python-oracledb Thin mode with
:ref:`asyncio <concurrentprogramming>`.

See `Oracle Call Interface Pipelining
<https://www.oracle.com/pls/topic/lookup?ctx=
dblatest&id=GUID-D131842B-354E-431D-A1B3-26A001289806>`__ for more information
about Oracle Database Pipelining.

.. note::

    True pipelining only occurs when you are connected to Oracle Database 23ai.

    When you connect to an older database, operations are sequentially
    executed by python-oracledb. Each operation concludes before the next is
    sent to the database. There is no reduction in round-trips and no
    performance benefit. This usage is only recommended for code portability
    such as when preparing for a database upgrade.

Using Pipelines
---------------

To create a :ref:`pipeline <pipelineobj>` to process a set of database
operations, use :meth:`oracledb.create_pipeline()`.

.. code-block:: python

    pipeline = oracledb.create_pipeline()

You can then add various operations to the pipeline using
:meth:`~Pipeline.add_callfunc()`, :meth:`~Pipeline.add_callproc()`,
:meth:`~Pipeline.add_commit()`, :meth:`~Pipeline.add_execute()`,
:meth:`~Pipeline.add_executemany()`, :meth:`~Pipeline.add_fetchall()`,
:meth:`~Pipeline.add_fetchmany()`, and :meth:`~Pipeline.add_fetchone()`.  For
example:

.. code-block:: python

    pipeline.add_execute("insert into mytable (mycol) values (1234)")
    pipeline.add_fetchone("select user from dual")
    pipeline.add_fetchmany("select employee_id from employees", num_rows=20)

Note that queries that return results do not call ``add_execute()``.

Only one set of query results can be returned from each query operation.  For
example :meth:`~Pipeline.add_fetchmany()` will only fetch the first set of
query records, up to the limit specified by the method's ``num_rows``
parameter. Similarly for :meth:`~Pipeline.add_fetchone()` only the first row
can ever be fetched. It is not possible to fetch more data from these
operations. To prevent the database processing rows that cannot be fetched by
the application, consider adding appropriate ``WHERE`` conditions or using a
``FETCH NEXT`` clause in the statement, see :ref:`rowlimit`.

Query results or :ref:`OUT binds <bind>` from one operation cannot be passed to
subsequent operations in the same pipeline.

To execute the pipeline, call :meth:`AsyncConnection.run_pipeline()`.

.. code-block:: python

    results = await connection.run_pipeline(pipeline)

The operations are all sent to the database and executed.  The method returns a
list of :ref:`PipelineOpResult objects <pipelineopresultobjs>`, one entry per
operation. The objects contain information about the execution of the relevant
operation, such as any error number, PL/SQL function return value, or any query
rows and column metadata.


The :attr:`Connection.call_timeout` value has no effect on pipeline operations.
To limit the time for a pipeline, use an `asyncio timeout
<https://docs.python.org/3/library/asyncio-task.html#timeouts>`__, available
from Python 3.11.

To tune fetching of rows with :meth:`Pipeline.add_fetchall()`, set
:attr:`defaults.arraysize` or pass the ``arraysize`` parameter.

Pipelining Examples
+++++++++++++++++++

An example of pipelining is:

.. code-block:: python

    import asyncio
    import oracledb

    async def main():
        # Create a pipeline and define the operations
        pipeline = oracledb.create_pipeline()
        pipeline.add_fetchone("select temperature from weather")
        pipeline.add_fetchall("select name from friends where active = true")
        pipeline.add_fetchmany("select story from news order by popularity", num_rows=5)

        connection = await oracle.connect_async(user="hr", password=userpwd,
                                                dsn="localhost/orclpdb")

        # Run the operations in the pipeline
        result_1, result_2, result_3 = await connection.run_pipeline(pipeline)

        # Print the database responses
        print("Current temperature:", result_1.rows)
        print("Active friends:", result_2.rows)
        print("Top news stories:", result_3.rows)

        await connection.close()

    asyncio.run(main())

See `pipelining_basic.py
<https://github.com/oracle/python-oracledb/tree/main/samples/pipelining_basic.py>`__
for a runnable example.

To allow an application to continue with non-database work before processing
any responses from the database, use code similar to:

.. code-block:: python

    async def run_thing_one():
        return "thing_one"

    async def run_thing_two():
        return "thing_two"

    async def main():
        connection = await oracle.connect_async(user="hr", password=userpwd,
                                                dsn="localhost/orclpdb")

        pipeline = oracledb.create_pipeline()
        pipeline.add_fetchone("select user from dual")
        pipeline.add_fetchone("select sysdate from dual")

        # Run the pipeline and non-database operations concurrently
        return_values = await asyncio.gather(
            run_thing_one(), run_thing_two(), connection.run_pipeline(pipeline)
        )

        for r in return_values:
            if isinstance(r, list):  # the pipeline return list
                for result in r:
                    if result.rows:
                        for row in result.rows:
                            print(*row, sep="\t")
            else:
                print(r)             # a local operation result

        await connection.close()

    asyncio.run(main())

Output will be like::

    thing_one
    thing_two
    HR
    2024-10-29 03:34:43

See `pipelining_parallel.py
<https://github.com/oracle/python-oracledb/tree/main/samples/pipelining_parallel.py>`__
for a runnable example.

Using OUT Binds with Pipelines
------------------------------

To fetch :ref:`OUT binds <bind>` from executed statements, create an explicit
cursor and use :meth:`Cursor.var()`.  These variables are associated with the
connection and can be used by the other cursors created internally for each
pipelined operation.  For example:

.. code-block:: python

    cursor = connection.cursor()
    v1 = cursor.var(oracledb.DB_TYPE_BOOLEAN)
    v2 = cursor.var(oracledb.DB_TYPE_VARCHAR)

    pipeline = oracledb.create_pipeline()

    pipeline.add_execute("""
        begin
          :1 := true;
          :2 := 'Python';
        end;
        """, [v1, v2])
    pipeline.add_fetchone("select 1234 from dual")

    results = await connection.run_pipeline(pipeline)

    for r in results:
        if r.rows:
            print(r.rows)

    print(v1.getvalue(), v2.getvalue())

This prints::

    [(1234,)]
    True Python

OUT binds from one operation cannot be used in subsequent operations.  For
example the following would print only ``True`` because the WHERE condition of
the SQL statement is not matched:

.. code-block:: python

    cursor = connection.cursor()
    v1 = cursor.var(oracledb.DB_TYPE_BOOLEAN)

    pipeline = oracledb.create_pipeline()

    pipeline.add_execute("""
        begin
          :1 := TRUE;
        end;
        """, [v1])
    pipeline.add_fetchone("select 1234 from dual where :1 = TRUE", [v1])

    results = await connection.run_pipeline(pipeline)

    for r in results:
        if r.rows:
            print(r.rows)

    print(v1.getvalue())  # prints True

Pipeline Error Handling
-----------------------

The ``continue_on_error`` parameter to :meth:`AsyncConnection.run_pipeline()`
determines whether subsequent operations should continue to run after a failure
in one operation has occurred. When set to the default value False, if any
error is returned in any operation in the pipeline then the database terminates
all subsequent operations.

For example:

.. code-block:: python

    # Stop on error

    pipeline.add_fetchall("select 1234 from does_not_exist")
    pipeline.add_fetchone("select 5678 from dual")

    r1, r2 = await connection.run_pipeline(pipeline)

will only execute the first operation and will throw the failure message::

    oracledb.exceptions.DatabaseError: ORA-00942: table or view "HR"."DOES_NOT_EXIST" does not exist
    Help: https://docs.oracle.com/error-help/db/ora-00942/


whereas this code:

.. code-block:: python

    # Continue on error

    pipeline.add_fetchall("select 1234 from does_not_exist")
    pipeline.add_fetchone("select 5678 from dual")

    r1, r2 = await connection.run_pipeline(pipeline, continue_on_error=True)

    print(r1.error)
    print(r2.rows)

will execute all operations and will display::

    ORA-00942: table or view "HR"."DOES_NOT_EXIST" does not exist
    Help: https://docs.oracle.com/error-help/db/ora-00942/
    [(5678,)]

.. _pipelinewarning:

**PL/SQL Compilation Warnings**

:ref:`plsqlwarning` can be identified by checking the :ref:`PipelineOpResult
Attribute <pipelineopresultobjs>` :attr:`PipelineOpResult.warning`.  For
example:

.. code-block:: python

    pipeline.add_execute(
        """create or replace procedure myproc as
           begin
              bogus;
           end;"""
    )
    (result,) = await connection.run_pipeline(pipeline)

    print(result.warning.full_code)
    print(result.warning)

will print::

    DPY-7000
    DPY-7000: creation succeeded with compilation errors


See `pipelining_error.py
<https://github.com/oracle/python-oracledb/tree/main/samples/pipelining_error.py>`__
for a runnable example showing warnings and errors.


Pipeline Cursor Usage
---------------------

For each operation added to a pipeline, with the exception of
:meth:`Pipeline.add_commit()`, a cursor will be opened when
:meth:`AsyncConnection.run_pipeline()` is called.  For example, the following
code will open two cursors:

.. code-block:: python

    pipeline = oracledb.create_pipeline()
    pipeline.add_execute("insert into t1 (c1) values (1234)")
    pipeline.add_fetchone("select user from dual")

    await connection.run_pipeline(pipeline)

Make sure your pipeline length does not exceed your cursor limit.  Set the
database parameter `open_cursors
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-FAFD1247-06E5-4E64-917F-AEBD4703CF40>`__
appropriately.

Pipeline Round-trips
--------------------

The complete set of operations in a pipeline will be performed in a single
:ref:`round-trip <roundtrips>` when :meth:`AsyncConnection.run_pipeline()` is
called, with the following exceptions:

- Queries that contain :ref:`LOBs <asynclobobj>` require an additional
  round-trip
- Queries that contain :ref:`DbObject <dbobject>` values may require multiple
  round-trips
- Queries with :meth:`~Pipeline.add_fetchall()` may require multiple
  round-trips

The reduction in round-trips is the significant contributor to pipelining's
performance improvement in comparison to explicitly executing the equivalent
SQL statements individually.  With high-speed networks there may be little
performance benefit to using pipelining, however the database and network
efficiencies can help overall system scalability.

Note that the traditional method of monitoring round-trips by taking snapshots
of the V$SESSTAT view is not accurate for pipelines.
