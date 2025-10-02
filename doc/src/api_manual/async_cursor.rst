.. _asynccursorobj:

************************
API: AsyncCursor Objects
************************

.. currentmodule:: oracledb

AsyncCursor Class
=================

.. autoclass:: AsyncCursor

    An AsyncCursor object should be created with
    :meth:`AsyncConnection.cursor()`.

    .. dbapiobjectextension::

    .. versionadded:: 2.0.0

    .. note::

        AsyncCursor objects are only supported in python-oracledb Thin mode.

.. _asynccursormeth:

AsyncCursor Methods
===================

.. automethod:: AsyncCursor.__aiter__

.. automethod:: AsyncCursor.__aenter__

.. automethod:: AsyncCursor.__aexit__

.. automethod:: AsyncCursor.arrayvar

.. automethod:: AsyncCursor.bindnames

.. automethod:: AsyncCursor.callfunc

    See :ref:`plsqlfunc` for examples.

    .. note::

        In line with the Python DB API, it is not recommended to call
        :meth:`setinputsizes()` prior to calling this function.
        Use :meth:`AsyncCursor.var()` instead.  In existing code that calls
        :meth:`~AsyncCursor.setinputsizes()`, the first item in the
        :meth:`~AsyncCursor.setinputsizes()` parameter list refers to the
        return value of the PL/SQL function.

.. automethod:: AsyncCursor.callproc

    See :ref:`plsqlproc` for an example.

.. automethod:: AsyncCursor.close

    .. note::

        Asynchronous cursors are not automatically closed at the end of
        scope. This is different to synchronous cursor behavior. Asynchronous
        cursors should either be explicitly closed, or have been initially
        created via a `context manager
        <https://docs.python.org/3/library/stdtypes.html#context-manager-types>`__
        ``with`` block.

.. automethod:: AsyncCursor.execute

    .. versionchanged:: 3.4.0

        The ``fetch_lobs`` and ``fetch_decimals`` parameters were added.

    .. versionchanged:: 3.3.0

        The ``suspend_on_success`` parameter was added.

.. automethod:: AsyncCursor.executemany

    .. versionchanged:: 3.4.0

        The ``batch_size`` parameter was added.

    .. versionchanged:: 3.3.0

        Added support for passing data frames in the ``parameters`` parameter.
        The ``suspend_on_success`` parameter was added.

.. automethod:: AsyncCursor.fetchall

.. automethod:: AsyncCursor.fetchmany

.. automethod:: AsyncCursor.fetchone

.. automethod:: AsyncCursor.getarraydmlrowcounts

.. automethod:: AsyncCursor.getbatcherrors

.. automethod:: AsyncCursor.getimplicitresults

    .. note::

        It is most like the DB API method nextset(), but unlike that method
        (which requires that the next result set overwrite the current result
        set), this method returns cursors which can be fetched independently of
        each other.

.. automethod:: AsyncCursor.parse

    .. note::

        You can parse any DML or DDL statement. DDL statements are executed
        immediately and an implied commit takes place.

.. automethod:: AsyncCursor.prepare

    See :ref:`Statement Caching <stmtcache>` for more information.

.. automethod:: AsyncCursor.setinputsizes

    .. note::

        :meth:`AsyncCursor.setinputsizes()` should not be used for bind
        variables passed to :meth:`AsyncCursor.callfunc()` or
        :meth:`AsyncCursor.callproc()`.  Instead, use `AsyncCursor.var()`.

        If :meth:`AsyncCursor.setinputsizes()` is used with
        :meth:`AsyncCursor.callfunc()`, the first parameter in the list refers
        to the return value of the PL/SQL function.

.. automethod:: AsyncCursor.scroll

.. automethod:: AsyncCursor.setoutputsize

.. automethod:: AsyncCursor.var

.. _asynccursorattr:

AsyncCursor Attributes
======================

.. autoproperty:: AsyncCursor.arraysize

    See :ref:`Tuning Fetch Performance <tuningfetch>` for more information.

.. autoproperty:: AsyncCursor.bindvars

.. autoproperty:: AsyncCursor.connection

.. autoproperty:: AsyncCursor.description

.. autoproperty:: AsyncCursor.fetchvars

.. autoproperty:: AsyncCursor.inputtypehandler

.. autoproperty:: AsyncCursor.lastrowid

.. autoproperty:: AsyncCursor.outputtypehandler

    See :ref:`outputtypehandlers`.

.. autoproperty:: AsyncCursor.prefetchrows

    See :ref:`Tuning Fetch Performance <tuningfetch>` for more information.

.. autoproperty:: AsyncCursor.rowcount

.. autoproperty:: AsyncCursor.rowfactory

    See :ref:`rowfactories`.

.. autoproperty:: AsyncCursor.scrollable
