.. _featuresummary:

*****************************************************************
Appendix A: Oracle Database Features Supported by python-oracledb
*****************************************************************

By default, python-oracledb runs in a 'Thin' mode which connects directly to
Oracle Database.  This mode does not need Oracle Client libraries.  However,
some additional functionality is available when python-oracledb uses them.
Python-oracledb is said to be in 'Thick' mode when Oracle Client libraries are
used.  Both modes have comprehensive functionality supporting the Python
Database API v2.0 Specification `PEP 249
<https://peps.python.org/pep-0249/>`__.  See :ref:`initialization` for how to
enable Thick mode.

The following table summarizes the Oracle Database features supported by
python-oracledb Thin and Thick modes, and by the obsolete cx_Oracle driver.
For more details see :ref:`driverdiff` and :ref:`compatibility`.

.. list-table-with-summary::  Features Supported by python-oracledb and cx_Oracle 8.3
    :header-rows: 1
    :class: wy-table-responsive
    :align: center
    :summary: The first column displays the Oracle feature. The second column indicates whether the feature is supported in python-oracledb Thin mode. The third column indicates whether the feature is supported in python-oracledb Thick mode. The fourth column indicates if the feature is supported in the obsolete cx_Oracle driver.

    * - Oracle Feature
      - python-oracledb Thin Mode
      - python-oracledb Thick Mode
      - cx_Oracle 8.3
    * - Oracle Client version
      - Not applicable
      - Release 11.2 and later
      - Release 11.2 and later
    * - Oracle Database version
      - Release 12.1 and later
      - Release 9.2 and later depending on Oracle Client library version
      - Release 9.2 and later depending on Oracle Client library version
    * - Standalone connections (see :ref:`standaloneconnection`)
      - Yes - must use keyword arguments
      - Yes - must use keyword arguments
      - Yes
    * - Connection Pooling - Heterogeneous and Homogeneous (see :ref:`Connection pooling <connpooling>`)
      - Homogeneous only - must use keyword arguments
      - Yes - must use keyword arguments
      - Yes
    * - Named Connection Pools (see :ref:`connpoolcache`)
      - Yes
      - Yes
      - No
    * - Connection Pool Connection Load Balancing (CLB) (see `Client-Side Load Balancing <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-10F7892A-92DD-482C-8D68-AE80CE956010>`__)
      - Yes
      - Yes
      - Yes
    * - Connection Pool Runtime Load Balancing (RLB) (see `Runtime Connection Load Balancing <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-A8B79A40-C4AA-4FBA-8042-C70C8FD2D2EF>`__)
      - No
      - Yes
      - Yes
    * - Connection Pool draining (see `Prepare Applications for Planned Maintenance <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-9121F9FF-88E5-4DA2-9874-23A185CB2F82>`__)
      - Yes
      - Yes
      - Yes
    * - Connection Pool session state callback (see :ref:`sessioncallback`)
      - Yes - Python functions but not PL/SQL functions
      - Yes
      - Yes
    * - Connection pool session tagging (see :ref:`conntagging`)
      - No
      - Yes
      - Yes
    * - Password authentication
      - Yes
      - Yes
      - Yes
    * - External authentication (see :ref:`extauth`)
      - No
      - Yes
      - Yes
    * - Oracle Cloud Infrastructure (OCI) Identity and Access Management (IAM) Tokens (see :ref:`iamauth`)
      - Yes
      - Yes
      - Yes - in connection string with appropriate Oracle Client
    * - Open Authorization (OAuth 2.0) (see :ref:`oauth2`)
      - Yes
      - Yes
      - Yes - in connection string with appropriate Oracle Client
    * - Kerberos and Radius authentication
      - No
      - Yes
      - Yes
    * - Lightweight Directory Access Protocol (LDAP) connections (see :ref:`ldapconnections`)
      - Yes - via a user function enabled with :meth:`oracledb.register_protocol()`
      - Yes
      - Yes
    * - Proxy connections (see :ref:`proxyauth`)
      - Yes
      - Yes
      - Yes
    * - Socket Secure (SOCKS) Proxy connections
      - No
      - No
      - No
    * - Connection mode privileges (see :ref:`connection-authorization-modes`)
      - Yes
      - Yes - only :data:`~oracledb.AUTH_MODE_SYSDBA` is supported
      - Yes - only :data:`~oracledb.AUTH_MODE_SYSDBA` is supported
    * - Preliminary connections
      - No
      - Yes
      - Yes
    * - Set the current schema using an attribute
      - Yes
      - Yes
      - Yes
    * - Oracle Cloud Database connectivity (see :ref:`autonomousdb`)
      - Yes
      - Yes
      - Yes
    * - Real Application Clusters (RAC)
      - Yes
      - Yes
      - Yes
    * - Oracle Globally Distributed Database - previously known as Oracle Sharded Databases (see :ref:`connsharding`)
      - No
      - Yes - No TIMESTAMP support
      - Yes - No TIMESTAMP support
    * - Oracle Database Native Network Encryption (NNE) (see :ref:`nne`)
      - No - use `TLS <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-8B82DD7E-7189-4FE9-8F3B-4E521706E1E4>`__ instead
      - Yes
      - Yes
    * - Connection health check APIs (see :meth:`~Connection.is_healthy()` and :meth:`~Connection.ping()`)
      - Yes
      - Yes
      - Yes
    * - Oracle Net Services ``tnsnames.ora`` file (see :ref:`optnetfiles`)
      - Yes
      - Yes
      - Yes
    * - Oracle Net Services ``sqlnet.ora`` file (see :ref:`optnetfiles`)
      - No - many values can be set at connection time
      - Yes
      - Yes
    * - Oracle Client library configuration file ``oraaccess.xml`` (see :ref:`optclientfiles`)
      - Not applicable
      - Yes
      - Yes
    * - Easy Connect connection strings (see :ref:`easyconnect`)
      - Yes - mostly supported. Unknown settings are ignored and not passed to Oracle Database.
      - Yes
      - Yes
    * - Centralized Configuration Providers (see :ref:`configurationproviders`)
      - Yes
      - Yes
      - No
    * - One-way TLS connections (see :ref:`onewaytls`)
      - Yes
      - Yes
      - Yes
    * - Mutual TLS (mTLS) connections (see :ref:`twowaytls`)
      - Yes
      - Yes
      - Yes
    * - Secure External Password Store (SEPS) wallet (e.g. wallets created by mkstore)
      - No
      - Yes
      - Yes
    * - Oracle Database Dedicated Servers, Shared Servers and :ref:`drcp`.
      - Yes
      - Yes
      - Yes
    * - Oracle Database 23ai Implicit Connection Pooling with :ref:`DRCP <drcp>` and PRCP (see :ref:`implicitconnpool`)
      - Yes
      - Yes
      - No
    * - Multitenant Databases
      - Yes
      - Yes
      - Yes
    * - CMAN and CMAN-TDM connectivity
      - Yes
      - Yes
      - Yes
    * - Password changing (see :meth:`Connection.changepassword()`)
      - Yes
      - Yes
      - Yes
    * - Statement break/reset (see :meth:`Connection.cancel()`)
      - Yes
      - Yes
      - Yes
    * - Edition Based Redefinition (EBR) (see :ref:`ebr`)
      - Yes
      - Yes
      - Yes
    * - SQL execution (see :ref:`sqlexecution`)
      - Yes
      - Yes
      - Yes
    * - PL/SQL execution (see :ref:`plsqlexecution`)
      - Yes for scalar types. Yes for collection types using array interface.
      - Yes
      - Yes
    * - Simple Oracle Document Access (SODA) API (see :ref:`SODA <soda>`)
      - No
      - Yes
      - Yes
    * - Bind variables for data binding (see :ref:`bind`)
      - Yes
      - Yes
      - Yes
    * - Array DML binding for bulk DML and PL/SQL (see :ref:`batchstmnt`)
      - Yes
      - Yes
      - Yes
    * - SQL and PL/SQL type and collections (see :ref:`fetchobjects`)
      - Yes
      - Yes
      - Yes
    * - Query column metadata (see :ref:`querymetadata`)
      - Yes
      - Yes
      - Yes
    * - Client character set support (see :ref:`globalization`)
      - UTF-8
      - UTF-8
      - Yes - can use Python encodings. Default in 8.0 is UTF-8
    * - Globalization support (see :ref:`globalization`)
      - Yes - via Python globalization support
      - Yes - Oracle Database NLS environment variables are respected, excluding the character set in NLS_LANG
      - Yes - Oracle Database NLS environment variables are respected, excluding the character set in NLS_LANG
    * - Row prefetching on first query execute (see :ref:`tuningfetch`)
      - Yes - unless the row contains LOBs or similar types
      - Yes - unless the row contains LOBs or similar types
      - Yes - unless the row contains LOBs or similar types
    * - Array fetching for queries (see :ref:`tuningfetch`)
      - Yes
      - Yes
      - Yes
    * - Statement caching (see :ref:`stmtcache`)
      - Yes - new driver also supports dropping from the cache
      - Yes - new driver also supports dropping from the cache
      - Yes
    * - Client Result Caching (CRC) (see :ref:`clientresultcache`)
      - No
      - Yes
      - Yes
    * - Oracle Database 23ai JSON-Relational Duality Views (see :ref:`jsondualityviews`)
      - Yes
      - Yes
      - No
    * - Continuous Query Notification (CQN) (see :ref:`cqn`)
      - No
      - Yes
      - Yes
    * - Oracle Transactional Event Queues and Advanced Queuing (AQ) (see :ref:`aqusermanual`)
      - Yes - only "Classic" queues are supported (RAW, named Oracle object, and JSON payloads)
      - Yes
      - Yes
    * - Call timeouts (see :attr:`Connection.call_timeout`)
      - Yes
      - Yes
      - Yes
    * - Scrollable cursors (see :ref:`scrollablecursors`)
      - Yes
      - Yes
      - Yes
    * - Oracle Database startup and shutdown (see :ref:`startup`)
      - No
      - Yes
      - Yes
    * - Transaction management (see :ref:`txnmgmnt`)
      - Yes
      - Yes
      - Yes
    * - Events mode for notifications
      - No
      - Yes
      - Yes
    * - Fast Application Notification (FAN) (see :ref:`fan`)
      - No
      - Yes
      - Yes
    * - In-band notifications
      - Yes
      - Yes
      - Yes
    * - Transparent Application Failover (TAF)
      - No
      - Yes - no callback
      - Yes - no callback
    * - Transaction Guard (TG) (see :ref:`tg`)
      - Yes
      - Yes
      - Yes
    * - Data Guard (DG) and Active Data Guard (ADG)
      - Yes
      - Yes
      - Yes
    * - Application Continuity (AC) and Transparent Application Continuity (TAC) (see :ref:`appcont`)
      - No
      - Yes
      - Yes
    * - Concurrent programming with asyncio (see :ref:`concurrentprogramming`)
      - Yes
      - No
      - No
    * - Oracle Database 23ai Pipelining (see :ref:`pipelining`)
      - Yes
      - No
      - No
    * - End-to-end monitoring and tracing attributes (see :ref:`tracingsql`)
      - Yes
      - Yes
      - Yes
    * - Automatic Diagnostic Repository (ADR) (see `About Fault Diagnosability in OCI <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-A2945AF1-36DE-4C87-8C19-DA82B352F176>`__)
      - No
      - Yes
      - Yes
    * - Java Debug Wire Protocol for debugging PL/SQL (see :ref:`jdwp`)
      - Yes
      - Yes
      - Yes
    * - Two-phase Commit (TPC) (see :ref:`tpc`)
      - Yes
      - Yes
      - Yes - limited support
    * - REF CURSORs and Nested Cursors
      - Yes
      - Yes
      - Yes
    * - Pipelined tables
      - Yes
      - Yes
      - Yes
    * - Implicit Result Sets
      - Yes
      - Yes
      - Yes
    * - Application Contexts (see :ref:`appcontext`)
      - Yes
      - Yes
      - Yes
    * - Persistent and Temporary LOBs
      - Yes
      - Yes
      - Yes
    * - LOB length prefetching
      - Yes
      - Yes
      - Yes
    * - LOB locator operations such as trim
      - Yes
      - Yes
      - Yes

.. _supporteddbtypes:

Supported Oracle Database Data Types
====================================

The following table lists the Oracle Database types that are supported in the
python-oracledb driver.  See `Oracle Database Types <https://www.oracle.com/
pls/topic/lookup?ctx=dblatest&id=GUID-A3C0D836-BADB-44E5-A5D4-265BA5968483>`__
and `PL/SQL Types <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID
-391C58FD-16AF-486C-AF28-173E309CDBA5>`__.  The python-oracledb constant shown
is the common one.  In some python-oracledb APIs you may use other types, for
example when binding numeric values.

.. list-table-with-summary::  Oracle Database Data Types Supported
    :header-rows: 1
    :class: wy-table-responsive
    :align: center
    :summary: The first column displays the database data type. The second column displays the python-oracledb constant Name. The third column contains notes.  The fourth column shows Python types that can be used.

    * - Oracle Database Type
      - python-oracledb Constant Name
      - Notes
      - Supported Python Types
    * - VARCHAR2
      - :data:`~oracledb.DB_TYPE_VARCHAR`
      - No relevant notes
      - bytes, str
    * - NVARCHAR2
      - :data:`~oracledb.DB_TYPE_NVARCHAR`
      - No relevant notes
      - bytes, str
    * - NUMBER, FLOAT
      - :data:`~oracledb.DB_TYPE_NUMBER`
      - No relevant notes
      - bool, int, float, decimal.Decimal
    * - DATE
      - :data:`~oracledb.DB_TYPE_DATE`
      - No relevant notes
      - datetime.date, datetime.datetime
    * - BOOLEAN (PL/SQL and Oracle Database 23ai SQL)
      - :data:`~oracledb.DB_TYPE_BOOLEAN`
      - No relevant notes
      - Any type convertible to bool
    * - BINARY_DOUBLE
      - :data:`~oracledb.DB_TYPE_BINARY_DOUBLE`
      - No relevant notes
      - bool, int, float, decimal.Decimal
    * - BINARY_FLOAT
      - :data:`~oracledb.DB_TYPE_BINARY_FLOAT`
      - No relevant notes
      - bool, int, float, decimal.Decimal
    * - TIMESTAMP
      - :data:`~oracledb.DB_TYPE_TIMESTAMP`
      - No relevant notes
      - datetime.date, datetime.datetime
    * - TIMESTAMP WITH TIME ZONE
      - :data:`~oracledb.DB_TYPE_TIMESTAMP_TZ`
      - No relevant notes
      - datetime.date, datetime.datetime
    * - TIMESTAMP WITH LOCAL TIME ZONE
      - :data:`~oracledb.DB_TYPE_TIMESTAMP_LTZ`
      - No relevant notes
      - datetime.date, datetime.datetime
    * - INTERVAL YEAR TO MONTH
      - :data:`~oracledb.DB_TYPE_INTERVAL_YM`
      - No relevant notes
      - :ref:`oracledb.IntervalYM <interval_ym>`
    * - INTERVAL DAY TO SECOND
      - :data:`~oracledb.DB_TYPE_INTERVAL_DS`
      - No relevant notes
      - datetime.timedelta
    * - RAW
      - :data:`~oracledb.DB_TYPE_RAW`
      - No relevant notes
      - bytes, str
    * - LONG
      - :data:`~oracledb.DB_TYPE_LONG`
      - No relevant notes
      - bytes, str
    * - LONG RAW
      - :data:`~oracledb.DB_TYPE_LONG_RAW`
      - No relevant notes
      - bytes, str
    * - ROWID
      - :data:`~oracledb.DB_TYPE_ROWID`
      - No relevant notes
      - bytes, str
    * - UROWID
      - :data:`~oracledb.DB_TYPE_ROWID`, :data:`~oracledb.DB_TYPE_UROWID` (only supported in python-oracledb Thin mode)
      - May show :data:`~oracledb.DB_TYPE_UROWID` in metadata. See :ref:`Query Metadata Differences <querymetadatadiff>`.
      - bytes, str
    * - CHAR
      - :data:`~oracledb.DB_TYPE_CHAR`
      - No relevant notes
      - bytes, str
    * - BLOB
      - :data:`~oracledb.DB_TYPE_BLOB`
      - No relevant notes
      - :ref:`oracledb.LOB <lobobj>`, bytes, str
    * - CLOB
      - :data:`~oracledb.DB_TYPE_CLOB`
      - No relevant notes
      - :ref:`oracledb.LOB <lobobj>`, bytes, str
    * - NCHAR
      - :data:`~oracledb.DB_TYPE_NCHAR`
      - No relevant notes
      - bytes, str
    * - NCLOB
      - :data:`~oracledb.DB_TYPE_NCLOB`, :data:`~oracledb.DB_TYPE_LONG_NVARCHAR` (if fetching NCLOB as a string)
      - No relevant notes
      - :ref:`oracledb.LOB <lobobj>`, bytes, str
    * - BFILE
      - :data:`~oracledb.DB_TYPE_BFILE`
      - Can fetch a BFILE object and insert that object in a table. Cannot create BFILE objects.
      - :ref:`oracledb.LOB <lobobj>`, bytes
    * - JSON
      - :data:`~oracledb.DB_TYPE_JSON`
      - No relevant notes
      - Any type convertible to Oracle JSON
    * - REF CURSOR (PL/SQL OR nested cursor)
      - :data:`~oracledb.DB_TYPE_CURSOR`
      - No relevant notes
      - :ref:`oracledb.Cursor <cursorobj>`
    * - PLS_INTEGER
      - :data:`~oracledb.DB_TYPE_BINARY_INTEGER`
      - No relevant notes
      - bool, int, float, decimal.Decimal
    * - BINARY_INTEGER
      - :data:`~oracledb.DB_TYPE_BINARY_INTEGER`
      - No relevant notes
      - bool, int, float, decimal.Decimal
    * - REF
      - n/a
      - Not supported in python-oracledb Thin mode
      - n/a
    * - XMLType
      - :data:`~oracledb.DB_TYPE_XMLTYPE`
      - May need to use ``xmltype.getclobval()`` to fetch in python-oracledb Thick mode. See :ref:`xmldatatype`
      - bytes, str
    * - User-defined types (object type, VARRAY, records, collections, SDO_*types)
      - :data:`~oracledb.DB_TYPE_OBJECT`
      - No relevant notes
      - OBJECT of specific type
    * - VECTOR
      - :data:`~oracledb.DB_TYPE_VECTOR`
      - No relevant notes
      - array.array

Binding of contiguous PL/SQL Index-by BINARY_INTEGER arrays of string, number, and date are
supported in python-oracledb Thin and Thick modes. Use :meth:`Cursor.arrayvar()` to build
these arrays.
