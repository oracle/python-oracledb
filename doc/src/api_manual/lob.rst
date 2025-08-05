.. _lobobj:

****************
API: LOB Objects
****************

.. currentmodule:: oracledb

LOB Class
=========

.. autoclass:: LOB

    A LOB object should be created with :meth:`Connection.createlob()`.

    This object is returned by default whenever Oracle :data:`CLOB`,
    :data:`BLOB`, and :data:`BFILE` columns are fetched.

    This type object is the Python type of :data:`DB_TYPE_BLOB`,
    :data:`DB_TYPE_BFILE`, :data:`DB_TYPE_CLOB` and :data:`DB_TYPE_NCLOB` data
    that is returned from cursors.

    .. dbapiobjectextension::

    See :ref:`lobdata` for more information about using LOBs.

LOB Methods
===========

.. automethod:: LOB.close

.. automethod:: LOB.fileexists

.. automethod:: LOB.getchunksize

.. automethod:: LOB.getfilename

.. automethod:: LOB.isopen

.. automethod:: LOB.open

.. automethod:: LOB.read

.. automethod:: LOB.setfilename

.. automethod:: LOB.size

.. automethod:: LOB.trim

.. automethod:: LOB.write

LOB Attributes
==============

.. autoproperty:: LOB.type

    See :ref:`database type constants <dbtypes>`.
