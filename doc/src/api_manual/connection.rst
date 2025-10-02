.. _connobj:

***********************
API: Connection Objects
***********************

.. currentmodule:: oracledb

Connection Class
================

.. autoclass:: Connection

    A connection object should be created with :meth:`oracledb.connect()` or
    with :meth:`ConnectionPool.acquire()`.

    .. note::

        Any outstanding database transaction will be rolled back when the
        connection object is destroyed or closed.  You must perform a commit
        first if you want data to persist in the database, see :ref:`txnmgmnt`.

Connection Methods
==================

.. automethod:: Connection.__enter__

    .. dbapimethodextension::

.. automethod:: Connection.__exit__

    .. dbapimethodextension::

.. automethod:: Connection.begin

    .. deprecated:: 1.0

    Use the method :meth:`tpc_begin()` instead.

    .. dbapimethodextension::

.. automethod:: Connection.begin_sessionless_transaction

    See :ref:`sessionlesstxns`.

    .. versionadded:: 3.3.0

.. automethod:: Connection.cancel

    .. dbapimethodextension::

.. automethod:: Connection.changepassword

    .. dbapimethodextension::

.. automethod:: Connection.close

.. automethod:: Connection.commit

.. automethod:: Connection.createlob

    .. versionchanged:: 2.0

        The parameter ``data`` was added.

    .. dbapimethodextension::

.. automethod:: Connection.cursor

.. automethod:: Connection.decode_oson

    .. versionadded:: 2.1.0

    .. dbapimethodextension::

.. automethod:: Connection.direct_path_load

    See :ref:`directpathloads`.

    .. versionadded:: 3.4.0

    .. dbapimethodextension::

.. automethod:: Connection.encode_oson

    .. versionadded:: 2.1.0

    .. dbapimethodextension::

.. automethod:: Connection.fetch_df_all

    See :ref:`dataframeformat` for the supported data types and examples.

    .. dbapimethodextension::

    .. versionchanged:: 3.4.0

        The ``fetch_decimals`` and ``requested_schema`` parameters were added.

    .. versionadded:: 3.0.0

.. automethod:: Connection.fetch_df_batches

    See :ref:`dataframeformat` for the supported data types and examples.

    .. dbapimethodextension::

    .. versionchanged:: 3.4.0

        The ``fetch_decimals`` and ``requested_schema`` parameters were added.

    .. versionadded:: 3.0.0

.. automethod:: Connection.getSodaDatabase

    .. dbapimethodextension::

.. automethod:: Connection.gettype

    .. dbapimethodextension::

.. automethod:: Connection.is_healthy

    .. dbapimethodextension::

.. automethod:: Connection.msgproperties

    .. dbapimethodextension::

.. automethod:: Connection.ping

    .. dbapimethodextension::

.. automethod:: Connection.prepare

    .. deprecated:: 1.0. Use the method :meth:`tpc_prepare()` instead.

    .. dbapimethodextension::

.. automethod:: Connection.queue

    .. dbapimethodextension::

.. automethod:: Connection.resume_sessionless_transaction

    See :ref:`sessionlesstxns`.

    .. versionadded:: 3.3.0

.. automethod:: Connection.rollback

.. automethod:: Connection.shutdown

    See :ref:`startup`.

    .. dbapimethodextension::

.. automethod:: Connection.startup

    See :ref:`startup`.

    .. dbapimethodextension::

.. automethod:: Connection.subscribe

    .. dbapimethodextension::

    .. note::

        The subscription can be deregistered in the database by calling the
        function :meth:`unsubscribe()`. If this method is not called and the
        connection that was used to create the subscription is explicitly
        closed using the function :meth:`close()`, the subscription will not be
        deregistered in the database.

.. automethod:: Connection.suspend_sessionless_transaction

    See :ref:`sessionlesstxns`.

    .. versionadded:: 3.3.0

    .. dbapimethodextension::

.. automethod:: Connection.tpc_begin

    The following code sample demonstrates the ``tpc_begin()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        connection.tpc_begin(xid=x, flags=oracledb.TPC_BEGIN_NEW, timeout=30)

    See :ref:`tpc` for information on TPC.

.. automethod:: Connection.tpc_commit

    The following code sample demonstrates the ``tpc_commit()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        connection.tpc_commit(xid=x, one_phase=False)

    See :ref:`tpc` for information on TPC.

.. automethod:: Connection.tpc_end

    The following code sample demonstrates the ``tpc_end()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        connection.tpc_end(xid=x, flags=oracledb.TPC_END_NORMAL)

    See :ref:`tpc` for information on TPC.

    .. dbapimethodextension::

.. automethod:: Connection.tpc_forget

    The following code sample demonstrates the ``tpc_forget()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        connection.tpc_forget(xid=x)

    See :ref:`tpc` for information on TPC.

    .. dbapimethodextension::

.. automethod:: Connection.tpc_prepare

    The following code sample demonstrates the ``tpc_prepare()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        connection.tpc_prepare(xid=x)

    See :ref:`tpc` for information on TPC.

.. automethod:: Connection.tpc_recover

    The following code sample demonstrates the ``tpc_recover()`` function::

        connection.tpc_recover()

    See :ref:`tpc` for information on TPC.

.. automethod:: Connection.tpc_rollback

    The following code sample demonstrates the ``tpc_rollback()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        connection.tpc_rollback(xid=x)

    See :ref:`tpc` for information on TPC.

.. automethod:: Connection.unsubscribe

    .. dbapimethodextension::

.. automethod:: Connection.xid

    The following code sample demonstrates the ``xid()`` function::

        connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")

    See :ref:`tpc` for information on TPC.

    .. dbapimethodextension::

.. _connattrs:

Connection Attributes
=====================

.. autoproperty:: Connection.action

    .. dbapiattributeextension::

.. autoproperty:: Connection.autocommit

    .. dbapiattributeextension::

.. autoproperty:: Connection.call_timeout

    .. dbapiattributeextension::

.. autoproperty:: Connection.client_identifier

    .. dbapiattributeextension::

.. autoproperty:: Connection.clientinfo

    .. dbapiattributeextension::

.. autoproperty:: Connection.current_schema

    .. dbapiattributeextension::

.. autoproperty:: Connection.db_domain

    .. dbapiattributeextension::

    .. versionadded:: 2.0.0

.. autoproperty:: Connection.db_name

    .. dbapiattributeextension::

    .. versionadded:: 2.0.0

.. autoproperty:: Connection.dbop

    .. dbapiattributeextension::

.. autoproperty:: Connection.dsn

    .. dbapiattributeextension::

.. autoproperty:: Connection.econtext_id

    .. dbapiattributeextension::

.. autoproperty:: Connection.edition

    .. dbapiattributeextension::

.. autoproperty:: Connection.external_name

    .. dbapiattributeextension::

.. autoproperty:: Connection.handle

    .. dbapiattributeextension::

.. autoproperty:: Connection.inputtypehandler

    See :ref:`inputtypehandlers`.

    .. dbapiattributeextension::

.. autoproperty:: Connection.instance_name

    .. dbapiattributeextension::

    .. versionadded:: 1.4.0

.. autoproperty:: Connection.internal_name

    .. dbapiattributeextension::

.. autoproperty:: Connection.ltxid

    .. dbapiattributeextension::

    .. versionchanged:: 3.0.0

        This attribute was added to python-oracledb Thin mode.

.. autoproperty:: Connection.max_identifier_length

    .. dbapiattributeextension::

    .. versionadded:: 2.5.0

.. autoproperty:: Connection.max_open_cursors

    .. dbapiattributeextension::

    .. versionadded:: 2.0.0

.. autoproperty:: Connection.module

    .. dbapiattributeextension::

.. autoproperty:: Connection.outputtypehandler

    See :ref:`outputtypehandlers`.

    .. versionchanged:: 1.4

        The method signature was changed. The previous signature
        ``handler(cursor, name, default_type, length, precision, scale)`` will
        still work but is deprecated and will be removed in a future version.

    .. dbapiattributeextension::

.. autoproperty:: Connection.proxy_user

    .. dbapiattributeextension::

    .. versionadded:: 2.0.0

.. autoproperty:: Connection.sdu

    .. dbapiattributeextension::

    .. versionadded:: 2.0.0

.. autoproperty:: Connection.serial_num

    .. dbapiattributeextension::

    .. versionadded:: 2.5.0

.. autoproperty:: Connection.service_name

    .. dbapiattributeextension::

    .. versionadded:: 2.0.0

.. autoproperty:: Connection.session_id

    .. dbapiattributeextension::

    .. versionadded:: 2.5.0

.. autoproperty:: Connection.stmtcachesize

    See :ref:`Statement Caching <stmtcache>` for more information.

    .. dbapiattributeextension::

.. autoproperty:: Connection.tag

    .. dbapiattributeextension::

.. autoproperty:: Connection.thin

    See :ref:`vsessconinfo`.

    .. dbapiattributeextension::

.. autoproperty:: Connection.transaction_in_progress

    .. dbapiattributeextension::

    .. versionadded:: 2.0.0

.. autoproperty:: Connection.username

    This read-only attribute returns the name of the user which established the
    connection to the database.

    .. dbapiattributeextension::

.. autoproperty:: Connection.version

    This read-only attribute returns the version of the database to which a
    connection has been established.

    .. dbapiattributeextension::

    .. note::

        If you connect to Oracle Database 18 (or higher) in python-oracledb
        Thick mode using Oracle Client libraries 12.2 (or lower) you will only
        receive the base version (such as 18.0.0.0.0) instead of the full
        version (such as 18.3.0.0.0).

.. autoproperty:: Connection.warning

    .. dbapiattributeextension::

    .. versionadded:: 2.0.0
