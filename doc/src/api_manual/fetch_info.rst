.. _fetchinfoobj:

**********************
API: FetchInfo Objects
**********************

These objects are created internally when a query is executed. They are found
in the sequence :data:`Cursor.description`. For compatibility with the Python
Database API, this object behaves as a 7-tuple containing the values for the
attributes ``name``, ``type_code``, ``display_size``, ``internal_size``,
``precision``, ``scale``, and ``null_ok`` in that order. For example, if
``fetch_info`` is of type FetchInfo, then ``fetch_info[2]`` is the same as
``fetch_info.display_size``.

.. versionadded:: 1.4.0

.. note::

    This object is an extension the DB API.

FetchInfo Attributes
====================

.. attribute:: FetchInfo.display_size

    This read-only attribute returns the display size of the column as mandated
    by the Python Database API.

.. attribute:: FetchInfo.internal_size

    This read-only attribute returns the internal size of the column as
    mandated by the Python Database API.

.. attribute:: FetchInfo.is_json

    This read-only attribute returns whether the column is known to contain
    JSON data. This will be ``true`` when the type code is
    ``oracledb.DB_TYPE_JSON`` as well as when an "IS JSON" constraint is
    enabled on LOB and VARCHAR2 columns.

.. attribute:: FetchInfo.name

    This read-only attribute returns the name of the column as mandated by the
    Python Database API.

.. attribute:: FetchInfo.null_ok

    This read-only attribute returns whether nulls are allowed in the column as
    mandated by the Python Database API.

.. attribute:: FetchInfo.precision

    This read-only attribute returns the precision of the column as mandated by
    the Python Database API.

.. attribute:: FetchInfo.scale

    This read-only attribute returns the scale of the column as mandated by
    the Python Database API.

.. attribute:: FetchInfo.type

    This read-only attribute returns the type of the column. This will be an
    :ref:`Oracle Object Type <dbobjecttype>` if the column contains Oracle
    objects; otherwise, it will be one of the :ref:`database type constants
    <dbtypes>` defined at the module level.


.. attribute:: FetchInfo.type_code

    This read-only attribute returns the type of the column as mandated by the
    Python Database API. The type will be one of the :ref:`database type
    constants <dbtypes>` defined at the module level.
