.. _pipelineobj:

*********************
API: Pipeline Objects
*********************

.. currentmodule:: oracledb

Pipelining is only supported in python-oracledb Thin mode with
:ref:`asyncio <concurrentprogramming>`. See :ref:`pipelining` for more
information about pipelining.

.. note::

    True pipelining is only available when connected to Oracle Database version
    23, or later.

.. versionadded:: 2.4.0

.. _pipelineobjs:

Pipeline Class
==============

.. autoclass:: Pipeline

    Pipeline objects represent a pipeline used to execute multiple database
    operations.  A Pipeline object is created by calling
    :meth:`oracledb.create_pipeline()`.

.. _pipelinemethods:

Pipeline Methods
----------------

.. automethod:: Pipeline.add_callfunc

.. automethod:: Pipeline.add_callproc

.. automethod:: Pipeline.add_commit

.. automethod:: Pipeline.add_execute

.. automethod:: Pipeline.add_executemany

    .. seealso::

        :ref:`batchstmnt`

.. automethod:: Pipeline.add_fetchall

    .. versionchanged:: 3.4.0

        The ``fetch_lobs`` and ``fetch_decimals`` parameters were added.

.. automethod:: Pipeline.add_fetchmany

    .. versionchanged:: 3.4.0

        The ``fetch_lobs`` and ``fetch_decimals`` parameters were added.

    .. seealso::

        :ref:`roundtrips`, and :ref:`rowlimit`

.. automethod:: Pipeline.add_fetchone

    .. versionchanged:: 3.4.0

        The ``fetch_lobs`` and ``fetch_decimals`` parameters were added.

    .. seealso::

        :ref:`rowlimit`

Pipeline Attributes
-------------------

.. autoproperty:: Pipeline.operations

.. _pipelineopobjs:

PipelineOp Class
================

.. autoclass:: PipelineOp

    A PipelineOp object should be created by calling the methods in the
    :ref:`Pipeline class <pipelineobjs>`.

.. _pipelineopattrs:

PipelineOp Attributes
---------------------

.. autoproperty:: PipelineOp.arraysize

    .. seealso::

        :ref:`tuningfetch`

.. autoproperty:: PipelineOp.fetch_decimals

    .. versionadded:: 3.4.0

.. autoproperty:: PipelineOp.fetch_lobs

    .. versionadded:: 3.4.0

.. autoproperty:: PipelineOp.keyword_parameters

.. autoproperty:: PipelineOp.name

.. autoproperty:: PipelineOp.num_rows

.. autoproperty:: PipelineOp.op_type

    See :ref:`pipeline-operation-types` for types of operations.

.. autoproperty:: PipelineOp.parameters

.. autoproperty:: PipelineOp.return_type

.. autoproperty:: PipelineOp.rowfactory

.. autoproperty:: PipelineOp.statement

.. _pipelineopresultobjs:

PipelineOpResult Objects
========================

.. autoclass:: PipelineOpResult

    When :meth:`AsyncConnection.run_pipeline()` is called, it returns a list of
    PipelineOpResult objects. These objects contain the results of the executed
    :ref:`PipelineOp objects <pipelineopobjs>` operations.

PipelineOpResult Attributes
---------------------------

.. autoproperty:: PipelineOpResult.columns

    .. versionadded:: 2.5.0

.. autoproperty:: PipelineOpResult.error

.. autoproperty:: PipelineOpResult.operation

.. autoproperty:: PipelineOpResult.return_value

.. autoproperty:: PipelineOpResult.rows

.. autoproperty:: PipelineOpResult.warning

    .. versionadded:: 2.5.0

    .. seealso::

        :ref:`PL/SQL Compilation Warnings  <pipelinewarning>`
