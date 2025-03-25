.. _dbobjecttype:

*************************
API: DbObjectType Objects
*************************

The DbObjectType object is returned by the :meth:`Connection.gettype()` call
and is available as the :data:`Variable.type` for variables containing Oracle
Database objects.

.. dbapiobjectextension::

DbObjectType Methods
====================

.. method:: DbObjectType([sequence])

    The object type may be called directly and serves as an alternative way of
    calling :meth:`~DbObjectType.newobject()`.

.. method:: DbObjectType.newobject([sequence])

    Returns a new Oracle object of the given type. This object can then be
    modified by setting its attributes and then bound to a cursor for
    interaction with Oracle. If the object type refers to a collection, a
    sequence may be passed and the collection will be initialized with the
    items in that sequence.

DbObjectType Attributes
=======================

.. attribute:: DbObjectType.attributes

    This read-only attribute returns a list of the :ref:`attributes
    <dbobjectattr>` that make up the object type.


.. attribute:: DbObjectType.element_type

    This read-only attribute returns the type of elements found in collections
    of this type, if :attr:`~DbObjectType.iscollection` is *True*; otherwise,
    it returns *None*. If the collection contains objects, this will be
    another object type; otherwise, it will be one of the
    :ref:`database type constants <dbtypes>`.


.. attribute:: DbObjectType.iscollection

    This read-only attribute returns a boolean indicating if the object type
    refers to a collection or not.


.. attribute:: DbObjectType.name

    This read-only attribute returns the name of the type.


.. attribute:: DbObjectType.package_name

    This read-only attribute returns the name of the package, if the type
    refers to a PL/SQL type (otherwise, it returns the value *None*).


.. attribute:: DbObjectType.schema

    This read-only attribute returns the name of the schema that owns the type.

.. _dbobject:

DbObject Objects
================

The DbObject object is returned by the :meth:`DbObjectType.newobject()` call
and can be bound to variables of type :data:`~oracledb.OBJECT`. Attributes can
be retrieved and set directly.

.. dbapiobjectextension::

DbObject Methods
++++++++++++++++

.. method:: DbObject.append(element)

    Appends an element to the collection object. If no elements exist in the
    collection, this creates an element at index 0; otherwise, it creates an
    element immediately following the highest index available in the
    collection.


.. method:: DbObject.asdict()

    Returns a dictionary where the collection's indexes are the keys and the
    elements are its values.


.. method:: DbObject.aslist()

    Returns a list of each of the collection's elements in index order.


.. method:: DbObject.copy()

    Creates a copy of the object and returns it.


.. method:: DbObject.delete(index)

    Deletes the element at the specified index of the collection. If the
    element does not exist or is otherwise invalid, an error is raised. Note
    that the indices of the remaining elements in the collection are not
    changed. In other words, the delete operation creates holes in the
    collection.


.. method:: DbObject.exists(index)

    Returns *True* or *False* indicating if an element exists in the collection
    at the specified index.


.. method:: DbObject.extend(sequence)

    Appends all of the elements in the sequence to the collection. This is
    the equivalent of performing :meth:`~DbObject.append()` for each element
    found in the sequence.


.. method:: DbObject.first()

    Returns the index of the first element in the collection. If the collection
    is empty, *None* is returned.


.. method:: DbObject.getelement(index)

    Returns the element at the specified index of the collection. If no element
    exists at that index, an exception is raised.


.. method:: DbObject.last()

    Returns the index of the last element in the collection. If the collection
    is empty, *None* is returned.


.. method:: DbObject.next(index)

    Returns the index of the next element in the collection following the
    specified index. If there are no elements in the collection following the
    specified index, *None* is returned.


.. method:: DbObject.prev(index)

    Returns the index of the element in the collection preceding the specified
    index. If there are no elements in the collection preceding the
    specified index, *None* is returned.


.. method:: DbObject.setelement(index, value)

    Sets the value in the collection at the specified index to the given value.


.. method:: DbObject.size()

    Returns the number of elements in the collection.


.. method:: DbObject.trim(num)

    Removes the specified number of elements from the end of the collection.

DbObject Attributes
+++++++++++++++++++

.. attribute:: DbObject.Type

    This read-only attribute returns an ObjectType corresponding to the type
    of object.


.. _dbobjectattr:

DbObjectAttribute Objects
=========================

The elements of :attr:`DbObjectType.attributes` are instances of this type.

.. dbapiobjectextension::

.. attribute:: DbObjectAttribute.max_size

    This read-only attribute returns the maximum size (in bytes) of the
    attribute when the attribute's type is one of
    :data:`oracledb.DB_TYPE_CHAR`, :data:`oracledb.DB_TYPE_NCHAR`,
    :data:`oracledb.DB_TYPE_NVARCHAR`, :data:`oracledb.DB_TYPE_RAW`, or
    :data:`oracledb.DB_TYPE_VARCHAR`. For all other types the value returned is
    *None*.

    .. versionadded:: 3.0.0


.. attribute:: DbObjectAttribute.name

    This read-only attribute returns the name of the attribute.


.. attribute:: DbObjectAttribute.precision

    This read-only attribute returns the precision of the attribute when the
    attribute's type is :data:`oracledb.DB_TYPE_NUMBER`. For all other types
    the value returned is *None*.

    .. versionadded:: 3.0.0


.. attribute:: DbObjectAttribute.scale

    This read-only attribute returns the scale of the attribute when the
    attribute's type is :data:`oracledb.DB_TYPE_NUMBER`. For all other types
    the value returned is *None*.

    .. versionadded:: 3.0.0


.. attribute:: DbObjectAttribute.type

    This read-only attribute returns the type of the attribute. This will be an
    :ref:`Oracle Object Type <dbobjecttype>` if the variable binds
    Oracle objects; otherwise, it will be one of the
    :ref:`database type constants <dbtypes>`.
