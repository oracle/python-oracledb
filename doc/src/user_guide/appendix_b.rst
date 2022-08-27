.. _driverdiff:

********************************************************************
Appendix B: Differences between python-oracledb Thin and Thick Modes
********************************************************************

By default, python-oracledb runs in a 'Thin' mode which connects directly to
Oracle Database.  This mode does not need Oracle Client libraries.  However,
some :ref:`additional functionality <featuresummary>` is available when
python-oracledb uses them.  Python-oracledb is said to be in 'Thick' mode when
Oracle Client libraries are used.  See :ref:`enablingthick`.  Both modes have
comprehensive functionality supporting the Python Database API v2.0
Specification.

This section details the differences between the python-oracledb Thin and Thick
modes.  Also see the summary feature comparison table in :ref:`featuresummary`.

Connection Handling Differences between Thin and Thick Modes
============================================================

Python-oracledb can create connections in either a Thin mode or a Thick
mode. However, only one of these modes can be used in each Python process:

- By default, python-oracledb runs in a Thin mode which connects directly to
  Oracle Database.

- If :func:`oracledb.init_oracle_client()` loads Oracle Client libraries before
  any standalone connection or pool is created, then the python-oracledb mode
  becomes Thick.  The client libraries handle communication with Oracle
  Database. See :ref:`enablingthick`.

- If an application opens a connection or creates a pool and then calls
  :func:`oracledb.init_oracle_client()`, an error will occur.

- Once a connection or pool has been opened, or
  :func:`~oracledb.init_oracle_client()` has been called, you cannot change the
  mode.

.. note::

    The parameters of connection and pool creation functions
    :func:`oracledb.connect()` and :func:`oracledb.create_pool()` are now
    keyword and not positional in both Thin and Thick modes. This change makes
    the python-oracledb driver compliant with the Python Database API
    specification PEP 249.  The old usage will cause an error, see
    :ref:`connerrors`.

Connections to a Local Database
-------------------------------

In Thin mode, there is no concept of a local database.  Bequeath connections
cannot be made since no Oracle Client libraries are used.  The Thin mode does
not de-reference environment variables such as ``ORACLE_SID``, ``TWO_TASK``, or
``LOCAL`` (the latter is specific to Windows).  A connection string, or
equivalent, must always be used.

.. _sqlnetclientconfig:

Oracle Net Services and Client Configuration Files
--------------------------------------------------

In the python-oracledb Thin mode:

- The location of any ``tnsnames.ora`` files must explicitly be passed to the
  application.

- Any ``sqlnet.ora`` file will not be read.  Instead, pass an equivalent
  setting when connecting.

- There is no support for ``oraaccess.xml`` since there are no Oracle Client
  libraries.


See :ref:`optnetfiles` and :ref:`optclientfiles` for more information.

.. _diffconnstr:

Connection Strings
------------------

The python-oracledb Thin mode accepts connection strings in the same formats as
the Oracle Client libraries used by Thick mode does, but not all Oracle Net
keywords will be supported.

The following table lists the parameters that are recognized in Thin mode
either in Easy Connect Strings or in Full Connect Descriptor Strings that are
either explicitly passed or referred to by a ``tnsnames.ora`` alias.  All
unrecognized parameters are ignored.  The connection parameters shown can be
used in :meth:`oracledb.connect()`, :meth:`oracledb.create_pool()`,
:meth:`oracledb.ConnectParams()`, and :meth:`oracledb.PoolParams()`.

.. list-table-with-summary::  Oracle Net Keywords Supported in the python-oracledb Thin Mode
    :header-rows: 1
    :class: wy-table-responsive
    :align: center
    :summary: The first column displays the keyword. The second column displays the equivalent oracledb.connect(), oracledb.create_pool(), oracledb.ConnectParams(), or oracledb.PoolParams() parameters. The third column displays the notes.

    * - Oracle Net Keyword
      - Equivalent Connection Parameter
      - Notes
    * - SSL_SERVER_CERT_DN
      - ssl_server_cert_dn
      - If specified, this value is used for any verification.  Otherwise, the hostname will be used.
    * - SSL_SERVER_DN_MATCH
      - ssl_server_dn_match
      - In Thin mode parsing the parameter supports case insensitive on/yes/true values similar to the Thick mode. Any other value is treated as disabling it.
    * - WALLET_LOCATION
      - wallet_location
      - Used in Easy Connect Strings. It is same as ``MY_WALLET_DIRECTORY`` in a connect descriptor.
    * - MY_WALLET_DIRECTORY
      - wallet_location
      -
    * - EXPIRE_TIME
      - expire_time
      -
    * - HTTPS_PROXY
      - https_proxy
      -
    * - HTTPS_PROXY_PORT
      - https_proxy_port
      -
    * - RETRY_COUNT
      - retry_count
      -
    * - RETRY_DELAY
      - retry_delay
      -
    * - TRANSPORT_CONNECT_TIMEOUT
      - tcp_connect_timeout
      -
    * - POOL_CONNECTION_CLASS
      - cclass
      -
    * - POOL_PURITY
      - purity
      -
    * - SERVICE_NAME
      - service_name
      -
    * - SID
      - sid
      -
    * - PORT
      - port
      -
    * - PROTOCOL
      - protocol
      -

In python-oracledb Thin mode, using the ``POOL_CONNECTION_CLASS`` or
``POOL_PURITY`` parameters in a connection string is similar to setting the
equivalent attributes when creating a connection or connection pool.

In python-oracledb Thick mode, the ``POOL_CONNECTION_CLASS`` or ``POOL_PURITY``
values will only work when connected to Oracle Database 21c. Note if
``POOL_PURITY=SELF`` is used in a connect string, then python-oracledb Thick
mode applications will ignore the action to drop the session when attempting to
remove an unusable connections from a pool in some uncommon error cases.  It is
recommended to avoid using ``POOL_PURITY=SELF`` in a connect string with
python-oracledb Thick mode. Instead, code the python-oracledb Thick mode
application to explicitly specify the purity and connection class as
attributes.

The ``ENABLE=BROKEN`` connect descriptor option is not supported in
python-oracledb Thin mode.  Use ``expire_time`` instead.

The ``Session Data Unit (SDU)`` connect descriptor option that is used to tune
network transfers is not supported in python-oracledb Thin mode. The value is
hard-coded as 8 KB.  In python-oracledb Thick mode, the SDU connect descriptor
option and equivalent ``sqlnet.ora`` setting are used.

If a name is given as a connect string, then the python-oracledb Thin mode will
consider it as a Net Service Name and not as the minimal Easy Connect string of
a hostname.  The given connect string will be looked up in a ``tnsnames.ora``
file.  This is different from the python-oracledb Thick mode. If supporting a
bare name as a hostname is important to you in the python-oracledb Thin mode,
then you can alter the connection string to include a port number such as
``hostname:1521`` or a protocol such as ``tcp://hostname``.

Token Based Authentication
--------------------------

In the python-oracledb Thin mode:

- When connecting to Oracle Cloud Database with mutual TLS (mTLS) using OAuth2
  tokens, you need to explicitly set the ``config_dir``, ``wallet_location``,
  and ``wallet_password`` parameters of :func:`~oracledb.connect` or
  :func:`~oracledb.create_pool()`. See, :ref:`autonomousdb`.

- :ref:`Open Authorization (OAuth 2.0) token based authentication connection
  strings <oauth2connstr>` and :ref:`Oracle Cloud Infrastructure (OCI) Identity
  and Access Management (IAM) token based authentication connection strings
  <iamauthconnstr>` are not supported. Use ``access_token`` parameter of
  :func:`oracledb.ConnectParams()` instead. See :ref:`tokenauth`.

Transport Layer Security (TLS) Support
--------------------------------------

When connecting with mutual TLS (mTLS) also known as two-way TLS, for example to
Oracle Autonomous Database in Oracle Cloud using a wallet, the certificate must
be in the correct format.

For the python-oracledb Thin mode, the certificate must be in a Privacy
Enhanced Mail (PEM) ``ewallet.pem`` file.  In python-oracledb Thick mode the
certificate must be in a ``cwallet.sso`` file.  See :ref:`autonomousdb` for
more information.

Native Network Encryption and Checksumming
------------------------------------------

The python-oracledb Thin mode does not support connections using Oracle
Database native network encryption or checksumming. You can enable
TLS instead of using native network encryption. If native network encryption
or checksumming are required, then use python-oracledb in the Thick mode.
See :ref:`enablingthick`.

For example, if you use python-oracledb Thin mode and try to connect to the
Oracle Cloud Infrastructure (OCI) Oracle Base Database where by default native
network encryption is set to REQUIRED in the ``sqlnet.ora`` file of the OCI
Oracle Base Database server, the connection will fail with the error::

  DPY-6000: cannot connect to database. Listener refused connection.
  (Similar to ORA-12660)

Connection Pooling Differences between Thin and Thick Modes
===========================================================

Python-oracledb introduced the :ref:`ConnectionPool Object <connpool>` class to
replace ``SessionPool``.  A new :func:`oracledb.create_pool()` method is now
the recommended way to create a connection pool.  The use of the equivalent
``SessionPool()`` constructor is :ref:`deprecated <deprecations>`.

The :func:`~oracledb.create_pool()` method in the python-oracledb Thin mode
differs from the python-oracledb Thick mode in the following ways:

* Not all the parameters of the :func:`oracledb.create_pool()` method are applicable
  to both python-oracledb modes.  Each mode ignores unrecognized parameters.
  The parameters that are ignored in Thin mode include ``events``, ``tag``,
  ``matchanytag``, ``appcontext``, ``shardingkey``, ``supershardingkey``, and
  ``handle`` parameters.  The parameters that are ignored in the Thick mode include
  ``wallet_password``, ``disable_oob``, ``config_dir``, and ``debug_jdwp`` parameters.

* The python-oracledb Thin mode only suppports :ref:`homogeneous
  <connpooltypes>` pools.

* The python-oracledb Thin mode creates connections in a daemon thread and so
  :func:`oracledb.create_pool()` returns before any or all minimum number of
  connections are created. As soon as the pool is created, the
  :attr:`ConnectionPool.opened` attribute will not be equal to
  :attr:`ConnectionPool.min`. The :attr:`~ConnectionPool.opened` attribute will
  increase to the minimum value over a short time as the connections are
  established. Note that this behavior may also be true of recent versions of
  the Oracle Call Interface (OCI) Session Pool used in the Thin mode.

  If the new ``getmode`` default value of :data:`~oracledb.POOL_GETMODE_WAIT` is
  used, then this behavior will not be an issue. With this new default value, any
  immediate :meth:`ConnectionPool.acquire()` calls will wait for the connections
  to be created by the daemon thread. This improves the application start up time
  when compared to the python-oracledb Thick mode and cx_Oracle 8.3 driver, where
  :func:`oracledb.create_pool()` will not return control to the application until
  all ``pool.min`` connections have been created.

  If the old default value ``POOL_GETMODE_NOWAIT`` is required, then the application
  could check if :attr:`ConnectionPool.opened` has reached :attr:`ConnectionPool.min`
  and then continue with application start up.

* In python-oracledb Thick mode, when you close a connection pool with the
  parameter ``force=True``, the underlying Oracle Client libraries wait for the
  current SQL executions to complete before closing the connections. All of the
  connections are then dropped from the pool and the pool is closed. Closing
  the pool in python-oracledb Thick mode could stop responding indefinitely,
  depending on the network and Oracle Net Services timeout parameters. This is
  also applicable to the cx_Oracle 8.3 driver. In python-oracledb Thin mode,
  the parameter ``force=True`` disconnects each connection's socket using a
  background thread, leaving the database to clean up its end of the
  connections.

* In python-oracledb Thin mode, the ``cclass`` parameter value is not used to
  tag connections in the application connection pool. It is only used for :ref:`drcp`.

* In python-oracledb Thin mode, the connection pool supports all the :ref:`connection
  mode privileges <connection-authorization-modes>`.

  The python-oracledb Thick mode only supports the :data:`~oracledb.AUTH_MODE_SYSDBA`
  privilege.

Supported Database Data Types in Thin and Thick Modes
=====================================================

The python-oracledb Thin and Thick modes support different Oracle database data
types.  See :ref:`supporteddbtypes`.

.. _querymetadatadiff:

Query Metadata in Thin and Thick Modes
======================================

In python-oracledb Thin mode, :data:`Cursor.description` metadata can distinguish
the ROWID and UROWID database types. The UROWID database type shows the new value
``DB_TYPE_UROWID`` and the database type ROWID uses the existing value
``DB_TYPE_ROWID``.

In python-oracledb Thick mode, the value ``DB_TYPE_ROWID`` is shown for both ROWID
and UROWID database types. In python-oracledb Thick and Thin modes, comparison with
the type ``oracledb.ROWID`` (defined in the Python DB API) will match both ROWID and
UROWID database types.

.. _stmtcaching:

Statement Caching in Thin and Thick Modes
=========================================

The :ref:`statement cache <stmtcache>` implemented in the python-oracledb Thin
mode is capable of determining when different database data types are used for
the same bind variables when a statement is re-executed.  This capability is
not supported in the Oracle Client libraries that are used in python-oracledb
Thick mode. Note changing the type of bind variables for the same SQL text is
inappropriate and gives indeterminate results in both modes.

.. _fetchJSON:

Fetching JSON in Thin and Thick Modes
=====================================

The python-oracledb Thin mode does not natively handle the Oracle Database 21c
JSON data type but a type handler can be used when fetching the type, see
:ref:`jsondatatype`.

Error Handling in Thin and Thick Modes
======================================

The python-oracledb Thin and Thick modes handle some errors differently. See
:ref:`errorhandling`.

Globalization in Thin and Thick Modes
=====================================

All NLS environment variables, and the ``ORA_SDTZ`` and ``ORA_TZFILE``
environment variables, are ignored by the python-oracledb Thin mode.  Use
Python's capabilities instead.

The python-oracledb Thin mode can only use NCHAR, NVARCHAR2, and NCLOB data
when Oracle Database's secondary character set is AL16UTF16.

See :ref:`globalization`.

Tracing in Thin and Thick Modes
===============================

In the python-oracledb Thin mode, low level tracing is different because there
are no Oracle Client libraries.  See :ref:`tracingsql`.
