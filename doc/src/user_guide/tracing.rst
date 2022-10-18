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

- The Java Debug Wire Protocol (JDWP) for debugging PL/SQL can be used. See :ref:`jdwp`.

- Python-oracledb in Thick mode can dump a trace of SQL statements
  executed. See :ref:`lowlevelsqltrace`.

.. _endtoendtracing:

Oracle Database End-to-End Tracing
----------------------------------

Oracle Database end-to-end application tracing simplifies diagnosing
application code flow and performance problems in multi-tier or multi-user
environments.

The connection attributes, :attr:`~Connection.client_identifier`,
:attr:`~Connection.clientinfo`, :attr:`~Connection.dbop`,
:attr:`~Connection.module` and :attr:`~Connection.action`, set the metadata for
end-to-end tracing.  You can query data dictionary and dynamic performance
views to monitor applications, or you can use tracing utilities.

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
            WHERE SID = SYS_CONTEXT('USERENV', 'SID')"""):
        print(row)

The output will be like::

    ('SYSTEM', 'pythonuser', 'End-to-end Demo', 'Query Session tracing parameters')

The values can also be manually set as shown by calling
`DBMS_APPLICATION_INFO procedures
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-14484F86-44F2-4B34-B34E-0C873D323EAD>`__
or `DBMS_SESSION.SET_IDENTIFIER
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-988EA930-BDFE-4205-A806-E54F05333562>`__. These incur round-trips to
the database; however, reducing scalability.

.. code-block:: sql

    BEGIN
        DBMS_SESSION.SET_IDENTIFIER('pythonuser');
        DBMS_APPLICATION_INFO.set_module('End-to-End Demo');
        DBMS_APPLICATION_INFO.set_action(action_name => 'Query Session tracing parameters');
    END;

The value of :attr:`Connection.dbop` will be shown in the ``DBOP_NAME`` column
of the ``V$SQL_MONITOR`` table:

.. code-block:: python

    connection.dbop = "my op"

    for row in cursor.execute("""
            SELECT dbop_name
            FROM v$sql_monitor
            WHERE SID = SYS_CONTEXT('USERENV', 'SID')"""):
        print(row)

.. _subclassconn:

Subclassing Connections
-----------------------

Subclassing enables applications to add "hooks" for connection and statement
execution.  This can be used to alter or log connection and execution
parameters, and to extend python-oracledb functionality.

The example below demonstrates subclassing a connection to log SQL execution
to a file.  This example also shows how connection credentials can be embedded
in the custom subclass, so application code does not need to supply them.

.. code-block:: python

    class Connection(oracledb.Connection):
        log_file_name = "log.txt"

        def __init__(self):
            connect_string = "hr/hr_password@dbhost.example.com/orclpdb"
            self._log("Connect to the database")
            return super(Connection, self).__init__(connect_string)

        def _log(self, message):
            with open(self.log_file_name, "a") as f:
                print(message, file=f)

        def execute(self, sql, parameters):
            self._log(sql)
            cursor = self.cursor()
            try:
                return cursor.execute(sql, parameters)
            except oracledb.Error as e:
                error_obj, = e.args
                self._log(error_obj.message)
                raise

    connection = Connection()
    connection.execute("""
            select department_name
            from departments
            where department_id = :id""", dict(id=270))

The messages logged in ``log.txt`` are::

    Connect to the database

                select department_name
                from departments
                where department_id = :id

If an error occurs, perhaps due to a missing table, the log file would contain
instead::

    Connect to the database

                select department_name
                from departments
                where department_id = :id
    ORA-00942: table or view does not exist

In production applications, be careful not to log sensitive information.

See `Subclassing.py
<https://github.com/oracle/python-oracledb/blob/main/
samples/subclassing.py>`__ for an example.


.. _jdwp:

Debugging PL/SQL with the Java Debug Wire Protocol
--------------------------------------------------

The Java Debug Wire Protocol (JDWP) for debugging PL/SQL can be used with
python-oracledb.

Python-oracledb applications that call PL/SQL can step through that PL/SQL code
using JDWP in a debugger. This allows Python and PL/SQL code to be debugged in
the same debugger environment. You can enable PL/SQL debugging in the
python-oracledb modes as follows:

- If you are using python-oracledb Thick mode, set the ``ORA_DEBUG_JDWP`` environment
  variable to `host=hostname;port=portnum` indicating where the PL/SQL debugger
  is running.  Then run the application.

- In the python-oracledb Thin mode, you can additionally set the connection
  parameter ``debug_jdwp`` during connection.  This variable defaults to the
  value of the ``ORA_DEBUG_JDWP`` environment variable.

See `DBMS_DEBUG_JDWP <https://docs.oracle.com/en/database/oracle/oracle-database
/19/arpls/DBMS_DEBUG_JDWP.html>`_ and `Debugging PL/SQL from ASP.NET and Visual
Studio <http://cshay.blogspot.com/2006/10/debugging-plsql-from-aspnet-and-visual.html>`_.


.. _lowlevelsqltrace:

Low Level SQL Tracing
---------------------

The Thick mode of python-oracledb is implemented using the `ODPI-C <https://oracle.
github.io/odpi>`__ wrapper on top of the Oracle Client libraries.  The ODPI-C tracing
capability can be used to log executed python-oracledb statements to the standard error
stream. Before executing Python, set the environment variable ``DPI_DEBUG_LEVEL`` to 16.

At a Windows command prompt, this could be done with::

    set DPI_DEBUG_LEVEL=16

On Linux, you might use::

    export DPI_DEBUG_LEVEL=16

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

.. _vsessconinfo:

Finding the Python-oracledb Mode
================================

The boolean attributes :attr:`Connection.thin` and :attr:`ConnectionPool.thin`
can be used to show the current mode of a python-oracledb connection or pool,
respectively.  The python-oracledb version can be shown with
:data:`oracledb.__version__`.

The information can also be seen in the Oracle Database data dictionary table
``V$SESSION_CONNECT_INFO``:

.. code-block:: python

    with connection.cursor() as cursor:
        sql = """SELECT UNIQUE CLIENT_DRIVER
                 FROM V$SESSION_CONNECT_INFO
                 WHERE SID = SYS_CONTEXT('USERENV', 'SID')"""
        for r, in cursor.execute(sql):
            print(r)

In the python-oracledb Thin mode, the output will be::

    python-oracledb thn : 1.0.0

In the python-oracledb Thick mode, the output will be::

    python-oracledb thk : 1.0.0

The ``CLIENT_DRIVER`` values is configurable in the python-oracledb Thick mode
with a call like ``init_oracle_client(driver_name='myapp : 2.0.0')``. See
:ref:`otherinit`.


.. _dbviews:

Database Views
==============

This section shows some sample column values for database views.  Other views
also contain useful information, such as the DRCP views discussed in
:ref:`monitoringdrcp`.

``V$SESSION_CONNECT_INFO``
--------------------------

The following table lists sample values for some `V$SESSION_CONNECT_INFO
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-9F0DCAEA-A67E-4183-89E7-B1555DC591CE>`__
columns:

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
      - "1.0.0.0.0" (the python-oracledb version number with an extra .0.0)
    * - CLIENT_DRIVER
      - "python-oracledb thk : 1.0.0"
      - "python-oracledb thn : 1.0.0"


``V$SESSION``
-------------

The following table list sample values for columns with differences in
`V$SESSION
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-28E2DC75-E157-4C0A-94AB-117C205789B9>`__.

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

The ``MODULE`` column value can be set as shown in :ref:`endtoendtracing`.

Low Level Python-oracledb Driver Tracing
========================================

Low level tracing is mostly useful to maintainers of python-oracledb.

- For the python-oracledb Thin mode, packets can be traced by setting the
  environment variable::

      PYO_DEBUG_PACKETS=1

  Output goes to stdout. The logging is similar to an Oracle Net trace of
  level 16.

- The python-oracledb Thick mode can be traced using:

  - dpi_debug_level as documented in `ODPI-C Debugging
    <https://oracle.github.io/odpi/doc/user_guide/debugging.html>`__.

  - Oracle Call Interface (OCI) tracing as directed by Oracle Support.

  - Oracle Net services tracing as documented in `Oracle Net Services Tracing
    Parameters
    <https://docs.oracle.com/en/database/oracle/oracle-database/21/
    netrf/parameters-for-the-sqlnet.ora.html>`__
