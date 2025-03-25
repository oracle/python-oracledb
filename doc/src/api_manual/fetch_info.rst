.. _fetchinfoobj:

**********************
API: FetchInfo Objects
**********************

FetchInfo objects are created internally when a query is executed. They are found
in the sequence :data:`Cursor.description`. There is one FetchInfo object for
each column. For compatibility with the Python Database API, this object
behaves as a 7-tuple containing the values for the attributes ``name``,
``type_code``, ``display_size``, ``internal_size``, ``precision``, ``scale``,
and ``null_ok`` in that order. For example, if ``fetch_info`` is of type
FetchInfo, then ``fetch_info[2]`` is the same as ``fetch_info.display_size``.

.. dbapiobjectextension::

.. versionadded:: 1.4.0

FetchInfo Attributes
====================

.. attribute:: FetchInfo.annotations

    This read-only attribute returns a dictionary containing the `annotations
    <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-1AC16117-
    BBB6-4435-8794-2B99F8F68052>`__ associated with the fetched column. If
    there are no annotations, the value *None* is returned. Annotations
    require Oracle Database 23ai. If using python-oracledb Thick mode, Oracle
    Client 23ai is also required.

    .. versionadded:: 2.0.0

.. attribute:: FetchInfo.display_size

    This read-only attribute returns the display size of the column as mandated
    by the Python Database API.

.. attribute:: FetchInfo.domain_name

    This read-only attribute returns the name of the `data use case domain
    <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-17D3A9C6-
    D993-4E94-BF6B-CACA56581F41>`__ associated with the fetched column. If
    there is no data use case domain, the value *None* is returned. `Data
    use case domains <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
    GUID-4743FDE1-7C6E-471B-BC9D-442383CCA2F9>`__ require Oracle Database 23ai.
    If using python-oracledb Thick mode, Oracle Client 23ai is also required.

    .. versionadded:: 2.0.0

.. attribute:: FetchInfo.domain_schema

    This read-only attribute returns the schema of the `data use case domain
    <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=GUID-17D3A9C6-
    D993-4E94-BF6B-CACA56581F41>`__ associated with the fetched column. If
    there is no data use case domain, the value *None* is returned. `Data
    use case domains <https://www.oracle.com/pls/topic/lookup?ctx=dblatest&id=
    GUID-4743FDE1-7C6E-471B-BC9D-442383CCA2F9>`__ require Oracle Database 23ai.
    If using python-oracledb Thick mode, Oracle Client 23ai is also required.

    .. versionadded:: 2.0.0

.. attribute:: FetchInfo.internal_size

    This read-only attribute returns the internal size of the column as
    mandated by the Python Database API.

.. attribute:: FetchInfo.is_json

    This read-only attribute returns whether the column is known to contain
    JSON data. This will be *True* when the type code is
    :data:`oracledb.DB_TYPE_JSON` as well as when an "IS JSON" constraint is
    enabled on LOB and VARCHAR2 columns.

.. attribute:: FetchInfo.is_oson

    This read-only attribute returns whether the column is known to contain
    binary encoded `OSON <https://www.oracle.com/pls/topic/lookup?ctx=dblatest
    &id=GUID-911D302C-CFAF-406B-B6A5-4E99DD38ABAD>`__ data. This will be *True*
    when an "IS JSON FORMAT OSON" check constraint is enabled on BLOB columns.

    .. versionadded:: 2.1.0

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

.. attribute:: FetchInfo.vector_dimensions

    This read-only attribute returns the number of dimensions required by
    VECTOR columns. If the column is not a VECTOR column or allows for any
    number of dimensions, the value returned is *None*.

    .. versionadded:: 2.2.0

.. attribute:: FetchInfo.vector_format

    This read-only attribute returns the storage format used by VECTOR
    columns. The value of this attribute can be:

    - :data:`oracledb.VECTOR_FORMAT_BINARY` which represents 8-bit unsigned
      integers
    - :data:`oracledb.VECTOR_FORMAT_INT8` which represents 8-bit signed
      integers
    - :data:`oracledb.VECTOR_FORMAT_FLOAT32` which represents 32-bit
      floating-point numbers
    - :data:`oracledb.VECTOR_FORMAT_FLOAT64` which represents 64-bit
      floating-point numbers

    If the column is not a VECTOR column or allows for any type of storage,
    the value returned is *None*.

    .. versionadded:: 2.2.0

.. attribute:: FetchInfo.vector_is_sparse

    This read-only attribute returns a boolean that indicates whether the
    vector is sparse or not.

    If the column contains vectors that are SPARSE, the value returned is
    True. If the column contains vectors that are DENSE, the value returned is
    False. If the column is not a VECTOR column, the value returned is ``None``.

    .. versionadded:: 3.0.0
