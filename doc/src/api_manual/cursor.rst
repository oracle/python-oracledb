.. _cursorobj:

*******************
API: Cursor Objects
*******************

.. currentmodule:: oracledb

Cursor Class
============

.. autoclass:: Cursor

    A cursor object should be created with :meth:`Connection.cursor()`.

Cursor Methods
==============

.. automethod:: Cursor.__enter__

    .. dbapimethodextension::

.. automethod:: Cursor.__exit__

    .. dbapimethodextension::

.. automethod:: Cursor.__iter__

    .. dbapimethodextension::
        It is mentioned in PEP 249 as an optional extension.

.. automethod:: Cursor.arrayvar

    Array variables can only be used for PL/SQL associative arrays with
    contiguous keys. For PL/SQL associative arrays with sparsely populated keys
    or for varrays and nested tables, the approach shown in this
    `example <https://github.com/oracle/python-oracledb/blob/main/
    samples/plsql_collection.py>`__ needs to be used.

    .. dbapimethodextension::

.. automethod:: Cursor.bindnames

    .. dbapimethodextension::

.. automethod:: Cursor.callfunc

    See :ref:`plsqlfunc` for examples.

    .. dbapimethodextension::

    .. note::

        In line with the Python DB API, it is not recommended to call
        :meth:`setinputsizes()` prior to calling this function.  Use
        :meth:`var()` instead. In existing code that calls
        :meth:`setinputsizes()`, the first item in the :meth:`setinputsizes()`
        parameter list refers to the return value of the PL/SQL function.

.. automethod:: Cursor.callproc

    See :ref:`plsqlproc` for an example.

    .. note::

        The DB API definition does not allow for keyword parameters.

.. automethod:: Cursor.close

.. automethod:: Cursor.execute

    .. versionchanged:: 3.4.0

        The ``fetch_lobs`` and ``fetch_decimals`` parameters were added.

    .. versionchanged:: 3.3.0

        The ``suspend_on_success`` parameter was added.

    .. note::

        The DB API definition does not define the return value of this method.

.. automethod:: Cursor.executemany

    .. versionchanged:: 3.4.0

        The ``batch_size`` parameter was added.

    .. versionchanged:: 3.3.0

        Added support for passing data frames in the ``parameters`` parameter.
        The ``suspend_on_success`` parameter was added.

.. automethod:: Cursor.fetchall

    See :ref:`fetching` for an example.

.. automethod:: Cursor.fetchmany

    See :ref:`fetching` for an example.

.. automethod:: Cursor.fetchone

    See :ref:`fetching` for an example.

.. automethod:: Cursor.getarraydmlrowcounts

    .. dbapimethodextension::

.. automethod:: Cursor.getbatcherrors

    .. dbapimethodextension::

.. automethod:: Cursor.getimplicitresults

    .. dbapimethodextension::

       It is most like the DB API method nextset(), but unlike that method
       (which requires that the next result set overwrite the current result
       set), this method returns cursors which can be fetched independently of
       each other.

.. automethod:: Cursor.parse

    .. dbapimethodextension::

    .. note::

        You can parse any DML or DDL statement. DDL statements are executed
        immediately and an implied commit takes place. You can also parse
        PL/SQL statements.

.. automethod:: Cursor.prepare

    See :ref:`Statement Caching <stmtcache>` for more information.

    .. dbapimethodextension::

.. automethod:: Cursor.scroll

    .. dbapimethodextension::
        It is mentioned in PEP 249 as an optional extension.

.. automethod:: Cursor.setinputsizes

    .. note::

        This function should not be used for bind variables passed to
        :meth:`callfunc()` or :meth:`callproc()`.  Instead, use :meth:`var()`.

        If this function is used with :meth:`callfunc()`, the first parameter
        in the list refers to the return value of the PL/SQL function.

.. automethod:: Cursor.setoutputsize

.. automethod:: Cursor.var

    .. versionchanged:: 1.4.0

        The ``convert_nulls`` parameter was added.

    .. dbapimethodextension::

Cursor Attributes
=================

.. autoproperty:: Cursor.arraysize

    See :ref:`Tuning Fetch Performance <tuningfetch>` for more information.

.. autoproperty:: Cursor.bindvars

    .. dbapiattributeextension::

.. autoproperty:: Cursor.connection

    .. dbapimethodextension::
        It is mentioned in PEP 249 as an optional extension.

.. autoproperty:: Cursor.description

    .. versionchanged:: 1.4.0

        Previously, this attribute was a sequence of 7-tuples.  Each of these
        tuples contained information describing one query column: "(name, type,
        display_size, internal_size, precision, scale, null_ok)".

.. autoproperty:: Cursor.fetchvars

    .. dbapiattributeextension::

.. autoproperty:: Cursor.inputtypehandler

    See :ref:`inputtypehandlers`.

    .. dbapiattributeextension::

.. autoproperty:: Cursor.lastrowid

.. autoproperty:: Cursor.outputtypehandler

    See :ref:`outputtypehandlers`.

    .. dbapiattributeextension::

    .. versionchanged:: 1.4.0

        The method signature was changed. The previous signature
        handler(cursor, name, default_type, length, precision, scale) will
        still work but is deprecated and will be removed in a future version.

.. autoproperty:: Cursor.prefetchrows

    See :ref:`Tuning Fetch Performance <tuningfetch>` for more information.

    .. dbapimethodextension::

.. autoproperty:: Cursor.rowcount

.. autoproperty:: Cursor.rowfactory

    See :ref:`rowfactories`.

    .. dbapiattributeextension::

.. autoproperty:: Cursor.scrollable

    .. dbapiattributeextension::

.. autoproperty:: Cursor.statement

    .. dbapiattributeextension::

.. autoproperty:: Cursor.warning

    See :ref:`plsqlwarning` for more information.

    .. dbapiattributeextension::

    .. versionadded:: 2.0.0
