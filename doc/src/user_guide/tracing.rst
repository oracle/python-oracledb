.. _tracingsql:

.. currentmodule:: oracledb

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

- Instrumentation libraries such as OpenTelemetry allow sophisticated
  monitoring, see :ref:`opentelemetry`.

- Python-oracledb in Thick mode can dump a trace of SQL statements
  executed. See :ref:`lowlevelsqltrace`.

- The unique connection identifiers that appear in connection error messages,
  and in Oracle Database traces and logs, can be used to resolve connectivity
  errors. See :ref:`connectionid`.

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

The :attr:`Connection.client_identifier` attribute is typically set to the name
(or identifier) of the actual end user initiating a query.  This allows the
database to distinguish, and trace, end users for applications that connect
using a common database username. It can also be used by `Oracle Virtual
Private Database (VPD)
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-06022729-9210-4895-BF04-6177713C65A7>`__ policies to automatically limit
data access. Oracle Database’s `DBMS_MONITOR
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-951568BF-D798-4456-8478-15FEEBA0C78E>`__ package can take advantage of the
client identifer to enable statistics and tracing at an individual level.

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
be shown in the DBOP_NAME column of the `V$SQL_MONITOR <https://www.oracle.com
/pls/topic/lookup?ctx=dblatest&id=GUID-79E97A84-9C27-4A5E-AC0D-C12CB3E748E6>`__
view:

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

    ODPI [23389068] 2025-06-25 12:07:55.405: ODPI-C 5.5.1
    ODPI [23389068] 2025-06-25 12:07:55.405: debugging messages initialized at level 16
    ODPI [23389068] 2025-06-25 12:08:01.363: SQL select name from jobs

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

Depending on the Oracle Database version in use, the information that is shown
in logs varies.

You can define a prefix value which is added to the beginning of the
``CONNECTION_ID`` value. This prefix aids in identifying the connections from a
specific application.

See `Troubleshooting Oracle Net Services <https://www.oracle.com/pls/topic/
lookup?ctx=dblatest&id=GUID-3F42D057-C9AC-4747-B48B-5A5FF7672E5D>`_ for more
information on connection identifiers.

**Python-oracledb Thin mode**

In python-oracledb Thin mode, you can specify a prefix using the
``connection_id_prefix`` parameter when creating :meth:`standalone connections
<oracledb.connect()>` or :meth:`pooled connections <oracledb.create_pool()>`,
or alternatively set a prefix when calling :meth:`oracledb.ConnectParams()` or
:meth:`oracledb.PoolParams()`. For example:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="localhost/orclpdb",
                                  connection_id_prefix="MYAPP")

If this connection to the database fails, ``MYAPP`` is added as a prefix to the
``CONNECTION_ID`` value shown in the error message, for example::

    DPY-6005: cannot connect to database (CONNECTION_ID=MYAPPm0PfUY6hYSmWPcgrHZCQIQ==).

**Python-oracledb Thick mode**

In python-oracledb Thick mode, you can specify the connection identifier prefix
in the connection string or connect descriptor. For example::

    mydb = (DESCRIPTION =
             (ADDRESS_LIST= (ADDRESS=...) (ADDRESS=...))
             (CONNECT_DATA=
                (SERVICE_NAME=sales.us.example.com)
                (CONNECTION_ID_PREFIX=MYAPP)
             )
           )

.. _tracingbind:

Tracing Bind Values
-------------------

Several methods for tracing bind variable values can be used. When tracing bind
variable values, be careful not to leak information and create a security
problem.

In Oracle Database, the view `V$SQL_BIND_CAPTURE <https://www.oracle.com/
pls/topic/lookup?ctx=dblatest&id=GUID-D353F4BE-5943-4F5B-A99B-BC9505E9579C>`__
can capture bind information. Tracing with Oracle Database’s `DBMS_MONITOR
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-951568BF-D798-4456-8478-15FEEBA0C78E>`__
package may also be useful.

You can additionally :ref:`subclass python-oracledb classes <subclassconn>` and
log any bind values.

OpenTelemetry can also be used, see :ref:`opentelemetry`.

.. _dbviews:

Database Views for Tracing python-oracledb
------------------------------------------

This section shows some of the Oracle Database views useful for tracing and
monitoring python-oracledb. Other views and columns not described here also
contain useful information, such as the :ref:`drcp` views discussed in
:ref:`monitoringdrcp`, and the views discussed in :ref:`endtoendtracing` and
:ref:`tracingbind`.

V$SESSION
+++++++++

The following table shows sample values for some `V$SESSION
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-28E2DC75-E157-4C0A-94AB-117C205789B9>`__ columns. You may see other values
if you have changed the defaults using the :ref:`Defaults object <defaults>`
before connecting, set the equivalent connection or pool creation parameters,
or set the attribute :attr:`Connection.module` as shown in
:ref:`endtoendtracing`.

.. list-table-with-summary:: Sample V$SESSION column values
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 10 15 15
    :name: V$SESSION_COLUMN_VALUES
    :summary: The first column is the name of the column. The second column lists a sample python-oracledb Thick mode value. The third column lists a sample python-oracledb Thin mode value.

    * - Column
      - Sample Thin mode value
      - Sample Thick mode value
    * - MACHINE
      - "myusername-mac"
      - "myusername-mac"
    * - MODULE
      - The value of Python's ``sys.executable``, such as `/Users/myusername/.pyenv/versions/3.13.3/bin/python`
      - Similar to `python@myusername-mac (TNS V1-V3)`
    * - OSUSER
      - "myusername"
      - "myusername"
    * - PROGRAM
      - The value of Python's ``sys.executable``, such as `/Users/myusername/.pyenv/versions/3.13.3/bin/python`
      - Similar to `python@myusername-mac (TNS V1-V3)`
    * - TERMINAL
      - "unknown"
      - Similar to `ttys001`

V$SESSION_CONNECT_INFO
++++++++++++++++++++++

The following table shows sample values for some `V$SESSION_CONNECT_INFO
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-9F0DCAEA-A67E-4183-89E7-B1555DC591CE>`__ columns. You may see other
values if you have changed the defaults using the :ref:`Defaults object
<defaults>` before connecting, set the equivalent connection or pool creation
parameters, or set the ``driver_name`` parameter in
:meth:`oracledb.init_oracle_client()`.

.. list-table-with-summary:: Sample V$SESSION_CONNECT_INFO column values
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 10 15 15
    :name: V$SESSION_CONNECT_INFO
    :summary: The first column is the name of V$SESSION_CONNECT_INFO view's column. The second column lists a sample python-oracledb Thick mode value. The third column list a sample python-oracledb Thin mode value.

    * - Column
      - Sample Thin mode value
      - Sample Thick mode value
    * - CLIENT_DRIVER
      - "python-oracledb thn : 3.2.0"
      - "python-oracledb thk : 3.2.0"
    * - CLIENT_OCI_LIBRARY
      - "Unknown"
      - The Oracle Client or Instant Client type, such as "Full Instant Client"
    * - CLIENT_VERSION
      - "3.2.0.0.0" (the python-oracledb version number with an extra .0.0)
      - The Oracle Client library version number
    * - OSUSER
      - "myusername"
      - "myusername"

.. _opentelemetry:

Using python-oracledb with OpenTelemetry
========================================

The OpenTelemetry observability framework is useful for monitoring applications
and identifying bottlenecks. Python-oracledb conforms to the `Python DB API
specification <https://peps.python.org/pep-0249/>`__ allowing the OpenTelemetry
Database API Instrumentation package `opentelemetry-instrumentation-dbapi
<https://pypi.org/project/opentelemetry-instrumentation-dbapi/>`__ to
automatically instrument your applications.

OpenTelemetry's `backend trace exporters
<https://opentelemetry.io/docs/languages/python/exporters/>`__ can provide
graphic and intuitive representation of OpenTelemetry trace
information. Recording and reporting tools include Zipkin, Jaeger, Grafana, and
Prometheus. These make database query relationships and timings easier to
analyze. Simple tracing can also be directed to the console by making use of
the exporter ``ConsoleSpanExporter`` from the ``opentelemetry-sdk`` package, as
shown in the example below.

For details on using OpenTelemetry in Python, see `Python OpenTelemetry
documentation <https://opentelemetry.io/docs/languages/python/>`_.

Example of Using python-oracledb with OpenTelemetry
---------------------------------------------------

This example shows a python-oracledb application using OpenTelemetry's
``ConsoleSpanExporter`` exporter to display trace information to the console.

**Installing OpenTelemetry Modules**

For this example, install::

    python -m pip install opentelemetry-sdk opentelemetry-api opentelemetry-instrumentation-dbapi

**Sample Application**

This simple application performs two queries in a custom span. It also sets the
service name and system attributes to user-chosen values. It uses the
``capture_parameters`` option to enable bind variable tracing.

.. warning::

   The trace integration setting ``capture_parameters=True`` captures
   :ref:`bind variable values <bind>` and is a security risk.

The sample code is:

.. code-block:: python

    import oracledb

    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    from opentelemetry.sdk.resources import Resource

    user = "hr"
    password = userpwd
    host = "dbhost.example.com"
    service_name = "orclpdb"

    resource = Resource(attributes={
        "service.name": service_name,   # displayed as a resource attribute "service.name"
    })

    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    from opentelemetry.instrumentation.dbapi import trace_integration

    trace_integration(
        oracledb,
        connect_method_name="connect",
        database_system="oracle",  # displayed as attribute "db.system"
        capture_parameters=True,   # displays bind values as attribute "db.statement.parameters"
                                   # SECURITY WARNING: this shows bind variable values
    )

    connection = oracledb.connect(user=user, password=password,
                                  host=host, service_name=service_name)

    with connection.cursor() as cursor:
        tracer = trace.get_tracer("HR-tracer-name")
        with tracer.start_as_current_span("HR-span-1") as span:
            sql = "select city from locations where location_id = :1"
            for r, in cursor.execute(sql, [2200]):
                print(r)
            sql = "select 'Hello World!' from dual"
            for r, in cursor.execute(sql):
                print(r)

**Sample Output**

The sample output will be like::

    Sydney
    Hello World!
    {
        "name": "select",
        "context": {
            "trace_id": "0xb24817cd2ea38ffa523c2ee2778508f7",
            "span_id": "0xacfd82ed60e8976d",
            "trace_state": "[]"
        },
        "kind": "SpanKind.CLIENT",
        "parent_id": "0x19027598c301cfac",
        "start_time": "2025-05-29T08:40:10.194645Z",
        "end_time": "2025-05-29T08:40:10.209815Z",
        "status": {
            "status_code": "UNSET"
        },
        "attributes": {
            "db.system": "oracle",
            "db.name": "",
            "db.statement": "select city from locations where location_id = :1",
            "db.statement.parameters": "[2200]"
        },
        "events": [],
        "links": [],
        "resource": {
            "attributes": {
                "service.name": "orclpdb"
            },
            "schema_url": ""
        }
    }
    {
        "name": "select",
        "context": {
            "trace_id": "0xb24817cd2ea38ffa523c2ee2778508f7",
            "span_id": "0x376dff430f66b14f",
            "trace_state": "[]"
        },
        "kind": "SpanKind.CLIENT",
        "parent_id": "0x19027598c301cfac",
        "start_time": "2025-05-29T08:40:10.210799Z",
        "end_time": "2025-05-29T08:40:10.214694Z",
        "status": {
            "status_code": "UNSET"
        },
        "attributes": {
            "db.system": "oracle",
            "db.name": "",
            "db.statement": "select 'Hello World!' from dual"
        },
        "events": [],
        "links": [],
        "resource": {
            "attributes": {
                "service.name": "orclpdb"
            },
            "schema_url": ""
        }
    }
    {
        "name": "HR-span-1",
        "context": {
            "trace_id": "0xb24817cd2ea38ffa523c2ee2778508f7",
            "span_id": "0x19027598c301cfac",
            "trace_state": "[]"
        },
        "kind": "SpanKind.INTERNAL",
        "parent_id": null,
        "start_time": "2025-05-29T08:40:10.194536Z",
        "end_time": "2025-05-29T08:40:10.214732Z",
        "status": {
            "status_code": "UNSET"
        },
        "attributes": {},
        "events": [],
        "links": [],
        "resource": {
            "attributes": {
                "service.name": "orclpdb"
            },
            "schema_url": ""
        }
    }

The two query results precede OpenTelemetry's tracing. The console tracing then
shows:

- The start and end time of each operation.

- Each "select" trace block's association to the span "HR-span-1" via their
  ``parent_id`` values, which match the span's ``span_id`` value. If you had
  alternatively exported to a recording and tracing system like Zipkin, you
  would be able to conveniently drill down into the spans.

- The bind variable value *2200* in the attribute
  ``db.statement.parameters``. *Warning*: it is a security risk to monitor bind
  variable values this way. Keep the ``capture_parameters`` option set to
  *False* in production applications.

- The system and service name as set in the application.

The Python OpenTelemetry modules allow further customization for tracing. See
their documentation for more information.

OpenTelemetry and extended python-oracledb functionality
--------------------------------------------------------

Python-oracledb calls that are part of the Python DB API standard are
automatically instrumented by ``opentelemetry-instrumentation-dbapi``.  For
python-oracledb's great functionality that extends the standard, you can add
explicit instrumentation. For example, to monitor a call to
:meth:`Connection.fetch_df_all()`, add a tracer like:

.. code-block:: python

    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("myDFQuery"):
        sql = "select city from locations where country_id = :1"
        odf = connection.fetch_df_all(sql, ['UK'])
        print(odf.num_rows())

The new OpenTelemetry span will be like::

    {
        "name": "myDFQuery",
        "context": {
            "trace_id": "0x8512a9fac568c07fc16cd872f68d0346",
            "span_id": "0x03f424111825540f",
            "trace_state": "[]"
        },
        "kind": "SpanKind.INTERNAL",
        "parent_id": null,
        "start_time": "2025-10-06T01:20:34.200129Z",
        "end_time":   "2025-10-06T01:20:39.212618Z",
        "status": {
            "status_code": "UNSET"
        },
        "attributes": {},
        "events": [],
        "links": [],
        "resource": {
            "attributes": {
                "service.name": "orclepdb",
                "db.name": ""
            },
            "schema_url": ""
        }
    }

.. _vsessconinfo:

Finding the python-oracledb Mode
================================

The boolean attributes :attr:`Connection.thin` and :attr:`ConnectionPool.thin`
can be used to find whether python-oracledb is in Thin or Thick mode.

For example, to show the current python-oracledb mode:

.. code-block:: python

    print(connection.thin)

The method :meth:`oracledb.is_thin_mode()` can also be used to find the
mode. Immediately after python-oracledb is imported,
:meth:`oracledb.is_thin_mode()` will return *True* indicating that
python-oracledb defaults to Thin mode.  However if a call to
:meth:`oracledb.init_oracle_client()` is made and it returns successfully, then
:meth:`oracledb.is_thin_mode()` will return *False*, indicating that Thick mode
is enabled.  Once the first standalone connection or connection pool is
created, or a successful call to :meth:`~oracledb.init_oracle_client()` is
made, or :meth:`oracledb.enable_thin_mode()` is called, then python-oracledb’s
mode is fixed and the value returned by :meth:`oracledb.is_thin_mode()` will
never change for the lifetime of the process.

For example:

.. code-block:: python

    print(oracledb.is_thin_mode())
    oracledb.init_oracle_client()
    print(oracledb.is_thin_mode())

If the call to :meth:`~oracledb.init_oracle_client()`, succeeds, the code above
prints::

    True
    False

Mode and version information can also be seen in the Oracle Database data
dictionary table `V$SESSION_CONNECT_INFO
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-9F0DCAEA-A67E-4183-89E7-B1555DC591CE>`__:

.. code-block:: python

    with connection.cursor() as cursor:
        sql = """SELECT UNIQUE client_driver
                 FROM V$SESSION_CONNECT_INFO
                 WHERE sid = SYS_CONTEXT('USERENV', 'SID')"""
        for r, in cursor.execute(sql):
            print(r)

In python-oracledb Thin mode, the output will be like::

    python-oracledb thn : 3.4.0

In python-oracledb Thick mode, the output will be like::

    python-oracledb thk : 3.4.0

Note that you may not see these values if you have set
:attr:`oracledb.defaults.driver_name <defaults.driver_name>` or the
``driver_name`` parameter in :meth:`oracledb.init_oracle_client()`.

The python-oracledb version can also be shown with
:data:`oracledb.__version__`:

.. code-block:: python

    print(oracledb.__version__)

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
