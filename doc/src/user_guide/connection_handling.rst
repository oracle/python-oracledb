.. _connhandling:

*****************************
Connecting to Oracle Database
*****************************

Connections between python-oracledb and Oracle Database are used for executing
:ref:`SQL <sqlexecution>`, :ref:`PL/SQL <plsqlexecution>`, and :ref:`SODA
<sodausermanual>`.

By default, python-oracledb runs in a 'Thin' mode which connects directly to
Oracle Database.  This mode does not need Oracle Client libraries.  However,
some :ref:`additional functionality <featuresummary>` is available when
python-oracledb uses them.  Python-oracledb is said to be in 'Thick' mode when
Oracle Client libraries are used.  See :ref:`enablingthick`.  Both modes have
comprehensive functionality supporting the Python Database API v2.0
Specification.

If you intend to use the Thick mode, then you *must* call
:func:`~oracledb.init_oracle_client()` in the application before any standalone
connection or pool is created.  The python-oracledb Thick mode loads Oracle
Client libraries which communicate over Oracle Net to an existing database.
The Oracle Client libraries need to be installed separately.  See
:ref:`installation`.  Oracle Net is not a separate product: it is how the
Oracle Client and Oracle Database communicate.

There are two ways to create a connection to Oracle Database using
python-oracledb:

*  **Standalone connections**: :ref:`Standalone connections <standaloneconnection>`
   are useful when the application needs a single connection to a database.
   Connections are created by calling :meth:`oracledb.connect()`.

*  **Pooled connections**: :ref:`Connection pooling <connpooling>` is important for
   performance when applications frequently connect and disconnect from the database.
   Pools support Oracle's :ref:`high availability <highavailability>` features and are
   recommended for applications that must be reliable.  Small pools can also be
   useful for applications that want a few connections available for infrequent
   use.  Pools are created with :meth:`oracledb.create_pool()` at application
   initialization time, and then :meth:`ConnectionPool.acquire()` can be called to
   obtain a connection from a pool.

Many connection behaviors can be controlled by python-oracledb connection
options.  Other settings can be configured in :ref:`optnetfiles` or in
:ref:`optclientfiles`.  These include limiting the amount of time that opening
a connection can take, or enabling :ref:`network encryption <netencrypt>`.

.. note::

       Creating a connection in python-oracledb Thin mode always requires a
       connection string, or the database host name and service name, to be
       specified.  The Thin mode cannot use "bequeath" connections and does not
       reference Oracle environment variables ``ORACLE_SID``, ``TWO_TASK``,
       or ``LOCAL``.

.. note::

       When using python-oracledb in Thin mode, the ``tnsnames.ora`` file will not
       be automatically located.  The file's directory must explicitly be passed
       to the application, see :ref:`optnetfiles`.

.. _standaloneconnection:

Standalone Connections
======================

Standalone connections are database connections that do not use a
python-oracledb connection pool.  They are useful for simple applications that
use a single connection to a database.  Simple connections are created by
calling :meth:`oracledb.connect()` and passing a database username, the
database password for that user, and a 'data source name' :ref:`connection
string <connstr>`.  Python-oracledb also supports :ref:`external authentication
<extauth>` and so passwords do not need to be in the application.

Creating a Standalone Connection
--------------------------------

Standalone connections are created by calling :meth:`oracledb.connect()`.

A simple standalone connection example:

.. code-block:: python

    import oracledb
    import getpass

    userpwd = getpass.getpass("Enter password: ")

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb")

You could alternatively read the password from an environment variable:

.. code-block:: python

    userpwd = os.environ.get("PYTHON_PASSWORD")

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="localhost/orclpdb")

The :meth:`oracledb.connect()` method allows the database host name and
database service name to be passed as separate parameters.  The database
listener port can also be passed:

.. code-block:: python

    import os

    userpwd = os.environ.get("PYTHON_PASSWORD")

    connection = oracledb.connect(user="hr", password=userpwd,
                                  host="localhost", port=1521, service_name="orclpdb")

If you like to encapsulate values, parameters can be passed using a
:ref:`ConnectParams Object <usingconnparams>`:

.. code-block:: python

    params = oracledb.ConnectParams(host="my_host", port=my_port, service_name="my_service_name")
    conn = oracledb.connect(user="my_user", password="my_password", params=params)

Some values such as the database host name can be specified as ``connect()``
parameters, as part of the connect string, and in the ``params`` object.  If a
``dsn`` is passed, the python-oracledb :ref:`Thick <enablingthick>` mode will
use the ``dsn`` string to connect. Otherwise, a connection string is internally
constructed from the individual parameters and ``params`` object values, with
the individual parameters having precedence.  In python-oracledb's default Thin
mode, a connection string is internally used that contains all relevant values
specified.  The precedence in Thin mode is that values in any ``dsn`` parameter
override values passed as individual parameters, which themselves override
values set in the ``params`` object.  Similar precedence rules also apply to
other values.

A single, combined connection string can be passed to ``connect()`` but this
may cause complications if the password contains '@' or '/' characters:

.. code-block:: python

    username="hr"
    userpwd = os.environ.get("PYTHON_PASSWORD")
    host = "localhost"
    port = 1521
    service_name = "orclpdb"

    dsn = f'{username}/{userpwd}@{host}:{port}/{service_name}'
    connection = oracledb.connect(dsn)

Closing Connections
+++++++++++++++++++

Connections should be released when they are no longer needed.  You may prefer
to let connections be automatically cleaned up when references to them go out
of scope.  This lets python-oracledb close dependent resources in the correct
order:

.. code-block:: python

    with oracledb.connect(user="hr", password=userpwd,
                          dsn="dbhost.example.com/orclpdb") as connection:
        with connection.cursor() as cursor:
            cursor.execute("insert into SomeTable values (:1, :2)",
                           (1, "Some string"))
            connection.commit()

This code ensures that once the block is completed, the connection is closed
and resources have been reclaimed by the database. In addition, any attempt to
use the variable ``connection`` outside of the block will simply fail.

Alternatively, you can explicitly close a connection by calling.
:meth:`Connection.close()`:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd, dsn="localhost/orclpdb")

    # do something with the connection
    . . .

    # close the connection
    connection.close()

.. _connerrors:

Common Connection Errors
------------------------

Some of the common connection errors that you may encounter in the
python-oracledb's default Thin mode are detailed below.  Also see
:ref:`errorhandling`.

Use keyword parameters
++++++++++++++++++++++

If you use:

.. code-block:: python

    connection = oracledb.connect("hr", userpwd, "localhost/orclpdb")

then you will get the error::

    TypeError: connect() takes from 0 to 1 positional arguments but 3 were given

The :meth:`oracledb.connect()` method requires keyword parameters to be used

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd, dsn="localhost/orclpdb")

The exception passing a single argument containing the combined credential and
connection string.  This is supported:

.. code-block:: python

    connection = oracledb.connect("hr/userpwd@localhost/orclpdb")

Use the correct credentials
+++++++++++++++++++++++++++

If your username or password are not known by the database that you attempted
to connect to, then you will get the error::

    ORA-01017: invalid username/password; logon denied

Find the correct username and password and try reconnecting.

Use the correct connection string
+++++++++++++++++++++++++++++++++

If the hostname, port, or service name are incorrect, then the connection will fail
with the error::

    DPY-6001: cannot connect to database. Service "doesnotexist" is not
    registered with the listener at host "localhost" port 1521. (Similar to
    ORA-12514)

This error means that Python successfully reached a computer (in this case,
"localhost" using the default port 1521) that is running a database.  However,
the database service you wanted ("doesnotexist") does not exist there.

Technically, the error means the listener does not know about the service at the
moment.  So you might also get this error if the database is currently restarting.

This error is similar to the ``ORA-12514`` error that you may see when connecting
with python-oracledb in Thick mode, or with some other Oracle tools.

The solution is to use a valid service name in the connection string. You can:

- Check and fix any typos in the service name you used

- Check if the hostname and port are correct

- Ask your database administrator (DBA) for the correct values

- Wait a few moments and re-try in case the database is restarting

- Review the connection information in your cloud console or cloud wallet, if
  you are using a cloud database

- Run `lsnrctl status` on the database machine to find the known service names


.. _connstr:

Connection Strings
==================

The data source name parameter ``dsn`` of :meth:`oracledb.connect()` and
:meth:`oracledb.create_pool()` is the Oracle Database connection string
that identifies which database service to connect to.  The ``dsn`` string can be
one of:

* An Oracle Easy Connect string
* An Oracle Net Connect Descriptor string
* A Net Service Name mapping to a connect descriptor

For more information about naming methods, see `Oracle Net Service Reference
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-E5358DEA-D619-4B7B-A799-3D2F802500F1>`__.

.. _easyconnect:

Easy Connect Syntax for Connection Strings
------------------------------------------

An Easy Connect string is often the simplest connection string to use for the
data source name parameter ``dsn`` of :meth:`oracledb.connect()` and
:meth:`oracledb.create_pool()`.  This method does not need configuration files
such as ``tnsnames.ora``.

For example, to connect to the Oracle Database service ``orclpdb`` that is
running on the host ``dbhost.example.com`` with the default Oracle
Database port 1521, use:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb")

If the database is using a non-default port, it must be specified:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com:1984/orclpdb")

The Easy Connect syntax supports Oracle Database service names.  It cannot be
used with the older System Identifiers (SID).

The latest `Easy Connect Plus
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-8C85D289-6AF3-41BC-848B-BF39D32648BA>`__ syntax allows the use of
multiple hosts or ports, along with optional entries for the wallet location,
the distinguished name of the database server, and even allows some network
configuration options be set. This means that a :ref:`sqlnet.ora <optnetfiles>`
file is not needed for some common connection scenarios.

In python-oracledb Thin mode, any unknown Easy Connect options are ignored and
are not passed to the database.  See :ref:`Connection String Differences
<diffconnstr>` for more information.

In python-oracledb Thick mode, it is the Oracle Client libraries that parse the
Easy Connect string.  Check the Easy Connect Naming method in `Oracle Net
Service Administrator's Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-B0437826-43C1-49EC-A94D-B650B6A4A6EE>`__ for the syntax to use in your
version of the Oracle Client libraries.

.. _netservice:

Net Service Names for Connection Strings
----------------------------------------

Connect Descriptor Strings are commonly stored in a :ref:`tnsnames.ora
<optnetfiles>` file and associated with a Net Service Name.  This name can be
used directly for the data source name parameter ``dsn`` of
:meth:`oracledb.connect()` and :meth:`oracledb.create_pool()`.  For example,
given a file ``/opt/oracle/config/tnsnames.ora`` with the following contents::

    ORCLPDB =
      (DESCRIPTION =
        (ADDRESS = (PROTOCOL = TCP)(HOST = dbhost.example.com)(PORT = 1521))
        (CONNECT_DATA =
          (SERVER = DEDICATED)
          (SERVICE_NAME = orclpdb)
        )
      )

Then you could connect in python-oracledb Thin mode by using the following code:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd, dsn="orclpdb",
                                  config_dir="/opt/oracle/config")

More options for how python-oracledb locates ``tnsnames.ora`` files is detailed
in :ref:`optnetfiles`.  Note in python-oracledb Thick mode, the configuration
directory must be set during initialization, not at connection time.

For more information about Net Service Names, see
`Database Net Services Reference
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-12C94B15-2CE1-4B98-9D0C-8226A9DDF4CB>`__.

Oracle Net Connect Descriptor Strings
-------------------------------------

Full Connect Descriptor strings can be embedded directly in python-oracledb
applications:

.. code-block:: python

    dsn = """(DESCRIPTION=
                 (FAILOVER=on)
                 (ADDRESS_LIST=
                   (ADDRESS=(PROTOCOL=tcp)(HOST=sales1-svr)(PORT=1521))
                   (ADDRESS=(PROTOCOL=tcp)(HOST=sales2-svr)(PORT=1521)))
                 (CONNECT_DATA=(SERVICE_NAME=sales.example.com)))"""

    connection = oracledb.connect(user="hr", password=userpwd, dsn=dsn)

The :meth:`oracledb.ConnectParams()` and :meth:`ConnectParams.get_connect_string()`
functions can be used to construct a connect descriptor string from the
individual components, see :ref:`usingconnparams`.  For example:

.. code-block:: python

    cp = oracledb.ConnectParams(host="dbhost.example.com", port=1521, service_name="orclpdb")
    dsn = cp.get_connect_string()
    print(dsn)

This prints::

    (DESCRIPTION=(ADDRESS_LIST=(ADDRESS=(PROTOCOL=tcp)(HOST=dbhost.example.com)(PORT=1521)))(CONNECT_DATA=(SERVICE_NAME=orclpdb))(SECURITY=(SSL_SERVER_DN_MATCH=True)))


JDBC and Oracle SQL Developer Connection Strings
------------------------------------------------

The python-oracledb connection string syntax is different from Java JDBC and the
common Oracle SQL Developer syntax.  If these JDBC connection strings reference
a service name like::

    jdbc:oracle:thin:@hostname:port/service_name

For example::

    jdbc:oracle:thin:@dbhost.example.com:1521/orclpdb

then use Oracle's Easy Connect syntax in python-oracledb:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com:1521/orclpdb")

Alternatively, if a JDBC connection string uses an old-style Oracle Database
SID "system identifier", and the database does not have a service name::

    jdbc:oracle:thin:@hostname:port:sid

For example::

    jdbc:oracle:thin:@dbhost.example.com:1521:orcl

then connect by using the ``sid`` parameter:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  host="dbhost.example.com", port=1521, sid="orcl")

Alternatively, create a ``tnsnames.ora`` (see :ref:`optnetfiles`) entry, for
example::

    finance =
     (DESCRIPTION =
       (ADDRESS = (PROTOCOL = TCP)(HOST = dbhost.example.com)(PORT = 1521))
       (CONNECT_DATA =
         (SID = ORCL)
       )
     )

This can be referenced in python-oracledb:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd, dsn="finance")

.. _usingconnparams:

Using the ConnectParams Builder Class
======================================

The :ref:`ConnectParams class <connparam>` allows you to define connection
parameters in a single place.  The :func:`oracledb.ConnectParams()` function
returns a ``ConnectParams`` object.  The object can be passed to
:func:`oracledb.connect()`. For example:

.. code-block:: python

    cp = oracledb.ConnectParams(user="hr", password=userpwd,
                                host="dbhost", port=1521, service_name="orclpdb")
    connection = oracledb.connect(params=cp)

The use of the ConnectParams class is optional because you can pass the same
parameters directly to :func:`~oracledb.connect()`.  For example, the code above
is equivalent to:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  host="dbhost", port=1521, service_name="orclpdb")


If you want to keep credentials separate, you can use ConnectParams just to
encapsulate connection string components:

.. code-block:: python

    cp = oracledb.ConnectParams(host="dbhost", port=1521, service_name="orclpdb")
    connection = oracledb.connect(user="hr", password=userpwd, params=cp)

You can use :meth:`ConnectParams.get_connect_string()` to get a connection
string from a ConnectParams object:

.. code-block:: python

    cp = oracledb.ConnectParams(host="dbhost", port="my_port", service_name="my_service_name")
    dsn = cp.get_connect_string()
    connection = oracledb.connect(user="hr", password=userpwd, dsn=dsn)

To parse a connection string and store components as attributes:

.. code-block:: python

    cp = oracledb.ConnectParams()
    cp.parse_connect_string("host.example.com:1522/orclpdb")

Most parameter values of :func:`oracledb.ConnectParams()` are gettable as
attributes. For example, to get the stored host name:

.. code-block:: python

    print(cp.host)

Attributes such as the password are not gettable.

You can set individual attributes using :meth:`ConnectParams.set()`:

.. code-block:: python

    cp = oracledb.ConnectParams(host="localhost", port=1521, service_name="orclpdb")

    # set a new port
    cp.set(port=1522)

    # change both the port and service name
    cp.set(port=1523, service_name="orclpdb")

Some values such as the database host name can be specified as
:func:`oracledb.connect()`, parameters, as part of the connect string, and in
the ``params`` object.  If a ``dsn`` is passed, the python-oracledb :ref:`Thick
<enablingthick>` mode will use the ``dsn`` string to connect. Otherwise, a
connection string is internally constructed from the individual parameters and
``params`` object values, with the individual parameters having precedence.  In
python-oracledb's default Thin mode, a connection string is internally used
that contains all relevant values specified.  The precedence in Thin mode is
that values in any ``dsn`` parameter override values passed as individual
parameters, which themselves override values set in the ``params`` object.
Similar precedence rules also apply to other values.

.. _connpooling:

Connection Pooling
==================

Python-oracledb's connection pooling lets applications create and maintain a
pool of open connections to the database.  Connection pooling is available in
both Thin and :ref:`Thick <enablingthick>` modes.  Connection pooling is
important for performance and scalability when applications need to handle a
large number of users who do database work for short periods of time but have
relatively long periods when the connections are not needed.  The high
availability features of pools also make small pools useful for applications
that want a few connections available for infrequent use and requires them to
be immediately usable when acquired.

In python-oracledb Thick mode, the pool implementation uses Oracle's `session
pool technology <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-F9662FFB-EAEF-495C-96FC-49C6D1D9625C>`__ which supports additional
Oracle Database features, for example some advanced :ref:`high availability
<highavailability>` features.

Creating a Connection Pool
--------------------------

A connection pool is created by calling :meth:`oracledb.create_pool()`.
Various pool options can be specified as described in
:meth:`~oracledb.create_pool()` and detailed below.

For example, to create a pool that initially contains one connection but
can grow up to five connections:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb",
                                min=1, max=5, increment=1)

After the pool has been created, your application can get a connection from
it by calling :meth:`ConnectionPool.acquire()`:

.. code-block:: python

    connection = pool.acquire()

These connections can be used in the same way that :ref:`standaloneconnection`
are used.

By default, :meth:`~ConnectionPool.acquire()` calls wait for a connection
to be available before returning to the application.  A connection will be
available if the pool currently has idle connections, when another user
returns a connection to the pool, or after the pool grows.  Waiting allows
applications to be resilient to temporary spikes in connection load.  Users
may have to wait a brief time to get a connection but will not experience
connection failures.

You can change the behavior of :meth:`~ConnectionPool.acquire()` by setting the
``getmode`` option during pool creation.  For example, the option can be
set so that if all the connections are currently in use by the application, any
additional :meth:`~ConnectionPool.acquire()` call will return an error
immediately.

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb",
                                min=2, max=5, increment=1,
                                getmode=oracledb.POOL_GETMODE_NOWAIT)

Note that when using this option value in Thick mode with Oracle Client
libraries 12.2 or earlier, the :meth:`~ConnectionPool.acquire()` call will
still wait if the pool can grow.  However, you will get an error immediately if
the pool is at its maximum size.  With newer Oracle Client libraries and with
Thin mode, an error will be returned if the pool has to, or cannot, grow.

When your application has finished performing all required database operations,
the pooled connection should be released to make it available for other users
of the pool.  You can do this with :meth:`ConnectionPool.release()` or
:meth:`Connection.close()`.  Alternatively you may prefer to let pooled
connections be closed implicitly at the end of scope.  For example, by using a
``with`` statement:

.. code-block:: python

    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            for result in cursor.execute("select * from mytab"):
                print(result)

At application shutdown, the connection pool can be completely closed using
:meth:`ConnectionPool.close()`:

.. code-block:: python

    pool.close()

To force immediate pool termination when connections are still in use, execute:

.. code-block:: python

    pool.close(force=True)

See `connection_pool.py
<https://github.com/oracle/python-oracledb/tree/main/samples/connection_pool.py>`__
for a runnable example of connection pooling.

**Connection Pool Growth**

At pool creation, ``min`` connections are established to the database.  When a
pool needs to grow, new connections are created automatically limited by the
``max`` size.  The pool ``max`` size restricts the number of application users
that can do work in parallel on the database.

The number of connections opened by a pool can shown with the attribute.
:attr:`ConnectionPool.opened`.  The number of connections the application has
obtained with :meth:`~ConnectionPool.acquire()` can be shown with
:attr:`ConnectionPool.busy`.  The difference in values is the number of
connections unused or 'idle' in the pool.  These idle connections may be
candidates for the pool to close, depending on the pool configuration.

Pool growth is normally initiated when :meth:`~ConnectionPool.acquire()` is
called and there are no idle connections in the pool that can be returned to
the application.  The number of new connections created internally will be the
value of the :meth:`~oracledb.create_pool()` parameter ``increment``.

Depending on whether Thin or Thick mode is used and on the pool creation
``getmode`` value that is set, any :meth:`~ConnectionPool.acquire()` call that
initiates pool growth may wait until all ``increment`` new connections are
internally opened.  However, in this case the cost is amortized because later
:meth:`~ConnectionPool.acquire()` calls may not have to wait and can
immediately return an available connection.  Some users set larger
``increment`` values even for fixed-size pools because it can help a pool
re-establish itself if all connections become invalid, for example after a
network dropout.  In the common case of Thin mode with the default ``getmode``
of ``POOL_GETMODE_WAIT``, any :meth:`~ConnectionPool.acquire()` call that
initiates pool growth will return after the first new connection is created,
regardless of how big ``increment`` is.  The pool will then continue to
re-establish connections in a background thread.

A connection pool can shrink back to its minimum size when connections opened
by the pool are not used by the application.  This frees up database resources
while allowing pools to retain connections for active users.  Note this is
currently applicable to Thick mode only.  If connections are idle in the pool
(i.e. not currently acquired by the application) and are unused for longer than
the pool creation attribute ``timeout`` value , then they will be closed.  The
default ``timeout`` is 0 seconds signifying an infinite time and meaning idle
connections will never be closed.  The pool creation parameter
``max_lifetime_session`` also allows pools to shrink.  This parameter bounds
the total length of time that a connection can exist starting from the time the
pool created it.  If a connection was created ``max_lifetime_session`` or
longer seconds ago, then it will be closed when it is idle in the pool.  In the
case when ``timeout`` and ``max_lifetime_session`` are both set, the connection
will be terminated if either the idle timeout happens or the max lifetime
setting is exceeded.  Note that when using python-oracledb in Thick mode with
Oracle Client libraries prior to 21c, pool shrinkage is only initiated when the
pool is accessed so pools in fully dormant applications will not shrink until
the application is next used.

For pools created with :ref:`external authentication <extauth>`, with
:ref:`homogeneous <connpooltypes>` set to False, or when using :ref:`drcp`,
then the number of connections opened at pool creation is zero even if a larger
value is specified for ``min``.  Also, in these cases the pool increment unit
is always 1 regardless of the value of ``increment``.

**Pool Connection Health**

Before :meth:`ConnectionPool.acquire()` returns, python-oracledb does a
lightweight check similar to :meth:`Connection.is_healthy()` to see if the
network transport for the selected connection is still open.  If it is not,
then :meth:`~ConnectionPool.acquire()` will clean up the connection and return
a different one.

This check will not detect cases such as where the database session has been
terminated by the DBA, or reached a database resource manager quota limit.  To
help in those cases, :meth:`~ConnectionPool.acquire()` will also do a full
:ref:`round-trip <roundtrips>` database ping similar to
:meth:`Connection.ping()` when it is about to return a connection that was idle
in the pool (i.e. not currently acquired by the application) for
:data:`ConnectionPool.ping_interval` seconds.  If the ping fails, the
connection will be discarded and another one obtained before
:meth:`~ConnectionPool.acquire()` returns to the application.

Because this full ping is time based and may not occur for each
:meth:`~ConnectionPool.acquire()`, the application may still get an unusable
connection.  Also, network timeouts and session termination may occur between
the calls to :meth:`~ConnectionPool.acquire()` and :meth:`Cursor.execute()`.
To handle these cases, applications need to check for errors after each
:meth:`~Cursor.execute()` and make application-specific decisions about
retrying work if there was a connection failure.  When using python-oracledb in
Thick mode, Oracle Database features like :ref:`Application Continuity
<highavailability>` can do this automatically in some cases.

You can explicitly initiate a full round-trip ping at any time with
:meth:`Connection.ping()` to check connection liveness but the overuse will
impact performance and scalability.

Ensure that the :ref:`firewall <hanetwork>`, `resource manager
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-2BEF5482-CF97-4A85-BD90-9195E41E74EF>`__
or user profile `IDLE_TIME
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-ABC7AE4D-64A8-4EA9-857D-BEF7300B64C3>`__
do not expire idle sessions, since this will require connections to be recreated
which will impact performance and scalability.

A pool's internal connection re-establishment after lightweight and full pings
can mask performance-impacting configuration issues such as firewalls
terminating connections.  You should monitor `AWR
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-56AEF38E-9400-427B-A818-EDEC145F7ACD>`__
reports for an unexpectedly large connection rate.

.. _connpoolsize:

Connection Pool Sizing
----------------------

The Oracle Real-World Performance Group's recommendation is to use fixed size
connection pools.  The values of ``min`` and ``max`` should be the same.  When
using older versions of Oracle Client libraries the ``increment`` parameter
will need to be zero (which is internally treated as a value of one), but
otherwise you may prefer a larger size since this will affect how the
connection pool is re-established after, for example, a network dropout
invalidates all connections.

Fixed size pools avoid connection storms on the database which can decrease
throughput.  See `Guideline for Preventing Connection Storms: Use Static Pools
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-7DFBA826-7CC0-4D16-B19C-31D168069B54>`__,
which contains more details about sizing of pools.  Having a fixed size will
also guarantee that the database can handle the upper pool size.  For example,
if a dynamically sized pool needs to grow but the database resources are
limited, then :meth:`ConnectionPool.acquire()` may return errors such as
``ORA-28547``.  With a fixed pool size, this class of error will occur when the
pool is created, allowing you to change the pool size or reconfigure the
database before users access the application.  With a dynamically growing pool,
the error may occur much later while the application is in use.

The Real-World Performance Group also recommends keeping pool sizes small because
they may perform better than larger pools. The pool attributes should be
adjusted to handle the desired workload within the bounds of available resources
in python-oracledb and the database.

.. _poolreconfiguration:

Connection Pool Reconfiguration
-------------------------------

Some pool settings can be changed dynamically with
:meth:`ConnectionPool.reconfigure()`.  This allows the pool size and other
attributes to be changed during application runtime without needing to restart
the pool or application.

For example a pool's size can be changed like:

.. code-block:: python

    pool.reconfigure(min=10, max=10, increment=0)

After any size change has been processed, reconfiguration on the other
parameters is done sequentially. If an error such as an invalid value occurs
when changing one attribute, then an exception will be generated but any already
changed attributes will retain their new values.

During reconfiguration of a pool's size, the behavior of
:meth:`ConnectionPool.acquire()` depends on the pool creation ``getmode`` value
in effect when :meth:`~ConnectionPool.acquire()` is called, see
:meth:`ConnectionPool.reconfigure()`.  Closing connections or closing the pool
will wait until after pool reconfiguration is complete.

Calling ``reconfigure()`` is the only way to change a pool's ``min``, ``max``
and ``increment`` values.  Other attributes such as
:data:`~ConnectionPool.wait_timeout` can be passed to ``reconfigure()`` or they
can be set directly, for example:

.. code-block:: python

    pool.wait_timeout = 1000

.. _sessioncallback:

Session CallBacks for Setting Pooled Connection State
-----------------------------------------------------

Applications can set "session" state in each connection.  Examples of session
state are NLS globalization settings from ``ALTER SESSION`` statements.  Pooled
connections will retain their session state after they have been released back
to the pool.  However, because pools can grow or connections in the pool can
be recreated, there is no guarantee a subsequent
:meth:`~ConnectionPool.acquire()` call will return a database connection that
has any particular state.

The :meth:`~oracledb.create_pool()` parameter ``session_callback`` enables
efficient setting of session state so that connections have a known session
state, without requiring that state to be explicitly set after every
:meth:`~ConnectionPool.acquire()` call.  The callback is internally invoked
when :meth:`~ConnectionPool.acquire()` is called and runs first.

The session callback can be a Python function or a PL/SQL procedure.

Connections can also be tagged when they are released back to the pool.  The
tag is a user-defined string that represents the session state of the
connection.  When acquiring connections, a particular tag can be requested.  If
a connection with that tag is available, it will be returned.  If not, then
another session will be returned.  By comparing the actual and requested tags,
applications can determine what exact state a session has, and make any
necessary changes.

Connection tagging and PL/SQL callbacks are only available in python-oracledb
Thick mode.  Python callbacks can be used in python-oracledb Thin and Thick
modes.

There are three common scenarios for ``session_callback``:

- When all connections in the pool should have the same state, use a
  Python callback without tagging.

- When connections in the pool require different state for different users, use
  a Python callback with tagging.

- With :ref:`drcp`, use a PL/SQL callback with tagging.

Python Callback
+++++++++++++++

If the ``session_callback`` parameter is a Python procedure, it will be called
whenever :meth:`~ConnectionPool.acquire()` will return a newly created database
connection that has not been used before.  It is also called when connection
tagging is being used and the requested tag is not identical to the tag in the
connection returned by the pool.

An example is:

.. code-block:: python

    # Set the NLS_DATE_FORMAT for a session
    def init_session(connection, requested_tag):
        with connection.cursor() as cursor:
            cursor.execute("alter session set nls_date_format = 'YYYY-MM-DD HH24:MI'")

    # Create the pool with session callback defined
    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="localhost/orclpdb",
                                session_callback=init_session)

    # Acquire a connection from the pool (will always have the new date format)
    connection = pool.acquire()

If needed, the ``init_session()`` procedure is called internally before
:meth:`~ConnectionPool.acquire()` returns.  It will not be called when
previously used connections are returned from the pool.  This means that the
ALTER SESSION does not need to be executed after every
:meth:`~ConnectionPool.acquire()` call.  This improves performance and
scalability.

In this example tagging was not being used, so the ``requested_tag`` parameter
is ignored.

Note that if you need to execute multiple SQL statements in the callback, use an
anonymous PL/SQL block to save :ref:`round-trips <roundtrips>` of repeated
``execute()`` calls.  With ALTER SESSION, pass multiple settings in the one
statement:

.. code-block:: python

    cursor.execute("""
            begin
                execute immediate
                        'alter session set nls_date_format = ''YYYY-MM-DD''
                                           nls_language = AMERICAN';
                -- other SQL statements could be put here
            end;""")

.. _conntagging:

Connection Tagging
++++++++++++++++++

Connection tagging is used when connections in a pool should have differing
session states.  In order to retrieve a connection with a desired state, the
``tag`` attribute in :meth:`~ConnectionPool.acquire()` needs to be set.

.. note::

    Connection tagging is only supported in the python-oracledb Thick mode. See
    :ref:`enablingthick` .

When python-oracledb is using Oracle Client libraries 12.2 or later, then
python-oracledb uses 'multi-property tags' and the tag string must be of the
form of one or more "name=value" pairs separated by a semi-colon, for example
``"loc=uk;lang=cy"``.

When a connection is requested with a given tag, and a connection with that tag
is not present in the pool, then a new connection, or an existing connection
with cleaned session state, will be chosen by the pool and the session callback
procedure will be invoked.  The callback can then set desired session state and
update the connection's tag.  However, if the ``matchanytag`` parameter of
:meth:`~ConnectionPool.acquire()` is True, then any other tagged connection may
be chosen by the pool and the callback procedure should parse the actual and
requested tags to determine which bits of session state should be reset.

The example below demonstrates connection tagging:

.. code-block:: python

    def init_session(connection, requested_tag):
        if requested_tag == "NLS_DATE_FORMAT=SIMPLE":
            sql = "ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD'"
        elif requested_tag == "NLS_DATE_FORMAT=FULL":
            sql = "ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI'"
        cursor = connection.cursor()
        cursor.execute(sql)
        connection.tag = requested_tag

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="orclpdb",
                                 session_callback=init_session)

    # Two connections with different session state:
    connection1 = pool.acquire(tag="NLS_DATE_FORMAT=SIMPLE")
    connection2 = pool.acquire(tag="NLS_DATE_FORMAT=FULL")

See `session_callback.py
<https://github.com/oracle/python-oracledb/tree/main/
samples/session_callback.py>`__ for an example.

PL/SQL Callback
+++++++++++++++

.. note::

    PL/SQL Callbacks are only supported in the python-oracledb Thick mode. See
    :ref:`enablingthick`.

When python-oracledb uses Oracle Client 12.2 or later, the session callback can
also be the name of a PL/SQL procedure.  A PL/SQL callback will be initiated
only when the tag currently associated with a connection does not match the tag
that is requested.  A PL/SQL callback is most useful when using :ref:`drcp`
because DRCP does not require a :ref:`round-trip <roundtrips>` to invoke a
PL/SQL session callback procedure.

The PL/SQL session callback should accept two VARCHAR2 arguments:

.. code-block:: sql

    PROCEDURE myPlsqlCallback (
        requestedTag IN  VARCHAR2,
        actualTag    IN  VARCHAR2
    );

The logic in this procedure can parse the actual tag in the session that has
been selected by the pool and compare it with the tag requested by the
application.  The procedure can then change any state required before the
connection is returned to the application from
:meth:`~ConnectionPool.acquire()`.

If the ``matchanytag`` attribute of :meth:`~ConnectionPool.acquire()` is
*True*, then a connection with any state may be chosen by the pool.

Oracle 'multi-property tags' must be used.  The tag string must be of the form
of one or more "name=value" pairs separated by a semi-colon, for example
``"loc=uk;lang=cy"``.

In python-oracledb set ``session_callback`` to the name of the PL/SQL
procedure. For example:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd,
                                 dsn="dbhost.example.com/orclpdb:pooled",
                                 session_callback="MyPlsqlCallback")

    connection = pool.acquire(tag="NLS_DATE_FORMAT=SIMPLE",
                              # DRCP options, if you are using DRCP
                              cclass='MYCLASS',
                              purity=oracledb.ATTR_PURITY_SELF)

See `session_callback_plsql.py
<https://github.com/oracle/python-oracledb/tree/main/
samples/session_callback_plsql.py>`__ for an example.

.. _connpooltypes:

Heterogeneous and Homogeneous Connection Pools
----------------------------------------------

By default, connection pools are 'homogeneous', meaning that all connections
use the same database credentials.  Both python-oracledb Thin and :ref:`Thick
<enablingthick>` modes support homogeneous pools.

**Creating Heterogeneous Pools**

The python-oracledb Thick mode additionally supports Heterogeneous pools,
allowing different user names and passwords to be passed to each
:meth:`~ConnectionPool.acquire()` call.

To create an heterogeneous pool, set the :meth:`~oracledb.create_pool()`
parameter ``homogeneous`` to False:

.. code-block:: python

    pool = oracledb.create_pool(dsn="dbhost.example.com/orclpdb", homogeneous=False)
    connection = pool.acquire(user="hr", password=userpwd)

.. _usingpoolparams:

Using the PoolParams Builder Class
----------------------------------

The :ref:`PoolParams class <poolparam>` allows you to define connection and
pool parameters in a single place.  The :func:`oracledb.PoolParams()` function
returns a ``PoolParams`` object.  This is a subclass of the :ref:`ConnectParams
class <connparam>` with additional pool-specific attributes such as the pool
size.  A ``PoolParams`` object can be passed to
:func:`oracledb.create_pool()`. For example:

.. code-block:: python

    pp = oracledb.PoolParams(min=1, max=2, increment=1)
    pool = oracledb.create_pool(user="hr", password=userpw, dsn="dbhost.example.com/orclpdb",
                                params=pp)

The use of the PoolParams class is optional because you can pass the same
parameters directly to :func:`~oracledb.create_pool()`.  For example, the code
above is equivalent to:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpw, dsn="dbhost.example.com/orclpdb",
                                min=1, max=2, increment=1)

Most PoolParams arguments are gettable as properties.  They may be set
individually using the ``set()`` method:

.. code-block:: python

    pp = oracledb.PoolParams()
    pp.set(min=5)
    print(pp.min) # 5

Some values such as the database host name, can be specified as
:func:`oracledb.create_pool()` parameters, as part of the connect string, and
in the ``params`` object.  If a ``dsn`` is passed, the python-oracledb
:ref:`Thick <enablingthick>` mode will use the ``dsn`` string to connect.
Otherwise, a connection string is internally constructed from the individual
parameters and ``params`` object values, with the individual parameters having
precedence.  In python-oracledb's default Thin mode, a connection string is
internally used that contains all relevant values specified.  The precedence in
Thin mode is that values in any ``dsn`` parameter override values passed as
individual parameters, which themselves override values set in the ``params``
object.  Similar precedence rules also apply to other values.

.. _drcp:

Database Resident Connection Pooling (DRCP)
===========================================

`Database Resident Connection Pooling (DRCP)
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-015CA8C1-2386-4626-855D-CC546DDC1086>`__ enables database resource
sharing for applications which use a large number of connections that run in
multiple client processes or run on multiple middle-tier application servers.
By default, each connection from Python will use one database server process.
DRCP allows pooling of these server processes.  This reduces the amount of
memory required on the database host.  The DRCP pool can be shared by multiple
applications.

DRCP is useful for applications which share the same database credentials, have
similar session settings (for example date format settings or PL/SQL package
state), and where the application gets a database connection, works on it for a
relatively short duration, and then releases it.

For efficiency, it is recommended that DRCP connections should be used in
conjunction with python-oracledb's local :ref:`connection pool <connpooling>`.
However, although using DRCP with standalone connections is not as efficient
it does allow the database to reuse database server processes which can provide
a performance benefit for applications that cannot use a local connection pool.

Although applications can choose whether or not to use pooled connections at
runtime, care must be taken to configure the database appropriately for the
number of expected connections, and also to stop inadvertent use of non-DRCP
connections leading to a database server resource shortage. Conversely, avoid
using DRCP connections for long-running operations.

For more information about DRCP, see `Oracle Database Concepts Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-531EEE8A-B00A-4C03-A2ED-D45D92B3F797>`__ and for DRCP Configuration,
see `Oracle Database Administrator's Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-82FF6896-F57E-41CF-89F7-755F3BC9C924>`__.

Using DRCP with python-oracledb applications involves the following steps:

1. Configuring and enabling DRCP in the database
2. Configuring the application to use a DRCP connection
3. Deploying the application

Enabling DRCP in Oracle Database
--------------------------------

Every Oracle Database uses a single, default DRCP connection pool.  From Oracle
Database 21c, each pluggable database can optionally have its own pool.  Note
that DRCP is already enabled in Oracle Autonomous Database and pool management
is different to the steps below.

DRCP pools can be configured and administered by a DBA using the
``DBMS_CONNECTION_POOL`` package:

.. code-block:: sql

    EXECUTE DBMS_CONNECTION_POOL.CONFIGURE_POOL(
        pool_name => 'SYS_DEFAULT_CONNECTION_POOL',
        minsize => 4,
        maxsize => 40,
        incrsize => 2,
        session_cached_cursors => 20,
        inactivity_timeout => 300,
        max_think_time => 600,
        max_use_session => 500000,
        max_lifetime_session => 86400)

Alternatively, the method ``DBMS_CONNECTION_POOL.ALTER_PARAM()`` can
set a single parameter:

.. code-block:: sql

    EXECUTE DBMS_CONNECTION_POOL.ALTER_PARAM(
        pool_name => 'SYS_DEFAULT_CONNECTION_POOL',
        param_name => 'MAX_THINK_TIME',
        param_value => '1200')

The ``inactivity_timeout`` setting terminates idle pooled servers, helping
optimize database resources.  To avoid pooled servers permanently being held
onto by a selfish Python script, the ``max_think_time`` parameter can be set.
The parameters ``num_cbrok`` and ``maxconn_cbrok`` can be used to distribute
the persistent connections from the clients across multiple brokers.  This may
be needed in cases where the operating system per-process descriptor limit is
small.  Some customers have found that having several connection brokers
improves performance.  The ``max_use_session`` and ``max_lifetime_session``
parameters help protect against any unforeseen problems affecting server
processes.  The default values will be suitable for most users.  See the
`Oracle DRCP documentation
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-015CA8C1-2386-4626-855D-CC546DDC1086>`__ for details on parameters.

In general, if pool parameters are changed, then the pool should be restarted.
Otherwise, server processes will continue to use old settings.

There is a ``DBMS_CONNECTION_POOL.RESTORE_DEFAULTS()`` procedure to
reset all values.

When DRCP is used with RAC, each database instance has its own connection
broker and pool of servers.  Each pool has the identical configuration.  For
example, all pools start with ``minsize`` server processes.  A single
DBMS_CONNECTION_POOL command will alter the pool of each instance at the same
time.  The pool needs to be started before connection requests begin.  The
command below does this by bringing up the broker, which registers itself with
the database listener:

.. code-block:: sql

    EXECUTE DBMS_CONNECTION_POOL.START_POOL()

Once enabled this way, the pool automatically restarts when the database
instance restarts, unless explicitly stopped with the
``DBMS_CONNECTION_POOL.STOP_POOL()`` command:

.. code-block:: sql

    EXECUTE DBMS_CONNECTION_POOL.STOP_POOL()

The pool cannot be stopped while connections are open.

Coding Applications to use DRCP
-------------------------------

To use DRCP, application connection establishment must request a DRCP pooled
server.  The best practice is also to specify a user-chosen connection class
name.  A 'purity' of the connection session state can optionally be specified.
See the Oracle Database documentation on `benefiting from scalability
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-661BB906-74D2-4C5D-9C7E-2798F76501B3>`__
for more information on purity and connection classes.

To request the database, use a DRCP pooled server and you can use a specific
connection string in :meth:`oracledb.create_pool()` or
:meth:`oracledb.connect()` like one of the following syntaxes.

For example with the :ref:`Easy Connect syntax <easyconnect>`:

.. code-block:: python

    dsn = "dbhost.example.com/orcl:pooled"

Alternatively, add ``(SERVER=POOLED)`` to the connect descriptor such as used in
an Oracle Network configuration file ``tnsnames.ora``::

    customerpool = (DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)
              (HOST=dbhost.example.com)
              (PORT=1521))(CONNECT_DATA=(SERVICE_NAME=CUSTOMER)
              (SERVER=POOLED)))

You can also specify to use a DRCP pooled server by setting the ``server_type``
parameter when creating a standalone connection or creating a python-oracledb
connection pool.  For example:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb",
                                min=2, max=5, increment=1,
                                server_type="pooled")


**DRCP Connection Class Names**

The best practice is to specify a ``cclass`` class name when creating a
python-oracledb connection pool.  This user-chosen name provides some
partitioning of DRCP session memory so reuse is limited to similar
applications.  It provides maximum pool sharing if multiple application
processes are started.  A class name also allows better DRCP usage tracking in
the database.  In the database monitoring views, the class name shown will be
the value specified in the application prefixed with the user name.

To create a connection pool requesting a DRCP pooled server and specifying a
class name you can call:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb:pooled",
                                min=2, max=5, increment=1,
                                cclass="MYAPP")

The python-oracledb connection pool size does not need to match the DRCP pool
size.  The limit on overall execution parallelism is determined by the DRCP
pool size.

Connection class names can also be passed to :meth:`~ConnectionPool.acquire()`,
if desired:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb:pooled",
                                min=2, max=5, increment=1,
                                cclass="MYAPP")

    connection = mypool.acquire(cclass="OTHERAPP")

If a pooled server of a requested class is not available, a server with new
session state is used.  If the DRCP pool cannot grow, a server with a different
class may be used and its session state cleared.

If ``cclass`` is not set, then the pooled server sessions will not be reused
optimally, and the DRCP statistic views may record large values for NUM_MISSES.

**DRCP Connection Purity**

DRCP allows the connection session memory to be reused or cleaned each time a
connection is acquired from the pool.  The pool or connection creation
``purity`` parameter can be one of ``PURITY_NEW``, ``PURITY_SELF``, or
``PURITY_DEFAULT``.  The value ``PURITY_SELF`` allows reuse of both the pooled
server process and session memory, giving maximum benefit from DRCP.  By
default, python-oracledb pooled connections use ``PURITY_SELF`` and standalone
connections use ``PURITY_NEW``.

To limit session sharing, you can explicitly require that new session memory be
allocated each time :meth:`~ConnectionPool.acquire()` is called:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb:pooled",
                                min=2, max=5, increment=1,
                                cclass="MYAPP", purity=oracledb.PURITY_NEW)

**Setting the Connection Class and Purity in the Connection String**

For the python-oracledb Thin mode, you can specify the class and purity in the
connection string itself.  This removes the need to modify an existing
application when you want to use DRCP:

.. code-block:: python

    dsn = "localhost/orclpdb:pooled?pool_connection_class=MYAPP&pool_purity=self"

Recent versions of Oracle Client libraries also support this syntax. However,
explicitly specifying the purity as SELF in this way may cause some unusable
connections in a python-oracledb Thick mode connection pool not to be
terminated.  In summary, if you cannot programmatically set the class name and
purity, or cannot use python-oracledb Thin mode, then avoid explicitly setting
the purity as a connection string parameter when using a python-oracledb
connection pooling in Thick mode.

**Closing Connections when using DRCP**

Similar to using a python-oracledb connection pool, Python scripts where
python-oracledb connections do not go out of scope quickly (which releases
them), or do not currently use :meth:`Connection.close()` or
:meth:`ConnectionPool.release()` should be examined to see if the connections
can be closed earlier.  This allows maximum reuse of DRCP pooled servers by
other users:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb:pooled",
                                min=2, max=5, increment=1,
                                cclass="MYAPP")

    # Do some database operations
    connection = mypool.acquire()
    . . .
    connection.close();             # <- Add this to release the DRCP pooled server

    # Do lots of non-database work
    . . .

    # Do some more database operations
    connection = mypool.acquire()   # <- And get a new pooled server only when needed
    . . .
    connection.close();

.. _monitoringdrcp:

Monitoring DRCP
---------------

Data dictionary views are available to monitor the performance of DRCP.
Database administrators can check statistics such as the number of busy and
free servers, and the number of hits and misses in the pool against the total
number of requests from clients. The views include:

* ``DBA_CPOOL_INFO``
* ``V$PROCESS``
* ``V$SESSION``
* ``V$CPOOL_STATS``
* ``V$CPOOL_CC_STATS``
* ``V$CPOOL_CONN_INFO``

**DBA_CPOOL_INFO View**

``DBA_CPOOL_INFO`` displays configuration information about the DRCP pool.  The
columns are equivalent to the ``dbms_connection_pool.configure_pool()``
settings described in the table of DRCP configuration options, with the
addition of a ``STATUS`` column.  The status is ``ACTIVE`` if the pool has been
started and ``INACTIVE`` otherwise.  Note that the pool name column is called
``CONNECTION_POOL``.  This example checks whether the pool has been started and
finds the maximum number of pooled servers::

    SQL> SELECT connection_pool, status, maxsize FROM dba_cpool_info;

    CONNECTION_POOL              STATUS        MAXSIZE
    ---------------------------- ---------- ----------
    SYS_DEFAULT_CONNECTION_POOL  ACTIVE             40

**V$PROCESS and V$SESSION Views**

The ``V$SESSION`` view shows information about the currently active DRCP
sessions.  It can also be joined with ``V$PROCESS`` through
``V$SESSION.PADDR = V$PROCESS.ADDR`` to correlate the views.

**V$CPOOL_STATS View**

The ``V$CPOOL_STATS`` view displays information about the DRCP statistics for
an instance.  The V$CPOOL_STATS view can be used to assess how efficient the
pool settings are.  This example query shows an application using the pool
effectively.  The low number of misses indicates that servers and sessions were
reused.  The wait count shows just over 1% of requests had to wait for a pooled
server to become available::

    NUM_REQUESTS   NUM_HITS NUM_MISSES  NUM_WAITS
    ------------ ---------- ---------- ----------
           10031      99990         40       1055

If ``cclass`` was set (allowing pooled servers and sessions to be
reused), then NUM_MISSES will be low.  If the pool maxsize is too small for
the connection load, then NUM_WAITS will be high.

**V$CPOOL_CC_STATS View**

The view ``V$CPOOL_CC_STATS`` displays information about the connection class
level statistics for the pool per instance::

    SQL> SELECT cclass_name, num_requests, num_hits, num_misses
         FROM v$cpool_cc_stats;

    CCLASS_NAME                      NUM_REQUESTS   NUM_HITS NUM_MISSES
    -------------------------------- ------------ ---------- ----------
    HR.MYCLASS                             100031      99993         38


The class name columns shows the database user name appended with the
connection class name.

**V$CPOOL_CONN_INFO View**

The ``V$POOL_CONN_INFO`` view gives insight into client processes that are
connected to the connection broker, making it easier to monitor and trace
applications that are currently using pooled servers or are idle. This view was
introduced in Oracle 11gR2.

You can monitor the view ``V$CPOOL_CONN_INFO`` to, for example, identify
misconfigured machines that do not have the connection class set correctly.
This view maps the machine name to the class name.  In python-oracledb Thick
mode, the class name will be default to one like shown below::

    SQL> SELECT cclass_name, machine FROM v$cpool_conn_info;

    CCLASS_NAME                             MACHINE
    --------------------------------------- ------------
    CJ.OCI:SP:wshbIFDtb7rgQwMyuYvodA        cjlinux

In this example, you would examine applications on ``cjlinux`` and make them
set ``cclass``.

When connecting to Oracle Autonomous Database on shared infrastructure (ADB-S),
the ``V$CPOOL_CONN_INFO`` view can be used to track the number of connection
hits and misses to show the pool efficiency.

.. _proxyauth:

Connecting Using Proxy Authentication
=====================================

Proxy authentication allows a user (the "session user") to connect to Oracle
Database using the credentials of a "proxy user".  Statements will run as the
session user.  Proxy authentication is generally used in three-tier applications
where one user owns the schema while multiple end-users access the data.  For
more information about proxy authentication, see the `Oracle documentation
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-D77D0D4A-7483-423A-9767-CBB5854A15CC>`__.

An alternative to using proxy users is to set
:attr:`Connection.client_identifier` after connecting and use its value in
statements and in the database, for example for :ref:`monitoring
<endtoendtracing>`.

The following proxy examples use these schemas.  The ``mysessionuser`` schema is
granted access to use the password of ``myproxyuser``:

.. code-block:: sql

    CREATE USER myproxyuser IDENTIFIED BY myproxyuserpw;
    GRANT CREATE SESSION TO myproxyuser;

    CREATE USER mysessionuser IDENTIFIED BY itdoesntmatter;
    GRANT CREATE SESSION TO mysessionuser;

    ALTER USER mysessionuser GRANT CONNECT THROUGH myproxyuser;

After connecting to the database, the following query can be used to show the
session and proxy users:

.. code-block:: sql

    SELECT SYS_CONTEXT('USERENV', 'PROXY_USER'),
           SYS_CONTEXT('USERENV', 'SESSION_USER')
    FROM DUAL;

Standalone connection examples:

.. code-block:: python

    # Basic Authentication without a proxy
    connection = oracledb.connect(user="myproxyuser", password="myproxyuserpw",
                                  dsn="dbhost.example.com/orclpdb")
    # PROXY_USER:   None
    # SESSION_USER: MYPROXYUSER

    # Basic Authentication with a proxy
    connection = oracledb.connect(user="myproxyuser[mysessionuser]", password="myproxyuserpw",
                                  dsn="dbhost.example.com/orclpdb")
    # PROXY_USER:   MYPROXYUSER
    # SESSION_USER: MYSESSIONUSER

Pooled connection examples:

.. code-block:: python

    # Basic Authentication without a proxy
    pool = oracledb.create_pool(user="myproxyuser", password="myproxyuserpw",
                                dsn="dbhost.example.com/orclpdb")
    connection = pool.acquire()
    # PROXY_USER:   None
    # SESSION_USER: MYPROXYUSER

    # Basic Authentication with proxy
    pool = oracledb.create_pool(user="myproxyuser[mysessionuser]", password="myproxyuserpw",
                                dsn="dbhost.example.com/orclpdb",
                                homogeneous=False)

    connection = pool.acquire()
    # PROXY_USER:   MYPROXYUSER
    # SESSION_USER: MYSESSIONUSER

Note the use of a :ref:`heterogeneous <connpooltypes>` pool in the example
above.  This is required in this scenario.

.. _extauth:

Connecting Using External Authentication
========================================

Instead of storing the database username and password in Python scripts or
environment variables, database access can be authenticated by an outside
system.  External Authentication allows applications to validate user access by
an external password store (such as an Oracle Wallet), by the operating system,
or with an external authentication service.

.. note::

    Connecting to Oracle Database using external authentication is only
    supported in the python-oracledb Thick mode. See :ref:`enablingthick`.

Using an Oracle Wallet for External Authentication
--------------------------------------------------

The following steps give an overview of using an Oracle Wallet.  Wallets should
be kept securely.  Wallets can be managed with `Oracle Wallet Manager
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-E3E16C82-E174-4814-98D5-EADF1BCB3C37>`__.

In this example the wallet is created for the ``myuser`` schema in the directory
``/home/oracle/wallet_dir``.  The ``mkstore`` command is available from a full
Oracle client or Oracle Database installation.  If you have been given wallet by
your DBA, skip to step 3.

1.  First create a new wallet as the ``oracle`` user::

        mkstore -wrl "/home/oracle/wallet_dir" -create

    This will prompt for a new password for the wallet.

2.  Create the entry for the database user name and password that are currently
    hardcoded in your Python scripts.  Use either of the methods shown below.
    They will prompt for the wallet password that was set in the first step.

    **Method 1 - Using an Easy Connect string**::

        mkstore -wrl "/home/oracle/wallet_dir" -createCredential dbhost.example.com/orclpdb myuser myuserpw

    **Method 2 - Using a connect name identifier**::

        mkstore -wrl "/home/oracle/wallet_dir" -createCredential mynetalias myuser myuserpw

    The alias key ``mynetalias`` immediately following the
    ``-createCredential`` option will be the connect name to be used in Python
    scripts.  If your application connects with multiple different database
    users, you could create a wallet entry with different connect names for
    each.

    You can see the newly created credential with::

        mkstore -wrl "/home/oracle/wallet_dir" -listCredential

3.  Skip this step if the wallet was created using an Easy Connect String.
    Otherwise, add an entry in :ref:`tnsnames.ora <optnetfiles>` for the connect
    name as follows::

        mynetalias =
            (DESCRIPTION =
                (ADDRESS = (PROTOCOL = TCP)(HOST = dbhost.example.com)(PORT = 1521))
                (CONNECT_DATA =
                    (SERVER = DEDICATED)
                    (SERVICE_NAME = orclpdb)
                )
            )

    The file uses the description for your existing database and sets the
    connect name alias to ``mynetalias``, which is the identifier used when
    adding the wallet entry.

4.  Add the following wallet location entry in the :ref:`sqlnet.ora
    <optnetfiles>` file, using the ``DIRECTORY`` you created the wallet in::

        WALLET_LOCATION =
            (SOURCE =
                (METHOD = FILE)
                (METHOD_DATA =
                    (DIRECTORY = /home/oracle/wallet_dir)
                )
            )
        SQLNET.WALLET_OVERRIDE = TRUE

    Examine the Oracle documentation for full settings and values.

5.  Ensure the configuration files are in a default location or TNS_ADMIN is
    set to the directory containing them.  See :ref:`optnetfiles`.

With an Oracle wallet configured, and readable by you, your scripts
can connect using:

.. code-block:: python

    connection = oracledb.connect(externalauth=True, dsn="mynetalias")

or:

.. code-block:: python

    pool = oracledb.create_pool(externalauth=True, homogeneous=False,
                                dsn="mynetalias")
    pool.acquire()

The ``dsn`` must match the one used in the wallet.

After connecting, the query::

    SELECT SYS_CONTEXT('USERENV', 'SESSION_USER') FROM DUAL;

will show::

    MYUSER

.. note::

    Wallets are also used to configure Transport Layer Security (TLS) connections.
    If you are using a wallet like this, you may need a database username and password
    in :meth:`oracledb.connect()` and :meth:`oracledb.create_pool()` calls.

**External Authentication and Proxy Authentication**

The following examples show external wallet authentication combined with
:ref:`proxy authentication <proxyauth>`.  These examples use the wallet
configuration from above, with the addition of a grant to another user::

    ALTER USER mysessionuser GRANT CONNECT THROUGH myuser;

After connection, you can check who the session user is with:

.. code-block:: sql

    SELECT SYS_CONTEXT('USERENV', 'PROXY_USER'),
           SYS_CONTEXT('USERENV', 'SESSION_USER')
    FROM DUAL;

Standalone connection example:

.. code-block:: python

    # External Authentication with proxy
    connection = oracledb.connect(user="[mysessionuser]", dsn="mynetalias")
    # PROXY_USER:   MYUSER
    # SESSION_USER: MYSESSIONUSER

You can also explicitly set the ``externalauth`` parameter to True in standalone
connections as shown below. The ``externalauth`` parameter is optional.

.. code-block:: python

    # External Authentication with proxy when externalauth is set to True
    connection = oracledb.connect(user="[mysessionuser]", dsn="mynetalias",
                                  externalauth=True)
    # PROXY_USER:   MYUSER
    # SESSION_USER: MYSESSIONUSER

Pooled connection example:

.. code-block:: python

    # External Authentication with proxy
    pool = oracledb.create_pool(externalauth=True, homogeneous=False,
                                dsn="mynetalias")
    pool.acquire(user="[mysessionuser]")
    # PROXY_USER:   MYUSER
    # SESSION_USER: MYSESSIONUSER

The following usage is not supported:

.. code-block:: python

    pool = oracledb.create_pool(user="[mysessionuser]", externalauth=True,
                                homogeneous=False, dsn="mynetalias")
    pool.acquire()


Operating System Authentication
-------------------------------

With Operating System authentication, Oracle allows user authentication to be
performed by the operating system.  The following steps give an overview of how
to implement OS Authentication on Linux.

1.  Log in to your computer. The commands used in these steps assume the
    operating system user name is "oracle".

2.  Log in to SQL*Plus as the SYSTEM user and verify the value for the
    ``OS_AUTHENT_PREFIX`` parameter::

        SQL> SHOW PARAMETER os_authent_prefix

        NAME                                 TYPE        VALUE
        ------------------------------------ ----------- ------------------------------
        os_authent_prefix                    string      ops$

3.  Create an Oracle database user using the ``os_authent_prefix`` determined in
    step 2, and the operating system user name:

   .. code-block:: sql

        CREATE USER ops$oracle IDENTIFIED EXTERNALLY;
        GRANT CONNECT, RESOURCE TO ops$oracle;

In Python, connect using the following code:

.. code-block:: python

       connection = oracledb.connect(dsn="mynetalias")

Your session user will be ``OPS$ORACLE``.

If your database is not on the same computer as Python, you can perform testing
by setting the database configuration parameter ``remote_os_authent=true``.
Beware of security concerns because this is insecure.

See `Oracle Database Security Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-37BECE32-58D5-43BF-A098-97936D66968F>`__ for more information about
Operating System Authentication.

.. _tokenauth:

Token-Based Authentication
==========================

Token-Based Authentication allows users to connect to a database by using an
encrypted authentication token without having to enter a database username and
password.  The authentication token must be valid and not expired for the
connection to be successful.  Users already connected will be able to continue
work after their token has expired but they will not be able to reconnect
without getting a new token.

The two authentication methods supported by python-oracledb are
:ref:`Open Authorization (OAuth 2.0) <oauth2>` and :ref:`Oracle
Cloud Infrastructure (OCI) Identity and Access Management (IAM) <iamauth>`.

.. _oauth2:

Connecting Using OAuth 2.0 Token-Based Authentication
-----------------------------------------------------

Oracle Cloud Infrastructure (OCI) users can be centrally managed in a Microsoft
Azure Active Directory (Azure AD) service. Open Authorization (OAuth 2.0) token-based
authentication allows users to authenticate to Oracle Database using Azure AD OAuth2
tokens. Currently, only Azure AD tokens are supported. Ensure that you have a
Microsoft Azure account and your Oracle Database is registered with Azure AD. See
`Configuring the Oracle Autonomous Database for Microsoft Azure AD Integration
<https://www.oracle.com/pls/topic/lookup?ctx=db19&id=
GUID-0A60F22D-56A3-408D-8EC8-852C38C159C0>`_ for more information.
Both Thin and Thick modes of the python-oracledb driver support OAuth 2.0 token-based
authentication.

When using python-oracledb in Thick mode, Oracle Client libraries 19.15 (or later),
or 21.7 (or later) are needed.

OAuth 2.0 token-based authentication can be used for both standalone connections
and connection pools. Tokens can be specified using the connection parameter
introduced in python-oracledb 1.1. Users of earlier python-oracledb versions
can alternatively use
:ref:`OAuth 2.0 Token-Based Authentication Connection Strings<oauth2connstr>`.

OAuth2 Token Generation And Extraction
++++++++++++++++++++++++++++++++++++++

There are different ways to retrieve Azure AD OAuth2 tokens. Some of the ways to
retrieve the OAuth2 tokens are detailed in `Examples of Retrieving Azure AD OAuth2
Tokens <https://www.oracle.com/pls/topic/lookup?ctx=db19&id=
GUID-3128BDA4-A233-48D8-A2B1-C8380DBDBDCF>`_. You can also retrieve Azure AD OAuth2
tokens by using `Azure Identity client library for Python
<https://docs.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=
azure-python>`_.

.. _oauthhandler:

Example of Using a TokenHandlerOAuth Class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here, as an example, we are using a Python script to automate the
process of generating and reading the Azure AD OAuth2 tokens.

.. code:: python

    import json
    import os

    import oracledb
    import requests

    class TokenHandlerOAuth:

        def __init__(self,
                     file_name="cached_token_file_name",
                     api_key="api_key",
                     client_id="client_id",
                     client_secret="client_secret"):
            self.token = None
            self.file_name = file_name
            self.url = \
                f"https://login.microsoftonline.com/{api_key}/oauth2/v2.0/token"
            self.scope = \
                f"https://oracledevelopment.onmicrosoft.com/{client_id}/.default"
            if os.path.exists(file_name):
                with open(file_name) as f:
                    self.token = f.read().strip()
            self.api_key = api_key
            self.client_id = client_id
            self.client_secret = client_secret

        def __call__(self, refresh):
            if self.token is None or refresh:
                post_data = dict(client_id=self.client_id,
                                 grant_type="client_credentials",
                                 scope=self.scope,
                                 client_secret=self.client_secret)
                r = requests.post(url=self.url, data=post_data)
                result = json.loads(r.text)
                self.token = result["access_token"]
                with open(self.file_name, "w") as f:
                    f.write(self.token)
            return self.token

The TokenHandlerOAuth class uses a callable to generate and read the OAuth2
tokens. When the callable in the TokenHandlerAuth class is invoked for the
first time to create a standalone connection or pool, the ``refresh`` parameter
is False which allows the callable to return a cached token, if desired. The
expiry date is then extracted from this token and compared with the current
date. If the token has not expired, then it will be used directly. If the token
has expired, the callable is invoked the second time with the ``refresh``
parameter set to True.

See :ref:`curl` for an alternative way to generate the tokens.

Standalone Connection Creation with OAuth2 Access Tokens
++++++++++++++++++++++++++++++++++++++++++++++++++++++++

For OAuth 2.0 Token-Based Authentication, the ``access_token`` connection parameter
must be specified. This parameter should be a string (or a callable that returns a
string) specifying an Azure AD OAuth2 token.

Standalone connections can be created in the python-oracledb Thick and Thin modes
using OAuth 2.0 token-based authentication. In the examples below, the
``access_token`` parameter is set to a callable.

**In python-oracledb Thin mode**

When connecting to Oracle Cloud Database with mutual TLS (mTLS) using OAuth2
tokens in the python-oracledb Thin mode, you need to explicitly set the
``config_dir``, ``wallet_location``, and ``wallet_password`` parameters of
:func:`~oracledb.connect`. See, :ref:`autonomousdb`.
The following example shows a standalone connection creation using OAuth 2.0 token
based authentication in the python-oracledb Thin mode. For information on
TokenHandlerOAuth() used in the example, see :ref:`oauthhandler`.

.. code:: python

    connection = oracledb.connect(access_token=TokenHandlerOAuth(),
                                  dsn=mydb_low,
                                  config_dir="path_to_extracted_wallet_zip",
                                  wallet_location="location_of_pem_file",
                                  wallet_password=wp)

**In python-oracledb Thick mode**

In the python-oracledb Thick mode, you can create a standalone connection using
OAuth2 tokens as shown in the example below. For information on
TokenHandlerOAuth() used in the example, see :ref:`oauthhandler`.

.. code:: python

    connection = oracledb.connect(access_token=TokenHandlerOAuth(),
                                  externalauth=True,
                                  dsn=mydb_low)

Connection Pool Creation with OAuth2 Access Tokens
++++++++++++++++++++++++++++++++++++++++++++++++++

For OAuth 2.0 Token-Based Authentication, the ``access_token`` connection
parameter must be specified. This parameter should be a string (or a callable
that returns a string) specifying an Azure AD OAuth2 token.

The ``externalauth`` parameter must be set to True in the python-oracledb Thick
mode.  The ``homogeneous`` parameter must be set to True in both the
python-oracledb Thin and Thick modes.

Connection pools can be created in the python-oracledb Thick and Thin modes
using OAuth 2.0 token-based authentication. In the examples below, the
``access_token`` parameter is set to a callable.

Note that the ``access_token`` parameter should be set to a callable. This is
useful when the connection pool needs to expand and create new connections but
the current token has expired. In such case, the callable should return a
string specifying the new, valid Azure AD OAuth2 token.

**In python-oracledb Thin mode**

When connecting to Oracle Cloud Database with mutual TLS (mTLS) using OAuth2
tokens in the python-oracledb Thin mode, you need to explicitly set the
``config_dir``, ``wallet_location``, and ``wallet_password`` parameters of
:func:`~oracledb.create_pool`. See, :ref:`autonomousdb`.
The following example shows a connection pool creation using OAuth 2.0 token
based authentication in the python-oracledb Thin mode. For information on
TokenHandlerOAuth() used in the example, see :ref:`oauthhandler`.

.. code:: python

    connection = oracledb.create_pool(access_token=TokenHandlerOAuth(),
                                      homogeneous=True, dsn=mydb_low,
                                      config_dir="path_to_extracted_wallet_zip",
                                      wallet_location="location_of_pem_file",
                                      wallet_password=wp
                                      min=1, max=5, increment=2)

**In python-oracledb Thick mode**

In the python-oracledb Thick mode, you can create a connection pool using
OAuth2 tokens as shown in the example below. For information on
TokenHandlerOAuth() used in the example, see :ref:`oauthhandler`.

.. code:: python

    pool = oracledb.create_pool(access_token=TokenHandlerOAuth(),
                                externalauth=True, homogeneous=True,
                                dsn=mydb_low, min=1, max=5, increment=2)

.. _oauth2connstr:

OAuth 2.0 Token-Based Authentication Connection Strings
+++++++++++++++++++++++++++++++++++++++++++++++++++++++

The connection string used by python-oracledb can specify the directory where
the token file is located. This syntax is usable with older versions of
python-oracledb. However, it is recommended to use connection parameters
introduced in python-oracledb 1.1 instead. See
:ref:`OAuth 2.0 Token-Based Authentication<oauth2>`.

.. note::

    OAuth 2.0 Token-Based Authentication Connection Strings is only supported in
    the python-oracledb Thick mode. See :ref:`enablingthick`.

There are different ways to retrieve Azure AD OAuth2 tokens. Some of the ways to
retrieve the OAuth2 tokens are detailed in `Examples of Retrieving Azure AD OAuth2
Tokens <https://www.oracle.com/pls/topic/lookup?ctx=db19&id=
GUID-3128BDA4-A233-48D8-A2B1-C8380DBDBDCF>`_. You can also retrieve Azure AD OAuth2
tokens by using `Azure Identity client library for Python
<https://docs.microsoft.com/en-us/python/api/overview/azure/identity-readme?view=
azure-python>`_.

.. _curl:

Example of Using a Curl Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here, as an example, we are using Curl with a Resource Owner
Password Credential (ROPC) Flow, that is, a ``curl`` command is used against
the Azure AD API to get the Azure AD OAuth2 token::

    curl -X POST -H 'Content-Type: application/x-www-form-urlencoded'
    https://login.microsoftonline.com/your_tenant_id/oauth2/v2.0/token
    -d 'client_id=your_client_id'
    -d 'grant_type=client_credentials'
    -d 'scope=https://oracledevelopment.onmicrosoft.com/your_client_id/.default'
    -d 'client_secret=your_client_secret'

This command generates a JSON response with token type, expiration, and access
token values. The JSON response needs to be parsed so that only the access
token is written and stored in a file. You can save the value of
``access_token`` generated to a file and set ``TOKEN_LOCATION`` to the location
of token file. See :ref:`oauthhandler` for an example of using the
TokenHandlerOAuth class to generate and read tokens.

The Oracle Net parameters ``TOKEN_AUTH`` and ``TOKEN_LOCATION`` must be set when
you are using the connection string syntax. Also, the ``PROTOCOL``
parameter must be ``tcps`` and ``SSL_SERVER_DN_MATCH`` should be ``ON``.

You can set ``TOKEN_AUTH=OAUTH``. There is no default location set in this
case, so you must set ``TOKEN_LOCATION`` to either of the following:

*  A directory, in which case, you must create a file named ``token`` which
   contains the token value
*  A fully qualified file name, in which case, you must specify the entire path
   of the file which contains the token value

You can either set ``TOKEN_AUTH`` and ``TOKEN_LOCATION`` in a sqlnet.ora file or
alternatively, you can specify it inside a connect descriptor stored in
:ref:`tnsnames.ora<optnetfiles>` file, for example::

    db_alias =
        (DESCRIPTION =
            (ADDRESS=(PROTOCOL=TCPS)(PORT=1522)(HOST=xxx.oraclecloud.com))
            (CONNECT_DATA=(SERVICE_NAME=xxx.adb.oraclecloud.com))
            (SECURITY =
                (SSL_SERVER_CERT_DN="CN=xxx.oraclecloud.com,OU=Oracle BMCS US, \
                 O=Oracle Corporation,L=Redwood City,ST=California,C=US")
                (TOKEN_AUTH=OAUTH)
                (TOKEN_LOCATION="/home/user1/mytokens/oauthtoken")
            )
        )

The ``TOKEN_AUTH`` and ``TOKEN_LOCATION`` values in a connection string take
precedence over the ``sqlnet.ora`` settings.

Standalone connection example:

.. code-block:: python

    connection = oracledb.connect(dsn=db_alias, externalauth=True)

Connection pool example:

.. code-block:: python

    pool = oracledb.create_pool(dsn=db_alias, externalauth=True,
                                homogeneous=False, min=1, max=2, increment=1)

    connection = pool.acquire()


.. _iamauth:

Connecting Using OCI IAM Token-Based Authentication
---------------------------------------------------

Oracle Cloud Infrastructure (OCI) Identity and Access Management (IAM) provides
its users with a centralized database authentication and authorization system.
Using this authentication method, users can use the database access token issued
by OCI IAM to authenticate to the Oracle Cloud Database. Both Thin and Thick modes
of the python-oracledb driver support OCI IAM token-based authentication.

When using python-oracledb in Thick mode, Oracle Client libraries 19.14 (or later),
or 21.5 (or later) are needed.

OCI IAM token-based authentication can be used for both standalone connections and
connection pools. Tokens can be specified using the connection parameter
introduced in python-oracledb 1.1. Users of earlier python-oracledb versions
can alternatively use :ref:`OCI IAM Token-Based Authentication Connection Strings
<iamauthconnstr>`.

OCI IAM Token Generation and Extraction
+++++++++++++++++++++++++++++++++++++++

Authentication tokens can be generated through execution of an Oracle Cloud
Infrastructure command line interface (OCI-CLI) command ::

    oci iam db-token get

On Linux, a folder ``.oci/db-token`` will be created in your home directory.
It will contain the token and private key files needed by python-oracledb.

.. _iamhandler:

Example of Using a TokenHandlerIAM Class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here, as an example, we are using a Python script to automate the process of
generating and reading the OCI IAM tokens.

.. code:: python

    import os

    import oracledb

    class TokenHandlerIAM:

        def __init__(self,
                     dir_name="dir_name",
                     command="oci iam db-token get"):
            self.dir_name = dir_name
            self.command = command
            self.token = None
            self.private_key = None

        def __call__(self, refresh):
            if refresh:
                if os.system(self.command) != 0:
                    raise Exception("token command failed!")
            if self.token is None or refresh:
                self.read_token_info()
            return (self.token, self.private_key)

        def read_token_info(self):
            token_file_name = os.path.join(self.dir_name, "token")
            pkey_file_name = os.path.join(self.dir_name, "oci_db_key.pem")
            with open(token_file_name) as f:
                self.token = f.read().strip()
            with open(pkey_file_name) as f:
                if oracledb.is_thin_mode():
                    self.private_key = f.read().strip()
                else:
                    lines = [s for s in f.read().strip().split("\n")
                             if s not in ('-----BEGIN PRIVATE KEY-----',
                                          '-----END PRIVATE KEY-----')]
                    self.private_key = "".join(lines)

The TokenHandlerIAM class uses a callable to generate and read the OCI IAM
tokens. When the callable in the TokenHandlerIAM class is invoked for the first
time to create a standalone connection or pool, the ``refresh`` parameter is
False which allows the callable to return a cached token, if desired. The
expiry date is then extracted from this token and compared with the current
date. If the token has not expired, then it will be used directly. If the token
has expired, the callable is invoked the second time with the ``refresh``
parameter set to True.

Standalone Connection Creation with OCI IAM Access Tokens
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

For OCI IAM Token-Based Authentication, the ``access_token`` connection parameter
must be specified. This parameter should be a 2-tuple (or a callable that returns
a 2-tuple) containing the token and private key.

Standalone connections can be created in the python-oracledb Thick and Thin modes
using OCI IAM token-based authentication. In the examples below, the
``access_token`` parameter is set to a callable.

**In python-oracledb Thin mode**

When connecting to Oracle Cloud Database with mutual TLS (mTLS) using OCI IAM
tokens in the python-oracledb Thin mode, you need to explicitly set the
``config_dir``, ``wallet_location``, and ``wallet_password`` parameters of
:func:`~oracledb.connect`. See, :ref:`autonomousdb`.
The following example shows a standalone connection creation using OCI IAM token
based authentication in the python-oracledb Thin mode. For information on
TokenHandlerIAM() used in the example, see :ref:`iamhandler`.

.. code:: python

    connection = oracledb.connect(access_token=TokenHandlerIAM(),
                                  dsn=mydb_low,
                                  config_dir="path_to_extracted_wallet_zip",
                                  wallet_location="location_of_pem_file",
                                  wallet_password=wp)

**In python-oracledb Thick mode**

In the python-oracledb Thick mode, you can create a standalone connection using
OCI IAM tokens as shown in the example below. For information on
TokenHandlerIAM() used in the example, see :ref:`iamhandler`.

.. code:: python

    connection = oracledb.connect(access_token=TokenHandlerIAM(),
                                  externalauth=True,
                                  dsn=mydb_low)

Connection Pool Creation with OCI IAM Access Tokens
+++++++++++++++++++++++++++++++++++++++++++++++++++

For OCI IAM Token-Based Authentication, the ``access_token`` connection
parameter must be specified. This parameter should be a 2-tuple (or a callable
that returns a 2-tuple) containing the token and private key.

The ``externalauth`` parameter must be set to True in the python-oracledb Thick
mode.  The ``homogeneous`` parameter must be set to True in both the
python-oracledb Thin and Thick modes.

Connection pools can be created in the python-oracledb Thick and Thin modes
using OCI IAM token-based authentication. In the examples below, the
``access_token`` parameter is set to a callable.

Note that the ``access_token`` parameter should be set to a callable. This is
useful when the connection pool needs to expand and create new connections but
the current token has expired. In such case, the callable should return a
2-tuple (token, private key) specifying the new, valid access token.

**In python-oracledb Thin mode**

When connecting to Oracle Cloud Database with mutual TLS (mTLS) using OCI IAM
tokens in the python-oracledb Thin mode, you need to explicitly set the
``config_dir``, ``wallet_location``, and ``wallet_password`` parameters of
:func:`~oracledb.create_pool`. See, :ref:`autonomousdb`.
The following example shows a connection pool creation using OCI IAM token
based authentication in the python-oracledb Thin mode. For information on
TokenHandlerIAM() used in the example, see :ref:`iamhandler`.

.. code:: python

    connection = oracledb.connect(access_token=TokenHandlerIAM(),
                                  homogeneous=True, dsn=mydb_low,
                                  config_dir="path_to_extracted_wallet_zip",
                                  wallet_location="location_of_pem_file",
                                  wallet_password=wp
                                  min=1, max=5, increment=2)

**In python-oracledb Thick mode**

In the python-oracledb Thick mode, you can create a connection pool using
OCI IAM tokens as shown in the example below. For information on
TokenHandlerIAM() used in the example, see :ref:`iamhandler`.

.. code:: python

    pool = oracledb.create_pool(access_token=TokenHandlerIAM(),
                                externalauth=True,
                                homogeneous=True,
                                dsn=mydb_low,
                                min=1, max=5, increment=2)

.. _iamauthconnstr:

OCI IAM Token-Based Authentication Connection Strings
+++++++++++++++++++++++++++++++++++++++++++++++++++++

The connection string used by python-oracledb can specify the directory where
the token and private key files are located. This syntax is usable with older
versions of python-oracledb. However, it is recommended to use connection
parameters introduced in python-oracledb 1.1 instead. See
:ref:`OCI IAM Token-Based Authentication<iamauth>`.

.. note::

    OCI IAM Token-Based Authentication Connection Strings is only supported in
    the python-oracledb Thick mode. See :ref:`enablingthick`.

The Oracle Cloud Infrastructure command line interface (OCI-CLI) can be used
externally to get tokens and private keys from OCI IAM, for example with the
OCI-CLI ``oci iam db-token get`` command.

The Oracle Net parameter ``TOKEN_AUTH`` must be set when you are using the
connection string syntax. Also, the ``PROTOCOL`` parameter must be ``tcps``
and ``SSL_SERVER_DN_MATCH`` should be ``ON``.

You can set ``TOKEN_AUTH=OCI_TOKEN`` in a ``sqlnet.ora`` file.
Alternatively, you can specify it in a connect descriptor, for example::

    db_alias =
        (DESCRIPTION =
            (ADDRESS=(PROTOCOL=TCPS)(PORT=1522)(HOST=xxx.oraclecloud.com))
            (CONNECT_DATA=(SERVICE_NAME=xxx.adb.oraclecloud.com))
            (SECURITY =
                (SSL_SERVER_CERT_DN="CN=xxx.oraclecloud.com,OU=Oracle BMCS US, \
                 O=Oracle Corporation,L=Redwood City,ST=California,C=US")
                (TOKEN_AUTH=OCI_TOKEN)
            )
        )

The default location for the token and private key is the same default location
that the OCI-CLI tool writes to. For example ``~/.oci/db-token/`` on Linux.

If the token and private key files are not in the default location then their
directory must be specified with the ``TOKEN_LOCATION`` parameter in a
sqlnet.ora file or in a connect descriptor stored inside
:ref:`tnsnames.ora<optnetfiles>` file, for example::

    db_alias =
        (DESCRIPTION =
            (ADDRESS=(PROTOCOL=TCPS)(PORT=1522)(HOST=xxx.oraclecloud.com))
            (CONNECT_DATA=(SERVICE_NAME=xxx.adb.oraclecloud.com))
            (SECURITY =
                (SSL_SERVER_CERT_DN="CN=xxx.oraclecloud.com,OU=Oracle BMCS US, \
                 O=Oracle Corporation,L=Redwood City,ST=California,C=US")
                (TOKEN_AUTH=OCI_TOKEN)
                (TOKEN_LOCATION="/path/to/token/folder")
            )
        )

The ``TOKEN_AUTH`` and ``TOKEN_LOCATION`` values in a connection string take
precedence over the ``sqlnet.ora`` settings.

Standalone connection example:

.. code-block:: python

    connection = oracledb.connect(dsn=db_alias, externalauth=True)

Connection pool example:

.. code-block:: python

    pool = oracledb.create_pool(dsn=db_alias, externalauth=True,
                                homogeneous=False, min=1, max=2, increment=1)

    connection = pool.acquire()


Privileged Connections
======================

The ``mode`` parameter of the function :meth:`oracledb.connect()` specifies
the database privilege that you want to associate with the user.

The example below shows how to connect to Oracle Database as SYSDBA:

.. code-block:: python

    connection = oracledb.connect(user="sys", password=syspwd,
                                  dsn="dbhost.example.com/orclpdb",
                                  mode=oracledb.AUTH_MODE_SYSDBA)

    with connection.cursor() as cursor:
        cursor.execute("GRANT SYSOPER TO hr")

This is equivalent to executing the following in SQL*Plus:

.. code-block:: sql

    CONNECT sys/syspwd AS SYSDBA
    GRANT SYSOPER TO hr;

.. _netencrypt:

Securely Encrypting Network Traffic to Oracle Database
======================================================

You can encrypt data transferred between the Oracle Database and
python-oracledb so that unauthorized parties are not able to view plain text
values as the data passes over the network.

Both python-oracledb Thin and Thick modes support TLS.  Refer to the `Oracle
Database Security Guide <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-41040F53-D7A6-48FA-A92A-0C23118BC8A0>`__ for more configuration
information.

.. _nne:

Native Network Encryption
-------------------------

The python-oracledb :ref:`Thick mode <enablingthick>` can additionally use
Oracle Database's `native network encryption
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-7F12066A-2BA1-476C-809B-BB95A3F727CF>`__.

With native network encryption, the client and database server negotiate a key
using Diffie-Hellman key exchange.  This provides protection against
man-in-the-middle attacks.

Native network encryption can be configured by editing Oracle Net's optional
:ref:`sqlnet.ora <optnetfiles>` configuration file.  The file on either the
database server and/or on each python-oracledb 'client' machine can be
configured.  Parameters control whether data integrity checking and encryption
is required or just allowed, and which algorithms the client and server should
consider for use.

As an example, to ensure all connections to the database are checked for
integrity and are also encrypted, create or edit the Oracle Database
``$ORACLE_HOME/network/admin/sqlnet.ora`` file.  Set the checksum negotiation
to always validate a checksum and set the checksum type to your desired value.
The network encryption settings can similarly be set.  For example, to use the
SHA512 checksum and AES256 encryption use::

    SQLNET.CRYPTO_CHECKSUM_SERVER = required
    SQLNET.CRYPTO_CHECKSUM_TYPES_SERVER = (SHA512)
    SQLNET.ENCRYPTION_SERVER = required
    SQLNET.ENCRYPTION_TYPES_SERVER = (AES256)

If you definitely know that the database server enforces integrity and
encryption, then you do not need to configure python-oracledb separately.  However,
you can also, or alternatively do so, depending on your business needs.  Create
a ``sqlnet.ora`` on your client machine and locate it with other
:ref:`optnetfiles`::

    SQLNET.CRYPTO_CHECKSUM_CLIENT = required
    SQLNET.CRYPTO_CHECKSUM_TYPES_CLIENT = (SHA512)
    SQLNET.ENCRYPTION_CLIENT = required
    SQLNET.ENCRYPTION_TYPES_CLIENT = (AES256)

The client and server sides can negotiate the protocols used if the settings
indicate more than one value is accepted.

Note that these are example settings only. You must review your security
requirements and read the documentation for your Oracle version. In particular,
review the available algorithms for security and performance.

The ``NETWORK_SERVICE_BANNER`` column of the database view
`V$SESSION_CONNECT_INFO
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-9F0DCAEA-A67E-4183-89E7-B1555DC591CE>`__ can be used to verify the
encryption status of a connection.


Resetting Passwords
===================

After connecting to Oracle Database, passwords can be changed by calling
:meth:`Connection.changepassword()`:

.. code-block:: python

    # Get the passwords from somewhere, such as prompting the user
    oldpwd = getpass.getpass(f"Old Password for {username}: ")
    newpwd = getpass.getpass(f"New Password for {username}: ")

    connection.changepassword(oldpwd, newpwd)

When a password has expired and you cannot connect directly, you can connect
and change the password in one operation by using the ``newpassword`` parameter
of the function :meth:`oracledb.connect()` constructor:

.. code-block:: python

    # Get the passwords from somewhere, such as prompting the user
    oldpwd = getpass.getpass(f"Old Password for {username}: ")
    newpwd = getpass.getpass(f"New Password for {username}: ")

    connection = oracledb.connect(user=username, password=oldpwd,
                                  dsn="dbhost.example.com/orclpdb",
                                  newpassword=newpwd)

.. _autonomousdb:

Connecting to Oracle Cloud Autonomous Databases
================================================

Python applications can connect to Oracle Autonomous Database (ADB) in Oracle
Cloud using one-way TLS (Transport Layer Security) or mutual TLS
(mTLS). One-way TLS and mTLS provide enhanced security for authentication and
encryption.

A database username and password are still required for your application
connections.  If you need to create a new database schema so you do not login
as the privileged ADMIN user, refer to the relevant Oracle Cloud documentation,
for example see `Create Database Users
<https://docs.oracle.com/en/cloud/paas/autonomous-database/adbdu/managing-database-
users.html#GUID-5B94EA60-554A-4BA4-96A3-1D5A3ED5878D>`__ in the Oracle
Autonomous Database manual.

.. _onewaytls:

One-way TLS Connection to Oracle Autonomous Database
----------------------------------------------------

With one-way TLS, python-oracledb applications can connect to Oracle ADB
without using a wallet.  Both Thin and Thick modes of the python-oracledb
driver support one-way TLS.  Applications that use the python-oracledb Thick
mode, can connect to the Oracle ADB through one-way TLS only when using Oracle
Client library versions 19.14 (or later) or 21.5 (or later).

To enable one-way TLS for an ADB instance, complete the following steps in an
Oracle Cloud console in the **Autonomous Database Information** section of the
ADB instance details:

1. Click the **Edit** link next to *Access Control List* to update the Access
   Control List (ACL). The **Edit Access Control List** dialog box is displayed.

2. In the **Edit Access Control List** dialog box, select the type of address
   list entries and the corresponding values. You can include the required IP
   addresses, hostnames, or Virtual Cloud Networks (VCNs).  The ACL limits
   access to only the IP addresses or VCNs that have been defined and blocks
   all other incoming traffic.

3. Navigate back to the ADB instance details page and click the **Edit** link
   next to *Mutual TLS (mTLS) Authentication*. The **Edit Mutual TLS Authentication**
   is displayed.

4. In the **Edit Mutual TLS Authentication** dialog box, deselect the
   **Require mutual TLS (mTLS) authentication** check box to disable the mTLS
   requirement on Oracle ADB and click **Save Changes**.

5. Navigate back to the ADB instance details page and click **DB Connection** on
   the top of the page. A **Database Connection** dialog box is displayed.

6. In the Database Connection dialog box, select TLS from the **Connection Strings**
   drop-down list.

7. Copy the appropriate Connection String of the database instance used by your application.

Applications can connect to your Oracle ADB instance using the database
credentials and the copied connect descriptor.  For example, to connect as the
ADMIN user:

.. code-block:: python

    cs = '''(description = (retry_count=20)(retry_delay=3)(address=(protocol=tcps)
               (port=1522)(host=xxx.oraclecloud.com))(connect_data=(service_name=xxx.adb.oraclecloud.com))
               (security=(ssl_server_dn_match=yes)(ssl_server_cert_dn="CN=xxx.oraclecloud.com,OU=Oracle BMCS US,
               O=Oracle Corporation, L=Redwood City, T=California, C=US")))'''

    connection = oracledb.connect(user="admin", password=pw, dsn=cs)


You can download the ADB connection wallet using the **DB Connection** button
and extract the ``tnsnames.ora`` file, or create one yourself if you prefer to
keep connections strings out of application code, see :ref:`netservice`.

You may be interested in the blog post `Easy wallet-less connections to Oracle
Autonomous Databases in Python
<https://blogs.oracle.com/opal/post/easy-way-to-connect-python-applications-to-oracle-autonomous-databases>`__.

.. _twowaytls:

Mutual TLS (mTLS) Connection to Oracle Autonomous Database
----------------------------------------------------------

To enable python-oracledb connections to Oracle Autonomous Database in Oracle
Cloud using mTLS, a wallet needs to be downloaded from the cloud console.  mTLS
is sometimes called Two-way TLS.

Install the Wallet and Network Configuration Files
++++++++++++++++++++++++++++++++++++++++++++++++++

From the Oracle Cloud console for the database, download the wallet zip file
using the **DB Connection** button.  The zip contains the wallet and network
configuration files.  When downloading the zip, the cloud console will ask you
to create a wallet password.  This password is used by python-oracledb in Thin
mode, but not in Thick mode.

Note: keep wallet files in a secure location and only share them and the
password with authorized users.

**In python-oracledb Thin mode**

For python-oracledb in Thin mode, only two files from the zip are needed:

- ``tnsnames.ora`` - Maps net service names used for application connection
  strings to your database services
- ``ewallet.pem`` - Enables SSL/TLS connections in Thin mode. Keep this file
  secure

If you do not have a PEM file, see :ref:`createpem`.

Unzip the wallet zip file and move the required files to a location such as
``/opt/OracleCloud/MYDB``.

Connection can be made using your database credentials and setting the ``dsn``
parameter to the desired network alias from the ``tnsnames.ora`` file.  The
``config_dir`` parameter indicates the directory containing ``tnsnames.ora``.
The ``wallet_location`` parameter is the directory containing the PEM file.  In
this example the files are in the same directory.  The ``wallet_password``
parameter should be set to the password created in the cloud console when
downloading the wallet. For example, to connect as the ADMIN user using the
``mydb_low`` network service name:

.. code-block:: python

    connection = oracledb.connect(user="admin", password=pw, dsn="mydb_low",
                                  config_dir="/opt/OracleCloud/MYDB",
                                  wallet_location="/opt/OracleCloud/MYDB",
                                  wallet_password=wp)

**In python-oracledb Thick mode**

For python-oracledb in Thick mode, only these files from the zip are needed:

- ``tnsnames.ora`` - Maps net service names used for application connection
  strings to your database services
- ``sqlnet.ora`` - Configures Oracle Network settings
- ``cwallet.sso`` - Enables SSL/TLS connections in Thick mode.  Keep this file
  secure

Unzip the wallet zip file.  There are two options for placing the required
files:

- Move the three files to the ``network/admin`` directory of the client
  libraries used by your application. For example if you are using Instant
  Client 19c and it is in ``$HOME/instantclient_19_15``, then you would put the
  wallet files in ``$HOME/instantclient_19_15/network/admin/``.

  Connection can be made using your database credentials and setting the
  ``dsn`` parameter to the desired network alias from the ``tnsnames.ora``
  file.  For example, to connect as the ADMIN user using the ``mydb_low``
  network service name:

  .. code-block:: python

       connection = oracledb.connect(user="admin", password=pw, dsn="mydb_low")

- Alternatively, move the three files to any accessible directory, for example
  ``/opt/OracleCloud/MYDB``.

  Then edit ``sqlnet.ora`` and change the wallet location directory to the
  directory containing the ``cwallet.sso`` file.  For example::

    WALLET_LOCATION = (SOURCE = (METHOD = file) (METHOD_DATA = (DIRECTORY="/opt/OracleCloud/MYDB")))
    SSL_SERVER_DN_MATCH=yes

  Since the ``tnsnames.ora`` and ``sqlnet.ora`` files are not in the default
  location, your application needs to indicate where they are, either with the
  ``config_dir`` parameter to :meth:`oracledb.init_oracle_client()`, or using
  the ``TNS_ADMIN`` environment variable.  See :ref:`Optional Oracle Net
  Configuration Files <optnetfiles>`.  (Neither of these settings are needed,
  and you do not need to edit ``sqlnet.ora``, if you have put all the files in
  the ``network/admin`` directory.)

  For example, to connect as the ADMIN user using the ``mydb_low`` network
  service name:

  .. code-block:: python

       oracledb.init_oracle_client(config_dir="/opt/OracleCloud/MYDB")

       connection = oracledb.connect(user="admin", password=pw, dsn="mydb_low")


In python-oracle Thick mode, to create mTLS connections in one Python process
to two or more Oracle Autonomous Databases, move each ``cwallet.sso`` file to
its own directory.  For each connection use different connection string
``WALLET_LOCATION`` parameters to specify the directory of each ``cwallet.sso``
file.  It is recommended to use Oracle Client libraries 19.17 (or later) when
using multiple wallets.

Access Through a Proxy
+++++++++++++++++++++++

If you are behind a firewall, you can tunnel TLS/SSL connections via a proxy
using `HTTPS_PROXY
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-C672E92D-CE32-4759-9931-92D7960850F7>`__
in the connect descriptor or setting connection attributes.  Successful
connection depends on specific proxy configurations.  Oracle does not recommend
doing this when performance is critical.

**In python-oracledb Thin mode**

The proxy settings can be passed during connection creation:

.. code-block:: python

    connection = oracledb.connect(user="admin", password=pw, dsn="mydb_low",
                                  config_dir="/opt/OracleCloud/MYDB",
                                  wallet_location="/opt/OracleCloud/MYDB", wallet_password=wp,
                                  https_proxy='myproxy.example.com', https_proxy_port=80)

Alternatively, edit ``tnsnames.ora`` and add an ``HTTPS_PROXY`` proxy name and
``HTTPS_PROXY_PORT`` port to the connect descriptor address list of any service
name you plan to use, for example::

    mydb_low = (description=
        (address=
        (https_proxy=myproxy.example.com)(https_proxy_port=80)
        (protocol=tcps)(port=1522)(host= . . . )

.. code-block:: python

    connection = oracledb.connect(user="admin", password=pw, dsn="mydb_low",
                                  config_dir="/opt/OracleCloud/MYDB",
                                  wallet_location="/opt/OracleCloud/MYDB", wallet_password=wp)

**In python-oracledb Thick mode**

Edit ``sqlnet.ora`` and add a line::

    SQLNET.USE_HTTPS_PROXY=on

Edit ``tnsnames.ora`` and add an ``HTTPS_PROXY`` proxy name and
``HTTPS_PROXY_PORT`` port to the connect descriptor address list of any service
name you plan to use, for example::

    mydb_high = (description=
        (address=
        (https_proxy=myproxy.example.com)(https_proxy_port=80)
        (protocol=tcps)(port=1522)(host= . . . )

Using the Easy Connect Syntax with Autonomous Database
+++++++++++++++++++++++++++++++++++++++++++++++++++++++

When python-oracledb is using Oracle Client libraries 19c or later, you can
optionally use the :ref:`Easy Connect <easyconnect>` syntax to connect to
Oracle Autonomous Database.

The mapping from the cloud ``tnsnames.ora`` entries to an Easy Connect Plus
string is::

    protocol://host:port/service_name?wallet_location=/my/dir&retry_count=N&retry_delay=N

For example, if your ``tnsnames.ora`` file had an entry::

    cjjson_high = (description=(retry_count=20)(retry_delay=3)
        (address=(protocol=tcps)(port=1522)
        (host=adb.ap-sydney-1.oraclecloud.com))
        (connect_data=(service_name=abc_cjjson_high.adb.oraclecloud.com))
        (security=(ssl_server_cert_dn="CN=adb.ap-sydney-1.oraclecloud.com,OU=Oracle ADB SYDNEY,O=Oracle Corporation,L=Redwood City,ST=California,C=US")))

Then your applications can connect using the connection string:

.. code-block:: python

    dsn = "tcps://adb.ap-sydney-1.oraclecloud.com:1522/abc_cjjson_high.adb.oraclecloud.com?wallet_location=/Users/cjones/Cloud/CJJSON&retry_count=20&retry_delay=3"
    connection = oracledb.connect(user="hr", password=userpwd, dsn=dsn)

The ``wallet_location`` parameter needs to be set to the directory containing
the ``cwallet.sso`` or ``ewallet.pem`` file from the wallet zip.  The other
wallet files, including ``tnsnames.ora``, are not needed when you use the Easy
Connect Plus syntax.

You can add other Easy Connect parameters to the connection string, for example::

    dsn = dsn + "&https_proxy=myproxy.example.com&https_proxy_port=80"

With python-oracledb Thin mode, the wallet password needs to be passed as a
connection parameter.

.. _createpem:

Creating a PEM File for python-oracledb Thin Mode
+++++++++++++++++++++++++++++++++++++++++++++++++

For mutual TLS in python-oracledb Thin mode, the certificate must be Privacy
Enhanced Mail (PEM) format.  If you are using Oracle Autonomous Database and
your wallet zip file does not already include a PEM file, then you can convert
the PKCS12 ``ewallet.p12`` file to PEM format using third party tools or the
script below.

For example, invoke the conversion script by passing the wallet password and the
directory containing the PKCS file::

    python create_pem.py --wallet-password 'xxxxx' /Users/scott/cloud_configs/MYDBDIR

Once the PEM file has been created, you can use it by passing its directory
location as the ``wallet_location`` parameter to :func:`oracledb.connect()` or
:func:`oracledb.create_pool()`.  These methods also accept a
``wallet_password`` parameter.  See :ref:`twowaytls`.

**Script to convert from PKCS12 to PEM**

.. code-block:: python

    # create_pem.py

    import argparse
    import getpass
    import os

    from cryptography.hazmat.primitives.serialization \
            import pkcs12, Encoding, PrivateFormat, BestAvailableEncryption, \
                   NoEncryption

    # parse command line
    parser = argparse.ArgumentParser(description="convert PKCS#12 to PEM")
    parser.add_argument("wallet_location",
                        help="the directory in which the PKCS#12 encoded "
                             "wallet file ewallet.p12 is found")
    parser.add_argument("--wallet-password",
                        help="the password for the wallet which is used to "
                             "decrypt the PKCS#12 encoded wallet file; if not "
                             "specified, it will be requested securely")
    parser.add_argument("--no-encrypt",
                        dest="encrypt", action="store_false", default=True,
                        help="do not encrypt the converted PEM file with the "
                             "wallet password")
    args = parser.parse_args()

    # validate arguments and acquire password if one was not specified
    pkcs12_file_name = os.path.join(args.wallet_location, "ewallet.p12")
    if not os.path.exists(pkcs12_file_name):
        msg = f"wallet location {args.wallet_location} does not contain " \
               "ewallet.p12"
        raise Exception(msg)
    if args.wallet_password is None:
        args.wallet_password = getpass.getpass()

    pem_file_name = os.path.join(args.wallet_location, "ewallet.pem")
    pkcs12_data = open(pkcs12_file_name, "rb").read()
    result = pkcs12.load_key_and_certificates(pkcs12_data,
                                              args.wallet_password.encode())
    private_key, certificate, additional_certificates = result
    if args.encrypt:
        encryptor = BestAvailableEncryption(args.wallet_password.encode())
    else:
        encryptor = NoEncryption()
    with open(pem_file_name, "wb") as f:
        f.write(private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8,
                                          encryptor))
        f.write(certificate.public_bytes(Encoding.PEM))
        for cert in additional_certificates:
            f.write(cert.public_bytes(Encoding.PEM))
    print("PEM file", pem_file_name, "written.")


.. _connsharding:

Connecting to Sharded Databases
===============================

`Oracle Sharding
<https://www.oracle.com/database/technologies/high-availability/sharding.html>`__
can be used to horizontally partition data across independent databases.  A
database table can be split so each shard contains a table with the same columns
but a different subset of rows.  These tables are known as sharded tables.
Sharding is configured in Oracle Database, see the `Oracle Sharding
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=SHARD>`__ manual.
Sharding requires Oracle Database and Oracle Client libraries 12.2, or later.

.. note::

    Sharding is only supported in the python-oracledb Thick mode.  See
    :ref:`enablingthick`.

The :meth:`oracledb.connect()` and :meth:`ConnectionPool.acquire()` functions
accept ``shardingkey`` and ``supershardingkey`` parameters that are a sequence
of values used to route the connection directly to a given shard.  A sharding
key is always required.  A super sharding key is additionally required when
using composite sharding, which is when data has been partitioned by a list or
range (the super sharding key), and then further partitioned by a sharding key.

When creating a connection pool, the :meth:`oracledb.create_pool()` attribute
``max_sessions_per_shard`` can be set.  This is used to balance connections in
the pool equally across shards.  It requires Oracle Client libraries 18.3 or
later.

Shard key values may be of type string (mapping to VARCHAR2 shard keys), number
(NUMBER), bytes (RAW), or date (DATE).  Multiple types may be used in each
array.  Sharding keys of TIMESTAMP type are not supported.

When connected to a shard, queries will only return data from that shard.  For
queries that need to access data from multiple shards, connections can be
established to the coordinator shard catalog database.  In this case, no shard
key or super shard key is used.

As an example of direct connection, if sharding had been configured on a single
VARCHAR2 column like:

.. code-block:: sql

    CREATE SHARDED TABLE customers (
      cust_id NUMBER,
      cust_name VARCHAR2(30),
      class VARCHAR2(10) NOT NULL,
      signup_date DATE,
      cust_code RAW(20),
      CONSTRAINT cust_name_pk PRIMARY KEY(cust_name))
      PARTITION BY CONSISTENT HASH (cust_name)
      PARTITIONS AUTO TABLESPACE SET ts1;

then direct connection to a shard can be made by passing a single sharding key:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb",
                                  shardingkey=["SCOTT"])

Numbers keys can be used in a similar way:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb",
                                  shardingkey=[110])

When sharding by DATE, you can connect like:

.. code-block:: python

    import datetime

    d = datetime.datetime(2014, 7, 3)

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb",
                                  shardingkey=[d])

When sharding by RAW, you can connect like:

.. code-block:: python

    b = b'\x01\x04\x08';

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb",
                                  shardingkey=[b])

Multiple keys can be specified, for example:

.. code-block:: python

    key_list = [70, "SCOTT", "gold", b'\x00\x01\x02']

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb",
                                  shardingkey=key_list)

A super sharding key example is:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb",
                                  supershardingkey=["goldclass"],
                                  shardingkey=["SCOTT"])
