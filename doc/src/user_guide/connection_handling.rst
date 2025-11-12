.. _connhandling:

.. currentmodule:: oracledb

*****************************
Connecting to Oracle Database
*****************************

Connections between python-oracledb and Oracle Database are used for
executing :ref:`SQL <sqlexecution>` and :ref:`PL/SQL <plsqlexecution>`, for
calling :ref:`SODA <sodausermanual>` functions, for receiving database
:ref:`notifications <cqn>` and :ref:`messages <aqusermanual>`, and for
:ref:`starting and stopping <startup>` the database.

This chapter covers python-oracledb's synchronous programming model. For
discussion of asynchronous programming, see :ref:`asyncio`.

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

* **Standalone connections**: :ref:`Standalone connections
  <standaloneconnection>` are useful when the application needs a single
  connection to a database.  Connections are created by calling
  :meth:`oracledb.connect()`. For :ref:`asyncio <asyncio>`, use
  :meth:`oracledb.connect_async()` instead, see :ref:`connasync`.

* **Pooled connections**: :ref:`Connection pooling <connpooling>` is important
  for performance when applications frequently connect and disconnect from the
  database.  Pools support Oracle's :ref:`high availability <highavailability>`
  features and are recommended for applications that must be reliable.  Small
  pools can also be useful for applications that want a few connections
  available for infrequent use.  Pools are created with
  :meth:`oracledb.create_pool()` at application initialization time, and then
  :meth:`ConnectionPool.acquire()` can be called to obtain a connection from a
  pool. For :ref:`asyncio <asyncio>`, use :meth:`oracledb.create_pool_async()`
  and :meth:`AsyncConnectionPool.acquire()` instead, see :ref:`asyncconnpool`.

Many connection behaviors can be controlled by python-oracledb connection
options.  Other settings can be configured in :ref:`optnetfiles` or in
:ref:`optclientfiles`.  These include limiting the amount of time that opening
a connection can take, or enabling :ref:`network encryption <netencrypt>`.

.. _standaloneconnection:

Standalone Connections
======================

Standalone connections are database connections that do not use a
python-oracledb connection pool.  They are useful for simple applications that
use a single connection to a database.  Simple connections are created by
calling :meth:`oracledb.connect()` and passing:

- A database username
- The database password for that user
- A 'data source name' connection string, see :ref:`connstr`

Python-oracledb also supports :ref:`external authentication <extauth>` so
passwords do not need to be in the application. For information on other
authentication methods supported, see :ref:`authenticationmethods`.

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

A single, combined connection string can be passed to ``connect()`` but this
may cause complications if the password contains "@" or "/" characters:

.. code-block:: python

    username="hr"
    userpwd = os.environ.get("PYTHON_PASSWORD")
    host = "localhost"
    port = 1521
    service_name = "orclpdb"

    dsn = f'{username}/{userpwd}@{host}:{port}/{service_name}'
    connection = oracledb.connect(dsn)

If you like to encapsulate values, parameters can be passed using a
:ref:`ConnectParams Object <usingconnparams>`:

.. code-block:: python

    params = oracledb.ConnectParams(host="my_host", port=my_port, service_name="my_service_name")
    conn = oracledb.connect(user="my_user", password="my_password", params=params)

Some values such as the database host name can be specified as ``connect()``
parameters, as part of the ``dsn`` connection string, and in the ``params``
object. A final connection string is internally constructed from any ``dsn``,
individual parameters, and ``params`` object values. The precedence is that
values in a ``dsn`` parameter override values passed as individual parameters,
which themselves override values set in the ``params`` object.

Closing Connections
+++++++++++++++++++

Connections should be released when they are no longer needed. You may prefer
to let connections be automatically cleaned up when references to them go out
of scope. This lets python-oracledb close dependent resources in the correct
order. For example, you can use a Python `context manager
<https://docs.python.org/3/library/stdtypes.html#context-manager-types>`__
``with`` block:

.. code-block:: python

    with oracledb.connect(user="hr", password=userpwd, dsn="myhostname/orclpdb") as connection:
        with connection.cursor() as cursor:
            cursor.execute("insert into SomeTable values (:1)", ("Some string"))
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

If you explicitly close connections you may also need to close other resources
first.

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

    ORA-01017: invalid credential or not authorized; logon denied

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

This error is similar to the ``ORA-12514`` error that you may see when
connecting with python-oracledb Thick mode, or with some other Oracle tools.

The solution is to use a valid service name in the connection string. You can:

- Check and fix any typos in the service name you used

- Check if the hostname and port are correct

- Ask your database administrator (DBA) for the correct values

- Wait a few moments and re-try in case the database is restarting

- Review the connection information in your cloud console or cloud wallet, if
  you are using a cloud database

- Run `lsnrctl status` on the database machine to find the known service names


.. _connstr:

Oracle Net Services Connection Strings
======================================

The data source name parameter ``dsn`` of :meth:`oracledb.connect()`,
:meth:`oracledb.create_pool()`, :meth:`oracledb.connect_async()`, and
:meth:`oracledb.create_pool_async()`, is the Oracle Database Oracle Net
Services Connection String (commonly abbreviated as "connection string") that
identifies which database service to connect to.  The ``dsn`` value can be one
of Oracle Database's naming methods:

* An Oracle :ref:`Easy Connect <easyconnect>` string
* A :ref:`Connect Descriptor <conndescriptor>`
* A :ref:`TNS Alias <netservice>` mapping to a Connect Descriptor stored in a
  :ref:`tnsnames.ora <optnetfiles>` file
* An :ref:`LDAP URL <ldapurl>`
* A :ref:`Configuration Provider URL <configproviderurl>`

Connection strings used for JDBC and Oracle SQL Developer need to be altered to
be usable as the ``dsn`` value, see :ref:`jdbcconnstring`.

For more information about naming methods, see the `Database Net Services
Administrator's Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-E5358DEA-D619-4B7B-A799-3D2F802500F1>`__.

.. note::

    Creating a connection in python-oracledb Thin mode always requires a
    connection string, or the database host name and service name, to be
    specified.  The Thin mode cannot use "bequeath" connections and does not
    reference Oracle environment variables ``ORACLE_SID``, ``TWO_TASK``,
    or ``LOCAL``.

.. _easyconnect:

Easy Connect Syntax for Connection Strings
------------------------------------------

An `Easy Connect <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-59956F00-4996-4943-8D8B-9720DC67AD5D>`__ string is often the simplest
connection string to use in the data source name parameter ``dsn`` of
connection functions such as :meth:`oracledb.connect()`,
:meth:`oracledb.create_pool()`, :meth:`oracledb.connect_async()`, and
:meth:`oracledb.create_pool_async()`.

Using Easy Connect strings means that an external :ref:`tnsnames.ora
<optnetfiles>` configuration file is not needed.

The Easy Connect syntax in python-oracledb is::

    [[protocol:]//]host1{,host12}[:port1]{,host2:port2}{;host1{,host12}[:port1]}[/[service_name][:server][/instance_name]][?parameter_name=value{&parameter_name=value}]

See the `Database Net Services Administrator's Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-8C85D289-6AF3-41BC-848B-BF39D32648BA>`__
and the technical brief `Oracle Database Easy Connect Plus
<https://download.oracle.com/ocomdocs/global/Oracle-Net-Easy
-Connect-Plus.pdf>`__ for more details.

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

The Easy Connect syntax supports Oracle Database service names.  It cannot
be used with the older System Identifiers (SID).

**Oracle Net Settings in Easy Connect Strings**

The Easy Connect syntax allows some `Oracle Network and database
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-8C85D289-6AF3-41BC-848B-BF39D32648BA>`__ configuration options to be
set. This means that a :ref:`sqlnet.ora <optnetfiles>` file is not needed for
common connection scenarios.

For example, to set a connection timeout and keep-alive value:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                 dsn="dbhost.example.com/orclpdb?transport_connect_timeout=10&expire_time=2")


For more information, see :ref:`connectdesckeywords`. Any Easy Connect
parameters that are not known to python-oracledb are ignored and not passed to
the database.

**Python-oracledb Settings in Easy Connect Strings**

Many python-oracledb connection method API arguments can alternatively be
passed as Easy Connect parameters with a "pyo."  prefix.  For example, to set
the statement cache size used by connections:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com/orclpdb?pyo.stmtcachesize=50")

See :ref:`pyoparams` for the usable attributes.

.. _conndescriptor:

Connect Descriptors
-------------------

Connect Descriptors can be embedded directly in python-oracledb applications,
or referenced via a :ref:`TNS Alias <netservice>`.

An example of direct use is:

.. code-block:: python

    dsn = """(DESCRIPTION=
                 (FAILOVER=on)
                 (ADDRESS_LIST=
                   (ADDRESS=(PROTOCOL=tcp)(HOST=sales1-svr)(PORT=1521))
                   (ADDRESS=(PROTOCOL=tcp)(HOST=sales2-svr)(PORT=1521)))
                 (CONNECT_DATA=(SERVICE_NAME=sales.example.com)))"""

    connection = oracledb.connect(user="hr", password=userpwd, dsn=dsn)

The :meth:`oracledb.ConnectParams()` and
:meth:`ConnectParams.get_connect_string()` functions can be used to construct a
connect descriptor from the individual components, see :ref:`usingconnparams`.
For example:

.. code-block:: python

    cp = oracledb.ConnectParams(host="dbhost.example.com", port=1521, service_name="orclpdb")
    dsn = cp.get_connect_string()
    print(dsn)

This prints::

    (DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)(HOST=dbhost.example.com)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=orclpdb)))

Syntax is shown in the `Database Net Services Reference
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-012BCA50-70FC-4951-9473-B6089718FF1C>`__.

Any ``DESCRIPTION``, ``CONNECT_DATA`` and ``SECURITY`` parameters of a full
connect descriptor that are unrecognized by python-oracledb are passed to the
database unchanged.

.. _netservice:

TNS Aliases for Connection Strings
----------------------------------

:ref:`Connect Descriptors <conndescriptor>` are commonly stored in a
:ref:`tnsnames.ora <optnetfiles>` file and associated with a TNS Alias.  This
alias can be used directly for the data source name parameter ``dsn`` of
:meth:`oracledb.connect()`, :meth:`oracledb.create_pool()`,
:meth:`oracledb.connect_async()`, and :meth:`oracledb.create_pool_async()`.
For example, given a file ``/opt/oracle/config/tnsnames.ora`` with the
following contents::

    ORCLPDB =
      (DESCRIPTION =
        (ADDRESS = (PROTOCOL = TCP)(HOST = dbhost.example.com)(PORT = 1521))
        (CONNECT_DATA =
          (SERVER = DEDICATED)
          (SERVICE_NAME = orclpdb)
        )
      )

Then you could connect by passing the TNS Alias "ORCLPDB" (case insensitive) as
the ``dsn`` value:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd, dsn="orclpdb",
                                  config_dir="/opt/oracle/config")

In python-oracledb Thick mode, the configuration directory can also be set
during library initialization:

.. code-block:: python

    oracledb.init_oracle_client(config_dir="/opt/oracle/config")
    connection = oracledb.connect(user="hr", password=userpwd, dsn="orclpdb")

More options for how python-oracledb locates :ref:`tnsnames.ora <optnetfiles>`
files are detailed in :ref:`usingconfigfiles`.

TNS Aliases may also be resolved by :ref:`LDAP <ldapconnections>`.

For more information about Net Service Names, see `Database Net Services
Reference <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-
12C94B15-2CE1-4B98-9D0C-8226A9DDF4CB>`__.

.. _ldapurl:

LDAP URL Connection Strings
---------------------------

The python-oracledb connection string can be an LDAP URL like:

.. code-block:: python

    ldapurl = "ldaps://ldapserver.example.com/cn=orcl,cn=OracleContext,dc=example,dc=com"
    connection = oracledb.connect(user="scott", password=pw, dsn=ldapurl)

This syntax removes the need for external LDAP and ``sqlnet.ora`` configuration
files. See the technical brief `Oracle Client 23ai LDAP URL Syntax
<https://www.oracle.com/a/otn/docs/database/oracle-net-23ai-ldap-url.pdf>`__.

In python-oracledb Thin mode, an additional :ref:`connection protocol hook
function <registerprotocolhook>` is required to handle this connection
protocol, see :ref:`ldapconnections`. A connection protocol hook function is
also required in python-oracledb Thick mode if
:attr:`oracledb.defaults.thick_mode_dsn_passthrough
<Defaults.thick_mode_dsn_passthrough>` is *False*.

To use LDAP URLs in python-oracledb Thick mode applications when
:attr:`oracledb.defaults.thick_mode_dsn_passthrough
<Defaults.thick_mode_dsn_passthrough>` is *True*, the Oracle Client libraries
must be 23.4, or later.


.. _configproviderurl:

Centralized Configuration Provider URL Connection Strings
---------------------------------------------------------

A :ref:`Centralized Configuration Provider <configurationproviders>` URL
connection string allows python-oracledb configuration information to be stored
centrally in OCI Object Storage, in Azure App Configuration, or in a local
file. Given a provider URL, python-oracledb will access the information stored
in the configuration provider and use it to connect to Oracle Database.

The database connect descriptor and any database credentials stored in a
configuration provider will be used by any language driver that accesses the
configuration. Other driver-specific sections can exist. Python-oracledb will
take settings that are in a section with the prefix "pyo", and will ignore
other sections.

For example, to use connection configuration stored in a local file
``/opt/oracle/my-config.json``:

.. code-block:: json

    {
      "connect_descriptor": "localhost/orclpdb",
      "pyo": {
        "min": 5,
        "max": 10,
        "increment": 2
        "stmtcachesize": 4
      }
    }

You could use this to create a connection pool by specifying the ``dsn``
connection string parameter as:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd,
                                dsn="config-file:///opt/oracle/my-config.json")


The pool will be created using the pool settings from the configuration.

The Centralized Configuration Provider URL must begin with
"config-<configuration-provider>://" where the configuration-provider value can
be set to *ociobject*, *azure*, or *file*, depending on the location of your
configuration information.

See :ref:`configurationproviders` for more information, particularly regarding
using python-oracledb Thick mode.

The valid keys for the "pyo" object are shown in :ref:`pyoparams`.

.. _jdbcconnstring:

JDBC and Oracle SQL Developer Connection Strings
------------------------------------------------

The python-oracledb connection string syntax is different from Java JDBC and
the common Oracle SQL Developer syntax.  If these JDBC connection strings
reference a service name like::

    jdbc:oracle:thin:@hostname:port/service_name

For example::

    jdbc:oracle:thin:@dbhost.example.com:1521/orclpdb

then use Oracle's Easy Connect syntax in python-oracledb:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  dsn="dbhost.example.com:1521/orclpdb")

You may need to remove JDBC-specific parameters from the connection string and
use python-oracledb alternatives.

If a JDBC connection string uses an old-style Oracle Database SID "system
identifier", and the database does not have a service name::

    jdbc:oracle:thin:@hostname:port:sid

For example::

    jdbc:oracle:thin:@dbhost.example.com:1521:orcl

then connect by using the ``sid`` parameter:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                                  host="dbhost.example.com", port=1521, sid="orcl")

Alternatively, create a ``tnsnames.ora`` entry (see :ref:`optnetfiles`), for
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

.. _connectdesckeywords:

Oracle Net Connect Descriptor and Easy Connect Keywords
-------------------------------------------------------

Easy Connect syntax is described in :ref:`easyconnect`.

Connect Descriptor keywords are shown in the `Database Net Services Reference
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-7F967CE5-5498-
427C-9390-4A5C6767ADAA>`__.

**Notes on specific keywords**

The ``POOL_CONNECTION_CLASS`` or ``POOL_PURITY`` values will only work when
connected to Oracle Database 21c, or later. Note if ``POOL_PURITY=SELF`` is
used in a connect string, then python-oracledb Thick mode applications will
ignore the action to drop the session when attempting to remove an unusable
connections from a pool in some uncommon error cases. It is recommended to
avoid using ``POOL_PURITY=SELF`` in a connect string with python-oracledb Thick
mode. Instead, code python-oracledb Thick mode applications to explicitly
specify the purity and connection class as attributes.

The ``ENABLE=BROKEN`` connect descriptor option is not supported by
python-oracledb Thin mode. Use ``EXPIRE_TIME`` instead.

If a name is given as a connect string, then python-oracledb will consider it
as a Net Service Name and not as the minimal Easy Connect string of a hostname.
The given connect string will be looked up in a :ref:`tnsnames.ora
<optnetfiles>` file. If supporting a bare name as a hostname is important to
you in python-oracledb, then you can alter the connection string to include a
protocol such as ``tcp://hostname``, or a port number such as
``hostname:1521``.

In python-oracledb Thick mode, when
:attr:`oracledb.defaults.thick_mode_dsn_passthrough
<Defaults.thick_mode_dsn_passthrough>` is *False*, any ``DESCRIPTION``,
``CONNECT_DATA`` and ``SECURITY`` parameters of a full connect descriptor that
are unrecognized by python-oracledb are passed to the database unchanged. Any
Easy Connect parameters that are not known to python-oracledb are discarded and
not passed to the database.

.. _pyoparams:

Python-oracledb Parameters Settable in Easy Connect Strings or Centralized Configuration Providers
--------------------------------------------------------------------------------------------------

Some python-oracledb connection and pool creation parameters can be set in
:ref:`Easy Connect strings <easyconnect>` or via a :ref:`Centralized
Configuration Provider <configurationproviders>`.  This is an alternative to
passing explicit arguments to :meth:`oracledb.connect()`,
:meth:`oracledb.create_pool()`, :meth:`oracledb.connect_async()`, or
:meth:`oracledb.create_pool_async()`. This allows application behavior to be
changed without needing application code to be updated.

The parameters are shown below in :ref:`this table
<params_ez_config_provider>`.  Parameters have a "pyo." prefix or are under a
"pyo" key. Each of these parameters that is defined in an Easy Connect string
or via a Centralized Configuration Provider will take precedence over the value
passed as the equivalent python-oracledb API parameter.

Parameters that apply to :ref:`pool creation <connpooling>` will be ignored if
they are used in the context of :ref:`standalone connections
<standaloneconnection>`.  Parameters with unknown names will be ignored in both
cases.

**Python-oracledb Parameters in Easy Connect Strings**

The Easy Connect parameter names are similar to the python-oracledb method
argument names, but have a "pyo."  prefix. For example:

.. code-block:: python

    cs = "host.example.com:1522/orclpdb?pyo.stmtcachesize=30&pyo.mode=SYSDBA"
    connection = oracledb.connect(user="hr", password=userpwd, dsn=cs)

is the same as:

.. code-block:: python

    cs = "host.example.com:1522/orclpdb"
    connection = oracledb.connect(user="hr", password=userpwd, dsn=cs,
                       stmtcachesize=30, mode=oracledb.AuthMode.SYSDBA)

If a parameter is specified multiple times in an Easy Connect string, then the
last value of that parameter is used. For example, in
"localhost/orclpdb?pyo.sdu=10&pyo.sdu=20" the SDU is set to 20.

Note some Oracle Net parameters can also be prefixed with "pyo.".

Parameters with the prefix "pyo." can only be used in Easy Connect strings and
not in :ref:`Connect Descriptors <conndescriptor>`.

**Python-oracledb Parameters in Configuration Providers**

With the :ref:`File Centralized Configuration Provider <fileconfigprovider>` or
:ref:`OCI Object Storage Centralized Configuration Provider
<ociobjstorageprovider>`, the settable python-oracledb driver attributes should
be in the JSON file under the key "pyo". An example is:

.. code-block:: json

    {
      "connect_descriptor": "localhost/orclpdb",
      "pyo": {
        "min": 5,
        "max": 10,
        "increment": 2
        "stmtcachesize": 4
      }
    }

With :ref:`Azure App Configuration <azureappstorageprovider>`, values are set
using a key such as "<prefix>/pyo/<key name>". This is similar to how `Oracle
Call Interface <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=LNOCI>`__ settings use the key "<prefix>/oci/<key name>" as shown in
`Oracle Net Service Administrator’s Guide <https://www.oracle.com/pls/topic
/lookup?ctx=dblatest&id=GUID-97E22A68-6FE3-4FE9-98A9-90E5BF83E9EC>`__.

.. _params_ez_config_provider:

**Parameter Names**

When used in Easy Connect Strings, the parameter names should be prefixed with
"pyo.".  When used in a Centralized Configuration Provider, the parameter
names are used to form the key names under a parent "pyo" key or with a "pyo/"
prefix. The names are case insensitive.

.. list-table-with-summary:: Python-oracledb parameters usable in Easy Connect Strings or Centralized Configuration Providers
    :header-rows: 1
    :class: wy-table-responsive
    :align: center
    :name:  _params_ez_config_provider_table
    :summary: The first column displays the base parameter name. The second column displays the type of the parameter. The third column displays the equivalent API parameter name. The fourth column contains notes.

    * - Base Parameter Name
      - Type/Value
      - Equivalent python-oracledb Connection Parameter Name
      - Notes
    * - ``CCLASS``
      - String
      - ``cclass``
      - No relevant notes
    * - ``CONNECTION_ID_PREFIX``
      - String
      - ``connection_id_prefix``
      - No relevant notes
    * - ``DISABLE_OOB``
      - String representing a boolean. Values may be one of *on* or *off*, *true* or *false*, *yes* or *no* (case insensitive).
      - ``disable_oob``
      - No relevant notes
    * - ``DRIVER_NAME``
      - String
      - ``driver_name``
      - No relevant notes
    * - ``EDITION``
      - String
      - ``edition``
      - No relevant notes
    * - ``EVENTS``
      - String representing a boolean. Values may be one of *on* or *off*, *true* or *false*, *yes* or *no* (case insensitive).
      - ``events``
      - No relevant notes
    * - ``EXPIRE_TIME``
      - Integer
      - ``expire_time``
      - No relevant notes
    * - ``EXTERNALAUTH``
      - String representing a boolean. Values may be one of *on* or *off*, *true* or *false*, *yes* or *no* (case insensitive).
      - ``externalauth``
      - No relevant notes
    * - ``EXTRA_AUTH_PARAMS``
      - A dictionary containing the configuration parameters necessary for Oracle Database authentication using :ref:`OCI <cloudnativeauthoci>` or :ref:`Azure <cloudnativeauthoauth>` cloud native authentication plugins.
      - ``extra_auth_params``
      - For use by Centralized Configuration Providers only
    * - ``GETMODE``
      - String, values may be one of *FORCEGET*, *NOWAIT*, *WAIT*, or *TIMEDWAIT* mapping to :ref:`connpoolmodes`.
      - ``getmode``
      - Pool creation only
    * - ``HOMOGENEOUS``
      - String representing a boolean. Values may be one of *on* or *off*, *true* or *false*, *yes* or *no* (case insensitive).
      - ``homogeneous``
      - Pool creation only
    * - ``HTTPS_PROXY``
      - String
      - ``https_proxy``
      - No relevant notes
    * - ``HTTPS_PROXY_PORT``
      - Integer
      - ``https_proxy_port``
      - No relevant notes
    * - ``INCREMENT``
      - Integer
      - ``increment``
      - Pool creation only
    * - ``MACHINE``
      - String
      - ``machine``
      - No relevant notes
    * - ``MAX``
      - Integer
      - ``max``
      - Pool creation only
    * - ``MAX_LIFETIME_SESSION``
      - Integer
      - ``max_lifetime_session``
      - Pool creation only
    * - ``MAX_SESSIONS_PER_SHARD``
      - Integer
      - ``max_sessions_per_shard``
      - Pool creation only
    * - ``MIN``
      - Integer
      - ``min``
      - Pool creation only
    * - ``MODE``
      - String, values may be one of *DEFAULT*, *PRELIM*, *SYSASM*, *SYSBKP*, *SYSDBA*, *SYSDGD*, *SYSKMT*, *SYSOPER*, or *SYSRAC* mapping to :ref:`connection-authorization-modes`.
      - ``mode``
      - No relevant notes
    * - ``OSUSER``
      - String
      - ``osuser``
      - No relevant notes
    * - ``PING_INTERVAL``
      - Integer
      - ``ping_interval``
      - Pool creation only
    * - ``PING_TIMEOUT``
      - Integer
      - ``ping_timeout``
      - Pool creation only
    * - ``POOL_BOUNDARY``
      - String
      - ``pool_boundary``
      - No relevant notes
    * - ``PROGRAM``
      - String
      - ``program``
      - No relevant notes
    * - ``PURITY``
      - String, values may be one of *DEFAULT*, *NEW*, or *SELF* mapping to :ref:`drcppurityconsts`.
      - ``purity``
      - No relevant notes
    * - ``RETRY_COUNT``
      - Integer
      - ``retry_count``
      - No relevant notes
    * - ``RETRY_DELAY``
      - Integer
      - ``retry_delay``
      - No relevant notes
    * - ``SDU``
      - Integer
      - ``sdu``
      - No relevant notes
    * - ``SODA_METADATA_CACHE``
      - String representing a boolean. Values may be one of *on* or *off*, *true* or *false*, *yes* or *no* (case insensitive).
      - ``soda_metadata_cache``
      - Pool creation only
    * - ``SSL_SERVER_CERT_DN``
      - String
      - ``ssl_server_cert_dn``
      - No relevant notes
    * - ``SSL_SERVER_DN_MATCH``
      - String representing a boolean. Values may be one of *on* or *off*, *true* or *false*, *yes* or *no* (case insensitive).
      - ``ssl_server_dn_match``
      - No relevant notes
    * - ``STMTCACHESIZE``
      - Integer
      - ``stmtcachesize``
      - No relevant notes
    * - ``TCP_CONNECT_TIMEOUT``
      - Integer
      - ``tcp_connect_timeout``
      - No relevant notes
    * - ``TERMINAL``
      - String
      - ``terminal``
      - No relevant notes
    * - ``TIMEOUT``
      - Integer
      - ``timeout``
      - Pool creation only
    * - ``USE_TCP_FAST_OPEN``
      - String representing a boolean. Values may be one of *on* or *off*, *true* or *false*, *yes* or *no* (case insensitive).
      - ``use_tcp_fast_open``
      - No relevant notes
    * - ``USE_SNI``
      - String representing a boolean. Values may be one of *on* or *off*, *true* or *false*, *yes* or *no* (case insensitive).
      - ``use_sni``
      - No relevant notes
    * - ``WAIT_TIMEOUT``
      - Integer
      - ``wait_timeout``
      - Pool creation only
    * - ``WALLET_LOCATION``
      - String
      - ``wallet_location``
      - Not recommended for use in Configuration Providers because the path name may not be valid on any particular application host.

.. _authentication:

Authenticating to Oracle Database
=================================

When connecting to Oracle Database, authentication plays a key role in
establishing an authorized connection. Python-oracledb supports various Oracle
Database authentication methods which are listed below:

- :ref:`dbauthentication`
- :ref:`proxyauth`
- :ref:`extauth`
- :ref:`tokenauth`
- :ref:`instanceprincipalauth`

The Oracle Client libraries used by python-oracledb Thick mode may support
additional authentication methods that are configured independently of the
driver.

.. _configurationproviders:

Centralized Configuration Providers
===================================

`Centralized Configuration Providers <https://www.oracle.com/pls/topic/lookup?
ctx=dblatest&id=GUID-E5D6E5D9-654C-4A11-90F8-2A79C58ABD38>`__ allow the storage
and management of database connection credentials and application configuration
information in a central location. Providers allow you to separately store
configuration information from the code of your application. The values that
can be stored includes the database connection string, database credentials, a
cache time, and python-oracledb specific attributes such as connection pool
settings. Python-oracledb can use the centrally stored information to connect
to Oracle Database with :meth:`oracledb.connect()`,
:meth:`oracledb.create_pool()`, :meth:`oracledb.connect_async()`, and
:meth:`oracledb.create_pool_async()`.

The following configuration providers are supported by python-oracledb:

- :ref:`File Centralized Configuration Provider <fileconfigprovider>`
- :ref:`Oracle Cloud Infrastructure (OCI) Object Storage Centralized
  Configuration Provider <ociobjstorageprovider>`
- :ref:`Microsoft Azure App Centralized Configuration Provider
  <azureappstorageprovider>`

To use :ref:`Centralized Configuration Provider <configurationproviders>`
functionality in python-oracledb Thick mode, you should set
:attr:`oracledb.defaults.thick_mode_dsn_passthrough
<Defaults.thick_mode_dsn_passthrough>` to *False*. Alternatively use
:meth:`ConnectParams.parse_connect_string()`, see :ref:`usingconnparams`.

Note: In Thick mode, when :attr:`oracledb.defaults.thick_mode_dsn_passthrough
<Defaults.thick_mode_dsn_passthrough>` is *True*, it is the Oracle Client
libraries that access the configuration provider when python-oracledb
connection or pool creation methods are invoked. Any python-oracledb parameter
section will be ignored. Any Oracle Client Interface parameter section should
be *removed* from the configuration because its values may be different to
those that python-oracledb assumes, and will cause undefined behavior.

**Precedence of Attributes**

Defining attributes in multiple places is not recommended. However, if
you have defined the values of ``user`` and ``password`` in both the
application and the configuration provider, then the values defined in the
application will have the higher precedence. If the ``externalauth`` parameter
is set to *True*, then the ``user`` and ``password`` values specified in the
configuration provider are ignored.

If other python-oracledb connection attributes have been defined in both the
application and the configuration provider, then the values defined in the
configuration provider will have higher precedence.

If you are using Thick mode, and have defined python-oracledb attributes in an
``oraaccess.xml`` file (see :ref:`optclientfiles`), the configuration provider,
and the application, then the values defined in the configuration provider will
have the higher precedence followed by the ``oraaccess.xml`` file settings, and
then application settings.

.. _fileconfigprovider:

Using a File Centralized Configuration Provider
-----------------------------------------------

The File Centralized Configuration Provider enables the storage and management
of Oracle Database connection information using local files.

To use a File Centralized Configuration Provider, you must:

1. Store the connection information in a JSON file on your local file system.

2. Set the path to the file in the ``dsn`` parameter of connection and pool
   creation methods.

**File Centralized Configuration Provider JSON File Syntax**

The configuration file must contain at least a ``connect_descriptor`` key to
specify the database connection string. Optionally, you can store the database
user name, password, a cache time, and :ref:`python-oracledb settings
<pyoparams>`. The keys that can be stored in the file are:

.. list-table-with-summary:: JSON keys for the File Configuration Provider
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 15 25 15
    :name: _file_configuration_provider
    :summary: The first column displays the name of the key. The second column displays its description. The third column displays whether the key is required or optional.

    * - Key
      - Description
      - Required or Optional
    * - ``user``
      - The database user name.
      - Optional
    * - ``password``
      - The password of the database user as a dictionary containing the key "type" and password type-specific keys.

        .. warning::

            Storing passwords in the configuration file should only ever be used in development or test environments.

      - Optional
    * - ``connect_descriptor``
      - The database :ref:`connection string <connstr>`.
      - Required
    * - ``config_time_to_live``
      - The number of seconds the configuration is cached for. Defaults to 86,400 seconds (24 hours).
      - Optional
    * - ``config_time_to_live_grace_period``
      - The number of seconds an expired configuration can still be used if a new configuration cannot be obtained. Defaults to 1,800 seconds (30 minutes).
      - Optional
    * - ``pyo``
      - See :ref:`pyoparams`.
      - Optional

See the `Oracle Net Service Administrator’s Guide <https://www.oracle.com/pls/
topic/lookup?ctx=dblatest&id=GUID-B43EA22D-5593-40B3-87FC-C70D6DAF780E>`__ for
more information on the generic provider sub-objects usable in JSON files.

Multiple configurations can be defined by specifying the above keys under
user-chosen, top-level keys, see the example further below.

**File Centralized Configuration Provider DSN Syntax**

To use a file provider, specify the ``dsn`` parameter of
:meth:`oracledb.connect()`, :meth:`oracledb.create_pool()`,
:meth:`oracledb.connect_async()`, or :meth:`oracledb.create_pool_async()` using
the following format::

    config-file://<file-path-and-name>[?key=<key_name>]

The elements of the ``dsn`` parameter are detailed in the table below.

.. list-table-with-summary:: Connection String Parameters for File Configuration Provider
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 20 60
    :name: _connection_string_for_file_configuration_provider
    :summary: The first column displays the name of the connection string parameter. The second column displays the description of the connection string parameter.

    * - Parameter
      - Description
    * - ``config-file``
      - Indicates that the centralized configuration provider is a file in your
        local system.
    * - <file-name>
      - The file path and name of the JSON file that contains the configuration
        information. For relative paths, python-oracledb will use the
        connection or pool creation ``config_dir`` parameter, or
        :attr:`oracledb.defaults.config_dir <Defaults.config_dir>` value, to
        create an absolute path.
    * - ``key``
      - The connection key name used to identify a specific configuration. If
        this parameter is specified, the file is assumed to contain multiple
        configurations that are indexed by the key value. If not specified, the
        file is assumed to contain a single configuration. See the example
        further below.

**File Configuration Provider Examples**

An example of File Configuration Provider file syntax is::

    {
        "user": "scott",
        "password": {
            "type": "base64",
            "value": "dGlnZXI="
        },
        "connect_descriptor": "dbhost.example.com:1522/orclpdb",
        "pyo": {
            "stmtcachesize": 30,
            "min": 2,
            "max": 10
        }
    }

This encodes the password as base64.  See :ref:`ociobjstorageprovider` for
other password examples. Plaintext passwords are not supported.

Note that python-oracledb caches configurations by default, see
:ref:`conncaching`.

If you have this configuration file in ``/opt/oracle/my-config1.json``, you
could use it like:

.. code-block:: python

    connection = oracledb.connect(dsn="config-file:///opt/oracle/my-config1.json")

Multiple configurations can be defined by specifying user-chosen top-level
keys::

    {
        "production": {
            "connect_descriptor": "localhost/orclpdb"
        },
        "testing": {
            "connect_descriptor": "localhost/orclpdb",
            "user": "scott",
            "password": {
                "type": "base64",
                "value": "dGlnZXI="
            }
        }
    }

If you have this configuration file in ``/opt/oracle/my-config2.json``, you
could use it like:

.. code-block:: python

    connection = oracledb.connect(user="hr", password=userpwd,
                 dsn="config-file:///opt/oracle/my-config2.json?key=production")


.. _ociobjstorageprovider:

Using an OCI Object Storage Centralized Configuration Provider
--------------------------------------------------------------

The Oracle Cloud Infrastructure (OCI) `Object Storage configuration provider
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-B43EA22D-5593-
40B3-87FC-C70D6DAF780E>`__ enables the storage and management of Oracle
Database connection information as JSON in `OCI Object Storage <https://docs.
oracle.com/en-us/iaas/Content/Object/Concepts/objectstorageoverview.htm>`__.

To use an OCI Object Storage Centralized Configuration Provider, you must:

1. Upload a JSON file that contains the connection information into an OCI
   Object Storage Bucket. See `Uploading an Object Storage Object to a Bucket
   <https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/managingobjects_
   topic-To_upload_objects_to_a_bucket.htm>`__ and the `Oracle Net Service
   Administrator’s Guide <https://www.oracle.com/pls/topic/lookup?ctx=
   dblatest&id=GUID-B43EA22D-5593-40B3-87FC-C70D6DAF780E>`__ for the steps.
   See :ref:`OCI Object Storage Centralized Configuration Provider Parameters
   <ociconfigparams>` for the configuration information that can be added.

2. Install the Python `OCI <https://pypi.org/project/oci/>`__ module, see
   :ref:`ociccpmodules`.

3. Import the :ref:`oracledb.plugins.oci_config_provider <configociplugin>`
   plugin in your application.

4. :ref:`Use an OCI Object Storage connection string URL <connstringoci>`
   in the ``dsn`` parameter of connection and pool creation methods.

.. _ociconfigparams:

**OCI Object Storage Centralized Configuration Provider JSON File Syntax**

The stored JSON configuration file must contain a ``connect_descriptor`` key.
Optionally, you can specify the database user name, password, a cache time, and
python-oracledb attributes. The database password can also be stored securely
using `OCI Vault <https://docs.oracle.com/en-us/iaas/Content/
KeyManagement/Tasks/managingsecrets.htm>`__ or `Azure Key Vault
<https://learn.microsoft.com/en-us /azure/key-vault/general/overview>`__. The
keys that can be in the JSON file are listed below.

.. list-table-with-summary:: JSON Keys for OCI Object Storage Configuration Provider
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 15 25 15
    :name: _oci_object_storage_sub-objects
    :summary: The first column displays the name of the key. The second column displays the description of the key. The third column displays whether the key is required or optional.

    * - Key
      - Description
      - Required or Optional
    * - ``user``
      - The database user name.
      - Optional
    * - ``password``
      - The password of the database user as a dictionary containing the key "type" and password type-specific keys.
      - Optional
    * - ``connect_descriptor``
      - The database :ref:`connection string <connstr>`.
      - Required
    * - ``config_time_to_live``
      - The number of seconds the configuration is cached for. Defaults to 86,400 seconds (24 hours).
      - Optional
    * - ``config_time_to_live_grace_period``
      - The number of seconds an expired configuration can still be used if a new configuration cannot be obtained. Defaults to 1,800 seconds (30 minutes).
      - Optional
    * - ``pyo``
      - See :ref:`pyoparams`.
      - Optional

.. _connstringoci:

**OCI Object Storage Centralized Configuration Provider DSN Syntax**

The ``dsn`` parameter for :meth:`oracledb.connect()`,
:meth:`oracledb.create_pool()`, :meth:`oracledb.connect_async()`, or
:meth:`oracledb.create_pool_async()` calls should use a connection string URL
in the format::

    config-ociobject:<objectstorage-name>/n/{namespaceName}/b/{bucketName}/o/
    <objectName>[/c/<networkServiceName>][?<option1>=<value1>&<option2>=<value2>...]

The elements of the connection string are detailed in the table below.

.. list-table-with-summary:: Connection String Parameters for OCI Object Storage
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 15 25 15
    :name: _connection_string_for_oci_object_storage
    :summary: The first row displays the name of the connection string parameter. The second row displays the description of the connection string parameter. The third row displays whether the connection string parameter is required or optional.

    * - Parameter
      - Description
      - Required or Optional
    * - ``config-ociobject``
      - Indicates that the configuration provider is OCI Object Storage.
      - Required
    * - <objectstorage-name>
      - The URL of OCI Object Storage endpoint.
      - Required
    * - <namespaceName>
      - The OCI Object Storage namespace where the JSON file is stored.
      - Required
    * - <bucketName>
      - The OCI Object Storage bucket name where the JSON file is stored.
      - Required
    * - <objectName>
      - The JSON file name.
      - Required
    * - <networkServiceName>
      - The network service name or alias if the JSON file contains one or more network service names.
      - Optional
    * - <option>=<value>
      - The authentication method and its corresponding parameters to access the OCI Object Storage configuration provider. You can specify one of the following authentication methods: API Key-based authentication, Instance Principal Authentication, and Resource Principal Authentication. See :ref:`ociobjectstorageauthmethods` for more information.
      - Optional

**OCI Object Storage Centralized Configuration Provider Examples**

An example of OCI Object Centralized Storage Configuration Provider JSON file
syntax is::

    {
        "user": "scott",
        "password": {
            "type": "ocivault",
            "value": "oci.vaultsecret.my-secret-id"
            "authentication": {
                "method": "OCI_INSTANCE_PRINCIPAL"
            }
        },
        "connect_descriptor": "dbhost.example.com:1522/orclpdb",
        "pyo": {
            "stmtcachesize": 30,
            "min": 2,
            "max": 10
        }
    }

Passwords can optionally be stored using the Azure Key Vault. To do this,
you must import the :ref:`oracledb.plugins.azure_config_provider
<configazureplugin>` python-oracledb plugin in your application and you must
define the Azure Key Vault credentials in the ``password`` key. In this, the
``azure_client_id`` and ``azure_tenant_id`` must be specified. Also, either
``azure_client_secret`` or ``azure_client_certificate_path`` should be
specified. For example::

    "password": {
        "type": "azurevault",
        "value": "<Azure Key Vault URI>",
        "authentication": {
            "azure_tenant_id": "<tenant_id>",
            "azure_client_id": "<client_id>",
            "azure_client_secret": "<secret value>"
        }
    }

Or::

    "password": {
        "type": "azurevault",
        "value": "<Azure Key Vault URI>",
        "authentication": {
            "azure_tenant_id": "<tenant_id>",
            "azure_client_id": "<client_id>",
            "azure_client_certificate_path": "<azure_client_certificate_path>"
        }
    }

Note that python-oracledb caches configurations by default, see
:ref:`conncaching`.

An example of a connection string for the OCI Object Centralized Storage
configuration provider is:

.. code-block:: python

    configociurl = "config-ociobject://abc.oraclecloud.com/n/abcnamespace/b/abcbucket/o/abcobject?authentication=oci_default&oci_tenancy=abc123&oci_user=ociuser1&oci_fingerprint=ab:14:ba:13&oci_key_file=ociabc/ocikeyabc.pem"

To create a :ref:`standalone connection <standaloneconnection>` you could use
this like:

.. code-block:: python

    import oracledb.plugins.oci_config_provider

    configociurl = "config-ociobject://abc.oraclecloud.com/n/abcnamespace/b/abcbucket/o/abcobject?authentication=oci_default&oci_tenancy=abc123&oci_user=ociuser1&oci_fingerprint=ab:14:ba:13&oci_key_file=ociabc/ocikeyabc.pem"

    connection = oracledb.connect(dsn=configociurl)

The configuration can also be used to create a :ref:`connection pool
<connpooling>`, for example:

.. code-block:: python

    pool = oracledb.create_pool(dsn=configociurl)

.. _azureappstorageprovider:

Using an Azure App Centralized Configuration Provider
-----------------------------------------------------

`Azure App Configuration <https://learn.microsoft.com/en-us/azure/azure-app-
configuration/overview>`__ is a cloud-based service provided by Microsoft
Azure. It can be used for storage and management of Oracle Database connection
information as key-value pairs.

To use python-oracledb with Azure App Configuration, you must:

1. Save your configuration information in your Azure App Configuration
   Provider. See :ref:`Azure App Centralized Configuration Provider Parameters
   <azureconfigparams>`.

2. Install the Azure App modules, see :ref:`azureccpmodules`.

3. Import the :ref:`oracledb.plugins.azure_config_provider <configazureplugin>`
   plugin in your application.

4. :ref:`Use an Azure App Configuration connection string URL
   <connstringazure>` in the ``dsn`` parameter of connection and pool creation
   methods.

.. _azureconfigparams:

**Azure App Centralized Configuration Provider Parameters**

Key-value pairs for stored connection information can be added using the
Configuration explorer page of your Azure App Configuration. See `Create a
key-value in Azure App Configuration <https://learn.microsoft.com/
en-us/azure/azure-app-configuration/quickstart-azure-app-configuration-create?
tabs=azure-portal#create-a-key-value>`__ for more information.  Alternatively,
they can be set by making `REST <https://learn.microsoft.com/en-us/python
/api/azure-appconfiguration/azure.appconfiguration.azureappconfigurationclient
?view=azure-python#azure-appconfiguration-azureappconfigurationclient-add-
configuration-setting>`__ calls.  Also see the `Oracle Net Service
Administrator’s Guide <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id
=GUID-FCCF1C8D-E4E9-4061-BEE5-5F21654BAC18>`__.

You can organize the key-value pairs under a prefix based on your
application's needs. For example, if you have two applications, Sales and
Human Resources, then you can store the relevant configuration information
under the prefix *sales* and the prefix *hr*.

The key-value pairs must contain the key ``connect_descriptor`` which specifies
the database connection string. This can be set using a prefix as
"<prefix>/connect_descriptor", for example, *sales/connect_descriptor*.

You can additionally store the database user name using a key such as
"<prefix>/user", and store the password using "<prefix>/password". For example,
*sales/user* and *sales/password*. The database password can also be stored
securely using `Azure Key Vault <https://learn.microsoft.com/en-us
/azure/key-vault/general/overview>`__.  A cache time can optionally be stored
using "<prefix>/config_time_to_live". For example, *sales/60000*. See
:ref:`conncaching`.

Optional python-oracledb settings can be set using a key such as
"<prefix>/pyo/<key name>", for example *sales/pyo/min*. This is similar to how
`Oracle Call Interface <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=LNOCI>`__ settings use keys like "<prefix>/oci/<key name>" as shown in
`Oracle Net Service Administrator’s Guide <https://www.oracle.com/pls/topic/
lookup?ctx=dblatest&id=GUID-97E22A68-6FE3-4FE9-98A9-90E5BF83E9EC>`__.

The keys that can be added in Azure App Configuration are listed below:

.. list-table-with-summary:: Keys for Azure App Configuration
    :header-rows: 1
    :class: wy-table-responsive
    :widths: 15 25 15
    :name: _azure_app_configuration_keys
    :summary: The first column displays the name of the key. The second column displays the description of the key. The third column displays whether the key is required or optional.

    * - Key
      - Description
      - Required or Optional
    * - ``user``
      - The database user name.
      - Optional
    * - ``password``
      - The password of the database user as a dictionary containing the key "type" and password type-specific keys. If using Azure Key Vault, this can be the URI to the vault containing the secret key, specified using the key "uri"
      - Optional
    * - ``connect_descriptor``
      - The database :ref:`connection string <connstr>`.
      - Required
    * - ``config_time_to_live``
      - The number of seconds the configuration is cached for. Defaults to 86,400 seconds (24 hours).
      - Optional
    * - ``config_time_to_live_grace_period``
      - The number of seconds an expired configuration can still be used if a new configuration cannot be obtained. Defaults to 1,800 seconds (30 minutes).
      - Optional
    * - ``pyo``
      - See :ref:`pyoparams`.
      - Optional

.. _connstringazure:

**Azure App Centralized Configuration Provider DSN Syntax**

You must define a connection string URL in a specific format in the ``dsn``
parameter of :meth:`oracledb.connect()`, :meth:`oracledb.create_pool()`,
:meth:`oracledb.connect_async()`, or :meth:`oracledb.create_pool_async()` to
access the information stored in Azure App Configuration. The syntax is::

    config-azure://<appconfigname>[?key=<prefix>&label=<value>&<option1>=<value1>&<option2>=<value2>...]

The elements of the connection string are detailed in the table below.

.. list-table-with-summary:: Connection String Parameters for Azure App Centralized Configuration Provider
    :header-rows: 1
    :class: wy-table-responsive
    :align: center
    :widths: 15 25 15
    :name: _connection_string_for_azure_app
    :summary: The first row displays the name of the connection string parameter. The second row displays the description of the connection string parameter. The third row displays whether the connection string parameter is required or optional.

    * - Parameter
      - Description
      - Required or Optional
    * - config-azure
      - Indicates that the configuration provider is Azure App Configuration.
      - Required
    * - <appconfigname>
      - The URL of the Azure App Configuration endpoint. The suffix ".azconfig.io" in the name is optional.
      - Required
    * - key=<prefix>
      - A key prefix to identify the connection. You can organize configuration information under a prefix as per application requirements.
      - Required
    * - label=<value>
      - The Azure App Configuration label name.
      - Optional
    * - <option>=<value>
      - The authentication method and its corresponding parameters to access the Azure App Configuration provider. You can specify one of the following authentication methods: Default Azure Credential, Service Principal with Client Secret, Service Principal with Client Certificate, and Managed Identity. See :ref:`azureappauthmethods` for more information on these authentication methods and their corresponding parameters.
      - Optional

**Azure App Centralized Configuration Examples**

.. _azureappconfigexample:

The following table shows sample configuration information defined using the
Configuration explorer page of your Azure App Configuration provider. The
example uses the prefix ``test/``.

.. list-table-with-summary::
    :header-rows: 1
    :class: wy-table-responsive
    :align: center
    :widths: 30 70
    :name: _azure_app_configuration_keys_and_values
    :summary: The first row displays the name of the key defined in Azure App Configuration. The second row displays the value of the key defined in Azure App Configuration.

    * - Sample Azure App Configuration Key
      - Sample Value
    * - test/connect_descriptor
      - ``dbhost.example.com:1522/orclpdb``
    * - test/user
      - ``scott``
    * - test/password
      - ``{"uri":"https://mykeyvault.vault.azure.net/secrets/passwordsales"}``
    * - test/pyo/max
      - ``20``

Note that python-oracledb caches configurations by default, see
:ref:`conncaching`.

An example of a connection string for the Azure App Configuration provider is:

.. code-block:: python

    configazureurl = "config-azure://aznetnamingappconfig.azconfig.io/?key=test/&azure_client_id=123-456&azure_client_secret=MYSECRET&azure_tenant_id=789-123"

.. _useazureconfigprovider:

An example using a :ref:`standalone connection <standaloneconnection>` is:

.. code-block:: python

    import oracledb.plugins.azure_config_provider

    configazureurl = "config-azure://aznetnamingappconfig.azconfig.io/?key=test/&azure_client_id=123-456&azure_client_secret=MYSECRET&azure_tenant_id=789-123"

    oracledb.connect(dsn=configazureurl)

The configuration can also be used to create a :ref:`connection pool
<connpooling>`, for example:

.. code-block:: python

    oracledb.create_pool(dsn=configazureurl)

.. _conncaching:

Caching Configuration Information
---------------------------------

Python-oracledb caches configurations obtained from Centralized Configuration
Providers to reduce access overheads.

You can use the ``config_time_to_live`` configuration key to specify the number
of seconds that python-oracledb should keep the information cached. The default
time is 86,400 seconds (24 hours).

When ``config_time_to_live`` is reached, the configuration is considered to be
"softly expired" and subsequent python-oracledb connections will attempt to
obtain the configuration again from the configuration provider. If it cannot be
retrieved, python-oracledb will continue to use the previous configuration for
up to ``config_time_to_live_grace_period`` seconds which defaults to 1,800
seconds (30 minutes). After this grace period the cached configuration fully
expires. Future connection attempts will try to retrieve the configuration from
the provider but will fail if the new configuration cannot be obtained.

An example of changing the cache time to 12 hours with an additional grace time
of 10 minutes for the File or OCI Object Storage Centralized Configuration
Providers is::

    {
        "connect_descriptor": "dbhost.example.com:1522/orclpdb",
        "config_time_to_live": 43200,
        "config_time_to_live_grace_period": 600,
        "pyo": {
            "stmtcachesize": 30,
            "min": 2,
            "max": 10
        }
    }

.. _usingconnparams:

Using the ConnectParams Builder Class
======================================

The :ref:`ConnectParams class <connparam>` allows you to define connection
parameters in a single place.  The :func:`oracledb.ConnectParams()` function
returns a :ref:`ConnectParams <connparam>` object.  The object can be passed to
:func:`oracledb.connect()` or :meth:`oracledb.connect_async()`. For example:

.. code-block:: python

    cp = oracledb.ConnectParams(user="hr", password=userpwd,
                                host="dbhost", port=1521, service_name="orclpdb")
    connection = oracledb.connect(params=cp)

For connection pools, see :ref:`usingpoolparams`.

The use of the ConnectParams class is optional because you can pass the same
parameters directly to :func:`~oracledb.connect()`.  For example, the code
above is equivalent to:

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

Some values such as the database host name can be specified as ``connect()``
parameters, as part of the ``dsn`` connection string, and in the ``params``
object. A final connection string is internally constructed from any ``dsn``,
individual parameters, and ``params`` object values. The precedence is that
values in a ``dsn`` parameter override values passed as individual parameters,
which themselves override values set in the ``params`` object.

To parse a connection string and store its components as attributes of a
ConnectParams instance, use :meth:`ConnectParams.parse_connect_string()`. For
example:

.. code-block:: python

    dsn = "host.example.com:1522/orclpdb?transport_connect_timeout=15&pyo.stmtcachesize=30"
    cp = oracledb.ConnectParams()
    cp.parse_connect_string(dsn)

    connection = oracledb.connect(user="hr", password=userpwd, params=cp)

Most parameter values of :func:`oracledb.ConnectParams()` are gettable as
attributes. For example, to get the stored host name:

.. code-block:: python

    print(cp.host)

Attributes such as the password are not gettable.

You can set individual default attributes using :meth:`ConnectParams.set()`:

.. code-block:: python

    cp = oracledb.ConnectParams(host="localhost", port=1521, service_name="orclpdb")

    # set a new port
    cp.set(port=1522)

    # change both the port and service name
    cp.set(port=1523, service_name="orclpdb")

Note :meth:`ConnectParams.set()` has no effect after
:meth:`ConnectParams.parse_connect_string()` has been called.

The method :meth:`ConnectParams.parse_dsn_with_credentials()` can be used to
extract the username, password, and connection string from a DSN:

.. code-block:: python

    cp = oracledb.ConnectParams()
    (un,pw,cs) = cp.parse_dsn_with_credentials("scott/tiger@localhost/orclpdb")

    print(un)   # scott
    print(pw)   # tiger
    print(cs)   # localhost/orclpdb

Any component not found in the DSN is returned as *None*.

The method :meth:`ConnectParams.get_network_service_names()` can be used to get
a list of the network service names that are defined in the :ref:`tnsnames.ora
<optnetfiles>` file. The directory that contains file can be specified in the
:attr:`~ConnectParams.config_dir` attribute.

.. code-block:: python

    cp = oracledb.ConnectParams(host="my_host", port=my_port, dsn="orclpdb",
                                config_dir="/opt/oracle/config")
    cp.get_network_service_names()

If :meth:`ConnectParams.get_network_service_names()` is called but a
:ref:`tnsnames.ora <optnetfiles>` file does not exist, then an error such as
the following is returned::

    DPY-4026: file tnsnames.ora not found in /opt/oracle/config

If :attr:`~ConnectParams.config_dir` is not specified, then the following
error is returned::

    DPY-4027: no configuration directory specified

When creating a standalone connection (or connection pool with a
:ref:`PoolParams class <poolparam>`) the equivalent internal extraction is done
automatically when a value is passed for the ``dsn`` parameter of
:meth:`oracledb.connect()`, :meth:`oracledb.connect_async()`,
:meth:`oracledb.create_pool()`, or :meth:`oracledb.create_pool_async()` but no
value is passed for the ``user`` parameter.

.. _connectionhook:

Connection Hook Functions
=========================

Python-oracledb supports protocol, password, and parameter hook functions that
can be used to customize connection logic.

.. _registerprotocolhook:

Using Protocol Hook Functions
-----------------------------

The :meth:`oracledb.register_protocol()` method registers a user protocol hook
function that will be called internally by python-oracledb Thin mode prior to
connection or pool creation.  The hook function will be invoked when
:func:`oracledb.connect`, :func:`oracledb.create_pool`,
:meth:`oracledb.connect_async()`, or :meth:`oracledb.create_pool_async()` are
called with a ``dsn`` parameter value prefixed with a specified protocol.  Your
hook function is expected to construct valid connection details, which
python-oracledb will use to complete the connection or pool creation.

You can also make use of a protocol hook function in python-oracledb Thick mode
connection calls by setting :attr:`oracledb.defaults.thick_mode_dsn_passthrough
<Defaults.thick_mode_dsn_passthrough>` to *False*. Alternatively use
:meth:`ConnectParams.parse_connect_string()`, see :ref:`usingconnparams`.

For example, the following hook function handles connection strings prefixed
with the ``tcp://`` protocol. When :func:`oracledb.connect()` is called, the
sample hook is invoked internally. It prints the parameters, and sets the
connection information in the ``params`` parameter (without passing the
``tcp://`` prefix to :meth:`~ConnectParams.parse_connect_string()` otherwise
recursion would occur).  This modified ConnectParams object is used by
python-oracledb to establish the database connection:

.. code-block:: python

    def myprotocolhook(protocol, arg, params):
        print(f"In myprotocolhook: protocol={protocol} arg={arg}")
        params.parse_connect_string(arg)

    oracledb.register_protocol("tcp", myprotocolhook)

    connection = oracledb.connect(user="scott", password=userpwd,
                                  dsn="tcp://localhost/orclpdb")

    with connection.cursor() as cursor:
        for (r,) in cursor.execute("select user from dual"):
            print(r)

The output would be::

    In myprotocolhook: protocol=tcp arg=localhost/orclpdb
    SCOTT

The ``params`` :ref:`attributes <connparamsattr>` can be set with
:meth:`ConnectParams.parse_connect_string()`, as shown, or by using
:meth:`ConnectParams.set()`.

See :ref:`ldapconnections` for a fuller example.

Internal protocol hook functions for the "tcp" and "tcps" protocols are
pre-registered but can be overridden, if needed.  If any other protocol has not
been registered, then connecting will result in an error.

Calling :meth:`~oracledb.register_protocol()` with the ``hook_function``
parameter set to None will result in a previously registered user function
being removed and the default behavior restored.

**Connection Hooks and parse_connect_string()**

A registered user protocol hook function will also be invoked in
python-oracledb Thin or Thick modes when
:meth:`ConnectParams.parse_connect_string()` is called with a
``connect_string`` parameter beginning with the registered protocol.  The hook
function ``params`` value will be the invoking ConnectParams instance that you
can update using :meth:`ConnectParams.set()` or
:meth:`ConnectParams.parse_connect_string()`.

For example, with the hook ``myprotocolhook`` shown previously, then the code:

.. code-block:: python

    cp = oracledb.ConnectParams()
    cp.set(port=1234)
    print(f"host is {cp.host}, port is {cp.port}, service name is {cp.service_name}")
    cp.parse_connect_string("tcp://localhost/orclpdb")
    print(f"host is {cp.host}, port is {cp.port}, service name is {cp.service_name}")

prints::

    host is None, port is 1234, service name is None
    In myprotocolhook: protocol=tcp arg=localhost/orclpdb
    host is localhost, port is 1234, service name is orclpdb

If you have an application that can run in either python-oracledb Thin or Thick
modes, and you want a registered connection protocol hook function to be used
in both modes, your connection code can be like:

.. code-block:: python

    dsn = "tcp://localhost/orclpdb"

    cp = oracledb.ConnectParams()
    cp.parse_connect_string(dsn)
    connection = oracledb.connect(user="hr", password=userpwd, params=cp)

.. _registerpasswordtype:

Using Password Hook Functions
-----------------------------

The :meth:`oracledb.register_password_type()` method registers a user password
hook function that will be called internally by python-oracledb prior to
connection or pool creation when :meth:`oracledb.connect()`,
:meth:`oracledb.create_pool()`, :meth:`oracledb.connect_async()`, or
:meth:`oracledb.create_pool_async()` are called. If the ``password``,
``newpassword``, or ``wallet_password`` parameters to those methods are a
dictionary containing the key "type", then the registered user password hook
function for the specific type will be invoked.  Your hook function is expected
to accept the dictionary and return the actual password string.

Below is an example of a password hook function that handles passwords of type
base64 stored in a dict like "dict(type='base64', value='dGlnZXI=')".  Note
this specific hook function is already included and registered in
python-oracledb:

.. code-block:: python

    def mypasswordhook(args):
        return base64.b64decode(args["value"].encode()).decode()

    oracledb.register_password_type("base64", mypasswordhook)

When :meth:`oracledb.connect()` is called as shown below, the sample hook is
invoked internally. It decodes the base64-encoded string in the key "value" and
returns the password which is then used by python-oracledb to establish a
connection to the database:

.. code-block:: python

    connection = oracledb.connect(user="scott",
                                  password=dict(type="base64", value="dGlnZXI="),
                                  dsn="localhost/orclpdb")

Calling :meth:`~oracledb.register_password_type()` with the ``hook_function``
parameter set to *None* will result in a previously registered user function
being removed.

.. _registerparamshook:

Using Parameter Hook Functions
------------------------------

The :meth:`oracledb.register_params_hook()` method registers a user parameter
hook function that will be called internally by python-oracledb prior to
connection or pool creation when :meth:`oracledb.connect()`,
:meth:`oracledb.create_pool()`, :meth:`oracledb.connect_async()`, or
:meth:`oracledb.create_pool_async()` are called. Your parameter hook function
should accept a copy of the parameters that will be used to create the pool or
standalone connections. The function can access and modify them in any way
necessary to allow python-oracledb to subsequently complete the connection or
pool creation request.

Pre-supplied python-oracledb plugins such as the :ref:`OCI Cloud Native
Authentication Plugin (oci_tokens) <cloudnativeauthoci>` make use of
:meth:`oracledb.register_params_hook()`. This plugin uses the information found
in a connection method's ``extra_auth_params`` parameter and modifies the
``access_token`` parameter with a function that will acquire the authentication
token needed to complete a connection. Refer to the complete plugin
implementation in `oci_tokens.py <https://github.com/oracle/python-oracledb/
blob/main/src/oracledb/plugins/oci_tokens.py>`__. The key code section showing
registering of a parameter hook function is:

.. code-block:: python

    def oci_token_hook(params: oracledb.ConnectParams):

      if params.extra_auth_params is not None:

        def token_callback(refresh):
          return generate_token(params.extra_auth_params, refresh)

        params.set(access_token=token_callback)

    oracledb.register_params_hook(oci_token_hook)

Your code might then try to connect like:

.. code-block:: python

    token_based_auth = {
        "auth_type": "SimpleAuthentication",
        "user": <user>,
        "key_file": <key_file>,
        "fingerprint": <fingerprint>,
        "tenancy": <tenancy>,
        "region": <region>,
        "profile": <profile>
    }

    connection = oracledb.connect(
        dsn=mydb_low,
        extra_auth_params=token_based_auth)

To unregister a user function that was earlier registered, you can use
:meth:`oracledb.unregister_params_hook`.

If you have registered user hook methods with
:meth:`oracledb.register_protocol()` and
:meth:`oracledb.register_params_hook`, then the method registered with
:meth:`oracledb.register_protocol()` is invoked first during connection or pool
creation calls. If you call :meth:`ConnectParams.parse_connect_string()`, the
registered protocol hook method will be called but the parameter hook will not
be.

..
   Note to doc writers: do not change the following heading because it is used
   for a link emitted by ldap_hook() in src/oracledb/builtin_hooks.py

.. _ldapconnections:

LDAP Directory Naming
=====================

Directory Naming centralizes the network names and addresses used for
connections in a single place. More details can be found in `Configuring Oracle
Database Clients for OID and OUD Directory Naming
<https://www.oracle.com/a/otn/docs/database/oracle-net-oud-oid-directory-naming.pdf>`__
and `Configuring Oracle Database Clients for Microsoft Active Directory Naming
<https://www.oracle.com/a/otn/docs/database/oracle-net-active-directory-naming.pdf>`__.

The DSN for LDAP connections can be an alias, as shown in the above references.
Alternatively it can be an LDAP URL. The URL syntax removes the need for
external LDAP and ``sqlnet.ora`` configuration files. See the technical brief
`Oracle Client 23ai LDAP URL Syntax
<https://www.oracle.com/a/otn/docs/database/oracle-net-23ai-ldap-url.pdf>`__.

**Python-oracledb Thick Mode LDAP Aliases**

Once a directory server is configured, and necessary configuration files have
been created as explained in the above references, python-oracledb Thick mode
applications can use the LDAP alias as the python-oracledb connection DSN:

.. code-block:: python

    connection = oracledb.connect(user="scott", password=pw, dsn="myLdapAlias")

**Python-oracledb Thick Mode LDAP URLs**

Python-oracledb Thick mode applications using Oracle Client 23.4, or later, can
connect with an LDAP URL. For example:

.. code-block:: python

    ldapurl = "ldaps://ldapserver.example.com/cn=orcl,cn=OracleContext,dc=example,dc=com"
    connection = oracledb.connect(user="scott", password=pw, dsn=ldapurl)

To use an LDAP URL in python-oracledb Thick mode when
:attr:`oracledb.defaults.thick_mode_dsn_passthrough
<Defaults.thick_mode_dsn_passthrough>` is *False*, a connection hook function
is required as shown below for Thin mode. This lets LDAP URLs be utilized when
python-oracledb uses any supported Oracle Client library version.

**Python-oracledb Thin Mode LDAP URLs**

To use LDAP in python-oracledb Thin mode, call
:meth:`oracledb.register_protocol()` to register your own user :ref:`connection
protocol hook function <registerprotocolhook>` that gets the database
connection string from your LDAP server. Your application can then specify an
LDAP URL as the DSN in connection and pool creation calls.

For example:

.. code-block:: python

    import ldap3
    import re

    # Get the Oracle Database connection string from an LDAP server when
    # connection calls use an LDAP URL.
    # In this example, "protocol"' will have the value "ldap", and "arg" will
    # be "ldapserver/dbname,cn=OracleContext,dc=dom,dc=com"

    def ldap_hook(protocol, arg, params):
        pattern = r"^(.+)\/(.+)\,(cn=OracleContext.*)$"
        match = re.match(pattern, arg)
        ldap_server, db, ora_context = match.groups()

        server = ldap3.Server(ldap_server)
        conn = ldap3.Connection(server)
        conn.bind()
        conn.search(ora_context, f"(cn={db})", attributes=['orclNetDescString'])
        connect_string = conn.entries[0].orclNetDescString.value
        params.parse_connect_string(connect_string)

    oracledb.register_protocol("ldap", ldap_hook)

    connection = oracledb.connect(user="hr", password=userpwd,
                 dsn="ldap://ldapserver/dbname,cn=OracleContext,dc=dom,dc=com")

You can modify or extend this as needed, for example to use an LDAP module that
satisfies your business and security requirements, to handled LDAPS, or to
cache the response from the LDAP server.

.. _appcontext:

Connection Metadata and Application Contexts
============================================

During connection you can set additional metadata properties that can be
accessed in the database for tracing and for enforcing fine-grained data
access, for example with Oracle Virtual Private Database policies. Values may
appear in logs and audit trails.

**End-to-End Tracing Attributes**

The connection attributes :attr:`Connection.client_identifier`,
:attr:`Connection.clientinfo`, :attr:`Connection.dbop`,
:attr:`Connection.module`, and :attr:`Connection.action` set metadata about the
connection.

It is recommended to always set at least :attr:`~Connection.client_identifier`,
:attr:`~Connection.module`, and :attr:`~Connection.action` for all applications
because their availability in the database can greatly aid future
troubleshooting.

See :ref:`endtoendtracing` for more information.

**Application Contexts**

An application context stores user identification that can enable or prevent a
user from accessing data in the database.  See the Oracle AI Database
documentation `About Application Contexts <https://www.oracle.com/pls/topic/
lookup?ctx=dblatest&id=GUID-6745DB10-F540-45D7-9761-9E8F342F1435>`__.

A context has a namespace and a key-value pair. The namespace CLIENTCONTEXT is
reserved for use with client session-based application contexts. Contexts are
set during connection as an array of 3-tuples containing string values for the
namespace, key, and value.  For example:

.. code-block:: python

    myctx = [
        ("clientcontext", "loc_id", "1900")
    ]

    connection = oracledb.connect(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb",
                                  appcontext=myctx)

Context values set during connection can be directly queried in your
applications. For example:

.. code-block:: python

    with connection.cursor() as cursor:
        sql = """select * from locations
                 where location_id = sys_context('clientcontext', 'loc_id')"""
        for r in cursor.execute(sql):
            print(r)

This will print::

    (1900, '6092 Boxwood St', 'YSW 9T2', 'Whitehorse', 'Yukon', 'CA')

Multiple context values can be set when connecting. For example:

.. code-block:: python

    myctx = [
        ("clientcontext", "loc_id", "1900"),
        ("clientcontext", "my_world", "earth"),
    ]

    connection = oracledb.connect(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb",
                                  appcontext=myctx)

    with connection.cursor() as cursor:
        sql = """select sys_context('clientcontext', 'loc_id'),
                        sys_context('clientcontext', 'my_world')
                 from dual"""
        for r in cursor.execute(sql):
            print(r)

will display::

    ('1900', 'earth')

You can use contexts to set up restrictive policies that are automatically
applied to any query executed. See Oracle AI Database documentation `Oracle
Virtual Private Database (VPD) <https://www.oracle.com/pls/topic/lookup?ctx=
dblatest&id=GUID-06022729-9210-4895-BF04-6177713C65A7>`__.

.. _connpooling:

Connection Pooling
==================

Connection pooling can significantly improve application performance and
scalability by allowing resource sharing. Pools also let applications use
optional advanced Oracle High Availability features.

Opening a connection to a database can be expensive: the connection string must
be parsed, a network connection must be established, the Oracle Database
network listener needs to be invoked, user authentication must be performed, a
database server process must be created, and session memory must be allocated
(and then the process is destroyed when the connection is closed). Connection
pools remove the overhead of repeatedly opening and closing :ref:`standalone
connections <standaloneconnection>` by establishing a pool of open connections
that can be reused throughout the life of an application process.

Various Oracle Database authentication methods are supported in
python-oracledb, see :ref:`authenticationmethods`.

The pooling solutions available to python-oracledb applications are:

- :ref:`Driver Connection Pools <driverconnpool>`: These are managed by the
  driver layer. They provide readily available database connections that can be
  shared by multiple users and are quick for applications to obtain.  They help
  make applications scalable and highly available. They are created with
  :meth:`oracledb.create_pool()` or :meth:`oracledb.create_pool_async()`.

  The main use case is for applications that hold connections for relatively
  short durations while doing database work, and that acquire and release
  connections back to the pool as needed to do those database operations.
  Using a driver pool is recommended for applications that need to support
  multiple users. High availability benefits also make driver pools useful for
  single-user applications that do infrequent database operations.

- :ref:`drcp`: This is pooling of server processes on the database host so they
  can be shared between application connections. This reduces the number of
  server processes that the database host needs to manage.

  DRCP is useful if there are large number of application connections,
  typically from having multiple application processes, and those applications
  do frequent connection acquire and release calls as needed to do database
  operations.  It is recommended to use DRCP in conjunction with a driver
  connection pool, since this reduces the number of re-authentications and
  session memory re-allocations.

- `Proxy Resident Connection Pooling (PRCP)
  <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-E0032017-03B1-
  4F14-AF9B-BCC87C982DA8>`__: This is connection pooling handled by Oracle's
  mid-tier connection proxy solution, `CMAN-TDM <https://download.oracle.com/
  ocomdocs/global/
  CMAN_TDM_Oracle_DB_Connection_Proxy_for_scalable_apps.pdf>`__.

  PRCP is useful for applications taking advantage of CMAN-TDM.

- :ref:`implicitconnpool`: This can add pooling benefits to applications that
  connect when they start, and only close the connection when the application
  terminates — but relatively infrequently do database work. It makes use of
  DRCP or PRCP, but instead of relying on the application to explicitly acquire
  and release connections, Implicit Connection Pooling automatically detects
  when applications are not performing database work. It then allows the
  associated database server process to be used by another connection that
  needs to do a database operation.

  Implicit Connection Pooling is useful for legacy applications or third-party
  code that cannot be updated to use a driver connection pool.

Python-oracledb :ref:`driver connection pools <driverconnpool>` are the first
choice for performance, scalability, and high availability.  If your database
is under memory pressure from having too many applications opening too many
connections, then consider either :ref:`DRCP <drcp>` or :ref:`Implicit
Connection Pooling <implicitconnpool>`, depending on your application’s
connection life-cycle. If you are utilizing CMAN-TDM, then using `PRCP
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-
E0032017-03B1-4F14-AF9B-BCC87C982DA8>`__ can be considered.

.. _driverconnpool:

Driver Connection Pooling
-------------------------

Python-oracledb's driver connection pooling lets applications create and
maintain a pool of open connections to the database.  Connection pooling is
available in both Thin and :ref:`Thick <enablingthick>` modes.  Connection
pooling is important for performance and scalability when applications need to
handle a large number of users who do database work for short periods of time
but have relatively long periods when the connections are not needed.  The high
availability features of pools also make small pools useful for applications
that want a few connections available for infrequent use and requires them to
be immediately usable when acquired.  Applications that would benefit from
connection pooling but are too difficult to modify from the use of
:ref:`standalone connections <standaloneconnection>` can take advantage of
:ref:`implicitconnpool`.

In python-oracledb Thick mode, the pool implementation uses Oracle's `session
pool technology <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-F9662FFB-EAEF-495C-96FC-49C6D1D9625C>`__ which supports additional
Oracle Database features, for example some advanced :ref:`high availability
<highavailability>` features.

.. note::

    Python-oracledb driver connection pools must be created, used, and closed
    within the same process. Sharing pools or connections across processes has
    unpredictable behavior.

    Using connection pools in multi-threaded architectures is supported.

    Multi-process architectures that cannot be converted to threading may get
    some benefit from :ref:`drcp`.

Creating a Connection Pool
++++++++++++++++++++++++++

A driver connection pool is created by calling :meth:`oracledb.create_pool()`.
Various pool options can be specified as described in
:meth:`~oracledb.create_pool()` and detailed below.

For example, to create a pool that initially contains one connection but
can grow up to five connections:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb",
                                min=1, max=5, increment=1)

Getting Connections from a Pool
+++++++++++++++++++++++++++++++

After a pool has been created, your application can get a connection from
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

Note that when using this option value in python-oracledb Thick mode with
Oracle Client libraries 12.2 or earlier, the :meth:`~ConnectionPool.acquire()`
call will still wait if the pool can grow.  However, you will get an error
immediately if the pool is at its maximum size.  With newer Oracle Client
libraries and with Thin mode, an error will be returned if the pool has to, or
cannot, grow.

Returning Connections to a Pool
+++++++++++++++++++++++++++++++

When your application has finished performing all required database operations,
the pooled connection should be released back to the pool to make it available
for other users. For example, you can use a Python `context manager
<https://docs.python.org/3/library/stdtypes.html#context-manager-types>`__
``with`` block which lets pooled connections be closed implicitly at the end of
scope and cleans up dependent resources:

.. code-block:: python

    with pool.acquire() as connection:
        with connection.cursor() as cursor:
            for result in cursor.execute("select * from mytab"):
                print(result)

Alternatively, you can explicitly return connections with
:meth:`ConnectionPool.release()` or :meth:`Connection.close()`, however you may
also need to close other resources first.

If you need to force a connection to be closed and its associated database
server process to be released, use :meth:`ConnectionPool.drop()`:

.. code-block:: python

    with pool.acquire() as connection:

        . . .

        pool.drop(connection)

Avoid doing this unnecessarily because it shrinks the pool. A future
:meth:`~ConnectionPool.acquire()` call may suffer the overhead of establishing
a new connection to the database, instead of being able to reuse a connection
already available in the pool.

Closing a Connection Pool
+++++++++++++++++++++++++

At application shutdown, the connection pool can be completely closed using
:meth:`ConnectionPool.close()`:

.. code-block:: python

    pool.close()

To force immediate pool termination when connections are still in use, execute:

.. code-block:: python

    pool.close(force=True)

See `connection_pool.py <https://github.com/oracle/python-oracledb/tree/main/
samples/connection_pool.py>`__ for a runnable example of connection pooling.

.. _connpoolcache:

Using the Connection Pool Cache
-------------------------------

When your application architecture makes it difficult to pass a
:ref:`ConnectionPool object <connpool>` between your code layers, you can use
the python-oracledb connection pool cache. This lets you store and retrieve
pools by name.

**Adding a pool to the python-oracledb connection pool cache**

To use the python-oracledb pool cache, specify the ``pool_alias`` parameter
when you create a pool during application initialization. Its value should be a
user-chosen string. For example:

.. code-block:: python

    import oracledb

    NAME = "my_pool"

    oracledb.create_pool(
        user="hr",
        password=userpwd,
        dsn="dbhost.example.com/orclpdb",
        pool_alias=NAME
    )

This creates a pool and stores it in the cache under the name "my_pool". The
application does not need to store or manage the reference to the pool so the
:meth:`~oracledb.create_pool()` return value is not saved.

If a pool already exists with the name "my_pool", the following error will
be raised::

    DPY-2055: connection pool with name "my_pool" already exists

**Getting a connection from a cached pool**

Applications can get a connection from a cached pool by passing its name
directly to :meth:`oracledb.connect()`:

.. code-block:: python

    import oracledb

    NAME = "my_pool"

    connection = oracledb.connect(pool_alias=NAME)

This is equivalent to calling :meth:`ConnectionPool.acquire()`. You can pass
additional parameters to :meth:`~oracledb.connect()` that are allowed for
:meth:`~ConnectionPool.acquire()`. For example, with a :ref:`heterogeneous
<connpooltypes>` pool you can pass the username and password:

.. code-block:: python

    import oracledb

    NAME = "my_pool"

    connection = oracledb.connect(pool_alias=NAME, user="toto", password=pw)

If there is no pool named ``my_pool`` in the cache, you will get the following
error::

    DPY-2054: connection pool with name "my_pool" does not exist

You cannot pass ``pool_alias`` and the deprecated ``pool`` parameter together
to :meth:`oracledb.connect()` or :meth:`oracledb.connect_async()`. If you do,
the following error is raised::

    DPY-2014: "pool_alias" and "pool" cannot be specified together

**Getting a pool from the connection pool cache**

You can use :meth:`oracledb.get_pool()` to retrieve a pool and then access it
directly:

.. code-block:: python

    import oracledb

    NAME = "my_pool"

    pool = oracledb.get_pool(NAME)
    connection = pool.acquire()

This allows any connection pool :ref:`method <connpoolmethods>` or
:ref:`attribute <connpoolattr>` from a cached pool to be used, as normal.

If there is no pool named ``my_pool`` in the cache, then
:meth:`~oracledb.get_pool()` will return None.

**Removing a pool from the cache**

A pool is automatically removed from the cache when the pool is closed:

.. code-block:: python

    import oracledb

    NAME = "my_pool"

    pool = oracledb.get_pool(NAME)
    pool.close()

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
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-7DFBA826-7CC0-
4D16-B19C-31D168069B54>`__, which contains more details about sizing of pools.
Having a fixed size will also guarantee that the database can handle the upper
pool size.  For example, if a dynamically sized pool needs to grow but the
database resources are limited, then :meth:`ConnectionPool.acquire()` may
return errors such as `ORA-28547 <https://docs.oracle.com/error-help/db/ora-
28547/>`__, or the database may simply drop connection attempts and
python-oracledb will show :ref:`DPY-4011 <dpy4011>`. With a fixed pool size,
this class of error will generally occur when the pool is created, allowing you
to change the pool size or reconfigure the database before users access the
application.  With a dynamically growing pool, the error may occur much later
while the application is in use.

The Real-World Performance Group also recommends keeping pool sizes small
because they often can perform better than larger pools. The pool attributes
should be adjusted to handle the desired workload within the bounds of
available resources in python-oracledb and the database.

Connection Pool Growth
++++++++++++++++++++++

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
of :data:`oracledb.POOL_GETMODE_WAIT`, any :meth:`~ConnectionPool.acquire()`
call that initiates pool growth will return after the first new connection is
created, regardless of how big ``increment`` is.  The pool will then continue
to re-establish connections in a background thread.

A connection pool can shrink back to its minimum size ``min`` when connections
opened by the pool are not used by the application. This frees up database
resources while allowing pools to retain open connections for active users. If
there are more than ``min`` connections open, and connections are idle in the
pool (i.e. not currently acquired by the application) and unused for longer
than the pool creation attribute ``timeout`` value, then they will be closed.
The check occurs every ``timeout`` interval and hence in the worst case it may
take twice the ``timeout`` time to close the idle connections. The default
``timeout`` is *0* seconds signifying an infinite time and meaning idle
connections will never be closed.

The pool creation parameter ``max_lifetime_session`` also allows pools to
shrink. This parameter bounds the total length of time that a connection can
exist starting from the time that it was created in the pool. It is mostly used
for defensive programming to mitigate against unforeseeable problems that may
occur with connections. If a connection was created ``max_lifetime_session`` or
longer seconds ago, then it will be a candidate for being closed. In the case
when ``timeout`` and ``max_lifetime_session`` are both set, the connection will
be terminated if either the idle timeout happens or the maximum lifetime
setting is exceeded. Note that when using python-oracledb in Thick mode with
Oracle Client libraries prior to 21c, pool shrinkage is only initiated when the
pool is accessed so pools in fully dormant applications will not shrink until
the application is next used. In Thick mode, Oracle Client libraries 12.1, or
later, are needed to use ``max_lifetime_session``.

For pools created with :ref:`external authentication <extauth>`, with
:ref:`homogeneous <connpooltypes>` set to False, or when using :ref:`drcp` (in
python-oracledb Thick mode), then the number of connections opened at pool
creation is zero even if a larger value is specified for ``min``.  Also, in
these cases the pool increment unit is always 1 regardless of the value of
``increment``.

.. _poolhealth:

Pool Connection Health
----------------------

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
in the pool (i.e. not acquired by the application) for
:data:`ConnectionPool.ping_interval` seconds.  If the ping fails, the
connection will be discarded and another one obtained before
:meth:`~ConnectionPool.acquire()` returns to the application.  The
``ping_timeout`` parameter to :meth:`oracledb.create_pool()` limits the amount
of time that any internal ping is allowed to take. If it is exceeded, perhaps
due to a network hang, the connection is considered unusable and a different
connection is returned to the application.

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
impact performance and scalability.  To avoid pings hanging due to network
errors, use :attr:`Connection.call_timeout` to limit the amount of time
:meth:`~Connection.ping()` is allowed to take.

The :meth:`Connection.is_healthy()` method is an alternative to
:meth:`Connection.ping()`.  It has lower overheads and may suit some uses, but
it does not perform a full connection check.

If the ``getmode`` parameter in :meth:`oracledb.create_pool()` is set to
:data:`oracledb.POOL_GETMODE_TIMEDWAIT`, then the maximum amount of time an
:meth:`~ConnectionPool.acquire()` call will wait to get a connection from the
pool is limited by the value of the :data:`ConnectionPool.wait_timeout`
parameter.  A call that cannot be immediately satisfied will wait no longer
than ``wait_timeout`` regardless of the value of ``ping_timeout``.

Connection pool health can be impacted by :ref:`firewalls <hanetwork>`,
`resource managers <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
GUID-2BEF5482-CF97-4A85-BD90-9195E41E74EF>`__ or user profile `IDLE_TIME
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-ABC7AE4D-64A8-
4EA9-857D-BEF7300B64C3>`__ values. For best efficiency, ensure these do not
expire idle sessions since this will require connections to be recreated which
will impact performance and scalability.

A pool's internal connection re-establishment after lightweight and full pings
can mask performance-impacting configuration issues such as firewalls
terminating connections.  You should monitor `AWR <https://www.oracle.com/pls/
topic/lookup?ctx=dblatest&id=GUID-56AEF38E-9400-427B-A818-EDEC145F7ACD>`__
reports for an unexpectedly large connection rate.

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

Session Callbacks for Setting Pooled Connection State
-----------------------------------------------------

Applications can set "session" state in each connection.  Examples of session
state are :ref:`NLS globalization <globalization>` settings from ``ALTER
SESSION`` statements.  Pooled connections will retain their session state after
they have been released back to the pool.  However, because pools can grow or
connections in the pool can be recreated, there is no guarantee a subsequent
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

    Connection tagging is only supported in python-oracledb Thick mode. See
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

    PL/SQL Callbacks are only supported in python-oracledb Thick mode. See
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
                              purity=oracledb.PURITY_SELF)

See `session_callback_plsql.py
<https://github.com/oracle/python-oracledb/tree/main/
samples/session_callback_plsql.py>`__ for an example.

.. _connpooltypes:

Heterogeneous and Homogeneous Connection Pools
----------------------------------------------

**Homogeneous Pools**

By default, connection pools are 'homogeneous', meaning that all connections
use the same database credentials.  Both python-oracledb Thin and :ref:`Thick
<enablingthick>` modes support homogeneous pools.

**Heterogeneous Pools**

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
returns a :ref:`PoolParams <poolparam>` object.  This is a subclass of the
:ref:`ConnectParams class <connparam>` (see :ref:`usingconnparams`) with
additional pool-specific attributes such as the maximum pool size. A
``PoolParams`` object can be passed to :func:`oracledb.create_pool()`. For
example:

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

Some values such as the database host name can be specified as
:func:`oracledb.create_pool()` parameters, as part of the ``dsn`` connection
string, and in the ``params`` object. A final connection string is internally
constructed from any ``dsn``, individual parameters, and ``params`` object
values. The precedence is that values in a ``dsn`` parameter override values
passed as individual parameters, which themselves override values set in the
``params`` object.

Most PoolParams arguments are gettable as properties.  They may be set
individually using the ``set()`` method:

.. code-block:: python

    pp = oracledb.PoolParams()
    pp.set(min=5)
    print(pp.min) # 5

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
memory required on the database host.  A DRCP pool can be shared by multiple
applications.

DRCP is useful for applications which share the same database credentials, have
similar session settings (for example date format settings or PL/SQL package
state), and where the application gets a database connection, works on it for a
relatively short duration, and then releases it.

For efficiency, it is recommended that DRCP connections should be used in
conjunction with python-oracledb's local :ref:`connection pool <connpooling>`.
Using DRCP with :ref:`standalone connections <standaloneconnection>` is not as
efficient but does allow the database to reuse database server processes which
can provide a performance benefit for applications that cannot use a local
connection pool. In this scenario, make sure to configure enough DRCP
authentication servers to handle the connection load.

Although applications can choose whether or not to use DRCP pooled connections
at runtime, care must be taken to configure the database appropriately for the
number of expected connections, and also to stop inadvertent use of non-DRCP
connections leading to a database server resource shortage. Conversely, avoid
using DRCP connections for long-running operations.

For more information about DRCP, see the technical brief `Extreme Oracle
Database Connection Scalability with Database Resident Connection Pooling
(DRCP) <https://www.oracle.com/docs/tech/drcp-technical-brief.pdf>`__, the user
documentation `Oracle AI Database Concepts Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-531EEE8A-B00A-4C03-A2ED-D45D92B3F797>`__, and for DRCP Configuration
see `Oracle AI Database Administrator's Guide
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-82FF6896-F57E-41CF-89F7-755F3BC9C924>`__.

Using DRCP with python-oracledb applications involves the following steps:

1. Enabling DRCP in the database
2. Configuring the application to use DRCP pooled servers

Enabling DRCP in Oracle Database
--------------------------------

Oracle Database versions prior to 21c can have a single DRCP connection pool.
From Oracle Database 21c, each pluggable database can optionally have its own
pool, or can use the container level pool. From Oracle Database 23.4, you can
create multiple pools at the pluggable, or container, database level. This
multi-pool feature is useful where different applications connect to the same
database, but there is a concern that one application's use of the pool may
impact other applications. If this is not the case, a single pool may allow
best resource sharing on the database host.

Note that DRCP is already enabled in Oracle Autonomous Database and pool
management is different to the steps below.

In the basic scenario, DRCP pools can be configured and administered by a DBA
using the ``DBMS_CONNECTION_POOL`` package:

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

When DRCP is used with `Oracle RAC
<https://www.oracle.com/database/real-application-clusters/>`__, each database
instance has its own connection broker and pool of servers.  Each pool has the
identical configuration.  For example, all pools start with ``minsize`` server
processes.  A single DBMS_CONNECTION_POOL command will alter the pool of each
instance at the same time.  The pool needs to be started before connection
requests begin.  The command below does this by bringing up the broker, which
registers itself with the database listener:

.. code-block:: sql

    EXECUTE DBMS_CONNECTION_POOL.START_POOL()

Once enabled this way, the pool automatically restarts when the database
instance restarts, unless explicitly stopped with the
``DBMS_CONNECTION_POOL.STOP_POOL()`` command:

.. code-block:: sql

    EXECUTE DBMS_CONNECTION_POOL.STOP_POOL()

Oracle Database version 23 allows a ``DRAINTIME`` argument to be passed to
``STOP_POOL()``, indicating that the pool will only be closed after the
specified time.  This allows in-progress application work to continue. A
draintime value of 0 can be used to immediately close the pool. See the
database documentation on `DBMS_CONNECTION_POOL.STOP_POOL()
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-3FF5F327-7BE3-
4EA8-844F-29554EE00B5F>`__.

In older database versions, the pool cannot be stopped while connections are
open.

Coding Applications to use DRCP
-------------------------------

To use DRCP, application connection establishment must request a DRCP pooled
server and should specify a user-chosen connection class name. A 'purity' of
the connection session state can optionally be specified. See the Oracle
Database documentation on `benefiting from scalability
<https://www.oracle.com/pls/topic/lookup?ctx=
dblatest&id=GUID-661BB906-74D2-4C5D-9C7E-2798F76501B3>`__ for more information
on purity and connection classes.

The best practice is to use DRCP in conjunction with a local driver
:ref:`connection pool <connpooling>` created with
:meth:`oracledb.create_pool()` or :meth:`oracledb.create_pool_async()`. The
python-oracledb connection pool size does not need to match the DRCP pool size.
The limit on overall execution parallelism is determined by the DRCP pool
size. Note that when using DRCP with a python-oracledb local connection pool in
Thick mode, the local connection pool ``min`` value is ignored and the pool
will be created with zero connections.

See `drcp_pool.py
<https://github.com/oracle/python-oracledb/tree/main/samples/drcp_pool.py>`__
for a runnable example of DRCP.

**Requesting Pooled Servers be Used**

To enable connections to use DRCP pooled servers, you can:

- Use a specific connection string in :meth:`oracledb.create_pool()` or
  :meth:`oracledb.connect()` to request a pooled server. For example with the
  :ref:`Easy Connect syntax <easyconnect>`:

  .. code-block:: python

        pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb:pooled",
                                    min=2, max=5, increment=1,
                                    cclass="MYAPP")

- Alternatively, add ``(SERVER=POOLED)`` to the :ref:`Connect Descriptor
  <conndescriptor>` such as used in an Oracle Network configuration file
  :ref:`tnsnames.ora <optnetfiles>`::

    customerpool = (DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)
              (HOST=dbhost.example.com)
              (PORT=1521))(CONNECT_DATA=(SERVICE_NAME=CUSTOMER)
              (SERVER=POOLED)))

- Another way to use a DRCP pooled server is to set the ``server_type``
  parameter during standalone connection creation or python-oracledb
  connection pool creation.  For example:

  .. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb",
                                min=2, max=5, increment=1,
                                server_type="pooled",
                                cclass="MYAPP")

**DRCP Connection Classes**

The best practice is to specify a ``cclass`` class name when creating a
python-oracledb connection pool.  This user-chosen name provides some
partitioning of DRCP session memory so reuse is limited to similar
applications.  It provides maximum pool sharing if multiple application
processes are started and use the same class name.  A class name also allows
better DRCP usage tracking in the database.  In the database monitoring views,
the class name shown will be the value specified in the application prefixed
with the user name.

If ``cclass`` was not specified during pool creation, then python-oracledb Thin
mode generates a unique connection class with the prefix "DPY" while
python-oracledb Thick mode generates a unique connection class with the prefix
"OCI".

To create a connection pool requesting DRCP pooled servers be used, and
specifying a class name, you can call:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb:pooled",
                                min=2, max=5, increment=1,
                                cclass="MYAPP")

If ``cclass`` is not set, then the pooled server sessions will not be reused
optimally, and the :ref:`DRCP statistic views <monitoringdrcp>` may record
large values for NUM_MISSES.

**DRCP Connection Purity**

DRCP allows the connection session memory to be reused or cleaned each time a
connection is acquired from the pool.  The pool or connection creation
``purity`` parameter can be one of ``PURITY_NEW``, ``PURITY_SELF``, or
``PURITY_DEFAULT``.  The value ``PURITY_SELF`` allows reuse of both the pooled
server process and session memory, giving maximum benefit from DRCP.  By
default, python-oracledb pooled connections use ``PURITY_SELF`` and standalone
connections use ``PURITY_NEW``.

To limit session sharing, you can explicitly require that new session memory be
allocated each time :meth:`~ConnectionPool.acquire()` is called. Do this when
creating a driver connection pool by specifying the ``purity`` as
``PURITY_NEW``:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb:pooled",
                                min=2, max=5, increment=1,
                                cclass="MYAPP", purity=oracledb.PURITY_NEW)

The overheads can impact ultimate scalability.

.. _poolnames:

**DRCP Pool Names**

From Oracle Database 23.4, multiple DRCP pools can be created by setting a pool
name at DRCP pool creation time. Applications using python-oracledb Thin mode
can specify which DRCP pool to use by passing the ``pool_name`` parameter
during connection or connection pool creation, for example:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd,
                                dsn="dbhost.example.com/orclpdb:pooled",
                                min=2, max=5, increment=1,
                                cclass="MYAPP", pool_name="MYPOOL")

When specifying a pool name, you should still set a connection class name to
allow efficient use of the pool's resources.

If you are using python-oracledb Thick mode and the
``thick_mode_dsn_passthrough`` value in effect is *True*, you can use the
``pool_name`` parameter only if the ``dsn`` parameter is not specified when
creating a standalone or pooled connection, for example:

.. code-block:: python

    oracledb.init_oracle_client()

    pool = oracledb.create_pool(user="hr", password=userpwd,
                                host="localhost", service_name="orclpdb",
                                server_type="pooled", min=2, max=5,
                                increment=1, cclass="MYAPP",
                                pool_name="MYPOOL")

If both the ``pool_name`` and ``dsn`` parameters are set when using Thick mode,
the ``pool_name`` parameter is ignored.

For Thick mode, you may prefer to set the Oracle Net
Services parameter `POOL_NAME <https://www.oracle.com/pls/topic/lookup?ctx=
dblatest&id=GUID-C2DA6A42-C30A-4E4C-9833-51CB383FE08B>`__ parameter in the
:ref:`easy connect string <easyconnect>` or
:ref:`connect descriptor <conndescriptor>`, for example:

.. code-block:: python

    oracledb.init_oracle_client()

    pool = oracledb.create_pool(user="hr", password=userpwd,
                                dsn="dbhost.example.com/orclpdb:pooled?pool_name=mypool",
                                min=2, max=5, increment=1,
                                cclass="MYAPP")

You can also define the DRCP pool name with the
:ref:`ConnectParams class <connparam>` when using python-oracledb Thin or Thick
mode. See :ref:`usingconnparams`.

**Acquiring a DRCP Connection**

Once DRCP has been enabled and the driver connection pool has been created with
the appropriate connection string, then your application can get a connection
that uses DRCP by calling:

.. code-block:: python

    connection = pool.acquire()

Connection class names can also be passed to :meth:`~ConnectionPool.acquire()`
if you want to use a connection with a different class:

.. code-block:: python

    pool = oracledb.create_pool(user="hr", password=userpwd, dsn="dbhost.example.com/orclpdb:pooled",
                                min=2, max=5, increment=1,
                                cclass="MYAPP")

    connection = mypool.acquire(cclass="OTHERAPP")

If a pooled server of a requested class is not available, a server with new
session state is used.  If the DRCP pool cannot grow, a server with a different
class may be used and its session state cleared.

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
    connection.close()              # <- Add this to release the DRCP pooled server

    # Do lots of non-database work
    . . .

    # Do some more database operations
    connection = mypool.acquire()   # <- And get a new pooled server only when needed
    . . .
    connection.close()

Setting DRCP Parameters in Connection Strings
---------------------------------------------

Setting the DRCP connection class, purity, and pool name as function parameters
in the application is preferred, but sometimes it is not possible to modify an
existing code base. For these applications, you can specify the values along
with the pooled server option in the connection string.

You can specify the class and purity options in connection strings when using
Oracle Database 21c, or later. You can specify the pool name when using Oracle
Database 23.4, or later.

For example with the :ref:`Easy Connect <easyconnect>` syntax::

    dbhost.example.com/orclpdb:pooled?pool_connection_class=MYAPP&pool_purity=self&pool_name=MYPOOL

Or by using a :ref:`TNS Alias <netservice>` in a
:ref:`tnsnames.ora <optnetfiles>` file::

    customerpool = (DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)
              (HOST=dbhost.example.com)
              (PORT=1521))(CONNECT_DATA=(SERVICE_NAME=orclpdb)
              (SERVER=POOLED)
              (POOL_CONNECTION_CLASS=MYAPP)
              (POOL_PURITY=SELF)
              (POOL_NAME=MYPOOL)))

Explicitly specifying the purity as *SELF* in a connection string may cause
some unusable connections in a python-oracledb Thick mode connection pool to
not be terminated, potentially eventually rendering all connections in the pool
to be unusable. If you cannot programmatically set the class name and purity,
or cannot use python-oracledb Thin mode, then avoid explicitly setting the
purity as a connection string parameter when using a local python-oracledb
Thick mode connection pool.

.. _monitoringdrcp:

Monitoring DRCP
---------------

Data dictionary views are available to monitor the performance of DRCP.
Database administrators can check statistics such as the number of busy and
free servers, and the number of hits and misses in the pool against the total
number of requests from clients. The views include:

* DBA_CPOOL_INFO
* V$PROCESS
* V$SESSION
* V$CPOOL_STATS
* V$CPOOL_CC_STATS
* V$CPOOL_CONN_INFO

**DBA_CPOOL_INFO View**

DBA_CPOOL_INFO displays configuration information about the DRCP pool.  The
columns are equivalent to the ``dbms_connection_pool.configure_pool()``
settings described in the table of DRCP configuration options, with the
addition of a STATUS column.  The status is ``ACTIVE`` if the pool has been
started and ``INACTIVE`` otherwise.  Note that the pool name column is called
CONNECTION_POOL.  This example checks whether the pool has been started and
finds the maximum number of pooled servers::

    SQL> SELECT connection_pool, status, maxsize FROM dba_cpool_info;

    CONNECTION_POOL              STATUS        MAXSIZE
    ---------------------------- ---------- ----------
    SYS_DEFAULT_CONNECTION_POOL  ACTIVE             40

**V$PROCESS and V$SESSION Views**

The V$SESSION view shows information about the currently active DRCP
sessions.  It can also be joined with V$PROCESS through
``V$SESSION.PADDR = V$PROCESS.ADDR`` to correlate the views.

**V$CPOOL_STATS View**

The V$CPOOL_STATS view displays information about the DRCP statistics for
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

The view V$CPOOL_CC_STATS displays information about the connection class
level statistics for the pool per instance::

    SQL> select cclass_name, num_requests, num_hits, num_misses
         from v$cpool_cc_stats;

    CCLASS_NAME                      NUM_REQUESTS   NUM_HITS NUM_MISSES
    -------------------------------- ------------ ---------- ----------
    HR.MYCLASS                             100031      99993         38


The class name columns shows the database user name appended with the
connection class name.

**V$CPOOL_CONN_INFO View**

The V$POOL_CONN_INFO view gives insight into client processes that are
connected to the connection broker, making it easier to monitor and trace
applications that are currently using pooled servers or are idle. This view was
introduced in Oracle 11gR2.

You can monitor the view V$CPOOL_CONN_INFO to, for example, identify
misconfigured machines that do not have the connection class set correctly.
This view maps the machine name to the class name.  In python-oracledb Thick
mode, the class name will be default to one like shown below::

    SQL> select cclass_name, machine from v$cpool_conn_info;

    CCLASS_NAME                             MACHINE
    --------------------------------------- ------------
    CJ.OCI:SP:wshbIFDtb7rgQwMyuYvodA        cjlinux

In this example, you would examine applications on ``cjlinux`` and make them
set ``cclass``.

When connecting to Oracle Autonomous Database on Shared Infrastructure (ADB-S),
the V$CPOOL_CONN_INFO view can be used to track the number of connection
hits and misses to show the pool efficiency.

.. _implicitconnpool:

Implicit Connection Pooling
===========================

`Implicit connection pooling <https://
www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-A9D74994-D81A-47BF-BAF2-
E4E1A354CA99>`__ is useful for applications that cause excess database server
load due to the number of :ref:`standalone connections <standaloneconnection>`
opened.  When these applications cannot be rewritten to use
:ref:`python-oracledb connection pooling <connpooling>`, then implicit
connection pooling may be an option to reduce the load on the database system.

Implicit connection pooling allows application connections to share pooled
servers in :ref:`DRCP <drcp>` or Oracle Connection Manager in Traffic Director
Mode's (CMAN-TDM) `Proxy Resident Connection Pooling (PRCP)
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-E0032017-03B1-
4F14-AF9B-BCC87C982DA8>`__.  Applications do not need to be modified.  The
feature is enabled by adding a ``pool_boundary`` parameter to the application's
:ref:`connection string <connstr>`.  Applications do not need to explicitly
acquire, or release, connections to be able use a DRCP or PRCP pool.

Implicit connection pooling is available in python-oracledb Thin and
:ref:`Thick <enablingthick>` modes. It requires Oracle Database
version 23. Python-oracledb Thick mode additionally requires Oracle Client
version 23 libraries.

With implicit connection pooling, connections are internally acquired from the
DRCP or PRCP pool when they are actually used by the application to do database
work.  They are internally released back to pool when not in use.  This may
occur between the application's explicit :meth:`oracledb.connect()` call and
:meth:`Connection.close()` (or the application's equivalent connection release
at end-of-scope).  The internal connection release can be controlled by the
value of the ``pool_boundary`` connection string parameter, which can be
either:

- *statement*: If this boundary is specified, then the connection is released
  back to the DRCP or PRCP connection pool when the connection is implicitly
  stateless.  A connection is implicitly stateless when there are no active
  cursors in the connection (that is, all the rows of the cursors have been
  internally fetched), no active transactions, no temporary tables, and no
  temporary LOBs.

- *transaction*: If this boundary is specified, then the connection is released
  back to the DRCP or PRCP connection pool when either one of the methods
  :meth:`Connection.commit()` or :meth:`Connection.rollback()` are
  called. It is recommended to not set the :attr:`Connection.autocommit`
  attribute to *true* when using implicit connection pooling.  If you do set
  this attribute, then you will be unable to:

  - Fetch any data that requires multiple :ref:`round-trips <roundtrips>` to
    the database
  - Run queries that fetch :ref:`LOB <lobdata>` and :ref:`JSON <jsondatatype>`
    data

Inline with DRCP and PRCP best practices regarding session sharing across
differing applications, you should add a connection string
``pool_connection_class`` parameter, using the same value for all applications
that are alike.

The DRCP and PRCP "purity" used by Implicit Connection Pooling defaults to
SELF, which allows reuse of the server process session memory for best
performance. Adding the connection string parameter ``pool_purity=new`` will
change this and cause each use of a connection to recreate the session memory.

.. _useimplicitconnpool:

**Configuring Implicit Connection Pooling**

To use implicit connection pooling in python-oracledb with DRCP:

1. Enable DRCP in the database. For example in SQL*Plus::

       SQL> EXECUTE DBMS_CONNECTION_POOL.START_POOL()

2. Specify to use a pooled server in:

   - The ``dsn`` parameter of :meth:`oracledb.connect()` or
     :meth:`oracledb.create_pool()`. For example with the
     :ref:`Easy Connect syntax <easyconnect>`:

     .. code-block:: python

        cs = "dbhost.example.com/orclpdb:pooled"

        pool = oracledb.create_pool(user="hr", password=userpwd,
                                    dsn=cs,
                                    min=2, max=5, increment=1,
                                    cclass="MYAPP")

   - Or in the :ref:`Connect Descriptor <conndescriptor>` used in an Oracle
     Network configuration file such as :ref:`tnsnames.ora <optnetfiles>` by
     adding ``(SERVER=POOLED)``. For example::

        customerpool = (DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)
              (HOST=dbhost.example.com)
              (PORT=1521))(CONNECT_DATA=(SERVICE_NAME=CUSTOMER)
              (SERVER=POOLED)))

   - Or in the ``server_type`` parameter during
     :meth:`standalone connection creation <oracledb.connect>`
     or :meth:`connection pool creation <oracledb.create_pool>`.  For example:

     .. code-block:: python

        pool = oracledb.create_pool(user="hr", password=userpwd,
                                    host="dbhost.example.com", service_name="orclpdb",
                                    min=2, max=5, increment=1, server_type="pooled",
                                    cclass="MYAPP")

3. Set the pool boundary to either *statement* or *transaction* in:

   - The :ref:`Easy Connect string <easyconnect>`. For example, to use the
     *statement* boundary::

        dsn = "localhost:1521/orclpdb:pooled?pool_boundary=statement"

   - Or the ``CONNECT_DATA`` section of the :ref:`Connect Descriptor
     <conndescriptor>`. For example, to use the *transaction* boundary::

        tnsalias = (DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)(HOST=mymachine.example.com)
                    (PORT=1521))(CONNECT_DATA=(SERVICE_NAME=orcl)
                    (SERVER=POOLED)(POOL_BOUNDARY=TRANSACTION)))

   - Or the ``pool_boundary`` parameter in :meth:`oracledb.connect()` or
     :meth:`oracledb.create_pool()`

   .. note::

        Implicit connection pooling is not enabled if the application sets the
        ``pool_boundary`` attribute to *transaction* or *statement* but does
        not specify to use a pooled server.

4. Set the connection class in:

    - The :ref:`Easy Connect string <easyconnect>`. For example, to use a class
      name 'myapp'::

        dsn = "localhost:1521/orclpdb:pooled?pool_boundary=statement&pool_connection_class=myapp"

    - Or the ``CONNECT_DATA`` section of the :ref:`Connect Descriptor
      <conndescriptor>`. For example, to use a class name 'myapp'::

        tnsalias = (DESCRIPTION=(ADDRESS=(PROTOCOL=tcp)(HOST=mymachine.example.com)
                    (PORT=1521))(CONNECT_DATA=(SERVICE_NAME=orcl)
                    (SERVER=POOLED)(POOL_BOUNDARY=TRANSACTION)
                    (POOL_CONNECTION_CLASS=myapp)))

   Use the same connection class name for application processes of the same
   type where you want session memory to be reused for connections.

   The pool purity can also optionally be changed by adding ``POOL_PURITY=NEW``
   to the Easy Connect string or Connect Descriptor.

Similar steps can be used with PRCP.  For general information on PRCP, see the
technical brief `CMAN-TDM — An Oracle Database connection proxy for scalable
and highly available applications <https://download.oracle.com/
ocomdocs/global/CMAN_TDM_Oracle_DB_Connection_Proxy_for_scalable_apps.pdf>`__.

**Implicit Pooling Notes**

You should thoroughly test your application when using implicit connection
pooling to ensure that the internal reuse of database servers does not cause
any problems. For example, any session state such as the connection `session id
and serial number
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-9F0DCAEA-A67E
-4183-89E7-B1555DC591CE>`__ will vary throughout the lifetime of the
application connection because different servers may be used at different
times. Another example is when using a statement boundary of *transaction*. In
this scenario, any commit can invalidate open cursors.

It is recommended to use python-oracledb's local :ref:`connpooling` where
possible instead of implicit connection pooling.  This gives multi-user
applications more control over pooled server reuse.

Privileged Connections
======================

The ``mode`` parameter of the function :meth:`oracledb.connect()` specifies
the database privilege that you want to associate with the user.

The example below shows how to connect to Oracle Database as SYSDBA:

.. code-block:: python

    connection = oracledb.connect(user="sys", password=syspwd,
                                  dsn="dbhost.example.com/orclpdb",
                                  mode=oracledb.AuthMode.SYSDBA)  # or mode=oracledb.AUTH_MODE_SYSDBA

    with connection.cursor() as cursor:
        cursor.execute("GRANT SYSOPER TO hr")

This is equivalent to executing the following in SQL*Plus:

.. code-block:: sql

    CONNECT sys/syspwd@dbhost.example.com/orclpdb AS SYSDBA
    GRANT SYSOPER TO hr;


In python-oracledb Thick mode, when python-oracledb uses Oracle Client
libraries from a database software installation, you can use "bequeath"
connections to databases that are also using the same Oracle libraries.  Do
this by setting the standard Oracle environment variables such as
``ORACLE_HOME`` and ``ORACLE_SID`` and connecting in Python like:

.. code-block:: python

    oracledb.init_oracle_client()

    conn = oracledb.connect(mode=oracledb.AuthMode.SYSDBA)

This is equivalent to executing the following in SQL*Plus:

.. code-block:: sql

    CONNECT / AS SYSDBA

.. _netencrypt:

Securely Encrypting Network Traffic to Oracle Database
======================================================

You can encrypt data transferred between the Oracle Database and
python-oracledb so that unauthorized parties are not able to view plain text
values as the data passes over the network.

Both python-oracledb Thin and Thick modes support TLS. Refer to the `Oracle
Database Security Guide <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-41040F53-D7A6-48FA-A92A-0C23118BC8A0>`__ for more configuration
information.

.. _nne:

Native Network Encryption
-------------------------

The python-oracledb :ref:`Thick mode <enablingthick>` can additionally use
Oracle Database's `native network encryption <https://www.oracle.com/pls/topic/
lookup?ctx=dblatest&id=GUID-7F12066A-2BA1-476C-809B-BB95A3F727CF>`__.

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

The NETWORK_SERVICE_BANNER column of the database view
`V$SESSION_CONNECT_INFO <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
id=GUID-9F0DCAEA-A67E-4183-89E7-B1555DC591CE>`__ can be used to verify the
encryption status of a connection. For example with SQL*Plus::

    SQL> select network_service_banner from v$session_connect_info;

If the connection is encrypted, then this query prints an output that includes
the available encryption service, the crypto-checksumming service, and the
algorithms in use, such as::

    NETWORK_SERVICE_BANNER
    -------------------------------------------------------------------------------------
    TCP/IP NT Protocol Adapter for Linux: Version 19.0.0.0.0 - Production
    Encryption service for Linux: Version 19.0.1.0.0 - Production
    AES256 Encryption service adapter for Linux: Version 19.0.1.0.0 - Production
    Crypto-checksumming service for Linux: Version 19.0.1.0.0 - Production
    SHA256 Crypto-checksumming service adapter for Linux: Version 19.0.1.0.0 - Production

If the connection is unencrypted, then the query will only print the
available encryption and crypto-checksumming services in the output. For example::

    NETWORK_SERVICE_BANNER
    -------------------------------------------------------------------------------------
    TCP/IP NT Protocol Adapter for Linux: Version 19.0.0.0.0 - Production
    Encryption service for Linux: Version 19.0.1.0.0 - Production
    Crypto-checksumming service for Linux: Version 19.0.1.0.0 - Production

For more information about Oracle Data Network Encryption and Integrity,
and for information about configuring TLS network encryption, refer to
the `Oracle AI Database Security Guide <https://www.oracle.com/pls/topic/
lookup?ctx=dblatest&id=DBSEG>`__.

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
Cloud using one-way TLS (Transport Layer Security) or mutual TLS (mTLS),
depending on how the database instance is configured. One-way TLS and mTLS
provide enhanced security for authentication and encryption.

A database username and password are still required for your application
connections. Refer to the relevant Oracle Cloud documentation, for example see
`Create Database Users <https://www.oracle.com/pls/topic/
lookup?ctx=dblatest&id=GUID-B5846072-995B-4B81-BDCB-AF530BC42847>`__.

.. _onewaytls:

One-way TLS Connection to Oracle Autonomous Database
----------------------------------------------------

With one-way TLS, the python-oracledb host machine must be in the Access
Control List (ACL) of the ADB instance. Applications then connect to Oracle ADB
by passing the database username, password, and appropriate connection
string. A wallet is not used.

Both python-oracledb Thin and Thick modes support one-way TLS.

Allowing One-way TLS Access to Oracle Autonomous Database
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

To create an ADB instance that allows one-way TLS, choose the access setting
*Secure access from allowed IPs and VCNs only* in the Oracle Cloud console
during instance creation. Then specify the IP addresses, hostnames, CIDR
blocks, Virtual Cloud networks (VCN), or Virtual Cloud network OCIDs where
Python will be running. The ACL limits access to only the resources that have
been defined and blocks all other incoming traffic.

Alternatively, to enable one-way TLS on an existing database, complete the
following steps in the Oracle Cloud console in the **Autonomous Database
Information** section of the ADB instance:

1. Click the **Edit** link next to *Access Control List* to update the Access
   Control List (ACL).

2. In the displayed **Edit Access Control List** dialog box, select the type of
   address list entries and the corresponding values. You can include the IP
   addresses, hostnames, CIDR blocks, Virtual Cloud networks (VCN), or Virtual
   Cloud network OCIDs where Python will be running.

3. Navigate back to the ADB instance details page and click the **Edit** link
   next to *Mutual TLS (mTLS) Authentication*.

4. In the displayed **Edit Mutual TLS Authentication** dialog box, deselect the
   **Require mutual TLS (mTLS) authentication** check box to disable the mTLS
   requirement on Oracle ADB and click **Save Changes**.

Connecting with python-oracledb Thin or Thick modes using One-way TLS
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

When your database has been enabled to allow one-way TLS, you can connect with
python-oracledb by following these steps:

1. Navigate to the ADB instance details page on the Cloud console and click
   **Database connection** at the top of the page.

2. In the displayed **Database Connection** dialog box, select TLS from the
   **Connection Strings** drop-down list.

3. Copy the appropriate Connection String for the connection service level you
   want.

Applications can connect using database credentials and the copied
:ref:`connection string <conndescriptor>`. Do *not* pass wallet parameters. For
example, to connect as the ADMIN user:

.. code-block:: python

    cs = '''(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1521)
            (host=adb.abcdef.oraclecloud.com))
            (connect_data=(service_name=abcde_mydb_high.adb.oraclecloud.com))
            (security=(ssl_server_dn_match=yes)))'''

    connection = oracledb.connect(user="admin", password=pw, dsn=cs)


If you prefer to keep connection descriptors out of application code, you can
add the descriptor with a :ref:`TNS Alias <netservice>` to a :ref:`tnsnames.ora
<optnetfiles>` file, and use the TNS alias as the ``dsn`` value.

Not having the ACL correctly configured is a common cause of connection
errors. To aid troubleshooting, remove ``(retry_count=20)(retry_delay=3)`` from
the connect descriptor so that errors are returned faster. If network
configuration issues are suspected then, for initial troubleshooting with a
disposable database, you can update the ACL to contain a CIDR block of
``0.0.0.0/0``, however this means *anybody* can attempt to connect to your
database so you should recreate the database immediately after identifying a
working, more restrictive ACL.

To connect with python-oracledb Thick mode requires Oracle Client library
versions 19.14 (or later), or 21.5 (or later), or 23.3 (or later). If you have
also been experimenting with mTLS and your environment has ``sqlnet.ora`` and
``tnsnames.ora`` files set up, then remove these before using python-oracledb
Thick mode with one-way TLS to avoid configuration clashes.

.. _twowaytls:

Mutual TLS (mTLS) Connection to Oracle Autonomous Database
----------------------------------------------------------

To enable python-oracledb connections to Oracle Autonomous Database in Oracle
Cloud using mTLS, a wallet needs to be downloaded from the cloud console.  mTLS
is sometimes called Two-way TLS.

Allowing mTLS Access to Oracle Autonomous Database
++++++++++++++++++++++++++++++++++++++++++++++++++

When creating an ADB instance in the Oracle Cloud console, choose the access
setting "Secure access from everywhere".

.. _getwallet:

Downloading the Database Wallet
+++++++++++++++++++++++++++++++

After your Autonomous Database has been enabled to allow mTLS, download its
``wallet.zip`` file which contains the certificate and network configuration
files:

1. Navigate to the ADB instance details page on the Oracle Cloud console and
   click **Database connection** at the top of the page.

2. In the displayed **Database Connection** dialog box, select the "Download
   Wallet" button in the *Download client credentials (Wallet)* section. The
   cloud console will ask you to create a wallet password. This password is
   required by python-oracledb in Thin mode, but not used in Thick mode.

**Note**: Keep wallet files in a secure location and only share them and the
password with authorized users.

Connecting with python-oracledb Thin mode using mTLS
++++++++++++++++++++++++++++++++++++++++++++++++++++

For python-oracledb Thin mode, unzip the :ref:`wallet.zip <getwallet>` file.
Only two files from it are needed:

- ``tnsnames.ora`` - Maps TNS Aliases used for application connection strings
  to your database services
- ``ewallet.pem`` - Enables SSL/TLS connections in Thin mode. Keep this file
  secure

If you do not have a PEM file, see :ref:`createpem`.

Move the two files to a directory that is accessible by your application. In
this example, the files are located in the same directory,
``/opt/OracleCloud/MYDB``.

A connection can be made by using your database credentials and setting the
``dsn`` parameter to the desired :ref:`TNS Alias <netservice>` from the
:ref:`tnsnames.ora <optnetfiles>` file. The ``config_dir`` parameter indicates
the directory containing :ref:`tnsnames.ora <optnetfiles>`. The
``wallet_location`` parameter is the directory containing the PEM file. The
``wallet_password`` parameter should be set to the password created in the
cloud console when downloading the wallet. It is not the database user or ADMIN
password. For example, to connect as the ADMIN user using the ``mydb_low`` TNS
Alias:

.. code-block:: python

    connection = oracledb.connect(
        user="admin",
        password=pw,                               # database password for ADMIN
        dsn="mydb_low",                            # TNS Alias from tnsnames.ora
        config_dir="/opt/OracleCloud/MYDB",        # directory with tnsnames.ora
        wallet_location="/opt/OracleCloud/MYDB",   # directory with ewallet.pem
        wallet_password=wp                         # not a database user password
    )

Connecting with python-oracledb Thick mode using mTLS
+++++++++++++++++++++++++++++++++++++++++++++++++++++

For python-oracledb Thick mode, unzip the :ref:`wallet.zip <getwallet>` file.
Only three files from it are needed:

- ``tnsnames.ora`` - Maps :ref:`TNS Aliases <netservice>` used for application
  connection strings to your database services
- ``sqlnet.ora`` - Configures Oracle Network settings
- ``cwallet.sso`` - Enables SSL/TLS connections in python-oracledb Thick mode.
  Keep this file secure

There are two options for placing the required files:

1. Move the three files to the ``network/admin`` directory of the client
   libraries used by your application. For example, if you are using Oracle
   Instant Client version 23 and it is in ``$HOME/instantclient_23_9``, then
   you would put the wallet files in
   ``$HOME/instantclient_23_9/network/admin/``.

   A connection can be made using your database credentials and setting the
   ``dsn`` parameter to the desired :ref:`TNS Alias <netservice>` from the
   :ref:`tnsnames.ora <optnetfiles>` file.  For example, to connect as the ADMIN
   user using the ``mydb_low`` TNS Alias:

   .. code-block:: python

        connection = oracledb.connect(user="admin", password=pw, dsn="mydb_low")

2. Alternatively, move the three files to any accessible directory, for example
   ``/opt/OracleCloud/MYDB``.

   Then edit ``sqlnet.ora`` and change the wallet location directory to the
   directory containing the ``cwallet.sso`` file.  For example::

     WALLET_LOCATION = (SOURCE = (METHOD = file) (METHOD_DATA = (DIRECTORY="/opt/OracleCloud/MYDB")))
     SSL_SERVER_DN_MATCH=yes

   Since the ``tnsnames.ora`` and ``sqlnet.ora`` files are not in the default
   location, your application needs to indicate where they are, either with the
   ``config_dir`` parameter to :meth:`oracledb.init_oracle_client()`, or by
   using the ``TNS_ADMIN`` environment variable.  See :ref:`Optional Oracle Net
   Configuration Files <optnetfiles>`.  (Neither of these settings are needed,
   and you do not need to edit ``sqlnet.ora``, if you have put all the files in
   the ``network/admin`` directory.)

   For example, to connect as the ADMIN user using the ``mydb_low`` TNS
   alias:

   .. code-block:: python

        oracledb.init_oracle_client(config_dir="/opt/OracleCloud/MYDB")

        connection = oracledb.connect(user="admin", password=pw, dsn="mydb_low")


In python-oracle Thick mode, to create mTLS connections in one Python process
to two or more Oracle Autonomous Databases, move each ``cwallet.sso`` file to
its own directory.  For each connection use different connection string
``WALLET_LOCATION`` parameters to specify the directory of each ``cwallet.sso``
file.  It is recommended to use Oracle Client libraries 19.17 (or later) when
using :ref:`multiple wallets <connmultiwallets>`.

If you are behind a firewall, see :ref:`firewallproxy`.

Using the Easy Connect Syntax with Oracle Autonomous Database
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

When python-oracledb is using Oracle Client libraries 19c, or later, you can
optionally use :ref:`Easy Connect <easyconnect>` syntax to connect to Oracle
Autonomous Database.

This section discuss the parameters for mTLS connection.

The mapping from the cloud :ref:`tnsnames.ora <optnetfiles>` entries to an Easy
Connect string is::

    protocol://host:port/service_name?wallet_location=/my/dir&retry_count=N&retry_delay=N

For example, if your ``tnsnames.ora`` file had an entry::

    cjjson_high = (description=(retry_count=20)(retry_delay=3)
        (address=(protocol=tcps)(port=1522)
        (host=xxx.oraclecloud.com))
        (connect_data=(service_name=abc_cjjson_high.adb.oraclecloud.com))
        (security=(ssl_server_cert_dn="CN=xxx.oraclecloud.com,O=Oracle Corporation,L=Redwood City,ST=California,C=US")))

Then your applications can connect using the connection string:

.. code-block:: python

    dsn = "tcps://xxx.oraclecloud.com:1522/abc_cjjson_high.adb.oraclecloud.com?wallet_location=/Users/cjones/Cloud/CJJSON&retry_count=20&retry_delay=3"
    connection = oracledb.connect(user="hr", password=userpwd, dsn=dsn)

The ``wallet_location`` parameter needs to be set to the directory containing
the ``cwallet.sso`` or ``ewallet.pem`` file extracted from the :ref:`wallet.zip
<getwallet>` file. The other files, including ``tnsnames.ora``, are not needed
when you use the Easy Connect syntax.

You can add other Easy Connect parameters to the connection string, for
example::

    dsn = dsn + "&https_proxy=myproxy.example.com&https_proxy_port=80"

With python-oracledb Thin mode, the wallet password needs to be passed as a
connection parameter.

.. _createpem:

Creating a PEM File for python-oracledb Thin Mode
+++++++++++++++++++++++++++++++++++++++++++++++++

For mutual TLS in python-oracledb Thin mode, the certificate must be Privacy
Enhanced Mail (PEM) format. If you are using Oracle Autonomous Database your
wallet zip file will already include a PEM file.

If you have a PKCS12 ``ewallet.p12`` file and need to create PEM file, you can
use third party tools or the script below to do a conversion. For example, you
can invoke the script by passing the wallet password and the directory
containing the PKCS12 file::

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

.. _firewallproxy:

Connecting Through a Firewall via a Proxy
=========================================

If you are behind a firewall, you can tunnel TLS/SSL connections via a proxy by
setting connection attributes, or by making `HTTPS_PROXY <https://www.oracle.
com/pls/topic/lookup?ctx=dblatest&id=GUID-C672E92D-CE32-4759-9931-
92D7960850F7>`__ proxy name and `HTTPS_PROXY_PORT <https://www.oracle.com/pls/
topic/lookup?ctx=dblatest&id=GUID-E69D27B7-2B59-4946-89B3-5DDD491C2D9A>`__
port parameters available in your :ref:`connection string <connstr>`.

.. note::

    Oracle does not recommend connecting through a firewall via a proxy when
    performance is critical.

**In python-oracledb Thin mode**

- Proxy settings ``https_proxy`` and ``https_proxy_port`` can be passed during
  connection or pool creation.  Use appropriate values for your proxy:

  .. code-block:: python

      connection = oracledb.connect(user="admin", password=pw, dsn="mydb_low",
                                    config_dir="/opt/OracleCloud/MYDB",
                                    wallet_location="/opt/OracleCloud/MYDB", wallet_password=wp,
                                    https_proxy="myproxy.example.com", https_proxy_port=80)

- Alternatively, add the parameters to your :ref:`Easy Connect <easyconnect>`
  string::

      localhost/orclpdb&https_proxy=myproxy.example.com&https_proxy_port=80

- Alternatively, update the :ref:`Connect Descriptor <conndescriptor>` (either
  being passed directly during connection or contained in your
  :ref:`tnsnames.ora <optnetfiles>` file). If you are using a
  :ref:`tnsnames.ora <optnetfiles>` file, a modified entry might look like::

      mydb_low = (description=
                   (address=
                     (https_proxy=myproxy.example.com)(https_proxy_port=80)
                     (protocol=tcps)(port=1522)(host= . . . )

**In python-oracledb Thick mode**

- If you are using an :ref:`Easy Connect <easyconnect>` string, add
  ``HTTPS_PROXY`` and ``HTTPS_PROXY_PORT`` parameters with appropriate values for
  your proxy. For example, you might pass parameters like::

      localhost/orclpdb&https_proxy=myproxy.example.com&https_proxy_port=80

- Alternatively, update the :ref:`Connect Descriptor <conndescriptor>` (either
  being passed directly during connection or contained in your
  :ref:`tnsnames.ora <optnetfiles>` file). If you are using a
  :ref:`tnsnames.ora <optnetfiles>` file, a modified entry might look like::

      mydb_low = (description=
                   (address=
                     (https_proxy=myproxy.example.com)(https_proxy_port=80)
                     (protocol=tcps)(port=1522)(host= . . . )

  Additionally create, or edit, a :ref:`sqlnet.ora <optnetfiles>` file and add
  a line::

      SQLNET.USE_HTTPS_PROXY=on

.. _connmultiwallets:

Connecting using Multiple Wallets
=================================

You can make multiple connections with different wallets in one Python
process.

**In python-oracledb Thin mode**

To use multiple wallets in python-oracledb Thin mode, pass the different
connection strings, wallet locations, and wallet password (if required) in each
:meth:`oracledb.connect()` call or when creating a :ref:`connection pool
<connpooling>`:

.. code-block:: python

    connection = oracledb.connect(user=user_name, password=userpw, dsn=dsn,
                                  config_dir="path_to_unzipped_wallet",
                                  wallet_location="location_of_pem_file",
                                  wallet_password=walletpw)

The ``config_dir`` parameter is the directory containing the :ref:`tnsnames.ora
<optnetfiles>` file. The ``wallet_location`` parameter is the directory
containing the ``ewallet.pem`` file. If you are using Oracle Autonomous
Database, both of these paths are typically the same directory where the
:ref:`wallet.zip <getwallet>` file was extracted. The ``dsn`` should specify a
TCPS connection.

**In python-oracledb Thick mode**

To use multiple wallets in python-oracledb Thick mode, a TCPS connection string
containing the ``MY_WALLET_DIRECTORY`` option needs to be created:

.. code-block:: python

    dsn = "mydb_high"   # one of the TNS Aliases from tnsnames.ora
    params = oracledb.ConnectParams(config_dir="path_to_unzipped_wallet",
                                    wallet_location="path_location_of_sso_file")
    params.parse_connect_string(dsn)
    dsn = params.get_connect_string()
    connection = oracledb.connect(user=user_name, password=password, dsn=dsn)

The ``config_dir`` parameter should be the directory containing the
:ref:`tnsnames.ora <optnetfiles>` and ``sqlnet.ora`` files. The
``wallet_location`` parameter is the directory containing the ``cwallet.sso``
file. If you are using Oracle Autonomous Database, both of these paths are
typically the same directory where the :ref:`wallet.zip <getwallet>` file was
extracted.

.. note::

       Use Oracle Client libraries 19.17, or later, or use Oracle Client
       version 21 or 23. These contain important bug fixes for using multiple
       wallets in the one process.

.. _connsharding:

Connecting to Oracle Globally Distributed Database
==================================================

`Oracle Globally Distributed Database
<https://www.oracle.com/database/distributed-database/>`__ is a feature of
Oracle Database that lets you automatically distribute and replicate data
across a pool of Oracle databases that share no hardware or software.  It was
previously known as Oracle Sharding.  It allows a database table to be split so
each database contains a table with the same columns but a different subset of
rows.  These tables are known as sharded tables.  From the perspective of an
application, a sharded table in Oracle Globally Distributed AI Database looks
like a single table: the distribution of data across those shards is completely
transparent to the application.

Sharding is configured in Oracle Database, see the `Oracle Globally Distributed
AI Database <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=SHARD>`__
manual.  It requires Oracle Database and Oracle Client libraries 12.2, or
later.

.. note::

    Oracle Globally Distributed Database is only supported in python-oracledb
    Thick mode.  See :ref:`enablingthick`.

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
