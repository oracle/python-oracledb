.. _pipelineobj:

*********************
API: Pipeline Objects
*********************

Pipelining is only supported in python-oracledb Thin mode with
:ref:`asyncio <concurrentprogramming>`. See :ref:`pipelining` for more
information about pipelining.

.. note::

    True pipelining is only available when connected to Oracle Database 23ai.

.. versionadded:: 2.4.0

.. _pipelineobjs:

Pipeline Objects
================

Pipeline objects represent a pipeline used to execute multiple database
operations.  A Pipeline object is created by calling
:meth:`oracledb.create_pipeline()`.

.. _pipelinemethods:

Pipeline Methods
----------------

.. method:: Pipeline.add_callfunc(name, return_type, parameters=None, keyword_parameters=None)

    Adds an operation to the pipeline that calls a stored PL/SQL function with
    the given parameters and return type. The created
    :ref:`PipelineOp object <pipelineopobjs>` is also returned from this
    function. :ref:`pipelineopattrs` can be used to examine the operation, if
    needed.

    When the Pipeline is executed, the
    :ref:`PipelineOpResult object <pipelineopresultobjs>` that is returned for
    this operation will have the :attr:`~PipelineOpResult.return_value`
    attribute populated with the return value of the PL/SQL function if the
    call completes successfully.

.. method:: Pipeline.add_callproc(name, parameters=None, keyword_parameters=None)

    Adds an operation that calls a stored procedure with the given parameters.
    The created :ref:`PipelineOp object <pipelineopobjs>` is also returned
    from this function. :ref:`pipelineopattrs` can be used to examine the
    operation, if needed.

.. method:: Pipeline.add_commit()

    Adds an operation that performs a commit.

.. method:: Pipeline.add_execute(statement, parameters=None)

    Adds an operation that executes a statement with the given parameters.
    The created :ref:`PipelineOp object <pipelineopobjs>` is also returned
    from this function. :ref:`pipelineopattrs` can be used to examine the
    operation, if needed.

    Do not use this for queries that return rows.  Instead use
    :meth:`Pipeline.add_fetchall()`, :meth:`Pipeline.add_fetchmany()`, or
    :meth:`Pipeline.add_fetchone()`.

.. method:: Pipeline.add_executemany(statement, parameters)

    Adds an operation that executes a SQL statement once using all bind value
    mappings or sequences found in the sequence parameters. This can be used to
    insert, update, or delete multiple rows in a table. It can also invoke a
    PL/SQL procedure multiple times. See :ref:`batchstmnt`.

    The created :ref:`PipelineOp object <pipelineopobjs>` is also returned from
    this function. :ref:`pipelineopattrs` can be used to examine the operation,
    if needed.

    The ``parameters`` parameter can be a list of tuples, where each tuple item
    maps to one bind variable placeholder in ``statement``. It can also be a
    list of dictionaries, where the keys match the bind variable placeholder
    names in ``statement``. If there are no bind values, or values have
    previously been bound, the ``parameters`` value can be an integer
    specifying the number of iterations.

.. method:: Pipeline.add_fetchall(statement, parameters=None, arraysize=None, rowfactory=None)

    Adds an operation that executes a query and returns all of the rows from
    the result set.  The created :ref:`PipelineOp object <pipelineopobjs>` is
    also returned from this function. :ref:`pipelineopattrs` can be used to
    examine the operation, if needed.

    When the Pipeline is executed, the :ref:`PipelineOpResult
    object <pipelineopresultobjs>` that is returned for this operation will
    have the :attr:`~PipelineOpResult.rows` attribute populated with the list
    of rows returned by the query.

    The default value for ``arraysize`` is :attr:`defaults.arraysize`.

    Internally, this operation's :attr:`Cursor.prefetchrows` size is set to the
    value of the explicit or default ``arraysize`` parameter value.

.. method:: Pipeline.add_fetchmany(statement, parameters=None, num_rows=None, rowfactory=None)

    Adds an operation that executes a query and returns up to the specified
    number of rows from the result set.  The created
    :ref:`PipelineOp object <pipelineopobjs>` is also returned from this
    function. :ref:`pipelineopattrs` can be used to examine the operation, if
    needed.

    When the Pipeline is executed, the
    :ref:`PipelineOpResult object <pipelineopresultobjs>` that is returned for
    this operation will have the :attr:`~PipelineOpResult.rows` attribute
    populated with the list of rows returned by the query.

    The default value for ``num_rows`` is the value of
    :attr:`defaults.arraysize`.

    Internally, this operation's :attr:`Cursor.prefetchrows` size is set to the
    value of the explicit or default ``num_rows`` parameter, allowing all rows
    to be fetched in one :ref:`round-trip <roundtrips>`

    Since only one fetch is performed for a query operation, consider adding a
    ``FETCH NEXT`` clause to the statement to prevent the database processing
    rows that will never be fetched, see :ref:`rowlimit`.

.. method:: Pipeline.add_fetchone(statement, parameters=None, rowfactory=None)

    Adds an operation that executes a query and returns the first row of the
    result set if one exists.  The created
    :ref:`PipelineOp object <pipelineopobjs>` is also returned from this
    function. :ref:`pipelineopattrs` can be used to examine the operation, if
    needed.

    When the Pipeline is executed, the
    :ref:`PipelineOpResult object <pipelineopresultobjs>` that is returned for
    this operation will have the :attr:`~PipelineOpResult.rows` attribute
    populated with this row if the query is performed successfully.

    Internally, this operation's :attr:`Cursor.prefetchrows` and
    :attr:`Cursor.arraysize` sizes will be set to 1.

    Since only one fetch is performed for a query operation, consider adding a
    ``WHERE`` condition or using a ``FETCH NEXT`` clause in the statement to
    prevent the database processing rows that will never be fetched, see
    :ref:`rowlimit`.

Pipeline Attributes
-------------------

.. attribute:: Pipeline.operations

    This read-only attribute returns the list of operations associated with
    the pipeline.

.. _pipelineopobjs:

PipelineOp Objects
==================

PipelineOp objects are created by calling the methods in the
:ref:`Pipeline class <pipelineobjs>`.

.. _pipelineopattrs:

PipelineOp Attributes
---------------------

.. attribute:: PipelineOp.arraysize

    This read-only attribute returns the :ref:`array size <tuningfetch>` that
    will be used when fetching query rows with :meth:`Pipeline.add_fetchall()`.
    For all other operations, the value returned is *0*.

.. attribute:: PipelineOp.keyword_parameters

    This read-only attribute returns the keyword parameters to the stored
    procedure or function being called by the operation, if applicable.

.. attribute:: PipelineOp.name

    This read-only attribute returns the name of the stored procedure or
    function being called by the operation, if applicable.

.. attribute:: PipelineOp.num_rows

    This read-only attribute returns the number of rows to fetch when
    performing a query of a specific number of rows. For all other operations,
    the value returned is *0*.

.. attribute:: PipelineOp.op_type

    This read-only attribute returns the type of operation that is taking
    place. See :ref:`pipeline-operation-types` for types of operations.

.. attribute:: PipelineOp.parameters

    This read-only attribute returns the parameters to the stored procedure or
    function or the parameters bound to the statement being executed by the
    operation, if applicable.

.. attribute:: PipelineOp.return_type

    This read-only attribute returns the return type of the stored function
    being called by the operation, if applicable.

.. attribute:: PipelineOp.rowfactory

    This read-only attribute returns the row factory callable function to be
    used in a query executed by the operation, if applicable.

.. attribute:: PipelineOp.statement

    This read-only attribute returns the statement being executed by the
    operation, if applicable.

.. _pipelineopresultobjs:

PipelineOpResult Objects
========================

When :meth:`AsyncConnection.run_pipeline()` is called, it returns a list of
PipelineOpResult objects. These objects contain the results of the executed
:ref:`PipelineOp objects <pipelineopobjs>` operations.

PipelineOpResult Attributes
---------------------------

.. attribute:: PipelineOpResult.columns

    This read-only attribute is a list of :ref:`FetchInfo<fetchinfoobj>`
    objects. This attribute will be *None* for operations that do not return
    rows.

    .. versionadded:: 2.5.0

.. attribute:: PipelineOpResult.error

    This read-only attribute returns the error that occurred when running this
    operation. If no error occurred, then the value *None* is returned.

.. attribute:: PipelineOpResult.operation

    This read-only attribute returns the :ref:`PipelineOp <pipelineopobjs>`
    operation object that generated the result.

.. attribute:: PipelineOpResult.return_value

    This read-only attribute returns the return value of the called PL/SQL
    function, if a function was called for the operation.

.. attribute:: PipelineOpResult.rows

    This read-only attribute returns the rows that were fetched by the
    operation, if a query was executed.

.. attribute:: PipelineOpResult.warning

    This read-only attribute returns any warning that was encountered when
    running this operation. If no warning was encountered, then the value
    *None* is returned. See :ref:`PL/SQL Compilation Warnings
    <pipelinewarning>`.

    .. versionadded:: 2.5.0
