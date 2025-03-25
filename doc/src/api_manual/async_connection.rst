.. _asyncconnobj:

****************************
API: AsyncConnection Objects
****************************

An AsyncConnection object can be created with :meth:`oracledb.connect_async()`
or with :meth:`AsyncConnectionPool.acquire()`. AsyncConnections support use of
concurrent programming with `asyncio <https://docs.python.org/3/library/
asyncio.html>`__. Unless explicitly noted as synchronous, the AsyncConnection
methods should be used with ``await``.

.. dbapiobjectextension::

.. versionadded:: 2.0.0

.. note::

    AsyncConnection objects are only supported in the python-oracledb Thin
    mode.

.. note::

    Any outstanding database transaction will be rolled back when the
    connection object is destroyed or closed.  You must perform a
    :meth:`commit <AsyncConnection.commit>` first if you want data to
    persist in the database, see :ref:`txnasync`.

.. _asyncconnmeth:

AsyncConnection Methods
=======================

.. method:: AsyncConnection.__aenter__()

    The entry point for the asynchronous connection as a context manager. It
    returns itself.

.. method:: AsyncConnection.__aexit__()

    The exit point for the asynchronous connection as a context manager. This
    will close the connection and roll back any uncommitted transaction.

.. method:: AsyncConnection.callfunc(name, return_type, parameters=None, \
                keyword_parameters=None)

    Calls a PL/SQL function with the given name.

    This is a shortcut for calling :meth:`AsyncConnection.cursor()`,
    :meth:`AsyncCursor.callfunc()`, and then :meth:`AsyncCursor.close()`.

.. method:: AsyncConnection.callproc(name, parameters=None, \
                keyword_parameters=None)

    Calls a PL/SQL procedure with the given name.

    This is a shortcut for calling :meth:`AsyncConnection.cursor()`,
    :meth:`AsyncCursor.callproc()`, and then :meth:`AsyncCursor.close()`.

.. method:: AsyncConnection.cancel()

    A synchronous method that breaks a long-running statement.

.. method:: AsyncConnection.changepassword(old_password, new_password)

    Changes the password for the user to which the connection is connected.

.. method:: AsyncConnection.close()

    Closes the connection.

.. method:: AsyncConnection.commit()

    Commits any pending transaction to the database.

.. method:: AsyncConnection.createlob(lob_type)

    Creates and returns a new temporary LOB of the specified type.

.. method:: AsyncConnection.cursor(scrollable=False)

    A synchronous method that returns an :ref:`AsyncCursor object
    <asynccursorobj>` associated with the connection.

.. method:: AsyncConnection.decode_oson(data)

    A synchronous method that decodes `OSON-encoded
    <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-911D302C-CFAF-406B-B6A5-4E99DD38ABAD>`__
    bytes and returns the object encoded in those bytes.  This is useful for
    fetching columns which have the check constraint ``IS JSON FORMAT OSON``
    enabled.

    .. versionadded:: 2.1.0

.. method:: AsyncConnection.encode_oson(value)

    A synchronous method that encodes a Python value into `OSON-encoded
    <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-911D302C-CFAF-406B-B6A5-4E99DD38ABAD>`__
    bytes and returns them. This is useful for inserting into columns which
    have the check constraint ``IS JSON FORMAT OSON`` enabled.

    .. versionadded:: 2.1.0

.. method:: AsyncConnection.execute(statement, parameters=None)

    Executes a statement against the database.

    This is a shortcut for calling :meth:`AsyncConnection.cursor()`,
    :meth:`AsyncCursor.execute()`, and then :meth:`AsyncCursor.close()`

.. method:: AsyncConnection.executemany(statement, parameters)

    Executes a SQL statement once using all bind value mappings or sequences
    found in the sequence parameters. This can be used to insert, update, or
    delete multiple rows in a table with a single python-oracledb call. It can
    also invoke a PL/SQL procedure multiple times.

    The ``parameters`` parameter can be a list of tuples, where each tuple item
    maps to one bind variable placeholder in ``statement``. It can also be a
    list of dictionaries, where the keys match the bind variable placeholder
    names in ``statement``. If there are no bind values, or values have
    previously been bound, the ``parameters`` value can be an integer
    specifying the number of iterations.

    This is a shortcut for calling :meth:`AsyncConnection.cursor()`,
    :meth:`AsyncCursor.executemany()`, and then :meth:`AsyncCursor.close()`.

.. method:: AsyncConnection.fetch_df_all(statement, parameters=None, \
            arraysize=None)

    Fetches all rows of the SQL query ``statement``, returning them in an
    :ref:`OracleDataFrame <oracledataframeobj>` object. An empty
    OracleDataFrame is returned if there are no rows available.

    The ``parameters`` parameter can be a list of tuples, where each tuple item
    maps to one :ref:`bind variable placeholder <bind>` in ``statement``. It
    can also be a list of dictionaries, where the keys match the bind variable
    placeholder names in ``statement``.

    The ``arraysize`` parameter can be specified to tune performance of fetching
    data across the network. It defaults to :attr:`defaults.arraysize`.
    Internally, the ``fetch_df_all()``'s :attr:`Cursor.prefetchrows` size is
    always set to the value of the explicit or default ``arraysize`` parameter
    value.

    See :ref:`dataframeformat` for the supported data types and examples.

    .. note::

        The data frame support in python-oracledb 3.1 is a pre-release and may
        change in a future version.

    .. versionadded:: 3.0.0

.. method:: AsyncConnection.fetch_df_batches(statement, parameters=None, \
            size=None)

    This returns an iterator yielding the next ``size`` rows of the SQL query
    ``statement`` in each iteration as an :ref:`OracleDataFrame
    <oracledataframeobj>` object. An empty OracleDataFrame is returned if there
    are no rows available.

    The ``parameters`` parameter can be a list of tuples, where each tuple item
    maps to one :ref:`bind variable placeholder <bind>` in ``statement``. It
    can also be a list of dictionaries, where the keys match the bind variable
    placeholder names in ``statement``.

    The ``size`` parameter controls the number of records fetched in each
    batch. It defaults to :attr:`defaults.arraysize`. Internally, the
    ``fetch_df_batches()``'s :attr:`Cursor.arraysize` and
    :attr:`Cursor.prefetchrows` sizes are always set to the value of the
    explicit or default ``size`` parameter value.

    See :ref:`dataframeformat` for the supported data types and examples.

    .. note::

        The data frame support in python-oracledb 3.1 is a pre-release and may
        change in a future version.

    .. versionadded:: 3.0.0

.. method:: AsyncConnection.fetchall(statement, parameters=None, \
                arraysize=None, rowfactory=None)

    Executes a query and returns all of the rows.

    The default value for ``arraysize`` is :attr:`defaults.arraysize`.

    Internally, this method's :attr:`Cursor.prefetchrows` size is set to the
    value of the explicit or default ``arraysize`` parameter value.

    This is a shortcut for calling :meth:`AsyncConnection.cursor()`,
    :meth:`AsyncCursor.fetchall()`, and then :meth:`AsyncCursor.close()`.

.. method:: AsyncConnection.fetchmany(statement, parameters=None, \
                num_rows=None, rowfactory=None)

    Executes a query and returns up to the specified number of rows.

    The default value for ``num_rows`` is the value of
    :attr:`defaults.arraysize`.

    Internally, this method's :attr:`Cursor.prefetchrows` size is set to the
    value of the explicit or default ``num_rows`` parameter, allowing all rows
    to be fetched in one :ref:`round-trip <roundtrips>`

    Since only one fetch is performed for a query, consider adding a ``FETCH
    NEXT`` clause to the statement to prevent the database processing rows that
    will never be fetched, see :ref:`rowlimit`.

    This a shortcut for calling :meth:`AsyncConnection.cursor()`,
    :meth:`AsyncCursor.fetchmany()`, and then :meth:`AsyncCursor.close()`.

.. method:: AsyncConnection.fetchone(statement, parameters=None, \
                rowfactory=None)

    Executes a query and returns the first row of the result set if one exists
    (or *None* if no rows exist).

    Internally, this method's :attr:`Cursor.prefetchrows` and
    :attr:`Cursor.arraysize` sizes will be set to *1*.

    Since only one fetch is performed for a query, consider adding a ``WHERE``
    condition or using a ``FETCH NEXT`` clause in the statement to prevent the
    database processing rows that will never be fetched, see :ref:`rowlimit`.

    This a shortcut for calling :meth:`AsyncConnection.cursor()`,
    :meth:`AsyncCursor.fetchone()`, and then :meth:`AsyncCursor.close()`.

.. method:: AsyncConnection.gettype(name)

    Returns a :ref:`type object <dbobjecttype>` given its name. This can then
    be used to create objects which can be bound to cursors created by this
    connection.

.. method:: AsyncConnection.is_healthy()

    A synchronous method that returns a boolean indicating the health status
    of a connection.

    Connections may become unusable in several cases, such as, if the network
    socket is broken, if an Oracle error indicates the connection is unusable,
    or after receiving a planned down notification from the database.

    This function is best used before starting a new database request on an
    existing standalone connection. Pooled connections internally perform this
    check before returning a connection to the application.

    If this function returns *False*, the connection should be not be used by
    the application and a new connection should be established instead.

    This function performs a local check. To fully check a connection's health,
    use :meth:`AsyncConnection.ping()` which performs a :ref:`round-trip
    <roundtrips>` to the database.

.. method:: AsyncConnection.msgproperties(payload, correlation, delay, exceptionq, expiration, priority)

    Creates and returns a message properties object that contains the
    properties of messages used in advanced queuing. See
    :ref:`asyncmsgproperties` for more information.

    Each of the parameters are optional. If specified, they act as a shortcut
    for setting each of the equivalently named properties.

    .. versionadded:: 3.1.0

.. method:: AsyncConnection.ping()

    Pings the database to verify if the connection is valid.

.. method:: AsyncConnection.queue(name, payload_type=None)

    Creates a :ref:`queue <asyncqueue>` which is used to enqueue and dequeue
    messages in Advanced Queuing.

    The ``name`` parameter is expected to be a string identifying the queue in
    which messages are to be enqueued or dequeued.

    The ``payload_type`` parameter, if specified, is expected to be an
    :ref:`object type <dbobjecttype>` that identifies the type of payload the
    queue expects. If the string "JSON" is specified, JSON data is enqueued and
    dequeued. If not specified, RAW data is enqueued and dequeued.

    .. versionadded:: 3.1.0

.. method:: AsyncConnection.rollback()

    Rolls back any pending transaction.

.. method:: AsyncConnection.run_pipeline(pipeline, continue_on_error=False)

    Runs all of the operations in the :ref:`pipeline <pipelineobj>` and returns
    a list of :ref:`PipelineOpResult Objects <pipelineopresultobjs>`, each
    entry corresponding to an operation executed in the pipeline.

    The ``continue_on_error`` parameter determines whether operations should
    continue to run after an error has occurred. If this parameter is set to
    *True*, then the :attr:`PipelineOpResult.error` attribute will be populated
    with an :ref:`_Error <exchandling>` instance which identifies the error
    that occurred. If this parameter is set to *False*, then an exception will
    be raised as soon as an error is detected and all subsequent operations
    will be terminated. The default value is *False*.

    See :ref:`pipelining` for more information.

    .. note::

        True pipelining requires Oracle Database 23ai.

        When you connect to an older database, operations are sequentially
        executed by python-oracledb. Each operation concludes before the next
        is sent to the database. There is no reduction in round-trips and no
        performance benefit. This usage is only recommended for code
        portability such as when preparing for a database upgrade.

    .. versionadded:: 2.4.0

.. method:: AsyncConnection.tpc_begin(xid, flags, timeout)

    Begins a Two-Phase Commit (TPC) on a global transaction using the specified
    transaction identifier (xid).

    The ``xid`` parameter should be an object returned by the
    :meth:`~Connection.xid()` method.

    The ``flags`` parameter is one of the constants
    :data:`oracledb.TPC_BEGIN_JOIN`, :data:`oracledb.TPC_BEGIN_NEW`,
    :data:`oracledb.TPC_BEGIN_PROMOTE`, or :data:`oracledb.TPC_BEGIN_RESUME`.
    The default is :data:`oracledb.TPC_BEGIN_NEW`.

    The ``timeout`` parameter is the number of seconds to wait for a
    transaction to become available for resumption when
    :data:`~oracledb.TPC_BEGIN_RESUME` is specified in the ``flags`` parameter.
    When :data:`~oracledb.TPC_BEGIN_NEW` is specified in the ``flags``
    parameter, the ``timeout`` parameter indicates the number of seconds the
    transaction can be inactive before it is automatically terminated by the
    system. A transaction is inactive between the time it is detached with
    :meth:`AsyncConnection.tpc_end()` and the time it is resumed with
    :meth:`AsyncConnection.tpc_begin()`.The default is *0* seconds.

    The following code sample demonstrates the ``tpc_begin()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        await connection.tpc_begin(xid=x, flags=oracledb.TPC_BEGIN_NEW, timeout=30)

    See :ref:`tpc` for information on TPC.

    .. versionadded:: 2.3.0

.. method:: AsyncConnection.tpc_commit(xid, one_phase)

    Commits a global transaction. When called with no arguments, this method
    commits a transaction previously prepared with
    :meth:`~AsyncConnection.tpc_begin()` and optionally prepared with
    :meth:`~AsyncConnection.tpc_prepare()`. If
    :meth:`~AsyncConnection.tpc_prepare()` is not called, a single phase commit
    is performed. A transaction manager may choose to do this if only a single
    resource is participating in the global transaction.

    If an ``xid`` parameter is passed, then an object should be returned by the
    :meth:`~Connection.xid()` function. This form should be called outside of a
    transaction and is intended for use in recovery.

    The ``one_phase`` parameter is a boolean identifying whether to perform a
    one-phase or two-phase commit. If ``one_phase`` parameter is *True*, a
    single-phase commit is performed.  The default value is *False*. This
    parameter is only examined if a value is provided for the ``xid``
    parameter. Otherwise, the driver already knows whether
    :meth:`~AsyncConnection.tpc_prepare()` was called for the transaction and
    whether a one-phase or two-phase commit is required.

    The following code sample demonstrates the ``tpc_commit()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        await connection.tpc_commit(xid=x, one_phase=False)

    See :ref:`tpc` for information on TPC.

    .. versionadded:: 2.3.0

.. method:: AsyncConnection.tpc_end(xid, flags)

    Ends or suspends work on a global transaction. This function is only
    intended for use by transaction managers.

    If an ``xid`` parameter is passed, then an object should be returned by the
    :meth:`~Connection.xid()` function. If no xid parameter is passed, then the
    transaction identifier used by the previous :meth:`~Connection.tpc_begin()`
    is used.

    The ``flags`` parameter is one of the constants
    :data:`oracledb.TPC_END_NORMAL` or :data:`oracledb.TPC_END_SUSPEND`. The
    default is :data:`oracledb.TPC_END_NORMAL`.

    If the flag is :data:`oracledb.TPC_END_SUSPEND` then the transaction may be
    resumed later by calling :meth:`AsyncConnection.tpc_begin()` with the flag
    :data:`oracledb.TPC_BEGIN_RESUME`.

    The following code sample demonstrates the ``tpc_end()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        await connection.tpc_end(xid=x, flags=oracledb.TPC_END_NORMAL)

    See :ref:`tpc` for information on TPC.

    .. versionadded:: 2.3.0

.. method:: AsyncConnection.tpc_forget(xid)

    Causes the database to forget a heuristically completed TPC transaction.
    This function is only intended to be called by transaction managers.

    The ``xid`` parameter is mandatory and should be an object should be
    returned by the :meth:`~Connection.xid()` function.

    The following code sample demonstrates the ``tpc_forget()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        await connection.tpc_forget(xid=x)

    See :ref:`tpc` for information on TPC.

    .. versionadded:: 2.3.0

.. method:: AsyncConnection.tpc_prepare(xid)

    Prepares a two-phase transaction for commit. After this function is called,
    no further activity should take place on this connection until either
    :meth:`~AsyncConnection.tpc_commit()` or
    :meth:`~AsyncConnection.tpc_rollback()` have been called.

    Returns a boolean indicating whether a commit is needed or not. If you
    attempt to commit when not needed, then it results in the error
    ``ORA-24756: transaction does not exist``.

    If an ``xid`` parameter is passed, then an object should be returned by the
    :meth:`~Connection.xid()` function. If an ``xid`` parameter is not passed,
    then the transaction identifier used by the previous
    :meth:`~AsyncConnection.tpc_begin()` is used.

    The following code sample demonstrates the ``tpc_prepare()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        await connection.tpc_prepare(xid=x)

    See :ref:`tpc` for information on TPC.

    .. versionadded:: 2.3.0

.. method:: AsyncConnection.tpc_recover()

    Returns a list of pending transaction identifiers that require recovery.
    Objects of type ``Xid`` (as returned by the :meth:`~Connection.xid()`
    function) are returned and these can be passed to
    :meth:`~AsyncConnection.tpc_commit()` or
    :meth:`~AsyncConnection.tpc_rollback()` as needed.

    This function queries the view ``DBA_PENDING_TRANSACTIONS`` and requires
    ``SELECT`` privilege on that view.

    The following code sample demonstrates the ``tpc_recover()`` function::

        await connection.tpc_recover()

    See :ref:`tpc` for information on TPC.

    .. versionadded:: 2.3.0

.. method:: AsyncConnection.tpc_rollback(xid)

    Rolls back a global transaction.

    If an ``xid`` parameter is not passed, then it rolls back the transaction
    that was previously started with :meth:`~AsyncConnection.tpc_begin()`.

    If an ``xid`` parameter is passed, then an object should be returned by
    :meth:`~Connection.xid()` and the specified transaction is rolled back.
    This form should be called outside of a transaction and is intended for use
    in recovery.

    The following code sample demonstrates the ``tpc_rollback()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        await connection.tpc_rollback(xid=x)

    See :ref:`tpc` for information on TPC.

    .. versionadded:: 2.3.0

.. _asynconnattr:

AsyncConnection Attributes
==========================

.. attribute:: AsyncConnection.action

    This write-only attribute sets the ACTION column in the V$SESSION view. It
    is a string attribute but the value *None* is accepted and treated as an
    empty string.

.. attribute:: AsyncConnection.autocommit

    This read-write attribute determines whether autocommit mode is on or off.
    When autocommit mode is on, all statements are committed as soon as they
    have completed executing.

.. attribute:: AsyncConnection.call_timeout

    This read-write attribute specifies the amount of time (in milliseconds)
    that a single round-trip to the database may take before a timeout will
    occur. A value of *0* means that no timeout will take place.

    If a timeout occurs, the error ``DPI-1067`` will be returned if the
    connection is still usable.  Alternatively, the error ``DPI-1080`` will be
    returned if the connection has become invalid and can no longer be used.

.. attribute:: AsyncConnection.client_identifier

    This write-only attribute sets the CLIENT_IDENTIFIER column in the
    V$SESSION view.

.. attribute:: AsyncConnection.clientinfo

    This write-only attribute sets the CLIENT_INFO column in the V$SESSION
    view.

.. attribute:: AsyncConnection.current_schema

    This read-write attribute sets the current schema attribute for the
    session. Setting this value is the same as executing the SQL statement
    ``ALTER SESSION SET CURRENT_SCHEMA``. The attribute is set (and verified) on
    the next call that does a round trip to the server. The value is placed
    before unqualified database objects in SQL statements you then execute.

.. attribute:: AsyncConnection.db_domain

    This read-only attribute specifies the Oracle Database domain name
    associated with the connection. It is the same value returned by the SQL
    ``SELECT value FROM V$PARAMETER WHERE NAME = 'db_domain'``.

.. attribute:: AsyncConnection.db_name

    This read-only attribute specifies the Oracle Database name associated with
    the connection. It is the same value returned by the SQL
    ``SELECT NAME FROM V$DATABASE``.

.. attribute:: AsyncConnection.dbop

    This write-only attribute sets the database operation that is to be
    monitored. This can be viewed in the DBOP_NAME column of the
    V$SQL_MONITOR view.

.. attribute:: AsyncConnection.dsn

    This read-only attribute returns the TNS entry of the database to which a
    connection has been established.

.. attribute:: AsyncConnection.econtext_id

    This write-only attribute specifies the execution context id. This value
    can be found as the ECID column in the V$SESSION view and ECONTEXT_ID in
    the auditing tables. The maximum length is 64 bytes.

.. attribute:: AsyncConnection.edition

    This read-only attribute gets the session edition and is only available
    with Oracle Database 11.2, or later.

.. attribute:: AsyncConnection.external_name

    This read-write attribute specifies the external name that is used by the
    connection when logging distributed transactions.

.. attribute:: AsyncConnection.inputtypehandler

    This read-write attribute specifies a method called for each value that is
    bound to a statement executed on any cursor associated with this
    connection.  The method signature is handler(cursor, value, arraysize) and
    the return value is expected to be a variable object or *None* in which
    case a default variable object will be created. If this attribute is
    *None*, the default behavior will take place for all values bound to
    statements.

.. attribute:: AsyncConnection.instance_name

    This read-only attribute specifies the Oracle Database instance name
    associated with the connection. It is the same value as the SQL expression
    ``sys_context('userenv', 'instance_name')``.

.. attribute:: AsyncConnection.internal_name

    This read-write attribute specifies the internal name that is used by the
    connection when logging distributed transactions.

.. attribute:: AsyncConnection.ltxid

    This read-only attribute returns the logical transaction id for the
    connection. It is used within Oracle Transaction Guard as a means of
    ensuring that transactions are not duplicated. See the Oracle documentation
    and the provided sample for more information.

    .. note:

        This attribute is only available with Oracle Database 12.1 or later.

.. attribute:: AsyncConnection.max_identifier_length

    This read-only attribute specifies the maximum database identifier length
    in bytes supported by the database to which the connection has been
    established.  See `Database Object Naming Rules
    <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
    id=GUID-75337742-67FD-4EC0-985F-741C93D918DA>`__.

    .. versionadded:: 2.5.0

.. attribute:: AsyncConnection.max_open_cursors

    This read-only attribute specifies the maximum number of cursors that the
    database can have open concurrently. It is the same value returned by the
    SQL ``SELECT VALUE FROM V$PARAMETER WHERE NAME = 'open_cursors'``.

.. attribute:: AsyncConnection.module

    This write-only attribute sets the MODULE column in the V$SESSION view.
    The maximum length for this string is 48 and if you exceed this length you
    will get ``ORA-24960``.

.. attribute:: AsyncConnection.outputtypehandler

    This read-write attribute specifies a method called for each column that is
    going to be fetched from any cursor associated with this connection. The
    method signature is ``handler(cursor, metadata)`` and the return value is
    expected to be a :ref:`variable object <varobj>` or *None* in which case a
    default variable object will be created. If this attribute is *None*, the
    default behavior will take place for all columns fetched from cursors.

    See :ref:`outputtypehandlers`.

.. attribute:: AsyncConnection.sdu

    This read-only attribute specifies the size of the Session Data Unit (SDU)
    that is being used by the connection. The value will be the lesser of the
    requested python-oracledb size and the maximum size allowed by the database
    network configuration.

.. attribute:: AsyncConnection.serial_num

    This read-only attribute specifies the session serial number associated with
    the connection. It is the same value returned by the SQL
    ``SELECT SERIAL# FROM V$SESSION``.

    It is available only in python-oracledb Thin mode.

    For applications using :ref:`drcp`, the ``serial_num`` attribute may not
    contain the current session state until a round-trip is made to the
    database after acquiring a session.  It is recommended to not use this
    attribute if your application uses DRCP but may not perform a round-trip.

    .. dbapiattributeextension::

    .. versionadded:: 2.5.0

.. attribute:: AsyncConnection.service_name

    This read-only attribute specifies the Oracle Database service name
    associated with the connection.  This is the same value returned by the SQL
    ``SELECT SYS_CONTEXT('USERENV', 'SERVICE_NAME') FROM DUAL``.

.. attribute:: AsyncConnection.session_id

    This read-only attribute specifies the session identifier associated with
    the connection. It is the same value returned by the SQL
    ``SELECT SID FROM V$SESSION``.

    It is available only in python-oracledb Thin mode.

    For applications using :ref:`drcp`, the ``session_id`` attribute may
    not contain the current session state until a round-trip is made to the
    database after acquiring a session.  It is recommended to not use this
    attribute if your application uses DRCP but may not perform a
    round-trip.

    .. dbapiattributeextension::

    .. versionadded:: 2.5.0

.. attribute:: AsyncConnection.stmtcachesize

    This read-write attribute specifies the size of the statement cache. This
    value can make a significant difference in performance if you have a small
    number of statements that you execute repeatedly.

    The default value is *20*.

    See :ref:`Statement Caching <stmtcache>` for more information.

.. attribute:: AsyncConnection.thin

    This read-only attribute returns a boolean indicating if the connection was
    established with the python-oracledb Thin mode (*True*) or python-oracledb
    Thick mode (*False*).

.. attribute:: AsyncConnection.transaction_in_progress

    This read-only attribute specifies whether a transaction is currently in
    progress on the database associated with the connection.

.. attribute:: AsyncConnection.username

    This read-only attribute returns the name of the user which established the
    connection to the database.

.. attribute:: AsyncConnection.version

    This read-only attribute returns the version of the database to which a
    connection has been established.
