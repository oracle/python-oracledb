.. _tuning:

.. currentmodule:: oracledb

***********************
Tuning python-oracledb
***********************

Some general tuning tips are:

* Tune your application architecture.

  A general application goal is to reduce the number of :ref:`round-trips
  <roundtrips>` between python-oracledb and the database.

  For multi-user applications, make use of connection pooling.  Create the pool
  once during application initialization.  Do not oversize the pool, see
  :ref:`connpooling`.  Use a session callback function to set session state,
  see
  :ref:`Session Callbacks for Setting Pooled Connection State <sessioncallback>`.

  Make use of efficient python-oracledb functions. For example, to insert
  multiple rows use :meth:`Cursor.executemany()` instead of
  :meth:`Cursor.execute()`. Alternatively use
  :meth:`Connection.direct_path_load()` for inserting very large
  datasets. Another example is to fetch data directly as :ref:`data frames
  <dataframeformat>` instead of using the traditional query code path when
  working with packages like Pandas and NumPy.

* Tune your SQL statements.  See the `SQL Tuning Guide
  <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=TGSQL>`__.

  Use :ref:`bind variables <bind>` to avoid statement reparsing.

  Tune :attr:`Cursor.arraysize` and :attr:`Cursor.prefetchrows` for each SELECT
  query, see :ref:`Tuning Fetch Performance <tuningfetch>`.

  Do simple optimizations like :ref:`limiting the number of rows <rowlimit>`
  and avoiding selecting columns not used in the application.

  It may be faster to work with simple scalar relational values than to use
  Oracle Database object types.

  Make good use of PL/SQL to avoid executing many individual statements from
  python-oracledb.

  Tune the :ref:`Statement Cache <stmtcache>`.

  Enable :ref:`Client Result Caching <clientresultcache>` for small lookup
  tables.

* Tune your database.  See the `Database Performance Tuning Guide
  <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=TGDBA>`__.

* Tune your network.  For example, when inserting or retrieving a large number
  of rows (or for large data), or when using a slow network, then tune the
  Oracle Network Session Data Unit (SDU) and socket buffer sizes, see
  `Configuring Session Data Unit <https://www.oracle.com/pls/topic/lookup?ctx=
  dblatest&id=GUID-86D61D6F-AD26-421A-BABA-77949C8A2B04>`__ and `Oracle Net
  Services: Best Practices for Database Performance and High Availability
  <https://static.rainfocus.com/oracle/oow19/sess/1553616880266001WLIh/PF/
  OOW19_Net_CON4641_1569022126580001esUl.pdf>`__.

  In python-oracledb Thick mode, the SDU size is configured in the
  :ref:`optnetfiles`. In python-oracledb Thin mode, the SDU size can be passed
  as a connection or pool creation parameter.  In both modes it may optionally
  be set in the connection :ref:`Easy Connect string <easyconnect>` or
  :ref:`connect descriptor <conndescriptor>`. The SDU size that will actually
  be used is negotiated down to the lower of application-side value and the
  database network SDU configuration value.

* Do not commit or rollback unnecessarily.  Use :attr:`Connection.autocommit`
  on the last of a sequence of DML statements.

* Consider using :ref:`concurrent programming <concurrentprogramming>` or
  :ref:`pipelining <pipelining>`.

* If Python's Global Interpreter Lock (GIL) is limiting concurrent program
  performance, then explore using parallel Python processes.

.. _tuningfetch:

Tuning Fetch Performance
========================

To improve application performance and scalability, you can set
:attr:`Cursor.prefetchrows` and :attr:`Cursor.arraysize` to adjust
python-oracledb's internal buffers used for SELECT and REF CURSOR query
results. Increasing the sizes causes bigger batches of rows to be fetched by
each internal request to the database. This reduces the number of
:ref:`round-trips <roundtrips>` required. The performance benefit of larger
buffer sizes can be significant when fetching lots of rows, or when using a
slow network. The database also benefits from reduced overheads.

Internally, python-oracledb always does row prefetching and array fetching.
Row prefetching is when rows are returned from the database in the round-trip
used for initial statement execution. Rows are then available in an internal
buffer for the application to consume. Without prefetching, the first set of
rows would have to fetched from the database using a separate round-trip. When
all rows in the prefetch buffer have been consumed by the application, the next
set of rows are internally fetched into a buffer using an array fetch which
takes one round-trip. These rows are made available to the application when it
wants them. After the initial array fetch buffer has been emptied, further
array fetches into the buffer occur as needed to completely retrieve all rows
from the database.

Changing the buffer sizes with :attr:`~Cursor.prefetchrows` and
:attr:`~Cursor.arraysize` affects the internal buffering behavior of
:meth:`Cursor.fetchone()`, :meth:`Cursor.fetchmany()`, and
:meth:`Cursor.fetchall()`. The attribute values do not affect how rows are
returned to the application with the exception of :meth:`Cursor.fetchmany()`,
where :attr:`Cursor.arraysize` is also used as the default for its ``size``
parameter.

An overhead of row prefetching in python-oracledb Thick mode is the use of a
separate buffer from the array fetch buffer, increasing the memory
requirements. Also, an additional data copy from Oracle Client's prefetch
buffer is performed. These costs may outweigh the benefits of using prefetching
in some cases.

SELECT queries that return :ref:`LOB <lobobj>` objects and similar types will
never prefetch rows, so the :attr:`~Cursor.prefetchrows` value is ignored in
those cases.

The attributes do not affect data insertion. To reduce round-trips for DML
statements, see :ref:`batchstmnt`.

Choosing values for ``arraysize`` and ``prefetchrows``
------------------------------------------------------

Tune "array fetching" with :attr:`Cursor.arraysize`. Tune "row prefetching"
with :attr:`Cursor.prefetchrows`. Set these before calling
:meth:`Cursor.execute()`. Also, see :ref:`defprefarray`.

The best :attr:`~Cursor.arraysize` and :attr:`~Cursor.prefetchrows` values can
be found by benchmarking your application under production load. Here are
starting suggestions for four common scenarios:

* Scenario 1: To tune queries that return an unknown and large number of rows,
  increase the :attr:`~Cursor.arraysize` value from its default of 100 until
  you are satisfied with performance, memory, and round-trip usage. For example:

  .. code-block:: python

      cursor = connection.cursor()

      # cursor.prefetchrows = 2  # generally leave this at its default
      cursor.arraysize = 1000

      for row in cursor.execute("select * from very_big_table"):
          print(row)

  In general for this scenario, leave :attr:`~Cursor.prefetchrows` at its
  default value.  If you do change it, then set :attr:`Cursor.arraysize` to a
  bigger value.  Do not make the sizes unnecessarily large.

* Scenario 2: If you are fetching a fixed number of rows, set
  :attr:`~Cursor.arraysize` to the number of expected rows, and set
  :attr:`~Cursor.prefetchrows` to one greater than this value.  Adding one
  removes the need for a round-trip to check for end-of-fetch.  For example, if
  you are using a SELECT query to retrieve 20 rows, perhaps to :ref:`display a
  page <rowlimit>` of data, then set :attr:`~Cursor.prefetchrows` to 21 and
  :attr:`~Cursor.arraysize` to 20:

  .. code-block:: python

      cursor = connection.cursor()

      cursor.prefetchrows = 21
      cursor.arraysize = 20

      for row in cursor.execute("""
          select last_name
             from employees
             order by last_name
             offset 0 rows fetch next 20 rows only"""):
          print(row)

  This will return all rows for the query in one round-trip.

* Scenario 3: If the number of rows returned by a SELECT statement varies from
  execution to execution in your application but is never large, you can use a
  similar strategy to Scenario 2.

  Choose :attr:`~Cursor.arraysize` and :attr:`~Cursor.prefetchrows` values that
  work well for the expected maximum number of rows.

* Scenario 4: If you know that a SELECT query returns just one row then set
  :attr:`~Cursor.arraysize` to 1 to minimize memory usage. The default prefetch
  value of 2 allows minimal round-trips for single-row queries:

  .. code-block:: python

      cursor = connection.cursor()

      cursor.arraysize = 1

      cursor.execute("select * from MyTable where id = 1"):
      row = cursor.fetchone()
      print(row)

**Round-trips Required for Fetching Rows**

The following table shows the number of round-trips required to fetch various
numbers of rows with different :attr:`~Cursor.prefetchrows` and
:attr:`~Cursor.arraysize` values.

.. list-table-with-summary::  Effect of ``prefetchrows`` and ``arraysize`` on the number of round-trips
    :header-rows: 1
    :class: wy-table-responsive
    :align: center
    :summary: The first column is the number of rows used for the example.  The second column is the prefetchrows value.  The third column is the arraysize value.  The final column shows how many round-trips it would take to fetch all data from the database.

    * - Number of rows
      - ``prefetchrows``
      - ``arraysize``
      - Round-trips
    * - 1
      - 2
      - 100
      - 1
    * - 100
      - 2
      - 100
      - 2
    * - 1000
      - 2
      - 100
      - 11
    * - 10000
      - 2
      - 100
      - 101
    * - 10000
      - 2
      - 1000
      - 11
    * - 10000
      - 1000
      - 1000
      - 11
    * - 20
      - 20
      - 20
      - 2
    * - 20
      - 21
      - 20
      - 1

The number of round-trips will be the same regardless of which
:ref:`python-oracledb method <fetching>` is used to fetch query results.

.. _defprefarray:

Application Default Prefetchrows and Arraysize Values
+++++++++++++++++++++++++++++++++++++++++++++++++++++

Application-wide defaults can be set using
:attr:`oracledb.defaults.prefetchrows <Defaults.prefetchrows>` and
:attr:`oracledb.defaults.arraysize <Defaults.arraysize>`, for example:

.. code-block:: python

    import oracledb

    oracledb.defaults.prefetchrows = 1000
    oracledb.defaults.arraysize    = 1000

When using python-oracledb in Thick mode, prefetching can also be tuned in an
external :ref:`oraaccess.xml <optclientfiles>` file, which may be useful for
tuning an application when modifying its code is not feasible.

Setting the sizes with ``oracledb.defaults`` attributes or with
``oraaccess.xml`` will affect the whole application, so it should not be the
first tuning choice.

Changing Prefetchrows and Arraysize for Re-executed Statements
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

In python-oracledb, the :attr:`~Cursor.prefetchrows` and
:attr:`~Cursor.arraysize` values are only examined when a statement is executed
the first time.  To change the values for a re-executed statement, create a new
cursor.  For example, to change :attr:`~Cursor.arraysize`:

.. code-block:: python

    array_sizes = (10, 100, 1000)
    for size in array_sizes:
        cursor = connection.cursor()
        cursor.arraysize = size
        start = time.time()
        cursor.execute(sql).fetchall()
        elapsed = time.time() - start
        print("Time for", size, elapsed, "seconds")

Avoiding Premature Prefetching
++++++++++++++++++++++++++++++

There are two cases that will benefit from setting :attr:`~Cursor.prefetchrows`
to zero:

* When passing a python-oracledb cursor *into* PL/SQL.  Setting
  :attr:`~Cursor.prefetchrows` to 0 can stop rows being prematurely (and
  silently) fetched into the python-oracledb internal buffer, making those rows
  unavailable to the PL/SQL REF CURSOR parameter::

    refcursor = connection.cursor()
    refcursor.prefetchrows = 0
    refcursor.execute("select ...")
    cursor.callproc("myproc", [refcursor])

* When querying a PL/SQL function that uses PIPE ROW to emit rows at
  intermittent intervals.  By default, several rows needs to be emitted by the
  function before python-oracledb can return them to the application.  Setting
  :attr:`~Cursor.prefetchrows` to 0 helps give a consistent flow of data to the
  application.

Tuning Fetching from REF CURSORS
--------------------------------

The internal buffering and performance of fetching data from REF CURSORS can be
tuned by setting the value of :attr:`~Cursor.arraysize` before rows are fetched
from the cursor. The :attr:`~Cursor.prefetchrows` value is ignored when
fetching *from* REF CURSORS.

For example:

.. code-block:: python

    ref_cursor = connection.cursor()
    cursor.callproc("myrefcursorproc", [ref_cursor])

    ref_cursor.arraysize = 1000
    print("Sum of IntCol for", num_rows, "rows:")
    for row in ref_cursor:
        sum_rows += row[0]
    print(sum_rows)

The :attr:`Cursor.arraysize`` value can also be set before calling the
procedure:

.. code-block:: python

    ref_cursor = connection.cursor()
    ref_cursor.arraysize = 1000

    cursor.callproc("myrefcursorproc", [ref_cursor])
    for row in ref_cursor:
        . . .

Also see `Avoiding Premature Prefetching`_.

Tuning Fetching for Data Frames
-------------------------------

When fetching :ref:`data frames <dataframeformat>` with
:meth:`Connection.fetch_df_all()` or :meth:`Connection.fetch_df_batches()`,
tuning of data transfer across the network is controlled by the respective
methods ``arraysize`` or ``size`` parameters.

Any :attr:`oracledb.defaults.prefetchrows <Defaults.prefetchrows>` value is
ignored since these methods always set the internal prefetch size to the
relevant ``arraysize`` or ``size`` value.

Parallelizing Data Fetches from a Single Table
----------------------------------------------

Before trying to improve the performance of querying a single table by issuing
multiple SELECT queries in multiple threads, where each query extracts a
different range of data, you should do careful benchmarking.

Factors that will impact such a solution:

- How heavily loaded is the database? The parallel solution may appear to be
  fast but it could be inefficient, thereby impacting, or eventually being
  limited by, everyone else.

- A single python-oracledb connection can only do one database operation at a
  time, so you need to use a different connection for each executed SQL
  statement, for example, using connections from a :ref:`pool
  <connpooling>`. This will cause extra database load that needs to be
  assessed.

- A naive solution using the OFFSET FETCH syntax to fetch sections of a table
  in individual queries will still cause table blocks to be scanned even though
  not all data is returned.

- Is the table partitioned?

- Are zone maps being used?

- Maybe the real performance bottleneck cannot be solved by parallelism.
  Perhaps you have function based indexes that are being invoked for every
  row.

- Is the data in the database spread across multiple spindles or is the one
  disk having to seek?

- Is Exadata with storage indexes being used?

- What is the impact of Python’s Global Interpreter Lock (GIL)?  Maybe multiple
  Python processes should be used instead of threads.

- What is the application doing with the data? Can the receiving end
  efficiently process it?

- Is it better to execute a single query in Python but use a PARALLEL query
  hint? Or will this overload the database.

.. _roundtrips:

Database Round-trips
====================

A round-trip is defined as the travel of a message from python-oracledb to the
database and back. Calling each python-oracledb function, or accessing each
attribute, will require zero or more round-trips.  For example, inserting a
simple row involves sending data to the database and getting a success response
back.  This is a round-trip. Along with tuning an application's architecture
and `tuning its SQL statements
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=TGSQL>`__, a general
performance and scalability goal is to minimize `round-trips
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-9B2F05F9-D841-
4493-A42D-A7D89694A2D1>`__ because they impact application performance and
overall system scalability.

Some general tips for reducing round-trips are:

* Tune :attr:`Cursor.arraysize` and :attr:`Cursor.prefetchrows` for each
  SELECT query.
* Use :meth:`Cursor.executemany()` for optimal DML execution.
* Only commit when necessary.  Use :attr:`Connection.autocommit` on the last
  statement of a transaction.
* For connection pools, use a callback to set connection state, see
  :ref:`Session Callbacks for Setting Pooled Connection State
  <sessioncallback>`.
* Make use of PL/SQL procedures which execute multiple SQL statements instead
  of executing them individually from python-oracledb.
* Review whether :ref:`Pipelining <pipelining>` can be used.
* Use scalar types instead of Oracle Database object types.
* Avoid overuse of :meth:`Connection.ping()`.
* Avoid setting :attr:`ConnectionPool.ping_interval` to 0 or a small value.
* When using :ref:`SODA <sodausermanual>`, use pooled connections and enable
  the :ref:`SODA metadata cache <sodametadatacache>`.

Finding the Number of Round-Trips
----------------------------------

Oracle's `Automatic Workload Repository <https://www.oracle.com/pls/topic/
lookup?ctx=dblatest&id=GUID-56AEF38E-9400-427B-A818-EDEC145F7ACD>`__
(AWR) reports show 'SQL*Net roundtrips to/from client' and are useful for
finding the overall behavior of a system.

Sometimes you may wish to find the number of round-trips used for a
specific application.  Snapshots of the V$SESSTAT view taken before
and after doing some work can be used for this:

.. code-block:: python

    # Get the connection's session id
    def get_session_id(connection):
        sql = "select sys_context('userenv','sid') from dual"
        result, = connection.cursor().execute(sql).fetchone()
        return result

     # Get the number of round-trips a session has made so far
     def get_round_trips(systemconn, sid):
         sql = """select
                      ss.value
                  from
                      v$sesstat  ss,
                      v$statname sn
                  where
                      ss.sid = :sid
                      and ss.statistic# = sn.statistic#
                      and sn.name like '%roundtrip%client%'"""
         round_trips, = systemconn.cursor().execute(sql, [sid]).fetchone()
         return round_trips


    systemconn = oracledb.connect(user="system", password=spw, dsn=cs)
    connection = oracledb.connect(user=un, password=pw, dsn=cs)

    sid = get_session_id(connection)
    round_trips_before = get_round_trips(systemconn, sid)

    # Do some "work"
    cursor.execute("select ...")
    rows = cursor.fetchall()

    round_trips_after = get_round_trips(systemconn, sid)

    print(f"Round-trips required for query: {round_trips_after - round_trips_before}")

Note that V$SESSTAT is not accurate for :ref:`pipelined database operations
<pipelining>`.

.. _stmtcache:

Statement Caching
=================

Python-oracledb's :meth:`Cursor.execute()` and :meth:`Cursor.executemany()`
methods use statement caching to make re-execution of statements efficient.
Statement caching lets Oracle Database cursors be used without re-parsing
the statement.  Statement caching also reduces metadata transfer costs between
python-oracledb and the database. Performance and scalability are improved.

The python-oracledb Thick mode uses `Oracle Call Interface statement caching
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-4947CAE8-1F00-
4897-BB2B-7F921E495175>`__, whereas the Thin mode uses its own implementation.

Each standalone or pooled connection has its own cache of statements with a
default size of 20. The default size of the statement cache can be changed
using the :attr:`oracledb.defaults.stmtcachesize <Defaults.stmtcachesize>`
attribute. The size can be set when creating connection pools or standalone
connections. In general, set the statement cache size to the size of the
working set of statements being executed by the application.  To manually tune
the cache, monitor the general application load and the `Automatic Workload
Repository <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-56AEF38E-9400-427B-A818-EDEC145F7ACD>`__ (AWR) "bytes sent via SQL*Net
to client" values.  The latter statistic should benefit from not shipping
statement metadata to python-oracledb.  Adjust the statement cache size to your
satisfaction. With Oracle Database 12c (or later), the Thick mode statement
cache size can be automatically tuned using an
:ref:`oraaccess.xml <optclientfiles>` file.

Setting the Statement Cache
---------------------------

The statement cache size can be set globally with
:attr:`oracledb.defaults.stmtcachesize <Defaults.stmtcachesize>`:

.. code-block:: python

    import oracledb

    oracledb.defaults.stmtcachesize = 40

The value can be overridden in an :meth:`oracledb.connect()` call, or when
creating a pool with :meth:`oracledb.create_pool()`. For example:

.. code-block:: python

  oracledb.create_pool(user="scott", password=userpwd, dsn="dbhost.example.com/orclpb",
                       min=2, max=5, increment=1, stmtcachesize=50)

When python-oracledb Thick mode uses Oracle Client 21 (or later), changing the
cache size with :meth:`ConnectionPool.reconfigure()` does not immediately
affect connections previously acquired and currently in use. When those
connections are subsequently released to the pool and re-acquired, they will
then use the new value. When the Thick mode uses Oracle Client prior to
version 21, changing the pool's statement cache size has no effect on
connections that already exist in the pool but will affect new connections
that are subsequently created, for example when the pool grows.

Tuning the Statement Cache
--------------------------

In general, set the statement cache to the size of the working set of
statements being executed by the application. :ref:`SODA <sodausermanual>`
internally makes SQL calls, so tuning the cache is also beneficial for SODA
applications.

In python-oracledb Thick mode with Oracle Client Libraries 12c (or later), the
statement cache size can be automatically tuned with the Oracle Client
Configuration :ref:`oraaccess.xml <optclientfiles>` file.

For manual tuning use views like V$SYSSTAT:

.. code-block:: sql

    SELECT value FROM V$SYSSTAT WHERE name = 'parse count (total)'

Find the value before and after running application load to give the number of
statement parses during the load test. Alter the statement cache size and
repeat the test until you find a minimal number of parses.

If you have Automatic Workload Repository (AWR) reports you can monitor
general application load and the "bytes sent via SQL*Net to client" values.
The latter statistic should benefit from not shipping statement metadata to
python-oracledb. Adjust the statement cache size and re-run the test to find
the best cache size.

Disabling the Statement Cache
-----------------------------

Statement caching can be disabled by setting the cache size to 0:

.. code-block:: python

    oracledb.defaults.stmtcachesize = 0

Disabling the cache may be beneficial when the quantity or order of statements
causes cache entries to be flushed before they get a chance to be
reused. For example if there are more distinct statements than cache
slots, and the order of statement execution causes older statements to
be flushed from the cache before the statements are re-executed.

Disabling the statement cache may also be helpful in test and development
environments.  The statement cache can become invalid if connections remain
open and database schema objects are recreated.  Applications can then receive
errors such as ``ORA-3106``. However, after a statement execution error is
returned once to the application, python-oracledb automatically drops that
statement from the cache. This lets subsequent re-executions of the statement
on that connection to succeed.

When it is inconvenient to pass statement text through an application, the
:meth:`Cursor.prepare()` call can be used to avoid statement re-parsing.
If the ``cache_statement`` parameter in the :meth:`Cursor.prepare()` method is
True and the statement cache size is greater than 0, then the statements will
be added to the cache, if not already present. If the ``cache_statement``
parameter in the :meth:`Cursor.prepare()` method is False and the statement
cache size is greater than 0, then the statement will be removed from the
statement cache (if present) or will not be cached (if not present). The
subsequent ``execute()`` calls use the value None instead of the SQL text.

This feature can prevent a rarely executed statement from flushing a potential
more frequently executed one from a full cache. For example, if a statement
will only ever be executed once:

.. code-block:: python

    cursor.prepare("select user from dual", cache_statement = False)
    cursor.execute(None)

Alternatively,

.. code-block:: python

    sql = "select user from dual"
    cursor.prepare(sql, cache_statement=False)
    cursor.execute(sql)

Statements passed to :meth:`~Cursor.prepare()` are also stored in the statement
cache.

.. _clientresultcache:

Client Result Caching (CRC)
===========================

Python-oracledb applications can use Oracle Database's `Client Result Cache
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-35CB2592-7588-
4C2D-9075-6F639F25425E>`__.  The CRC enables client-side caching of SELECT
query results in client memory for immediate use when the same query is
re-executed.  This is useful for reducing the cost of queries for small,
mostly static, lookup tables, such as for postal codes.  CRC reduces network
:ref:`round-trips <roundtrips>`, and also reduces database server CPU usage.

.. note::

    Client Result Caching is only supported in python-oracledb Thick mode. See
    :ref:`enablingthick`.

The cache is at the application process level.  Access and invalidation is
managed by the Oracle Client libraries.  This removes the need for extra
application logic, or external utilities, to implement a cache.

CRC can be enabled by setting the `database parameters <https://www.oracle.com
/pls/topic/lookup?ctx=dblatest&id=GUID-A9D4A5F5-B939-48FF-80AE-0228E7314C7D>`__
``CLIENT_RESULT_CACHE_SIZE`` and ``CLIENT_RESULT_CACHE_LAG``, and then
restarting the database, for example:

.. code-block:: sql

    SQL> ALTER SYSTEM SET CLIENT_RESULT_CACHE_LAG = 3000 SCOPE=SPFILE;
    SQL> ALTER SYSTEM SET CLIENT_RESULT_CACHE_SIZE = 64K SCOPE=SPFILE;
    SQL> STARTUP FORCE

CRC can alternatively be configured in an :ref:`oraaccess.xml <optclientfiles>`
or :ref:`sqlnet.ora <optnetfiles>` file on the Python host, see `Client
Configuration Parameters <https://www.oracle.com/pls/topic/lookup?ctx=dblatest
&id=GUID-E63D75A1-FCAA-4A54-A3D2-B068442CE766>`__.

Tables can then be created, or altered, so repeated queries use CRC.  This
allows existing applications to use CRC without needing modification.  For
example:

.. code-block:: sql

    SQL> CREATE TABLE cities (id number, name varchar2(40)) RESULT_CACHE (MODE FORCE);
    SQL> ALTER TABLE locations RESULT_CACHE (MODE FORCE);

Alternatively, hints can be used in SQL statements.  For example:

.. code-block:: sql

    SELECT /*+ result_cache */ postal_code FROM locations
