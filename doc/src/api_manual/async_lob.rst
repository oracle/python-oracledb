.. _asynclobobj:

*********************
API: AsyncLOB Objects
*********************

.. currentmodule:: oracledb

AsyncLOB Class
==============

.. autoclass:: AsyncLOB

    An AsyncLOB object can be created with
    :meth:`AsyncConnection.createlob()`. Also, this object is returned whenever
    Oracle :data:`CLOB`, :data:`BLOB` and :data:`BFILE` columns are fetched.

    .. dbapiobjectextension::

    See :ref:`lobdata` for more information about using LOBs.

    .. note::

        AsyncLOB objects are only supported in python-oracledb Thin mode.

.. _asynclobmeth:

AsyncLOB Methods
================

.. automethod:: AsyncLOB.close

.. automethod:: AsyncLOB.fileexists

.. automethod:: AsyncLOB.getchunksize

.. automethod:: AsyncLOB.getfilename

.. automethod:: AsyncLOB.isopen

.. automethod:: AsyncLOB.open

.. automethod:: AsyncLOB.read

.. automethod:: AsyncLOB.setfilename

.. automethod:: AsyncLOB.size

.. automethod:: AsyncLOB.trim

.. automethod:: AsyncLOB.write

.. _asynclobattr:

AsyncLOB Attributes
===================

.. autoproperty:: AsyncLOB.type

    See :ref:`database type constants <dbtypes>`.
