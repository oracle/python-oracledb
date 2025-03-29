.. _connobj:

***********************
API: Connection Objects
***********************

A Connection object can be created with :meth:`oracledb.connect()` or with
:meth:`ConnectionPool.acquire()`.

.. note::

    Any outstanding database transaction will be rolled back when the
    connection object is destroyed or closed.  You must perform a commit first
    if you want data to persist in the database, see :ref:`txnmgmnt`.

Connection Methods
==================

.. method:: Connection.__enter__()

    The entry point for the connection as a context manager. It returns itself.

    .. dbapimethodextension::

.. method:: Connection.__exit__()

    The exit point for the connection as a context manager. This will close
    the connection and roll back any uncommitted transaction.

    .. dbapimethodextension::

.. method:: Connection.begin([formatId, transactionId, branchId])

    Explicitly begins a new transaction. Without parameters, this explicitly
    begins a local transaction; otherwise, this explicitly begins a distributed
    (global) transaction with the given parameters. See the Oracle
    documentation for more details.

    Note that in order to make use of global (distributed) transactions, the
    :attr:`~Connection.internal_name` and :attr:`~Connection.external_name`
    attributes must be set.

    .. deprecated:: 1.0

    Use the method :meth:`Connection.tpc_begin()` instead.

    .. dbapimethodextension::

.. method:: Connection.cancel()

    Breaks a long-running statement.

    .. dbapimethodextension::

.. method:: Connection.changepassword(oldpassword, newpassword)

    Changes the password for the user to which the connection is
    connected.

    .. dbapimethodextension::

.. method:: Connection.close()

    Closes the connection now and makes it unusable for further operations.
    An Error exception will be raised if any operation is attempted with this
    connection after this method is completed successfully.

    All open cursors and LOBs created by the connection will be closed and will
    also no longer be usable.

    Internally, references to the connection are held by cursor objects,
    LOB objects, subscription objects, etc. Once all of these references are
    released, the connection itself will be closed automatically. Either
    control references to these related objects carefully or explicitly close
    connections in order to ensure sufficient resources are available.

.. method:: Connection.commit()

    Commits any pending transactions to the database.

.. method:: Connection.createlob(lob_type, data=None)

    Creates and returns a new temporary :ref:`LOB object <lobobj>` of the
    specified type. The ``lob_type`` parameter should be one of
    :data:`oracledb.DB_TYPE_CLOB`, :data:`oracledb.DB_TYPE_BLOB`, or
    :data:`oracledb.DB_TYPE_NCLOB`.

    If data is supplied, it will be written to the temporary LOB before it is
    returned.

    .. versionchanged:: 2.0

        The parameter ``data`` was added.

    .. dbapimethodextension::

.. method:: Connection.cursor(scrollable=False)

    Returns a new :ref:`cursor object <cursorobj>` using the connection.

.. method:: Connection.decode_oson(data)

    Decodes `OSON-encoded <https://www.oracle.com/pls/topic/lookup?ctx=dblatest
    &id=GUID-911D302C-CFAF-406B-B6A5-4E99DD38ABAD>`__ bytes and returns the
    object encoded in those bytes.  This is useful for fetching columns which
    have the check constraint ``IS JSON FORMAT OSON`` enabled.

    .. versionadded:: 2.1.0

.. method:: Connection.encode_oson(value)

    Encodes a Python value into `OSON-encoded <https://www.oracle.com/pls/
    topic/lookup?ctx=dblatest&id=GUID-911D302C-CFAF-406B-B6A5-4E99DD38ABAD>`__
    bytes and returns them. This is useful for inserting into columns which
    have the check constraint ``IS JSON FORMAT OSON`` enabled.

    .. versionadded:: 2.1.0

.. method:: Connection.fetch_df_all(statement, parameters=None, \
            arraysize=None)

    Fetches all rows of the SQL query ``statement``, returning them in an
    :ref:`OracleDataFrame <oracledataframeobj>` object. An empty
    OracleDataFrame is returned if there are no rows available.

    The ``parameters`` parameter can be a list of tuples, where each tuple item
    maps to one :ref:`bind variable placeholder <bind>` in ``statement``. It
    can also be a list of dictionaries, where the keys match the bind variable
    placeholder names in ``statement``.

    The ``arraysize`` parameter can be specified to tune performance of
    fetching data across the network. It defaults to
    :attr:`defaults.arraysize`. Internally, the ``fetch_df_all()``'s
    :attr:`Cursor.prefetchrows` size is always set to the value of the explicit
    or default ``arraysize`` parameter value.

    Any LOB fetched must be less than 1 GB.

    See :ref:`dataframeformat` for the supported data types and examples.

    .. note::

        The data frame support in python-oracledb 3.1 is a pre-release and may
        change in a future version.

    .. dbapimethodextension::

    .. versionadded:: 3.0.0

.. method:: Connection.fetch_df_batches(statement, parameters=None, \
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

    Any LOB fetched must be less than 1 GB.

    See :ref:`dataframeformat` for the supported data types and examples.

    .. note::

        The data frame support in python-oracledb 3.1 is a pre-release and may
        change in a future version.

    .. dbapimethodextension::

    .. versionadded:: 3.0.0

.. method:: Connection.getSodaDatabase()

    Returns a :ref:`SodaDatabase <sodadb>` object for Simple Oracle Document
    Access (SODA). All SODA operations are performed either on the returned
    SodaDatabase object or from objects created by the returned SodaDatabase
    object. See `here <https://www.oracle.com/pls/topic/lookup?
    ctx=dblatest&id=GUID-BE42F8D3-B86B-43B4-B2A3-5760A4DF79FB>`__  for
    additional information on SODA.

    .. dbapimethodextension::

.. method:: Connection.gettype(name)

    Returns a :ref:`type object <dbobjecttype>` given its name. This can then
    be used to create objects which can be bound to cursors created by this
    connection.

    .. dbapimethodextension::

.. method:: Connection.is_healthy()

    This function returns a boolean indicating the health status of a
    connection.

    Connections may become unusable in several cases, such as, if the network
    socket is broken, if an Oracle error indicates the connection is unusable,
    or, after receiving a planned down notification from the database.

    This function is best used before starting a new database request on an
    existing :ref:`standalone connections <standaloneconnection>`. For pooled
    connections, the :meth:`ConnectionPool.acquire()` method internally
    performs this check before returning a connection to the application, see
    :ref:`poolhealth`.

    If this function returns *False*, the connection should be not be used by
    the application and a new connection should be established instead.

    This function performs a local check. To fully check a connection's health,
    use :meth:`Connection.ping()` which performs a round-trip to the database.

    .. dbapimethodextension::

.. method:: Connection.msgproperties(payload, correlation, delay, exceptionq, expiration, priority)

    Returns an object specifying the properties of messages used in advanced
    queuing. See :ref:`msgproperties` for more information.

    Each of the parameters are optional. If specified, they act as a shortcut
    for setting each of the equivalently named properties.

    .. dbapimethodextension::

.. method:: Connection.ping()

    Pings the database to verify if the connection is valid. An exception is
    thrown if it is not, in which case the connection should not be used by the
    application and a new connection should be established instead.

    This function performs a :ref:`round-trip <roundtrips>` to the database, so
    it should not be used unnecessarily.

    Note connection pools will perform the same health check automatically,
    based on configuration settings. See :ref:`poolhealth`.

    Also, see :meth:`Connection.is_healthy()` for a lightweight alternative.

    .. dbapimethodextension::

.. method:: Connection.prepare()

    Prepares the distributed (global) transaction for commit. Returns a boolean
    indicating if a transaction was actually prepared in order to avoid the
    error ``ORA-24756 (transaction does not exist)``.

    .. deprecated:: python-oracledb 1.0

    Use the method :meth:`Connection.tpc_prepare()` instead.

    .. dbapimethodextension::

.. method:: Connection.queue(name, payload_type=None)

    Creates a :ref:`queue <queue>` which is used to enqueue and dequeue
    messages in Advanced Queuing.

    The ``name`` parameter is expected to be a string identifying the queue in
    which messages are to be enqueued or dequeued.

    The ``payload_type`` parameter, if specified, is expected to be an
    :ref:`object type <dbobjecttype>` that identifies the type of payload the
    queue expects. If the string "JSON" is specified, JSON data is enqueued and
    dequeued. If not specified, RAW data is enqueued and dequeued.

    For consistency and compliance with the PEP 8 naming style, the
    parameter ``payloadType`` was renamed to ``payload_type``. The old name
    will continue to work as a keyword parameter for a period of time.

    .. dbapimethodextension::

.. method:: Connection.rollback()

    Rolls back any pending transactions.

.. method:: Connection.shutdown([mode])

    Shuts down the database. In order to do this the connection must be
    connected as :data:`~oracledb.SYSDBA` or :data:`~oracledb.SYSOPER`. Two
    calls must be made unless the mode specified is
    :data:`~oracledb.DBSHUTDOWN_ABORT`.
    An example is shown below:

    ::

        import oracledb

        connection = oracledb.connect(mode = oracledb.SYSDBA)
        connection.shutdown(mode = oracledb.DBSHUTDOWN_IMMEDIATE)
        cursor = connection.cursor()
        cursor.execute("alter database close normal")
        cursor.execute("alter database dismount")
        connection.shutdown(mode = oracledb.DBSHUTDOWN_FINAL)

    .. dbapimethodextension::


.. method:: Connection.startup(force=False, restrict=False, pfile=None)

    Starts up the database. This is equivalent to the SQL\*Plus command
    ``startup nomount``. The connection must be connected as
    :data:`~oracledb.SYSDBA` or :data:`~oracledb.SYSOPER` with the
    :data:`~oracledb.PRELIM_AUTH` option specified for this to work.

    The ``pfile`` parameter, if specified, is expected to be a string
    identifying the location of the parameter file (PFILE) which will be used
    instead of the stored parameter file (SPFILE).

    An example is shown below:

    ::

        import oracledb

        connection = oracledb.connect(
                mode=oracledb.SYSDBA | oracledb.PRELIM_AUTH)
        connection.startup()
        connection = oracledb.connect(mode=oracledb.SYSDBA)
        cursor = connection.cursor()
        cursor.execute("alter database mount")
        cursor.execute("alter database open")

    .. dbapimethodextension::

.. method:: Connection.subscribe(namespace=oracledb.SUBSCR_NAMESPACE_DBCHANGE, \
                protocol=oracledb.SUBSCR_PROTO_OCI, callback=None, timeout=0, \
                operations=OPCODE_ALLOPS, port=0, qos=0, ip_address=None, grouping_class=0, \
                grouping_value=0, grouping_type=oracledb.SUBSCR_GROUPING_TYPE_SUMMARY, \
                name=None, client_initiated=False)

    Returns a new :ref:`subscription object <subscrobj>` that receives
    notifications for events that take place in the database that match the
    given parameters.

    The ``namespace`` parameter specifies the namespace the subscription uses.
    It can be one of :data:`oracledb.SUBSCR_NAMESPACE_DBCHANGE` or
    :data:`oracledb.SUBSCR_NAMESPACE_AQ`.

    The ``protocol`` parameter specifies the protocol to use when notifications
    are sent. Currently the only valid value is
    :data:`oracledb.SUBSCR_PROTO_OCI`.

    The ``callback`` is expected to be a callable that accepts a single
    parameter. A :ref:`message object <msgobjects>` is passed to this callback
    whenever a notification is received.

    The ``timeout`` value specifies that the subscription expires after the
    given time in seconds. The default value of *0* indicates that the
    subscription never expires.

    The ``operations`` parameter enables filtering of the messages that are
    sent (insert, update, delete). The default value will send notifications
    for all operations. This parameter is only used when the namespace is set
    to :data:`oracledb.SUBSCR_NAMESPACE_DBCHANGE`.

    The ``port`` parameter specifies the listening port for callback
    notifications from the database server. If not specified, an unused port
    will be selected by the Oracle Client libraries.

    The ``qos`` parameter specifies quality of service options. It should be
    one or more of the following flags, OR'ed together:
    :data:`oracledb.SUBSCR_QOS_RELIABLE`,
    :data:`oracledb.SUBSCR_QOS_DEREG_NFY`,
    :data:`oracledb.SUBSCR_QOS_ROWIDS`,
    :data:`oracledb.SUBSCR_QOS_QUERY`,
    :data:`oracledb.SUBSCR_QOS_BEST_EFFORT`.

    The ``ip_address`` parameter specifies the IP address (*IPv4* or *IPv6*) in
    standard string notation to bind for callback notifications from the
    database server. If not specified, the client IP address will be determined
    by the Oracle Client libraries.

    The ``grouping_class`` parameter specifies what type of grouping of
    notifications should take place. Currently, if set, this value can only be
    set to the value :data:`oracledb.SUBSCR_GROUPING_CLASS_TIME`, which
    will group notifications by the number of seconds specified in the
    ``grouping_value`` parameter. The ``grouping_type`` parameter should be one
    of the values :data:`oracledb.SUBSCR_GROUPING_TYPE_SUMMARY` (the default)
    or :data:`oracledb.SUBSCR_GROUPING_TYPE_LAST`.

    The ``name`` parameter is used to identify the subscription and is
    specific to the selected namespace. If the namespace parameter is
    :data:`oracledb.SUBSCR_NAMESPACE_DBCHANGE` then the name is optional and
    can be any value. If the namespace parameter is
    :data:`oracledb.SUBSCR_NAMESPACE_AQ`, however, the name must be in the
    format '<QUEUE_NAME>' for single consumer queues and
    '<QUEUE_NAME>:<CONSUMER_NAME>' for multiple consumer queues, and identifies
    the queue that will be monitored for messages. The queue name may include
    the schema, if needed.

    The ``client_initiated`` parameter is used to determine if client initiated
    connections or server initiated connections (the default) will be
    established. Client initiated connections are only available in Oracle
    Client 19.4 and Oracle Database 19.4 and higher.

    For consistency and compliance with the PEP 8 naming style, the
    parameter ``ipAddress`` was renamed to ``ip_address``, the parameter
    ``groupingClass`` was renamed to ``grouping_class``, the parameter
    ``groupingValue`` was renamed to ``grouping_value``, the parameter
    ``groupingType`` was renamed to ``grouping_type`` and the parameter
    ``clientInitiated`` was renamed to ``client_initiated``. The old names will
    continue to work as keyword parameters for a period of time.

    .. dbapimethodextension::

    .. note::

        The subscription can be deregistered in the database by calling the
        function :meth:`~Connection.unsubscribe()`. If this method is not
        called and the connection that was used to create the subscription is
        explicitly closed using the function :meth:`~Connection.close()`, the
        subscription will not be deregistered in the database.

.. method:: Connection.tpc_begin(xid, flags, timeout)

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
    :meth:`Connection.tpc_end()` and the time it is resumed with
    :meth:`Connection.tpc_begin()`.The default is *0* seconds.

    The following code sample demonstrates the ``tpc_begin()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        connection.tpc_begin(xid=x, flags=oracledb.TPC_BEGIN_NEW, timeout=30)

    See :ref:`tpc` for information on TPC.

.. method:: Connection.tpc_commit(xid, one_phase)

    Commits a global transaction. When called with no arguments, this method
    commits a transaction previously prepared with
    :meth:`~Connection.tpc_begin()` and optionally prepared with
    :meth:`~Connection.tpc_prepare()`. If :meth:`~Connection.tpc_prepare()`
    is not called, a single phase commit is performed. A transaction manager
    may choose to do this if only a single resource is participating in the
    global transaction.

    If an ``xid`` parameter is passed, then an object should be returned by the
    :meth:`~Connection.xid()` function. This form should be called outside of a
    transaction and is intended for use in recovery.

    The ``one_phase`` parameter is a boolean identifying whether to perform a
    one-phase or two-phase commit. If ``one_phase`` parameter is *True*, a
    single-phase commit is performed. The default value is *False*. This
    parameter is only examined if a value is provided for the ``xid``
    parameter. Otherwise, the driver already knows whether
    :meth:`~Connection.tpc_prepare()` was called for the transaction and
    whether a one-phase or two-phase commit is required.

    The following code sample demonstrates the ``tpc_commit()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        connection.tpc_commit(xid=x, one_phase=False)

    See :ref:`tpc` for information on TPC.

.. method:: Connection.tpc_end(xid, flags)

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
    resumed later by calling :meth:`Connection.tpc_begin()` with the flag
    :data:`oracledb.TPC_BEGIN_RESUME`.

    The following code sample demonstrates the ``tpc_end()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        connection.tpc_end(xid=x, flags=oracledb.TPC_END_NORMAL)

    See :ref:`tpc` for information on TPC.

.. method:: Connection.tpc_forget(xid)

    Causes the database to forget a heuristically completed TPC transaction.
    This function is only intended to be called by transaction managers.

    The ``xid`` parameter is mandatory and should be an object should be
    returned by the :meth:`~Connection.xid()` function.

    The following code sample demonstrates the ``tpc_forget()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        connection.tpc_forget(xid=x)

    See :ref:`tpc` for information on TPC.

.. method:: Connection.tpc_prepare(xid)

    Prepares a two-phase transaction for commit. After this function is called,
    no further activity should take place on this connection until either
    :meth:`~Connection.tpc_commit()` or :meth:`~Connection.tpc_rollback()` have
    been called.

    Returns a boolean indicating whether a commit is needed or not. If you
    attempt to commit when not needed, then it results in the error
    ``ORA-24756: transaction does not exist``.

    If an ``xid`` parameter is passed, then an object should be returned by
    the :meth:`~Connection.xid()` function. If an ``xid`` parameter is not
    passed, then the transaction identifier used by the previous
    :meth:`~Connection.tpc_begin()` is used.

    The following code sample demonstrates the ``tpc_prepare()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        connection.tpc_prepare(xid=x)

    See :ref:`tpc` for information on TPC.

.. method:: Connection.tpc_recover()

    Returns a list of pending transaction identifiers that require recovery.
    Objects of type ``Xid`` (as returned by the :meth:`~Connection.xid()`
    function) are returned and these can be passed to
    :meth:`~Connection.tpc_commit()` or :meth:`~Connection.tpc_rollback()` as
    needed.

    This function queries the DBA_PENDING_TRANSACTIONS view and requires
    "SELECT" privilege on that view.

    The following code sample demonstrates the ``tpc_recover()`` function::

        connection.tpc_recover()


    See :ref:`tpc` for information on TPC.

.. method:: Connection.tpc_rollback(xid)

    Rolls back a global transaction.

    If an ``xid`` parameter is not passed, then it rolls back the transaction
    that was previously started with :meth:`~Connection.tpc_begin()`.

    If an ``xid`` parameter is passed, then an object should be returned by
    :meth:`~Connection.xid()` and the specified transaction is rolled back.
    This form should be called outside of a transaction and is intended for
    use in recovery.

    The following code sample demonstrates the ``tpc_rollback()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        connection.tpc_rollback(xid=x)

    See :ref:`tpc` for information on TPC.

.. method:: Connection.unsubscribe(subscr)

    Unsubscribe from events in the database that were originally subscribed to
    using :meth:`~Connection.subscribe()`. The connection used to unsubscribe
    should be the same one used to create the subscription, or should access
    the same database and be connected as the same user name.

.. method:: Connection.xid (format_id, global_transaction_id, branch_qualifier)

    Returns a global transaction identifier (xid) that can be used with the
    Two-Phase Commit (TPC) functions.

    The ``xid`` contains a format identifier, a global transaction identifier, and
    a branch identifier. There are no checks performed at the Python level. The
    values are checked by ODPI-C when they are passed to the relevant functions.
    .. When this functionality is also supported in the thin driver the checks will be performed at the Python level as well.

    The ``format_id`` parameter should be a positive 32-bit integer. This
    value identifies the format of the ``global_transaction_id`` and
    ``branch_qualifier`` parameters and the value is determined by the
    Transaction Manager (TM), if one is in use.

    The ``global_transaction_id`` and ``branch_qualifier`` parameters should
    be of type bytes or string. If a value of type string is passed, then
    this value will be UTF-8 encoded to bytes. The values cannot exceed 64
    bytes in length.

    The following code sample demonstrates the ``xid()`` function::

        connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")

    See :ref:`tpc` for information on TPC.

.. _connattrs:

Connection Attributes
=====================

.. attribute:: Connection.action

    This write-only attribute sets the ACTION column in the V$SESSION view. It
    is a string attribute but the value *None* is accepted and treated as an
    empty string.

    .. dbapiattributeextension::

.. attribute:: Connection.autocommit

    This read-write attribute determines whether autocommit mode is on or off.
    When autocommit mode is on, all statements are committed as soon as they
    have completed executing.

    .. dbapiattributeextension::

.. attribute:: Connection.call_timeout

    This read-write attribute specifies the amount of time (in milliseconds)
    that a single round-trip to the database may take before a timeout will
    occur. A value of *0* means that no timeout will take place.

    In python-oracledb Thick mode, this attribute is only available in Oracle
    Client 18c or later.

    If a timeout occurs, the error ``DPI-1067`` will be returned if the
    connection is still usable.  Alternatively the error ``DPI-1080`` will be
    returned if the connection has become invalid and can no longer be used.

    For consistency and compliance with the PEP 8 naming style, the
    attribute ``callTimeout`` was renamed to ``call_timeout``. The old name
    will continue to work for a period of time.  The error ``DPI-1080`` was
    also introduced in this release.

    .. dbapiattributeextension::

.. attribute:: Connection.client_identifier

    This write-only attribute sets the CLIENT_IDENTIFIER column in the
    V$SESSION view.

    .. dbapiattributeextension::

.. attribute:: Connection.clientinfo

    This write-only attribute sets the CLIENT_INFO column in the V$SESSION
    view.

    .. dbapiattributeextension::

.. attribute:: Connection.current_schema

    This read-write attribute sets the current schema attribute for the
    session. Setting this value is the same as executing the SQL statement
    ``ALTER SESSION SET CURRENT_SCHEMA``. The attribute is set (and verified) on
    the next call that does a round trip to the server. The value is placed
    before unqualified database objects in SQL statements you then execute.

    .. dbapiattributeextension::

.. attribute:: Connection.db_domain

    This read-only attribute specifies the Oracle Database domain name
    associated with the connection. It is the same value returned by the SQL
    ``SELECT value FROM V$PARAMETER WHERE NAME = 'db_domain'``.

    .. dbapiattributeextension::

    .. versionadded:: 2.0.0

.. attribute:: Connection.db_name

    This read-only attribute specifies the Oracle Database name associated with
    the connection. It is the same value returned by the SQL
    ``SELECT NAME FROM V$DATABASE``.

    .. dbapiattributeextension::

    .. versionadded:: 2.0.0

.. attribute:: Connection.dbop

    This write-only attribute sets the database operation that is to be
    monitored. This can be viewed in the DBOP_NAME column of the
    V$SQL_MONITOR view.

    .. dbapiattributeextension::

.. attribute:: Connection.dsn

    This read-only attribute returns the TNS entry of the database to which a
    connection has been established.

    .. dbapiattributeextension::

.. attribute:: Connection.econtext_id

    This write-only attribute specifies the execution context id. This value
    can be found as the ECID column in the V$SESSION view and ECONTEXT_ID in
    the auditing tables. The maximum length is 64 bytes.

.. attribute:: Connection.edition

    This read-only attribute gets the session edition and is only available
    with Oracle Database 11.2, or later.

    .. dbapiattributeextension::

.. attribute:: Connection.external_name

    This read-write attribute specifies the external name that is used by the
    connection when logging distributed transactions.

    .. dbapiattributeextension::

.. attribute:: Connection.handle

    This read-only attribute returns the Oracle Call Interface (OCI) service
    context handle for the connection. It is primarily provided to facilitate
    testing the creation of a connection using the OCI service context handle.

    This property is only relevant in the python-oracledb Thick mode.

    .. dbapiattributeextension::

.. attribute:: Connection.inputtypehandler

    This read-write attribute specifies a method called for each value that is
    bound to a statement executed on any cursor associated with this
    connection.  The method signature is handler(cursor, value, arraysize) and
    the return value is expected to be a variable object or *None* in which
    case a default variable object will be created. If this attribute is
    *None*, the default behavior will take place for all values bound to
    statements.

    See :ref:`inputtypehandlers`.

    .. dbapiattributeextension::

.. attribute:: Connection.instance_name

    This read-only attribute specifies the Oracle Database instance name
    associated with the connection. It is the same value as the SQL expression
    ``sys_context('userenv', 'instance_name')``.

    .. dbapiattributeextension::

    .. versionadded:: 1.4.0

.. attribute:: Connection.internal_name

    This read-write attribute specifies the internal name that is used by the
    connection when logging distributed transactions.

    .. dbapiattributeextension::

.. attribute:: Connection.ltxid

    This read-only attribute returns the logical transaction id for the
    connection. It is used within Oracle Transaction Guard as a means of
    ensuring that transactions are not duplicated. See :ref:`tg` for more
    information.

    This is only available with Oracle Database 12.1 or later. In
    python-oracledb Thick mode, it also requires Oracle Client libraries 12.1
    or later.

    .. dbapiattributeextension::

    .. versionchanged:: 3.0.0

        This attribute was added to python-oracledb Thin mode.

.. attribute:: Connection.max_identifier_length

    This read-only attribute specifies the maximum database identifier length
    in bytes supported by the database to which the connection has been
    established.  See `Database Object Naming Rules
    <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&
    id=GUID-75337742-67FD-4EC0-985F-741C93D918DA>`__. The value may be
    *None*, *30*, or *128*. The value *None* indicates the size cannot be
    reliably determined by python-oracledb, which occurs when using Thick mode
    with Oracle Client libraries 12.1 (or older) to connect to Oracle Database
    12.2, or later.

    .. versionadded:: 2.5.0

.. attribute:: Connection.max_open_cursors

    This read-only attribute specifies the maximum number of cursors that the
    database can have open concurrently. It is the same value returned by the
    SQL ``SELECT VALUE FROM V$PARAMETER WHERE NAME = 'open_cursors'``. When
    using python-oracledb Thick mode, Oracle Client libraries 12.1 (or later)
    are required.

    .. dbapiattributeextension::

    .. versionadded:: 2.0.0

.. attribute:: Connection.module

    This write-only attribute sets the MODULE column in the V$SESSION view.
    The maximum length for this string is 48 and if you exceed this length you
    will get ``ORA-24960``.

    .. dbapiattributeextension::

.. attribute:: Connection.outputtypehandler

    This read-write attribute specifies a method called for each column that is
    going to be fetched from any cursor associated with this connection. The
    method signature is ``handler(cursor, metadata)`` and the return value is
    expected to be a :ref:`variable object<varobj>` or *None* in which case a
    default variable object will be created. If this attribute is *None*, the
    default behavior will take place for all columns fetched from cursors.

    See :ref:`outputtypehandlers`.

    .. versionchanged:: 1.4

        The method signature was changed. The previous signature
        ``handler(cursor, name, default_type, length, precision, scale)`` will
        still work but is deprecated and will be removed in a future version.

    .. dbapiattributeextension::

.. attribute:: Connection.proxy_user

    This read-only attribute returns the name of the user which was used as a
    proxy when creating the connection to the database.

    .. dbapiattributeextension::

    .. versionadded:: 2.0.0

.. attribute:: Connection.sdu

    This read-only attribute specifies the size of the Session Data Unit (SDU)
    that is being used by the connection. The value will be the lesser of the
    requested python-oracledb size and the maximum size allowed by the database
    network configuration. It is available only in the python-oracledb Thin
    mode.

    .. dbapiattributeextension::

    .. versionadded:: 2.0.0

.. attribute:: Connection.serial_num

    This read-only attribute specifies the session serial number associated
    with the connection. It is the same value returned by the SQL
    ``SELECT SERIAL# FROM V$SESSION WHERE SID=SYS_CONTEXT('USERENV', 'SID')``.
    It is available only in python-oracledb Thin mode.


    For applications using :ref:`drcp`, the ``serial_num`` attribute may not
    contain the current session state until a round-trip is made to the
    database after acquiring a session.  It is recommended to not use this
    attribute if your application uses DRCP but may not perform a round-trip.

    .. dbapiattributeextension::

    .. versionadded:: 2.5.0

.. attribute:: Connection.service_name

    This read-only attribute specifies the Oracle Database service name
    associated with the connection.  This is the same value returned by the SQL
    ``SELECT SYS_CONTEXT('USERENV', 'SERVICE_NAME') FROM DUAL``.

    .. dbapiattributeextension::

    .. versionadded:: 2.0.0

.. attribute:: Connection.session_id

    This read-only attribute specifies the session identifier associated with
    the connection. It is the same value returned by the SQL
    ``SELECT SYS_CONTEXT('USERENV', 'SID') FROM DUAL``. It is available
    only in python-oracledb Thin mode.

    For applications using :ref:`drcp`, the ``session_id`` attribute may not
    contain the current session state until a round-trip is made to the
    database after acquiring a session.  It is recommended to not use this
    attribute if your application uses DRCP but may not perform a round-trip.

    .. dbapiattributeextension::

    .. versionadded:: 2.5.0

.. attribute:: Connection.stmtcachesize

    This read-write attribute specifies the size of the statement cache. This
    value can make a significant difference in performance if you have a small
    number of statements that you execute repeatedly.

    The default value is *20*.

    See :ref:`Statement Caching <stmtcache>` for more information.

    .. dbapiattributeextension::

.. attribute:: Connection.tag

    This read-write attribute initially contains the actual tag of the session
    that was acquired from a pool by :meth:`ConnectionPool.acquire()`. If the
    connection was not acquired from a pool or no tagging parameters were
    specified (``tag`` and ``matchanytag``) when the connection was acquired
    from the pool, this value will be None. If the value is changed, it must
    be a string containing name=value pairs like "k1=v1;k2=v2".

    If this value is not *None* when the connection is released back to the
    pool it will be used to retag the session. This value can be overridden in
    the call to :meth:`ConnectionPool.release()`.

    .. dbapiattributeextension::

.. attribute:: Connection.thin

    This read-only attribute returns a boolean indicating if the connection was
    established with the python-oracledb Thin mode (*True*) or python-oracledb
    Thick mode (*False*).

    .. dbapiattributeextension::

.. attribute:: Connection.transaction_in_progress

    This read-only attribute specifies whether a transaction is currently in
    progress on the database associated with the connection.

    .. dbapiattributeextension::

    .. versionadded:: 2.0.0

.. attribute:: Connection.username

    This read-only attribute returns the name of the user which established the
    connection to the database.

    .. dbapiattributeextension::

.. attribute:: Connection.version

    This read-only attribute returns the version of the database to which a
    connection has been established.

    .. dbapiattributeextension::

    .. note::

        If you connect to Oracle Database 18 (or higher) in python-oracledb
        Thick mode using Oracle Client libraries 12.2 (or lower) you will only
        receive the base version (such as 18.0.0.0.0) instead of the full
        version (such as 18.3.0.0.0).

.. attribute:: Connection.warning

    This read-only attribute provides an :ref:`oracledb._Error<exchandling>`
    object giving information about any database warnings (such as the password
    being in the grace period, or the pool being created with a smaller than
    requested size due to database resource restrictions) that were generated
    during connection establishment or by :meth:`oracledb.create_pool()`. The
    attribute will be present if there was a warning, but creation otherwise
    completed successfully. The connection will be usable despite the warning.

    For :ref:`standalone connections <standaloneconnection>`,
    ``Connection.warning`` will be present for the lifetime of the connection.

    For :ref:`pooled connections <connpooling>`, ``Connection.warning`` will be
    cleared when a connection is released to the pool such as with
    :meth:`ConnectionPool.release()`.

    In python-oracledb Thick mode, warnings may be generated during pool
    creation itself.  These warnings will be placed on new connections created
    by the pool, provided no warnings were generated by the individual
    connection creations, in which case those connection warnings will be
    returned.

    If no warning was generated the value *None* is returned.

    .. dbapiattributeextension::

    .. versionadded:: 2.0.0
