.. _fetchinfoobj:

**********************
API: FetchInfo Objects
**********************

.. currentmodule:: oracledb

FetchInfo Class
===============

.. autoclass:: FetchInfo

    A FetchInfo object is created internally when a query is executed. They
    are found in the sequence :data:`Cursor.description`. There is one
    FetchInfo object for each column. For compatibility with the Python
    Database API, this object behaves as a 7-tuple containing the values for
    the attributes ``name``, ``type_code``, ``display_size``,
    ``internal_size``, ``precision``, ``scale``, and ``null_ok`` in that order.
    For example, if ``fetch_info`` is of type FetchInfo, then ``fetch_info[2]``
    is the same as ``fetch_info.display_size``.

    .. dbapiobjectextension::

    .. versionadded:: 1.4.0

FetchInfo Attributes
====================

.. autoproperty:: FetchInfo.annotations

    .. versionadded:: 2.0.0

.. autoproperty:: FetchInfo.display_size

.. autoproperty:: FetchInfo.domain_name

    .. versionadded:: 2.0.0

.. autoproperty:: FetchInfo.domain_schema

    .. versionadded:: 2.0.0

.. autoproperty:: FetchInfo.internal_size

.. autoproperty:: FetchInfo.is_json

.. autoproperty:: FetchInfo.is_oson

    .. versionadded:: 2.1.0

.. autoproperty:: FetchInfo.name

.. autoproperty:: FetchInfo.null_ok

.. autoproperty:: FetchInfo.precision

.. autoproperty:: FetchInfo.scale

.. autoproperty:: FetchInfo.type

.. autoproperty:: FetchInfo.type_code

.. autoproperty:: FetchInfo.vector_dimensions

    .. versionadded:: 2.2.0

.. autoproperty:: FetchInfo.vector_format

    .. versionadded:: 2.2.0

.. autoproperty:: FetchInfo.vector_is_sparse

    .. versionadded:: 3.0.0
