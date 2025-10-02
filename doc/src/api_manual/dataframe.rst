.. _oracledataframe:

**********************
API: DataFrame Objects
**********************

.. currentmodule:: oracledb

Python-oracledb can fetch directly to data frames that expose an Apache Arrow
PyCapsule Interface. These can be used by many numerical and data analysis
libraries.

See :ref:`dataframeformat` for more information, including the type mapping
from Oracle Database types to Arrow data types.

.. _oracledataframeobj:

DataFrame Class
===============

.. autoclass:: DataFrame

    A DataFrame object is returned by the methods
    :meth:`Connection.fetch_df_all()`,
    :meth:`Connection.fetch_df_batches()`,
    :meth:`AsyncConnection.fetch_df_all()`, or
    :meth:`AsyncConnection.fetch_df_batches()`.

    Each column in a DataFrame exposes an `Apache Arrow PyCapsule
    <https://arrow.apache.org/docs/format/CDataInterface/
    PyCapsuleInterface.html>`__ interface, giving access to the underlying
    Apache Arrow array.

    .. dbapiobjectextension::

    .. versionchanged:: 3.3.0

        Removed the prefix "Oracle" from the class name.

    .. versionadded:: 3.0.0

.. _oracledataframemeth:

DataFrame Methods
-----------------

.. automethod:: DataFrame.column_arrays

.. automethod:: DataFrame.column_names

.. automethod:: DataFrame.get_column

.. automethod:: DataFrame.get_column_by_name

.. automethod:: DataFrame.num_columns

.. automethod:: DataFrame.num_rows

.. _oraclearrowarrayobj:

ArrowArray Objects
==================

.. autoclass:: ArrowArray

    ArrowArray objects are returned by :meth:`DataFrame.column_arrays()`.

    These are used for conversion to `PyArrow Tables
    <https://arrow.apache.org/docs/python/generated/pyarrow.Table.html>`__, see
    :ref:`dataframeformat`.

    .. versionchanged:: 3.3.0

        Removed the prefix "Oracle" from the class name.

    .. versionadded:: 3.0.0
