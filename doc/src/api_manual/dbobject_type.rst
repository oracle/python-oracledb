.. _dbobjecttype:

*************************
API: DbObjectType Objects
*************************

.. currentmodule:: oracledb

DbObjectType Class
==================

.. autoclass:: DbObjectType

    A DbObjectType object is returned with :meth:`Connection.gettype()` call
    and is available as the :data:`Var.type` for variables containing Oracle
    Database objects.

    .. dbapiobjectextension::

DbObjectType Methods
--------------------

.. automethod:: DbObjectType.__call__

.. automethod:: DbObjectType.newobject

DbObjectType Attributes
-----------------------

.. autoproperty:: DbObjectType.attributes

.. autoproperty:: DbObjectType.element_type

   See :ref:`database type constants <dbtypes>`.

.. autoproperty:: DbObjectType.iscollection

.. autoproperty:: DbObjectType.name

.. autoproperty:: DbObjectType.package_name

.. autoproperty:: DbObjectType.schema

.. _dbobject:

DbObject Class
================

.. autoclass:: DbObject

    A DbObject object is returned by the :meth:`DbObjectType.newobject()` call
    and can be bound to variables of type :data:`~oracledb.DB_TYPE_OBJECT`.
    Attributes can be retrieved and set directly.

    .. dbapiobjectextension::

DbObject Methods
----------------

.. automethod:: DbObject.append

.. automethod:: DbObject.asdict

.. automethod:: DbObject.aslist

.. automethod:: DbObject.copy

.. automethod:: DbObject.delete

.. automethod:: DbObject.exists

.. automethod:: DbObject.extend

.. automethod:: DbObject.first

.. automethod:: DbObject.getelement

.. automethod:: DbObject.last

.. automethod:: DbObject.next

.. automethod:: DbObject.prev

.. automethod:: DbObject.setelement

.. automethod:: DbObject.size

.. automethod:: DbObject.trim

DbObject Attributes
-------------------

.. autoproperty:: DbObject.type

.. _dbobjectattr:

DbObjectAttribute Class
=======================

.. autoclass:: DbObjectAttr

    The elements of :attr:`DbObjectType.attributes` are instances of this
    type.

    .. dbapiobjectextension::

DbObjectAttr Attributes
-----------------------

.. autoproperty:: DbObjectAttr.max_size

    .. versionadded:: 3.0.0

.. autoproperty:: DbObjectAttr.name

.. autoproperty:: DbObjectAttr.precision

    .. versionadded:: 3.0.0

.. autoproperty:: DbObjectAttr.scale

    .. versionadded:: 3.0.0

.. autoproperty:: DbObjectAttr.type

    See :ref:`database type constants <dbtypes>`.
