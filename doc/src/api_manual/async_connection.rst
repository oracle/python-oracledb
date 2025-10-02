.. _asyncconnobj:

****************************
API: AsyncConnection Objects
****************************

.. currentmodule:: oracledb

AsyncConnection Class
=====================

.. autoclass:: AsyncConnection

    An AsyncConnection object should be created with
    :meth:`oracledb.connect_async()` or with
    :meth:`AsyncConnectionPool.acquire()`. AsyncConnections support use of
    concurrent programming with
    `asyncio <https://docs.python.org/3/library/asyncio.html>`__.

    .. dbapiobjectextension::

    .. versionadded:: 2.0.0

    .. note::

        AsyncConnection objects are only supported in python-oracledb Thin
        mode.

    .. note::

        Any outstanding database transaction will be rolled back when the
        connection object is destroyed or closed.  You must perform a
        :meth:`commit <commit>` first if you want data to persist in the
        database, see :ref:`txnasync`.

.. _asyncconnmeth:

AsyncConnection Methods
=======================

.. automethod:: AsyncConnection.__aenter__

.. automethod:: AsyncConnection.__aexit__

.. automethod:: AsyncConnection.begin_sessionless_transaction

    See :ref:`sessionlesstxns`.

    .. versionadded:: 3.3.0

.. automethod:: AsyncConnection.callfunc

.. automethod:: AsyncConnection.callproc

.. automethod:: AsyncConnection.cancel

.. automethod:: AsyncConnection.changepassword

.. automethod:: AsyncConnection.close

    .. note::

        Asynchronous connections are not automatically closed at the end of
        scope. This is different to synchronous connection
        behavior. Asynchronous connections should either be explicitly closed,
        or have been initially created via a `context manager
        <https://docs.python.org/3/library/stdtypes.html#context-manager-types>`__
        ``with`` block.

.. automethod:: AsyncConnection.commit

.. automethod:: AsyncConnection.createlob

.. automethod:: AsyncConnection.cursor

.. automethod:: AsyncConnection.decode_oson

    .. versionadded:: 2.1.0

.. automethod:: AsyncConnection.direct_path_load

    See :ref:`directpathloads`.

    .. versionadded:: 3.4.0

    .. dbapimethodextension::

.. automethod:: AsyncConnection.encode_oson

    .. versionadded:: 2.1.0

.. automethod:: AsyncConnection.execute

.. automethod:: AsyncConnection.executemany

.. automethod:: AsyncConnection.fetchall

    .. versionchanged:: 3.4.0

        The ``fetch_lobs`` and ``fetch_decimals`` parameters were added.

.. automethod:: AsyncConnection.fetch_df_all

    See :ref:`dataframeformat` for the supported data types and examples.

    .. versionchanged:: 3.4.0

        The ``fetch_decimals`` and ``requested_schema`` parameters were added.

    .. versionadded:: 3.0.0

.. automethod:: AsyncConnection.fetch_df_batches

    See :ref:`dataframeformat` for the supported data types and examples.

    .. versionchanged:: 3.4.0

        The ``fetch_decimals`` and ``requested_schema`` parameters were added.

    .. versionadded:: 3.0.0

.. automethod:: AsyncConnection.fetchmany

    .. versionchanged:: 3.4.0

        The ``fetch_lobs`` and ``fetch_decimals`` parameters were added.

.. automethod:: AsyncConnection.fetchone

    .. versionchanged:: 3.4.0

        The ``fetch_lobs`` and ``fetch_decimals`` parameters were added.

.. automethod:: AsyncConnection.gettype

.. automethod:: AsyncConnection.is_healthy

.. automethod:: AsyncConnection.msgproperties

    .. versionadded:: 3.1.0

.. automethod:: AsyncConnection.ping()

.. automethod:: AsyncConnection.queue

    .. versionadded:: 3.1.0

.. automethod:: AsyncConnection.resume_sessionless_transaction

    See :ref:`sessionlesstxns`.

    .. versionadded:: 3.3.0

.. automethod:: AsyncConnection.rollback

.. automethod:: AsyncConnection.run_pipeline

    See :ref:`pipelining` for more information.

    .. note::

        True pipelining requires Oracle Database version 23, or later.

        When you connect to an older database, operations are sequentially
        executed by python-oracledb. Each operation concludes before the next
        is sent to the database. There is no reduction in round-trips and no
        performance benefit. This usage is only recommended for code
        portability such as when preparing for a database upgrade.

    .. versionadded:: 2.4.0

.. automethod:: AsyncConnection.suspend_sessionless_transaction

    See :ref:`sessionlesstxns`.

    .. versionadded:: 3.3.0

.. automethod:: AsyncConnection.tpc_begin

    The following code sample demonstrates the ``tpc_begin()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        await connection.tpc_begin(xid=x, flags=oracledb.TPC_BEGIN_NEW, timeout=30)

    See :ref:`tpc` for information on TPC.

    .. versionadded:: 2.3.0

.. automethod:: AsyncConnection.tpc_commit

    The following code sample demonstrates the ``tpc_commit()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        await connection.tpc_commit(xid=x, one_phase=False)

    See :ref:`tpc` for information on TPC.

    .. versionadded:: 2.3.0

.. automethod:: AsyncConnection.tpc_end

    The following code sample demonstrates the ``tpc_end()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        await connection.tpc_end(xid=x, flags=oracledb.TPC_END_NORMAL)

    See :ref:`tpc` for information on TPC.

    .. versionadded:: 2.3.0

.. automethod:: AsyncConnection.tpc_forget

    The following code sample demonstrates the ``tpc_forget()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        await connection.tpc_forget(xid=x)

    See :ref:`tpc` for information on TPC.

    .. versionadded:: 2.3.0

.. automethod:: AsyncConnection.tpc_prepare

    The following code sample demonstrates the ``tpc_prepare()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        await connection.tpc_prepare(xid=x)

    See :ref:`tpc` for information on TPC.

    .. versionadded:: 2.3.0

.. automethod:: AsyncConnection.tpc_recover

    The following code sample demonstrates the ``tpc_recover()`` function::

        await connection.tpc_recover()

    See :ref:`tpc` for information on TPC.

    .. versionadded:: 2.3.0

.. automethod:: AsyncConnection.tpc_rollback

    The following code sample demonstrates the ``tpc_rollback()`` function::

        x = connection.xid(format_id=1, global_transaction_id="tx1", branch_qualifier="br1")
        await connection.tpc_rollback(xid=x)

    See :ref:`tpc` for information on TPC.

    .. versionadded:: 2.3.0

.. automethod:: AsyncConnection.xid

.. _asynconnattr:

AsyncConnection Attributes
==========================

.. autoproperty:: AsyncConnection.action

.. autoproperty:: AsyncConnection.autocommit

.. autoproperty:: AsyncConnection.call_timeout

.. autoproperty:: AsyncConnection.client_identifier

.. autoproperty:: AsyncConnection.clientinfo

.. autoproperty:: AsyncConnection.current_schema

.. autoproperty:: AsyncConnection.db_domain

.. autoproperty:: AsyncConnection.db_name

.. autoproperty:: AsyncConnection.dbop

.. autoproperty:: AsyncConnection.dsn

.. autoproperty:: AsyncConnection.econtext_id

.. autoproperty:: AsyncConnection.edition

.. autoproperty:: AsyncConnection.external_name

.. autoproperty:: AsyncConnection.inputtypehandler

.. autoproperty:: AsyncConnection.instance_name

.. autoproperty:: AsyncConnection.internal_name

.. autoproperty:: AsyncConnection.ltxid

.. autoproperty:: AsyncConnection.max_identifier_length

    .. versionadded:: 2.5.0

.. autoproperty:: AsyncConnection.max_open_cursors

.. autoproperty:: AsyncConnection.module

.. autoproperty:: AsyncConnection.outputtypehandler

    See :ref:`outputtypehandlers`.

.. autoproperty:: AsyncConnection.sdu

.. autoproperty:: AsyncConnection.serial_num

    .. versionadded:: 2.5.0

.. autoproperty:: AsyncConnection.service_name

.. autoproperty:: AsyncConnection.session_id

    .. versionadded:: 2.5.0

.. autoproperty:: AsyncConnection.stmtcachesize

    See :ref:`Statement Caching <stmtcache>` for more information.

.. autoproperty:: AsyncConnection.thin

.. autoproperty:: AsyncConnection.transaction_in_progress

.. autoproperty:: AsyncConnection.username

.. autoproperty:: AsyncConnection.version
