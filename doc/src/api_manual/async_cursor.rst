.. _asynccursorobj:

************************
API: AsyncCursor Objects
************************

An AsyncCursor object can be created with :meth:`AsyncConnection.cursor()`.
Unless explicitly noted as synchronous, the AsyncCursor methods should be used
with ``await``. This object is an extension to the DB API.

.. versionadded:: 2.0.0

.. note::

    AsyncCursor objects are only supported in the python-oracledb Thin mode.

.. _asynccursormeth:

AsyncCursor Methods
===================

.. method:: AsyncCursor.__aiter__()

    Returns the cursor itself to be used as an asynchronous iterator.

.. method:: AsyncCursor.__enter__()

    The entry point for the cursor as a context manager. It returns itself.

.. method:: AsyncCursor.__exit__()

    The exit point for the cursor as a context manager. It closes the cursor.

.. method:: AsyncCursor.arrayvar(typ, value, [size])

    A synchronous method that creates an array variable associated with the
    cursor of the given type and size and returns a
    :ref:`variable object <varobj>`. The value is either an integer specifying
    the number of elements to allocate or it is a list and the number of
    elements allocated is drawn from the size of the list. If the value is a
    list, the variable is also set with the contents of the list. If the size
    is not specified and the type is a string or binary, 4000 bytes is
    allocated. This is needed for passing arrays to PL/SQL (in cases where
    the list might be empty and the type cannot be determined automatically) or
    returning arrays from PL/SQL.

    Array variables can only be used for PL/SQL associative arrays with
    contiguous keys. For PL/SQL associative arrays with sparsely populated keys
    or for varrays and nested tables, the approach shown in this
    `example <https://github.com/oracle/python-oracledb/blob/main/
    samples/plsql_collection.py>`__ needs to be used.

.. method:: AsyncCursor.bindnames()

    A synchronous method that returns the list of bind variable names bound to
    the statement. Note that a statement must have been prepared first.

.. method:: AsyncCursor.callfunc(name, returnType, parameters=None, \
        keyword_parameters=None)

    Calls a function with the given name. The return type is specified in the
    same notation as is required by :meth:`~AsyncCursor.setinputsizes()`. The
    sequence of parameters must contain one entry for each parameter that the
    function expects. Any keyword parameters will be included after the
    positional parameters. The result of the call is the return value of the
    function.

    See :ref:`plsqlfunc` for an example.

    .. note::

        If you intend to call :meth:`AsyncCursor.setinputsizes()` on the cursor
        prior to making this call, then note that the first item in the
        parameter list refers to the return value of the function.

.. method:: AsyncCursor.callproc(name, parameters=None, keyword_parameters=None)

    Calls a procedure with the given name. The sequence of parameters must
    contain one entry for each parameter that the procedure expects. The result
    of the call is a modified copy of the input sequence. Input parameters are
    left untouched; output and input/output parameters are replaced with
    possibly new values. Keyword parameters will be included after the
    positional parameters and are not returned as part of the output sequence.

    See :ref:`plsqlproc` for an example.

.. method:: AsyncCursor.close()

    A synchronous method that closes the cursor now, rather than whenever
    ``__del__`` is called. The cursor will be unusable from this point
    forward; an Error exception will be raised if any operation is attempted
    with the cursor.

.. method:: AsyncCursor.execute(statement, parameters=None, ** keyword_parameters)

    Executes a statement against the database. See :ref:`sqlexecution`.

    Parameters may be passed as a dictionary or sequence or as keyword
    parameters. If the parameters are a dictionary, the values will be bound by
    name and if the parameters are a sequence the values will be bound by
    position. Note that if the values are bound by position, the order of the
    variables is from left to right as they are encountered in the statement
    and SQL statements are processed differently than PL/SQL statements. For
    this reason, it is generally recommended to bind parameters by name instead
    of by position.

    Parameters passed as a dictionary are name and value pairs. The name maps
    to the bind variable name used by the statement and the value maps to the
    Python value you wish bound to that bind variable.

    A reference to the statement will be retained by the cursor. If None or the
    same string object is passed in again, the cursor will execute that
    statement again without performing a prepare or rebinding and redefining.
    This is most effective for algorithms where the same statement is used, but
    different parameters are bound to it (many times). Note that parameters
    that are not passed in during subsequent executions will retain the value
    passed in during the last execution that contained them.

    For maximum efficiency when reusing a statement, it is best to use the
    :meth:`~AsyncCursor.setinputsizes()` method to specify the parameter types and
    sizes ahead of time; in particular, None is assumed to be a string of
    length 1 so any values that are later bound as numbers or dates will raise
    a TypeError exception.

    If the statement is a query, the cursor is returned as a convenience to the
    caller (so it can be used directly as an iterator over the rows in the
    cursor); otherwise, ``None`` is returned.

.. method:: AsyncCursor.executemany(statement, parameters, batcherrors=False, \
        arraydmlrowcounts=False)

    Prepares a statement for execution against a database and then execute it
    against all parameter mappings or sequences found in the sequence
    parameters. See :ref:`batchstmnt`.

    The ``statement`` parameter is managed in the same way as the
    :meth:`~AsyncCursor.execute()` method manages it. If the size of the buffers
    allocated for any of the parameters exceeds 2 GB, you will receive the
    error "DPI-1015: array size of <n> is too large", where <n> varies with the
    size of each element being allocated in the buffer. If you receive this
    error, decrease the number of elements in the sequence parameters.

    If there are no parameters, or parameters have previously been bound, the
    number of iterations can be specified as an integer instead of needing to
    provide a list of empty mappings or sequences.

    When True, the ``batcherrors`` parameter enables batch error support within
    Oracle and ensures that the call succeeds even if an exception takes place
    in one or more of the sequence of parameters. The errors can then be
    retrieved using :meth:`~AsyncCursor.getbatcherrors()`.

    When True, the ``arraydmlrowcounts`` parameter enables DML row counts to be
    retrieved from Oracle after the method has completed. The row counts can
    then be retrieved using :meth:`~AsyncCursor.getarraydmlrowcounts()`.

    Both the ``batcherrors`` parameter and the ``arraydmlrowcounts`` parameter
    can only be true when executing an insert, update, delete or merge
    statement; in all other cases an error will be raised.

    For maximum efficiency, it is best to use the
    :meth:`~AsyncCursor.setinputsizes()` method to specify the parameter types and
    sizes ahead of time; in particular, None is assumed to be a string of
    length 1 so any values that are later bound as numbers or dates will raise
    a TypeError exception.

.. method:: AsyncCursor.fetchall()

    Fetches all (remaining) rows of a query result, returning them as a list of
    tuples. An empty list is returned if no more rows are available. Note that
    the cursor's ``arraysize`` attribute can affect the performance of this
    operation, as internally reads from the database are done in batches
    corresponding to ``arraysize``.

    An exception is raised if the previous call to
    :meth:`~AsyncCursor.execute()` did not produce any result set or no call
    was issued yet.

.. method:: AsyncCursor.fetchmany(size=cursor.arraysize)

    Fetches the next set of rows of a query result, returning a list of tuples.
    An empty list is returned if no more rows are available. Note that the
    cursor's arraysize attribute can affect the performance of this operation.

    The number of rows to fetch is specified by the parameter. If it is not
    given, the cursor's arraysize attribute determines the number of rows to be
    fetched. If the number of rows available to be fetched is fewer than the
    amount requested, fewer rows will be returned.

    An exception is raised if the previous call to
    :meth:`~AsyncCursor.execute()` did not produce any result set or no call
    was issued yet.

.. method:: AsyncCursor.fetchone()

    Fetches the next row of a query result set, returning a single tuple or
    None when no more data is available.

    An exception is raised if the previous call to
    :meth:`~AsyncCursor.execute()` did not produce any result set or no call
    was issued yet.

.. method:: AsyncCursor.getarraydmlrowcounts()

    A synchronous method that retrieves the DML row counts after a call to
    :meth:`~AsyncCursor.executemany()` with arraydmlrowcounts enabled. This
    will return a list of integers corresponding to the number of rows
    affected by the DML statement for each element of the array passed to
    :meth:`~AsyncCursor.executemany()`.

    .. note::

        This method is only available for Oracle 12.1 and later.

.. method:: AsyncCursor.getbatcherrors()

    A synchronous method that retrieves the exceptions that took place after a
    call to :meth:`~AsyncCursor.executemany()` with batcherrors enabled. This
    will return a list of Error objects, one error for each iteration that
    failed. The offset can be determined by looking at the offset attribute of
    the error object.

.. method:: AsyncCursor.getimplicitresults()

    A synchronous method that returns a list of cursors which correspond to
    implicit results made  available from a PL/SQL block or procedure without
    the use of OUT ref cursor parameters. The PL/SQL block or procedure opens
    the cursors and marks them for return to the driver using the procedure
    dbms_sql.return_result. Cursors returned in this fashion should not be
    closed. They will be closed automatically by the parent cursor when it is
    closed. Closing the parent cursor will invalidate the cursors returned by
    this method.

    .. note::

        This method is only available with Oracle Database 12.1 or later. It is
        most like the DB API method nextset(), but unlike that method (which
        requires that the next result set overwrite the current result set),
        this method returns cursors which can be fetched independently of each
        other.

.. method:: AsyncCursor.parse(statement)

    This can be used to parse a statement without actually executing it
    (parsing step is done automatically by Oracle when a statement is
    :meth:`executed <AsyncCursor.execute>`).

    .. note::

        You can parse any DML or DDL statement. DDL statements are executed
        immediately and an implied commit takes place.

.. method:: AsyncCursor.prepare(statement, tag, cache_statement=True)

    A synchronous method that can be used before a call to
    :meth:`~AsyncCursor.execute()` to define the  statement that will be
    executed. When this is done, the prepare phase will not be performed when
    the call to :meth:`~AsyncCursor.execute()` is made with None or the same
    string object as the statement.

    If the ``tag`` parameter is specified and the ``cache_statement`` parameter
    is True, the statement will be returned to the statement cache with the
    given tag.

    If the ``cache_statement`` parameter is False, the statement will be
    removed from the statement cache (if it was found there) or will simply not
    be cached.

    See :ref:`Statement Caching <stmtcache>` for more information.

.. method:: AsyncCursor.setinputsizes(*args, **keywordArgs)

    A synchronous method that can be used before a call to
    :meth:`~AsyncCursor.execute()`, :meth:`~AsyncCursor.executemany()`,
    :meth:`~AsyncCursor.callfunc()` or :meth:`~AsyncCursor.callproc()` to
    predefine memory areas for the operation's parameters. Each parameter
    should be a type object corresponding to the input that will be used or it
    should be an integer specifying the maximum length of a string parameter.
    Use keyword parameters when binding by name and positional parameters when
    binding by position. The singleton None can be used as a parameter when
    using positional parameters to indicate that no space should be reserved
    for that position.

    .. note::

        If you plan to use :meth:`~AsyncCursor.callfunc()` then be aware that the
        first parameter in the list refers to the return value of the function.

.. method:: AsyncCursor.setoutputsize(size, [column])

    This method does nothing and is retained solely for compatibility with the
    DB API. The module automatically allocates as much space as needed to fetch
    LONG and LONG RAW columns (or CLOB as string and BLOB as bytes).

.. method:: AsyncCursor.var(typ, [size, arraysize, inconverter, outconverter, \
        typename, encoding_errors, bypass_decode, convert_nulls])

    A synchronous method that creates a variable with the specified
    characteristics. This method was designed for use with PL/SQL in/out
    variables where the length or type cannot be determined automatically from
    the Python object passed in or for use in input and output type handlers
    defined on cursors or connections.

    The ``typ`` parameter specifies the type of data that should be stored in the
    variable. This should be one of the :ref:`database type constants
    <dbtypes>`, :ref:`DB API constants <types>`, an object type returned from
    the method :meth:`AsyncConnection.gettype()` or one of the following Python
    types:

    .. list-table-with-summary::
        :header-rows: 1
        :class: wy-table-responsive
        :align: center
        :summary: The first column is the Python Type. The second column is the corresponding Database Type.

        * - Python Type
          - Database Type
        * - bool
          - :attr:`oracledb.DB_TYPE_BOOLEAN`
        * - bytes
          - :attr:`oracledb.DB_TYPE_RAW`
        * - datetime.date
          - :attr:`oracledb.DB_TYPE_DATE`
        * - datetime.datetime
          - :attr:`oracledb.DB_TYPE_DATE`
        * - datetime.timedelta
          - :attr:`oracledb.DB_TYPE_INTERVAL_DS`
        * - decimal.Decimal
          - :attr:`oracledb.DB_TYPE_NUMBER`
        * - float
          - :attr:`oracledb.DB_TYPE_NUMBER`
        * - int
          - :attr:`oracledb.DB_TYPE_NUMBER`
        * - str
          - :attr:`oracledb.DB_TYPE_VARCHAR`

    The ``size`` parameter specifies the length of string and raw variables and is
    ignored in all other cases. If not specified for string and raw variables,
    the value 4000 is used.

    The ``arraysize`` parameter specifies the number of elements the variable will
    have. If not specified the bind array size (usually 1) is used. When a
    variable is created in an output type handler this parameter should be set
    to the cursor's array size.

    The ``inconverter`` and ``outconverter`` parameters specify methods used for
    converting values to/from the database. More information can be found in
    the section on :ref:`variable objects<varobj>`.

    The ``typename`` parameter specifies the name of a SQL object type and must be
    specified when using type :data:`oracledb.OBJECT` unless the type object
    was passed directly as the first parameter.

    The ``encoding_errors`` parameter specifies what should happen when decoding
    byte strings fetched from the database into strings. It should be one of
    the values noted in the builtin
    `decode <https://docs.python.org/3/library/stdtypes.html#bytes.decode>`__
    function.

    The ``bypass_decode`` parameter, if specified, should be passed as a
    boolean value. Passing a `True` value causes values of database types
    :data:`~oracledb.DB_TYPE_VARCHAR`, :data:`~oracledb.DB_TYPE_CHAR`,
    :data:`~oracledb.DB_TYPE_NVARCHAR`, :data:`~oracledb.DB_TYPE_NCHAR` and
    :data:`~oracledb.DB_TYPE_LONG` to be returned as `bytes` instead of `str`,
    meaning that python-oracledb does not do any decoding. See :ref:`Fetching raw
    data <fetching-raw-data>` for more information.

    The ``convert_nulls`` parameter, if specified, should be passed as a boolean
    value. Passing the value ``True`` causes the ``outconverter`` to be called
    when a null value is fetched from the database; otherwise, the
    ``outconverter`` is only called when non-null values are fetched from the
    database.

.. _asynccursorattr:

AsyncCursor Attributes
======================

.. attribute:: AsyncCursor.arraysize

    This read-write attribute can be used to tune the number of rows internally
    fetched and buffered by internal calls to the database when fetching rows
    from SELECT statements and REF CURSORS.  The value can drastically affect
    the performance of a query since it directly affects the number of network
    round trips between Python and the database.  For methods like
    :meth:`~AsyncCursor.fetchone()` and :meth:`~AsyncCursor.fetchall()` it
    does not change how many rows are returned to the application. For
    :meth:`~AsyncCursor.fetchmany()` it is the default number of rows to fetch.

    The attribute is only used for tuning row and SODA document fetches from
    the database.  It does not affect data inserts.

    Due to the performance benefits, the default ``Cursor.arraysize`` is 100
    instead of the 1 that the Python DB API recommends.

    See :ref:`Tuning Fetch Performance <tuningfetch>` for more information.

.. attribute:: AsyncCursor.bindvars

    This read-only attribute provides the bind variables used for the last
    execute. The value will be either a list or a dictionary depending on
    whether binding was done by position or name. Care should be taken when
    referencing this attribute. In particular, elements should not be removed
    or replaced.

.. attribute:: AsyncCursor.description

    This read-only attribute is a sequence of :ref:`FetchInfo<fetchinfoobj>`
    objects. This attribute will be None for operations that do not return rows
    or if the cursor has not had an operation invoked via the
    :meth:`~AsyncCursor.execute()` method yet.

.. attribute:: AsyncCursor.fetchvars

    This read-only attribute specifies the list of variables created for the
    last query that was executed on the cursor.  Care should be taken when
    referencing this attribute. In particular, elements should not be removed
    or replaced.

.. attribute:: AsyncCursor.inputtypehandler

    This read-write attribute specifies a method called for each value that is
    bound to a statement executed on the cursor and overrides the attribute
    with the same name on the connection if specified. The method signature is
    handler(cursor, value, arraysize) and the return value is expected to be a
    variable object or None in which case a default variable object will be
    created. If this attribute is None, the default behavior will take place
    for all values bound to the statements.

.. attribute:: AsyncCursor.lastrowid

    This read-only attribute returns the rowid of the last row modified by the
    cursor. If no row was modified by the last operation performed on the
    cursor, the value None is returned.

.. attribute:: AsyncCursor.outputtypehandler

    This read-write attribute specifies a method called for each column that is
    to be fetched from this cursor. The method signature is
    handler(cursor, metadata) and the return value is expected to be a
    :ref:`variable object<varobj>` or None in which case a default variable
    object will be created. If this attribute is None, then the default
    behavior will take place for all columns fetched from this cursor.

    See :ref:`outputtypehandlers`.

.. attribute:: AsyncCursor.prefetchrows

    This read-write attribute can be used to tune the number of rows that the
    python-oracledb fetches when a SELECT statement is executed. This value can
    reduce the number of round-trips to the database that are required to fetch
    rows but at the cost of additional memory. Setting this value to 0 can be
    useful when the timing of fetches must be explicitly controlled.

    The attribute is only used for tuning row fetches from the database.  It
    does not affect data inserts.

    See :ref:`Tuning Fetch Performance <tuningfetch>` for more information.

.. attribute:: AsyncCursor.rowcount

    This read-only attribute specifies the number of rows that have currently
    been fetched from the cursor (for select statements) or that have been
    affected by the operation (for insert, update, delete and merge
    statements). For all other statements the value is always zero. If the
    cursor or connection is closed, the value returned is -1.

.. attribute:: AsyncCursor.rowfactory

    This read-write attribute specifies a method to call for each row that is
    retrieved from the database. Ordinarily, a tuple is returned for each row
    but if this attribute is set, the method is called with the tuple that
    would normally be returned, and the result of the method is returned
    instead.

    See :ref:`rowfactories`.

.. attribute:: AsyncCursor.scrollable

    This read-write boolean attribute specifies whether the cursor can be
    scrolled or not. By default, cursors are not scrollable, as the server
    resources and response times are greater than nonscrollable cursors. This
    attribute is checked and the corresponding mode set in Oracle when calling
    the method :meth:`~AsyncCursor.execute()`.
