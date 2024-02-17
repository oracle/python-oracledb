.. _asyncconnobj:

****************************
API: AsyncConnection Objects
****************************

An AsyncConnection object can be created with :meth:`oracledb.connect_async()`
or with :meth:`AsyncConnectionPool.acquire()`. AsyncConnections support use of
concurrent programming with `asyncio <https://docs.python.org/3/library/
asyncio.html>`__. Unless explicitly noted as synchronous, the AsyncConnection
methods should be used with ``await``. This object is an extension to the DB
API.

.. versionadded:: 2.0.0

.. note::

    The Asynchronous I/O (asyncio) support in python-oracledb 2.0.0 is a
    pre-release and may change in the next version.

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

.. method:: AsyncConnection.callfunc(name, return_type, parameters=[], \
                keyword_parameters={})

    Calls a PL/SQL function with the given name.

    This is a shortcut for creating a cursor, calling the stored function with
    the cursor, and then closing the cursor.

.. method:: AsyncConnection.callproc(name, parameters=[], \
                keyword_parameters={})

    Calls a PL/SQL procedure with the given name.

    This is a shortcut for creating a cursor, calling the stored procedure
    with the cursor, and then closing the cursor.

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

    A synchronous method that returns a cursor associated with the connection.

.. method:: AsyncConnection.decode_oson(data)

    A synchronous method that decodes OSON-encoded bytes and returns the object
    encoded in those bytes.  This is useful for fetching columns which have the
    check constraint ``IS JSON FORMAT OSON`` enabled.

    .. versionadded:: 2.1.0

.. method:: AsyncConnection.encode_oson(value)

    A synchronous method that encodes a Python value into OSON-encoded bytes
    and returns them. This is useful for inserting into columns which have the
    check constraint ``IS JSON FORMAT OSON`` enabled.

    .. versionadded:: 2.1.0

.. method:: AsyncConnection.execute(statement, parameters=[])

    Executes a statement against the database.

    This is a shortcut for creating a cursor, executing a statement with the
    cursor, and then closing the cursor.

.. method:: AsyncConnection.executemany(statement, parameters=[])

    Prepares a statement for execution against a database and then executes it
    against all parameter mappings or sequences found in the sequence
    parameters.

    This is a shortcut for creating a cursor, calling
    :meth:`AsyncCursor.executemany()` on the cursor, and then closing the
    cursor.

.. method:: AsyncConnection.fetchall(statement, parameters=None, \
                arraysize=None, rowfactory=None)

    Executes a query and returns all of the rows. After the rows are
    fetched, the cursor is closed.

.. method:: AsyncConnection.fetchmany(statement, parameters=None, \
                num_rows=None, rowfactory=None)

    Executes a query and returns up to the specified number of rows. After the
    rows are fetched, the cursor is closed.

.. method:: AsyncConnection.fetchone(statement, parameters=None, \
                rowfactory=None)

    Executes a query and returns the first row of the result set if one exists
    (or None if no rows exist). After the row is fetched, the cursor is
    closed.

.. method:: AsyncConnection.gettype(name)

    Returns a :ref:`type object <dbobjecttype>` given its name. This can then
    be used to create objects which can be bound to cursors created by this
    connection.

.. method:: AsyncConnection.is_healthy()

    A synchronous method that returns a boolean indicating the health status
    of a connection.

    Connections may become unusable in several cases, such as, if the network
    socket is broken, if an Oracle error indicates the connection is unusable,
    or, after receiving a planned down notification from the database.

    This function is best used before starting a new database request on an
    existing standalone connection. Pooled connections internally perform this
    check before returning a connection to the application.

    If this function returns False, the connection should be not be used by the
    application and a new connection should be established instead.

    This function performs a local check. To fully check a connection's health,
    use :meth:`AsyncConnection.ping()` which performs a round-trip to the
    database.

.. method:: AsyncConnection.ping()

    Pings the database to verify if the connection is valid.

.. method:: AsyncConnection.rollback()

    Rolls back any pending transaction.

.. _asynconnattr:

AsyncConnection Attributes
==========================

.. attribute:: AsyncConnection.action

    This write-only attribute sets the action column in the v$session table. It
    is a string attribute but the value None is accepted and treated as an
    empty string.

.. attribute:: AsyncConnection.autocommit

    This read-write attribute determines whether autocommit mode is on or off.
    When autocommit mode is on, all statements are committed as soon as they
    have completed executing.

.. attribute:: AsyncConnection.call_timeout

    This read-write attribute specifies the amount of time (in milliseconds)
    that a single round-trip to the database may take before a timeout will
    occur. A value of 0 means that no timeout will take place.

    If a timeout occurs, the error *DPI-1067* will be returned if the
    connection is still usable.  Alternatively the error *DPI-1080* will be
    returned if the connection has become invalid and can no longer be used.

.. attribute:: AsyncConnection.client_identifier

    This write-only attribute sets the client_identifier column in the
    v$session table.

.. attribute:: AsyncConnection.clientinfo

    This write-only attribute sets the client_info column in the v$session
    table.

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
    monitored. This can be viewed in the ``DBOP_NAME`` column of the
    ``v$sql_monitor`` table.

.. attribute:: AsyncConnection.dsn

    This read-only attribute returns the TNS entry of the database to which a
    connection has been established.

.. attribute:: AsyncConnection.econtext_id

    This write-only attribute specifies the execution context id. This
    value can be found as ecid in the v$session table and econtext_id in the
    auditing tables. The maximum length is 64 bytes.

.. attribute:: AsyncConnection.edition

    This read-only attribute gets the session edition and is only available in
    Oracle Database 11.2 (the server must be at this level or higher for this
    to work). This attribute is ignored in python-oracledb Thin mode.

.. attribute:: AsyncConnection.external_name

    This read-write attribute specifies the external name that is used by the
    connection when logging distributed transactions.

.. attribute:: AsyncConnection.inputtypehandler

    This read-write attribute specifies a method called for each value that is
    bound to a statement executed on any cursor associated with this
    connection.  The method signature is handler(cursor, value, arraysize) and
    the return value is expected to be a variable object or None in which case
    a default variable object will be created. If this attribute is None, the
    default behavior will take place for all values bound to statements.

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

        This attribute is only available when Oracle Database 12.1 or later is
        in use

.. attribute:: AsyncConnection.max_open_cursors

    This read-only attribute specifies the maximum number of cursors that the
    database can have open concurrently. It is the same value returned by the
    SQL ``SELECT VALUE FROM V$PARAMETER WHERE NAME = 'open_cursors'``.

.. attribute:: AsyncConnection.module

    This write-only attribute sets the module column in the v$session table.
    The maximum length for this string is 48 and if you exceed this length you
    will get ORA-24960.

.. attribute:: AsyncConnection.outputtypehandler

    This read-write attribute specifies a method called for each column that is
    going to be fetched from any cursor associated with this connection. The
    method signature is ``handler(cursor, metadata)`` and the return value is
    expected to be a :ref:`variable object<varobj>` or None in which case a
    default variable object will be created. If this attribute is None, the
    default behavior will take place for all columns fetched from cursors.

    See :ref:`outputtypehandlers`.

.. attribute:: AsyncConnection.sdu

    This read-only attribute specifies the size of the Session Data Unit (SDU)
    that is being used by the connection. The value will be the lesser of the
    requested python-oracledb size and the maximum size allowed by the database
    network configuration.

.. attribute:: AsyncConnection.service_name

    This read-only attribute specifies the Oracle Database service name
    associated with the connection.  This is the same value returned by the SQL
    ``SELECT SYS_CONTEXT('USERENV', 'SERVICE_NAME') FROM DUAL``.

.. attribute:: AsyncConnection.stmtcachesize

    This read-write attribute specifies the size of the statement cache. This
    value can make a significant difference in performance if you have a small
    number of statements that you execute repeatedly.

    The default value is 20.

    See :ref:`Statement Caching <stmtcache>` for more information.

.. attribute:: AsyncConnection.thin

    This read-only attribute returns a boolean indicating if the connection was
    established with the python-oracledb Thin mode (True) or python-oracledb
    Thick mode (False).

.. attribute:: AsyncConnection.transaction_in_progress

    This read-only attribute specifies whether a transaction is currently in
    progress on the database associated with the connection.

.. attribute:: AsyncConnection.username

    This read-only attribute returns the name of the user which established the
    connection to the database.

.. attribute:: AsyncConnection.version

    This read-only attribute returns the version of the database to which a
    connection has been established.
