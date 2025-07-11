.. _oracledataframe:

****************
API: Data Frames
****************

Python-oracledb can fetch directly to data frames that expose an Apache Arrow
PyCapsule Interface. These can be used by many numerical and data analysis
libraries.

See :ref:`dataframeformat` for more information, including the type mapping
from Oracle Database types to Arrow data types.

.. note::

    The data frame support in python-oracledb 3.3 is a pre-release and may
    change in a future version.

.. _oracledataframeobj:

OracleDataFrame Objects
=======================

OracleDataFrame objects are returned from the methods
:meth:`Connection.fetch_df_all()` and :meth:`Connection.fetch_df_batches()`.

Each column in OracleDataFrame exposes an `Apache Arrow PyCapsule
<https://arrow.apache.org/docs/format/CDataInterface/PyCapsuleInterface.html>`__
interface, giving access to the underlying Arrow array.

.. dbapiobjectextension::

.. versionadded:: 3.0.0

.. _oracledataframemeth:

OracleDataFrame Methods
-----------------------

.. method:: OracleDataFrame.column_arrays()

    Returns a list of :ref:`OracleArrowArray <oraclearrowarrayobj>` objects,
    each containing a select list column.

.. method:: OracleDataFrame.column_names()

    Returns a list of the column names in the data frame.

.. method:: OracleDataFrame.get_column(i)

    Returns an :ref:`OracleArrowArray <oraclearrowarrayobj>` object for the column
    at the given index ``i``.

.. method:: OracleDataFrame.get_column_by_name(name)

    Returns an :ref:`OracleArrowArray <oraclearrowarrayobj>` object for the column
    with the given name ``name``.

.. method:: OracleDataFrame.num_columns()

   Returns the number of columns in the data frame.

.. method:: OracleDataFrame.num_rows()

   Returns the number of rows in the data frame.

.. _oracledataframeattr:

OracleDataFrame Attributes
--------------------------

.. attribute:: OracleDataFrame.metadata

    This read-only attribute returns the metadata for the data frame as a
    dictionary with keys ``num_columns``, ``num_rows``, and ``num_chunks``,
    showing the number of columns, rows, and chunks, respectively. The number
    of chunks is always 1 in python-oracledb.

.. _oraclearrowarrayobj:

OracleArrowArray Objects
========================

OracleArrowArray objects are returned by
:meth:`OracleDataFrame.column_arrays()`.

These are used for conversion to `PyArrow Tables
<https://arrow.apache.org/docs/python/generated/pyarrow.Table.html>`__, see
:ref:`dataframeformat`.

.. versionadded:: 3.0.0
