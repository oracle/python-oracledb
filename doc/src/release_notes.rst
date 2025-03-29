:orphan:

.. _releasenotes:

python-oracledb Release Notes
=============================

For deprecations, see :ref:`Deprecations <deprecations>`.

Release changes are listed as affecting Thin Mode (the default runtime behavior
of python-oracledb), as affecting the optional :ref:`Thick Mode
<enablingthick>`, or as being 'Common' for changes that impact both modes.

oracledb 3.1.0 (TBD)
--------------------

Thin Mode Changes
+++++++++++++++++

#)  Added support for :ref:`scrollable cursors <scrollablecursors>`.
#)  Improved support for :ref:`Oracle Advanced Queuing <aqusermanual>`:

    - Added support for JSON payloads
    - Added support for bulk enqueuing and dequeuing
    - Added support for using AQ with asyncio

#)  Improved error message when the cryptography package cannot be imported
    (`issue 455 <https://github.com/oracle/python-oracledb/issues/455>`__).
#)  Fixed decoding of nested PL/SQL records
    (`issue 456 <https://github.com/oracle/python-oracledb/issues/456>`__).
#)  Fixed wildcard matching of domains in Subject Alternative Names
    (`issue 462 <https://github.com/oracle/python-oracledb/issues/462>`__).
#)  Fixed bug when binding a temporary LOB IN/OUT to a PL/SQL procedure
    (`issue 468 <https://github.com/oracle/python-oracledb/issues/468>`__).
#)  Fixed bug when an error is reported by the server in the middle of a
    response to a client request
    (`issue 472 <https://github.com/oracle/python-oracledb/issues/472>`__).
#)  Fixed bug when connecting to an AC-enabled service
    (`issue 476 <https://github.com/oracle/python-oracledb/issues/476>`__).
#)  Fixed bug when using temporary LOBs with implicit pooling.
#)  Fixed bug when fetching nested cursors.

Thick Mode Changes
++++++++++++++++++

#)  Fixed bug resulting in a segfault when unable to load the Oracle Client
    libraries
    (`ODPI-C <https://github.com/oracle/odpi>`__ dependency update).
#)  Fixed bug which resulted in error ``ORA-24328: illegal attribute value``
    when calling :meth:`Connection.gettype()` with Oracle Client 11.2
    libraries
    (`ODPI-C <https://github.com/oracle/odpi>`__ dependency update).
#)  Improved error message when getting :attr:`Connection.max_open_cursors`
    when using Oracle Client 11.2 libraries
    (`ODPI-C <https://github.com/oracle/odpi>`__ dependency update).
#)  Improved error message when attempting to work with sparse vectors using
    Oracle Client 23.6 (or earlier) libraries
    (`ODPI-C <https://github.com/oracle/odpi>`__ dependency update).

Common Changes
++++++++++++++

#)  Dropped support for Python 3.8.
#)  Improvements to data frame fetching with :meth:`Connection.fetch_df_all()`
    and :meth:`Connection.fetch_df_batches()`:

    - Added support for CLOB, BLOB and RAW data types
    - Fixed support for BOOLEAN data type
    - Fixed bug when NUMBER data is fetched that does not have a precision or
      scale specified and :attr:`defaults.fetch_decimals` is set to *True*.
    - More efficient processing when a significant amount of data is duplicated
      from one row to the next
    - Avoid memory allocation/free cycles for decimal data
    - Eliminated memory leak if OracleDataFrame is not converted to an external
      data frame
    - Eliminated small memory leak with production of each data frame

#)  Made the :ref:`Azure App Centralized Configuration Provider
    <azureappstorageprovider>` connection string suffix ".azconfig.io"
    optional.
#)  Fixed bug when binding a variable that was previously bound as an output
    variable in a DML RETURNING statement.
#)  Fixed bug when multiple rows containing LOBs and DbObjects are returned in
    a DML RETURNING statement.
#)  An error message that links to :ref:`documentation <ldapconnections>` on
    setting up a protocol hook function is now returned by default for LDAP and
    LDAPS URL connection strings in python-oracledb thin mode, or when
    :attr:`defaults.thick_mode_dsn_passthrough` is *False*.
#)  Error ``DPY-2062: payload cannot be enqueued since it does not match the
    payload type supported by the queue`` is now raised when the payload of a
    message being enqueued is not supported by the queue. Previously,
    python-oracledb Thick mode raised the error ``DPI-1071: payload type in
    message properties must match the payload type of the queue`` and thin mode
    raised an internal error.
#)  Improved the test suite and documentation.


oracledb 3.0.0 (March 2025)
---------------------------

Thin Mode Changes
+++++++++++++++++

#)  Added :ref:`Oracle Advanced Queuing <aqusermanual>` support for single
    enqueue and dequeue of RAW and Oracle object payload types.
#)  Added namespace package :ref:`oracledb.plugins <plugins>` for plugins that
    can be used to extend the capability of python-oracledb.
#)  Added support for property :attr:`ConnectionPool.max_lifetime_session`
    (`issue 410 <https://github.com/oracle/python-oracledb/issues/410>`__).
#)  Added parameter :data:`ConnectParams.use_sni` to specify that the TLS SNI
    extension should be used to reduce the number of TLS negotiations that are
    needed to connect to the database.
#)  Added parameter :data:`ConnectParams.instance_name` to specify the instance
    name to use when connecting to the database. Added support for setting the
    instance name in :ref:`Easy Connect strings <easyconnect>`.
#)  Added support for Transaction Guard by adding support to get the values of
    :attr:`Connection.ltxid` and :attr:`oracledb._Error.isrecoverable`.
#)  Improved support for planned database maintenance by internally sending
    explicit request boundaries when using python-oracledb connection pools.
#)  Perform TLS server matching in python-oracledb instead of the Python SSL
    library to allow alternate names to be checked
    (`issue 415 <https://github.com/oracle/python-oracledb/issues/415>`__).
#)  Host names are now resolved to IP addresses in python-oracledb instead of
    the Python libraries. Address list load balancing and failover settings
    will be used when establishing connections.
#)  The thread that closes connection pools on interpreter shutdown is now only
    started when the first pool is created and not at module import
    (`issue 426 <https://github.com/oracle/python-oracledb/issues/426>`__).
#)  Support for :ref:`Pipelining <pipelining>` is no longer considered a
    pre-release.
#)  Fixed hang when attempting to use pipelining against a database that
    doesn't support the end of response flag.
#)  Fixed hang when using asyncio and a connection is unexpectedly closed by
    the database.
#)  Fixed bug when using :ref:`asyncio <concurrentprogramming>` and calling a
    stored procedure with data that exceeds 32767 bytes in length
    (`issue 441 <https://github.com/oracle/python-oracledb/issues/441>`__).
#)  Fixed bug when attempting to fetch a database object stored in a LOB. The
    fetch will still fail but with an unsupported error exception instead of a
    hang.
#)  Error ``DPY-6002: The distinguished name (DN) on the server certificate
    does not match the expected value: "{expected_dn}"`` now shows the expected
    value.
#)  Error ``DPY-6006: The name on the server certificate does not match the
    expected value: "{expected_name}"`` is now raised when neither the common
    name (CN) nor any of the subject alternative names (SANs) found on the
    server certificate match the host name used to connect to the database.
#)  The text of error ``DPY-4022: invalid value for DRCP purity {purity}``
    changed to ``DPY-4022: invalid value for enumeration {name}: {value}``.
#)  Error ``DPY-3001: bequeath is only supported in python-oracledb thick
    mode`` is now raised when attempting to connect to the database without a
    connect string.
#)  Error ``DPY-3001: Native Network Encryption and Data Integrity is only
    supported in python-oracledb thick mode`` is now the secondary error
    message returned when Oracle Net NNE or checksumming is required by the
    database. Previously, the error ``DPY-4011: the database or network closed
    the connection`` was raised.
#)  Optimization: the connect descriptor sent to the database does not include
    the RETRY_DELAY parameter unless the RETRY_COUNT parameter is also
    specified.
#)  Internal change: improve low-level encoding and decoding routines.
#)  Internal change: send buffer length for bind variables without unneeded
    adjustment.

Thick Mode Changes
++++++++++++++++++

#)  At successful completion of a call to :meth:`oracledb.init_oracle_client()`,
    the value of :attr:`defaults.config_dir` may get set by python-oracledb in
    some cases. For example it might be set to the configuration directory that
    is relative to the loaded Oracle Client libraries.
#)  Connect string parsing and :ref:`tnsnames.ora <optnetfiles>` file handling
    can be configured with the new parameter
    :attr:`defaults.thick_mode_dsn_passthrough` which can be helpful for
    application portability. When it is `False`, python-oracledb Thick mode
    behaves similarly to Thin mode.
#)  Fixed bug that caused :attr:`oracledb._Error.isrecoverable` to always be
    `False`.

Common Changes
++++++++++++++

#)  Added new methods :meth:`Connection.fetch_df_all()`,
    :meth:`Connection.fetch_df_batches()`,
    :meth:`AsyncConnection.fetch_df_all()`, and
    :meth:`AsyncConnection.fetch_df_batches()` to fetch data as
    :ref:`OracleDataFrame objects <oracledataframeobj>` that expose an Apache
    Arrow PyCapsule interface for efficient data exchange with external
    libraries. See :ref:`dataframeformat`.
#)  Added support for Oracle Database 23.7
    :ref:`SPARSE vectors <sparsevectors>`.
#)  Added support for :ref:`naming and caching connection pools
    <connpoolcache>` during creation, and retrieving them later from the
    python-oracledb pool cache with :meth:`oracledb.get_pool()`.
#)  Added :ref:`Centralized Configuration Provider <configurationproviders>`
    support for Oracle Cloud Infrastructure Object Storage, Microsoft Azure App
    Configuration, and file-based configurations.
#)  Added :meth:`oracledb.register_password_type()` to allow users to register
    a function that will be called when a password is supplied as a dictionary
    containing the key "type".
#)  Added :ref:`cloud native authentication <tokenauth>` support through the
    integration of Oracle Cloud Infrastructure (OCI) SDK and Azure SDK.
#)  Added parameter ``extra_auth_params`` to :meth:`oracledb.connect()`,
    :meth:`oracledb.connect_async()`, :meth:`oracledb.create_pool()`,
    and :meth:`oracledb.create_pool_async()` which is used to specify the
    configuration parameters required for cloud native authentication.
#)  Added :meth:`oracledb.register_params_hook()` and
    :meth:`oracledb.unregister_params_hook()` which allow users to register or
    unregister a function that manipulates the parameters used for creating
    pools or standalone connections. See
    :ref:`oci_tokens <ocicloudnativeauthplugin>` and
    :ref:`azure_tokens <azurecloudnativeauthplugin>` plugins which make use of
    this functionality.
#)  Added attributes :attr:`DbObjectAttribute.precision`,
    :attr:`DbObjectAttribute.scale`, and :attr:`DbObjectAttribute.max_size` that
    provide additional metadata about
    :ref:`database object attributes <dbobjectattr>`.
#)  The attribute :attr:`defaults.config_dir` is now set to
    ``$ORACLE_HOME/network/admin`` if the environment variable ``ORACLE_HOME``
    is set and ``TNS_ADMIN`` is *not* set.
#)  All connect strings are parsed by the driver if the new parameter
    ``thick_mode_dsn_passthrough`` is set to *True*. Previously, only Thin
    mode parsed all connect strings and Thick mode passed the connect string
    unchanged to the Oracle Client library to parse. Parameters unrecognized by
    the driver in :ref:`Easy Connect strings <easyconnect>` are now ignored.
    Parameters unrecognized by the driver in the ``DESCRIPTION``,
    ``CONNECT_DATA`` and ``SECURITY`` sections of a
    :ref:`full connect descriptor <conndescriptor>` are passed through
    unchanged. All other parameters in other sections of a full connect
    descriptor that are unrecognized by the driver are ignored.
#)  Fixed bug where some :ref:`DbObject <dbobjecttype>` attributes for database
    objects defined using ANSI names (including FLOAT and REAL) may have shown
    as integers.
#)  All Oracle errors that result in the connection no longer being usable will
    be raised as ``DPY-4011: the database or network closed the connection``
    with the underlying reason being included in the error message.
#)  Fix typing issue with :meth:`oracledb.connect()`,
    :meth:`oracledb.connect_async()`, :meth:`oracledb.create_pool()` and
    :meth:`oracledb.create_pool_async()`
    (`issue 438 <https://github.com/oracle/python-oracledb/issues/438>`__).
#)  Fix typing issues with setters for :attr:`defaults.fetch_lobs` and
    :attr:`defaults.fetch_decimals`
    (`issue 458 <https://github.com/oracle/python-oracledb/issues/458>`__).
#)  Error ``DPY-2053: python-oracledb thin mode cannot be used because thick
    mode has already been enabled`` is now raised when attempting to use
    asyncio in thick mode
    (`issue 448 <https://github.com/oracle/python-oracledb/issues/448>`__).
#)  Error ``DPY-2056: registered handler for protocol "{protocol}" failed for
    arg "{arg}"`` is now raised when an exception occurs when calling the
    registered handler for a protocol.
#)  Added a sample Dockerfile that can be used to create a container for
    developing and deploying python-oracledb applications.
#)  Internal change: improve handling of metadata.
#)  Internal build tool change: bumped minimum Cython version to 3.0.10 to
    avoid bug in earlier versions.
#)  Improved test suite and documentation.


oracledb 2.5.1 (December 2024)
------------------------------

Thin Mode Changes
+++++++++++++++++

#)  Fixed bug when table recreation changes the data type of a column from
    :data:`oracledb.DB_TYPE_LONG` or :data:`oracledb.DB_TYPE_LONG_RAW` to a
    different compatible type
    (`issue 424 <https://github.com/oracle/python-oracledb/issues/424>`__).
#)  If the database states that an out-of-band break check should not take
    place during connect (by setting the `DISABLE_OOB_AUTO
    <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
    id=GUID-490A0B3B-FEF3-425A-81B0-6FA29D4B8C0E>`__ parameter to TRUE),
    python-oracledb no longer attempts to do so
    (`issue 419 <https://github.com/oracle/python-oracledb/issues/419>`__).
#)  All exceptions subclassed from ``OSError`` now cause connection retry
    attempts, subject to the connection ``retry_count`` and ``retry_delay``
    parameters
    (`issue 420 <https://github.com/oracle/python-oracledb/issues/420>`__).

Thick Mode Changes
++++++++++++++++++

#)  Fixed bug calculating property :data:`Connection.max_identifier_length`
    when using Oracle Client libraries 12.1, or older. The returned value may
    now be ``None`` when the size cannot be reliably determined by
    python-oracledb, which occurs when using Oracle Client libraries 12.1 (or
    older) to connect to Oracle Database 12.2, or later.
    (`ODPI-C <https://github.com/oracle/odpi>`__ dependency update).
#)  Fixed bug resulting in a segfault when using external authentication
    (`issue 425 <https://github.com/oracle/python-oracledb/issues/425>`__).

Common Changes
++++++++++++++

#)  Fixed bug when fetching empty data from CLOB or BLOB columns marked with
    the ``IS JSON`` constraint
    (`issue 429 <https://github.com/oracle/python-oracledb/issues/429>`__).


oracledb 2.5.0 (November 2024)
------------------------------

Thin Mode Changes
+++++++++++++++++

#)  Added attributes :attr:`Connection.session_id` and
    :attr:`Connection.serial_num` that provide information about the session
    identifier and session serial number associated with a connection.
#)  Added attributes
    :attr:`oracledb.defaults.driver_name <defaults.driver_name>`,
    :attr:`oracledb.defaults.machine <defaults.machine>`,
    :attr:`oracledb.defaults.osuser <defaults.osuser>`,
    :attr:`oracledb.defaults.program <defaults.program>`, and
    :attr:`oracledb.defaults.terminal <defaults.terminal>` to set
    information about the driver name, machine name, operating system user,
    program name, and terminal name respectively. The ``driver_name``,
    ``machine``, ``osuser``, ``program``, and ``terminal`` parameters were also
    added to :meth:`oracledb.connect()`, :meth:`oracledb.connect_async()`,
    :meth:`oracledb.create_pool()`, and :meth:`oracledb.create_pool_async()`
    (`issue 343 <https://github.com/oracle/python-oracledb/issues/343>`__).
#)  Added :meth:`oracledb.register_protocol()` to allow users to register a
    function that will be called when a particular protocol is detected in a
    connection string.
#)  Added :meth:`oracledb.enable_thin_mode()` as a means of enabling
    python-oracledb Thin mode without waiting for an initial connection to be
    succesfully established. Since python-oracledb defaults to Thin mode, this
    method is mostly useful for applications with multiple threads concurrently
    creating connections to databases when the application starts
    (`issue 408 <https://github.com/oracle/python-oracledb/issues/408>`__).
#)  Added attribute :data:`PipelineOpResult.warning` to provide information
    about any warning that was encountered during the execution of a pipeline
    operation.
#)  Added attribute :data:`PipelineOpResult.columns` to provide information
    about any query column metadata returned from a pipeline operation.
#)  Added support for setting the :ref:`edition <ebr>` when connecting to
    Oracle Database.
#)  Added support for Application Contexts, i.e. the ``appcontext`` parameter
    is supported when connecting.
#)  Fixed bug causing some pooled connections to be permanently marked as busy
    and unavailable for reuse
    (`issue 392 <https://github.com/oracle/python-oracledb/issues/392>`__).
#)  Fixed bug with error handling when calling :meth:`Connection.gettype()` for
    a type that exists but on which the user has insufficient privileges to
    view
    (`issue 397 <https://github.com/oracle/python-oracledb/issues/397>`__).
#)  Fixed bug when calling :meth:`ConnectParams.parse_dsn_with_credentials()`
    with an Easy Connect string containing a protocol.
#)  Fixed bug when calling :meth:`Cursor.parse()` with autocommit enabled.
#)  Fixed bug when parsing a :ref:`tnsnames.ora files <optnetfiles>` file with
    a connect descriptor containing an embedded comment.
#)  Fixed bug when calling :meth:`AsyncConnection.run_pipeline()` with a DML
    RETURNING statement that results in an error.
#)  Fixed error message when a SQL statement is parsed containing a q-string
    without a closing quote.
#)  Fixed bug affecting Python interpreter shut down using connection pooling
    in SQLAlchemy. Pooled connection shutdown now occurs separately from pool
    destruction.

Thick Mode Changes
++++++++++++++++++

#)  Use `locale.getencoding() <https://docs.python.org/3/library/locale.html#
    locale.getencoding>`__ with Python 3.11 and higher to determine the
    encoding to use for the ``config_dir`` and ``lib_dir`` parameters to
    :meth:`oracledb.init_oracle_client()`. Bytes are also accepted in which
    case they will be used as is without any encoding
    (`issue 255 <https://github.com/oracle/python-oracledb/issues/255>`__).
#)  Fixed bug preventing subscriptions from invoking the callbacks associated
    with them
    (`issue 409 <https://github.com/oracle/python-oracledb/issues/409>`__).
#)  Fixed bug affecting Application Continuity when older Oracle Client
    libraries are used (`ODPI-C <https://github.com/oracle/odpi>`__ dependency
    update).

Common Changes
++++++++++++++

#)  Added support for returning the maximum identifier length allowed by the
    database using the new property :data:`Connection.max_identifier_length`
    (`issue 395 <https://github.com/oracle/python-oracledb/issues/395>`__).
#)  Improved type hints for cursors
    (`issue 391 <https://github.com/oracle/python-oracledb/issues/391>`__).
#)  Improved error message when attempting to access attributes on a connection
    before a connection has been established or a connection pool before it has
    been created
    (`issue 385 <https://github.com/oracle/python-oracledb/issues/385>`__).
#)  The variables saved with :meth:`Cursor.setinputsizes()` are now forgotten
    when an exception is raised
    (`issue 411 <https://github.com/oracle/python-oracledb/issues/411>`__).
#)  Fixed bug when calling :meth:`ConnectParams.set()` with a value of ``None``
    for the ``connectiontype`` and ``session_callback`` parameters. Previously,
    any values set earlier would be improperly cleared and now they are
    retained
    (`issue 404 <https://github.com/oracle/python-oracledb/issues/404>`__).
#)  Improved test suite and documentation.


oracledb 2.4.1 (August 2024)
----------------------------

Thin Mode Changes
+++++++++++++++++

#)  Fixed bug when detecting in-band notification warnings while the connection
    is being created or actively used
    (`issue 383 <https://github.com/oracle/python-oracledb/issues/383>`__).


oracledb 2.4.0 (August 2024)
----------------------------

Thin Mode Changes
+++++++++++++++++

#)  Added support for Oracle Database 23ai :ref:`statement pipelining
    <pipelining>`.
#)  Fixed bug resulting in a segfault when a closed cursor is bound as a REF
    CURSOR
    (`issue 368 <https://github.com/oracle/python-oracledb/issues/368>`__).
#)  Fixed bug resulting in an inability to connect to Oracle Database 23ai
    instances which have fast authentication disabled.
#)  Fixed error message when idle time is exceeded by a connection. The error
    ``DPY-4033: the database closed the connection because the connection's
    idle time has been exceeded`` is now raised when this situation is
    detected.
#)  Reworked connection string parser:

    - Fixed parsing an :ref:`Easy Connect <easyconnect>` string starting
      with "`//`" (`issue 352
      <https://github.com/oracle/python-oracledb/issues/352>`__).
    - Fixed parsing an Easy Connect string with multiple hosts (a comma for
      multiple addresses and a semicolon for multiple address lists).
    - Fixed parsing an Easy Connect string with a static IPv6 address.
    - Improved error when a connect descriptor parameter like DESCRIPTION or
      ADDRESS incorrectly contains a simple value instead of nested values.

#)  Reworked :ref:`tnsnames.ora<optnetfiles>` file parser to handle multiple
    aliases found on separate lines (`issue 362
    <https://github.com/oracle/python-oracledb/issues/362>`__).

Thick Mode Changes
++++++++++++++++++

#)  Variables containing cursors, LOBs or DbObject values now return the same
    instances when calling :meth:`Variable.getvalue()`, matching Thin mode
    behavior. Previously, new instances were created for each call in Thick
    mode.

Common Changes
++++++++++++++

#)  Added support for Python 3.13 and dropped support for Python 3.7.
#)  Attribute :data:`ConnectionPool.getmode` is now one of the values of the
    enumeration :ref:`connection pool get modes <connpoolmodes>` in order to be
    consistent with the other uses of this attribute.
#)  Error ``DPY-3027: binding a cursor from a different connection is not
    supported`` is now raised when attempting to bind a cursor created on a
    different connection. Previously, the attempt may have succeeded or may
    have failed with a number of different unexpected exceptions.
#)  Error ``DPY-1006: cursor is not open`` is now raised consistently when
    attempting to bind a closed cursor. Previously, thin mode would result in a
    segfault and thick mode would result in unusual errors.


oracledb 2.3.0 (July 2024)
--------------------------

Thin Mode Changes
+++++++++++++++++

#)  Added support for :ref:`two-phase commits <tpc>`.
#)  Added support for columns of type BFILE.
#)  When calling :meth:`ConnectionPool.acquire()` or
    :meth:`AsyncConnectionPool.acquire()`, the connection pool ``mode``
    :data:`oracledb.POOL_GETMODE_TIMEDWAIT` now always honors the
    ``wait_timeout`` value and the connection request will not additionally be
    delayed by any internal network ping to the database (`issue 330
    <https://github.com/oracle/python-oracledb/issues/330>`__).
#)  Fixed bug when calling :meth:`oracledb.connect_async()` multiple times
    concurrently
    (`issue 353 <https://github.com/oracle/python-oracledb/issues/353>`__).
#)  Fixed bug in fetching dates with years less than 0
    (`issue 345 <https://github.com/oracle/python-oracledb/issues/345>`__).


Thick Mode Changes
++++++++++++++++++

#)  Eliminated memory leak when dequeing messages with JSON payloads
    (`issue 346 <https://github.com/oracle/python-oracledb/issues/346>`__).
#)  An exception is now avoided if an error message is not correctly UTF-8
    encoded by the database.

Common Changes
++++++++++++++

#)  Added support for Oracle Database 23ai
    :ref:`BINARY vector format <binaryformat>`.
#)  Replaced integer constants for
    :ref:`connection authorization modes <connection-authorization-modes>`,
    :ref:`connection pool get modes <connpoolmodes>`,
    :ref:`connection pool purity constants <drcppurityconsts>` and
    :ref:`vector format constants <vectorformatconstants>` with
    `enumerations <https://docs.python.org/3/library/enum.html>`__ in order to
    provide a more useful ``repr()`` and improve type safety, among other
    things.
#)  The default value of the ``tcp_connect_timeout`` parameter was changed
    from 60 seconds to 20 seconds. The default value of the
    ``retry_delay`` parameter was changed from 0 seconds to 1 second.
#)  Added parameter ``ssl_version`` to :meth:`oracledb.connect()`
    :meth:`oracledb.connect_async()`, :meth:`oracledb.create_pool()`, and
    :meth:`oracledb.create_pool_async()` methods in order to specify which TLS
    version to use when establishing connections with the protocol "tcps".
#)  Added parameter ``ping_timeout`` to methods :meth:`oracledb.create_pool()`
    and :meth:`oracledb.create_pool_async()` with a default value of 5000
    milliseconds. This limits the amount of time that a call to
    :meth:`~ConnectionPool.acquire()` will wait for a connection to respond to
    any internal ping to the database before the connection is considered
    unusable and a different connection is returned to the application.
    Previously, a fixed timeout of 5000 milliseconds was used in Thick mode and
    no explicit timeout was used in Thin mode.
#)  Added support for maintainers to specify optional compilation arguments
    when building python-oracledb. A new environment variable
    ``PYO_COMPILE_ARGS`` can be set :ref:`before building <installsrc>`.
#)  Improved detection of the signature used by output type handlers, in
    particular those that that make use of ``__call__()``.
#)  Python wheel package binaries for Linux on `PyPI
    <https://pypi.org/project/oracledb/>`__ are now stripped to reduce their
    size.
#)  Error ``DPY-2049: invalid flags for tpc_begin()`` is now raised when
    invalid flags are passed to :meth:`Connection.tpc_begin()`.  Previously,
    ``TypeError`` or ``ORA-24759: invalid transaction start flags``
    was raised instead.
#)  Error ``DPY-2050: invalid flags for tpc_end()`` is now raised when invalid
    flags are passed to :meth:`Connection.tpc_end()`. Previously, ``TypeError``
    or ``DPI-1002: invalid OCI handle`` was raised instead.
#)  Error ``DPY-3025: operation is not supported on BFILE LOBs`` is now raised
    when operations are attempted on BFILE LOBs that are not permitted.
    Previously, ``ORA-22275: invalid LOB locator specified`` was raised
    instead.
#)  Error ``DPY-3026: operation is only supported on BFILE LOBs`` is now raised
    when operations are attempted on LOBs that are only supported by BFILE
    LOBs. Previously, ``DPI-1002: invalid OCI handle`` was raised instead.
#)  Error ``DPY-4005: timed out waiting for the connection pool to return a
    connection`` is now raised consistently when using get mode
    :data:`oracledb.POOL_GETMODE_TIMEDWAIT` and the timeout expires.
    Previously ``asyncio.TimeoutError`` was being raised when using
    :ref:`asyncio <asyncio>` and ``ORA-24457: OCISessionGet() could not find a
    free session in the specified timeout period`` was being raised in thick
    mode.
#)  If both the ``sid`` and ``service_name`` parameters are specified to
    :meth:`oracledb.makedsn()`, now only the ``service_name`` parameter is
    used and the ``sid`` parameter is ignored.
#)  Fixed bug in :meth:`ConnectParams.set()` where parameters found in a
    connect string (like ``host`` and ``service_name``) would be ignored.
#)  Fixed bug in :meth:`Connection.tpc_recover()` where the returned items were
    not of the type returned by :meth:`Connection.xid()` as documented.
#)  Internal changes to ensure that no circular imports occur.


oracledb 2.2.1 (May 2024)
-------------------------

Thin Mode Changes
+++++++++++++++++

#)  Fixed bug when a :ref:`DbObject <dbobject>` instance contains an attribute
    of type ``SYS.XMLTYPE``
    (`issue 336 <https://github.com/oracle/python-oracledb/issues/336>`__).
#)  Fixed bug when fetching LOBs after an exception has been raised
    (`issue 338 <https://github.com/oracle/python-oracledb/issues/338>`__).
#)  Fixed bug when a connect descriptor is used that doesn't define any
    addresses
    (`issue 339 <https://github.com/oracle/python-oracledb/issues/339>`__).
#)  Fixed bug in statement cache when the maximum number of cursors is unknown
    due to the database not being open.
#)  Fixed bug in handling redirect data with small SDU sizes.
#)  Fixed bug with TLS renegotiation under some circumstances.
#)  Adjusted handling of internal break/reset mechanism in order to avoid
    potential hangs in some configurations under some circumstances.


oracledb 2.2.0 (May 2024)
-------------------------

Thin Mode Changes
+++++++++++++++++

#)  Fixed bug in handling invisible columns with object type names containing
    ``%ROWTYPE``
    (`issue 325 <https://github.com/oracle/python-oracledb/issues/325>`__).
#)  Fixed bug that would cause pooled connections to be marked checked out but
    be unavailable for use permanently
    (`issue 221 <https://github.com/oracle/python-oracledb/issues/221>`__).
#)  Fixed bug that would cause an internal error to be raised when attempting
    to close a connection that has been forcibly closed by the database.
#)  Internal change: further efforts to tighten code looking for the end of a
    database request made to Oracle Database 23ai.

Common Changes
++++++++++++++

#)  Added support for Oracle Database 23ai columns of type :ref:`VECTOR
    <vectors>`.
#)  Added support for columns of type INTERVAL YEAR TO MONTH which can be
    represented in Python by instances of the new
    :ref:`oracledb.IntervalYM <interval_ym>` class
    (`issue 310 <https://github.com/oracle/python-oracledb/issues/310>`__).
#)  Added support for processing :ref:`tnsnames.ora files <optnetfiles>`
    containing ``IFILE`` directives
    (`issue 311 <https://github.com/oracle/python-oracledb/issues/311>`__).
#)  Added support for getting a list of the network service names found in a
    :ref:`tnsnames.ora <optnetfiles>` file by adding the method
    :meth:`ConnectParams.get_network_service_names()`
    (`issue 313 <https://github.com/oracle/python-oracledb/issues/313>`__).
#)  Added support for iterating over :ref:`DbObject <dbobject>` instances that
    are collections
    (`issue 314 <https://github.com/oracle/python-oracledb/issues/314>`__).
#)  Error ``ORA-24545: invalid value of POOL_BOUNDARY specified in connect
    string`` is now raised consistently for both Thick and Thin modes.
    Previously, Thin mode was raising the error
    ``DPY-4030: invalid DRCP pool boundary {boundary}``.


oracledb 2.1.2 (April 2024)
---------------------------

Thin Mode Changes
+++++++++++++++++

#)  Fixed bug that prevented error ``ORA-01403: no data found`` from being
    raised when executing a PL/SQL block
    (`issue 321 <https://github.com/oracle/python-oracledb/issues/321>`__).

Common Changes
++++++++++++++

#)  Fixed the internal regular expression used for parsing :ref:`Easy Connect
    <easyconnect>` strings to avoid errors with connection string arguments
    containing the ``/`` character.


oracledb 2.1.1 (March 2024)
---------------------------

Thin Mode Changes
+++++++++++++++++

#)  Fixed bug when calling :meth:`~Connection.gettype()` with an object type
    name containing ``%ROWTYPE``
    (`issue 304 <https://github.com/oracle/python-oracledb/issues/304>`__).
#)  Error ``DPY-2048: the bind variable placeholder ":{name}" cannot be used
    both before and after the RETURNING clause in a DML RETURNING statement``
    is now raised when the same bind variable placeholder name is used both
    before and after the RETURNING clause in a
    :ref:`DML RETURNING statement <dml-returning-bind>`. Previously, various
    internal errors were raised.
#)  Restored the error message raised when attempting to connect to Oracle
    Database 11g.
#)  Internal change: tightened up code looking for the end of a database
    request.
#)  Network packet output is now immediately flushed in order to avoid
    losing output due to buffering when multiple threads are running.


oracledb 2.1.0 (March 2024)
---------------------------

Thin Mode Changes
+++++++++++++++++

#)  Oracle Database 23ai feature support:

    - Added support for
      :ref:`implicit connection pooling with DRCP and PRCP <implicitconnpool>`,
      enabled by the new ``pool_boundary`` parameter to
      :meth:`oracledb.connect()`, :meth:`oracledb.connect_async()`,
      :meth:`oracledb.create_pool()` and :meth:`oracledb.create_pool_async()`.
    - Improved the performance of connection creation by reducing the number of
      round trips required for all connections.
    - Added support for TCP Fast Open for applications connecting from within
      the OCI Cloud network to Oracle Autonomous Database Serverless (ADB-S),
      enabled by the new ``use_tcp_fast_open`` parameter to
      :meth:`oracledb.connect()`, :meth:`oracledb.connect_async()`,
      :meth:`oracledb.create_pool()` and :meth:`oracledb.create_pool_async()`.

#)  :ref:`asyncio <asyncio>` changes:

    - Support for asyncio is no longer considered a pre-release.
    - Internal change to improve handling of packets.
    - Fixed bug when using :ref:`DRCP <drcp>`.
    - Fixed bug in processing metadata that spans multiple network packets.
    - Fixed bug when connecting to a database using listener redirects
      (`issue 285 <https://github.com/oracle/python-oracledb/issues/285>`__).

#)  Added support for Easy Connect strings found in
    :ref:`tnsnames.ora <optnetfiles>` files.
#)  Added support for writing UTF-8 encoded bytes to CLOB and NCLOB values and
    writing strings to BLOB values in order to be consistent with what is done
    for string variables.
#)  User-defined errors raised by the database no longer display an error help
    portal URL.
#)  Fixed potential cursor issues when using :ref:`drcp`.
#)  Fixed regression when using :ref:`IAM token authentication <iamauth>`
    (`issue 288 <https://github.com/oracle/python-oracledb/issues/288>`__).
#)  Fixed bug connecting to databases that are only mounted and not opened
    (`issue 294 <https://github.com/oracle/python-oracledb/issues/294>`__).
#)  Fixed bug in identifying bind variables in SQL statements containing a
    single line comment at the end of the statement.
#)  Fixed bug in determining the list of attributes for PL/SQL collections.
#)  Fixed bug in calculating the :data:`Connection.thin` attribute.
#)  Fixed type declaration for the ``connectiontype`` parameter to
    :meth:`oracledb.create_pool_async()` and the return value of
    :meth:`AsyncConnectionPool.acquire()`.


Thick Mode Changes
++++++++++++++++++

#)  Added support for internal use of JSON in SODA with Oracle Client 23. This
    allows for seamless transfer of extended data types.
#)  Fixed bug when calling :meth:`SodaDoc.getContent()` for SODA documents
    that do not contain JSON.
#)  Corrected support for Oracle Sharding.
#)  Errors ``DPY-4011: the database or network closed the connection`` and
    ``DPY-4024: call timeout of {timeout} ms exceeded`` now retain the original
    error message raised by the Oracle Client library.

Common Changes
++++++++++++++

#)  Added a boolean property :data:`FetchInfo.is_oson` which is set when a
    column has the check constraint ``IS JSON FORMAT OSON`` enabled.
#)  Added methods :meth:`Connection.decode_oson()` and
    :meth:`Connection.encode_oson()` to support fetching and inserting into
    columns which have the check constraint ``IS JSON FORMAT OSON`` enabled.
#)  Added class :ref:`oracledb.JsonId <jsonid>` to represent JSON ID values
    returned by SODA in Oracle Database 23.4 and later in the ``_id``
    attribute of documents stored in native collections.
#)  Added support for columns of type VECTOR usable with a limited
    availability release of Oracle Database 23.
#)  Errors raised when calling :meth:`Cursor.executemany()` with PL/SQL now
    have the :data:`oracledb._Error.offset` attribute populated with the last
    iteration that succeeded
    (`issue 283 <https://github.com/oracle/python-oracledb/issues/283>`__).
#)  A number of performance improvements were made.
#)  Error ``DPY-2045: arraysize must be an integer greater than zero`` is now
    raised when an invalid value is used for the attribute
    :data:`Cursor.arraysize`. Previously, a variety of errors (``TypeError``,
    ``OverflowError`` or ``ORA-03147: missing mandatory TTC field``) were
    raised.
#)  Error ``DPY-2016: variable array size of %d is too small (should be at
    least %d)`` is now raised when :meth:`Cursor.executemany()` is called with
    an integer number of iterations that is too large for the existing bind
    variables. Previously, the python-oracledb Thin mode raised ``IndexError``
    and python-oracledb Thick mode raised
    ``DPI-1018: array size of %d is too small``.
#)  Error ``DPY-1001: not connected to database`` is now raised when an attempt
    is made to perform an operation on a LOB using a closed connection.
    Previously, the python-oracledb Thin mode raised an ``AttributeError``
    exception and python-oracledb Thick mode raised
    ``DPI-1040: LOB was already closed``.
#)  Fixed bug in :meth:`ConnectParams.get_connect_string()` when a value for
    the connection parameter ``purity`` has been specified.
#)  Fixed bug in :meth:`ConnectParams.set()` that would clear the
    ``ssl_context``, ``appcontext``, ``shardingkey`` and ``supershardingkey``
    parameters if they were not included in the parameters. This also affected
    calls to :meth:`oracledb.connect()` and :meth:`oracledb.create_pool()` that
    made use of the DSN with credentials format.
#)  The error ``DPY-2047: LOB amount must be greater than zero`` is now raised
    when the ``amount`` parameter in :meth:`LOB.read()` is set to zero or
    negative.
#)  Fixed bug in the calculation of :data:`Cursor.rowcount` under some
    circumstances.
#)  Connection parameters that are strings now treat an empty string in the
    same way as the value ``None``.


oracledb 2.0.1 (January 2024)
-----------------------------

Thin Mode Changes
+++++++++++++++++

#)  Added support for using alternative event loop implementations such as
    uvloop with :ref:`asyncio <asyncio>`
    (`issue 276 <https://github.com/oracle/python-oracledb/issues/276>`__).
#)  Added support for the `asynchronous context manager protocol
    <https://docs.python.org/3/reference/datamodel.html?
    highlight=aenter#asynchronous-context-managers>`__ on the
    :ref:`AsyncCursor class <asynccursorobj>` as a convenience.
#)  Fixed regression when connecting to a database using listener redirects
    with either a :ref:`connection pool <connpooling>` or using
    :ref:`asyncio <asyncio>`
    (`issue 275 <https://github.com/oracle/python-oracledb/issues/275>`__).
#)  Fixed bug when an intermittent hang occurs on some versions of Oracle
    Database while using :ref:`asyncio <asyncio>` and the database raises an
    error and output variables are present
    (`issue 278 <https://github.com/oracle/python-oracledb/issues/278>`__).
#)  Fixed bug when fetch variables contain output converters and a query is
    re-executed
    (`issue 271 <https://github.com/oracle/python-oracledb/issues/271>`__).
#)  Corrected typing declaration for :meth:`oracledb.connect_async()`.
#)  Internal change to ensure that connection pools are closed gracefully when
    the main thread terminates.
#)  Internal change to slightly improve performance of LOB reads and writes.

Common Changes
++++++++++++++

#)  Fixed regression which prevented a null value from being set on
    :ref:`DbObject <dbobject>` attributes or used as elements of collections
    (`issue 273 <https://github.com/oracle/python-oracledb/issues/273>`__).
#)  Fixed regression from cx_Oracle which ignored the value of the
    ``encoding_errors`` parameter when creating variables by calling the method
    :meth:`Cursor.var()`
    (`issue 279 <https://github.com/oracle/python-oracledb/issues/279>`__).
#)  Bumped minimum requirement of Cython to 3.0.


oracledb 2.0.0 (December 2023)
------------------------------

Thin Mode Changes
+++++++++++++++++

#)  Added support for :ref:`concurrent programming with asyncio <asyncio>`
    (`issue 6 <https://github.com/oracle/python-oracledb/issues/6>`__).
#)  Added parameter :attr:`ConnectParams.sdu` for configuring the Session Data
    Unit (SDU) size for sizing internal buffers used for tuning communication
    with the database. The connection property :attr:`Connection.sdu` was also
    added.
#)  Added parameter :data:`ConnectParams.ssl_context` to modify the SSL context
    used when connecting via TLS
    (`issue 259 <https://github.com/oracle/python-oracledb/issues/259>`__).
#)  Added support for an Oracle Database 23ai JSON feature allowing field names
    with more than 255 UTF-8 encoded bytes.
#)  Added support for the ``FAILOVER`` clause in full connect descriptors.
#)  Fixed bug in detecting the current time zone
    (`issue 257 <https://github.com/oracle/python-oracledb/issues/257>`__).
#)  Fixed bug in handling database response in certain unusual circumstances.
#)  Fixed bug in handling exceptions raised during connection establishment.
#)  Fixed bug in identifying bind variables in SQL statements containing
    multiple line comments with multiple asterisks before the closing slash.
#)  A more meaningful error is raised when the wrong type of data is passed to
    :meth:`LOB.write()`.
#)  Internal change to support an Oracle Database 23ai JSON feature improving
    JSON storage usage.
#)  Internal change to ensure that all connections in a pool have been closed
    gracefully before the pool is closed.
#)  Internal changes to improve handling of the network protocol between
    python-oracledb and Oracle Database.
#)  Internal changes to improve handling of multiple address and description
    lists in full connect descriptors.

Thick Mode Changes
++++++++++++++++++

#)  Fixed bug in return value of :meth:`SodaOperation.replaceOne()`.

Common Changes
++++++++++++++

#)  Dropped support for Python 3.6.
#)  Desupported a number of parameters and attributes that were previously
    deprecated. See :ref:`desupport notices<_desupported_2_0>` for details.
#)  Added property :attr:`Cursor.warning` for database warnings (such as PL/SQL
    compilation warnings) generated by calls to :meth:`Cursor.execute()` or
    :meth:`Cursor.executemany()`.
#)  Added property :attr:`Connection.warning` for warnings (such as the password
    being in the grace period) generated during connection.
#)  Added properties that provide information about the database:
    :attr:`Connection.db_domain`, :attr:`Connection.db_name`,
    :attr:`Connection.max_open_cursors`, :attr:`Connection.service_name`
    and :attr:`Connection.transaction_in_progress`.
#)  Added property :data:`Connection.proxy_user` to show the name of the user
    which was used as a proxy when connecting (`issue 250
    <https://github.com/oracle/python-oracledb/issues/250>`__).
#)  Added properties :data:`FetchInfo.domain_schema`,
    :data:`FetchInfo.domain_name` and :data:`FetchInfo.annotations` for the
    `SQL domain <https://docs.oracle.com/en/database/oracle/oracle-database/
    23/sqlrf/create-domain.html#GUID-17D3A9C6-D993-4E94-BF6B-CACA56581F41>`__
    and `annotations <https://docs.oracle.com/en/database/oracle/
    oracle-database/23/sqlrf/annotations_clause.html#
    GUID-1AC16117-BBB6-4435-8794-2B99F8F68052>`__
    associated with columns that are being fetched. SQL domains and annotations
    require Oracle Database 23ai. If using python-oracledb Thick mode, Oracle
    Client 23ai is also required.
#)  Added parameter ``data`` to :meth:`Connection.createlob()` to allow data to
    be written at LOB creation time.
#)  Added type :data:`~oracledb.DB_TYPE_XMLTYPE` to represent data of type
    ``SYS.XMLTYPE`` in the database. Previously the value of
    :data:`FetchInfo.type_code` for data of this type was
    :data:`~oracledb.DB_TYPE_LONG` in Thick mode and
    :data:`~oracledb.DB_TYPE_OBJECT` in Thin mode.
#)  Attribute and element values of :ref:`Oracle Object <dbobject>` instances
    that contain strings or bytes now have their maximum size constraints
    checked. Errors ``DPY-2043`` (attributes) and ``DPY-2044`` (element values)
    are now raised when constraints are violated.
#)  Attribute and element values of :ref:`Oracle Object <dbobject>` instances
    that are numbers are now returned as integers if the precision and scale
    allow for it. This is the same way that numbers are fetched from the
    database
    (`issue 99 <https://github.com/oracle/python-oracledb/issues/99>`__).
#)  Errors that have entries in the
    :ref:`troubleshooting documentation <troubleshooting>` now have links to
    that documentation shown in the message text.
#)  Fixed bug with binding boolean values with Oracle Database 23ai
    (`issue 263 <https://github.com/oracle/python-oracledb/issues/263>`__).
#)  Fixed bug with getting unknown attributes from :ref:`Oracle Object
    <dbobject>` instances.
#)  Error ``DPY-4029: errors in array DML exceed 65535`` is now raised when the
    number of batch errors exceeds 65535 when calling
    :meth:`Cursor.executemany()` with the parameter ``batcherrors`` set to the
    value ``True``. Note that in thick mode this error is not raised unless the
    number of batch errors is a multiple of 65536; instead, the number of batch
    errors returned is modulo 65536
    (`issue 262 <https://github.com/oracle/python-oracledb/issues/262>`__).
#)  Black is now used to format Python code and ruff to lint Python code.


oracledb 1.4.2 (October 2023)
-----------------------------

Thick Changes
+++++++++++++

#)  Fixed bug resulting in a segfault on some platforms when using two-phase
    commit.

Common Changes
++++++++++++++

#)  Pre-built binaries are now being created for Python 3.12
    (`issue 237 <https://github.com/oracle/python-oracledb/issues/237>`__).


oracledb 1.4.1 (September 2023)
-------------------------------

Thin Mode Changes
+++++++++++++++++

#)  Improved statement bind variable placeholder parser performance, handle
    statements which use the `Alternative Quoting Mechanism
    <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-1824CBAA-6E16-4921-B2A6-112FB02248DA>`__
    ('Q' strings), and fix some issues identifying bind variable placeholders
    in embedded quotes and in JSON syntax.

Thick Changes
+++++++++++++

#)  Fixed error checking when getting or setting the connection pool parameters
    ``ping_interval`` and ``soda_metadata_cache``.

Common Changes
++++++++++++++

#)  Fixed bug when calling :meth:`Cursor.execute()` or
    :meth:`Cursor.executemany()` with missing bind data after calling
    :meth:`Cursor.setinputsizes()` with at least one of the values supplied as
    ``None``
    (`issue 217 <https://github.com/oracle/python-oracledb/issues/217>`__).
#)  SQL statement parsing now raises ``DPY-2041: missing ending quote (') in
    string`` or ``DPY-2042: missing ending quote (") in identifier`` for
    statements with the noted invalid syntax.  Previously, thick mode gave
    ``ORA-1756`` or ``ORA-1740``, respectively, while thin mode did not throw
    an error.
#)  Added missing ">" to ``repr()`` of :ref:`sodadb`.


oracledb 1.4.0 (August 2023)
----------------------------

Thin Mode Changes
+++++++++++++++++

#)  Added support for an Oracle Database 23ai feature that can improve the
    performance of connection creation by reducing the number of round trips
    required to create the second and subsequent connections to the same
    database.
#)  Added support for shrinking the connection pool back to the specified
    minimum size when the pool is idle for :data:`ConnectionPool.timeout`
    seconds.
#)  Added support for growing the connection pool back to the minimum number of
    connections after connections are killed or otherwise made unusable.
#)  A default connection class is now generated when DRCP is used with a
    connection pool and no connection class was specified when the pool was
    created. The default connection class will be of the form ``DPY:`` followed
    by a 16-byte unique identifier converted to base64 encoding.
#)  Changed internal connection feature negotiation for more accurate Oracle
    Database 23ai support.
#)  Added support for sending a generated connection identifier to the
    database used for tracing. An application specific prefix is prepended to
    this value if specified via a new ``connection_id_prefix`` parameter when
    creating standalone connections or connection pools.
#)  Added URL to the Oracle Database Error Help Portal in Oracle Database
    error messages similar to when Thick mode uses Oracle Client 23ai.
#)  Added support for the ``ORA_SDTZ`` environment variable used to set the
    session time zone used by the database.
#)  Fixed bug when a dynamically sized connection pool is created with an
    ``increment`` of zero and the pool needs to grow.
#)  Fixed bug affecting connection reuse when connections were acquired from
    the connection pool with a ``cclass`` different to the one used to
    create the pool.
#)  Fixed bug when a connection is discarded from the connection pool during
    :meth:`ConnectionPool.acquire()` and the ping check fails due to the
    connection being dead.
#)  Fixed bug when an output type handler is used and the value of
    :attr:`Cursor.prefetchrows` exceeds :attr:`Cursor.arraysize`
    (`issue 173 <https://github.com/oracle/python-oracledb/issues/173>`__).
#)  Fixed bug when an Application Continuity replay context is returned during
    connection to the database
    (`issue 176 <https://github.com/oracle/python-oracledb/issues/176>`__).
#)  Fixed bug when socket is not closed immediately upon failure to establish a
    connection to the database
    (`issue 211 <https://github.com/oracle/python-oracledb/issues/211>`__).

Thick Mode Changes
++++++++++++++++++

#)  Added function :meth:`SodaCollection.listIndexes()` for getting the indexes
    on a SODA collection.
#)  Added support for specifying if documents should be locked when fetched
    from SODA collections. A new non-terminal method
    :meth:`~SodaOperation.lock()` was added which requires Oracle Client
    21.3 or higher (or Oracle Client 19 from 19.11).
#)  Relaxed restriction for end-to-end tracing string connection
    attributes. These values can now be set to the value ``None`` which will be
    treated the same as an empty string.
#)  Fixed bug when using external authentication with an Easy Connect
    connection string.
#)  Fixed memory leak when accessing objects embedded within other objects.

Common Changes
++++++++++++++

#)  Use of Python 3.6 and 3.7 is deprecated and support for them will be
    removed in a future release. A warning is issued when these versions are
    used but otherwise they will continue to function as usual. The warning can
    be suppressed by importing `warnings
    <https://docs.python.org/3/library/warnings.html>`__ and adding a call like
    ``warnings.filterwarnings(action='ignore', module="oracledb")``
    *before* importing ``oracledb``.
#)  Added support for the :attr:`~Variable.outconverter` being called when a
    null value is fetched from the database and the new parameter
    ``convert_nulls`` to the method :meth:`Cursor.var()` is passed the value
    ``True``
    (`issue 107 <https://github.com/oracle/python-oracledb/issues/107>`__).
#)  Replaced fixed 7-tuple for the cursor metadata found in
    :data:`Cursor.description` with a class which provides additional
    information such as the database object type and whether the column
    contains JSON data.
#)  Changed the signature for output type handlers to
    ``handler(cursor, metadata)`` where the ``metadata`` parameter is a
    :ref:`FetchInfo<fetchinfoobj>` object containing the same information found
    in :data:`Cursor.description`. The original signature for output type
    handlers is deprecated and will be removed in a future version.
#)  Added support for fetching VARCHAR2 and LOB columns which contain JSON (and
    have the "IS JSON" check constraint enabled) in the same way as columns of
    type JSON (which requires Oracle Database 21c or higher) are fetched. In
    thick mode this requires Oracle Client 19c or higher. The attribute
    ``oracledb.__future__.old_json_col_as_obj`` must be set to the value
    ``True`` for this behavior to occur. In version 2.0 this will become the
    normal behavior and setting this attribute will no longer be needed.
#)  Added new property :attr:`Connection.instance_name` which provides the
    Oracle Database instance name associated with the connection. This is the
    same value as the SQL expression
    ``sys_context('userenv', 'instance_name')``.
#)  Added support for relational queries on the underlying tables of SODA
    collections created in Oracle Database 23ai if they contain JSON documents
    with embedded OIDs.
#)  Automatically retry a query if the error ``ORA-00932: inconsistent data
    types`` is raised (which can occur if a table or view is recreated with a
    data type that is incompatible with the column's previous data type).
#)  The ``repr()`` value of the DbObject class now shows the string "DbObject"
    instead of the string "Object" for consistency with the name of the class
    and the other ``repr()`` values for DbObjectType and DbObjectAttr.
#)  Fixed bug when binding sequences other than lists and tuples
    (`issue 205 <https://github.com/oracle/python-oracledb/issues/205>`__).
#)  Added support for using the Cython 3.0 release
    (`issue 204 <https://github.com/oracle/python-oracledb/issues/204>`__).
#)  Improved test suite and documentation.

oracledb 1.3.2 (June 2023)
--------------------------

Thin Mode Changes
+++++++++++++++++

#)  Fixed bug using :attr:`Cursor.arraysize` for tuning data fetches from REF
    CURSORS.
#)  Fixed bug connecting to databases with older 11g password verifiers
    (`issue 189 <https://github.com/oracle/python-oracledb/issues/189>`__).
#)  Fixed bugs in the implementation of the statement cache.
#)  Fixed bug which caused a cursor leak if an error was thrown while
    processing the execution of a query.
#)  Eliminated unneeded round trip when using token authentication to connect
    to the database.
#)  Fixed bug which could cause a redirect loop with improperly configured
    listener redirects.
#)  Fixed bug when executing PL/SQL with a large number of binds.
#)  Fixed bug when using DRCP with Oracle Database 23ai.

Thick Mode Changes
++++++++++++++++++

#)  Fixed bug when using external authentication with a Net Service Name
    connection string
    (`issue 178 <https://github.com/oracle/python-oracledb/issues/178>`__).
#)  Fixed bug when using external authentication with an Easy Connect
    connection string.

Common Changes
++++++++++++++

#)  When fetching rows from REF CURSORS, the cursor's
    :attr:`~Cursor.prefetchrows` attribute is now ignored. Use
    :attr:`Cursor.arraysize` for tuning these fetches. This change allows
    consistency between Thin and Thick modes.


oracledb 1.3.1 (April 2023)
---------------------------

Thin Mode Changes
+++++++++++++++++

#)  Improved performance of regular expressions used for parsing SQL
    (`issue 172 <https://github.com/oracle/python-oracledb/issues/172>`__).
#)  Fixed bug with Oracle Database 23ai when SQL is executed after first being
    parsed.
#)  Fixed bug when :data:`ConnectionPool.timeout` is not `None` when creating a
    connection pool
    (`issue 166 <https://github.com/oracle/python-oracledb/issues/166>`__).
#)  Fixed bug when a query is re-executed after an underlying table is dropped
    and recreated, and the query select list contains LOBs or JSON data.
#)  Fixed bug when warning message such as for impending password expiry is
    encountered during connect
    (`issue 171 <https://github.com/oracle/python-oracledb/issues/171>`__).

Common Changes
++++++++++++++

#)  Improved test suite and samples.


oracledb 1.3.0 (March 2023)
---------------------------

Thin Mode Changes
+++++++++++++++++

#)  Added direct support for the Oracle Database 21c JSON data type, removing
    the need to use an output type handler.
#)  Added implementation for :data:`ConnectionPool.timeout` to allow pools to
    shrink to ``min`` connections.
#)  Added check to prevent adding too many elements to bounded database
    collections.
#)  Removed internally set fixed size for database collections. Collections of
    any size supported by the database can now be created.
#)  Added support for connecting to databases that accept passwords longer than
    30 UTF-8 encoded bytes.
#)  Detect the time zone on the OS and set the session timezone using this
    value to be consistent with thick mode
    (`issue 144 <https://github.com/oracle/python-oracledb/issues/144>`__).
#)  Improved BOOLEAN handling.
#)  Error ``DPY-6005: cannot connect to database`` is now raised for all
    failures to connect to the database and the phrase ``cannot connect to
    database`` is removed from all other error messages (since this can be
    confusing when these errors are raised from
    :meth:`ConnectParams.parse_connect_string()`).
#)  Fixed bug when calling :meth:`Cursor.executemany()` with PL/SQL when the
    size of the bound data increases on subsequent calls
    (`issue 132 <https://github.com/oracle/python-oracledb/issues/132>`__).
#)  Fixed bug when binding data of type TIMESTAMP WITH TIME ZONE but with
    zero fractional seconds.
#)  Fixed bug with incorrect values of :data:`Cursor.rowcount` when fetching
    data
    (`issue 147 <https://github.com/oracle/python-oracledb/issues/147>`__).
#)  Fixed bug with SQL containing multibyte characters with certain database
    character sets
    (`issue 133 <https://github.com/oracle/python-oracledb/issues/133>`__).
#)  Fixed bug with ordering of binds in SQL when the database version is 12.1
    (`issue 135 <https://github.com/oracle/python-oracledb/issues/135>`__).
#)  Fixed bug with ordering of binds in PL/SQL when the bind variable may
    potentially exceed the 32767 byte limit but the actual value bound does not
    (`issue 146 <https://github.com/oracle/python-oracledb/issues/146>`__).
#)  Fixed bug connecting to an IPv6 address with IAM tokens.
#)  Fixed bug determining RETURNING binds in a SQL statement when RETURNING and
    INTO keywords are not separated by whitespace, but are separated by
    parentheses.
#)  The exception ``DPY-3022: named time zones are not supported in thin mode``
    is now raised when attempting to fetch data of type TIMESTAMP WITH TIME
    ZONE when the time zone associated with the data is a named time zone.
    Previously invalid data was returned
    (`disc 131 <https://github.com/oracle/python-oracledb/discussions/131>`__).
#)  Internal implementation changes:

    - Added internal support for prefetching the LOB size and chunk size,
      thereby eliminating a :ref:`round-trip<roundtrips>` when calling
      :meth:`LOB.size()` and :meth:`LOB.getchunksize()`.
    - Made the pool implementation LIFO to improve locality, reduce the number
      of times any session callback must be invoked, and allow connections to
      be timed out.
    - Removed packet for negotiating network services which are not supported
      in thin mode.
    - Removed unneeded packet for changing the password of the connected user.


Thick Mode Changes
++++++++++++++++++

#)  Raise a more meaningful error when an unsupported type in a JSON value is
    detected.
#)  Added support for the "signed int", "signed long" and "decimal128" scalar
    types in JSON (generally only seen when converting from MongoDB).
#)  Defer raising an exception when calling :meth:`Connection.gettype()`
    for a type containing an attribute or element with an unsupported data type
    until the first attempt to reference the attribute or element with the
    unsupported data type.
#)  Fixed bug when attempting to create bequeath connections when the DSN
    contains credentials.

Common Changes
++++++++++++++

#)  Improved type annotations.
#)  Added method :meth:`ConnectParams.parse_dsn_with_credentials()` for parsing
    a DSN that contains credentials.
#)  Error ``DPY-2038: element at index {index} does not exist`` is now raised
    whenever an element in a database collection is missing. Previously, thick
    mode raised ``DPI-1024: element at index {index} does not exist`` and thin
    mode raised ``KeyError`` or ``IndexError``.
#)  Error ``DPY-2039: given index {index} must be in the range of {min_index}
    to {max_index}`` is now raised whenever an element in a database collection
    is set outside the bounds of the collection. Previously, thick mode raised
    ``OCI-22165: given index [{index}] must be in the range of [{min_index}] to
    [{max_index}]`` and thin mode raised ``IndexError``.
#)  Error ``DPY-2040: parameters "batcherrors" and "arraydmlrowcounts" may only
    be true when used with insert, update, delete and merge statements`` is now
    raised when either of the parameters `batcherrors` and `arraydmlrowcounts`
    is set to the value `True` when calling :meth:`Cursor.executemany()`.
    Previously, thick mode raised ``DPI-1063: modes DPI_MODE_EXEC_BATCH_ERRORS
    and DPI_MODE_EXEC_ARRAY_DML_ROWCOUNTS can only be used with insert, update,
    delete and merge statements`` and thin mode raised
    ``ORA-03137: malformed TTC packet from client rejected``
    (`issue 128 <https://github.com/oracle/python-oracledb/issues/128>`__).
#)  Internal changes to ensure that errors taking place while raising
    exceptions are handled more gracefully.


oracledb 1.2.2 (January 2023)
-----------------------------

Thin Mode Changes
+++++++++++++++++

#)  Any exception raised while finding the operating system user for database
    logging is now ignored (`issue 112
    <https://github.com/oracle/python-oracledb/issues/112>`__).
#)  Fixed bug when binding OUT a NULL boolean value.
    (`issue 119 <https://github.com/oracle/python-oracledb/issues/119>`__).
#)  Fixed bug when getting a record type based on a table (%ROWTYPE)
    (`issue 123 <https://github.com/oracle/python-oracledb/issues/123>`__).
#)  Fixed bug when using a `select * from table` query and columns are added to
    the table
    (`issue 125 <https://github.com/oracle/python-oracledb/issues/125>`__).

Thick Mode Changes
++++++++++++++++++

#)  Fixed bug when attempting to create bequeath connections to a local
    database
    (`issue 114 <https://github.com/oracle/python-oracledb/issues/114>`__).

Common Changes
++++++++++++++

#)  Fixed bug when attempting to populate an array variable with too many
    elements.


oracledb 1.2.1 (December 2022)
------------------------------

Thin Mode Changes
+++++++++++++++++

#)  Fixed bug determining RETURNING binds in a SQL statement when RETURNING and
    INTO keywords are not separated by spaces, but are separated by other
    whitespace characters
    (`issue 104 <https://github.com/oracle/python-oracledb/issues/104>`__).
#)  Fixed bug determining bind variables when found between two comment blocks
    (`issue 105 <https://github.com/oracle/python-oracledb/issues/105>`__).

Thick Mode Changes
++++++++++++++++++

#)  Fixed bug creating a homogeneous connection pool with a proxy user
    (`issue 101 <https://github.com/oracle/python-oracledb/issues/101>`__).
#)  Fixed bug closing a SODA document cursor explicitly (instead of simply
    allowing it to be closed automatically when it goes out of scope).
#)  Fixed bug when calling :meth:`Subscription.registerquery()` with bind
    values.
#)  Fixed bug that caused :data:`Message.dbname` to always be the value `None`.

Common Changes
++++++++++++++

#)  Corrected ``__repr__()`` of connections to include the actual class name
    instead of a hard-coded ``oracledb``.


oracledb 1.2.0 (November 2022)
------------------------------

Thin Mode Changes
+++++++++++++++++

#)  Added support for binding and fetching data of type
    :data:`~oracledb.DB_TYPE_OBJECT`. Note that some of the error codes and
    messages have changed as a result: DPY errors are raised instead of ones
    specific to ODPI-C and OCI
    (`issue 43 <https://github.com/oracle/python-oracledb/issues/43>`__).
#)  Added support for fetching SYS.XMLTYPE data as strings. Note that unlike
    in Thick mode, fetching longer values does not require using
    ``XMLTYPE.GETCLOBVAL()``.
#)  Added support for using a wallet for one-way TLS connections, rather than
    requiring OS recognition of certificates
    (`issue 65 <https://github.com/oracle/python-oracledb/issues/65>`__).
#)  Added support for connecting to CMAN using ``(SOURCE_ROUTE=YES)`` in the
    connect string
    (`issue 81 <https://github.com/oracle/python-oracledb/issues/81>`__).
#)  Fixed bug when fetching nested cursors with more columns than the parent
    cursor.
#)  Fixed bug preventing a cursor from being reused after it was bound as a
    REF CURSOR to a PL/SQL block that closes it.
#)  Fixed bug preventing binding OUT data of type
    :data:`~oracledb.DB_TYPE_UROWID` that exceeds 3950 bytes in length.
#)  Fixed bug preventing correct parsing of connect descriptors with both
    ``ADDRESS`` and ``ADDRESS_LIST`` components at the same level.
#)  The complete connect string is now sent to the server instead of just the
    actual components being used. This is important for some configurations.
#)  Fixed bug resulting in an internal protocol error when handling database
    responses.
#)  Fixed bug when calling :meth:`Cursor.executemany()` with the `batcherrors`
    parameter set to `True` multiple times with each call resulting in at least
    one batch error.

Thick Mode Changes
++++++++++++++++++

#)  Connections acquired from a homogeneous pool now show the username and dsn
    to which they are connected in their repr().

Common Changes
++++++++++++++

#)  Added support for Python 3.11.
#)  Added attribute :attr:`DbObjectType.package_name` which contains the name
    of the package if the type is a PL/SQL type (otherwise, it will be `None`).
#)  Added sample for loading data from a CSV file.
#)  Improved test suite and documentation.


oracledb 1.1.1 (September 2022)
-------------------------------

Thin Mode Changes
+++++++++++++++++

#)  Fixed bug that prevented binding data of types
    :data:`~oracledb.DB_TYPE_ROWID` and :data:`~oracledb.DB_TYPE_UROWID`.
#)  Fixed bug that caused :meth:`Connection.is_healthy()` to return `True`
    after a connection has been killed.
#)  Internally, before a connection is returned from a pool, perform additional
    checks in order to avoid returning a dead connection from the pool.

Thick Mode Changes
++++++++++++++++++

#)  Fixed bug returning metadata of SODA documents inserted into a collection
    using :meth:`SodaCollection.saveAndGet()`.

Common Changes
++++++++++++++

#)  Fixed type checking errors
    (`issue 52 <https://github.com/oracle/python-oracledb/issues/52>`__).
#)  Enhanced type checking
    (`issue 54 <https://github.com/oracle/python-oracledb/issues/54>`__),
    (`issue 60 <https://github.com/oracle/python-oracledb/issues/60>`__).
#)  The mode of python-oracledb is now fixed only after a call to
    :meth:`oracledb.init_oracle_client()`, :meth:`oracledb.connect()` or
    :meth:`oracledb.create_pool()` has completed successfully
    (`issue 44 <https://github.com/oracle/python-oracledb/issues/44>`__).
#)  Improved test suite and documentation.


oracledb 1.1.0 (September 2022)
-------------------------------

Thin Mode Changes
+++++++++++++++++

#)  Added support for getting the LOB chunk size
    (`issue 14 <https://github.com/oracle/python-oracledb/issues/14>`__).
#)  The error `DPY-2030: LOB offset must be greater than zero` is now raised
    when the offset parameter to :func:`LOB.read()` is zero or negative
    (`issue 13 <https://github.com/oracle/python-oracledb/issues/13>`__).
#)  Internally, before a connection is returned from a pool, check for control
    packets from the server (which may inform the client that the connection
    needs to be closed and a new one established).
#)  Internally make use of the `TCP_NODELAY` socket option to remove delays
    in socket reads.
#)  Fixed bug when calling :func:`Cursor.parse()` multiple times with the same
    SQL statement.
#)  Fixed bug that prevented connecting to Oracle Database 12.1.0.1.
#)  Fixed bug that prevented the database error message from being returned
    when connecting to a database that the listener configuration file states
    exists but actually doesn't
    (`issue 51 <https://github.com/oracle/python-oracledb/issues/51>`__).
#)  The error `DPY-3016: python-oracledb thin mode cannot be used because the
    cryptography package is not installed` is now raised when the cryptography
    package is not installed, instead of an ImportError. This allows platforms
    that are not capable of building the cryptography package to still use
    Thick mode.
#)  Fixed bug that prevented the `full_code` attribute from being populated on
    the errors returned by :func:`Cursor.getbatcherrors()`.

Thick Mode Changes
++++++++++++++++++

#)  Added support for getting the message id of the AQ message which generated
    a notification.
#)  Added support for enqueuing and dequeing AQ messages as JSON.
#)  Added the ability to use `externalauth` as a connection parameter for
    standalone connections in addition to creating pools. For standalone
    connections, this parameter is optional.

Common Changes
++++++++++++++

#)  Added support for Azure Active Directory OAuth 2.0 and Oracle Cloud
    Infrastructure Identity and Access Management (IAM) token authentication
    via the new parameter `access_token` to :func:`oracledb.connect()` and
    :func:`oracledb.create_pool()`.
#)  Added method :func:`oracledb.is_thin_mode()` to support determining whether
    the driver is using Thin mode or not
    (`issue 16 <https://github.com/oracle/python-oracledb/issues/10>`__).
#)  Improved samples and documentation.


oracledb 1.0.3 (August 2022)
----------------------------

Thin Mode Changes
+++++++++++++++++

#)  The error `DPY-3015: password verifier type is not supported by
    python-oracledb in thin mode` is now raised when
    the database sends a password challenge with a verifier type that is not
    recognized, instead of `ORA-01017: invalid username/password`
    (`issue 26 <https://github.com/oracle/python-oracledb/issues/26>`__).
#)  Fixed bug with handling of redirect data returned by some SCAN listeners
    (`issue 39 <https://github.com/oracle/python-oracledb/issues/39>`__).
#)  Fixed bug with re-execution of SQL that requires a define, such as occurs
    when setting `oracledb.defaults.fetch_lobs` to the value `False`
    (`issue 41 <https://github.com/oracle/python-oracledb/issues/41>`__).
#)  Fixed bug that prevented cursors from implicit results sets from being
    closed.

Common Changes
++++++++++++++

#)  Fixed bug with the deferral of type assignment when creating variables for
    :func:`Cursor.executemany()`
    (`issue 35 <https://github.com/oracle/python-oracledb/issues/35>`__).


oracledb 1.0.2 (July 2022)
--------------------------

Thin Mode Changes
+++++++++++++++++

#)  Connecting to a database with national character set `UTF8` is now
    supported; an error is now raised only when the first attempt to use
    NCHAR, NVARCHAR2 or NCLOB data is made
    (`issue 16 <https://github.com/oracle/python-oracledb/issues/16>`__).
#)  Fixed a bug when calling `cursor.executemany()` with a PL/SQL statement and
    a single row of data
    (`issue 30 <https://github.com/oracle/python-oracledb/issues/30>`__).
#)  When using the connection parameter `https_proxy` while using protocol
    `tcp`, a more meaningful exception is now raised:
    `DPY-2029: https_proxy requires use of the tcps protocol`.
#)  Fixed a bug that caused TLS renegotiation to be skipped in some
    configurations, thereby causing the connection to fail to be established
    (https://github.com/oracle/python-oracledb/discussions/34).

Thick Mode Changes
++++++++++++++++++

#)  Fixed the ability to use external authentication with connection pools.

Common Changes
++++++++++++++

#)  The compiler flag ``-arch x86_64`` no longer needs to be explicitly
    specified when building from source code on macOS (Intel x86) without
    Universal Python binaries.
#)  Binary packages have been added for the Linux ARM 64-bit platform.
#)  Improved samples and documentation.


oracledb 1.0.1 (June 2022)
--------------------------

Thin Mode Changes
+++++++++++++++++

#)  Added support for multiple aliases in one entry in tnsnames.ora
    (`issue 3 <https://github.com/oracle/python-oracledb/issues/3>`__).
#)  Fixed connection retry count handling to work in cases where the database
    listener is running but the service is down
    (`issue 3 <https://github.com/oracle/python-oracledb/issues/3>`__).
#)  Return the same value for TIMESTAMP WITH TIME ZONE columns as thick mode
    (`issue 7 <https://github.com/oracle/python-oracledb/issues/7>`__).
#)  Fixed order in which bind data is sent to the server when LONG and
    non-LONG column data is interspersed
    (`issue 12 <https://github.com/oracle/python-oracledb/issues/12>`__).
#)  If an error occurs during the creation of a connection to the database, the
    error is wrapped by DPY-6005 (so that it can be caught with an exception
    handler on class oracledb.DatabaseError).
#)  Ensured that errors occurring during fetch are detected consistently.
#)  Fixed issue when fetching null values in implicit results.
#)  Small performance optimization when sending column metadata.

Thick Mode Changes
++++++++++++++++++

#)  Fixed the ability to create bequeath connections to a local database.
#)  Fixed issue fetching NCLOB columns with
    `oracledb.defaults.fetch_lobs = False`.

Common Changes
++++++++++++++

#)  Fixed issue where unconstrained numbers containing integer values would be
    fetched as floats when `oracledb.defaults.fetch_lobs = False`.
    (`issue 15 <https://github.com/oracle/python-oracledb/issues/15>`__).
#)  Ensured connection error messages contain the function name instead of
    ``wrapped()``.
#)  Improved samples, including adding a Dockerfile that starts a container
    with a running database and the samples.
#)  A binary package has been added for Python 3.7 on macOS (Intel x86).
#)  Improved documentation.


oracledb 1.0.0 (May 2022)
-------------------------

#)  Renamed cx_Oracle to python-oracledb.  See :ref:`upgradecomparison`.
#)  Python-oracledb is a 'Thin' driver by default that connects directly
    to Oracle Database.  Optional use of Oracle Client libraries enables a
    :ref:`'Thick' mode <enablingthick>` with some additional functionality.
    Both modes support the Python Database API v2.0 Specification.
#)  Added a :attr:`Connection.thin` attribute which shows whether the
    connection was established in the python-oracledb Thin mode or Thick mode.
#)  Creating connections or connection pools now requires :ref:`keyword
    parameters <connectdiffs>` be passed.  This brings python-oracledb into
    compliance with the Python Database API specification PEP 249.
#)  Threaded mode is now always enabled for standalone connections (Thick
    mode).
#)  The function :func:`oracledb.init_oracle_client()` must now always be
    called to load Oracle Client libraries, which enables Thick mode.
#)  Allow :meth:`oracledb.init_oracle_client` to be called multiple times in
    each process as long as the same parameters are used each time.
#)  Improved some :ref:`connection and binding error messages <errorhandling>`
    (Thin mode only).
#)  Added :ref:`oracledb.defaults <defaults>` containing attributes that can
    be used to adjust the default behavior of the python-oracledb driver.  In
    particular ``oracledb.defaults.fetch_lobs`` obsoletes the need for a
    :ref:`LOB type handler <directlobs>` .
#)  Added a :ref:`ConnectParams Class <connparam>` which provides the ability
    to define connection parameters in one place.
#)  Added a :ref:`PoolParams Class <poolparam>` which provides the ability to
    define pool parameters in one place.
#)  Added a :ref:`ConnectionPool Class <connpool>` which is equivalent to the
    SessionPool class previously used in cx_Oracle.  The new
    :func:`oracledb.create_pool()` function is now the preferred method for
    creating connection pools.
#)  Changed the default :func:`oracledb.create_pool()` ``getmode`` parameter
    value to :data:`~oracledb.POOL_GETMODE_WAIT` to remove potential transient
    errors when calling :meth:`ConnectionPool.acquire()` during pool growth.
#)  Connection pools in python-oracledb Thin mode support all :ref:`connection
    mode privileges <connection-authorization-modes>`.
#)  Added new :ref:`Two-phase commit <tpc>` functionality.
#)  Added :meth:`Connection.is_healthy()` to do a local check of a connection's
    health.
#)  Added a boolean parameter ``cache_statement`` to :meth:`Cursor.prepare()`,
    giving applications control over statement caching.
#)  Made improvements to statement cache invalidation (Thin mode only)
#)  Added a :attr:`~Messageproperties.recipient` attribute to support recipient
    lists in :ref:`Oracle Advanced Queuing <aq>`.
#)  Added a :attr:`~oracledb._Error.full_code` attribute to the Error object
    giving the top-level error prefix and the error number.
#)  Added a :data:`~oracledb.DB_TYPE_LONG_NVARCHAR` constant.


cx_Oracle 8.3 (November 2021)
-----------------------------

#)  Updated embedded ODPI-C to `version 4.3.0
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-4-3-november-4-2021>`__.
#)  Added official support for Python 3.10.
#)  Support for dequeuing messages from Oracle Transactional Event Queue (TEQ)
    queues was restored.
#)  Corrected calculation of attribute :data:`MessageProperties.msgid`. Note
    that the attribute is now also read only.
#)  Binary integer variables now explicitly convert values to integers (since
    implicit conversion to integer has become an error in Python 3.10) and
    values that are not `int`, `float` or `decimal.Decimal` are explicitly
    rejected.
#)  Improved samples and test suite.


cx_Oracle 8.2.1 (June 2021)
---------------------------

#)  Updated embedded ODPI-C to `version 4.2.1
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-4-2-1-june-1-2021>`__.
#)  Added support for caching the database version in pooled connections with
    Oracle Client 19 and earlier (later Oracle Clients handle this caching
    internally). This optimization eliminates a round-trip previously often
    required when reusing a pooled connection.
#)  Fixed a regression with error messages when creating a connection fails.
#)  Fixed crash when using the deprecated parameter name `keywordParameters`
    with :meth:`Cursor.callproc()`.
#)  Improved documentation and the test suite.


cx_Oracle 8.2 (May 2021)
------------------------

#)  Updated embedded ODPI-C to `version 4.2.0
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-4-2-may-18-2021>`__.
#)  Threaded mode is now always enabled when creating connection pools with
    ``cx_Oracle.SessionPool()``. Any `threaded` parameter value is ignored.
#)  Added ``SessionPool.reconfigure()`` to support pool reconfiguration.
    This method provides the ability to change properties such as the size of
    existing pools instead of having to restart the application or create a new
    pool.
#)  Added parameter `max_sessions_per_shard` to ``cx_Oracle.SessionPool()``
    to allow configuration of the maximum number of sessions per shard in the
    pool.  In addition, the attribute
    ``SessionPool.max_sessions_per_shard`` was added in order to permit
    making adjustments after the pool has been created. They are usable when
    using Oracle Client version 18.3 and higher.
#)  Added parameter `stmtcachesize` to ``cx_Oracle.connect()`` and
    ``cx_Oracle.SessionPool()`` in order to permit specifying the size of
    the statement cache during the creation of pools and standalone
    connections.
#)  Added parameter `ping_interval` to ``cx_Oracle.SessionPool()`` to
    specify the ping interval when acquiring pooled connections. In addition,
    the attribute ``SessionPool.ping_interval`` was added in order to
    permit making adjustments after the pool has been created.  In previous
    cx_Oracle releases a fixed ping interval of 60 seconds was used.
#)  Added parameter `soda_metadata_cache` to ``cx_Oracle.SessionPool()``
    for :ref:`SODA metadata cache <sodametadatacache>` support.  In addition,
    the attribute ``SessionPool.soda_metadata_cache`` was added in order to
    permit making adjustments after the pool has been created. This feature
    significantly improves the performance of methods
    :meth:`SodaDatabase.createCollection()` (when not specifying a value for
    the metadata parameter) and :meth:`SodaDatabase.openCollection()`. Caching
    is available when using Oracle Client version 21.3 and higher (or Oracle
    Client 19 from 19.11).
#)  Added support for supplying hints to SODA operations. A new non-terminal
    method :meth:`~SodaOperation.hint()` was added and a `hint` parameter was
    added to the methods :meth:`SodaCollection.insertOneAndGet()`,
    :meth:`SodaCollection.insertManyAndGet()` and
    :meth:`SodaCollection.saveAndGet()`. All of these require Oracle Client
    21.3 or higher (or Oracle Client 19 from 19.11).
#)  Added parameter `bypass_decode` to :meth:`Cursor.var()` in order to allow
    the `decode` step to be bypassed when converting data from Oracle Database
    into Python strings
    (`issue 385 <https://github.com/oracle/python-cx_Oracle/issues/385>`__).
    Initial work was done in `PR 549
    <https://github.com/oracle/python-cx_Oracle/pull/549>`__.
#)  Enhanced dead connection detection.  If an Oracle Database error indicates
    that a connection is no longer usable, the error `DPI-1080: connection was
    closed by ORA-%d` is now returned.  The `%d` will be the Oracle error
    causing the connection to be closed.  Using the connection after this will
    give `DPI-1010: not connected`.  This behavior also applies for
    :data:`Connection.call_timeout` errors that result in an unusable
    connection.
#)  Eliminated a memory leak when calling :meth:`SodaOperation.filter()` with a
    dictionary.
#)  The distributed transaction handle assosciated with the connection is now
    cleared on commit or rollback (`issue 530
    <https://github.com/oracle/python-cx_Oracle/issues/530>`__).
#)  Added a check to ensure that when setting variables or object attributes,
    the type of the temporary LOB must match the expected type.
#)  A small number of parameter, method, and attribute names were updated to
    follow the PEP 8 style guide. This brings better consistency to the
    cx_Oracle API. The old names are still usable but may be removed in a
    future release of cx_Oracle. See :ref:`_deprecations_8_2` for details.
#)  Improved the test suite.


cx_Oracle 8.1 (December 2020)
-----------------------------

#)  Updated embedded ODPI-C to `version 4.1.0
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-4-1-december-8-2020>`__.
#)  Added support for new JSON data type available in Oracle Client and
    Database 21 and higher.
#)  Dropped support for Python 3.5. Added support for Python 3.9.
#)  Added internal methods for getting/setting OCI attributes that are
    otherwise not supported by cx_Oracle. These methods should only be used as
    directed by Oracle.
#)  Minor code improvement supplied by Alex Henrie
    (`PR 472 <https://github.com/oracle/python-cx_Oracle/pull/472>`__).
#)  Builds are now done with setuptools and most metadata has moved from
    `setup.py` to `setup.cfg` in order to take advantage of Python packaging
    improvements.
#)  The ability to pickle/unpickle Database and API types has been restored.
#)  Tests can now be run with tox in order to automate testing of the different
    environments that are supported.
#)  The value of prefetchrows for REF CURSOR variables is now honored.
#)  Improved documentation, samples and test suite.


cx_Oracle 8.0.1 (August 2020)
-----------------------------

#)  Updated embedded ODPI-C to `version 4.0.2
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-4-0-2-august-31-2020>`__. This includes the fix for binding and
    fetching numbers with 39 or 40 decimal digits
    (`issue 459 <https://github.com/oracle/python-cx_Oracle/issues/459>`__).
#)  Added build metadata specifying that Python 3.5 and higher is required in
    order to avoid downloading and failing to install with Python 2. The
    exception message when running ``setup.py`` directly was updated to inform
    those using Python 2 to use version 7.3 instead.
#)  Documentation improvements.


cx_Oracle 8.0 (June 2020)
-------------------------

#)  Dropped support for Python 2.
#)  Updated embedded ODPI-C to `version 4.0.1
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-4-0-1-june-26-2020>`__.
#)  Reworked type management to clarify and simplify code

    - Added :ref:`constants <dbtypes>` for all database types. The database
      types ``cx_Oracle.DB_TYPE_BINARY_FLOAT``,
      ``cx_Oracle.DB_TYPE_INTERVAL_YM``, ``cx_Oracle.DB_TYPE_TIMESTAMP_LTZ``
      and ``cx_Oracle.DB_TYPE_TIMESTAMP_TZ`` are completely new. The other
      types were found in earlier releases under a different name. These types
      will be found in :data:`Cursor.description` and passed as the defaultType
      parameter to the :data:`Connection.outputtypehandler` and
      :data:`Cursor.outputtypehandler` functions.
    - Added :ref:`synonyms <dbtypesynonyms>` from the old type names to the new
      type names for backwards compatibility. They are deprecated and will be
      removed in a future version of cx_Oracle.
    - The DB API :ref:`constants <types>` are now a specialized constant that
      matches to the corresponding database types, as recommended by the DB
      API.
    - The variable attribute :data:`~Variable.type` now refers to one of the
      new database type constants if the variable does not contain objects
      (previously it was None in that case).
    - The attribute :data:`~LOB.type` was added to LOB values.
    - The attribute ``type`` was added to attributes of object types.
    - The attribute ``element_type`` was added to object types.
    - Object types now compare equal if they were created
      by the same connection or session pool and their schemas and names match.
    - All variables are now instances of the same class (previously each type
      was an instance of a separate variable type). The attribute
      :data:`~Variable.type` can be examined to determine the database type it
      is associated with.
    - The string representation of variables has changed to include the type
      in addition to the value.

#)  Added function ``cx_Oracle.init_oracle_client()`` in order to enable
    programmatic control of the initialization of the Oracle Client library.
#)  The default encoding for all character data is now UTF-8 and any character
    set specified in the environment variable ``NLS_LANG`` is ignored.
#)  Added functions :meth:`SodaCollection.save()`,
    :meth:`SodaCollection.saveAndGet()` and :meth:`SodaCollection.truncate()`
    available in Oracle Client 20 and higher.
#)  Added function :meth:`SodaOperation.fetchArraySize()` available in Oracle
    Client 19.5 and higher.
#)  Added attribute :attr:`Cursor.prefetchrows` to control the number of rows
    that the Oracle Client library fetches into internal buffers when a query
    is executed.
#)  Internally make use of new mode available in Oracle Client 20 and higher in
    order to avoid a round-trip when accessing :attr:`Connection.version` for
    the first time.
#)  Added support for starting up a database using a parameter file (PFILE),
    as requested
    (`issue 295 <https://github.com/oracle/python-cx_Oracle/issues/295>`__).
#)  Fixed overflow issue when calling :meth:`Cursor.getbatcherrors()` with
    row offsets exceeding 65536.
#)  Eliminated spurious error when accessing :attr:`Cursor.lastrowid` after
    executing an INSERT ALL statement.
#)  Miscellaneous improvements supplied by Alex Henrie (pull requests
    `419 <https://github.com/oracle/python-cx_Oracle/pull/419>`__,
    `420 <https://github.com/oracle/python-cx_Oracle/pull/420>`__,
    `421 <https://github.com/oracle/python-cx_Oracle/pull/421>`__,
    `422 <https://github.com/oracle/python-cx_Oracle/pull/422>`__,
    `423 <https://github.com/oracle/python-cx_Oracle/pull/423>`__,
    `437 <https://github.com/oracle/python-cx_Oracle/pull/437>`__ and
    `438 <https://github.com/oracle/python-cx_Oracle/pull/438>`__).
#)  Python objects bound to boolean variables are now converted to True or
    False based on whether they would be considered True or False in a Python
    if statement. Previously, only True was treated as True and all other
    Python values (including 1, 1.0, and "foo") were treated as False
    (pull request
    `435 <https://github.com/oracle/python-cx_Oracle/pull/435>`__).
#)  Documentation, samples and test suite improvements.


cx_Oracle 7.3 (December 2019)
-----------------------------

#)  Added support for Python 3.8.
#)  Updated embedded ODPI-C to `version 3.3
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-3-3-december-2-2019>`__.
#)  Added support for CQN and other subscription client initiated connections
    to the database (as opposed to the default server initiated connections)
    created by calling :meth:`Connection.subscribe()`.
#)  Added :attr:`support <Cursor.lastrowid>` for returning the rowid of the
    last row modified by an operation on a cursor (or None if no row was
    modified).
#)  Added support for setting the ``maxSessionsPerShard`` attribute when
    creating connection pools.
#)  Added check to ensure sharding key is specified when a super sharding key
    is specified.
#)  Improved error message when the Oracle Client library is loaded
    successfully but the attempt to detect the version of that library fails,
    either due to the fact that the library is too old or the method could not
    be called for some reason (`node-oracledb issue 1168
    <https://github.com/oracle/node-oracledb/issues/1168>`__).
#)  Adjusted support for creating a connection using an existing OCI service
    context handle. In order to avoid potential memory corruption and
    unsupported behaviors, the connection will now use the same encoding as the
    existing OCI service context handle when it was created.
#)  Added ``ORA-3156: OCI call timed out`` to the list of error messages that
    result in error DPI-1067.
#)  Adjusted samples and the test suite so that they can be run against Oracle
    Cloud databases.
#)  Fixed bug when attempting to create a scrollable cursor on big endian
    platforms like AIX on PPC.
#)  Eliminated reference leak and ensure that memory is properly initialized in
    case of error when using sharding keys.
#)  Eliminated reference leak when splitting the password and DSN components
    out of a full connect string.
#)  Corrected processing of DATE sharding keys (sharding requires a slightly
    different format to be passed to the server).
#)  Eliminated reference leak when
    :meth:`creating message property objects <Connection.msgproperties()>`.
#)  Attempting to use proxy authentication with a homogeneous pool will now
    raise a ``DatabaseError`` exception with the message
    ``DPI-1012: proxy authentication is not possible with homogeneous pools``
    instead of a ``ProgrammingError`` exception with the message
    ``pool is homogeneous. Proxy authentication is not possible.`` since this
    check is done by ODPI-C. An empty string (or None) for the user name will
    no longer generate an exception.
#)  Exception ``InterfaceError: not connected`` is now always raised when an
    operation is attempted with a closed connection. Previously, a number of
    different exceptions were raised depending on the operation.
#)  Added ``ORA-40479: internal JSON serializer error`` to the list of
    exceptions that result in ``cx_Oracle.IntegrityError``.
#)  Improved documentation.


cx_Oracle 7.2.3 (October 2019)
------------------------------

#)  Updated embedded ODPI-C to `version 3.2.2
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-3-2-2-october-1-2019>`__.
#)  Restored support for setting numeric bind variables with boolean values.
#)  Ensured that sharding keys are dedicated to the connection that is acquired
    using them in order to avoid possible hangs, crashes or unusual errors.
#)  Corrected support for PLS_INTEGER and BINARY_INTEGER types when used in
    PL/SQL records
    (`ODPI-C issue 112 <https://github.com/oracle/odpi/issues/112>`__).
#)  Improved documentation.


cx_Oracle 7.2.2 (August 2019)
-----------------------------

#)  Updated embedded ODPI-C to `version 3.2.1
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-3-2-1-august-12-2019>`__.
#)  A more meaningful error is now returned when calling
    :meth:`SodaCollection.insertMany()` with an empty list.
#)  A more meaningful error is now returned when calling
    :meth:`Subscription.registerquery()` with SQL that is not a SELECT
    statement.
#)  Eliminated segfault when a connection is closed after being created by a
    call to ``cx_Oracle.connect()`` with the parameter ``cclass`` set to
    a non-empty string.
#)  Added user guide documentation.
#)  Updated default connect strings to use 19c and XE 18c defaults.


cx_Oracle 7.2.1 (July 2019)
---------------------------

#)  Resolved ``MemoryError`` exception on Windows when using an output type
    handler
    (`issue 330 <https://github.com/oracle/python-cx_Oracle/issues/330>`__).
#)  Improved test suite and samples.
#)  Improved documentation.


cx_Oracle 7.2 (July 2019)
-------------------------

#)  Updated embedded ODPI-C to `version 3.2
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-3-2-july-1-2019>`__.
#)  Improved AQ support

    - added support for enqueue and dequeue of RAW payloads
    - added support for bulk enqueue and dequeue of messages
    - added new method :meth:`Connection.queue()` which creates a new
      :ref:`queue object <queue>` in order to simplify AQ usage
    - enhanced method :meth:`Connection.msgproperties()` to allow the writable
      properties of the newly created object to be initialized.
    - the original methods for enqueuing and dequeuing (Connection.deq(),
      Connection.deqoptions(), Connection.enq() and Connection.enqoptions())
      are now deprecated and will be removed in a future version.

#)  Removed preview status from existing SODA functionality. See
    `this tracking issue
    <https://github.com/oracle/python-cx_Oracle/issues/309>`__ for known issues
    with SODA.
#)  Added support for a preview of SODA bulk insert, available in Oracle Client
    18.5 and higher.
#)  Added support for setting LOB object attributes, as requested
    (`issue 299 <https://github.com/oracle/python-cx_Oracle/issues/299>`__).
#)  Added mode ``cx_Oracle.DEFAULT_AUTH`` as requested
    (`issue 293 <https://github.com/oracle/python-cx_Oracle/issues/293>`__).
#)  Added support for using the LOB prefetch length indicator in order to
    reduce the number of round trips when fetching LOBs and then subsequently
    calling :meth:`LOB.size()`, :meth:`LOB.getchunksize()` or
    :meth:`LOB.read()`. This is always enabled.
#)  Added support for types BINARY_INTEGER, PLS_INTEGER, ROWID, LONG and LONG
    RAW when used in PL/SQL.
#)  Eliminated deprecation of attribute :attr:`Subscription.id`. It is now
    populated with the value of ``REGID`` found in the database view
    ``USER_CHANGE_NOTIFICATION_REGS`` or the value of ``REG_ID`` found in the
    database view ``USER_SUBSCR_REGISTRATIONS``. For AQ subscriptions, the
    value is 0.
#)  Enabled PY_SSIZE_T_CLEAN, as required by Python 3.8
    (`issue 317 <https://github.com/oracle/python-cx_Oracle/issues/317>`__).
#)  Eliminated memory leak when fetching objects that are atomically null
    (`issue 298 <https://github.com/oracle/python-cx_Oracle/issues/298>`__).
#)  Eliminated bug when processing the string representation of numbers like
    1e-08 and 1e-09 (`issue 300
    <https://github.com/oracle/python-cx_Oracle/issues/300>`__).
#)  Improved error message when the parent cursor is closed before a fetch is
    attempted from an implicit result cursor.
#)  Improved test suite and samples.
#)  Improved documentation.


cx_Oracle 7.1.3 (April 2019)
----------------------------

#)  Updated to `ODPI-C 3.1.4
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-3-1-4-april-24-2019>`__.
#)  Added support for getting the row count for PL/SQL statements
    (`issue 285 <https://github.com/oracle/python-cx_Oracle/issues/285>`__).
#)  Corrected parsing of connect string so that the last @ symbol is searched
    for instead of the first @ symbol; otherwise, passwords containing an @
    symbol will result in the incorrect DSN being extracted
    (`issue 290 <https://github.com/oracle/python-cx_Oracle/issues/290>`__).
#)  Adjusted return value of cursor.callproc() to follow documentation (only
    positional arguments are returned since the order of keyword parameters
    cannot be guaranteed in any case)
    (`PR 287 <https://github.com/oracle/python-cx_Oracle/pull/287>`__).
#)  Corrected code getting sample and test parameters by user input when using
    Python 2.7.


cx_Oracle 7.1.2 (March 2019)
----------------------------

#)  Updated to `ODPI-C 3.1.3
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-3-1-3-march-12-2019>`__.
#)  Ensured that the strings "-0" and "-0.0" are correctly handled as zero
    values
    (`issue 274 <https://github.com/oracle/python-cx_Oracle/issues/274>`__).
#)  Eliminated error when startup and shutdown events are generated
    (`ODPI-C issue 102 <https://github.com/oracle/odpi/issues/102>`__).
#)  Enabled the types specified in :meth:`Cursor.setinputsizes()` and
    :meth:`Cursor.callfunc()` to be an object type in addition to a Python
    type, just like in :meth:`Cursor.var()`.
#)  Reverted changes to return decimal numbers when the numeric precision was
    too great to be returned accurately as a floating point number. This change
    had too great an impact on existing functionality and an output type
    handler can be used to return decimal numbers where that is desirable
    (`issue 279 <https://github.com/oracle/python-cx_Oracle/issues/279>`__).
#)  Eliminated discrepancies in character sets between an external connection
    handle and the newly created connection handle that references the external
    connection handle
    (`issue 273 <https://github.com/oracle/python-cx_Oracle/issues/273>`__).
#)  Eliminated memory leak when receiving messages received from subscriptions.
#)  Improved test suite and documentation.


cx_Oracle 7.1.1 (February 2019)
-------------------------------

#)  Updated to `ODPI-C 3.1.2
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-3-1-2-february-19-2019>`__.
#)  Corrected code for freeing CQN message objects when multiple queries are
    registered
    (`ODPI-C issue 96 <https://github.com/oracle/odpi/issues/96>`__).
#)  Improved error messages and installation documentation.


cx_Oracle 7.1 (February 2019)
-----------------------------

#)  Updated to `ODPI-C 3.1
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-3-1-january-21-2019>`__.
#)  Improved support for session tagging in session pools by allowing a
    session callback to be specified when creating a pool via
    ``cx_Oracle.SessionPool()``. Callbacks can be written in Python or in
    PL/SQL and can be used to improve performance by decreasing round trips to
    the database needed to set session state. Callbacks written in Python will
    be invoked for brand new connections (that have never been acquired from
    the pool before) or when the tag assigned to the connection doesn't match
    the one that was requested. Callbacks written in PL/SQL will only be
    invoked when the tag assigned to the connection doesn't match the one that
    was requested.
#)  Added attribute :attr:`Connection.tag` to provide access to the actual tag
    assigned to the connection. Setting this attribute will cause the
    connection to be retagged when it is released back to the pool.
#)  Added support for fetching SYS.XMLTYPE values as strings, as requested
    (`issue 14 <https://github.com/oracle/python-cx_Oracle/issues/14>`__).
    Note that this support is limited to the size of VARCHAR2 columns in the
    database (either 4000 or 32767 bytes).
#)  Added support for allowing the typename parameter in method
    :meth:`Cursor.var()` to be None or a valid object type created by the
    method :meth:`Connection.gettype()`, as requested
    (`issue 231 <https://github.com/oracle/python-cx_Oracle/issues/231>`__).
#)  Added support for getting and setting attributes of type RAW on Oracle
    objects, as requested
    (`ODPI-C issue 72 <https://github.com/oracle/odpi/issues/72>`__).
#)  Added support for performing external authentication with proxy for
    standalone connections.
#)  Added support for mixing integers, floating point and decimal values in
    data passed to :meth:`Cursor.executemany()`
    (`issue 241 <https://github.com/oracle/python-cx_Oracle/issues/241>`__).
    The error message raised when a value cannot be converted to an Oracle
    number was also improved.
#)  Adjusted fetching of numeric values so that no precision is lost. If an
    Oracle number cannot be represented by a Python floating point number a
    decimal value is automatically returned instead.
#)  Corrected handling of multiple calls to method
    :meth:`Cursor.executemany()` where all of the values in one of the columns
    passed to the first call are all None and a subsequent call has a value
    other than None in the same column
    (`issue 236 <https://github.com/oracle/python-cx_Oracle/issues/236>`__).
#)  Added additional check for calling :meth:`Cursor.setinputsizes()` with an
    empty dictionary in order to avoid the error "cx_Oracle.ProgrammingError:
    positional and named binds cannot be intermixed"
    (`issue 199 <https://github.com/oracle/python-cx_Oracle/issues/199>`__).
#)  Corrected handling of values that exceed the maximum value of a plain
    integer object on Python 2 on Windows
    (`issue 257 <https://github.com/oracle/python-cx_Oracle/issues/257>`__).
#)  Added error message when attempting external authentication with proxy
    without placing the user name in [] (proxy authentication was previously
    silently ignored).
#)  Exempted additional error messages from forcing a statement to be dropped
    from the cache
    (`ODPI-C issue 76 <https://github.com/oracle/odpi/issues/76>`__).
#)  Improved dead session detection when using session pools for Oracle Client
    12.2 and higher.
#)  Ensured that the connection returned from a pool after a failed ping (such
    as due to a killed session) is not itself marked as needing to be dropped
    from the pool.
#)  Eliminated memory leak under certain circumstances when pooled connections
    are released back to the pool.
#)  Eliminated memory leak when connections are dropped from the pool.
#)  Eliminated memory leak when calling :meth:`Connection.close()` after
    fetching collections from the database.
#)  Adjusted order in which memory is freed when the last references to SODA
    collections, documents, document cursors and collection cursors are
    released, in order to prevent a segfault under certain circumstances.
#)  Improved code preventing a statement from binding itself, in order to avoid
    a potential segfault under certain circumstances.
#)  Worked around OCI bug when attempting to free objects that are PL/SQL
    records, in order to avoid a potential segfault.
#)  Improved test suite and samples. Note that default passwords are no longer
    supplied. New environment variables can be set to specify passwords if
    desired, or the tests and samples will prompt for the passwords when
    needed. In addition, a Python script is now available to create and drop
    the schemas used for the tests and samples.
#)  Improved documentation.


cx_Oracle 7.0 (September 2018)
------------------------------

#)  Update to `ODPI-C 3.0
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-3-0-0-september-13-2018>`__.
#)  Added support for Oracle Client 18 libraries.
#)  Added support for SODA (as preview). See :ref:`SODA Database <sodadb>`,
    :ref:`SODA Collection <sodacoll>` and :ref:`SODA Document <sodadoc>` for
    more information.
#)  Added support for call timeouts available in Oracle Client 18.1 and
    higher. See :attr:`Connection.call_timeout`.
#)  Added support for getting the contents of a SQL collection object as a
    dictionary, where the keys are the indices of the collection and the values
    are the elements of the collection. See function :meth:`Object.asdict()`.
#)  Added support for closing a session pool via the function
    ``SessionPool.close()``. Once closed, further attempts to use any
    connection that was acquired from the pool will result in the error
    "DPI-1010: not connected".
#)  Added support for setting a LOB attribute of an object with a string or
    bytes (instead of requiring a temporary LOB to be created).
#)  Added support for the packed decimal type used by object attributes with
    historical types DECIMAL and NUMERIC
    (`issue 212 <https://github.com/oracle/python-cx_Oracle/issues/212>`__).
#)  On Windows, first attempt to load oci.dll from the same directory as
    the cx_Oracle module.
#)  SQL objects that are created or fetched from the database are now tracked
    and marked unusable when a connection is closed. This was done in order
    to avoid a segfault under certain circumstances.
#)  Re-enabled dead session detection functionality when using pools for Oracle
    Client 12.2 and higher in order to handle classes of connection errors such
    as resource profile limits.
#)  Improved error messages when the Oracle Client or Oracle Database need to
    be at a minimum version in order to support a particular feature.
#)  When a connection is used as a context manager, the connection is now
    closed when the block ends. Attempts to set
    ``cx_Oracle.__future__.ctx_mgr_close`` are now ignored.
#)  When a DML returning statement is executed, variables bound to it will
    return an array when calling :meth:`Variable.getvalue()`. Attempts to set
    ``cx_Oracle.__future__.dml_ret_array_val`` are now ignored.
#)  Support for Python 3.4 has been dropped.
#)  Added additional test cases.
#)  Improved documentation.


cx_Oracle 6.4.1 (July 2018)
---------------------------

#)  Update to `ODPI-C 2.4.2
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-2-4-2-july-9-2018>`__.

    - Avoid buffer overrun due to improper calculation of length byte when
      converting some negative 39 digit numbers from string to the internal
      Oracle number format
      (`ODPI-C issue 67 <https://github.com/oracle/odpi/issues/67>`__).

#)  Prevent error "cx_Oracle.ProgrammingError: positional and named binds
    cannot be intermixed" when calling cursor.setinputsizes() without any
    parameters and then calling cursor.execute() with named bind parameters
    (`issue 199 <https://github.com/oracle/python-cx_Oracle/issues/199>`__).


cx_Oracle 6.4 (July 2018)
-------------------------

#)  Update to `ODPI-C 2.4.1
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-2-4-1-july-2-2018>`__.

    - Added support for grouping subscriptions. See parameters groupingClass,
      groupingValue and groupingType to function
      :meth:`Connection.subscribe()`.
    - Added support for specifying the IP address a subscription should use
      instead of having the Oracle Client library determine the IP address on
      its own. See parameter ipAddress to function
      :meth:`Connection.subscribe()`.
    - Added support for subscribing to notifications when messages are
      available to dequeue in an AQ queue. The new constant
      ``cx_Oracle.SUBSCR_NAMESPACE_AQ`` should be passed to the namespace
      parameter of function :meth:`Connection.subscribe()` in order to get this
      functionality. Attributes :attr:`Message.queueName` and
      :attr:`Message.consumerName` will be populated in notification messages
      that are received when this namespace is used.
    - Added attribute :attr:`Message.registered` to let the notification
      callback know when the subscription that generated the notification is no
      longer registered with the database.
    - Added support for timed waits when acquiring a session from a session
      pool. Use the new constant ``cx_Oracle.SPOOL_ATTRVAL_TIMEDWAIT`` in
      the parameter getmode to function ``cx_Oracle.SessionPool()`` along
      with the new parameter ``waitTimeout``.
    - Added support for specifying the timeout and maximum lifetime session for
      session pools when they are created using function
      ``cx_Oracle.SessionPool()``. Previously the pool had to be created
      before these values could be changed.
    - Avoid memory leak when dequeuing from an empty queue.
    - Ensure that the row count for queries is reset to zero when the statement
      is executed
      (`issue 193 <https://github.com/oracle/python-cx_Oracle/issues/193>`__).
    - If the statement should be deleted from the statement cache, first check
      to see that there is a statement cache currently being used; otherwise,
      the error "ORA-24300: bad value for mode" will be raised under certain
      conditions.

#)  Added support for using the cursor as a context manager
    (`issue 190 <https://github.com/oracle/python-cx_Oracle/issues/190>`__).
#)  Added parameter "encodingErrors" to function :meth:`Cursor.var()` in order
    to add support for specifying the "errors" parameter to the decode() that
    takes place internally when fetching strings from the database
    (`issue 162 <https://github.com/oracle/python-cx_Oracle/issues/162>`__).
#)  Added support for specifying an integer for the parameters argument to
    :meth:`Cursor.executemany()`. This allows for batch execution when no
    parameters are required or when parameters have previously been bound. This
    replaces Cursor.executemanyprepared() (which is now deprecated and will be
    removed in cx_Oracle 7).
#)  Adjusted the binding of booleans so that outside of PL/SQL they are bound
    as integers
    (`issue 181 <https://github.com/oracle/python-cx_Oracle/issues/181>`__).
#)  Added support for binding decimal.Decimal values to cx_Oracle.NATIVE_FLOAT
    as requested
    (`issue 184 <https://github.com/oracle/python-cx_Oracle/issues/184>`__).
#)  Added checks on passing invalid type parameters to methods
    :meth:`Cursor.arrayvar()`, :meth:`Cursor.callfunc()` and
    :meth:`Cursor.setinputsizes()`.
#)  Corrected handling of cursors and rowids in DML Returning statements.
#)  Added sample from David Lapp demonstrating the use of GeoPandas with
    SDO_GEOMETRY and a sample for demonstrating the use of REF cursors.
#)  Adjusted samples and documentation for clarity.
#)  Added additional test cases.


cx_Oracle 6.3.1 (May 2018)
--------------------------

#)  Update to `ODPI-C 2.3.2
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-2-3-2-may-7-2018>`__.

    - Ensure that a call to unregister a subscription only occurs if the
      subscription is still registered.
    - Ensure that before a statement is executed any buffers used for DML
      returning statements are reset.

#)  Ensure that behavior with ``cx_Oracle.__future__.dml_ret_array_val`` not
    set or False is the same as the behavior in cx_Oracle 6.2 (`issue 176
    <https://github.com/oracle/python-cx_Oracle/issues/176>`__).


cx_Oracle 6.3 (April 2018)
--------------------------

#)  Update to `ODPI-C 2.3.1
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-2-3-1-april-25-2018>`__.

    - Fixed binding of LONG data (values exceeding 32KB) when using the
      function :meth:`Cursor.executemany()`.
    - Added code to verify that a CQN subscription is open before permitting it
      to be used. Error "DPI-1060: subscription was already closed" will now be
      raised if an attempt is made to use a subscription that was closed
      earlier.
    - Stopped attempting to unregister a CQN subscription before it was
      completely registered. This prevents errors encountered during
      registration from being masked by an error stating that the subscription
      has not been registered!
    - Added error "DPI-1061: edition is not supported when a new password is
      specified" to clarify the fact that specifying an edition and a new
      password at the same time is not supported when creating a connection.
      Previously the edition value was simply ignored.
    - Improved error message when older OCI client libraries are being used
      that don't have the method OCIClientVersion().
    - Fixed the handling of ANSI types REAL and DOUBLE PRECISION as
      implemented by Oracle. These types are just subtypes of NUMBER and are
      different from BINARY_FLOAT and BINARY_DOUBLE
      (`issue 163 <https://github.com/oracle/python-cx_Oracle/issues/163>`__).
    - Fixed support for true heterogeneous session pools that use different
      user/password combinations for each session acquired from the pool.
    - Added error message indicating that setting either of the parameters
      arraydmlrowcounts and batcherrors to True in :meth:`Cursor.executemany()`
      is only supported with insert, update, delete and merge statements.

#)  Fixed support for getting the OUT values of bind variables bound to a DML
    Returning statement when calling the function :meth:`Cursor.executemany()`.
    Note that the attribute dml_ret_array_val in ``cx_Oracle.__future__``
    must be set to True first.
#)  Added support for binding integers and floats as ``cx_Oracle.NATIVE_FLOAT``.
#)  A ``cx_Oracle._Error`` object is now the value of all cx_Oracle
    exceptions raised by cx_Oracle.
    (`issue 51 <https://github.com/oracle/python-cx_Oracle/issues/51>`__).
#)  Added support for building cx_Oracle with a pre-compiled version of ODPI-C,
    as requested
    (`issue 103 <https://github.com/oracle/python-cx_Oracle/issues/103>`__).
#)  Default values are now provided for all parameters to
    ``cx_Oracle.SessionPool()``.
#)  Improved error message when an unsupported Oracle type is encountered.
#)  The Python GIL is now prevented from being held while performing a round
    trip for the call to get the attribute :attr:`Connection.version`
    (`issue 158 <https://github.com/oracle/python-cx_Oracle/issues/158>`__).
#)  Added check for the validity of the year for Python 2.x since it doesn't do
    that itself like Python 3.x does
    (`issue 166 <https://github.com/oracle/python-cx_Oracle/issues/166>`__).
#)  Adjusted documentation to provide additional information on the use of
    :meth:`Cursor.executemany()` as requested
    (`issue 153 <https://github.com/oracle/python-cx_Oracle/issues/153>`__).
#)  Adjusted documentation to state that batch errors and array DML row counts
    can only be used with insert, update, delete and merge statements
    (`issue 31 <https://github.com/oracle/python-cx_Oracle/issues/31>`__).
#)  Updated tutorial to import common connection information from files in
    order to make setup a bit more generic.


cx_Oracle 6.2.1 (March 2018)
----------------------------

#)  Make sure cxoModule.h is included in the source archive
    (`issue 155 <https://github.com/oracle/python-cx_Oracle/issues/155>`__).


cx_Oracle 6.2 (March 2018)
--------------------------

#)  Update to `ODPI-C 2.2.1
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-2-2-1-march-5-2018>`__.

    - eliminate error "DPI-1054: connection cannot be closed when open
      statements or LOBs exist" (`issue 138
      <https://github.com/oracle/python-cx_Oracle/issues/138>`__).
    - avoid a round trip to the database when a connection is released back to
      the pool by preventing a rollback from being called when no transaction
      is in progress.
    - improve error message when the use of bind variables is attempted with
      DLL statements, which is not supported by Oracle.
    - if an Oracle object is retrieved from an attribute of another Oracle
      object or a collection, prevent the "owner" from being destroyed until
      the object that was retrieved has itself been destroyed.
    - correct handling of boundary numbers 1e126 and -1e126
    - eliminate memory leak when calling :meth:`Connection.enq()` and
      :meth:`Connection.deq()`
    - eliminate memory leak when setting NCHAR and NVARCHAR attributes of
      objects.
    - eliminate memory leak when fetching collection objects from the database.

#)  Added support for creating a temporary CLOB, BLOB or NCLOB via the method
    :meth:`Connection.createlob()`.
#)  Added support for binding a LOB value directly to a cursor.
#)  Added support for closing the connection when reaching the end of a
    ``with`` code block controlled by the connection as a context manager, but
    in a backwards compatible way
    (`issue 113 <https://github.com/oracle/python-cx_Oracle/issues/113>`__).
    See ``cx_Oracle.__future__`` for more information.
#)  Reorganized code to simplify continued maintenance and consolidate
    transformations to/from Python objects.
#)  Ensure that the number of elements in the array is not lost when the
    buffer size is increased to accommodate larger strings.
#)  Corrected support in Python 3.x for cursor.parse() by permitting a string
    to be passed, instead of incorrectly requiring a bytes object.
#)  Eliminate reference leak with LOBs acquired from attributes of objects or
    elements of collections.
#)  Eliminate reference leak when extending an Oracle collection.
#)  Documentation improvements.
#)  Added test cases to the test suite.


cx_Oracle 6.1 (December 2017)
-----------------------------

#)  Update to `ODPI-C 2.1
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-2-1-december-12-2017>`__.

    - Support was added for accessing sharded databases via sharding keys (new
      in Oracle 12.2). NOTE: the underlying OCI library has a bug when using
      standalone connections. There is a small memory leak proportional to the
      number of connections created/dropped. There is no memory leak when using
      session pools, which is recommended.
    - Added options for authentication with SYSBACKUP, SYSDG, SYSKM and SYSRAC,
      as requested (`issue 101
      <https://github.com/oracle/python-cx_Oracle/issues/101>`__).
    - Attempts to release statements or free LOBs after the connection has been
      closed (by, for example, killing the session) are now prevented.
    - An error message was added when specifying an edition and a connection
      class since this combination is not supported.
    - Attempts to close the session for connections created with an external
      handle are now prevented.
    - Attempting to ping a database earlier than 10g results in ORA-1010:
      invalid OCI operation, but that implies a response from the database and
      therefore a successful ping, so treat it that way!
      (see `<https://github.com/rana/ora/issues/224>`__ for more information).
    - Support was added for converting numeric values in an object type
      attribute to integer and text, as requested (`ODPI-C issue 35
      <https://github.com/oracle/odpi/issues/35>`__).
    - Setting attributes :attr:`DeqOptions.msgId` and
      :attr:`MessageProperties.msgId` now works as expected.
    - The overflow check when using double values (Python floats) as input
      to float attributes of objects or elements of collections was removed as
      it didn't work anyway and is a well-known issue that cannot be prevented
      without removing desired functionality. The developer should ensure that
      the source value falls within the limits of floats, understand the
      consequent precision loss or use a different data type.
    - Variables of string/raw types are restricted to 2 bytes less than 1 GB
      (1,073,741,822 bytes), since OCI cannot handle more than that currently.
    - Support was added for identifying the id of the transaction which spawned
      a CQN subscription message, as requested
      (`ODPI-C issue 32 <https://github.com/oracle/odpi/issues/32>`__).
    - Corrected use of subscription port number (`issue 115
      <https://github.com/oracle/python-cx_Oracle/issues/115>`__).
    - Problems reported with the usage of FormatMessage() on Windows were
      addressed (`ODPI-C issue 47
      <https://github.com/oracle/odpi/issues/47>`__).
    - On Windows, if oci.dll cannot be loaded because it is the wrong
      architecture (32-bit vs 64-bit), attempt to find the offending DLL and
      include the full path of the DLL in the message, as suggested.
      (`ODPI-C issue 49 <https://github.com/oracle/odpi/issues/49>`__).
    - Force OCI prefetch to always use the value 2; the OCI default is 1 but
      setting the ODPI-C default to 2 ensures that single row fetches don't
      require an extra round trip to determine if there are more rows to fetch;
      this change also reduces the potential memory consumption when
      fetchArraySize was set to a large value and also avoids performance
      issues discovered with larger values of prefetch.

#)  Fix build with PyPy 5.9.0-alpha0 in libpython mode
    (`PR 54 <https://github.com/oracle/python-cx_Oracle/pull/54>`__).
#)  Ensure that the edition is passed through to the database when a session
    pool is created.
#)  Corrected handling of Python object references when an invalid keyword
    parameter is passed to ``cx_Oracle.SessionPool()``.
#)  Corrected handling of :attr:`Connection.handle` and the handle parameter
    to ``cx_Oracle.connect()`` on Windows.
#)  Documentation improvements.
#)  Added test cases to the test suite.


cx_Oracle 6.0.3 (November 2017)
-------------------------------

#)  Update to `ODPI-C 2.0.3
    <https://oracle.github.io/odpi/doc/releasenotes.html#
    version-2-0-3-november-6-2017>`__.

    - Prevent use of uninitialized data in certain cases (`issue 77
      <https://github.com/oracle/python-cx_Oracle/issues/77>`__).
    - Attempting to ping a database earlier than 10g results in error
      "ORA-1010: invalid OCI operation", but that implies a response from the
      database and therefore a successful ping, so treat it that way!
    - Correct handling of conversion of some numbers to NATIVE_FLOAT.
    - Prevent use of NaN with Oracle numbers since it produces corrupt data
      (`issue 91 <https://github.com/oracle/python-cx_Oracle/issues/91>`__).
    - Verify that Oracle objects bound to cursors, fetched from cursors, set in
      object attributes or appended to collection objects are of the correct
      type.
    - Correct handling of NVARCHAR2 when used as attributes of Oracle objects
      or as elements of collections.

#)  Ensure that a call to setinputsizes() with an invalid type prior to a call
    to executemany() does not result in a type error, but instead gracefully
    ignores the call to setinputsizes() as required by the DB API
    (`issue 75 <https://github.com/oracle/python-cx_Oracle/issues/75>`__).
#)  Check variable array size when setting variable values and raise
    IndexError, as is already done for getting variable values.


cx_Oracle 6.0.2 (August 2017)
-----------------------------

#)  Update to `ODPI-C 2.0.2
    <https://oracle.github.io/odpi/doc/releasenotes.html
    #version-2-0-2-august-30-2017>`__.

    - Don't prevent connection from being explicitly closed when a fatal error
      has taken place (`issue 67
      <https://github.com/oracle/python-cx_Oracle/issues/67>`__).
    - Correct handling of objects when dynamic binding is performed.
    - Process deregistration events without an error.
    - Eliminate memory leak when creating objects.

#)  Added missing type check to prevent coercion of decimal to float
    (`issue 68 <https://github.com/oracle/python-cx_Oracle/issues/68>`__).
#)  On Windows, sizeof(long) = 4, not 8, which meant that integers between 10
    and 18 digits were not converted to Python correctly
    (`issue 70 <https://github.com/oracle/python-cx_Oracle/issues/70>`__).
#)  Eliminate memory leak when repeatedly executing the same query.
#)  Eliminate segfault when attempting to reuse a REF cursor that has been
    closed.
#)  Updated documentation.


cx_Oracle 6.0.1 (August 2017)
-----------------------------

#)  Update to `ODPI-C 2.0.1
    <https://oracle.github.io/odpi/doc/releasenotes.html
    #version-2-0-1-august-18-2017>`__.

    - Ensure that queries registered via :meth:`Subscription.registerquery()`
      do not prevent the associated connection from being closed
      (`ODPI-C issue 27 <https://github.com/oracle/odpi/issues/27>`__).
    - Deprecated attribute :attr:`Subscription.id` as it was never intended to
      be exposed (`ODPI-C issue 28
      <https://github.com/oracle/odpi/issues/28>`__). It will be dropped in
      version 6.1.
    - Add support for DML Returning statements that require dynamically
      allocated variable data (such as CLOBs being returned as strings).

#)  Correct packaging of Python 2.7 UCS4 wheels on Linux
    (`issue 64 <https://github.com/oracle/python-cx_Oracle/issues/64>`__).
#)  Updated documentation.


cx_Oracle 6.0 (August 2017)
---------------------------

#)  Update to `ODPI-C 2.0 <https://oracle.github.io/odpi/doc/releasenotes.html
    #version-2-0-august-14-2017>`__.

    -   Prevent closing the connection when there are any open statements or
        LOBs and add new error "DPI-1054: connection cannot be closed when open
        statements or LOBs exist" when this situation is detected; this is
        needed to prevent crashes under certain conditions when statements or
        LOBs are being acted upon while at the same time (in another thread) a
        connection is being closed; it also prevents leaks of statements and
        LOBs when a connection is returned to a session pool.
    -   On platforms other than Windows, if the regular method for loading the
        Oracle Client libraries fails, try using $ORACLE_HOME/lib/libclntsh.so
        (`ODPI-C issue 20 <https://github.com/oracle/odpi/issues/20>`__).
    -   Use the environment variable ``DPI_DEBUG_LEVEL`` at runtime, not compile
        time.
    -   Added support for DPI_DEBUG_LEVEL_ERRORS (reports errors and has the
        value 8) and DPI_DEBUG_LEVEL_SQL (reports prepared SQL statement text
        and has the value 16) in order to further improve the ability to debug
        issues.
    -   Correct processing of :meth:`Cursor.scroll()` in some circumstances.

#)  Delay initialization of the ODPI-C library until the first standalone
    connection or session pool is created so that manipulation of the
    environment variable ``NLS_LANG`` can be performed after the module has been
    imported; this also has the added benefit of reducing the number of errors
    that can take place when the module is imported.
#)  Prevent binding of null values from generating the exception "ORA-24816:
    Expanded non LONG bind data supplied after actual LONG or LOB column" in
    certain circumstances
    (`issue 50 <https://github.com/oracle/python-cx_Oracle/issues/50>`__).
#)  Added information on how to run the test suite
    (`issue 33 <https://github.com/oracle/python-cx_Oracle/issues/33>`__).
#)  Documentation improvements.


cx_Oracle 6.0 rc 2 (July 2017)
------------------------------

#)  Update to `ODPI-C rc 2 <https://oracle.github.io/odpi/doc/releasenotes.html
    #version-2-0-0-rc-2-july-20-2017>`__.

    -   Provide improved error message when OCI environment cannot be created,
        such as when the oraaccess.xml file cannot be processed properly.
    -   On Windows, convert system message to Unicode first, then to UTF-8;
        otherwise, the error message returned could be in a mix of encodings
        (`issue 40 <https://github.com/oracle/python-cx_Oracle/issues/40>`__).
    -   Corrected support for binding decimal values in object attribute values
        and collection element values.
    -   Corrected support for binding PL/SQL boolean values to PL/SQL
        procedures with Oracle client 11.2.

#)  Define exception classes on the connection object in addition to at module
    scope in order to simplify error handling in multi-connection environments,
    as specified in the Python DB API.
#)  Ensure the correct encoding is used for setting variable values.
#)  Corrected handling of CLOB/NCLOB when using different encodings.
#)  Corrected handling of TIMESTAMP WITH TIME ZONE attributes on objects.
#)  Ensure that the array position passed to var.getvalue() does not exceed the
    number of elements allocated in the array.
#)  Reworked test suite and samples so that they are independent of each other
    and so that the SQL scripts used to create/drop schemas are easily adjusted
    to use different schema names, if desired.
#)  Updated DB API test suite stub to support Python 3.
#)  Added additional test cases and samples.
#)  Documentation improvements.


cx_Oracle 6.0 rc 1 (June 2017)
------------------------------

#)  Update to `ODPI-C rc 1 <https://oracle.github.io/odpi/doc/releasenotes.html
    #version-2-0-0-rc-1-june-16-2017>`__.
#)  The method :meth:`Cursor.setoutputsize` no longer needs to do anything,
    since ODPI-C automatically manages buffer sizes of LONG and LONG RAW
    columns.
#)  Handle case when both precision and scale are zero, as occurs when
    retrieving numeric expressions (`issue 34
    <https://github.com/oracle/python-cx_Oracle/issues/34>`__).
#)  OCI requires that both encoding and nencoding have values or that both
    encoding and encoding do not have values. These parameters are used in
    functions ``cx_Oracle.connect()`` and ``cx_Oracle.SessionPool()``. The
    missing value is set to its default value if one of the values is set and
    the other is not (`issue 36
    <https://github.com/oracle/python-cx_Oracle/issues/36>`__).
#)  Permit use of both string and unicode for Python 2.7 for creating session
    pools and for changing passwords (`issue 23
    <https://github.com/oracle/python-cx_Oracle/issues/23>`__).
#)  Corrected handling of BFILE LOBs.
#)  Add script for dropping test schemas.
#)  Documentation improvements.


cx_Oracle 6.0 beta 2 (May 2017)
-------------------------------

#)  Added support for getting/setting attributes of objects or element values
    in collections that contain LOBs, BINARY_FLOAT values, BINARY_DOUBLE values
    and NCHAR and NVARCHAR2 values. The error message for any types that are
    not supported has been improved as well.
#)  Enable temporary LOB caching in order to avoid disk I/O as
    `suggested <https://github.com/oracle/odpi/issues/10>`__.
#)  Added support for setting the debug level in ODPI-C, if desirable, by
    setting environment variable ``DPI_DEBUG_LEVEL`` prior to building cx_Oracle.
#)  Correct processing of strings in :meth:`Cursor.executemany` when a
    larger string is found after a shorter string in the list of data bound to
    the statement.
#)  Correct handling of long Python integers that cannot fit inside a 64-bit C
    integer (`issue 18
    <https://github.com/oracle/python-cx_Oracle/issues/18>`__).
#)  Correct creation of pool using external authentication.
#)  Handle edge case when an odd number of zeroes trail the decimal point in a
    value that is effectively zero (`issue 22
    <https://github.com/oracle/python-cx_Oracle/issues/22>`__).
#)  Prevent segfault under load when the attempt to create an error fails.
#)  Eliminate resource leak when a standalone connection or pool is freed.
#)  Correct `typo <https://github.com/oracle/python-cx_Oracle/issues/24>`__.
#)  Correct handling of REF cursors when the array size is manipulated.
#)  Prevent attempts from binding the cursor being executed to itself.
#)  Correct reference count handling of parameters when creating a cursor.
#)  Correct determination of the names of the bind variables in prepared SQL
    statements (which behaves a little differently from PL/SQL statements).


cx_Oracle 6.0 beta 1 (April 2017)
---------------------------------

#)  Simplify building cx_Oracle considerably by use of
    `ODPI-C <https://oracle.github.io/odpi>`__. This means that cx_Oracle can
    now be built without Oracle Client header files or libraries and that at
    runtime cx_Oracle can adapt to Oracle Client 11.2, 12.1 or 12.2 libraries
    without needing to be rebuilt. This also means that wheels can now be
    produced and installed via pip.
#)  Added attribute ``SessionPool.stmtcachesize`` to support getting and
    setting the default statement cache size for connections in the pool.
#)  Added attribute :attr:`Connection.dbop` to support setting the database
    operation that is to be monitored.
#)  Added attribute :attr:`Connection.handle` to facilitate testing the
    creation of a connection using a OCI service context handle.
#)  Added parameters tag and matchanytag to the ``cx_Oracle.connect()``
    and ``SessionPool.acquire()`` methods and added parameters tag and retag
    to the ``SessionPool.release`` method in order to support session
    tagging.
#)  Added parameter edition to the ``cx_Oracle.SessionPool()`` method.
#)  Added support for
    `universal rowids <https://github.com/oracle/python-cx_Oracle/blob/main/
    samples/universal_rowids.py>`__.
#)  Added support for `DML Returning of multiple rows
    <https://github.com/oracle/python-cx_Oracle/blob/main/samples/
    dml_returning_multiple_rows.py>`__.
#)  Added attributes :attr:`Variable.actualElements` and
    :attr:`Variable.values` to variables.
#)  Added parameters region, sharding_key and super_sharding_key to the
    ``cx_Oracle.makedsn()`` method to support connecting to a sharded
    database (new in Oracle Database 12.2).
#)  Added support for smallint and float data types in Oracle objects, as
    `requested <https://github.com/oracle/python-cx_Oracle/issues/4>`__.
#)  An exception is no longer raised when a collection is empty for methods
    :meth:`Object.first()` and :meth:`Object.last()`. Instead, the value None
    is returned to be consistent with the methods :meth:`Object.next()` and
    :meth:`Object.prev()`.
#)  If the environment variables NLS_LANG and NLS_NCHAR are being used, they
    must be set before the module is imported. Using the encoding and nencoding
    parameters to the ``cx_Oracle.connect()`` and
    ``cx_Oracle.SessionPool()`` methods is a simpler alternative to setting
    these environment variables.
#)  Removed restriction on fetching LOBs across round trips to the database
    (eliminates error "LOB variable no longer valid after subsequent fetch").
#)  Removed requirement for specifying a maximum size when fetching LONG or
    LONG raw columns. This also allows CLOB, NCLOB, BLOB and BFILE columns to
    be fetched as strings or bytes without needing to specify a maximum size.
#)  Dropped deprecated parameter twophase from the ``cx_Oracle.connect()``
    method. Applications should set the :attr:`Connection.internal_name` and
    :attr:`Connection.external_name` attributes instead to a value appropriate
    to the application.
#)  Dropped deprecated parameters action, module and clientinfo from the
    ``cx_Oracle.connect()`` method. The appcontext parameter should be used
    instead as shown in this `sample <https://github.com/oracle/
    python-cx_Oracle/blob/main/samples/app_context.py>`__.
#)  Dropped deprecated attribute numbersAsString from
    :ref:`cursor objects <cursorobj>`. Use an output type handler instead as
    shown in this `sample <https://github.com/oracle/python-cx_Oracle/blob/
    main/samples/return_numbers_as_decimals.py>`__.
#)  Dropped deprecated attributes cqqos and rowids from
    :ref:`subscription objects <subscrobj>`. Use the qos attribute instead as
    shown in this `sample <https://github.com/oracle/python-cx_Oracle/blob/
    main/samples/cqn.py>`__.
#)  Dropped deprecated parameters cqqos and rowids from the
    :meth:`Connection.subscribe()` method. Use the qos parameter instead as
    shown in this `sample <https://github.com/oracle/python-cx_Oracle/blob/
    main/samples/cqn.py>`__.


cx_Oracle 5.3 (March 2017)
--------------------------

#)  Added support for Python 3.6.
#)  Dropped support for Python versions earlier than 2.6.
#)  Dropped support for Oracle clients earlier than 11.2.
#)  Added support for
    :meth:`fetching implicit results<Cursor.getimplicitresults()>`
    (available in Oracle 12.1)
#)  Added support for :attr:`Transaction Guard <Connection.ltxid>` (available
    in Oracle 12.1).
#)  Added support for setting the maximum lifetime of pool connections
    (available in Oracle 12.1).
#)  Added support for large row counts (larger than 2 ** 32, available in
    Oracle 12.1)
#)  Added support for :meth:`advanced queuing <Connection.deq()>`.
#)  Added support for :meth:`scrollable cursors <Cursor.scroll()>`.
#)  Added support for :attr:`edition based redefinition <Connection.edition>`.
#)  Added support for :meth:`creating <ObjectType.newobject()>`, modifying and
    binding user defined types and collections.
#)  Added support for creating, modifying and binding PL/SQL records and
    collections (available in Oracle 12.1).
#)  Added support for binding :data:`native integers <cx_Oracle.NATIVE_INT>`.
#)  Enabled statement caching.
#)  Removed deprecated variable attributes maxlength and allocelems.
#)  Corrected support for setting the encoding and nencoding parameters when
    :meth:`creating a connection <cx_Oracle.Connection>` and added support for
    setting these when creating a session pool. These can now be used instead
    of setting the environment variables ``NLS_LANG`` and ``NLS_NCHAR``.
#)  Use None instead of 0 for items in the :attr:`Cursor.description` attribute
    that do not have any validity.
#)  Changed driver name to match informal driver name standard used by Oracle
    for other drivers.
#)  Add check for maximum of 10,000 parameters when calling a stored procedure
    or function in order to prevent a possible improper memory access from
    taking place.
#)  Removed -mno-cygwin compile flag since it is no longer used in newer
    versions of the gcc compiler for Cygwin.
#)  Simplified test suite by combining Python 2 and 3 scripts into one script
    and separated out 12.1 features into a single script.
#)  Updated samples to use code that works on both Python 2 and 3.
#)  Added support for pickling/unpickling error objects
    (Bitbucket Issue #23).
#)  Dropped support for callbacks on OCI functions.
#)  Removed deprecated types UNICODE, FIXED_UNICODE and LONG_UNICODE (use
    NCHAR, FIXED_NCHAR and LONG_NCHAR instead).
#)  Increased default array size to 100 (from 50) to match other drivers.
#)  Added support for setting the :attr:`~Connection.internal_name` and
    :attr:`~Connection.external_name` on the connection directly. The use of
    the twophase parameter is now deprecated.  Applications should set the
    internal_name and external_name attributes directly to a value appropriate
    to the application.
#)  Added support for using application context when
    :meth:`creating a connection <cx_Oracle.Connection>`. This should be used
    in preference to the module, action and clientinfo parameters which are now
    deprecated.
#)  Reworked database change notification and continuous query notification to
    more closely align with the PL/SQL implementation and prepare for sending
    notifications for AQ messages. The following changes were made:

    - added constant ``cx_Oracle.SUBSCR_QOS_BEST_EFFORT`` to replace
      deprecated constant SUBSCR_CQ_QOS_BEST_EFFORT
    - added constant ``cx_Oracle.SUBSCR_QOS_QUERY`` to replace
      deprecated constant SUBSCR_CQ_QOS_QUERY
    - added constant ``cx_Oracle.SUBSCR_QOS_DEREG_NFY`` to replace
      deprecated constant SUBSCR_QOS_PURGE_ON_NTFN
    - added constant ``cx_Oracle.SUBSCR_QOS_ROWIDS`` to replace parameter
      rowids for method :meth:`Connection.subscribe()`
    - deprecated parameter cqqos for method :meth:`Connection.subscribe()`. The
      qos parameter should be used instead.
    - dropped constants SUBSCR_CQ_QOS_CLQRYCACHE, SUBSCR_QOS_HAREG,
      SUBSCR_QOS_MULTICBK, SUBSCR_QOS_PAYLOAD, SUBSCR_QOS_REPLICATE, and
      SUBSCR_QOS_SECURE since they were never actually used
#)  Deprecated use of the numbersAsStrings attribute on cursors. An output type
    handler should be used instead.


cx_Oracle 5.2.1 (January 2016)
------------------------------

#)  Added support for Python 3.5.
#)  Removed password attribute from connection and session pool objects in
    order to promote best security practices (if stored in RAM in cleartext it
    can be read in process dumps, for example). For those who would like to
    retain this feature, a subclass of Connection could be used to store the
    password.
#)  Added optional parameter ``externalauth`` to ``cx_Oracle.SessionPool()``
    which enables wallet based or other external authentication mechanisms to
    be used.
#)  Use the national character set encoding when required (when char set form
    is SQLCS_NCHAR); otherwise, the wrong encoding would be used if the
    environment variable ``NLS_NCHAR`` is set.
#)  Added support for binding boolean values to PL/SQL blocks and stored
    procedures (available in Oracle 12.1).


cx_Oracle 5.2 (June 2015)
-------------------------

#)  Added support for strings up to 32k characters (new in Oracle 12c).
#)  Added support for getting array DML row counts (new in Oracle 12c).
#)  Added support for fetching batch errors.
#)  Added support for LOB values larger than 4 GB.
#)  Added support for connections as SYSASM.
#)  Added support for building without any configuration changes to the machine
    when using instant client RPMs on Linux.
#)  Added types NCHAR, FIXED_NCHAR and LONG_NCHAR to replace the types UNICODE,
    FIXED_UNICODE and LONG_UNICODE (which are now deprecated). These types are
    available in Python 3 as well so they can be used to specify the use of
    NCHAR type fields when binding or using setinputsizes().
#)  Fixed binding of booleans in Python 3.x.
#)  Test suite now sets NLS_LANG if not already set.
#)  Enhanced documentation for connection.action attribute and added note
    on cursor.parse() method to make clear that DDL statements are executed
    when parsed.
#)  Removed remaining remnants of support Oracle 9i.
#)  Added __version__ attribute to conform with PEP 396.
#)  Ensure that sessions are released to the pool when calling
    connection.close().
    (Bitbucket Issue #2).
#)  Fixed handling of datetime intervals
    (Bitbucket Issue #7).


cx_Oracle 5.1.3 (May 2014)
--------------------------

#)  Added support for Oracle 12c.
#)  Added support for Python 3.4.
#)  Added support for query result set change notification. Thanks to Glen
    Walker for the patch.
#)  Ensure that in Python 3.x that NCHAR and NVARCHAR2 and NCLOB columns are
    retrieved properly without conversion issues. Thanks to Joakim Andersson
    for pointing out the issue and the possible solution.
#)  Fix bug when an exception is caught and then another exception is raised
    while handling that exception in Python 3.x. Thanks to Boris Dzuba for
    pointing out the issue and providing a test case.
#)  Enhance performance returning integers between 10 and 18 digits on 64-bit
    platforms that support it. Thanks for Shai Berger for the initial patch.
#)  Fixed two memory leaks.
#)  Fix to stop current_schema from throwing a MemoryError on 64-bit platforms
    on occasion. Thanks to Andrew Horton for the fix.
#)  Class name of cursors changed to real name cx_Oracle.Cursor.


cx_Oracle 5.1.2 (July 2012)
---------------------------

#)  Added support for LONG_UNICODE which is a type used to handle long unicode
    strings. These are not explicitly supported in Oracle but can be used to
    bind to NCLOB, for example, without getting the error "unimplemented or
    unreasonable conversion requested".
#)  Set the row number in a cursor when executing PL/SQL blocks as requested
    by Robert Ritchie.
#)  Added support for setting the module, action and client_info attributes
    during connection so that logon triggers will see the supplied values, as
    requested by Rodney Barnett.


cx_Oracle 5.1.1 (October 2011)
------------------------------

#)  Simplify management of threads for callbacks performed by database change
    notification and eliminate a crash that occurred under high load in
    certain situations. Thanks to Calvin S. for noting the issue and suggesting
    a solution and testing the patch.
#)  Force server detach on close so that the connection is completely closed
    and not just the session as before.
#)  Force use of OCI_UTF16ID for NCLOBs as using the default character set
    would result in ORA-03127 with Oracle 11.2.0.2 and UTF8 character set.
#)  Avoid attempting to clear temporary LOBs a second time when destroying the
    variable as in certain situations this results in spurious errors.
#)  Added additional parameter service_name to makedsn() which can be used to
    use the service_name rather than the SID in the DSN string that is
    generated.
#)  Fix cursor description in test suite to take into account the number of
    bytes per character.
#)  Added tests for NCLOBS to the test suite.
#)  Removed redundant code in setup.py for calculating the library path.


cx_Oracle 5.1 (March 2011)
--------------------------

#)  Remove support for UNICODE mode and permit Unicode to be passed through in
    everywhere a string may be passed in. This means that strings will be
    passed through to Oracle using the value of the NLS_LANG environment
    variable in Python 3.x as well. Doing this eliminated a bunch of problems
    that were discovered by using UNICODE mode and also removed an unnecessary
    restriction in Python 2.x that Unicode could not be used in connect strings
    or SQL statements, for example.
#)  Added support for creating an empty object variable via a named type, the
    first step to adding full object support.
#)  Added support for Python 3.2.
#)  Account for lib64 used on x86_64 systems. Thanks to Alex Wood for supplying
    the patch.
#)  Clear up potential problems when calling cursor.close() ahead of the
    cursor being freed by going out of scope.
#)  Avoid compilation difficulties on AIX5 as OCIPing does not appear to be
    available on that platform under Oracle 10g Release 2. Thanks to
    Pierre-Yves Fontaniere for the patch.
#)  Free temporary LOBs prior to each fetch in order to avoid leaking them.
    Thanks to Uwe Hoffmann for the initial patch.


cx_Oracle 5.0.4 (July 2010)
---------------------------

#)  Added support for Python 2.7.
#)  Added support for new parameter (port) for subscription() call which allows
    the client to specify the listening port for callback notifications from
    the database server. Thanks to Geoffrey Weber for the initial patch.
#)  Fixed compilation under Oracle 9i.
#)  Fixed a few error messages.


cx_Oracle 5.0.3 (February 2010)
-------------------------------

#)  Added support for 64-bit Windows.
#)  Added support for Python 3.1 and dropped support for Python 3.0.
#)  Added support for keyword parameters in cursor.callproc() and
    cursor.callfunc().
#)  Added documentation for the UNICODE and FIXED_UNICODE variable types.
#)  Added extra link arguments required for Mac OS X as suggested by Jason
    Woodward.
#)  Added additional error codes to the list of error codes that raise
    OperationalError rather than DatabaseError.
#)  Fixed calculation of display size for strings with national database
    character sets that are not the default AL16UTF16.
#)  Moved the resetting of the setinputsizes flag before the binding takes
    place so that if an error takes place and a new statement is prepared
    subsequently, spurious errors will not occur.
#)  Fixed compilation with Oracle 10g Release 1.
#)  Tweaked documentation based on feedback from a number of people.
#)  Added support for running the test suite using "python setup.py test"
#)  Added support for setting the CLIENT_IDENTIFIER value in the v$session
    table for connections.
#)  Added exception when attempting to call executemany() with arrays which is
    not supported by the OCI.
#)  Fixed bug when converting from decimal would result in OCI-22062 because
    the locale decimal point was not a period. Thanks to Amaury Forgeot d'Arc
    for the solution to this problem.


cx_Oracle 5.0.2 (May 2009)
--------------------------

#)  Fix creation of temporary NCLOB values and the writing of NCLOB values in
    non Unicode mode.
#)  Re-enabled parsing of non select statements as requested by Roy Terrill.
#)  Implemented a parse error offset as requested by Catherine Devlin.
#)  Removed lib subdirectory when forcing RPATH now that the library directory
    is being calculated exactly in setup.py.
#)  Added an additional cast in order to support compiling by Microsoft
    Visual C++ 2008 as requested by Marco de Paoli.
#)  Added additional include directory to setup.py in order to support
    compiling by Microsoft Visual Studio was requested by Jason Coombs.
#)  Fixed a few documentation issues.


cx_Oracle 5.0.1 (February 2009)
-------------------------------

#)  Added support for database change notification available in Oracle 10g
    Release 2 and higher.
#)  Fix bug where NCLOB data would be corrupted upon retrieval (non Unicode
    mode) or would generate exception ORA-24806 (LOB form mismatch). Oracle
    insists upon differentiating between CLOB and NCLOB no matter which
    character set is being used for retrieval.
#)  Add new attributes size, bufferSize and numElements to variable objects,
    deprecating allocelems (replaced by numElements) and maxlength (replaced
    by bufferSize)
#)  Avoid increasing memory allocation for strings when using variable width
    character sets and increasing the number of elements in a variable during
    executemany().
#)  Tweaked code in order to ensure that cx_Oracle can compile with Python
    3.0.1.


cx_Oracle 5.0 (December 2008)
-----------------------------

#)  Added support for Python 3.0 with much help from Amaury Forgeot d'Arc.
#)  Removed support for Python 2.3 and Oracle 8i.
#)  Added support for full unicode mode in Python 2.x where all strings are
    passed in and returned as unicode (module must be built in this mode)
    rather than encoded strings
#)  nchar and nvarchar columns now return unicode instead of encoded strings
#)  Added support for an output type handler and/or an input type handler to be
    specified at the connection and cursor levels.
#)  Added support for specifying both input and output converters for variables
#)  Added support for specifying the array size of variables that are created
    using the cursor.var() method
#)  Added support for events mode and database resident connection pooling
    (DRCP) in Oracle 11g.
#)  Added support for changing the password during construction of a new
    connection object as well as after the connection object has been created
#)  Added support for the interval day to second data type in Oracle,
    represented as datetime.timedelta objects in Python.
#)  Added support for getting and setting the current_schema attribute for a
    session
#)  Added support for proxy authentication in session pools as requested by
    Michael Wegrzynek (and thanks for the initial patch as well).
#)  Modified connection.prepare() to return a boolean indicating if a
    transaction was actually prepared in order to avoid the error ORA-24756
    (transaction does not exist).
#)  Raise a cx_Oracle.Error instance rather than a string for column
    truncation errors as requested by Helge Tesdal.
#)  Fixed handling of environment handles in session pools in order to allow
    session pools to fetch objects without exceptions taking place.


cx_Oracle 4.4.1 (October 2008)
------------------------------

#)  Make the bind variables and fetch variables accessible although they need
    to be treated carefully since they are used internally; support added for
    forward compatibility with version 5.x.
#)  Include the "cannot insert null value" in the list of errors that are
    treated as integrity errors as requested by Matt Boersma.
#)  Use a cx_Oracle.Error instance rather than a string to hold the error when
    truncation (ORA-1406) takes place as requested by Helge Tesdal.
#)  Added support for fixed char, old style varchar and timestamp attribute
    values in objects.
#)  Tweaked setup.py to check for the Oracle version up front rather than
    during the build in order to produce more meaningful errors and simplify
    the code.
#)  In setup.py added proper detection for the instant client on Mac OS X as
    recommended by Martijn Pieters.
#)  In setup.py, avoided resetting the extraLinkArgs on Mac OS X as doing so
    prevents simple modification where desired as expressed by Christian
    Zagrodnick.
#)  Added documentation on exception handling as requested by Andreas Mock, who
    also graciously provided an initial patch.
#)  Modified documentation indicating that the password attribute on connection
    objects can be written.
#)  Added documentation warning that parameters not passed in during subsequent
    executions of a statement will retain their original values as requested by
    Harald Armin Massa.
#)  Added comments indicating that an Oracle client is required since so many
    people find this surprising.
#)  Removed all references to Oracle 8i from the documentation and version 5.x
    will eliminate all vestiges of support for this version of the Oracle
    client.
#)  Added additional link arguments for Cygwin as requested by Rob Gillen.


cx_Oracle 4.4 (June 2008)
-------------------------

#)  Fix setup.py to handle the Oracle instant client and Oracle XE on both
    Linux and Windows as pointed out by many. Thanks also to the many people
    who also provided patches.
#)  Set the default array size to 50 instead of 1 as the DB API suggests
    because the performance difference is so drastic and many people have
    recommended that the default be changed.
#)  Added Py_BEGIN_ALLOW_THREADS and Py_END_ALLOW_THREADS around each blocking
    call for LOBs as requested by Jason Conroy who also provided an initial
    patch and performed a number of tests that demonstrate the new code is much
    more responsive.
#)  Add support for acquiring cursor.description after a parse.
#)  Defer type assignment when performing executemany() until the last possible
    moment if the value being bound in is null as suggested by Dragos Dociu.
#)  When dropping a connection from the pool, ignore any errors that occur
    during the rollback; unfortunately, Oracle decides to commit data even when
    dropping a connection from the pool instead of rolling it back so the
    attempt still has to be made.
#)  Added support for setting CLIENT_DRIVER in V$SESSION_CONNECT_INFO in Oracle
    11g and higher.
#)  Use cx_Oracle.InterfaceError rather than the builtin RuntimeError when
    unable to create the Oracle environment object as requested by Luke Mewburn
    since the error is specific to Oracle and someone attempting to catch any
    exception cannot simply use cx_Oracle.Error.
#)  Translated some error codes to OperationalError as requested by Matthew
    Harriger; translated if/elseif/else logic to switch statement to make it
    more readable and to allow for additional translation if desired.
#)  Transformed documentation to new format using restructured text. Thanks to
    Waldemar Osuch for contributing the initial draft of the new documentation.
#)  Allow the password to be overwritten by a new value as requested by Alex
    VanderWoude; this value is retained as a convenience to the user and not
    used by anything in the module; if changed externally it may be convenient
    to keep this copy up to date.
#)  Cygwin is on Windows so should be treated in the same way as noted by
    Matthew Cahn.
#)  Add support for using setuptools if so desired as requested by Shreya
    Bhatt.
#)  Specify that the version of Oracle 10 that is now primarily used is 10.2,
    not 10.1.


cx_Oracle 4.3.3 (October 2007)
------------------------------

#)  Added method ping() on connections which can be used to test whether or not
    a connection is still active (available in Oracle 10g R2).
#)  Added method cx_Oracle.clientversion() which returns a 5-tuple giving the
    version of the client that is in use (available in Oracle 10g R2).
#)  Added methods startup() and shutdown() on connections which can be used to
    startup and shutdown databases (available in Oracle 10g R2).
#)  Added support for Oracle 11g.
#)  Added samples directory which contains a handful of scripts containing
    sample code for more advanced techniques. More will follow in future
    releases.
#)  Prevent error "ORA-24333: zero iteration count" when calling executemany()
    with zero rows as requested by Andreas Mock.
#)  Added methods __enter__() and __exit__() on connections to support using
    connections as context managers in Python 2.5 and higher. The context
    managed is the transaction state. Upon exit the transaction is either
    rolled back or committed depending on whether an exception took place or
    not.
#)  Make the search for the lib32 and lib64 directories automatic for all
    platforms.
#)  Tweak the setup configuration script to include all of the metadata and
    allow for building the module within another setup configuration script
#)  Include the Oracle version in addition to the Python version in the build
    directories that are created and in the names of the binary packages that
    are created.
#)  Remove unnecessary dependency on win32api to build module on Windows.


cx_Oracle 4.3.2 (August 2007)
-----------------------------

#)  Added methods open(), close(), isopen() and getchunksize() in order to
    improve performance of reading/writing LOB values in chunks.
#)  Fixed support for native doubles and floats in Oracle 10g; added new type
    NATIVE_FLOAT to allow specification of a variable of that specific type
    where desired. Thanks to D.R. Boxhoorn for pointing out the fact that this
    was not working properly when the arraysize was anything other than 1.
#)  When calling connection.begin(), only create a new transaction handle if
    one is not already associated with the connection. Thanks to Andreas Mock
    for discovering this and for Amaury Forgeot d'Arc for diagnosing the
    problem and pointing the way to a solution.
#)  Added attribute cursor.rowfactory which allows a method to be called for
    each row that is returned; this is about 20% faster than calling the method
    in Python using the idiom [method(\*r) for r in cursor].
#)  Attempt to locate an Oracle installation by looking at the PATH if the
    environment variable ``ORACLE_HOME`` is not set; this is of primary use on
    Windows where this variable should not normally be set.
#)  Added support for autocommit mode as requested by Ian Kelly.
#)  Added support for connection.stmtcachesize which allows for both reading
    and writing the size of the statement cache size. This parameter can make a
    huge difference with the length of time taken to prepare statements. Added
    support for setting the statement tag when preparing a statement. Both of
    these were requested by Bjorn Sandberg who also provided an initial patch.
#)  When copying the value of a variable, copy the return code as well.


cx_Oracle 4.3.1 (April 2007)
----------------------------

#)  Ensure that if the client buffer size exceeds 4000 bytes that the server
    buffer size does not as strings may only contain 4000 bytes; this allows
    handling of multibyte character sets on the server as well as the client.
#)  Added support for using buffer objects to populate binary data and made the
    Binary() constructor the buffer type as requested by Ken Mason.
#)  Fix potential crash when using full optimization with some compilers.
    Thanks to Aris Motas for noticing this and providing the initial patch and
    to Amaury Forgeot d'Arc for providing an even simpler solution.
#)  Pass the correct charset form in to the write call in order to support
    writing to national character set LOB values properly. Thanks to Ian Kelly
    for noticing this discrepancy.


cx_Oracle 4.3 (March 2007)
--------------------------

#)  Added preliminary support for fetching Oracle objects (SQL types) as
    requested by Kristof Beyls (who kindly provided an initial patch).
    Additional work needs to be done to support binding and updating objects
    but the basic structure is now in place.
#)  Added connection.maxBytesPerCharacter which indicates the maximum number of
    bytes each character can use; use this value to also determine the size of
    local buffers in order to handle discrepancies between the client character
    set and the server character set. Thanks to Andreas Mock for providing the
    initial patch and working with me to resolve this issue.
#)  Added support for querying native floats in Oracle 10g as requested by
    Danny Boxhoorn.
#)  Add support for temporary LOB variables created via PL/SQL instead of only
    directly by cx_Oracle; thanks to Henning von Bargen for discovering this
    problem.
#)  Added support for specifying variable types using the builtin types int,
    float, str and datetime.date which allows for finer control of what type of
    Python object is returned from cursor.callfunc() for example.
#)  Added support for passing booleans to callproc() and callfunc() as
    requested by Anana Aiyer.
#)  Fixed support for 64-bit environments in Python 2.5.
#)  Thanks to Filip Ballegeer and a number of his co-workers, an intermittent
    crash was tracked down; specifically, if a connection is closed, then the
    call to OCIStmtRelease() will free memory twice. Preventing the call when
    the connection is closed solves the problem.


cx_Oracle 4.2.1 (September 2006)
--------------------------------

#)  Added additional type (NCLOB) to handle CLOBs that use the national
    character set as requested by Chris Dunscombe.
#)  Added support for returning cursors from functions as requested by Daniel
    Steinmann.
#)  Added support for getting/setting the "get" mode on session pools as
    requested by Anand Aiyer.
#)  Added support for binding subclassed cursors.
#)  Fixed binding of decimal objects with absolute values less than 0.1.


cx_Oracle 4.2 (July 2006)
-------------------------

#)  Added support for parsing an Oracle statement as requested by Patrick
    Blackwill.
#)  Added support for BFILEs at the request of Matthew Cahn.
#)  Added support for binding decimal.Decimal objects to cursors.
#)  Added support for reading from NCLOBs as requested by Chris Dunscombe.
#)  Added connection attributes encoding and nencoding which return the IANA
    character set name for the character set and national character set in use
    by the client.
#)  Rework module initialization to use the techniques recommended by the
    Python documentation as one user was experiencing random segfaults due
    to the use of the module dictionary after the initialization was complete.
#)  Removed support for the OPT_Threading attribute. Use the threaded keyword
    when creating connections and session pools instead.
#)  Removed support for the OPT_NumbersAsStrings attribute. Use the
    numbersAsStrings attribute on cursors instead.
#)  Use type long rather than type int in order to support long integers on
    64-bit machines as reported by Uwe Hoffmann.
#)  Add cursor attribute "bindarraysize" which is defaulted to 1 and is used
    to determine the size of the arrays created for bind variables.
#)  Added repr() methods to provide something a little more useful than the
    standard type name and memory address.
#)  Added keyword parameter support to the functions that imply such in the
    documentation as requested by Harald Armin Massa.
#)  Treat an empty dictionary passed through to cursor.execute() as keyword
    parameters the same as if no keyword parameters were specified at all, as
    requested by Fabien Grumelard.
#)  Fixed memory leak when a LOB read would fail.
#)  Set the LDFLAGS value in the environment rather than directly in the
    setup.py file in order to satisfy those who wish to enable the use of
    debugging symbols.
#)  Use __DATE__ and __TIME__ to determine the date and time of the build
    rather than passing it through directly.
#)  Use Oracle types and add casts to reduce warnings as requested by Amaury
    Forgeot d'Arc.
#)  Fixed typo in error message.


cx_Oracle 4.1.2 (December 2005)
-------------------------------

#)  Restore support of Oracle 9i features when using the Oracle 10g client.


cx_Oracle 4.1.1 (December 2005)
-------------------------------

#)  Add support for dropping a connection from a session pool.
#)  Add support for write only attributes "module", "action" and "clientinfo"
    which work only in Oracle 10g as requested by Egor Starostin.
#)  Add support for pickling database errors.
#)  Use the previously created bind variable as a template if available when
    creating a new variable of a larger size. Thanks to Ted Skolnick for the
    initial patch.
#)  Fixed tests to work properly in the Python 2.4 environment where dates and
    timestamps are different Python types. Thanks to Henning von Bargen for
    pointing this out.
#)  Added additional directories to search for include files and libraries in
    order to better support the Oracle 10g instant client.
#)  Set the internal fetch number to 0 in order to satisfy very picky source
    analysis tools as requested by Amaury Fogeot d'Arc.
#)  Improve the documentation for building and installing the module from
    source as some people are unaware of the standard methods for building
    Python modules using distutils.
#)  Added note in the documentation indicating that the arraysize attribute
    can drastically affect performance of queries since this seems to be a
    common misunderstanding of first time users of cx_Oracle.
#)  Add a comment indicating that on HP-UX Itanium with Oracle 10g the library
    ttsh10 must also be linked against. Thanks to Bernard Delmee for the
    information.


cx_Oracle 4.1 (January 2005)
----------------------------

#)  Fixed bug where subclasses of Cursor do not pass the connection in the
    constructor causing a segfault.
#)  DDL statements must be reparsed before execution as noted by Mihai
    Ibanescu.
#)  Add support for setting input sizes by position.
#)  Fixed problem with catching an exception during execute and then still
    attempting to perform a fetch afterwards as noted by Leith Parkin.
#)  Rename the types so that they can be pickled and unpickled. Thanks to Harri
    Pasanen for pointing out the problem.
#)  Handle invalid NLS_LANG setting properly (Oracle seems to like to provide a
    handle back even though it is invalid) and determine the number of bytes
    per character in order to allow for proper support in the future of
    multibyte and variable width character sets.
#)  Remove date checking from the native case since Python already checks that
    dates are valid; enhance error message when invalid dates are encountered
    so that additional processing can be done.
#)  Fix bug executing SQL using numeric parameter names with predefined
    variables (such as what takes place when calling stored procedures with out
    parameters).
#)  Add support for reading CLOB values using multibyte or variable length
    character sets.


cx_Oracle 4.1 beta 1 (September 2004)
-------------------------------------

#)  Added support for Python 2.4. In Python 2.4, the datetime module is used
    for both binding and fetching of date and timestamp data. In Python 2.3,
    objects from the datetime module can be bound but the internal datetime
    objects will be returned from queries.
#)  Added pickling support for LOB and datetime data.
#)  Fully qualified the table name that was missing in an alter table
    statement in the setup test script as noted by Marc Gehling.
#)  Added a section allowing for the setting of the RPATH linker directive in
    setup.py as requested by Iustin Pop.
#)  Added code to raise a programming error exception when an attempt is made
    to access a LOB locator variable in a subsequent fetch.
#)  The username, password and dsn (tnsentry) are stored on the connection
    object when specified, regardless of whether or not a standard connection
    takes place.
#)  Added additional module level constant called "LOB" as requested by Joseph
    Canedo.
#)  Changed exception type to IntegrityError for constraint violations as
    requested by Joseph Canedo.
#)  If scale and precision are not specified, an attempt is made to return a
    long integer as requested by Joseph Canedo.
#)  Added workaround for Oracle bug which returns an invalid handle when the
    prepare call fails. Thanks to alantam@hsbc.com for providing the code that
    demonstrated the problem.
#)  The cursor method arrayvar() will now accept the actual list so that it is
    not necessary to call cursor.arrayvar() followed immediately by
    var.setvalue().
#)  Fixed bug where attempts to execute the statement "None" with bind
    variables would cause a segmentation fault.
#)  Added support for binding by position (paramstyle = "numeric").
#)  Removed memory leak created by calls to OCIParamGet() which were not
    mirrored by calls to OCIDescriptorFree(). Thanks to Mihai Ibanescu for
    pointing this out and providing a patch.
#)  Added support for calling cursor.executemany() with statement None
    implying that the previously prepared statement ought to be executed.
    Thanks to Mihai Ibanescu for providing a patch.
#)  Added support for rebinding variables when a subsequent call to
    cursor.executemany() uses a different number of rows. Thanks to Mihai
    Ibanescu for supplying a patch.
#)  The microseconds are now displayed in datetime variables when nonzero
    similar to method used in the datetime module.
#)  Added support for binary_float and binary_double columns in Oracle 10g.


cx_Oracle 4.0.1 (February 2004)
-------------------------------

#)  Fixed bugs on 64-bit platforms that caused segmentation faults and bus
    errors in session pooling and determining the bind variables associated
    with a statement.
#)  Modified test suite so that 64-bit platforms are tested properly.
#)  Added missing commit statements in the test setup scripts. Thanks to Keith
    Lyon for pointing this out.
#)  Fix setup.py for Cygwin environments. Thanks to Doug Henderson for
    providing the necessary fix.
#)  Added support for compiling cx_Oracle without thread support. Thanks to
    Andre Reitz for pointing this out.
#)  Added support for a new keyword parameter called threaded on connections
    and session pools. This parameter defaults to False and indicates whether
    threaded mode ought to be used. It replaces the module level attribute
    OPT_Threading although examining the attribute will be retained until the
    next release at least.
#)  Added support for a new keyword parameter called twophase on connections.
    This parameter defaults to False and indicates whether support for two
    phase (distributed or global) transactions ought to be present. Note that
    support for distributed transactions is buggy when crossing major version
    boundaries (Oracle 8i to Oracle 9i for example).
#)  Ensure that the rowcount attribute is set properly when an exception is
    raised during execution. Thanks to Gary Aviv for pointing out this problem
    and its solution.


cx_Oracle 4.0 (December 2003)
-----------------------------

#)  Added support for subclassing connections, cursors and session pools. The
    changes involved made it necessary to drop support for Python 2.1 and
    earlier although a branch exists in CVS to allow for support of Python 2.1
    and earlier if needed.
#)  Connections and session pools can now be created with keyword parameters,
    not just sequential parameters.
#)  Queries now return integers whenever possible and long integers if the
    number will overflow a simple integer. Floats are only returned when it is
    known that the number is a floating point number or the integer conversion
    fails.
#)  Added initial support for user callbacks on OCI functions. See the
    documentation for more details.
#)  Add support for retrieving the bind variable names associated with a
    cursor with a new method bindnames().
#)  Add support for temporary LOB variables. This means that setinputsizes()
    can be used with the values CLOB and BLOB to create these temporary LOB
    variables and allow for the equivalent of empty_clob() and empty_blob()
    since otherwise Oracle will treat empty strings as NULL values.
#)  Automatically switch to long strings when the data size exceeds the
    maximum string size that Oracle allows (4000 characters) and raise an
    error if an attempt is made to set a string variable to a size that it
    does not support. This avoids truncation errors as reported by Jon Franz.
#)  Add support for global (distributed) transactions and two phase commit.
#)  Force the NLS settings for the session so that test tables are populated
    correctly in all circumstances; problems were noted by Ralf Braun and
    Allan Poulsen.
#)  Display error messages using the environment handle when the error handle
    has not yet been created; this provides better error messages during this
    rather rare situation.
#)  Removed memory leak in callproc() that was reported by Todd Whiteman.
#)  Make consistent the calls to manipulate memory; otherwise segfaults can
    occur when the pymalloc option is used, as reported by Matt Hoskins.
#)  Force a rollback when a session is released back to the session pool.
    Apparently the connections are not as stateless as Oracle's documentation
    suggests and this makes the logic consistent with normal connections.
#)  Removed module method attach(). This can be replaced with a call to
    Connection(handle=) if needed.


cx_Oracle 3.1 (August 2003)
---------------------------

#)  Added support for connecting with SYSDBA and SYSOPER access which is
    needed for connecting as sys in Oracle 9i.
#)  Only check the dictionary size if the variable is not NULL; otherwise, an
    error takes place which is not caught or cleared; this eliminates a
    spurious "Objects/dictobject.c:1258: bad argument to internal function" in
    Python 2.3.
#)  Add support for session pooling. This is only support for Oracle 9i but
    is amazingly fast -- about 100 times faster than connecting.
#)  Add support for statement caching when pooling sessions, this reduces the
    parse time considerably. Unfortunately, the Oracle OCI does not allow this
    to be easily turned on for normal sessions.
#)  Add method trim() on CLOB and BLOB variables for trimming the size.
#)  Add support for externally identified users; to use this feature leave the
    username and password fields empty when connecting.
#)  Add method cancel() on connection objects to cancel long running queries.
    Note that this only works on non-Windows platforms.
#)  Add method callfunc() on cursor objects to allow calling a function
    without using an anonymous PL/SQL block.
#)  Added documentation on objects that were not documented. At this point all
    objects, methods and constants in cx_Oracle have been documented.
#)  Added support for timestamp columns in Oracle 9i.
#)  Added module level method makedsn() which creates a data source name given
    the host, port and SID.
#)  Added constant "buildtime" which is the time when the module was built as
    an additional means of identifying the build that is in use.
#)  Binding a value that is incompatible to the previous value that was bound
    (data types do not match or array size is larger) will now result in a
    new bind taking place. This is more consistent with the DB API although
    it does imply a performance penalty when used.


cx_Oracle 3.0a (June 2003)
--------------------------

#)  Fixed bug where zero length PL/SQL arrays were being mishandled
#)  Fixed support for the data type "float" in Oracle; added one to the
    display size to allow for the sign of the number, if necessary; changed
    the display size of unconstrained numbers to 127, which is the largest
    number that Oracle can handle
#)  Added support for retrieving the description of a bound cursor before
    fetching it
#)  Fixed a couple of build issues on Mac OS X, AIX and Solaris (64-bit)
#)  Modified documentation slightly based on comments from several people
#)  Included files in MANIFEST that are needed to generate the binaries
#)  Modified test suite to work within the test environment at Computronix
    as well as within the packages that are distributed


cx_Oracle 3.0 (March 2003)
--------------------------

#)  Removed support for connection to Oracle7 databases; it is entirely
    possible that it will still work but I no longer have any way of testing
    and Oracle has dropped any meaningful support for Oracle7 anyway
#)  Fetching of strings is now done with predefined memory areas rather than
    dynamic memory areas; dynamic fetching of strings was causing problems
    with Oracle 9i in some instances and databases using a different character
    set other than US ASCII
#)  Fixed bug where segfault would occur if the '/' character preceded the '@'
    character in a connect string
#)  Added two new cursor methods var() and arrayvar() in order to eliminate
    the need for setinputsizes() when defining PL/SQL arrays and as a generic
    method of acquiring bind variables directly when needed
#)  Fixed support for binding cursors and added support for fetching cursors
    (these are known as ref cursors in PL/SQL).
#)  Eliminated discrepancy between the array size used internally and the
    array size specified by the interface user; this was done earlier to avoid
    bus errors on 64-bit platforms but another way has been found to get
    around that issue and a number of people were getting confused because of
    the discrepancy
#)  Added support for the attribute "connection" on cursors, an optional
    DB API extension
#)  Added support for passing a dictionary as the second parameter for the
    cursor.execute() method in order to comply with the DB API more closely;
    the method of passing parameters with keyword parameters is still supported
    and is in fact preferred
#)  Added support for the attribute "statement" on cursors which is a
    reference to the last SQL statement prepared or executed
#)  Added support for passing any sequence to callproc() rather than just
    lists as before
#)  Fixed bug where segfault would occur if the array size was changed after
    the cursor was executed but before it was fetched
#)  Ignore array size when performing executemany() and use the length of the
    list of parameters instead
#)  Rollback when connection is closed or destroyed to follow DB API rather
    than use the Oracle default (which is commit)
#)  Added check for array size too large causing an integer overflow
#)  Added support for iterators for Python 2.2 and above
#)  Added test suite based on PyUnitTest
#)  Added documentation in HTML format similar to the documentation for the
    core Python library


cx_Oracle 2.5a (August 2002)
----------------------------

#)  Fix problem with Oracle 9i and retrieving strings; it seems that Oracle 9i
    uses the correct method for dynamic callback but Oracle 8i will not work
    with that method so an #ifdef was added to check for the existence of an
    Oracle 9i feature; thanks to Paul Denize for discovering this problem


cx_Oracle 2.5 (July 2002)
-------------------------

#)  Added flag OPT_NoOracle7 which, if set, assumes that connections are being
    made to Oracle8 or higher databases; this allows for eliminating the
    overhead in performing this check at connect time
#)  Added flag OPT_NumbersAsStrings which, if set, returns all numbers as
    strings rather than integers or floats; this flag is used when defined
    variables are created (during select statements only)
#)  Added flag OPT_Threading which, if set, uses OCI threading mode; there is a
    significant performance degradation in this mode (about 15-20%) but it does
    allow threads to share connections (threadsafety level 2 according to the
    Python Database API 2.0); note that in order to support this, Oracle 8i or
    higher is now required
#)  Added Py_BEGIN_ALLOW_THREADS and Py_END_ALLOW_THREADS pairs where
    applicable to support threading during blocking OCI calls
#)  Added global method attach() to cx_Oracle to support attaching to an
    existing database handle (as provided by PowerBuilder, for example)
#)  Eliminated the cursor method fetchbinds() which was used for returning the
    list of bind variables after execution to get the values of out variables;
    the cursor method setinputsizes() was modified to return the list of bind
    variables and the cursor method execute() was modified to return the list
    of defined variables in the case of a select statement being executed;
    these variables have three methods available to them: getvalue([<pos>]) to
    get the value of a variable, setvalue(<pos>, <value>) to set its value and
    copy(<var>, <src_pos>, <targ_pos>) to copy the value from a variable in a
    more efficient manner than setvalue(getvalue())
#)  Implemented cursor method executemany() which expects a list of
    dictionaries for the parameters
#)  Implemented cursor method callproc()
#)  Added cursor method prepare() which parses (prepares) the statement for
    execution; subsequent execute() or executemany() calls can pass None as the
    statement which will imply use of the previously prepared statement; used
    for high performance only
#)  Added cursor method fetchraw() which will perform a raw fetch of the cursor
    returning the number of rows thus fetched; this is used to avoid the
    overhead of generating result sets; used for high performance only
#)  Added cursor method executemanyprepared() which is identical to the method
    executemany() except that it takes a single parameter which is the number
    of times to execute a previously prepared statement and it assumes that the
    bind variables already have their values set; used for high performance
    only
#)  Added support for rowid being returned in a select statement
#)  Added support for comparing dates returned by cx_Oracle
#)  Integrated patch from Andre Reitz to set the null ok flag in the
    description attribute of the cursor
#)  Integrated patch from Andre Reitz to setup.py to support compilation with
    Python 1.5
#)  Integrated patch from Benjamin Kearns to setup.py to support compilation
    on Cygwin


cx_Oracle 2.4 (January 2002)
----------------------------

#)  String variables can now be made any length (previously restricted to the
    64K limit imposed by Oracle for default binding); use the type
    cx_Oracle.LONG_STRING as the parameter to setinputsizes() for binding in
    string values larger than 4000 bytes.
#)  Raw and long raw columns are now supported; use the types cx_Oracle.BINARY
    and cx_Oracle.LONG_BINARY as the parameter to setinputsizes() for binding
    in values of these types.
#)  Functions DateFromTicks(), TimeFromTicks() and TimestampFromTicks()
    are now implemented.
#)  Function cursor.setoutputsize() implemented
#)  Added the ability to bind arrays as out parameters to procedures; use the
    format [cx_Oracle.<DataType>, <NumElems>] as the input to the function
    setinputsizes() for binding arrays
#)  Discovered from the Oracle 8.1.6 version of the documentation of the OCI
    libraries, that the size of the memory location required for the precision
    variable is larger than the printed documentation says; this was causing a
    problem with the code on the Sun platform.
#)  Now support building RPMs for Linux.


cx_Oracle 2.3 (October 2001)
----------------------------

#)  Incremental performance enhancements (dealing with reusing cursors and
    bind handles)
#)  Ensured that arrays of integers with a single float in them are all
    treated as floats, as suggested by Martin Koch.
#)  Fixed code dealing with scale and precision for both defining a numeric
    variable and for providing the cursor description; this eliminates the
    problem of an underflow error (OCI-22054) when retrieving data with
    non-zero scale.


cx_Oracle 2.2 (July 2001)
-------------------------

#)  Upgraded thread safety to level 1 (according to the Python DB API 2.0) as
    an internal project required the ability to share the module between
    threads.
#)  Added ability to bind ref cursors to PL/SQL blocks as requested by
    Brad Powell.
#)  Added function write(Value, [Offset]) to LOB variables as requested by
    Matthias Kirst.
#)  Procedure execute() on Cursor objects now permits a value None for the
    statement which means that the previously prepared statement will be
    executed and any input sizes set earlier will be retained. This was done to
    improve the performance of scripts that execute one statement many times.
#)  Modified module global constants BINARY and DATETIME to point to the
    external representations of those types so that the expression
    type(var) == cx_Oracle.DATETIME will work as expected.
#)  Added global constant version to provide means of determining the current
    version of the module.
#)  Modified error checking routine to distinguish between an Oracle error and
    invalid handles.
#)  Added error checking to avoid setting the value of a bind variable to a
    value that it cannot support and raised an exception to indicate this fact.
#)  Added extra compile arguments for the AIX platform as suggested by Jehwan
    Ryu.
#)  Added section to the README to indicate the method for a binary
    installation as suggested by Steve Holden.
#)  Added simple usage example as requested by many people.
#)  Added HISTORY file to the distribution.
