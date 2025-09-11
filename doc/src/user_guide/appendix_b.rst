.. _driverdiff:

.. currentmodule:: oracledb

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
    :func:`oracledb.connect()` and :func:`oracledb.create_pool()` are keyword
    and not positional. This makes the python-oracledb driver compliant with
    the Python Database API specification PEP 249.  The old positional usage
    possible in the obsolete cx_Oracle driver will cause an error, see
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

In python-oracledb Thin mode:

- The location of any ``tnsnames.ora`` files must explicitly be passed to the
  application.

- Any ``sqlnet.ora`` file will not be read.  Instead, pass an equivalent
  setting when connecting.

- There is no support for ``oraaccess.xml`` since there are no Oracle Client
  libraries.


See :ref:`optnetfiles` and :ref:`optclientfiles` for more information.

Token Based Authentication
--------------------------

In python-oracledb Thin mode:

- When connecting to Oracle Cloud Database with mutual TLS (mTLS) using OAuth2
  tokens, you need to explicitly set the ``config_dir``, ``wallet_location``,
  and ``wallet_password`` parameters of :func:`~oracledb.connect` or
  :func:`~oracledb.create_pool()`. See, :ref:`autonomousdb`.

- :ref:`Open Authorization (OAuth 2.0) token based authentication connection
  strings <oauth2connstr>` and :ref:`Oracle Cloud Infrastructure (OCI) Identity
  and Access Management (IAM) token based authentication connection strings
  <iamauthconnstr>` are not supported. Use the ``access_token`` parameter of
  :func:`oracledb.ConnectParams()` instead. See :ref:`tokenauth`.

Transport Layer Security (TLS) Support
--------------------------------------

When connecting with mutual TLS (mTLS) also known as two-way TLS, for example to
Oracle Autonomous Database in Oracle Cloud using a wallet, the certificate must
be in the correct format.

For python-oracledb Thin mode, the certificate must be in a Privacy Enhanced
Mail (PEM) ``ewallet.pem`` file.  In python-oracledb Thick mode the certificate
must be in a ``cwallet.sso`` file.  See :ref:`autonomousdb` for more
information.

Native Network Encryption and Checksumming
------------------------------------------

The python-oracledb Thin mode does not support connections using Oracle
Database Native Network Encryption (NNE) or checksumming. You can `enable TLS
<https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-8B82DD7E-7189-
4FE9-8F3B-4E521706E1E4>`__ instead of using native network encryption. If
native network encryption or checksumming are required, then use
python-oracledb in Thick mode. See :ref:`enablingthick`.

For example, if you use python-oracledb Thin mode and try to connect to an
Oracle Cloud Infrastructure (OCI) Oracle Base Database (where Native Network
Encryption is set to *REQUIRED* by default in the database ``sqlnet.ora``
file), the connection will fail with an error like::

  DPY-3001: Native Network Encryption and Data Integrity is only
  supported in python-oracledb thick mode

or::

  DPY-4011: the database or network closed the connection

or::

  DPY-6000: cannot connect to database. Listener refused connection.
  (Similar to ORA-12660)

See :ref:`Troubleshooting DPY-3001 <dpy3001>` for more information.

Connection Pooling Differences between Thin and Thick Modes
===========================================================

Python-oracledb introduced the :ref:`ConnectionPool Object <connpool>` class to
replace ``SessionPool``.  A new :func:`oracledb.create_pool()` method is now
the recommended way to create a connection pool.  The use of the equivalent
``SessionPool()`` constructor is :ref:`deprecated <deprecations>`.

The :func:`~oracledb.create_pool()` method in python-oracledb Thin mode differs
from python-oracledb Thick mode in the following ways:

* Not all the parameters of the :func:`oracledb.create_pool()` method are
  applicable to both python-oracledb modes.  Each mode ignores unrecognized
  parameters.  The parameters that are ignored in Thin mode include ``events``,
  ``tag``, ``matchanytag``, ``shardingkey``, ``supershardingkey``, and
  ``handle`` parameters.  The parameters that are ignored in Thick mode include
  ``wallet_password``, ``disable_oob``, and ``debug_jdwp`` parameters.

* The python-oracledb Thin mode only supports :ref:`homogeneous
  <connpooltypes>` pools.

* The python-oracledb Thin mode creates connections in a daemon thread and so
  :func:`oracledb.create_pool()` returns before any or all minimum number of
  connections are created. As soon as the pool is created, the
  :attr:`ConnectionPool.opened` attribute will not be equal to
  :attr:`ConnectionPool.min`. The :attr:`~ConnectionPool.opened` attribute will
  increase to the minimum value over a short time as the connections are
  established. Note that this behavior may also be true of recent versions of
  the Oracle Call Interface (OCI) Session Pool used in the Thin mode.

  If the new ``getmode`` default value of :data:`~oracledb.POOL_GETMODE_WAIT`
  is used, then this behavior will not be an issue. With this new default
  value, any immediate :meth:`ConnectionPool.acquire()` calls will wait for the
  connections to be created by the daemon thread. This improves application
  start up time when compared to python-oracledb Thick mode, where
  :func:`oracledb.create_pool()` will not return control to the application
  until all ``pool.min`` connections have been created.

  If the old default value ``POOL_GETMODE_NOWAIT`` is required, then the
  application could check if :attr:`ConnectionPool.opened` has reached
  :attr:`ConnectionPool.min` and then continue with application start up.

* In python-oracledb Thick mode, when you close a connection pool with the
  parameter ``force=True``, the underlying Oracle Client libraries wait for the
  current SQL executions to complete before closing the connections. All of the
  connections are then dropped from the pool and the pool is closed. Closing
  the pool in python-oracledb Thick mode could stop responding indefinitely,
  depending on the network and Oracle Net Services timeout parameters. In
  python-oracledb Thin mode, the parameter ``force=True`` disconnects each
  connection's socket using a background thread, leaving the database to clean
  up its end of the connections.

* In python-oracledb Thin mode, the ``cclass`` parameter value is not used to
  tag connections in the application connection pool. It is only used for
  :ref:`drcp`.

* In python-oracledb Thin mode, the connection pool supports all the
  :ref:`connection mode privileges <connection-authorization-modes>`.

* In python-oracledb Thick mode, when the ``thick_mode_dsn_passthrough`` value
  in effect is *True*, the ``pool_name`` parameter can be used to specify a
  DRCP pool name only if the ``dsn`` parameter is not set. If both of these
  parameters are specified, then the ``pool_name`` parameter is ignored. In
  python-oracledb Thin mode, both of these parameters can be set and the value
  defined in the ``pool_name`` parameter will be used as the DRCP pool name.

Supported Database Data Types in Thin and Thick Modes
=====================================================

The python-oracledb Thin and Thick mode support for the UROWID, REF, and
XMLType database data types has some small differences. See
:ref:`supporteddbtypes`.

.. _querymetadatadiff:

Query Metadata in Thin and Thick Modes
======================================

In python-oracledb Thin mode, :data:`Cursor.description` metadata can
distinguish the ROWID and UROWID database types. The UROWID database type shows
the new value ``DB_TYPE_UROWID`` and the database type ROWID uses the existing
value ``DB_TYPE_ROWID``.

In python-oracledb Thick mode, the value ``DB_TYPE_ROWID`` is shown for both
ROWID and UROWID database types. In python-oracledb Thick and Thin modes,
comparison with the type ``oracledb.ROWID`` (defined in the Python DB API) will
match both ROWID and UROWID database types.

.. _implicitresultsdiff:

Implicit Results in Thin and Thick Modes
========================================

In python-oracledb Thick mode, the parent cursor that is used to get the
:ref:`implicit results <implicitresults>` must remain open until all of the
implicit result sets have been fetched or until the application no longer
requires them. Closing the parent cursor before all the implicit result sets
have been fetched will result in the automatic closure of the implicit result
set cursors.

In python-oracledb Thin mode, there is no requirement to leave the parent
cursor open when fetching implicit result sets. The parent cursor and implicit
cursors are independently handled in Thin mode.

.. _stmtcaching:

Statement Caching in Thin and Thick Modes
=========================================

The :ref:`statement cache <stmtcache>` implemented in python-oracledb Thin mode
is capable of determining when different database data types are used for the
same bind variables when a statement is re-executed.  This capability is not
supported in the Oracle Client libraries that are used in python-oracledb Thick
mode. Note changing the type of bind variables for the same SQL text is
inappropriate and gives indeterminate results in both modes.

Duplicate SQL Bind Variable Placeholders in Thin and Thick Modes
================================================================

To use python-oracledb Thin mode when you have duplicate bind variable
placeholder names in a SQL statement and are :ref:`binding by position
<bindbyposition>`, then supply a value for each use of the placeholders, see
:ref:`dupbindplaceholders`.

This does not apply to PL/SQL blocks.

Error Handling in Thin and Thick Modes
======================================

Python-oracledb Thin and Thick modes handle some errors differently. See
:ref:`errorhandling`.

Globalization in Thin and Thick Modes
=====================================

All NLS environment variables, and the ``ORA_TZFILE`` environment variable, are
ignored by python-oracledb Thin mode.  Use Python's capabilities instead.

Python-oracledb Thin mode can only use NCHAR, NVARCHAR2, and NCLOB data when
Oracle Database's secondary character set is AL16UTF16.

See :ref:`globalization`.

Tracing in Thin and Thick Modes
===============================

In python-oracledb Thin mode, low level tracing is different because there are
no Oracle Client libraries. See :ref:`tracingsql`.
