.. _tracingsql:

***********************
Tracing python-oracledb
***********************

.. _applntracing:

Application Tracing
===================

There are multiple approaches for application tracing and monitoring:

- :ref:`End-to-end database tracing <endtoendtracing>` attributes such as
  :attr:`Connection.action` and :attr:`Connection.module` are supported in the
  python-oracledb Thin and Thick modes.  Using these attributes is recommended
  since they aid application monitoring and troubleshooting.

- You can :ref:`subclass python-oracledb classes <subclassconn>` and implement
  your own driver API call tracing and logging. Also, the standard `Python
  tracing capabilities <https://docs.python.org/3/library/trace.html>`__ can be
  used.

- The Java Debug Wire Protocol (JDWP) for debugging PL/SQL can be used. See
  :ref:`jdwp`.

- Python-oracledb in Thick mode can dump a trace of SQL statements
  executed. See :ref:`lowlevelsqltrace`.

- The connection identifiers that appear in the traces and logs can be used
  to resolve connectivity errors. See :ref:`connectionid`.

.. _endtoendtracing:

Oracle Database End-to-End Tracing
----------------------------------

Oracle Database end-to-end application tracing simplifies diagnosing
application code flow and performance problems in multi-tier or multi-user
environments.

The connection attributes :attr:`Connection.client_identifier`,
:attr:`Connection.clientinfo`, :attr:`Connection.dbop`,
:attr:`Connection.module`, and :attr:`Connection.action` set metadata for
end-to-end tracing. The values can be queried from data dictionary and dynamic
performance views to monitor applications, or you can use tracing
utilities. Values may appear in logs and audit trails.

Also see :ref:`appcontext` for information about setting Application Contexts.

The :attr:`Connection.client_identifier` attribute is typically set to the
name (or identifier) of the actual end user initiating a query.  This allows
the database to distinguish, and trace, end users for applications that connect
to a common database username. It can also be used by `Oracle Virtual Private
Database (VPD) <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-06022729-9210-4895-BF04-6177713C65A7>`__ policies to automatically limit
data access.

The :attr:`Connection.module` and :attr:`Connection.action` attributes can be
set to user-chosen, descriptive values identifying your code architecture.

After attributes are set, the values are sent to the database when the next
:ref:`round-trip <roundtrips>` to the database occurs, for example when the
next SQL statement is executed.

The attribute values will remain set in connections released back to a
connection pool.  When the application re-acquires a connection from the pool,
it should initialize the values to a desired state before using that
connection.

The example below shows setting the action, module, and client identifier
attributes on a connection object, and then querying a view to see the recorded
values.  The example both sets and queries the values, but typically monitoring
is done externally to the application.

.. code-block:: python

    # Set the tracing metadata
    connection.client_identifier = "pythonuser"
    connection.action = "Query Session tracing parameters"
    connection.module = "End-to-end Demo"

    for row in cursor.execute("""
            SELECT username, client_identifier, module, action
            FROM V$SESSION
            WHERE sid = SYS_CONTEXT('USERENV', 'SID')"""):
        print(row)

The output will be like::

    ('SYSTEM', 'pythonuser', 'End-to-end Demo', 'Query Session tracing parameters')

The values can also be manually set by calling `DBMS_APPLICATION_INFO
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-14484F86-44F2-4B34-B34E-0C873D323EAD>`__ procedures or
`DBMS_SESSION.SET_IDENTIFIER <https://www.oracle.com/pls/topic/lookup?
ctx=dblatest&id=GUID-988EA930-BDFE-4205-A806-E54F05333562>`__. These incur
round-trips to the database which reduces application scalability:

.. code-block:: sql

    BEGIN
        DBMS_SESSION.SET_IDENTIFIER('pythonuser');
        DBMS_APPLICATION_INFO.set_module('End-to-End Demo');
        DBMS_APPLICATION_INFO.set_action(action_name => 'Query Session tracing parameters');
    END;

The :attr:`Connection.dbop` attribute can be used for Real-Time SQL Monitoring,
see `Monitoring Database Operations <https://www.oracle.com/pls/topic/lookup?
ctx=dblatest&id=GUID-C941CE9D-97E1-42F8-91ED-4949B2B710BF>`__. The value will
be shown in the DBOP_NAME column of the V$SQL_MONITOR view:

.. code-block:: python

    connection.dbop = "my op"

    for row in cursor.execute("""
            SELECT dbop_name
            FROM V$SQL_MONITOR
            WHERE sid = SYS_CONTEXT('USERENV', 'SID')"""):
        print(row)

.. _jdwp:

Debugging PL/SQL with the Java Debug Wire Protocol
--------------------------------------------------

The Java Debug Wire Protocol (JDWP) for debugging PL/SQL can be used with
python-oracledb.

Python-oracledb applications that call PL/SQL can step through that PL/SQL code
using JDWP in a debugger. This allows Python and PL/SQL code to be debugged in
the same debugger environment. You can enable PL/SQL debugging in
python-oracledb as follows:

- In python-oracledb Thin or Thick modes, set the ``ORA_DEBUG_JDWP``
  environment variable to `host=hostname;port=portnum` indicating where the
  PL/SQL debugger is running.  Then run the application.

- In python-oracledb Thin mode, you can alternatively set the connection
  parameter ``debug_jdwp`` during connection.  This variable defaults to the
  value of the ``ORA_DEBUG_JDWP`` environment variable.

See the documentation on `DBMS_DEBUG_JDWP
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-AFF566A0-9E90-
4218-B5C6-A74C3BF1CE14>`_, the video `PL/SQL debugging with Visual Studio and
Visual Studio Code <https://www.youtube.com/watch?v=wk-3hLe30kk>`_, and the
blog post `Debugging PL/SQL with Visual Studio Code (and more)
<https://medium.com/oracledevs/debugging-pl-sql-with-visual-studio-code-and-
more-45631f3952cf>`_.

.. _lowlevelsqltrace:

Low Level SQL Tracing
---------------------

The Thick mode of python-oracledb is implemented using the
`ODPI-C <https://oracle.github.io/odpi>`__ wrapper on top of the Oracle Client
libraries.  The ODPI-C tracing capability can be used to log executed
python-oracledb statements to the standard error stream. Before executing
Python, set the environment variable ``DPI_DEBUG_LEVEL`` to 16 in your terminal
window.

On Linux, you might use::

    export DPI_DEBUG_LEVEL=16

On Windows, this could be done with::

    set DPI_DEBUG_LEVEL=16

After setting the variable, run the Python Script, for example on Linux::

    python end-to-endtracing.py 2> log.txt

For an application that does a single query, the log file might contain a
tracing line consisting of the prefix 'ODPI', a thread identifier, a timestamp,
and the SQL statement executed::

    ODPI [26188] 2019-03-26 09:09:03.909: ODPI-C 3.1.1
    ODPI [26188] 2019-03-26 09:09:03.909: debugging messages initialized at level 16
    ODPI [26188] 2019-03-26 09:09:09.917: SQL SELECT * FROM jobss
    Traceback (most recent call last):
    File "end-to-endtracing.py", line 14, in <module>
      cursor.execute("select * from jobss")
    oracledb.DatabaseError: ORA-00942: table or view does not exist

See `ODPI-C Debugging
<https://oracle.github.io/odpi/doc/user_guide/debugging.html>`__ for
documentation on ``DPI_DEBUG_LEVEL``.

.. _connectionid:

Using Connection Identifiers
----------------------------

A unique connection identifier (``CONNECTION_ID``) is generated for each
connection to the Oracle Database. The connection identifier is shown in some
Oracle Network error messages and logs, which helps in better tracing and
diagnosing of connection failures. For example::

    DPY-6005: cannot connect to database (CONNECTION_ID=m0PfUY6hYSmWPcgrHZCQIQ==)

You can define a prefix value which is added to the beginning of the
``CONNECTION_ID``. This prefix aids in identifying the connections from a
specific application.

In python-oracledb Thin mode, you can specify a prefix in the
``connection_id_prefix`` parameter when creating
:meth:`standalone connections <oracledb.connect()>`, or
:meth:`pooled connections <oracledb.create_pool()>`. Also, you can specify
the connection identifier in :meth:`oracledb.ConnectParams()` or
:meth:`oracledb.PoolParams()`. For example:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="localhost/orclpdb",
                                  connection_id_prefix="MYAPP")

If this connection to the database fails, ``MYAPP`` is added as a prefix to the
``CONNECTION_ID`` as shown in the error message below::

    DPY-6005: cannot connect to database (CONNECTION_ID=MYAPPm0PfUY6hYSmWPcgrHZCQIQ==).

In python-oracledb Thick mode, you can specify the connection identifier prefix in
a connection string. For example::

    mydb = (DESCRIPTION =
             (ADDRESS_LIST= (ADDRESS=...) (ADDRESS=...))
             (CONNECT_DATA=
                (SERVICE_NAME=sales.us.example.com)
                (CONNECTION_ID_PREFIX=MYAPP)
             )
           )

Depending on the Oracle Database version in use, the information that is shown
in logs varies.

See `Troubleshooting Oracle Net Services <https://www.oracle.com/pls/topic/
lookup?ctx=dblatest&id=GUID-3F42D057-C9AC-4747-B48B-5A5FF7672E5D>`_ for more
information on connection identifiers.

.. _vsessconinfo:

Finding the python-oracledb Mode
================================

The boolean attributes :attr:`Connection.thin` and :attr:`ConnectionPool.thin`
can be used to show the current mode of a python-oracledb connection or pool,
respectively. The method :meth:`oracledb.is_thin_mode()` can also be used, but
review its usage notes about when its return value may change.

For example, to show the mode used by a connection:

.. code-block:: python

    print(connection.thin)

The python-oracledb version can be shown with :data:`oracledb.__version__`:

.. code-block:: python

    print(oracledb.__version__)

Version and mode information can also be seen in the Oracle Database data
dictionary table V$SESSION_CONNECT_INFO:

.. code-block:: python

    with connection.cursor() as cursor:
        sql = """SELECT UNIQUE client_driver
                 FROM V$SESSION_CONNECT_INFO
                 WHERE sid = SYS_CONTEXT('USERENV', 'SID')"""
        for r, in cursor.execute(sql):
            print(r)

In python-oracledb Thin mode, the output will be like::

    python-oracledb thn : 3.0.0

In python-oracledb Thick mode, the output will be like::

    python-oracledb thk : 3.0.0

Note that you may not see these values if you have set
:attr:`oracledb.defaults.driver_name <defaults.driver_name>` or the
``driver_name`` parameter in :meth:`oracledb.init_oracle_client()`.

.. _dbviews:

Database Views
==============

This section shows some sample column values for database views useful for
tracing and monitoring python-oracledb.  Other views also contain useful
information, such as the :ref:`drcp` views discussed in :ref:`monitoringdrcp`.

V$SESSION_CONNECT_INFO
----------------------

The following table lists sample default values for some
`V$SESSION_CONNECT_INFO <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-9F0DCAEA-A67E-4183-89E7-B1555DC591CE>`__ columns. You may not see
values with these formats if you have changed the defaults using the
:ref:`Defaults object <defaults>`, set the equivalent connection or pool
creation parameters, or set the ``driver_name`` parameter in
:meth:`oracledb.init_oracle_client()`.

.. list-table-with-summary:: Sample V$SESSION_CONNECT_INFO column values
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 15 10 10
    :name: V$SESSION_CONNECT_INFO
    :summary: The first column is the name of V$SESSION_CONNECT_INFO view's column. The second column lists a sample python-oracledb Thick mode value. The third column list a sample python-oracledb Thin mode value.

    * - Column
      - Thick value
      - Thin value
    * - CLIENT_OCI_LIBRARY
      - The Oracle Client or Instant Client type, such as "Full Instant Client"
      - "Unknown"
    * - CLIENT_VERSION
      - The Oracle Client library version number
      - "3.0.0.0.0" (the python-oracledb version number with an extra .0.0)
    * - CLIENT_DRIVER
      - "python-oracledb thk : 3.0.0"
      - "python-oracledb thn : 3.0.0"

V$SESSION
---------

The following table lists sample default values for columns with differences in
`V$SESSION <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-28E2DC75-E157-4C0A-94AB-117C205789B9>`__. You may not see values with
these formats if you have changed the defaults using the
:ref:`Defaults object <defaults>`, set the equivalent connection or pool
creation parameters, or set the attribute :attr:`Connection.module` as
shown in :ref:`endtoendtracing`.

.. list-table-with-summary:: Sample V$SESSION column values
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 15 10 10
    :name: V$SESSION_COLUMN_VALUES
    :summary: The first column is the name of the column. The second column lists a sample python-oracledb Thick mode value. The third column lists a sample python-oracledb Thin mode value.

    * - Column
      - Thick value
      - Thin value
    * - TERMINAL
      - similar to `ttys001`
      - the string "unknown"
    * - PROGRAM
      - similar to `python@myuser-mac2 (TNS V1-V3)`
      - the contents of Python's ``sys.executable``, such as `/Users/myuser/.pyenv/versions/3.9.6/bin/python`
    * - MODULE
      - similar to `python@myuser-mac2 (TNS V1-V3)`
      - the contents of Python's ``sys.executable``, such as `/Users/myuser/.pyenv/versions/3.9.6/bin/python`

Low Level Python-oracledb Driver Tracing
========================================

Low level tracing is mostly useful to maintainers of python-oracledb.

- For python-oracledb Thin mode, packets can be traced by setting the
  environment variable PYO_DEBUG_PACKETS in your terminal window before running
  your application.

  For example, on Linux, you might use::

      export PYO_DEBUG_PACKETS=1

  On Windows you might set the variable like::

      set PYO_DEBUG_PACKETS=1

  Alternatively, the variable can be set in the application:

  .. code-block:: python

      import os
      os.environ["PYO_DEBUG_PACKETS"] = "1"
      import oracledb

  The output goes to stdout. The information logged is roughly similar to an
  Oracle Net trace of level 16, see `Oracle Net Services TRACE_LEVEL_CLIENT
  <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
  GUID-1CC6424E-B3B5-4D55-A605-0C558496CBE0>`__.

- Python-oracledb Thick mode can be traced using:

  - DPI_DEBUG_LEVEL as documented in `ODPI-C Debugging
    <https://odpi-c.readthedocs.io/en/latest/user_guide/debugging.html>`__.

  - Oracle Call Interface (OCI) tracing as directed by Oracle Support.

  - Oracle Net services tracing as documented in `Oracle Net Services Tracing
    Parameters <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
    GUID-619D46BB-FE40-4EE1-8D5F-9E7666B23276>`__.
