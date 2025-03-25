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

    The data frame support in python-oracledb 3.1 is a pre-release and may
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

The object implements the Python DataFrame Interchange Protocol `DataFrame API
Interface <https://data-apis.org/dataframe-protocol/latest/API.html>`__

.. method:: OracleDataFrame.column_arrays()

    Returns a list of :ref:`OracleArrowArray <oraclearrowarrayobj>` objects,
    each containing a select list column.

    This is an extension to the DataFrame Interchange Protocol.

.. method:: OracleDataFrame.column_names()

    Returns a list of the column names in the data frame.

.. method:: OracleDataFrame.get_chunks(n_chunks)

    Returns itself, since python-oracledb only uses one chunk.

.. method:: OracleDataFrame.get_column(i)

    Returns an :ref:`OracleColumn <oraclearrowarrayobj>` object for the column
    at the given index ``i``.

.. method:: OracleDataFrame.get_column_by_name(name)

    Returns an :ref:`OracleColumn <oraclearrowarrayobj>` object for the column
    with the given name ``name``.

.. method:: OracleDataFrame.get_columns()

    Returns a list of :ref:`OracleColumn <oraclearrowarrayobj>` objects, one
    object for each column in the data frame.

.. method:: OracleDataFrame.num_chunks()

    Return the number of chunks the data frame consists of.

    This always returns 1.

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

.. _oraclecolumnobj:

OracleColumn Objects
====================

OracleColumn objects are returned by :meth:`OracleDataFrame.get_column()`,
:meth:`OracleDataFrame.get_column_by_name()`, and
:meth:`OracleDataFrame.get_columns()`.

.. versionadded:: 3.0.0

.. _oraclecolumnmeth:

OracleColumn Methods
--------------------

.. method:: OracleColumn.get_buffers()

    Returns a dictionary containing the underlying buffers.

    The returned dictionary contains the ``data``, ``validity``, and ``offset``
    keys.

    The ``data`` attribute is a two-element tuple whose first element is a
    buffer containing the data and whose second element is the data buffer's
    associated dtype.

    The ``validity`` attribute is a a two-element tuple whose first element
    is a buffer containing mask values indicating missing data and whose
    second element is the mask value buffer's associated dtype. The value of
    this attribute is *None* if the null representation is not a bit or byte
    mask.

    The ``offset`` attribute is a two-element tuple whose first element is a
    buffer containing the offset values for variable-size binary data (for
    example, variable-length strings) and whose second element is the offsets
    buffer's associated dtype. The value of this attribute is *None* if the
    data buffer does not have an associated offsets buffer.

.. method:: OracleColumn.get_chunks(n_chunks)

    Returns itself, since python-oracledb only uses one chunk.

.. method:: OracleColumn.num_chunks()

    Returns the number of chunks the column consists of.

    This always returns 1.

.. method:: OracleColumn.size()

    Returns the number of rows in the column.

.. _oraclecolumnattr:

OracleColumn Attributes
-----------------------

.. attribute:: OracleColumn.describe_null

    This read-only property returns the description of the null representation
    that the column uses.

.. attribute:: OracleColumn.dtype

    This read-only attribute returns the Dtype description as a tuple
    containing the values for the attributes ``kind``, ``bit-width``,
    ``format string``, and ``endianess``.

    The ``kind`` attribute specifies the type of the data.

    The ``bit-width`` attribute specifies the number of bits as an integer.

    The ``format string`` attribute specifies the data type description format
    string in Apache Arrow C Data Interface format.

    The ``endianess`` attribute specifies the byte order of the data type.
    Currently, only native endianess is supported.

.. attribute:: OracleColumn.metadata

    This read-only attribute returns the metadata for the column as a
    dictionary with string keys.

.. attribute:: OracleColumn.null_count

    This read-only attribute returns the number of null row values, if known.

.. attribute:: OracleColumn.offset

    This read-only attribute specifies the offset of the first row.

.. _oraclecolumnbufferobj:

OracleColumnBuffer Objects
==========================

A buffer object backed by an ArrowArray consisting of a single chunk.

This is an internal class used for conversion to third party data frames.

.. versionadded:: 3.0.0

.. _oraclecolumnbufferattr:

OracleColumnBuffer Attributes
-----------------------------

.. attribute:: OracleColumnBuffer.bufsize

    This read-only property returns the buffer size in bytes.

.. attribute:: OracleColumnBuffer.ptr

    This read-only attribute specifies the pointer to the start of the buffer
    as an integer.
